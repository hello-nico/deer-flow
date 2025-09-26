"""Deer Flow 深度调研模块

此模块提供通义千问 DeepResearch 模型的集成能力，
支持可插拔的深度调研功能。
"""

from .node import DeepResearchNode, DeepResearchNodeOutputs
from .adapter import DeepResearchAdapter
from .wrapper import DeepResearchNodeWrapper, create_deep_research_wrapper
from .config import DeepResearchConfig
from .agent import MultiTurnReactAgent

__all__ = [
    "DeepResearchNode",
    "DeepResearchNodeOutputs",
    "DeepResearchAdapter",
    "DeepResearchNodeWrapper",
    "create_deep_research_wrapper",
    "DeepResearchConfig",
    "MultiTurnReactAgent",
]