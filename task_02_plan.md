**任务目标**

- 在不破坏 deer-flow 现有架构的前提下，接入新版 LightRAG 检索接口：在“背景调查”阶段使用 background_search 获取结构化先验；在“本地检索”阶段使用 local_search 返回文档片段，服务后续证据检索。
- 强化上下文预算与先验标注，避免上下文爆窗，并让 Planner 基于先验生成验证型计划。

**接口对齐要点**

- 资源列表：`GET /api/v1/retrieve/resources`（取代旧的 `/api/v1/resources`）。
- 检索入口：`POST /api/v1/retrieve`，`resources` 必填（`rag://<instance>` 列表），`local_search` 与 `background_search` 二选一。
- 鉴权：优先支持 `X-API-Key: <key>`；如有需要兼容 `Authorization: Bearer <token>`（双头并行发送亦可）。
- 响应结构：
  - local_search: `result = { query, chunks[], metadata{}, total_results }`
  - background_search: `result = { background, entities[], relationships[], metadata{} }`

**最小改动范围**

- 仅小改 `src/rag/lightrag.py` 以适配新接口并新增“背景先验查询”方法；
- 在 `src/graph/nodes.py` 的 `background_investigation_node` 增加 LightRAG 背景检索分支（可通过 env 开关控制）；
- 调整 `src/tools/retriever.py` 让本地检索走 `local_search=true`（维持现有裁剪逻辑）；
- 补充 `.env.example` 与文档变量说明；其他流程与提示词保持不变。

**实施步骤（可执行 TODO）**

- 配置与文档
  - [ ] 在 `.env.example` 增加并注释：
    - `RAG_PROVIDER=lightrag`（启用 LightRAG 提供者）
    - `RAG_BACKGROUND_USE_LIGHTRAG=true`（背景调查启用 LightRAG）
    - `LIGHTRAG_API_URL=`（如 `http://localhost:8000/`，末尾 `/`）
    - `LIGHTRAG_API_KEY=`（用于 `X-API-Key`；如需要也兼容 Bearer）
    - `LIGHTRAG_TIMEOUT=30`、`LIGHTRAG_MAX_RESULTS=10`
    - `LIGHTRAG_QUERY_MODE=global`（可留作后续扩展，当前按接口以 background/local 区分）
  - [ ] 在 `docs/` 或 `conf.yaml.example` 同步新增变量说明与接入指引。

- LightRAG Provider（`src/rag/lightrag.py`）
  - [ ] 路径更新：
    - 列表：`GET {api_url}api/v1/retrieve/resources`
    - 检索：`POST {api_url}api/v1/retrieve`
  - [ ] 鉴权头：若 `LIGHTRAG_API_KEY` 存在，设置 `X-API-Key`；如已存在 Bearer 逻辑，保留并可并行发送以增强兼容性。
  - [ ] 新增方法：`query_background_knowledge(query: str, resources: list[Resource]) -> dict`
    - 请求体：`{"query", "max_results", "resources", "background_search": true}`
    - 返回：服务端 `result` 直接透传（`background/entities/relationships/metadata`），并记录诊断日志（耗时、返回大小、实体/关系计数）。
  - [ ] 调整本地检索：`query_relevant_documents`
    - 请求体：`{"query", "max_results", "resources", "local_search": true}`
    - 将 `result.chunks[]` 映射为既有的 `Document/Chunk`（`id/doc_id/content/score/similarity`），保持现有上层工具的兼容。
  - [ ] `list_resources` 解析新响应：`{"resources": [{uri,title,description}]}`。

- 背景调查节点（`src/graph/nodes.py`）
  - [ ] 在 `background_investigation_node` 中读取开关：若 `RAG_BACKGROUND_USE_LIGHTRAG=true` 且 `RAG_PROVIDER=lightrag`：
    - 调用 `LightRAGProvider.query_background_knowledge`，资源取自 `Configuration.resources`；
    - 对返回结果做“先验压缩与结构化”：
      - 限额：总长度 ~1200 字符（或后续换 token 计数）；
      - 限制条目：`entities` ≤ 10、`relationships` ≤ 15、`claims`（若存在）≤ 5；
      - 生成 Markdown 段落，首行加入“未验证先验，仅供规划参考，后续需逐条验证。”；
      - 将压缩后的文本作为 `background_investigation_results` 写入。
    - 失败或空结果：回退到 Tavily 路径，保证流程健壮。

- 本地检索工具（`src/tools/retriever.py`）
  - [ ] 保持现有裁剪逻辑（`RAG_TOOL_MAX_*`），底层调用仍为 `retriever.query_relevant_documents`；
  - [ ] 验证在新接口下 `chunks` 字段兼容，日志包含“trimmed 总字数”。

- 验证与质量门禁
  - [ ] 用 GraphRAG 主题运行一次全流程：
    - 背景阶段仅调用 LightRAG 一次；
    - 日志中记录 background 响应解析计数与压缩后长度；
    - 研究阶段不再出现上下文超限错误；
    - Planner 生成验证型子任务，Reporter 的引用来自可溯源来源。
  - [ ] 通过 `make lint`、`make test` 或 `uv run ruff check && uv run pytest`。

**方案细节**

- 先验使用原则
  - 先验仅用于构建“问题域图谱/高阶主张/术语表”，不得在报告正文中当作已证事实；
  - Researcher 阶段用 web/crawl/RAG 原文针对先验逐条验证，形成引用与证据。
- 上下文预算与风控
  - 背景输出严格限额，超限截断并标注 `[truncated]`；
  - 记录“压缩前/后长度、实体/关系计数”，便于 A/B 与回归；
  - 如仍有超窗风险，再引入 token 级预算与跨轮摘要（后续迭代）。
- 兼容与回退
  - 若 LightRAG 服务不可用/鉴权失败/无资源，自动回退到 Tavily 背景调查路径；
  - 开关关闭时（`RAG_BACKGROUND_USE_LIGHTRAG=false`）完全恢复旧行为。

**时间与里程碑**

- Day 1：Provider 与接口对齐、背景节点分支打通（含回退与日志）
- Day 2：裁剪/结构化输出、限额与标注、基础验证用例跑通
- Day 3：文档与配置整理、A/B 日志复核与参数微调

**验收标准**

- 背景阶段 LightRAG 调用成功率 > 95%；
- 背景先验注入后不出现“context window exceeded”；
- Planner 能基于先验给出验证型计划，Reporter 引用可溯源；
- Lint/测试通过，配置项在 `.env.example` 完整可用。

**补充：工具优先级（web_search > local_search）**

- 原因：当前知识库覆盖不足，需先保证信息广度与新鲜度，再用本地检索补充与佐证。
- 执行策略：
  - 背景调查：只用 LightRAG background_search 获取“先验”。
  - 研究阶段：优先 web_search（广度）→ 必要时 crawl_tool（取正文）→ 最后再用 local_search（针对 `rag://` 资源或本地证据补充）。
- 代码改动（纳入 TODO）：
  - 在 `src/graph/nodes.py` 的 `researcher_node` 中，确保 `retriever_tool` 排在 `web_search` 之后（而非 tools[0]）。
  - 在 `src/tools/retriever.py` 修改工具描述，去掉“higher priority than the web search”字样，改为“在需要本地资源或本地证据补充时使用，优先级低于 web_search”。
  - （可选）在 `src/prompts/researcher.md` 增补一句：当需要广度/时效性信息时优先使用 web_search，`rag://` 资源或需要本地证据时使用 local_search_tool。
