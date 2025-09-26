"""测试深度调研包装器功能"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.deep_research.wrapper import DeepResearchNodeWrapper, create_deep_research_wrapper
from src.deep_research.config import DeepResearchConfig
from src.deep_research.node import DeepResearchNode, DeepResearchNodeOutputs
from src.graph.types import State


class TestDeepResearchNodeWrapper:
    """测试深度调研包装器"""

    def test_init_disabled(self):
        """测试初始化禁用状态的包装器"""
        wrapper = DeepResearchNodeWrapper(is_enabled=False)

        assert wrapper.is_enabled is False
        assert wrapper.deep_research_node is None

    def test_init_enabled_with_node(self):
        """测试初始化启用状态的包装器"""
        mock_node = MagicMock(spec=DeepResearchNode)
        wrapper = DeepResearchNodeWrapper(deep_research_node=mock_node, is_enabled=True)

        assert wrapper.is_enabled is True
        assert wrapper.deep_research_node is mock_node

    @pytest.mark.asyncio
    async def test_ainvoke_disabled(self):
        """测试禁用状态下的异步调用"""
        wrapper = DeepResearchNodeWrapper(is_enabled=False)
        mock_state = MagicMock(spec=State)
        mock_config = MagicMock()

        with patch('src.deep_research.wrapper.researcher_node', new_callable=AsyncMock) as mock_researcher:
            result = await wrapper.ainvoke(mock_state, mock_config)

            mock_researcher.assert_called_once_with(mock_state, mock_config)
            assert result is not None

    @pytest.mark.asyncio
    async def test_ainvoke_enabled_no_node(self):
        """测试启用状态但没有节点的异步调用"""
        wrapper = DeepResearchNodeWrapper(is_enabled=True)
        mock_state = MagicMock(spec=State)
        mock_config = MagicMock()

        with patch('src.deep_research.wrapper.researcher_node', new_callable=AsyncMock) as mock_researcher:
            result = await wrapper.ainvoke(mock_state, mock_config)

            mock_researcher.assert_called_once_with(mock_state, mock_config)
            assert result is not None

    @pytest.mark.asyncio
    async def test_ainvoke_enabled_success(self):
        """测试启用状态成功调用"""
        # 创建模拟输出
        mock_output = DeepResearchNodeOutputs(
            answer="测试答案",
            messages=[],
            serialized_messages=[],
            plan=["步骤1", "步骤2"],
            task_results=[{"task": "测试任务", "answer": "任务结果"}]
        )

        # 创建模拟节点
        mock_node = MagicMock(spec=DeepResearchNode)
        mock_node.ainvoke.return_value = mock_output

        wrapper = DeepResearchNodeWrapper(deep_research_node=mock_node, is_enabled=True)

        # 创建模拟状态
        mock_plan = MagicMock()
        mock_plan.steps = [
            MagicMock(description="步骤1"),
            MagicMock(description="步骤2")
        ]
        mock_state = MagicMock(spec=State)
        mock_state.get.side_effect = lambda key, default=None: {
            "research_topic": "测试主题",
            "messages": [],
            "task_results": [],
            "current_plan": mock_plan
        }.get(key, default)

        mock_config = MagicMock()

        result = await wrapper.ainvoke(mock_state, mock_config)

        # 验证节点被调用
        mock_node.ainvoke.assert_called_once()
        assert result["observations"] == ["测试答案", "任务结果: 任务结果"]
        assert result["deep_research_used"] is True
        assert result["deep_research_answer"] == "测试答案"

    @pytest.mark.asyncio
    async def test_ainvoke_enabled_failure(self):
        """测试启用状态但调用失败"""
        # 创建模拟节点
        mock_node = MagicMock(spec=DeepResearchNode)
        mock_node.ainvoke.side_effect = Exception("测试错误")

        wrapper = DeepResearchNodeWrapper(deep_research_node=mock_node, is_enabled=True)

        mock_state = MagicMock(spec=State)
        mock_config = MagicMock()

        with patch('src.deep_research.wrapper.researcher_node', new_callable=AsyncMock) as mock_researcher:
            result = await wrapper.ainvoke(mock_state, mock_config)

            # 验证回退到标准流程
            mock_researcher.assert_called_once_with(mock_state, mock_config)

    def test_invoke_disabled(self):
        """测试禁用状态下的同步调用"""
        wrapper = DeepResearchNodeWrapper(is_enabled=False)
        mock_state = MagicMock(spec=State)
        mock_config = MagicMock()

        with patch('src.deep_research.wrapper.researcher_node') as mock_researcher:
            result = wrapper.invoke(mock_state, mock_config)

            mock_researcher.assert_called_once_with(mock_state, mock_config)
            assert result is not None

    def test_invoke_enabled_success(self):
        """测试启用状态成功调用"""
        # 创建模拟输出
        mock_output = DeepResearchNodeOutputs(
            answer="测试答案",
            messages=[],
            serialized_messages=[],
            plan=["步骤1"],
            task_results=[]
        )

        # 创建模拟节点
        mock_node = MagicMock(spec=DeepResearchNode)
        mock_node.invoke.return_value = mock_output

        wrapper = DeepResearchNodeWrapper(deep_research_node=mock_node, is_enabled=True)

        mock_state = MagicMock(spec=State)
        mock_state.get.side_effect = lambda key, default=None: {
            "research_topic": "测试主题",
            "messages": [],
            "task_results": [],
            "current_plan": None
        }.get(key, default)

        mock_config = MagicMock()

        result = wrapper.invoke(mock_state, mock_config)

        # 验证节点被调用
        mock_node.invoke.assert_called_once()
        assert result["observations"] == ["测试答案"]
        assert result["deep_research_used"] is True

    def test_extract_plan_steps(self):
        """测试提取计划步骤"""
        wrapper = DeepResearchNodeWrapper()

        # 创建模拟计划
        mock_step1 = MagicMock()
        mock_step1.description = "步骤1描述"
        mock_step2 = MagicMock()
        mock_step2.title = "步骤2标题"
        mock_step3 = MagicMock()
        mock_step3.description = None
        mock_step3.title = None

        mock_plan = MagicMock()
        mock_plan.steps = [mock_step1, mock_step2, mock_step3]

        mock_state = MagicMock(spec=State)
        mock_state.get.return_value = mock_plan

        steps = wrapper._extract_plan_steps(mock_state)

        assert steps == ["步骤1描述", "步骤2标题"]

    def test_extract_plan_steps_no_plan(self):
        """测试没有计划时的步骤提取"""
        wrapper = DeepResearchNodeWrapper()

        mock_state = MagicMock(spec=State)
        mock_state.get.return_value = None

        steps = wrapper._extract_plan_steps(mock_state)

        assert steps == []

    def test_convert_to_researcher_format(self):
        """测试转换为researcher格式"""
        wrapper = DeepResearchNodeWrapper()

        # 创建模拟输出
        mock_output = DeepResearchNodeOutputs(
            answer="主要答案",
            messages=[],
            serialized_messages=[],
            plan=["计划步骤"],
            task_results=[
                {"task": "任务1", "answer": "结果1"},
                {"task": "任务2", "answer": "结果2"}
            ]
        )

        result = wrapper._convert_to_researcher_format(mock_output)

        assert result["observations"] == ["主要答案", "任务结果: 结果1", "任务结果: 结果2"]
        assert result["deep_research_used"] is True
        assert result["deep_research_answer"] == "主要答案"

    def test_set_enabled(self):
        """测试设置启用状态"""
        wrapper = DeepResearchNodeWrapper()
        wrapper.set_enabled(True)

        assert wrapper.is_enabled is True

        wrapper.set_enabled(False)
        assert wrapper.is_enabled is False

    def test_is_deep_research_available(self):
        """测试检查深度调研可用性"""
        wrapper = DeepResearchNodeWrapper()
        assert wrapper.is_deep_research_available() is False

        wrapper.set_enabled(True)
        assert wrapper.is_deep_research_available() is False

        mock_node = MagicMock(spec=DeepResearchNode)
        wrapper.deep_research_node = mock_node
        assert wrapper.is_deep_research_available() is True


class TestCreateDeepResearchWrapper:
    """测试创建深度调研包装器函数"""

    def test_create_disabled(self):
        """测试创建禁用的包装器"""
        config = DeepResearchConfig()
        config.enabled = False

        wrapper = create_deep_research_wrapper(config)

        assert wrapper.is_enabled is False
        assert wrapper.deep_research_node is None

    @patch.dict(os.environ, {
        "DEEP_RESEARCHER_ENABLE": "true",
        "OPENROUTER_API_KEY": "test-api-key"
    })
    def test_create_enabled_success(self):
        """测试成功创建启用的包装器"""
        config = DeepResearchConfig()

        # 这里会尝试创建节点，但由于缺少真实的LLM配置，可能会失败
        # 但包装器应该仍然被创建
        wrapper = create_deep_research_wrapper(config)

        assert isinstance(wrapper, DeepResearchNodeWrapper)
        # 由于创建节点可能失败，deep_research_node可能为None
        # 但is_enabled应该反映配置状态
        assert wrapper.is_enabled is True

    def test_create_with_existing_node(self):
        """测试使用现有节点创建包装器"""
        config = DeepResearchConfig()
        mock_node = MagicMock(spec=DeepResearchNode)

        wrapper = create_deep_research_wrapper(config, mock_node)

        assert wrapper.deep_research_node is mock_node
        assert wrapper.is_enabled is config.enabled