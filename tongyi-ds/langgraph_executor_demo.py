"""LangGraph 调用 Tongyi DeepResearch 作为执行器的参考示例。"""

import logging
from typing import List

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

from deepresearch_node import build_default_deepresearch_node


def run(question: str) -> List[str]:
    node = build_default_deepresearch_node(logger=logger)
    result = node.invoke({"question": question})
    messages = result.get("messages", [])
    return [getattr(msg, "content", "") for msg in messages if hasattr(msg, "content")]


if __name__ == "__main__":
    user_question = "What is GraphRAG technology?"
    outputs = run(user_question)
    print("\n".join(outputs[-2:]))
