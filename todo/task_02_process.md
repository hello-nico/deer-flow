# Task 02 实施过程记录（Phase 1）

## 背景与目标

- 将 LightRAG 的背景检索（background_search）作为“未验证先验（priors）”接入 deer-flow 流程的 `background_investigation_node`，用于 Planner 规划与认知建模；研究阶段仅做事实性取证。
- 暂时禁用本地事实检索（local_search），避免重复与上下文膨胀；优先使用 web_search 与 crawl_tool 做可溯源证据收集。

## 接口与鉴权对齐

- 资源列表：`GET /api/v1/retrieve/resources`
- 检索入口：`POST /api/v1/retrieve`
  - 本地检索：`{"local_search": true}`（返回 `result.chunks[]`）
  - 背景检索：`{"background_search": true}`（返回 `result.background/entities/relationships/metadata`）
- 鉴权：优先 `X-API-Key: <key>`，兼容 `Authorization: Bearer <token>`。

## 代码改动清单（已落地）

- 文件：`src/rag/lightrag.py`
  - 资源列表路径改为 `GET /api/v1/retrieve/resources`；检索统一走 `POST /api/v1/retrieve`。
  - 新增 `query_background_knowledge(query, resources) -> dict`，透传 `result`，并记录诊断日志：
    - `entities/relationships` 计数
    - `background_chars` 与 `background_approx_tokens`（近似 tokens）
  - 本地检索 `query_relevant_documents`：以 `{"local_search": true}` 调用并将 `result.chunks[]` 映射为 `Document/Chunk`。
  - 鉴权头优先 `X-API-Key`，并保留 Bearer 兼容。
  - 默认 `include_metadata=true`、`min_score=0.65`（本地过滤参考）。

- 文件：`src/graph/nodes.py`
  - `background_investigation_node`：
    - 当 `RAG_PROVIDER=lightrag`（或 `RAG_BACKGROUND_USE_LIGHTRAG=true`）时启用背景检索；
    - 资源优先取 `state.resources`→`configurable.resources`，若为空则自动从 LightRAG `list_resources()` 发现，选用前 1 个；
    - 生成“未验证先验”摘要（背景摘要、实体示例、统计），默认带长度/近似 token 双重限额；
    - 当满足以下任一条件时放宽背景限额：`RAG_DISABLE_LOCAL_SEARCH=true` 或 `BACKGROUND_PRIORS_RELAX_LIMITS=true`。
  - `researcher_node`：工具顺序为 `web_search` → `crawl_tool`（默认不再加入 `local_search_tool`）；可通过 `RAG_DISABLE_LOCAL_SEARCH=true` 明确禁用。
  - 研究者输入增强：禁用本地检索时不再注入“必须使用 local_search_tool”的提示。

- 文件：`src/tools/retriever.py`
  - 工具描述更新：明确“优先 web_search，本地仅用于本地资源或证据补充”。
  - 新增跨文档去重（按内容哈希）；
  - 新增近似 token 总预算 `RAG_TOOL_MAX_TOTAL_TOKENS` 的按比例裁剪；修复 `max_total_tokens` 引发的 NameError 风险并安全记录日志。

- 文件：`.env`
  - 已写入默认开关与预算（可按需调整）：
    - `RAG_PROVIDER=lightrag`
    - `RAG_BACKGROUND_USE_LIGHTRAG=true`
    - `RAG_DISABLE_LOCAL_SEARCH=true`
    - `BACKGROUND_PRIORS_RELAX_LIMITS=true`
    - `AGENT_RECURSION_LIMIT=12`
    - 背景先验预算（放宽后仅用于回退）：`BACKGROUND_PRIORS_MAX_CHARS=900`，`BACKGROUND_PRIORS_MAX_TOKENS=600`
    - 本地检索预算（当前禁用，不生效）：`RAG_TOOL_MAX_DOCS=2`，`RAG_TOOL_MAX_CHUNKS_PER_DOC=3`，`RAG_TOOL_MAX_CHARS_PER_DOC=1200`，`RAG_TOOL_MAX_TOTAL_CHARS=2500`，`RAG_TOOL_MAX_TOTAL_TOKENS=1800`
    - `LIGHTRAG_API_URL=http://localhost:9621/`，`LIGHTRAG_INCLUDE_METADATA=true`，`LIGHTRAG_MIN_SCORE=0.65`

## 运行时行为（期望）

- 背景阶段：仅一次 `background_search`，日志出现 `LightRAG background parsed.`，含 `background_approx_tokens`。
- 研究阶段：工具为 `web_search` 与 `crawl_tool`，不再有 `local_search_tool` 调用与相关提示注入。
- 上下文稳定性：因 local_search 禁用 + 背景先验放宽但仅注入一次，爆窗风险显著下降；如仍超限，可继续收紧 Planner/研究阶段预算或上调模型上下文。

## 验证要点

- 日志确认：
  - 背景日志包含 `entities/relationships` 计数、`background_chars` 与 `background_approx_tokens`；
  - “Researcher tools” 无 `local_search_tool`；
  - 无多次 “LightRAG response received.”（local_search）记录；
  - 不出现 “Your input exceeds the context window …”。

## 风险与回退

- LightRAG 后端异常或无资源：背景节点自动回退至 Tavily/web 搜索路径；
- 通过 `.env` 快速回滚：
  - `RAG_DISABLE_LOCAL_SEARCH=false` 可恢复 local_search；
  - `BACKGROUND_PRIORS_RELAX_LIMITS=false` 恢复背景限额；
  - 关闭背景：`RAG_BACKGROUND_USE_LIGHTRAG=false` 或切换 `RAG_PROVIDER`。

## 后续计划（Phase 2 候选）

- 精准 token 计数：接入 `tiktoken` 进行真实 token 预算（替换近似估算）。
- 受控本地检索：仅在背景 `metadata/doc_id/space` 指向明确证据时，按需少量取文；加入 MMR 去冗与更高相似度阈值。
- 跨轮摘要与去重：对 `observations` 做聚合/摘要，降低历史堆叠；引入“新增信息率”门限停止条件。
- 提示词增强：在 Planner/Researcher 提示中强化“先验≠证据，需逐条验证”的约束（当前已通过声明文本实现，后续可模板化）。
- 质量度量：持续记录 `background_approx_tokens` 与最终输入规模，建立 A/B 基线。
