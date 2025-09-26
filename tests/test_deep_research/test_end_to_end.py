"""深度调研模块端到端测试

测试完整的深度调研流程，包括配置加载、节点创建和图集成。
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os

from src.deep_research.config import DeepResearchConfig
from src.deep_research.wrapper import create_deep_research_wrapper
from src.graph.builder import build_graph, build_graph_with_memory


class TestDeepResearchEndToEnd:
    """深度调研模块端到端测试"""

    def test_config_from_env_disabled(self):
        """测试从环境变量创建禁用的配置"""
        with patch.dict(os.environ, {
            'DEEP_RESEARCHER_ENABLE': 'false',
            'DEEPRESEARCH_MODEL': 'test-model',
            'DEEPRESEARCH_PORT': '6001',
            'DEEPRESEARCH_MAX_ROUNDS': '3',
            'DEEPRESEARCH_TIMEOUT': '60',
            'DEEPRESEARCH_RETRIES': '1'
        }):
            config = DeepResearchConfig()
            assert config.enabled is False
            assert config.model == 'test-model'
            assert config.planning_port == 6001
            assert config.max_rounds == 3
            assert config.timeout_seconds == 60
            assert config.max_retries == 1

    def test_config_from_env_enabled(self):
        """测试从环境变量创建启用的配置"""
        with patch.dict(os.environ, {
            'DEEP_RESEARCHER_ENABLE': 'true',
            'OPENROUTER_API_KEY': 'test-api-key',
            'PLANNER_MODEL': 'test-planner',
            'SYNTHESIZER_MODEL': 'test-synthesizer'
        }):
            config = DeepResearchConfig()
            assert config.enabled is True
            assert config.openrouter_api_key == 'test-api-key'
            assert config.planner_model == 'test-planner'
            assert config.synthesizer_model == 'test-synthesizer'

    def test_config_validation_success(self):
        """测试配置验证成功"""
        config = DeepResearchConfig()
        config.enabled = True
        config.openrouter_api_key = 'test-key'
        config.max_rounds = 5
        config.timeout_seconds = 120

        assert config.validate() is True

    def test_config_validation_missing_api_key(self):
        """测试配置验证失败 - 缺少API密钥"""
        config = DeepResearchConfig()
        config.enabled = True
        config.openrouter_api_key = None

        with pytest.raises(ValueError, match="OPENROUTER_API_KEY 环境变量未设置"):
            config.validate()

    def test_config_validation_invalid_max_rounds(self):
        """测试配置验证失败 - 无效的最大轮次"""
        config = DeepResearchConfig()
        config.enabled = True
        config.openrouter_api_key = 'test-key'
        config.max_rounds = 0

        with pytest.raises(ValueError, match="DEEPRESEARCH_MAX_ROUNDS 必须大于0"):
            config.validate()

    def test_config_validation_invalid_timeout(self):
        """测试配置验证失败 - 无效的超时时间"""
        config = DeepResearchConfig()
        config.enabled = True
        config.openrouter_api_key = 'test-key'
        config.timeout_seconds = -1

        with pytest.raises(ValueError, match="DEEPRESEARCH_TIMEOUT 必须大于0"):
            config.validate()

    def test_config_get_function_list(self):
        """测试获取功能列表"""
        config = DeepResearchConfig()
        functions = config.get_function_list()

        assert isinstance(functions, list)
        assert "search" in functions
        assert "visit" in functions
        assert "google_scholar" in functions
        assert "PythonInterpreter" in functions

    def test_config_create_planner(self):
        """测试创建规划器"""
        config = DeepResearchConfig()
        mock_llm = MagicMock()

        planner = config.create_planner(mock_llm)

        assert planner is not None

    def test_config_create_synthesizer(self):
        """测试创建合成器"""
        config = DeepResearchConfig()
        mock_llm = MagicMock()

        synthesizer = config.create_synthesizer(mock_llm)

        assert synthesizer is not None

    @patch('src.deep_research.wrapper.create_deep_research_node')
    def test_create_wrapper_with_enabled_config(self, mock_create_node):
        """测试使用启用配置创建包装器"""
        config = DeepResearchConfig()
        config.enabled = True

        mock_node = MagicMock()
        mock_create_node.return_value = mock_node

        wrapper = create_deep_research_wrapper(config)

        assert wrapper.is_enabled is True
        assert wrapper.deep_research_node == mock_node

    @patch('src.deep_research.wrapper.create_deep_research_node')
    def test_create_wrapper_with_disabled_config(self, mock_create_node):
        """测试使用禁用配置创建包装器"""
        config = DeepResearchConfig()
        config.enabled = False

        wrapper = create_deep_research_wrapper(config)

        assert wrapper.is_enabled is False
        assert wrapper.deep_research_node is None
        mock_create_node.assert_not_called()

    @patch('src.deep_research.wrapper.create_deep_research_node')
    def test_create_wrapper_node_creation_fails(self, mock_create_node):
        """测试创建包装器时节点创建失败"""
        config = DeepResearchConfig()
        config.enabled = True

        mock_create_node.side_effect = Exception("创建失败")

        wrapper = create_deep_research_wrapper(config)

        assert wrapper.is_enabled is False
        assert wrapper.deep_research_node is None

    @patch('src.deep_research.config.DeepResearchConfig')
    def test_build_graph_with_deep_research_enabled(self, mock_config_class):
        """测试构建启用深度调研的图"""
        mock_config = MagicMock()
        mock_config.enabled = True
        mock_config_class.return_value = mock_config

        with patch('src.graph.builder._build_graph_with_deep_research') as mock_build:
            mock_builder = MagicMock()
            mock_build.compile.return_value = "compiled_graph"
            mock_build.return_value = mock_builder

            graph = build_graph()

            assert graph == "compiled_graph"
            mock_build.assert_called_once()

    @patch('src.deep_research.config.DeepResearchConfig')
    def test_build_graph_with_deep_research_disabled(self, mock_config_class):
        """测试构建禁用深度调研的图"""
        mock_config = MagicMock()
        mock_config.enabled = False
        mock_config_class.return_value = mock_config

        with patch('src.graph.builder._build_base_graph') as mock_build:
            mock_builder = MagicMock()
            mock_builder.compile.return_value = "base_graph"
            mock_build.return_value = mock_builder

            graph = build_graph()

            assert graph == "base_graph"
            mock_build.assert_called_once()

    @patch('src.deep_research.config.DeepResearchConfig')
    def test_build_graph_with_memory_deep_research_enabled(self, mock_config_class):
        """测试构建带内存的启用深度调研的图"""
        mock_config = MagicMock()
        mock_config.enabled = True
        mock_config_class.return_value = mock_config

        with patch('src.graph.builder._build_graph_with_deep_research') as mock_build:
            mock_builder = MagicMock()
            mock_builder.compile.return_value = "compiled_graph_with_memory"
            mock_build.return_value = mock_builder

            with patch('langgraph.checkpoint.memory.MemorySaver') as mock_memory:
                mock_memory.return_value = "memory_saver"

                graph = build_graph_with_memory()

                assert graph == "compiled_graph_with_memory"
                mock_build.assert_called_once()
                mock_memory.assert_called_once()

    @patch('src.deep_research.config.DeepResearchConfig')
    def test_build_graph_with_memory_deep_research_disabled(self, mock_config_class):
        """测试构建带内存的禁用深度调研的图"""
        mock_config = MagicMock()
        mock_config.enabled = False
        mock_config_class.return_value = mock_config

        with patch('src.graph.builder._build_base_graph') as mock_build:
            mock_builder = MagicMock()
            mock_builder.compile.return_value = "base_graph_with_memory"
            mock_build.return_value = mock_builder

            with patch('langgraph.checkpoint.memory.MemorySaver') as mock_memory:
                mock_memory.return_value = "memory_saver"

                graph = build_graph_with_memory()

                assert graph == "base_graph_with_memory"
                mock_build.assert_called_once()
                mock_memory.assert_called_once()

    def test_environment_variable_loading(self):
        """测试环境变量加载"""
        test_env = {
            'DEEP_RESEARCHER_ENABLE': 'true',
            'DEEPRESEARCH_MODEL': 'custom-model',
            'DEEPRESEARCH_PORT': '8080',
            'DEEPRESEARCH_MAX_ROUNDS': '10',
            'DEEPRESEARCH_TIMEOUT': '300',
            'DEEPRESEARCH_RETRIES': '3',
            'OPENROUTER_API_KEY': 'custom-api-key',
            'OPENROUTER_BASE_URL': 'https://custom.com',
            'PLANNER_MODEL': 'custom-planner',
            'SYNTHESIZER_MODEL': 'custom-synthesizer',
            'DEEPRESEARCH_LOG_LEVEL': 'DEBUG'
        }

        with patch.dict(os.environ, test_env):
            config = DeepResearchConfig()

            assert config.enabled is True
            assert config.model == 'custom-model'
            assert config.planning_port == 8080
            assert config.max_rounds == 10
            assert config.timeout_seconds == 300
            assert config.max_retries == 3
            assert config.openrouter_api_key == 'custom-api-key'
            assert config.openrouter_base_url == 'https://custom.com'
            assert config.planner_model == 'custom-planner'
            assert config.synthesizer_model == 'custom-synthesizer'
            assert config.log_level == 'DEBUG'

    def test_config_defaults(self):
        """测试配置默认值"""
        with patch.dict(os.environ, {}, clear=True):
            config = DeepResearchConfig()

            assert config.enabled is False
            assert config.model == 'alibaba/tongyi-deepresearch-30b-a3b'
            assert config.planning_port == 6001
            assert config.max_rounds == 8
            assert config.timeout_seconds == 2700
            assert config.max_retries == 2
            assert config.openrouter_base_url == 'https://openrouter.ai/api/v1'
            assert config.planner_model == 'openai/gpt-4o'
            assert config.synthesizer_model == 'openai/gpt-4o'
            assert config.log_level == 'INFO'