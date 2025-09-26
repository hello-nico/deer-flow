"""测试深度调研工具适配功能"""

import pytest
from unittest.mock import MagicMock, patch

from src.deep_research.tools import (
    SearchTool,
    VisitTool,
    ScholarTool,
    PythonInterpreterTool,
    TOOL_CLASS,
    TOOL_MAP
)


class TestSearchTool:
    """测试搜索工具适配器"""

    def test_init(self):
        """测试初始化"""
        tool = SearchTool()
        assert tool.name == "search"
        assert tool.search_tool is not None

    def test_call_success(self):
        """测试成功调用搜索"""
        tool = SearchTool()

        # 模拟搜索工具
        mock_result = {"result": "搜索结果"}
        tool.search_tool = MagicMock()
        tool.search_tool.invoke.return_value = mock_result

        result = tool.call({"query": "测试查询"})

        tool.search_tool.invoke.assert_called_once_with({"query": "测试查询"})
        assert result == "搜索结果"

    def test_call_no_query(self):
        """测试没有查询参数"""
        tool = SearchTool()
        result = tool.call({})

        assert result == "请提供搜索查询"

    def test_call_exception(self):
        """测试搜索异常"""
        tool = SearchTool()

        tool.search_tool = MagicMock()
        tool.search_tool.invoke.side_effect = Exception("搜索错误")

        result = tool.call({"query": "测试查询"})

        assert result == "搜索失败: 搜索错误"

    def test_call_dict_result(self):
        """测试字典格式结果"""
        tool = SearchTool()

        # 模拟返回字典格式结果
        mock_result = {"items": ["结果1", "结果2"]}
        tool.search_tool = MagicMock()
        tool.search_tool.invoke.return_value = mock_result

        result = tool.call({"query": "测试查询"})

        assert result == str(mock_result)


class TestVisitTool:
    """测试网页访问工具适配器"""

    def test_init(self):
        """测试初始化"""
        tool = VisitTool()
        assert tool.name == "visit"
        assert tool.crawl_tool is not None

    def test_call_success(self):
        """测试成功访问网页"""
        tool = VisitTool()

        # 模拟爬虫工具
        mock_result = {"result": "网页内容"}
        tool.crawl_tool = MagicMock()
        tool.crawl_tool.invoke.return_value = mock_result

        result = tool.call({"url": "https://example.com"})

        tool.crawl_tool.invoke.assert_called_once_with({"url": "https://example.com"})
        assert result == "网页内容"

    def test_call_no_url(self):
        """测试没有URL参数"""
        tool = VisitTool()
        result = tool.call({})

        assert result == "请提供网页URL"

    def test_call_exception(self):
        """测试访问异常"""
        tool = VisitTool()

        tool.crawl_tool = MagicMock()
        tool.crawl_tool.invoke.side_effect = Exception("访问错误")

        result = tool.call({"url": "https://example.com"})

        assert result == "访问失败: 访问错误"


class TestScholarTool:
    """测试学术搜索工具适配器"""

    def test_init(self):
        """测试初始化"""
        tool = ScholarTool()
        assert tool.name == "google_scholar"
        assert tool.search_tool is not None

    def test_call_success(self):
        """测试成功学术搜索"""
        tool = ScholarTool()

        # 模拟搜索工具
        mock_result = {"result": "学术搜索结果"}
        tool.search_tool = MagicMock()
        tool.search_tool.invoke.return_value = mock_result

        result = tool.call({"query": "机器学习"})

        # 验证查询被添加了学术关键词
        expected_query = "机器学习 academic research scholarly"
        tool.search_tool.invoke.assert_called_once_with({"query": expected_query})
        assert result == "学术搜索结果"

    def test_call_no_query(self):
        """测试没有查询参数"""
        tool = ScholarTool()
        result = tool.call({})

        assert result == "请提供搜索查询"


class TestPythonInterpreterTool:
    """测试Python解释器工具适配器"""

    def test_init(self):
        """测试初始化"""
        tool = PythonInterpreterTool()
        assert tool.name == "PythonInterpreter"
        assert tool.python_tool is not None

    def test_call_success_with_dict(self):
        """测试使用字典参数成功调用"""
        tool = PythonInterpreterTool()

        # 模拟Python工具
        mock_result = {"result": "执行结果"}
        tool.python_tool = MagicMock()
        tool.python_tool.invoke.return_value = mock_result

        result = tool.call({"code": "print('Hello')"})
        assert result == "执行结果"

    def test_call_success_with_string(self):
        """测试使用字符串参数成功调用"""
        tool = PythonInterpreterTool()

        # 模拟Python工具
        mock_result = {"result": "执行结果"}
        tool.python_tool = MagicMock()
        tool.python_tool.invoke.return_value = mock_result

        result = tool.call("print('Hello')")
        assert result == "执行结果"

    def test_call_no_code(self):
        """测试没有代码参数"""
        tool = PythonInterpreterTool()
        result = tool.call({})

        assert result == "请提供Python代码"

    def test_call_empty_code(self):
        """测试空代码参数"""
        tool = PythonInterpreterTool()
        result = tool.call({"code": ""})

        assert result == "请提供Python代码"

    def test_call_exception(self):
        """测试代码执行异常"""
        tool = PythonInterpreterTool()

        tool.python_tool = MagicMock()
        tool.python_tool.invoke.side_effect = Exception("代码错误")

        result = tool.call({"code": "invalid code"})

        assert result == "代码执行失败: 代码错误"


class TestToolRegistration:
    """测试工具注册"""

    def test_tool_class_list(self):
        """测试工具类列表"""
        assert len(TOOL_CLASS) == 4

        tool_names = [tool.name for tool in TOOL_CLASS]
        expected_names = ["google_scholar", "visit", "search", "PythonInterpreter"]
        assert set(tool_names) == set(expected_names)

    def test_tool_map(self):
        """测试工具映射"""
        assert len(TOOL_MAP) == 4

        expected_names = ["google_scholar", "visit", "search", "PythonInterpreter"]
        assert set(TOOL_MAP.keys()) == set(expected_names)

        # 验证映射正确
        for name in expected_names:
            assert TOOL_MAP[name].name == name

    def test_tool_instances(self):
        """测试工具实例"""
        for tool in TOOL_CLASS:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'call')
            assert callable(tool.call)