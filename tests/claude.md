# Tests 目录文档

## 概述

`tests` 目录包含 DeerFlow 项目的完整测试套件，采用分层测试策略，确保代码质量和功能正确性。测试框架基于 pytest 构建，支持单元测试、集成测试和覆盖率报告。

## 目录结构

```
tests/
├── integration/              # 集成测试
│   ├── test_crawler.py      # 爬虫集成测试
│   ├── test_nodes.py        # 图节点集成测试
│   ├── test_template.py     # 模板集成测试
│   └── test_tts.py          # 文本转语音集成测试
├── test_state.py            # 状态管理测试
└── unit/                    # 单元测试
    ├── checkpoint/          # 检查点系统测试
    │   ├── postgres_mock_utils.py  # PostgreSQL 模拟工具
    │   └── test_checkpoint.py     # 检查点功能测试
    ├── config/              # 配置系统测试
    │   ├── test_configuration.py  # 配置管理测试
    │   └── test_loader.py        # 配置加载器测试
    ├── crawler/             # 爬虫模块测试
    │   ├── test_article.py        # 文章处理测试
    │   └── test_crawler_class.py # 爬虫类测试
    ├── graph/               # 图结构测试
    │   └── test_builder.py       # 图构建器测试
    ├── llms/                # 大语言模型测试
    │   ├── test_dashscope.py     # 通义千问测试
    │   └── test_llm.py           # LLM 基础测试
    ├── prompt_enhancer/     # 提示词增强测试
    │   └── graph/           # 图相关测试
    ├── rag/                 # RAG 系统测试
    │   ├── test_milvus.py         # Milvus 向量数据库测试
    │   ├── test_ragflow.py       # RAGFlow 测试
    │   ├── test_retriever.py     # 检索器测试
    │   └── test_vikingdb_knowledge_base.py  # VikingDB 知识库测试
    ├── server/              # 服务器端点测试
    │   ├── test_app.py            # FastAPI 应用测试
    │   ├── test_chat_request.py  # 聊天请求测试
    │   ├── test_mcp_request.py   # MCP 请求测试
    │   └── test_mcp_utils.py     # MCP 工具测试
    ├── tools/               # 工具模块测试
    │   ├── test_crawl.py          # 爬虫工具测试
    │   ├── test_decorators.py    # 装饰器测试
    │   ├── test_python_repl.py   # Python REPL 测试
    │   ├── test_search.py         # 搜索工具测试
    │   ├── test_tavily_search_api_wrapper.py  # Tavily 搜索测试
    │   ├── test_tavily_search_results_with_images.py  # 图像搜索测试
    │   └── test_tools_retriever.py  # 工具检索器测试
    └── utils/               # 工具函数测试
        └── test_json_utils.py    # JSON 工具测试
```

## 测试策略

### 1. 分层测试架构

#### 单元测试 (Unit Tests)
- **位置**: `tests/unit/` 目录
- **目标**: 测试单个模块、类和函数的独立功能
- **特点**:
  - 使用 mock 和 stub 隔离依赖
  - 快速执行，无外部依赖
  - 覆盖核心业务逻辑

#### 集成测试 (Integration Tests)
- **位置**: `tests/integration/` 目录
- **目标**: 测试模块间的交互和整体功能
- **特点**:
  - 涉及多个组件的协作
  - 可能需要外部服务（如数据库）
  - 验证端到端流程

### 2. 测试覆盖范围

#### 核心模块覆盖
- **LLM 集成**: 支持多种大语言模型（OpenAI、DashScope、Google AI等）
- **图执行引擎**: LangGraph 工作流的节点和状态管理
- **RAG 系统**: 向量数据库集成和文档检索
- **Web 服务**: FastAPI 端点和流式响应
- **工具生态**: 搜索、爬虫、代码执行等工具

#### 配置和环境
- **配置管理**: YAML 配置加载和环境变量替换
- **检查点系统**: PostgreSQL 和 MongoDB 持久化
- **MCP 协议**: Model Context Protocol 工具集成

## 测试工具和配置

