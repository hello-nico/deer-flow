"""Reusable LangGraph node for Tongyi DeepResearch execution."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.runnables import Runnable, RunnableConfig, RunnableSerializable

from langgraph_executor import (
    DeepResearchAdapter,
    create_default_planner,
    create_default_synthesizer,
    create_deepresearch_executor_graph,
)
from react_agent import MultiTurnReactAgent


@dataclass
class DeepResearchNodeOutputs:
    """Structured output returned by :class:`DeepResearchNode`."""

    answer: str
    messages: List[BaseMessage]
    serialized_messages: List[Dict[str, Any]]
    plan: List[str]
    task_results: List[Dict[str, Any]]


class DeepResearchNode(RunnableSerializable[Dict[str, Any], Dict[str, Any]]):
    """LangGraph runnable that wraps the default DeepResearch executor graph."""

    def __init__(self, planner: Runnable, synthesizer: Runnable, adapter: DeepResearchAdapter):
        super().__init__()
        self._graph = create_deepresearch_executor_graph(planner, synthesizer, adapter)

    def invoke(self, inputs: Dict[str, Any], config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
        question = inputs.get("question")
        messages = self._prepare_messages(question, inputs.get("messages"))
        state = {
            "messages": messages,
            "task_results": inputs.get("task_results", []),
            "plan": inputs.get("plan", []),
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
        question = inputs.get("question")
        messages = self._prepare_messages(question, inputs.get("messages"))
        state = {
            "messages": messages,
            "task_results": inputs.get("task_results", []),
            "plan": inputs.get("plan", []),
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
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                return msg.content
        return ""

    def _serialize_messages(self, messages: List[BaseMessage]) -> List[Dict[str, Any]]:
        serialized: List[Dict[str, Any]] = []
        for msg in messages:
            if hasattr(msg, "to_dict"):
                serialized.append(msg.to_dict())
            elif hasattr(msg, "dict"):
                serialized.append(msg.dict())
            else:
                serialized.append({"type": msg.__class__.__name__, "content": getattr(msg, "content", str(msg))})
        return serialized


def build_default_deepresearch_node(logger: Optional[logging.Logger] = None) -> DeepResearchNode:
    """Factory helper that builds a :class:`DeepResearchNode` with sensible defaults."""

    from langchain_openai import ChatOpenAI

    planner_llm = ChatOpenAI(
        base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        api_key=os.environ["OPENROUTER_API_KEY"],
        model=os.environ.get("PLANNER_MODEL", "openai/gpt-4o"),
        temperature=0,
        timeout=120,
    )
    synthesizer_llm = ChatOpenAI(
        base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        api_key=os.environ["OPENROUTER_API_KEY"],
        model=os.environ.get("SYNTHESIZER_MODEL", "openai/gpt-4o"),
        temperature=0.2,
        timeout=120,
    )

    planner = create_default_planner(planner_llm)
    synthesizer = create_default_synthesizer(synthesizer_llm)

    model_path = os.environ.get("DEEPRESEARCH_MODEL", "alibaba/tongyi-deepresearch-30b-a3b")
    planning_port = int(os.environ.get("DEEPRESEARCH_PORT", "6001"))

    agent = MultiTurnReactAgent(
        llm={
            "model": model_path,
            "generate_cfg": {
                "max_input_tokens": 320000,
                "max_retries": 10,
                "temperature": 0.6,
                "top_p": 0.95,
                "presence_penalty": 1.1,
            },
        },
        function_list=["search", "visit", "google_scholar", "PythonInterpreter"],
    )

    adapter = DeepResearchAdapter(
        agent=agent,
        model=model_path,
        planning_port=planning_port,
        logger=logger or logging.getLogger(__name__),
        max_rounds=int(os.environ.get("DEEPRESEARCH_MAX_ROUNDS", "8")),
        timeout_seconds=int(os.environ.get("DEEPRESEARCH_TIMEOUT", str(45 * 60))),
        max_retries=int(os.environ.get("DEEPRESEARCH_RETRIES", "2")),
    )

    return DeepResearchNode(planner=planner, synthesizer=synthesizer, adapter=adapter)


__all__ = ["DeepResearchNode", "DeepResearchNodeOutputs", "build_default_deepresearch_node"]
