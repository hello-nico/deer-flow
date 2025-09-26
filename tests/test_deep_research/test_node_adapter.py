"""DeepResearchNode和DeepResearchAdapter单元测试"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Dict, Any, List

from src.deep_research.node import DeepResearchNode, DeepResearchNodeOutputs, create_deep_research_node
from src.deep_research.adapter import DeepResearchAdapter, ResearchState, TaskResult
from src.deep_research.agent import MultiTurnReactAgent


class TestDeepResearchNode:
    """DeepResearchNode单元测试"""

    @pytest.fixture
    def mock_adapter(self):
        """创建模拟适配器"""
        adapter = MagicMock(spec=DeepResearchAdapter)
        adapter.create_executor_graph.return_value = AsyncMock()
        return adapter

    @pytest.fixture
    def mock_planner(self):
        """创建模拟规划器"""
        return AsyncMock()

    @pytest.fixture
    def mock_synthesizer(self):
        """创建模拟合成器"""
        return AsyncMock()

    @pytest.fixture
    def deep_research_node(self, mock_adapter, mock_planner, mock_synthesizer):
        """创建深度调研节点"""
        return DeepResearchNode(
            planner=mock_planner,
            synthesizer=mock_synthesizer,
            adapter=mock_adapter
        )

    def test_node_initialization(self, deep_research_node, mock_adapter, mock_planner, mock_synthesizer):
        """测试节点初始化"""
        assert deep_research_node._adapter == mock_adapter
        mock_adapter.create_executor_graph.assert_called_once_with(mock_planner, mock_synthesizer)

    @pytest.mark.asyncio
    async def test_ainvoke_with_question(self, deep_research_node):
        """测试异步调用 - 只有问题"""
        mock_graph = AsyncMock()
        mock_result = {
            "messages": [{"role": "assistant", "content": "测试答案"}],
            "plan": ["步骤1", "步骤2"],
            "task_results": []
        }
        mock_graph.ainvoke.return_value = mock_result
        deep_research_node._graph = mock_graph

        inputs = {"question": "测试问题"}
        result = await deep_research_node.ainvoke(inputs)

        assert isinstance(result, dict)
        assert "answer" in result
        assert "messages" in result
        assert "serialized_messages" in result
        assert "plan" in result
        assert "task_results" in result

    @pytest.mark.asyncio
    async def test_ainvoke_with_messages(self, deep_research_node):
        """测试异步调用 - 有消息"""
        mock_graph = AsyncMock()
        mock_result = {
            "messages": [{"role": "assistant", "content": "测试答案"}],
            "plan": ["步骤1"],
            "task_results": []
        }
        mock_graph.ainvoke.return_value = mock_result
        deep_research_node._graph = mock_graph

        inputs = {
            "question": "测试问题",
            "messages": [{"role": "user", "content": "用户消息"}]
        }
        result = await deep_research_node.ainvoke(inputs)

        assert result["answer"] == "测试答案"

    def test_invoke_with_question(self, deep_research_node):
        """测试同步调用 - 只有问题"""
        mock_graph = MagicMock()
        mock_result = {
            "messages": [{"role": "assistant", "content": "测试答案"}],
            "plan": ["步骤1"],
            "task_results": []
        }
        mock_graph.invoke.return_value = mock_result
        deep_research_node._graph = mock_graph

        inputs = {"question": "测试问题"}
        result = deep_research_node.invoke(inputs)

        assert result["answer"] == "测试答案"

    def test_invoke_with_messages(self, deep_research_node):
        """测试同步调用 - 有消息"""
        mock_graph = MagicMock()
        mock_result = {
            "messages": [{"role": "assistant", "content": "测试答案"}],
            "plan": ["步骤1"],
            "task_results": []
        }
        mock_graph.invoke.return_value = mock_result
        deep_research_node._graph = mock_graph

        inputs = {
            "question": "测试问题",
            "messages": [{"role": "user", "content": "用户消息"}]
        }
        result = deep_research_node.invoke(inputs)

        assert result["answer"] == "测试答案"

    def test_prepare_messages_empty(self, deep_research_node):
        """测试准备空消息"""
        with pytest.raises(ValueError, match="DeepResearchNode requires either 'question' or 'messages'"):
            deep_research_node._prepare_messages(None, None)

    def test_prepare_messages_base_message(self, deep_research_node):
        """测试准备BaseMessage格式的消息"""
        from langchain_core.messages import HumanMessage, AIMessage

        messages = [
            HumanMessage(content="用户消息"),
            AIMessage(content="助手消息")
        ]
        result = deep_research_node._prepare_messages("问题", messages)

        assert len(result) == 3  # 2个原有消息 + 1个问题
        assert isinstance(result[2], HumanMessage)
        assert result[2].content == "问题"

    def test_prepare_messages_dict_format(self, deep_research_node):
        """测试准备字典格式的消息"""
        messages = [
            {"role": "user", "content": "用户消息"},
            {"role": "assistant", "content": "助手消息"}
        ]
        result = deep_research_node._prepare_messages("问题", messages)

        assert len(result) == 3
        assert result[0].content == "用户消息"
        assert result[1].content == "助手消息"
        assert result[2].content == "问题"

    def test_prepare_messages_string_format(self, deep_research_node):
        """测试准备字符串格式的消息"""
        messages = ["字符串消息"]
        result = deep_research_node._prepare_messages("问题", messages)

        assert len(result) == 2
        assert result[0].content == "字符串消息"
        assert result[1].content == "问题"

    def test_extract_answer(self, deep_research_node):
        """测试从消息中提取答案"""
        from langchain_core.messages import HumanMessage, AIMessage

        messages = [
            HumanMessage(content="用户消息"),
            AIMessage(content="这是答案")
        ]
        answer = deep_research_node._extract_answer(messages)

        assert answer == "这是答案"

    def test_extract_answer_no_ai_message(self, deep_research_node):
        """测试没有AI消息时提取答案"""
        from langchain_core.messages import HumanMessage

        messages = [
            HumanMessage(content="用户消息")
        ]
        answer = deep_research_node._extract_answer(messages)

        assert answer == ""

    def test_serialize_messages(self, deep_research_node):
        """测试序列化消息"""
        from langchain_core.messages import HumanMessage

        message = HumanMessage(content="测试消息")
        serialized = deep_research_node._serialize_messages([message])

        assert len(serialized) == 1
        assert isinstance(serialized[0], dict)

    @patch('src.deep_research.node.DeepResearchConfig')
    @patch('src.deep_research.node.create_multi_turn_react_agent')
    @patch('langchain_openai.ChatOpenAI')
    def test_create_deep_research_node(self, mock_chat_openai, mock_create_agent, mock_config_class):
        """测试创建深度调研节点"""
        mock_config = MagicMock()
        mock_config.enabled = True
        mock_config.openrouter_base_url = "https://test.com"
        mock_config.openrouter_api_key = "test-key"
        mock_config.planner_model = "test-planner"
        mock_config.synthesizer_model = "test-synthesizer"
        mock_config.model = "test-model"
        mock_config.planning_port = 6001
        mock_config.max_rounds = 8
        mock_config.timeout_seconds = 2700
        mock_config.max_retries = 2
        mock_config.create_planner.return_value = "planner"
        mock_config.create_synthesizer.return_value = "synthesizer"
        mock_config_class.return_value = mock_config

        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm
        mock_agent = MagicMock()
        mock_create_agent.return_value = mock_agent

        node = create_deep_research_node()

        assert isinstance(node, DeepResearchNode)


class TestDeepResearchAdapter:
    """DeepResearchAdapter单元测试"""

    @pytest.fixture
    def mock_agent(self):
        """创建模拟代理"""
        agent = MagicMock(spec=MultiTurnReactAgent)
        agent._run.return_value = {
            "prediction": "测试答案",
            "termination": "success",
            "messages": [{"role": "assistant", "content": "测试答案"}]
        }
        return agent

    @pytest.fixture
    def adapter(self, mock_agent):
        """创建适配器"""
        return DeepResearchAdapter(
            agent=mock_agent,
            model="test-model",
            planning_port=6001,
            max_rounds=3,
            timeout_seconds=60,
            max_retries=2
        )

    def test_adapter_initialization(self, adapter, mock_agent):
        """测试适配器初始化"""
        assert adapter.agent == mock_agent
        assert adapter.model == "test-model"
        assert adapter.planning_port == 6001
        assert adapter.max_rounds == 3
        assert adapter.timeout_seconds == 60
        assert adapter.max_retries == 2

    def test_invoke_with_plan(self, adapter):
        """测试调用 - 有计划"""
        state = ResearchState(
            messages=[],
            plan=["任务1", "任务2"],
            current_task_index=0,
            task_results=[],
            executor_ready=False,
            active_task_index=None
        )

        result = adapter.invoke(state)

        assert isinstance(result, dict)
        assert "messages" in result
        assert "task_results" in result
        assert "current_task_index" in result
        assert "executor_ready" in result

    def test_invoke_plan_complete(self, adapter):
        """测试调用 - 计划完成"""
        state = ResearchState(
            messages=[],
            plan=["任务1"],
            current_task_index=1,  # 超出计划范围
            task_results=[],
            executor_ready=False,
            active_task_index=None
        )

        result = adapter.invoke(state)

        assert result["executor_ready"] is False
        adapter.agent._run.assert_not_called()

    def test_invoke_retry_mechanism(self, adapter):
        """测试重试机制"""
        adapter.agent._run.side_effect = [
            Exception("第一次失败"),
            {"prediction": "重试成功", "termination": "success", "messages": []}
        ]

        state = ResearchState(
            messages=[],
            plan=["任务1"],
            current_task_index=0,
            task_results=[],
            executor_ready=False,
            active_task_index=None
        )

        result = adapter.invoke(state)

        assert adapter.agent._run.call_count == 2

    def test_invoke_all_retries_fail(self, adapter):
        """测试所有重试都失败"""
        adapter.agent._run.side_effect = Exception("总是失败")

        state = ResearchState(
            messages=[],
            plan=["任务1"],
            current_task_index=0,
            task_results=[],
            executor_ready=False,
            active_task_index=None
        )

        result = adapter.invoke(state)

        assert "messages" in result
        assert result["task_results"][0]["status"] == "failed"

    def test_convert_messages(self, adapter):
        """测试消息转换"""
        messages = [
            {"role": "system", "content": "系统消息"},
            {"role": "user", "content": "用户消息"},
            {"role": "assistant", "content": "助手消息"}
        ]

        converted = adapter._convert_messages(messages)

        # 应该跳过系统消息，只转换用户和助手消息
        assert len(converted) == 2

    def test_convert_assistant_message_with_tool_calls(self, adapter):
        """测试转换包含工具调用的助手消息"""
        content = """
        <think>思考过程</think>
        <answer>答案</answer>
        <invoke>
        {"name": "search", "arguments": {"query": "测试"}}
        </invoke>
        """

        result = adapter._convert_assistant_message(content)

        assert result.content == "答案"
        assert "thought" in result.additional_kwargs
        assert len(result.tool_calls) == 1

    def test_convert_assistant_message_with_code(self, adapter):
        """测试转换包含代码的助手消息"""
        content = """
        <think>思考过程</think>
        <answer>答案</answer>
        <invoke>
        <code>print("Hello, World!")</code>
        </invoke>
        """

        result = adapter._convert_assistant_message(content)

        assert result.content == "答案"
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["name"] == "python"

    def test_strip_visible_text(self, adapter):
        """测试提取可见文本"""
        content = "普通文本<think>隐藏内容</think>更多文本<answer>答案</answer>"
        result = adapter._strip_visible_text(content)

        assert "think" not in result
        assert "answer" not in result
        assert "普通文本" in result
        assert "更多文本" in result

    def test_strip_tag(self, adapter):
        """测试提取标签内容"""
        content = "<think>思考内容</think>"
        result = adapter._strip_tag(content, "think")

        assert result == "思考内容"

    def test_strip_tag_not_found(self, adapter):
        """测试标签未找到的情况"""
        content = "没有标签的内容"
        result = adapter._strip_tag(content, "think")

        assert result == ""

    def test_parse_tool_call_json(self, adapter):
        """测试解析JSON格式的工具调用"""
        block = '{"name": "search", "arguments": {"query": "测试"}}'
        result = adapter._parse_tool_call(block)

        assert result["name"] == "search"
        assert result["arguments"]["query"] == "测试"

    def test_parse_tool_call_invalid_json(self, adapter):
        """测试解析无效JSON的工具调用"""
        block = "无效的JSON内容"
        result = adapter._parse_tool_call(block)

        assert result["name"] == "unknown"
        assert "raw" in result["arguments"]

    def test_collect_tool_calls(self, adapter):
        """测试收集工具调用"""
        from langchain_core.messages import AIMessage

        message = AIMessage(
            content="测试",
            tool_calls=[
                {"id": "1", "name": "search", "args": {"query": "测试"}},
                {"id": "2", "name": "visit", "args": {"url": "http://test.com"}}
            ]
        )

        tool_calls = adapter._collect_tool_calls([message])

        assert len(tool_calls) == 2
        assert tool_calls[0]["name"] == "search"
        assert tool_calls[1]["name"] == "visit"

    def test_create_executor_graph(self, adapter):
        """测试创建执行图"""
        mock_planner = MagicMock()
        mock_synthesizer = MagicMock()

        graph = adapter.create_executor_graph(mock_planner, mock_synthesizer)

        assert graph is not None