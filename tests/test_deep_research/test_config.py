"""测试深度调研配置功能"""

import os
import pytest
from unittest.mock import patch

from src.deep_research.config import DeepResearchConfig


class TestDeepResearchConfig:
    """测试深度调研配置类"""

    def test_default_config(self):
        """测试默认配置"""
        config = DeepResearchConfig()

        # 检查默认值
        assert config.enabled is False
        assert config.model == "alibaba/tongyi-deepresearch-30b-a3b"
        assert config.planning_port == 6001
        assert config.max_rounds == 8
        assert config.timeout_seconds == 2700
        assert config.max_retries == 2
        assert config.planner_model == "openai/gpt-4o"
        assert config.synthesizer_model == "openai/gpt-4o"

    @patch.dict(os.environ, {
        "DEEP_RESEARCHER_ENABLE": "true",
        "DEEPRESEARCH_MODEL": "test-model",
        "DEEPRESEARCH_PORT": "7001",
        "DEEPRESEARCH_MAX_ROUNDS": "10",
        "DEEPRESEARCH_TIMEOUT": "3600",
        "DEEPRESEARCH_RETRIES": "3",
        "OPENROUTER_API_KEY": "test-api-key",
        "PLANNER_MODEL": "test-planner",
        "SYNTHESIZER_MODEL": "test-synthesizer"
    })
    def test_env_config(self):
        """测试环境变量配置"""
        config = DeepResearchConfig()

        assert config.enabled is True
        assert config.model == "test-model"
        assert config.planning_port == 7001
        assert config.max_rounds == 10
        assert config.timeout_seconds == 3600
        assert config.max_retries == 3
        assert config.openrouter_api_key == "test-api-key"
        assert config.planner_model == "test-planner"
        assert config.synthesizer_model == "test-synthesizer"

    def test_validate_success(self):
        """测试配置验证成功"""
        config = DeepResearchConfig()
        config.enabled = False

        # 未启用时应该验证通过
        assert config.validate() is True

    @patch.dict(os.environ, {
        "DEEP_RESEARCHER_ENABLE": "true",
        "OPENROUTER_API_KEY": "test-api-key"
    })
    def test_validate_enabled_success(self):
        """测试启用时配置验证成功"""
        config = DeepResearchConfig()

        assert config.validate() is True

    @patch.dict(os.environ, {
        "DEEP_RESEARCHER_ENABLE": "true",
        "OPENROUTER_API_KEY": ""  # 设置为空字符串
    })
    def test_validate_missing_api_key(self):
        """测试缺少API密钥时的验证"""
        config = DeepResearchConfig()

        with pytest.raises(ValueError, match="OPENROUTER_API_KEY 环境变量未设置"):
            config.validate()

    @patch.dict(os.environ, {
        "DEEP_RESEARCHER_ENABLE": "true",
        "OPENROUTER_API_KEY": "test-api-key",
        "DEEPRESEARCH_MAX_ROUNDS": "0"
    })
    def test_validate_invalid_max_rounds(self):
        """测试无效的最大轮次数"""
        config = DeepResearchConfig()

        with pytest.raises(ValueError, match="DEEPRESEARCH_MAX_ROUNDS 必须大于0"):
            config.validate()

    @patch.dict(os.environ, {
        "DEEP_RESEARCHER_ENABLE": "true",
        "OPENROUTER_API_KEY": "test-api-key",
        "DEEPRESEARCH_TIMEOUT": "0"
    })
    def test_validate_invalid_timeout(self):
        """测试无效的超时时间"""
        config = DeepResearchConfig()

        with pytest.raises(ValueError, match="DEEPRESEARCH_TIMEOUT 必须大于0"):
            config.validate()

    def test_get_function_list(self):
        """测试获取工具列表"""
        config = DeepResearchConfig()
        functions = config.get_function_list()

        expected_functions = ["search", "visit", "google_scholar", "PythonInterpreter"]
        assert functions == expected_functions

    def test_create_planner(self):
        """测试创建规划器"""
        config = DeepResearchConfig()

        # 创建模拟LLM - 需要是可调用的
        class MockLLM:
            def __init__(self):
                self.temperature = 0
                self.timeout = 120

            def __call__(self, messages):
                return "Mock response"

        mock_llm = MockLLM()
        planner = config.create_planner(mock_llm)

        assert planner is not None

    def test_create_synthesizer(self):
        """测试创建合成器"""
        config = DeepResearchConfig()

        # 创建模拟LLM - 需要是可调用的
        class MockLLM:
            def __init__(self):
                self.temperature = 0.2
                self.timeout = 120

            def __call__(self, messages):
                return "Mock response"

        mock_llm = MockLLM()
        synthesizer = config.create_synthesizer(mock_llm)

        assert synthesizer is not None

    def test_from_env_classmethod(self):
        """测试从环境变量创建配置的类方法"""
        config = DeepResearchConfig.from_env()

        assert isinstance(config, DeepResearchConfig)
        assert config.enabled is False  # 默认值