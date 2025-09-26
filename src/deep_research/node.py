"""深度调研节点实现

迁移和适配 tongyi-ds 中的 DeepResearchNode，集成到 Deer Flow 架构中。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.runnables import Runnable, RunnableConfig, RunnableSerializable

from src.graph.types import State
from src.deep_research.adapter import DeepResearchAdapter


@dataclass
class DeepResearchNodeOutputs:
    """深度调研节点输出结构"""

    answer: str
    messages: List[BaseMessage]
    serialized_messages: List[Dict[str, Any]]
    plan: List[str]
    task_results: List[Dict[str, Any]]


class DeepResearchNode(RunnableSerializable[Dict[str, Any], Dict[str, Any]]):
    """深度调研节点，包装通义千问 DeepResearch 执行图"""

    def __init__(self, planner: Runnable, synthesizer: Runnable, adapter: DeepResearchAdapter):
        super().__init__()
        self._graph = adapter.create_executor_graph(planner, synthesizer)
        self._adapter = adapter

    def invoke(self, inputs: Dict[str, Any], config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
        """同步调用深度调研"""
        question = inputs.get("question")
        messages = self._prepare_messages(question, inputs.get("messages"))

        state = {
            "messages": messages,
            "task_results": inputs.get("task_results", []),
            "plan": inputs.get("plan", []),
            "current_task_index": inputs.get("current_task_index", 0),
            "executor_ready": False,
            "active_task_index": None,
        }

        result = self._graph.invoke(state, config=config)
        langchain_messages = result.get("messages", [])
        answer = self._extract_answer(langchain_messages)

        return {
            "answer": answer,
            "messages": langchain_messages,
            "serialized_messages": self._serialize_messages(langchain_messages),
            "plan": result.get("plan", inputs.get("plan", [])),
            "task_results": result.get("task_results", []),
        }

    async def ainvoke(self, inputs: Dict[str, Any], config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
        """异步调用深度调研"""
        question = inputs.get("question")
        messages = self._prepare_messages(question, inputs.get("messages"))

        state = {
            "messages": messages,
            "task_results": inputs.get("task_results", []),
            "plan": inputs.get("plan", []),
            "current_task_index": inputs.get("current_task_index", 0),
            "executor_ready": False,
            "active_task_index": None,
        }

        result = await self._graph.ainvoke(state, config=config)
        langchain_messages = result.get("messages", [])
        answer = self._extract_answer(langchain_messages)

        return {
            "answer": answer,
            "messages": langchain_messages,
            "serialized_messages": self._serialize_messages(langchain_messages),
            "plan": result.get("plan", inputs.get("plan", [])),
            "task_results": result.get("task_results", []),
        }

    def _prepare_messages(
        self,
        question: Optional[str],
        messages_input: Optional[Iterable[Any]],
    ) -> List[BaseMessage]:
        """准备消息格式"""
        prepared: List[BaseMessage] = []

        if messages_input:
            for item in messages_input:
                if isinstance(item, BaseMessage):
                    prepared.append(item)
                elif isinstance(item, dict) and item.get("role") and item.get("content"):
                    role = item["role"].lower()
                    content = str(item["content"])
                    if role == "user":
                        prepared.append(HumanMessage(content=content))
                    else:
                        prepared.append(AIMessage(content=content))
                elif isinstance(item, str):
                    prepared.append(HumanMessage(content=item))

        if not prepared:
            if not question:
                raise ValueError("DeepResearchNode requires either 'question' or 'messages'.")
            prepared.append(HumanMessage(content=str(question)))
        elif question:
            prepared.append(HumanMessage(content=str(question)))

        return prepared

    def _extract_answer(self, messages: List[BaseMessage]) -> str:
        """从消息中提取答案"""
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                return msg.content
        return ""

    def _serialize_messages(self, messages: List[BaseMessage]) -> List[Dict[str, Any]]:
        """序列化消息"""
        serialized: List[Dict[str, Any]] = []
        for msg in messages:
            if hasattr(msg, "to_dict"):
                serialized.append(msg.to_dict())
            elif hasattr(msg, "dict"):
                serialized.append(msg.dict())
            else:
                serialized.append({
                    "type": msg.__class__.__name__,
                    "content": getattr(msg, "content", str(msg))
                })
        return serialized


def create_deep_research_node(
    logger: Optional[logging.Logger] = None
) -> DeepResearchNode:
    """创建默认的深度调研节点"""
    from src.deep_research.config import DeepResearchConfig
    from src.deep_research.agent import create_multi_turn_react_agent
    from langchain_openai import ChatOpenAI

    config = DeepResearchConfig()

    # 创建规划器和合成器
    planner_llm = ChatOpenAI(
        base_url=config.openrouter_base_url,
        api_key=config.openrouter_api_key,
        model=config.planner_model,
        temperature=0,
        timeout=120,
    )

    synthesizer_llm = ChatOpenAI(
        base_url=config.openrouter_base_url,
        api_key=config.openrouter_api_key,
        model=config.synthesizer_model,
        temperature=0.2,
        timeout=120,
    )

    planner = config.create_planner(planner_llm)
    synthesizer = config.create_synthesizer(synthesizer_llm)

    # 创建代理
    agent = create_multi_turn_react_agent(config)

    # 创建适配器
    adapter = DeepResearchAdapter(
        agent=agent,
        model=config.model,
        planning_port=config.planning_port,
        logger=logger or logging.getLogger(__name__),
        max_rounds=config.max_rounds,
        timeout_seconds=config.timeout_seconds,
        max_retries=config.max_retries,
    )

    return DeepResearchNode(planner=planner, synthesizer=synthesizer, adapter=adapter)
