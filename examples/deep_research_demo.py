"""简易示例：在 Deer Flow 中启用 Tongyi DeepResearch 路径。

运行前请确保已经设置 OPENROUTER_API_KEY，并通过 uv 环境执行：
    uv run python examples/deep_research_demo.py
"""

import asyncio
import os
import sys

from src.workflow import run_agent_workflow_async


async def main() -> None:
    question = (
        "What is GraphRAG technology?"
    )
    await run_agent_workflow_async(
        user_input=question,
        debug=False,
        max_plan_iterations=1,
        max_step_num=3,
        enable_background_investigation=True,
    )


if __name__ == "__main__":
    if not os.getenv("OPENROUTER_API_KEY"):
        sys.stderr.write("需先配置 OPENROUTER_API_KEY 环境变量。\n")
        sys.exit(1)

    # 示范用途：若未显式开启则默认启用深度调研路径。
    os.environ.setdefault("DEEP_RESEARCHER_ENABLE", "true")

    asyncio.run(main())
