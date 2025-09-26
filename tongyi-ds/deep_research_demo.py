#!/usr/bin/env python3
"""
DeepResearch Demo示例
展示如何使用DeepResearch进行深度研究任务

该示例展示了DeepResearch的核心功能：
1. 基于ReAct模式的研究推理
2. 多轮对话和工具调用
3. 集成多种工具（搜索、访问网页、学术论文、代码执行、文件解析）
"""

import json
import os
import sys
from typing import Dict, List, Optional

# 添加父目录到路径以便导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inference.react_agent import MultiTurnReactAgent


class DeepResearchDemo:
    """DeepResearch演示类"""

    def __init__(self, model_path: str = "default", planning_port: int = 6001):
        """
        初始化DeepResearch演示

        Args:
            model_path: 模型路径
            planning_port: 规划端口
        """
        self.model_path = model_path
        self.planning_port = planning_port

        # 配置LLM
        self.llm_cfg = {
            'model': model_path,
            'generate_cfg': {
                'max_input_tokens': 320000,
                'max_retries': 10,
                'temperature': 0.6,
                'top_p': 0.95,
                'presence_penalty': 1.1
            },
            'model_type': 'qwen_dashscope'
        }

        # 初始化Agent
        self.agent = MultiTurnReactAgent(
            llm=self.llm_cfg,
            function_list=["search", "visit", "google_scholar", "PythonInterpreter", "parse_file"]
        )

        # 演示问题集合
        self.demo_questions = [
            {
                "category": "科技研究",
                "question": "分析2024年人工智能在医疗诊断领域的最新进展和应用案例",
                "description": "这个问题需要搜索最新的AI医疗应用研究，访问相关网页获取详细信息"
            },
            {
                "category": "学术研究",
                "question": "查找并总结关于量子计算在密码学中应用的最新学术论文",
                "description": "需要使用Google Scholar搜索相关学术论文"
            },
            {
                "category": "数据分析",
                "question": "分析Python中机器学习库scikit-learn的最新版本特性和性能改进",
                "description": "需要搜索最新信息并可能需要执行Python代码来验证某些特性"
            },
            {
                "category": "商业分析",
                "question": "研究特斯拉公司2024年的财务表现和市场战略",
                "description": "需要搜索财经信息并访问相关公司报告"
            }
        ]

    def run_single_question(self, question: str) -> Dict:
        """
        运行单个问题研究

        Args:
            question: 研究问题

        Returns:
            研究结果字典
        """
        print(f"\n{'='*60}")
        print(f"开始研究问题: {question}")
        print(f"{'='*60}")

        # 构造输入数据
        input_data = {
            "item": {
                "question": question,
                "answer": ""  # 演示中不需要标准答案
            },
            "planning_port": self.planning_port
        }

        try:
            # 运行研究
            result = self.agent._run(input_data, self.model_path)

            # 输出结果
            print(f"\n{'='*60}")
            print("研究结果:")
            print(f"{'='*60}")

            if "prediction" in result:
                print(f"预测答案: {result['prediction']}")

            if "termination" in result:
                print(f"终止原因: {result['termination']}")

            # 显示对话轮数
            if "messages" in result:
                conversation_rounds = len([msg for msg in result["messages"] if msg["role"] == "assistant"])
                print(f"对话轮数: {conversation_rounds}")

            return result

        except Exception as e:
            print(f"研究过程中出现错误: {e}")
            return {"error": str(e), "question": question}

    def run_interactive_demo(self):
        """运行交互式演示"""
        print("DeepResearch 交互式演示")
        print("="*60)
        print("可用的演示问题:")

        for i, demo in enumerate(self.demo_questions, 1):
            print(f"{i}. [{demo['category']}] {demo['question']}")
            print(f"   描述: {demo['description']}")
            print()

        print("输入问题编号进行演示，或输入自定义问题")
        print("输入 'quit' 退出")

        while True:
            user_input = input("\n请选择 (1-4) 或输入问题: ").strip()

            if user_input.lower() == 'quit':
                break

            # 处理预设问题选择
            if user_input.isdigit() and 1 <= int(user_input) <= len(self.demo_questions):
                question = self.demo_questions[int(user_input) - 1]["question"]
                self.run_single_question(question)
            else:
                # 处理自定义问题
                if user_input:
                    self.run_single_question(user_input)

    def run_batch_demo(self):
        """运行批量演示"""
        print("DeepResearch 批量演示")
        print("="*60)

        results = []
        for i, demo in enumerate(self.demo_questions, 1):
            print(f"\n[{i}/{len(self.demo_questions)}] {demo['category']}")
            result = self.run_single_question(demo["question"])
            results.append({
                "category": demo["category"],
                "question": demo["question"],
                "result": result
            })

        # 保存结果
        output_file = "examples/demo_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n演示完成！结果已保存到 {output_file}")

    def show_tools_info(self):
        """显示可用工具信息"""
        print("DeepResearch 可用工具:")
        print("="*60)

        tools_info = [
            {
                "name": "search",
                "description": "执行Google网络搜索，返回搜索结果",
                "usage": "搜索多个相关查询以获得全面信息"
            },
            {
                "name": "visit",
                "description": "访问网页并返回内容摘要",
                "usage": "深入分析特定网页的内容"
            },
            {
                "name": "google_scholar",
                "description": "搜索学术论文和研究资料",
                "usage": "获取学术界的最新研究成果"
            },
            {
                "name": "PythonInterpreter",
                "description": "执行Python代码进行数据分析",
                "usage": "处理数据、运行计算、验证假设"
            },
            {
                "name": "parse_file",
                "description": "解析本地文件（PDF、DOCX、TXT等）",
                "usage": "分析上传的文档资料"
            }
        ]

        for tool in tools_info:
            print(f"🔧 {tool['name']}")
            print(f"   描述: {tool['description']}")
            print(f"   用途: {tool['usage']}")
            print()


def main():
    """主函数"""
    print("DeepResearch 演示程序")
    print("="*60)

    # 检查环境变量
    required_env_vars = [
        "SERPER_KEY_ID",  # 搜索API密钥
        "JINA_API_KEYS",  # 网页解析API密钥
    ]

    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"⚠️  缺少环境变量: {', '.join(missing_vars)}")
        print("某些功能可能无法正常使用")
        print()

    # 创建演示实例
    demo = DeepResearchDemo()

    print("选择演示模式:")
    print("1. 交互式演示")
    print("2. 批量演示")
    print("3. 查看工具信息")

    choice = input("请选择 (1-3): ").strip()

    if choice == "1":
        demo.run_interactive_demo()
    elif choice == "2":
        demo.run_batch_demo()
    elif choice == "3":
        demo.show_tools_info()
    else:
        print("无效选择")


if __name__ == "__main__":
    main()