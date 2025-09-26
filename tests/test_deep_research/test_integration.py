"""深度调研模块集成测试

测试DeepResearchNode、DeepResearchAdapter和包装器的完整集成。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from src.deep_research.node import DeepResearchNode, DeepResearchNodeOutputs
from src.deep_research.adapter import DeepResearchAdapter
from src.deep_research.wrapper import DeepResearchNodeWrapper, create_deep_research_wrapper
from src.deep_research.config import DeepResearchConfig
from src.deep_research.agent import MultiTurnReactAgent


class TestDeepResearchIntegration:
    """深度调研模块集成测试"""

    @pytest.fixture
    def mock_config(self):
        """创建模拟配置"""
        config = MagicMock(spec=DeepResearchConfig)
        config.enabled = True
        config.model = "test-model"
        config.planning_port = 6001
        config.max_rounds = 3
        config.timeout_seconds = 60
        config.max_retries = 1
        config.openrouter_api_key = "test-key"
        config.openrouter_base_url = "https://test.com"
        config.planner_model = "test-planner"
        config.synthesizer_model = "test-synthesizer"
        return config

    @pytest.fixture
    def mock_agent(self):
        """创建模拟代理"""
        agent = MagicMock(spec=MultiTurnReactAgent)
        agent._run = MagicMock(return_value={
            "prediction": "测试答案",
            "termination": "success",
            "messages": [{"role": "assistant", "content": "测试答案"}],
            "success": True
        })
        return agent

    @pytest.fixture
    def mock_planner(self):
        """创建模拟规划器"""
        planner = AsyncMock()
        planner.invoke = MagicMock(return_value='{"steps": ["步骤1", "步骤2"]}')
        return planner

    @pytest.fixture
    def mock_synthesizer(self):
        """创建模拟合成器"""
        synthesizer = AsyncMock()
        synthesizer.invoke = MagicMock(return_value="综合结果")
        return synthesizer

    @pytest.fixture
    def deep_research_adapter(self, mock_agent):
        """创建深度调研适配器"""
        return DeepResearchAdapter(
            agent=mock_agent,
            model="test-model",
            planning_port=6001,
            max_rounds=3,
            timeout_seconds=60
        )

    @pytest.fixture
    def deep_research_node(self, deep_research_adapter, mock_planner, mock_synthesizer):
        """创建深度调研节点"""
        return DeepResearchNode(
            planner=mock_planner,
            synthesizer=mock_synthesizer,
            adapter=deep_research_adapter
        )

    @pytest.fixture
    def deep_research_wrapper(self, deep_research_node):
        """创建深度调研包装器"""
        return DeepResearchNodeWrapper(
            deep_research_node=deep_research_node,
            is_enabled=True
        )

    @pytest.mark.asyncio
    async def test_deep_research_node_ainvoke(self, deep_research_node):
        """测试深度调研节点的异步调用"""
        inputs = {
            "question": "测试问题",
            "messages": [],
            "plan": ["步骤1", "步骤2"],
            "task_results": []
        }

        result = await deep_research_node.ainvoke(inputs)

        assert isinstance(result, dict)
        assert "answer" in result
        assert "messages" in result
        assert "serialized_messages" in result
        assert "plan" in result
        assert "task_results" in result

    def test_deep_research_node_invoke(self, deep_research_node):
        """测试深度调研节点的同步调用"""
        inputs = {
            "question": "测试问题",
            "messages": [],
            "plan": ["步骤1", "步骤2"],
            "task_results": []
        }

        result = deep_research_node.invoke(inputs)

        assert isinstance(result, dict)
        assert "answer" in result
        assert "messages" in result
        assert "serialized_messages" in result
        assert "plan" in result
        assert "task_results" in result

    @pytest.mark.asyncio
    async def test_deep_research_wrapper_ainvoke_enabled(self, deep_research_wrapper):
        """测试启用状态下的包装器异步调用"""
        state = {
            "research_topic": "测试主题",
            "messages": [],
            "current_plan": MagicMock(steps=[MagicMock(description="步骤1"), MagicMock(description="步骤2")]),
            "task_results": []
        }

        result = await deep_research_wrapper.ainvoke(state, {})

        assert isinstance(result, dict)
        assert "messages" in result
        assert "observations" in result
        assert "task_results" in result
        assert "plan_updates" in result
        assert "deep_research_used" in result
        assert result["deep_research_used"] is True

    @pytest.mark.asyncio
    async def test_deep_research_wrapper_ainvoke_disabled(self):
        """测试禁用状态下的包装器异步调用"""
        wrapper = DeepResearchNodeWrapper(is_enabled=False)

        state = {
            "research_topic": "测试主题",
            "messages": [],
            "current_plan": MagicMock(steps=[MagicMock(description="步骤1")]),
            "task_results": []
        }

        with patch('src.deep_research.wrapper.researcher_node') as mock_researcher:
            mock_researcher.return_value = {"test": "result"}
            result = await wrapper.ainvoke(state, {})

        assert result == {"test": "result"}

    def test_deep_research_wrapper_invoke_enabled(self, deep_research_wrapper):
        """测试启用状态下的包装器同步调用"""
        state = {
            "research_topic": "测试主题",
            "messages": [],
            "current_plan": MagicMock(steps=[MagicMock(description="步骤1"), MagicMock(description="步骤2")]),
            "task_results": []
        }

        result = deep_research_wrapper.invoke(state, {})

        assert isinstance(result, dict)
        assert "messages" in result
        assert "observations" in result
        assert "task_results" in result
        assert "plan_updates" in result
        assert "deep_research_used" in result
        assert result["deep_research_used"] is True

    def test_deep_research_wrapper_invoke_disabled(self):
        """测试禁用状态下的包装器同步调用"""
        wrapper = DeepResearchNodeWrapper(is_enabled=False)

        state = {
            "research_topic": "测试主题",
            "messages": [],
            "current_plan": MagicMock(steps=[MagicMock(description="步骤1")]),
            "task_results": []
        }

        with patch('src.deep_research.wrapper.researcher_node') as mock_researcher:
            mock_researcher.return_value = {"test": "result"}
            result = wrapper.invoke(state, {})

        assert result == {"test": "result"}

    def test_wrapper_set_enabled(self, deep_research_wrapper):
        """测试设置启用状态"""
        deep_research_wrapper.set_enabled(False)
        assert deep_research_wrapper.is_enabled is False

        deep_research_wrapper.set_enabled(True)
        assert deep_research_wrapper.is_enabled is True

    def test_wrapper_is_deep_research_available(self, deep_research_wrapper):
        """测试检查深度调研可用性"""
        # 启用状态且有节点
        assert deep_research_wrapper.is_deep_research_available() is True

        # 禁用状态
        deep_research_wrapper.set_enabled(False)
        assert deep_research_wrapper.is_deep_research_available() is False

        # 启用状态但无节点
        wrapper = DeepResearchNodeWrapper(deep_research_node=None, is_enabled=True)
        assert wrapper.is_deep_research_available() is False

    def test_extract_plan_steps(self, deep_research_wrapper):
        """测试提取计划步骤"""
        # 测试有description的情况
        step1 = MagicMock()
        step1.description = "步骤1描述"
        step2 = MagicMock()
        step2.description = "步骤2描述"

        current_plan = MagicMock()
        current_plan.steps = [step1, step2]

        state = {"current_plan": current_plan}
        steps = deep_research_wrapper._extract_plan_steps(state)

        assert steps == ["步骤1描述", "步骤2描述"]

        # 测试无current_plan的情况
        state = {}
        steps = deep_research_wrapper._extract_plan_steps(state)
        assert steps == []

    def test_convert_to_researcher_format(self, deep_research_wrapper):
        """测试转换为researcher格式"""
        deep_output = DeepResearchNodeOutputs(
            answer="测试答案",
            messages=[],
            serialized_messages=[],
            plan=["步骤1", "步骤2"],
            task_results=[
                {"answer": "任务1结果", "task": "任务1"},
                {"answer": "任务2结果", "task": "任务2"}
            ]
        )

        result = deep_research_wrapper._convert_to_researcher_format(deep_output)

        assert "messages" in result
        assert "observations" in result
        assert "task_results" in result
        assert "plan_updates" in result
        assert "deep_research_used" in result
        assert "deep_research_answer" in result

        assert result["deep_research_used"] is True
        assert result["deep_research_answer"] == "测试答案"
        assert len(result["observations"]) == 3  # 答案 + 2个任务结果

    @patch('src.deep_research.wrapper.create_deep_research_node')
    @patch('src.deep_research.wrapper.DeepResearchConfig')
    def test_create_deep_research_wrapper_with_config(self, mock_config_class, mock_create_node):
        """测试使用配置创建包装器"""
        mock_config = MagicMock()
        mock_config.enabled = True
        mock_config_class.return_value = mock_config

        mock_node = MagicMock()
        mock_create_node.return_value = mock_node

        wrapper = create_deep_research_wrapper(mock_config)

        assert isinstance(wrapper, DeepResearchNodeWrapper)
        assert wrapper.deep_research_node == mock_node
        assert wrapper.is_enabled is True

    @patch('src.deep_research.wrapper.create_deep_research_node')
    @patch('src.deep_research.wrapper.DeepResearchConfig')
    def test_create_deep_research_wrapper_disabled(self, mock_config_class, mock_create_node):
        """测试创建禁用的包装器"""
        mock_config = MagicMock()
        mock_config.enabled = False
        mock_config_class.return_value = mock_config

        wrapper = create_deep_research_wrapper(mock_config)

        assert isinstance(wrapper, DeepResearchNodeWrapper)
        assert wrapper.deep_research_node is None
        assert wrapper.is_enabled is False

    @patch('src.deep_research.wrapper.create_deep_research_node')
    @patch('src.deep_research.wrapper.DeepResearchConfig')
    def test_create_deep_research_wrapper_node_creation_fails(self, mock_config_class, mock_create_node):
        """测试创建节点失败的情况"""
        mock_config = MagicMock()
        mock_config.enabled = True
        mock_config_class.return_value = mock_config

        mock_create_node.side_effect = Exception("创建失败")

        wrapper = create_deep_research_wrapper(mock_config)

        assert isinstance(wrapper, DeepResearchNodeWrapper)
        assert wrapper.deep_research_node is None
        assert wrapper.is_enabled is False
        mock_config.enabled = False