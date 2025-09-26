"""LangGraph 集成：Planner → DeepResearch Executor → Synthesizer.

该模块实现了场景1中 Tongyi DeepResearch 作为执行体的 LangGraph 状态图，
并提供 DeepResearchAdapter 将 MultiTurnReactAgent 的输出转成 LangGraph
可消费的 message 序列与执行日志。
"""

from __future__ import annotations

import json5
import logging
import re
import time
from dataclasses import dataclass
from operator import add
from typing import Any, Dict, Iterable, List, Optional, Sequence
from uuid import uuid4
from pydantic import ConfigDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig, RunnableSerializable
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict

from react_agent import MultiTurnReactAgent


class TaskResult(TypedDict, total=False):
    task_index: int
    task: str
    answer: str
    status: str
    termination: str
    attempts: int
    elapsed: float
    tool_calls: List[Dict[str, Any]]
    raw_messages: List[Dict[str, Any]]
    errors: List[str]


class ResearchState(TypedDict, total=False):
    messages: Annotated[List[BaseMessage], add_messages]
    plan: List[str]
    current_task_index: int
    task_results: Annotated[List[TaskResult], add]
    executor_ready: bool
    active_task_index: Optional[int]


class DeepResearchAdapter(RunnableSerializable):
    """将 MultiTurnReactAgent 输出适配为 LangGraph 消息序列。"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent: MultiTurnReactAgent
    model: str
    planning_port: int
    max_rounds: Optional[int] = None
    timeout_seconds: Optional[int] = None
    max_retries: int = 1
    logger: Optional[logging.Logger] = None

    def invoke(self, state: ResearchState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
        plan: Sequence[str] = state.get("plan", []) or []
        task_index = state.get("current_task_index", 0)
        if task_index >= len(plan):
            return {"executor_ready": False}

        task = plan[task_index]
        attempt = 0
        errors: List[str] = []
        start_ts = time.time()

        while attempt < max(self.max_retries, 1):
            attempt += 1
            try:
                input_payload = {
                    "item": {"question": task, "answer": ""},
                    "planning_port": self.planning_port,
                }
                result = self.agent._run(
                    input_payload,
                    self.model,
                    max_rounds=self.max_rounds,
                    max_runtime_seconds=self.timeout_seconds,
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(str(exc))
                if self.logger:
                    self.logger.error("DeepResearch 执行异常: %s", exc, exc_info=True)
                continue

            messages_raw: List[Dict[str, Any]] = result.get("messages", [])
            parsed_messages = self._convert_messages(messages_raw)
            final_answer = result.get("prediction", "")
            termination = result.get("termination", "unknown")
            elapsed = time.time() - start_ts
            tool_calls = self._collect_tool_calls(parsed_messages)

            task_result: TaskResult = {
                "task_index": task_index,
                "task": task,
                "answer": final_answer,
                "status": "success",
                "termination": termination,
                "attempts": attempt,
                "elapsed": elapsed,
                "tool_calls": tool_calls,
                "raw_messages": messages_raw,
            }

            return {
                "messages": parsed_messages,
                "task_results": [task_result],
                "current_task_index": task_index + 1,
                "executor_ready": False,
                "active_task_index": None,
            }

        failure_elapsed = time.time() - start_ts
        failure_message = AIMessage(
            content=f"执行任务失败：{task}\n错误信息：{errors[-1] if errors else '未知异常'}",
            additional_kwargs={
                "task_index": task_index,
                "status": "failed",
                "errors": errors,
            },
        )
        failure_result: TaskResult = {
            "task_index": task_index,
            "task": task,
            "status": "failed",
            "termination": "exception",
            "attempts": attempt,
            "elapsed": failure_elapsed,
            "errors": errors,
        }
        return {
            "messages": [failure_message],
            "task_results": [failure_result],
            "current_task_index": task_index + 1,
            "executor_ready": False,
            "active_task_index": None,
        }

    def _convert_messages(self, messages: Iterable[Dict[str, Any]]) -> List[BaseMessage]:
        converted: List[BaseMessage] = []
        user_seen = False
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "") or ""
            if role == "system":
                continue
            if role == "user":
                if not user_seen:
                    user_seen = True
                    continue
                tool_response = self._strip_tag(content, "tool_response")
                converted.append(
                    HumanMessage(
                        content=tool_response,
                        additional_kwargs={"source": "tool_response"},
                    )
                )
                continue
            if role == "assistant":
                converted.append(self._convert_assistant_message(content))
        return converted

    def _convert_assistant_message(self, content: str) -> AIMessage:
        think_text = self._strip_tag(content, "think")
        answer_text = self._strip_tag(content, "answer")
        tool_calls_raw = re.findall(r"<tool_call>(.*?)</tool_call>", content, flags=re.DOTALL)
        tool_calls = []
        for raw in tool_calls_raw:
            parsed = self._parse_tool_call(raw)
            tool_calls.append(parsed)
        visible_content = answer_text or self._strip_visible_text(content)
        return AIMessage(
            content=visible_content,
            additional_kwargs={
                "thought": think_text,
                "raw_tool_calls": tool_calls_raw,
            },
            tool_calls=[
                {
                    "id": str(uuid4()),
                    "name": item.get("name", "unknown"),
                    "args": item.get("arguments", {}),
                    "type": "tool_call",
                }
                for item in tool_calls
            ],
        )

    def _strip_visible_text(self, content: str) -> str:
        cleaned = re.sub(r"<.*?>", "", content, flags=re.DOTALL)
        return cleaned.strip()

    def _strip_tag(self, content: str, tag: str) -> str:
        pattern = re.compile(rf"<{tag}>(.*?)</{tag}>", flags=re.DOTALL)
        match = pattern.search(content)
        if match:
            return match.group(1).strip()
        return ""

    def _parse_tool_call(self, block: str) -> Dict[str, Any]:
        block = block.strip()
        if "<code>" in block and "</code>" in block:
            code = self._strip_tag(block, "code")
            return {"name": "python", "arguments": {"code": code}}
        try:
            parsed = json5.loads(block)
            if isinstance(parsed, dict):
                return {
                    "name": parsed.get("name", "unknown"),
                    "arguments": parsed.get("arguments", {}),
                }
        except Exception:  # noqa: BLE001
            pass
        return {"name": "unknown", "arguments": {"raw": block}}

    def _collect_tool_calls(self, messages: Sequence[BaseMessage]) -> List[Dict[str, Any]]:
        summary: List[Dict[str, Any]] = []
        for msg in messages:
            if isinstance(msg, AIMessage) and msg.tool_calls:
                for call in msg.tool_calls:
                    summary.append(
                        {
                            "id": call.get("id"),
                            "name": call.get("name"),
                            "arguments": call.get("args", {}),
                        }
                    )
        return summary


def create_default_planner(llm: Runnable) -> Runnable:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是研究规划师。请根据用户问题拆分 2-4 个可执行步骤，"
                "以 JSON 格式返回 {{\"steps\": [{{\"task\": str, \"deliverable\": str}}]}}.",
            ),
            ("placeholder", "{messages}"),
        ]
    )
    chain = prompt | llm | StrOutputParser()
    return chain


def create_default_synthesizer(llm: Runnable) -> Runnable:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你负责整合 DeepResearch 执行结果，输出一份条理清晰的总结，"
                "引用关键证据并在需要时列出参考。",
            ),
            (
                "user",
                "原始问题：{question}\n计划步骤：{plan}\n执行记录：{task_results}\n请生成最终答复。",
            ),
        ]
    )
    chain = prompt | llm
    return chain


def _extract_plan(content: str) -> List[str]:
    try:
        payload = json5.loads(content)
        if isinstance(payload, dict) and "steps" in payload:
            steps = payload.get("steps", [])
            if isinstance(steps, list):
                cleaned = []
                for item in steps:
                    if isinstance(item, str):
                        cleaned.append(item.strip())
                    elif isinstance(item, dict):
                        value = item.get("task") or item.get("objective") or item.get("description")
                        if value:
                            cleaned.append(str(value).strip())
                if cleaned:
                    return cleaned
    except Exception:  # noqa: BLE001
        pass
    numbered = []
    for line in content.splitlines():
        match = re.match(r"^\s*\d+[\.)]\s*(.+)$", line)
        if match:
            numbered.append(match.group(1).strip())
    if numbered:
        return numbered
    stripped = content.strip()
    return [stripped] if stripped else []


def planner_node_factory(planner: Runnable) -> Runnable:
    class _Planner(RunnableSerializable):
        def invoke(self, state: ResearchState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
            result = planner.invoke({"messages": state.get("messages", [])}, config=config)
            if isinstance(result, BaseMessage):
                content = result.content
                planner_message = result
            else:
                content = str(result)
                planner_message = AIMessage(content=content)
            steps = _extract_plan(content)
            return {
                "messages": [planner_message],
                "plan": steps,
                "current_task_index": 0,
                "executor_ready": False,
                "active_task_index": None,
            }

    return _Planner()


def select_task_node(state: ResearchState) -> Dict[str, Any]:
    plan = state.get("plan", []) or []
    index = state.get("current_task_index", 0)
    if index >= len(plan):
        return {"executor_ready": False, "active_task_index": None}
    task = plan[index]
    message = HumanMessage(
        content=f"请执行第{index + 1}步任务：{task}",
        additional_kwargs={"task_index": index, "role": "planner_instructions"},
    )
    return {
        "messages": [message],
        "executor_ready": True,
        "active_task_index": index,
    }


def select_task_router(state: ResearchState) -> str:
    return "deepresearch" if state.get("executor_ready") else "synthesizer"


def executor_router(state: ResearchState) -> str:
    plan = state.get("plan", []) or []
    index = state.get("current_task_index", 0)
    if index < len(plan):
        return "select_task"
    return "synthesizer"


def synthesizer_node_factory(synthesizer: Runnable) -> Runnable:
    class _Synthesizer(RunnableSerializable):
        def invoke(self, state: ResearchState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
            question = next(
                (msg.content for msg in state.get("messages", []) if isinstance(msg, HumanMessage)),
                "",
            )
            payload = {
                "question": question,
                "plan": state.get("plan", []),
                "task_results": state.get("task_results", []),
                "messages": state.get("messages", []),
            }
            result = synthesizer.invoke(payload, config=config)
            if isinstance(result, BaseMessage):
                message = result
            else:
                message = AIMessage(content=str(result))
            return {"messages": [message]}

    return _Synthesizer()


def create_deepresearch_executor_graph(
    planner: Runnable,
    synthesizer: Runnable,
    adapter: DeepResearchAdapter,
) -> Any:
    graph: StateGraph[ResearchState] = StateGraph(ResearchState)
    graph.add_node("planner", planner_node_factory(planner))
    graph.add_node("select_task", select_task_node)
    graph.add_node("deepresearch", adapter)
    graph.add_node("synthesizer", synthesizer_node_factory(synthesizer))

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "select_task")
    graph.add_conditional_edges("select_task", select_task_router, {"deepresearch": "deepresearch", "synthesizer": "synthesizer"})
    graph.add_conditional_edges("deepresearch", executor_router, {"select_task": "select_task", "synthesizer": "synthesizer"})
    graph.add_edge("synthesizer", END)

    return graph.compile()
