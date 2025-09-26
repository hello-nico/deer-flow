# DeepResearch LangGraph 节点使用指南

本指南介绍如何在独立项目中复用 Tongyi DeepResearch 的 LangGraph 节点（`DeepResearchNode`），并展示所需配置、执行工作流、输入输出格式示例。

## 功能概览

`DeepResearchNode` 将 Planner → DeepResearch 执行器 → Synthesizer 组合封装成一个可复用的 LangGraph runnable，具备以下能力：

- 自动规划调研任务、执行多轮工具调用与总结输出
- 内置 `search`（Serper / Tavily 自动选择）、`visit`、`google_scholar`、`PythonInterpreter` 等工具
- 返回完整执行轨迹（计划、任务结果、消息记录）以及最终答案，方便在其他流程中复用或追踪

## 工作流

1. **接收任务**：`question` 或自定义 `messages`
2. **Planner 拆解**：调用 Planner LLM 生成 2–4 步的执行计划
3. **DeepResearch 执行器**：针对每个子任务，Tongyi DeepResearch 代理自主调用工具（搜索、网页访问、代码执行等）
4. **Synthesizer 整合**：根据计划与任务结果输出最终总结，并附带证据

> 该流程内部基于 LangGraph 的有向状态图：`START → planner → select_task ↔ deepresearch → synthesizer → END`

## 安装与配置

1. 安装依赖（推荐使用 `uv`）：

```bash
uv sync
```

2. 设置必要的环境变量：

| 名称 | 说明 |
| --- | --- |
| `OPENROUTER_API_KEY` | Planner/Synthesizer 所使用的 OpenRouter API Key |
| `OPENROUTER_BASE_URL` | 可选，自定义 OpenRouter 入口，默认 `https://openrouter.ai/api/v1` |
| `PLANNER_MODEL` / `SYNTHESIZER_MODEL` | 可选，默认 `openai/gpt-4o` |
| `DEEPRESEARCH_MODEL` | DeepResearch 服务模型，默认 `alibaba/tongyi-deepresearch-30b-a3b` |
| `DEEPRESEARCH_PORT` | DeepResearch 服务监听端口，默认 `6001` |
| `DEEPRESEARCH_MAX_ROUNDS` / `DEEPRESEARCH_TIMEOUT` / `DEEPRESEARCH_RETRIES` | 可选，控制执行器重试与超时 |
| `SERPER_KEY_ID` | 可选，Google Serper 搜索 API Key |
| `TAVILY_API_KEY` | 可选，启用 Tavily 搜索作为备选方案 |
| `JINA_API_KEYS` | 网页抓取使用的 Jina Reader API Key |
| `API_KEY` / `API_BASE` / `SUMMARY_MODEL_NAME` | 可选，若配置则网页访问将使用外部 LLM 进行结构化摘要 |

> 若 Serper Key 不存在而 Tavily Key 存在，`search` 工具会自动切换到 Tavily；若两者都缺失则返回提示信息。

## 快速上手

```python
from inference.deepresearch_node import build_default_deepresearch_node

node = build_default_deepresearch_node()
result = node.invoke({"question": "what is GraphRAG technology?"})

print(result["answer"])          # Synthesizer 输出
print(result["plan"])            # Planner 生成的步骤数组
print(result["task_results"])    # 每个子任务的执行记录
```

如需在自有 LangGraph 图中嵌入该节点，可直接将 `node` 作为一个 `Runnable` 添加到状态图中。

## 输入与输出

- **输入**（dict）
  - `question`: `str`，必填或与 `messages` 二选一
  - `messages`: `List[BaseMessage | str | dict]`，可选，已有上下文
  - `task_results`: `List[dict]`，可选，继续执行未完成任务时的历史记录
  - `plan`: `List[str]`，可选，复用预先生成的计划

- **输出**（dict）
  - `answer`: `str`，Synthesizer 生成的最终答复
  - `messages`: `List[BaseMessage]`，LangGraph 执行后的完整消息列表
  - `serialized_messages`: `List[dict]`，消息的可序列化表示，便于日志或存档
  - `plan`: `List[str]`，执行时采用的计划步骤
  - `task_results`: `List[dict]`，每个子任务的答案、耗时、工具调用记录等

## Tavily/Visit 工具增强说明

- `tool_search` 新增 Tavily 支持，自动根据可用 API Key 在 Serper 与 Tavily 之间切换，也可通过参数 `provider` 指定使用 `serper`、`tavily` 或 `auto`
- `tool_visit` 增强了容错能力：当外部摘要服务不可用时，将回落到基于原文的关键信息抽取，确保返回可用证据

## 调试建议

- 运行 `examples/langgraph_executor_demo.py` 验证默认节点工作流
- `uv run pytest tests/test_tools.py -k visit` 可快速检查网页访问工具
- 建议在生产环境中为日志系统配置 `logger`，传入 `build_default_deepresearch_node(logger=your_logger)` 以接收执行细节
