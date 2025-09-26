"""MultiTurnReactAgent 适配实现

基于 tongyi-ds 中的 MultiTurnReactAgent，适配到 Deer Flow 项目中。
"""

import json
import json5
import os
from typing import Dict, List, Optional, Union

from qwen_agent.agents.fncall_agent import FnCallAgent
from qwen_agent.llm import BaseChatModel
from qwen_agent.llm.schema import Message
from qwen_agent.tools import BaseTool

from src.deep_research.tools import TOOL_CLASS, TOOL_MAP


class MultiTurnReactAgent(FnCallAgent):
    """多轮反应代理，支持深度调研功能"""

    def __init__(
        self,
        function_list: Optional[List[Union[str, Dict, BaseTool]]] = None,
        llm: Optional[Union[Dict, BaseChatModel]] = None,
        **kwargs
    ):
        """初始化多轮反应代理

        Args:
            function_list: 工具列表
            llm: 语言模型配置
            **kwargs: 其他参数
        """
        if llm is None:
            raise ValueError("LLM configuration is required")

        self.llm_generate_cfg = llm.get("generate_cfg", {})
        self.llm_local_path = llm["model"]
        self.function_list = function_list or [tool.name for tool in TOOL_CLASS]
        self.tool_map = TOOL_MAP

    def _run(self, input_data: Dict, model: str, max_rounds: Optional[int] = None, max_runtime_seconds: Optional[int] = None) -> Dict:
        """运行代理执行深度调研任务

        Args:
            input_data: 输入数据，包含问题和答案
            model: 模型路径
            max_rounds: 最大轮次
            max_runtime_seconds: 最大运行时间

        Returns:
            执行结果字典
        """
        # 构建消息
        messages = self._build_messages(input_data)

        # 设置运行配置
        run_cfg = {
            "max_round": max_rounds or 8,
            "max_runtime_seconds": max_runtime_seconds or 2700,
        }

        # 执行代理
        try:
            result = self.run(messages, **run_cfg)
            return self._format_result(result)
        except Exception as e:
            return {
                "prediction": f"执行失败: {str(e)}",
                "termination": "error",
                "messages": [],
                "success": False
            }

    def _build_messages(self, input_data: Dict) -> List[Message]:
        """构建输入消息列表

        Args:
            input_data: 包含question和answer的输入数据

        Returns:
            消息列表
        """
        messages = []

        # 添加系统消息
        system_message = self._get_system_message()
        if system_message:
            messages.append(Message("system", system_message))

        # 添加用户问题
        question = input_data.get("item", {}).get("question", "")
        if question:
            messages.append(Message("user", question))

        return messages

    def _get_system_message(self) -> str:
        """获取系统提示词

        Returns:
            系统提示词
        """
        return """你是一个专业的研究助手，能够使用搜索、访问网页、学术搜索和代码执行等工具来深入研究和解决问题。

你的任务是：
1. 仔细分析用户的问题
2. 制定合理的研究计划
3. 使用适当的工具收集信息
4. 分析和综合信息
5. 提供准确、全面的答案

你可以使用以下工具：
- search: 网络搜索
- visit: 访问网页
- google_scholar: 学术搜索
- PythonInterpreter: 执行Python代码

请确保你的回答：
- 基于可靠的信息来源
- 提供具体的证据和引用
- 逻辑清晰，结构合理
- 回答全面且有深度"""

    def _format_result(self, result) -> Dict:
        """格式化执行结果

        Args:
            result: 原始执行结果

        Returns:
            格式化的结果字典
        """
        if hasattr(result, 'to_dict'):
            result_dict = result.to_dict()
        elif isinstance(result, dict):
            result_dict = result
        else:
            result_dict = {"content": str(result)}

        # 提取最终答案
        prediction = ""
        messages = []

        if isinstance(result, list) and result:
            # 如果结果是消息列表
            for msg in result:
                if hasattr(msg, 'role') and msg.role == 'assistant':
                    prediction = getattr(msg, 'content', '')
                messages.append(self._message_to_dict(msg))
        elif hasattr(result, 'content'):
            # 如果是单个消息
            prediction = result.content
            messages.append(self._message_to_dict(result))
        elif isinstance(result_dict, dict) and 'content' in result_dict:
            # 如果是包含content的字典
            prediction = result_dict['content']
            messages.append(result_dict)

        return {
            "prediction": prediction,
            "termination": "success",
            "messages": messages,
            "success": True
        }

    def _message_to_dict(self, message) -> Dict:
        """将消息转换为字典格式

        Args:
            message: 消息对象

        Returns:
            消息字典
        """
        if hasattr(message, 'to_dict'):
            return message.to_dict()
        elif isinstance(message, dict):
            return message
        else:
            return {
                "role": getattr(message, 'role', 'unknown'),
                "content": getattr(message, 'content', str(message))
            }

    def call_server(self, msgs: List[Message], planning_port: int, max_tries: int = 3) -> Dict:
        """调用服务器执行推理

        Args:
            msgs: 消息列表
            planning_port: 规划端口
            max_tries: 最大重试次数

        Returns:
            推理结果
        """
        # 这里实现与服务器的通信逻辑
        # 由于架构限制，这里暂时使用本地执行
        return self._run({"item": {"question": msgs[-1].content if msgs else ""}}, self.llm_local_path)

    def custom_call_tool(self, tool_name: str, tool_args: Dict) -> Dict:
        """自定义工具调用

        Args:
            tool_name: 工具名称
            tool_args: 工具参数

        Returns:
            工具调用结果
        """
        if tool_name in TOOL_MAP:
            tool = TOOL_MAP[tool_name]
            try:
                result = tool.call(tool_args)
                return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}
        else:
            return {"success": False, "error": f"工具 {tool_name} 不存在"}


def create_multi_turn_react_agent(config) -> MultiTurnReactAgent:
    """创建多轮反应代理实例

    Args:
        config: 深度调研配置

    Returns:
        MultiTurnReactAgent实例
    """
    llm_config = {
        "model": config.model,
        "generate_cfg": {
            "max_input_tokens": 320000,
            "max_retries": 10,
            "temperature": 0.6,
            "top_p": 0.95,
            "presence_penalty": 1.1,
        },
    }

    return MultiTurnReactAgent(
        function_list=config.get_function_list(),
        llm=llm_config,
    )
