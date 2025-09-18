# DeerFlow 项目导航索引

## 🚀 快速导航

### 核心架构

- **主项目文档**: [claude.md](./claude.md) - 项目总览和架构
- **工作流引擎**: [src/graph/claude.md](./src/graph/claude.md) - LangGraph 核心工作流
- **智能体系统**: [src/agents/claude.md](./src/agents/claude.md) - 多智能体协作
- **工具集成**: [src/tools/claude.md](./src/tools/claude.md) - 搜索、爬虫、代码执行工具

### 配置与管理

- **配置系统**: [src/config/claude.md](./src/config/claude.md) - 系统配置管理
- **LLM 抽象层**: [src/llms/claude.md](./src/llms/claude.md) - 大语言模型接口
- **提示词系统**: [src/prompts/claude.md](./src/prompts/claude.md) - 角色提示词模板

### 功能模块

- **RAG 系统**: [src/rag/claude.md](./src/rag/claude.md) - 检索增强生成
- **API 服务**: [src/server/claude.md](./src/server/claude.md) - FastAPI 服务端
- **播客生成**: [src/podcast/claude.md](./src/podcast/claude.md) - 音频内容生成
- **PPT 生成**: [src/ppt/claude.md](./src/ppt/claude.md) - 演示文稿生成
- **文本处理**: [src/prose/claude.md](./src/prose/claude.md) - 文本编辑和优化

### 测试与前端

- **测试系统**: [tests/claude.md](./tests/claude.md) - 单元测试和集成测试
- **前端界面**: [web/claude.md](./web/claude.md) - Next.js Web 应用

## 🎯 功能场景导航

### 研究工作流

1. **规划阶段** → `src/graph/nodes.py` - `planner_node`
2. **研究执行** → `src/graph/nodes.py` - `research_team_node`
3. **代码分析** → `src/graph/nodes.py` - `coder_node`
4. **报告生成** → `src/graph/nodes.py` - `reporter_node`

### 工具使用

- **网络搜索** → `src/tools/search.py`
- **网页爬虫** → `src/tools/crawl.py`
- **代码执行** → `src/tools/python_repl.py`
- **RAG 检索** → `src/tools/retriever.py`

### 多模态输出

- **文本报告** → `src/prompts/reporter.md`
- **播客音频** → `src/podcast/graph/`
- **PPT 演示** → `src/ppt/graph/`
- **语音合成** → `src/tools/tts.py`

## 🔧 开发任务导航

### 添加新智能体

1. 定义智能体类型 → `src/agents/agents.py` - `AGENT_TYPE_MAP`
2. 配置 LLM 映射 → `src/config/agents.py` - `AGENT_LLM_MAP`
3. 创建提示词 → `src/prompts/` - 新增 `.md` 文件
4. 实现工作流节点 → `src/graph/nodes.py`

### 添加新工具

1. 实现工具类 → `src/tools/` - 继承 `BaseTool`
2. 注册工具配置 → `src/config/tools.py`
3. 集成到工作流 → `src/graph/nodes.py`

### 配置管理

- **环境变量** → `src/config/loader.py`
- **YAML 配置** → `conf.yaml.example`
- **模型配置** → `src/llms/llm.py`

### API 端点

- **聊天接口** → `src/server/app.py` - `/api/chat/stream`
- **配置接口** → `src/server/app.py` - `/api/config`
- **功能接口** → `src/server/app.py` - 各种生成接口

## 📊 架构依赖图

```
用户界面 (web/)
    ↓
API 服务 (src/server/)
    ↓
工作流引擎 (src/graph/)
    ↓
智能体系统 (src/agents/) ← 提示词系统 (src/prompts/)
    ↓                       ↓
工具系统 (src/tools/)    LLM 抽象层 (src/llms/)
    ↓                       ↓
配置管理 (src/config/)   RAG 系统 (src/rag/)
```

## 🚨 常见问题定位

### 配置问题

- **环境变量未设置** → `src/config/loader.py`
- **模型配置错误** → `src/llms/llm.py`
- **工具配置缺失** → `src/config/tools.py`

### 工作流问题

- **节点执行失败** → `src/graph/nodes.py`
- **状态流转异常** → `src/graph/types.py`
- **检查点错误** → `src/graph/checkpoint.py`

### 工具问题

- **搜索失败** → `src/tools/search.py`
- **代码执行错误** → `src/tools/python_repl.py`
- **RAG 检索失败** → `src/rag/retriever.py`

### API 问题

- **请求格式错误** → `src/server/*_request.py`
- **流式响应异常** → `src/server/app.py`
- **MCP 连接失败** → `src/server/mcp_utils.py`

## 📈 性能优化要点

### 缓存策略

- **LLM 实例缓存** → `src/llms/llm.py` - `_llm_cache`
- **配置缓存** → `src/config/loader.py` - `_config_cache`

### 异步处理

- **流式响应** → `src/server/app.py` - SSE 实现
- **异步工具** → `src/tools/` - 异步工具实现

### 资源管理

- **数据库连接池** → `src/rag/` - 延迟连接
- **临时文件清理** → `src/ppt/graph/` - 自动清理

## 🧪 测试覆盖

### 单元测试

- **配置测试** → `tests/unit/config/`
- **LLM 测试** → `tests/unit/llms/`
- **工具测试** → `tests/unit/tools/`

### 集成测试

- **工作流测试** → `tests/integration/`
- **API 测试** → `tests/integration/`
- **端到端测试** → `tests/integration/`

## 🔗 外部集成

### LLM 提供商

- **OpenAI** → `src/llms/llm.py`
- **DeepSeek** → `src/llms/llm.py`
- **Google AI** → `src/llms/llm.py`
- **通义千问** → `src/llms/providers/dashscope.py`

### 数据库

- **MongoDB** → `src/graph/checkpoint.py`
- **PostgreSQL** → `src/graph/checkpoint.py`
- **Milvus** → `src/rag/milvus.py`

### 云服务

- **火山引擎 TTS** → `src/tools/tts.py`
- **RAGFlow** → `src/rag/ragflow.py`
- **VikingDB** → `src/rag/vikingdb_knowledge_base.py`

---

*此导航索引提供了 DeerFlow 项目的完整功能地图，帮助开发者快速定位和理解各个模块的功能和关系。*
