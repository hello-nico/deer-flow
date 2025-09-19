# Task 02 方案与待办清单（Phase 1 快速验证）

目标：在不破坏 deer-flow 现有多代理流程的前提下，于“背景调查（background_investigation_node）”阶段启用 LightRAG 的全局/图谱检索（global 模式），将其输出作为“未验证先验（priors）”输入到 Planner，用以构建研究提纲与假设，再在后续步骤用 web/crawl/本地原文做证据验证。强调结构化、限额与标注，规避上下文爆窗。

---

## 设计要点

- 使用时机：仅在 background_investigation_node 执行一次，产出“结构化先验”。
- 角色定位：先验≠证据。Planner 依据先验规划验证清单，Researcher 再用 web/crawl/RAG 原文去背书或反驳。
- 数据形态：尽量结构化（JSON），字段示例：
  - `entities`: 主题关键实体及权重/标签
  - `relations`: 三元组/关系边（含置信度/社区）
  - `claims`: 高阶主张/待验证结论（≤5 条）
- 预算与稳健性：严格长度上限（字符或 tokens），仅一次调用；失败/不可用时回退到当前 Tavily 流程。

---

## 影响最小的改动点（按优先级）

1) 配置与开关

- 新增环境变量（.env.example 与 docs/说明同步）：
  - `RAG_BACKGROUND_USE_LIGHTRAG=true|false`（默认 false）
  - `LIGHTRAG_QUERY_MODE=global|local|hybrid`（默认 global）
  - `LIGHTRAG_INCLUDE_METADATA=true`（默认 true）
  - `LIGHTRAG_MIN_SCORE=0.65`（默认 0.65，可调）

2) LightRAG Provider 透传查询模式（小改）

- 文件：`src/rag/lightrag.py`
- 在 `payload` 中可选加入 `mode/query_type` 字段（由 `LIGHTRAG_QUERY_MODE` 控制）。
- 默认开启 `include_metadata`（可被 env 覆盖），提高可追踪性。
- 不改变现有 `query_relevant_documents` 返回类型（兼容 Document/Chunk）；若后端返回结构化字段（entities/relations/...），在本期先不强依赖，仅记录到 debug 日志以备二期接入。

3) 背景调查节点对接（核心改动，单点）

- 文件：`src/graph/nodes.py`
- `background_investigation_node` 增加分支：
  - 若 `RAG_BACKGROUND_USE_LIGHTRAG=true` 且 `RAG_PROVIDER=lightrag`：
    1) 调用 LightRAGProvider（global 模式）获取结果
    2) 执行“先验压缩与结构化”：
       - 将 chunks/摘要压成结构化 JSON（entities/relations/claims），控制总长度不超过 ~1200 字符（或 ~600-800 tokens）。
       - 对 `claims` 限制在 ≤5 条，并标注“需要验证”。
    3) 返回值写入 `background_investigation_results`，并在文本前置：
       - “以下为未验证先验，用于规划与假设构建，后续需逐条验证。”
  - 否则保持原 Tavily 流程不变（完全回退）。

4) Planner 消息拼接（非破坏性）

- 现有 Planner 已将 `background_investigation_results` 追加到消息中。无需修改结构，但建议补充一句系统备注（一次性字符串），提醒“先验不得当作已证事实”。（可选）

5) 上下文与日志

- 限额：对背景输出应用严格长度上限（实现时按字符上限即可，二期再切换 token 计数）。
- 日志：记录 LightRAG 调用是否命中、返回大小、压缩前后长度、结构化字段计数，便于 A/B 与回归。

---

## 可执行 TODO-List（第一期）

- [ ] 配置与文档
  - [ ] 在 `.env.example` 增加上述开关与默认值注释
  - [ ] 在 `conf.yaml.example` 或 docs 中补充说明（若需要）

- [ ] Provider 小改（src/rag/lightrag.py）
  - [ ] 支持从 env 读取 `LIGHTRAG_QUERY_MODE` 并在请求 `payload` 透传
  - [ ] `include_metadata` 默认 true，可由 env 覆盖
  - [ ] 默认 `min_score=0.65`（可由 env 覆盖）

- [ ] 背景节点改造（src/graph/nodes.py）
  - [ ] 读取 `RAG_BACKGROUND_USE_LIGHTRAG` 与 `RAG_PROVIDER`
  - [ ] 分支调用 LightRAGProvider（global），捕获异常并回退
  - [ ] 结构化先验构建（简单压缩+抽取）：entities/relations/community_summaries/claims/source_hints
  - [ ] 严格长度控制与“未验证先验”标注

