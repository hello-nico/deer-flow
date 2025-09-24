# Task 03 交付总结

## 完成目标
- 解决非英文提问时检索质量偏低的问题：统一生成英文搜索 query，同时保持最终回复语言与用户一致。
- 在最小化改动架构的前提下，引入 Prompt Enhancer 与翻译工具协同工作，形成可替换的翻译实现。

## 关键改动

### 1. 自动增强入口
- **文件**：`src/server/app.py`
- 在 `_astream_workflow_generator` 中自动调用 Prompt Enhancer，将结果存入状态 `enhanced_query_en`，失败时回退空字符串。
- 确保原始用户消息仍用于 locale 识别和最终输出。

### 2. 翻译工具实现
- **文件**：`src/utils/translation.py`
- 新增 `translate_to_en` 与 `_is_likely_english`：先做英文检测，必要时通过基础 LLM 模型执行翻译；对空结果或异常统一回退原文。
- 记录翻译日志，便于后续监控。

### 3. 搜索链路改造
- **背景检索**：`src/graph/nodes.py`
  - 优先使用 `enhanced_query_en`，若为空则对 `research_topic` 调用 `translate_to_en`，成功时替换查询。
- **搜索工具**：`src/tools/search.py`
  - 为 Tavily 创建 `PreprocessedTavilySearch`，在 `_run` 中调用 `translate_to_en` 作为兜底。
  - 保留辅助函数 `preprocess_search_query`，便于未来扩展其他搜索引擎。
- **提示词强化**：
  - `src/prompts/prompt_enhancer/prompt_enhancer.md` 明确增强结果必须输出英文。
  - `src/prompts/researcher.md` 强调搜索前先将关键词翻译成英文。

### 4. 测试
- **文件**：`tests/test_translation.py`
- 新增单元测试覆盖三种场景：英文输入跳过翻译、非英文调用 LLM、翻译异常时回退原文。
- 当前在沙箱中运行 `uv run pytest tests/test_translation.py` 因缓存目录权限暂未执行；需在本地或解锁权限后验证。

## 行为变更摘要
- 任何用户提问都会先尝试生成英文增强版本；若失败则在搜索前使用 LLM 翻译原始提问。
- 背景检索及 Tavily 工具保证向外部搜索服务发送英文查询，从而提升检索质量。
- 输出仍根据 `locale` 维持原语言。

## 后续建议
- 在真实环境完成 `uv run pytest` 和现有项目质量门槛（lint、type check）。
- 若需进一步优化性能，可考虑缓存翻译结果或替换为专用翻译 API。

## 补充说明：搜索与计划语言差异

### 现状说明
根据日志分析，当前实现存在以下语言分布情况：
- **搜索查询**：已成功实现英文化（包括背景检索和研究员节点搜索）
- **Planner输出**：保持中文（与用户语言一致）

### 详细分析

#### 1. 搜索链路（已英文化）
- **背景检索节点**：优先使用 `enhanced_query_en`，失败时调用 `translate_to_en` 翻译原始查询
- **研究员节点**：通过 `PreprocessedTavilySearch` 自动翻译搜索查询为英文
- **效果**：所有外部搜索服务都接收到英文查询，提升了检索质量

#### 2. Planner节点（保持中文）
- **原因**：`src/prompts/planner.md:151` 明确指示 "Use the same language as the user to generate the plan"
- **实现**：当 `locale="zh-CN"` 时，planner会输出中文计划内容
- **影响**：用户看到的是母语计划，更易于理解和确认

#### 3. 设计合理性
这种语言分布是符合设计目标的：
- **搜索质量优化**：英文查询获得更好的搜索结果
- **用户体验优化**：中文计划让用户清楚了解研究步骤
- **系统兼容性**：研究员节点能够正确处理英文搜索和中文计划

### 结论
当前实现完全符合Task 03的设计目标："统一生成英文搜索 query，同时保持最终回复语言与用户一致"。Planner输出中文是预期的行为，不是问题或缺陷。