### 1. 测试框架

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --cov=src --cov-report=term-missing"
filterwarnings = [
    "ignore::DeprecationWarning",
    "ignore::UserWarning",
]
```

### 2. 依赖管理

```toml
test = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=1.0.0",
    "pytest-cov>=6.0.0",
    "asyncpg-stubs>=0.30.2",
    "mongomock>=4.3.0",
    "pytest-postgresql>=7.0.2",
]
```

### 3. 覆盖率要求

```toml
[tool.coverage.report]
fail_under = 25
```

## 测试模式和实践

### 1. Mock 和 Fixture 模式

#### 广泛使用 Mock
```python
# 典型的 mock 模式
@pytest.fixture
def mock_llm():
    with patch("src.llms.llm.get_llm_by_type") as mock:
        mock.return_value = MagicMock()
        yield mock
```

#### 复杂 Fixture 设计
```python
@pytest.fixture
def mock_state():
    return {
        "messages": [HumanMessage(content="test query")],
        "research_topic": "test query",
        "background_investigation_results": None,
    }
```

### 2. 异步测试支持

使用 `pytest-asyncio` 支持异步函数测试：
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
    assert result is not None
```

### 3. 参数化测试

广泛使用参数化来测试不同场景：
```python
@pytest.mark.parametrize("search_engine", [SearchEngine.TAVILY.value, "other"])
def test_search_engine(search_engine):
    # 测试不同搜索引擎
    pass
```

## 特殊测试工具

### 1. PostgreSQL 模拟工具

`postgres_mock_utils.py` 提供完整的 PostgreSQL 数据库模拟：
```python
class PostgreSQLMockInstance:
    def __init__(self, database_name: str = "test_db"):
        self.database_name = database_name
        self.mock_data = {"chat_streams": {}}

    def connect(self) -> MagicMock:
        # 创建模拟连接
        pass
```

### 2. 环境变量管理

测试中广泛使用 `monkeypatch` 管理环境变量：
```python
def test_with_env_vars(monkeypatch):
    monkeypatch.setenv("API_KEY", "test_key")
    # 测试代码
```

## CI/CD 集成

### GitHub Actions 工作流

在 `.github/workflows/unittest.yaml` 中定义：

#### 服务依赖
- **PostgreSQL**: 版本 15，用于检查点系统测试
- **MongoDB**: 版本 6，用于向量数据库测试

#### 测试执行
```yaml
- name: Run test cases with coverage
  run: |
    source .venv/bin/activate
    TAVILY_API_KEY=mock-key DB_TESTS_ENABLED=true make coverage
```

## 测试命令

### 1. 运行所有测试
```bash
make test
# 或
uv run pytest tests/
```

### 2. 运行覆盖率测试
```bash
make coverage
# 或
uv run pytest --cov=src tests/ --cov-report=term-missing --cov-report=xml
```

### 3. 运行特定测试
```bash
uv run pytest tests/unit/llms/
uv run pytest tests/unit/llms/test_llm.py::test_specific_function
```

## 测试最佳实践

### 1. 测试隔离
- 每个测试独立运行，不依赖执行顺序
- 使用 fixture 创建和清理测试数据
- Mock 外部依赖，确保测试稳定性

### 2. 命名约定
- 测试文件: `test_*.py`
- 测试函数: `test_*`
- Fixture 函数: 描述性名称

### 3. 断言清晰
- 使用明确的断言消息
- 测试预期行为而非实现细节
- 覆盖正常流程和错误情况

### 4. 性能考虑
- 单元测试快速执行（秒级）
- 集成测试可能需要网络和数据库
- 使用 mock 减少外部依赖

## 扩展指南

### 添加新测试

1. **单元测试**: 在对应 `unit/` 子目录创建 `test_*.py`
2. **集成测试**: 在 `integration/` 目录添加测试
3. **使用现有 fixture**: 利用已有的 mock 和 fixture
4. **覆盖率**: 确保新代码有对应测试覆盖

### 调试测试

1. 使用 `-v` 参数查看详细输出
2. 使用 `-s` 参数禁用输出捕获
3. 使用 `--pdb` 在失败时启动调试器
4. 使用 `pytest.mark.skip` 跳过特定测试

这个测试架构确保了 DeerFlow 项目的稳定性和可维护性，支持持续集成和快速迭代开发。