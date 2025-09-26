"""深度调研配置管理

管理深度调研相关的环境变量和配置参数。
"""

import os
from typing import Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable


class DeepResearchConfig:
    """深度调研配置类"""

    def __init__(self):
        # 基础配置
        self.enabled = os.getenv("DEEP_RESEARCHER_ENABLE", "false").lower() == "true"
        self.model = os.getenv("DEEPRESEARCH_MODEL", "alibaba/tongyi-deepresearch-30b-a3b")
        self.planning_port = int(os.getenv("DEEPRESEARCH_PORT", "6001"))
        self.max_rounds = int(os.getenv("DEEPRESEARCH_MAX_ROUNDS", "8"))
        self.timeout_seconds = int(os.getenv("DEEPRESEARCH_TIMEOUT", "2700"))
        self.max_retries = int(os.getenv("DEEPRESEARCH_RETRIES", "2"))

        # OpenRouter 配置
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.planner_model = os.getenv("PLANNER_MODEL", "openai/gpt-4o")
        self.synthesizer_model = os.getenv("SYNTHESIZER_MODEL", "openai/gpt-4o")

        # 日志配置
        self.log_level = os.getenv("DEEPRESEARCH_LOG_LEVEL", "INFO")

    def create_planner(self, llm: Runnable) -> Runnable:
        """创建规划器"""
        prompt = ChatPromptTemplate.from_template(
            """
你是研究规划师。请根据以下对话拆分 2-4 个可执行步骤，
以 JSON 格式返回 {{"steps": [{{"task": str, "deliverable": str}}]}}。

对话内容：
{messages}
"""
        )
        chain = prompt | llm | StrOutputParser()
        return chain

    def create_synthesizer(self, llm: Runnable) -> Runnable:
        """创建合成器"""
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "你负责整合 DeepResearch 执行结果，输出一份条理清晰的总结，"
                "引用关键证据并在需要时列出参考。",
            ),
            (
                "user",
                "原始问题：{question}\n计划步骤：{plan}\n执行记录：{task_results}\n请生成最终答复。",
            ),
        ])
        chain = prompt | llm
        return chain

    def validate(self) -> bool:
        """验证配置是否有效"""
        if not self.enabled:
            return True

        if not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY 环境变量未设置")

        if self.max_rounds <= 0:
            raise ValueError("DEEPRESEARCH_MAX_ROUNDS 必须大于0")

        if self.timeout_seconds <= 0:
            raise ValueError("DEEPRESEARCH_TIMEOUT 必须大于0")

        return True

    def get_function_list(self) -> list:
        """获取工具列表"""
        return ["search", "visit", "google_scholar", "PythonInterpreter"]

    @classmethod
    def from_env(cls) -> "DeepResearchConfig":
        """从环境变量创建配置"""
        return cls()
