"""深度调研工具适配

将 Deer Flow 现有工具适配为 DeepResearch 可以使用的格式。
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Union

from src.tools.search import get_web_search_tool
from src.tools.crawl import crawl_tool
from src.tools.python_repl import python_repl_tool


class ScholarTool:
    """学术搜索工具适配器"""

    def __init__(self):
        self.name = "google_scholar"
        self.search_tool = get_web_search_tool(max_search_results=10)
        self.logger = logging.getLogger(__name__)

    def call(self, params: Dict[str, Any], **kwargs) -> str:
        """执行学术搜索"""
        query = params.get("query", "")
        if not query:
            return "请提供搜索查询"

        # 添加学术搜索关键词
        academic_query = f"{query} academic research scholarly"
        try:
            self.logger.info(f"执行学术搜索: {academic_query}")
            result = self.search_tool.invoke({"query": academic_query})
            return result.get("result", "") or str(result)
        except Exception as e:
            self.logger.error(f"学术搜索失败: {e}")
            return f"搜索失败: {str(e)}"


class SearchTool:
    """网络搜索工具适配器"""

    def __init__(self):
        self.name = "search"
        self.search_tool = get_web_search_tool(max_search_results=10)
        self.logger = logging.getLogger(__name__)

    def call(self, params: Dict[str, Any], **kwargs) -> str:
        """执行网络搜索"""
        query = params.get("query", "")
        if not query:
            return "请提供搜索查询"

        try:
            self.logger.info(f"执行网络搜索: {query}")
            result = self.search_tool.invoke({"query": query})
            return result.get("result", "") or str(result)
        except Exception as e:
            self.logger.error(f"网络搜索失败: {e}")
            return f"搜索失败: {str(e)}"


class VisitTool:
    """网页访问工具适配器"""

    def __init__(self):
        self.name = "visit"
        self.crawl_tool = crawl_tool
        self.logger = logging.getLogger(__name__)

    def call(self, params: Dict[str, Any], **kwargs) -> str:
        """访问网页"""
        url = params.get("url", "")
        if not url:
            return "请提供网页URL"

        try:
            self.logger.info(f"访问网页: {url}")
            result = self.crawl_tool.invoke({"url": url})
            return result.get("result", "") or str(result)
        except Exception as e:
            self.logger.error(f"网页访问失败: {e}")
            return f"访问失败: {str(e)}"


class PythonInterpreterTool:
    """Python代码执行工具适配器"""

    def __init__(self):
        self.name = "PythonInterpreter"
        self.python_tool = python_repl_tool
        self.logger = logging.getLogger(__name__)

    def call(self, params: Union[str, Dict[str, Any]], **kwargs) -> str:
        """执行Python代码"""
        if isinstance(params, str):
            code = params
        else:
            code = params.get("code", "")

        if not code:
            return "请提供Python代码"

        try:
            self.logger.info("执行Python代码")
            result = self.python_tool.invoke({"code": code})
            return result.get("result", "") or str(result)
        except Exception as e:
            self.logger.error(f"Python代码执行失败: {e}")
            return f"代码执行失败: {str(e)}"


# 创建工具实例
TOOL_CLASS = [
    ScholarTool(),
    VisitTool(),
    SearchTool(),
    PythonInterpreterTool(),
]

TOOL_MAP = {tool.name: tool for tool in TOOL_CLASS}