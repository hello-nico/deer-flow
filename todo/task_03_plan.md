# Task 03 方案规划

## 目标回顾

- 解决非英文用户提问时检索质量偏低的问题。
- 在不大幅改动现有架构的前提下，确保搜索查询以英文发出，同时保持最终回复语言与用户一致。
- 允许后续替换为外部翻译 API，实现可拔插的翻译策略。

## 实施策略

1. **统一增强入口**
   - 在 `src/server/app.py` 的 `_astream_workflow_generator` 中，自动调用 Prompt Enhancer，将结果保存为 `enhanced_query_en`（若失败则留空）。
   - 保留原始用户消息，确保 Locale 识别与最终输出仍依据用户语言。

2. **翻译工具抽象**
   - 新增 `src/utils/translation.py`，提供 `translate_to_en(text: str) -> str`。
   - 默认实现为占位逻辑：当检测到非英文且无增强结果时，调用预留的外部 API（当前可直接返回原文，后续接入真实服务）。
   - 失败时记录日志并回退原文，保证鲁棒性。

3. **搜索链路改造**
   - `background_investigation_node`：优先使用 `enhanced_query_en`，否则通过 `translate_to_en` 生成英文查询后调用 Tavily。
   - `researcher_node`：在工具调用前对当前步骤描述生成英文查询，传递给 `web_search` 工具。
   - `src/tools/search.py`：封装统一的查询预处理（含翻译兜底），确保未来新增搜索工具同样生效。

4. **提示词与状态适配**
   - Prompt Enhancer 模板补充指令：保证 `<enhanced_prompt>` 输出英文，保留用户意图。
   - 研究员提示词可增加一条提醒，要求在检索前将关键词转换为英文，与代码逻辑形成互补。

5. **测试与验证**
   - 为 `translate_to_en` 编写单元测试，覆盖中文输入、英文输入、API 失败回退等场景。
   - 构造中文提问的端到端用例，验证背景检索与研究员节点均使用英文查询但最终报告仍为中文。
   - 执行 `uv run pytest` 与 `uv run ruff check` 作为基线验证。

## 未来扩展

- 替换占位翻译为实际 API 时，只需在 `translation.py` 中实现真实调用。
- 若性能成为瓶颈，可引入异步批量翻译或本地模型，无需影响主流程逻辑。