- [ ] 提示与注释（最小变更）
  - [ ] 在 background 节点拼接给 Planner 的文本中加入先验声明（不修改模板，仅追加一段说明）

- [ ] 观测与日志
  - [ ] 记录 LightRAG 响应长度/解析计数、压缩后长度、最终注入 Planner 的长度

- [ ] 验证与质量门禁
  - [ ] 运行一次 GraphRAG 主题流程，确认 background 阶段仅触发 1 次 LightRAG 调用
  - [ ] 日志无 “context window exceeded” 错误
  - [ ] Planner 能基于先验提出验证型子任务
  - [ ] `make lint`/`make test` 通过（或 `uv run ruff check`、`uv run pytest`）

---

## 详细实施方案

### A. 配置开关

- `.env.example` 示例：

```
# LightRAG as priors in background
RAG_BACKGROUND_USE_LIGHTRAG=true
RAG_PROVIDER=lightrag
LIGHTRAG_QUERY_MODE=global
LIGHTRAG_INCLUDE_METADATA=true
LIGHTRAG_MIN_SCORE=0.65
```

### B. LightRAG Provider 透传模式

- 在 `LightRAGProvider.__init__` 读取 `LIGHTRAG_QUERY_MODE`（默认 `global`）。
- 在 `query_relevant_documents` 的 `payload` 中加：`{"mode": self.query_mode}`（字段名视服务端约定，也可用 `query_type`）。
- 默认 `include_metadata=True`，并保留现有 `chunks` 解析与容错逻辑。

### C. 背景调查节点集成

1) 判断开关：若启用 LightRAG 背景先验，直接走 LightRAG 分支，否则沿用 Tavily。
2) 数据处理：
   - 若响应含结构化字段（entities/relations/...），择优抽取 Top-K；否则对文本 chunks 做轻量“要点抽取+概念/关系提名”。
   - 生成结构化 JSON：
     - entities: ≤10 个，带 `name`, `weight`, `tags`（可选）
     - relations: ≤15 条三元组，带 `confidence`
     - community_summaries: ≤3 段，每段 ≤300 字符
     - claims: ≤5 条，每条附 `confidence` 与 `related_entities`
     - source_hints: 收集 doc_id/space/tags（如可得）
   - 合并为简短 Markdown 文本：先置“未验证先验”声明，再附上结构化 JSON（或表格化摘要）。
   - 总长度上限 ~1200 字符（或 600–800 tokens），超出截断并标 `[truncated]`。

### D. Planner 协作

- 继续沿用当前将 `background_investigation_results` 注入 Planner 的方式。
- 可在注入内容中提醒：“请据此制定验证清单，不得将先验当作已证事实”。

### E. 失败与回退

- LightRAG 请求失败/超时/空结果 → 记录日志并回退到 Tavily 原有路径，保障流程稳定。

### F. 观测指标与验收

- 运行 GraphRAG 主题样例：
  - 背景阶段仅 1 次 LightRAG 调用；
  - 日志包含“压缩前后长度、结构化字段计数”；
  - 研究阶段工具调用次数下降，未出现上下文超限错误；
  - 最终报告中结论均有可溯源证据（References 完整）。

---

## 验证步骤（建议）

1) 本地验证

- `uv sync`
- `make lint`（或 `uv run ruff check src && uv run ruff format src`）
- `make test`（如无测试，可运行关键路径用例）
- `make serve` 或 `uv run server.py --reload`，触发一次 GraphRAG 主题请求

2) 日志确认

- 观察 `logs/api_response_*.log`：
  - 有且仅有一次 LightRAG 背景调用；
  - “LightRAG response received.” 与“压缩后长度”等诊断；
  - 无 “Your input exceeds the context window ...”。

3) 质量抽查

- Planner 生成的步骤包含“验证 claims/补充证据”的动作；
- Reporter 的 Key Citations 引用真实可访问来源。

---

## 风险与回滚

- 风险：LightRAG 后端不支持 `mode` 字段或返回结构化字段不稳定。
  - 缓解：保留原 `chunks` 路径与压缩逻辑；失败即回退 Tavily。
- 风险：先验过长导致 Planner token 压力。
  - 缓解：严格长度上限与字段上限；必要时改为仅 JSON + 极短摘要。
- 回滚：将 `RAG_BACKGROUND_USE_LIGHTRAG=false` 即可恢复旧行为，无需代码回退。

---

## 二期展望（非本期交付）

- 新增 `GraphPriorTool` 于 researcher 阶段（缓存/去重/MMR/新增信息率门限）。
- Token 级预算（tiktoken）替换字符级；对 `observations` 做跨轮摘要与去重。
- 利用 LightRAG 返回的 entities/relations 原生结构，减少二次抽取成本。
