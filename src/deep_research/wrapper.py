"""深度调研节点包装器

实现可插拔的深度调研功能，支持在标准流程和深度调研流程之间切换。
"""

import logging
from typing import Any, Dict, Optional, Union

from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from src.graph.types import State
from src.graph.nodes import researcher_node
from src.deep_research.node import DeepResearchNode, DeepResearchNodeOutputs
from src.deep_research.config import DeepResearchConfig


class DeepResearchNodeWrapper:
    """深度调研节点包装器，实现可插拔逻辑"""

    def __init__(self, deep_research_node: Optional[DeepResearchNode] = None, is_enabled: bool = False):
        """初始化包装器

        Args:
            deep_research_node: 深度调研节点实例
            is_enabled: 是否启用深度调研
        """
        self.deep_research_node = deep_research_node
        self.is_enabled = is_enabled
        self.logger = logging.getLogger(__name__)

    async def ainvoke(self, state: State, config: RunnableConfig) -> Command:
        """异步调用深度调研或回退到标准流程

        Args:
            state: 当前状态
            config: 运行配置

        Returns:
            执行结果Command
        """
        if not self.is_enabled or not self.deep_research_node:
            # 回退到标准researcher节点
            self.logger.info("使用标准研究流程")
            return await researcher_node(state, config)

        try:
            # 使用深度调研节点
            self.logger.info("使用深度调研流程")
            deep_output = await self.deep_research_node.ainvoke(
                {
                    "question": state.get("research_topic"),
                    "messages": state.get("messages", []),
                    "plan": self._extract_plan_steps(state),
                    "task_results": state.get("task_results", [])
                },
                config
            )

            # 转换为标准格式
            result = self._convert_to_researcher_format(deep_output)
            return Command(update=result, goto="research_team")

        except Exception as e:
            self.logger.error(f"深度调研执行失败: {e}", exc_info=True)
            # 回退到标准流程
            self.logger.info("回退到标准研究流程")
            return await researcher_node(state, config)

    def invoke(self, state: State, config: RunnableConfig) -> Command:
        """同步调用深度调研或回退到标准流程

        Args:
            state: 当前状态
            config: 运行配置

        Returns:
            执行结果Command
        """
        import asyncio

        if not self.is_enabled or not self.deep_research_node:
            # 回退到标准researcher节点，需要处理异步调用
            self.logger.info("使用标准研究流程")
            try:
                # 获取或创建事件循环
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                # 运行异步researcher_node
                return loop.run_until_complete(researcher_node(state, config))
            except Exception as e:
                self.logger.error(f"标准研究流程执行失败: {e}", exc_info=True)
                # 返回错误结果
                return Command(update={
                    "messages": state.get("messages", []),
                    "observations": [f"研究流程执行失败: {str(e)}"],
                    "task_results": [],
                    "plan_updates": []
                }, goto="research_team")

        try:
            # 使用深度调研节点
            self.logger.info("使用深度调研流程")
            deep_output = self.deep_research_node.invoke(
                {
                    "question": state.get("research_topic"),
                    "messages": state.get("messages", []),
                    "plan": self._extract_plan_steps(state),
                    "task_results": state.get("task_results", [])
                },
                config
            )

            # 转换为标准格式
            result = self._convert_to_researcher_format(deep_output)
            return Command(update=result, goto="research_team")

        except Exception as e:
            self.logger.error(f"深度调研执行失败: {e}", exc_info=True)
            # 回退到标准流程
            self.logger.info("回退到标准研究流程")
            try:
                # 获取或创建事件循环
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                # 运行异步researcher_node
                return loop.run_until_complete(researcher_node(state, config))
            except Exception as fallback_error:
                self.logger.error(f"回退流程也失败了: {fallback_error}", exc_info=True)
                # 返回错误结果
                return Command(update={
                    "messages": state.get("messages", []),
                    "observations": [f"深度调研和标准流程都失败了: {str(e)} / {str(fallback_error)}"],
                    "task_results": [],
                    "plan_updates": []
                }, goto="research_team")

    def _extract_plan_steps(self, state: State) -> list:
        """从状态中提取计划步骤

        Args:
            state: 当前状态

        Returns:
            计划步骤列表
        """
        current_plan = state.get("current_plan")
        if not current_plan or not hasattr(current_plan, 'steps'):
            return []

        steps = []
        for step in current_plan.steps:
            if hasattr(step, 'description') and step.description:
                steps.append(step.description)
            elif hasattr(step, 'title') and step.title:
                steps.append(step.title)

        return steps

    def _convert_to_researcher_format(self, deep_output: Union[DeepResearchNodeOutputs, Dict[str, Any]]) -> Dict[str, Any]:
        """将深度调研输出转换为researcher节点格式

        Args:
            deep_output: 深度调研输出（DeepResearchNodeOutputs对象或字典）

        Returns:
            标准researcher格式输出
        """
        # 统一处理输入，支持DeepResearchNodeOutputs对象和字典
        if isinstance(deep_output, DeepResearchNodeOutputs):
            # 如果是DeepResearchNodeOutputs对象，直接访问属性
            answer = deep_output.answer
            messages = deep_output.messages
            task_results = deep_output.task_results
            plan = deep_output.plan
        else:
            # 如果是字典，通过键访问
            answer = deep_output.get("answer", "")
            messages = deep_output.get("messages", [])
            task_results = deep_output.get("task_results", [])
            plan = deep_output.get("plan", [])

        # 构建observation
        observation = answer if answer else "深度调研完成，但未生成有效答案"

        # 添加任务结果到observations
        observations = [observation]
        if task_results:
            for task_result in task_results:
                if isinstance(task_result, dict) and task_result.get("answer"):
                    observations.append(f"任务结果: {task_result['answer']}")

        # 返回标准格式
        return {
            "messages": messages,
            "observations": observations,
            "task_results": task_results,
            "plan_updates": plan,
            "deep_research_used": True,
            "deep_research_answer": answer
        }

    def set_enabled(self, enabled: bool):
        """设置是否启用深度调研

        Args:
            enabled: 是否启用
        """
        self.is_enabled = enabled
        self.logger.info(f"深度调研功能已{'启用' if enabled else '禁用'}")

    def is_deep_research_available(self) -> bool:
        """检查深度调研是否可用

        Returns:
            是否可用
        """
        return self.is_enabled and self.deep_research_node is not None


def create_deep_research_wrapper(
    config: Optional[DeepResearchConfig] = None,
    deep_research_node: Optional[DeepResearchNode] = None
) -> DeepResearchNodeWrapper:
    """创建深度调研包装器实例

    Args:
        config: 深度调研配置
        deep_research_node: 深度调研节点实例

    Returns:
        DeepResearchNodeWrapper实例
    """
    if config is None:
        config = DeepResearchConfig()

    # 如果没有提供深度调研节点且配置启用，则创建一个
    if deep_research_node is None and config.enabled:
        try:
            from src.deep_research.node import create_deep_research_node
            deep_research_node = create_deep_research_node()
        except Exception as e:
            logging.getLogger(__name__).warning(f"创建深度调研节点失败: {e}，将使用标准流程")
            config.enabled = False

    return DeepResearchNodeWrapper(
        deep_research_node=deep_research_node,
        is_enabled=config.enabled
    )
