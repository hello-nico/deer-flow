1. 对localsearch的访问比较频繁，而且query差异化比较大。针对我们当前仅仅对论文的录入数据可能还不够。
2. 检索会超出上下文长度，我初步判断是检索的质量不够让观察者会一直query，直到撑爆整个上下文。(这一点需要提供技术验证)

---

问题定位

- 检索调用过于频繁且结果堆积导致上下文溢出
  - ReAct 研究代理递归上限高（日志显示“Recursion limit set to: 30”），工具优先选择本地检索，导致多轮反复调用本地 RAG，累计大量观察内容进入后续对话，最终超出模型上下文。
  - 本地检索工具在工具列表中被插入到第一个，且描述强调“应优先于 web 搜索”，强化了其被频繁调用的倾向（src/graph/nodes.py，researcher_node 把 retriever 放在 tools[0]）。
- 检索载荷过大且缺少跨轮去重/压缩
  - 本地检索每次返回的内容虽然在工具侧做了截断，但默认上限仍高：RAG_TOOL_MAX_DOCS=3、RAG_TOOL_MAX_CHUNKS_PER_DOC=5、RAG_TOOL_MAX_CHARS_PER_DOC=4000、RAG_TOOL_MAX_TOTAL_CHARS=8000（src/
  tools/retriever.py）。多轮调用叠加极易超窗。
  - 缺少跨工具调用的去重与缓存（相同/相似 query、重复 chunk 内容），相同主题的多次查询会不断把相近文本重复塞入对话历史。
- 数据覆盖与相关性阈值偏宽
  - 仅录入论文，面对“什么是RAG/GraphRAG”等定义类需求，返回的是论文段落而非定义型材料，质量不稳定，促使代理持续追加检索试图“找更好答案”。
  - LightRAG 客户端最小分数阈值较低（默认 min_score=0.3，src/rag/lightrag.py），易引入边缘相关的长段文本。
  - 默认未请求元数据（include_metadata=False），返回缺少标题/URL 等线索，不利于代理判断可信度与复用引用，进一步诱发“再查一次”。

  证据

- 多轮本地检索请求与累积内容
  - 日志多次出现 LightRAG 响应：“LightRAG response received.”，“LightRAG chunks parsed.”（logs/api_response_2.log）。
  - 研究代理对本地检索的具体 query 多次且差异化很大（覆盖 GraphRAG 定义、组件、时间线、架构等）：logs/api_response_2.log:42/47/52/57/62/67/72/78/84。
- 上下文超限错误
  - openai.APIError: Your input exceeds the context window of this model（logs/api_response_2.log 尾部栈追踪），发生在 researcher/agent 执行期间，符合“多轮累积内容过大”的模式。
- 返回内容载荷大
  - lightrag 响应样例包含长段论文内容（logs/lightrag_response_1.json 中 chunks[0].content 极长），即使单轮截断，叠加若干轮后容易超窗。

  改进建议（优先级从快到慢）

- 工具使用策略与预算
  - 下调递归上限：将 AGENT_RECURSION_LIMIT 从 30 调整为 8–12，避免长链路自我放大。
  - 调整工具优先级与描述：
    - 在 researcher 工具列表中将 web_search 放在 local_search_tool 前；或修改 local_search_tool 的 description，明确“定义类/广义主题优先使用 web_search，本地仅在明确需要本地知识库或限定
  资源时使用”。
  - 严格化单轮上下文预算（工具侧已有截断能力）：
    - 建议初始参数：RAG_TOOL_MAX_DOCS=2、RAG_TOOL_MAX_CHUNKS_PER_DOC=3、RAG_TOOL_MAX_CHARS_PER_DOC=1200、RAG_TOOL_MAX_TOTAL_CHARS=2500（src/tools/retriever.py）。
    - 如需更稳妥，改为按 tokens 计数（tiktoken）而非字符，确保与目标模型上下文窗口对齐。
- 结果质量与相关性
  - 提高 LightRAG 客户端阈值：LIGHTRAG_MIN_SCORE=0.6~0.7，LIGHTRAG_MAX_RESULTS=5（src/rag/lightrag.py）。
  - 工具端二次过滤：增加本地 RAG_TOOL_SCORE_THRESHOLD（在 retriever.py 仅保留 chunk.score >= 阈值），并按相似度降序 + MMR 选取，提升多样性、降低冗余。
  - 启用元数据回传：设置 LIGHTRAG_INCLUDE_METADATA=true，并在工具输出中保留 title/url 供引用判断，减少“再查一次”动机（src/rag/lightrag.py -> include_metadata；src/tools/retriever.py 已支
  持 URL/标题透传）。
- 去重与缓存
  - 查询级缓存：对 keywords 归一化（小写/去标点/去停用词），在 RetrieverTool 维护 LRU（如 32 条），命中直接复用上次裁剪后的结果，避免同义反复查询。
  - 内容去重：对 chunk.content 做 hash，跨轮记录 seen set，工具输出阶段跳过已出现内容，或仅保留新信息的摘要。
- 压缩与工作流稳健性
  - 工具内置“压缩返回模式”：可选在检索后先做 map-compress（LLM 生成每 chunk 的 3 条要点 + 来源），把长文压成要点列表，显著降低 tokens。
  - 限制观察堆积：对 state["observations"] 按最近 N 条保留或先合并摘要后再进入 reporter，避免在生成最终报告时二次爆窗。
  - 失败重试策略：当连续 K 次本地检索新增有效信息 < X（例如 < 10% 新 token），自动切换到 web_search 或终止检索阶段。
- 数据层面
  - 扩充本地语料：加入定义型与权威入口（官方 GitHub README、微软 GraphRAG 文档、LlamaIndex/LangChain docs、Lettria/FalkorDB/Neo4j 专题页、Wikipedia/维基词条等），而不仅是论文段落。
  - 预处理与摘要：在索引阶段生成“文档级概览摘要”和“关键术语词条”，对“什么是X”类查询优先返回短摘要而非长段原文。
  - 多语言支持：针对中文查询优先返回中文材料与中文摘要，减少额外解释轮次。

  变更落点建议

- 限载与过滤：src/tools/retriever.py（调整环境变量、加入分数阈值/去重/可选压缩、按 tokens 计数）。
- LightRAG 客户端：src/rag/lightrag.py（提高 min_score 默认、开启 include_metadata、可选截断极长 chunk）。
- 工具优先级与提示：src/graph/nodes.py（researcher 工具顺序/减少对本地工具“高优先级”的描述倾向）。
- 配置暴露：.env.example 与 conf.yaml.example 同步新增/调整的变量并注释用途。

  验证方案

- 复现用例：使用同一主题（GraphRAG）运行完整流程，观察
  - 每轮“Retriever output trimmed”日志中的 total_chars_after_trim 是否显著下降（logs 中已有该项记录，src/tools/retriever.py）。
  - LightRAG 调用次数是否减少（检索工具 query 次数下降）。
  - 是否不再出现 “Your input exceeds the context window…”（logs/api_response_2.log 同类位置）。
- A/B 对比：原始参数 vs 新参数，在相同计划步骤数下统计
  - 工具调用次数、总 tokens、最终报告质量与引用完整性。

  需要我基于上述建议直接提交一版参数调整与工具层去重/分数阈值的最小改动吗？也可以同时修改工具描述与顺序，先做一轮验证。
