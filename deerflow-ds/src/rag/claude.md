# RAG 模块文档

## 概述

`src/rag` 目录实现了检索增强生成（RAG）功能，为研究框架提供统一的文档检索接口。该模块支持多种向量数据库和知识库服务，通过统一的抽象层实现了灵活的数据检索策略。

## 架构设计

### 核心抽象

模块采用面向对象设计，通过抽象基类定义统一的接口：

- **Retriever**: 检索器抽象基类，定义了资源列表和文档查询的标准接口
- **Document**: 文档对象，包含文档ID、URL、标题和内容块列表
- **Chunk**: 内容块，包含文本内容和相似度分数
- **Resource**: 资源对象，表示可检索的知识库或数据集

### 支持的提供者

1. **RAGFlow**: 商业RAG服务，提供知识库管理和语义检索
2. **VikingDB Knowledge Base**: 企业级知识库服务，支持HMAC-SHA256签名认证
3. **Milvus**: 开源向量数据库，支持本地Lite和远程服务器模式

## 文件结构

```
src/rag/
├── __init__.py              # 模块导出和接口定义
├── retriever.py             # 核心抽象类和数据模型
├── builder.py               # 检索器工厂模式实现
├── ragflow.py               # RAGFlow提供者实现
├── vikingdb_knowledge_base.py  # VikingDB知识库提供者实现
└── milvus.py                # Milvus向量数据库提供者实现
```

## 核心组件

### 1. 抽象接口 (retriever.py)

```python
class Retriever(abc.ABC):
    @abc.abstractmethod
    def list_resources(self, query: str | None = None) -> list[Resource]:
        """列出可用的资源"""
        pass

    @abc.abstractmethod
    def query_relevant_documents(self, query: str, resources: list[Resource] = []) -> list[Document]:
        """查询相关文档"""
        pass
```

### 2. 工厂模式 (builder.py)

提供统一的检索器创建接口，支持通过环境变量动态配置：

```python
def build_retriever() -> Retriever | None:
    if SELECTED_RAG_PROVIDER == RAGProvider.RAGFLOW.value:
        return RAGFlowProvider()
    elif SELECTED_RAG_PROVIDER == RAGProvider.VIKINGDB_KNOWLEDGE_BASE.value:
        return VikingDBKnowledgeBaseProvider()
    elif SELECTED_RAG_PROVIDER == RAGProvider.MILVUS.value:
        return MilvusProvider()
```

## 提供者实现

### RAGFlow 提供者

**特点**：

- 基于HTTP REST API的云服务
- 支持跨语言检索配置
- 分页和文档过滤功能

**环境变量**：

- `RAGFLOW_API_URL`: API服务地址
- `RAGFLOW_API_KEY`: 认证密钥
- `RAGFLOW_PAGE_SIZE`: 分页大小（默认10）
- `RAGFLOW_CROSS_LANGUAGES`: 跨语言支持

**URI格式**：`rag://dataset/{dataset_id}#{document_id}`

### VikingDB 知识库提供者

**特点**：

- 企业级安全认证（HMAC-SHA256签名）
- 支持预处理和后处理配置
- 详细的检索参数控制

**环境变量**：

- `VIKINGDB_KNOWLEDGE_BASE_API_URL`: API服务地址
- `VIKINGDB_KNOWLEDGE_BASE_API_AK`: Access Key
- `VIKINGDB_KNOWLEDGE_BASE_API_SK`: Secret Key
- `VIKINGDB_KNOWLEDGE_BASE_RETRIEVAL_SIZE`: 检索数量（默认10）
- `VIKINGDB_KNOWLEDGE_BASE_REGION`: 服务区域（默认cn-north-1）

**认证机制**：

```python
def _create_signature(self, method: str, path: str, query_params: dict, headers: dict, payload: bytes) -> str:
    # 实现HMAC-SHA256签名算法
    # 支持时间戳、区域、服务等签名要素
```

### Milvus 提供者

**特点**：

- 支持本地Lite和远程服务器两种模式
- 内置示例文档自动加载功能
- 多种嵌入模型支持（OpenAI、Dashscope）

**环境变量**：

- `MILVUS_URI`: 连接URI（本地文件路径或远程服务地址）
- `MILVUS_USER`: 用户名（远程服务器）
- `MILVUS_PASSWORD`: 密码（远程服务器）
- `MILVUS_COLLECTION`: 集合名称（默认documents）
- `MILVUS_TOP_K`: 检索结果数量（默认10）
- `MILVUS_EMBEDDING_PROVIDER`: 嵌入模型提供商（openai/dashscope）
- `MILVUS_EMBEDDING_MODEL`: 嵌入模型名称
- `MILVUS_EMBEDDING_DIM`: 嵌入维度
- `MILVUS_AUTO_LOAD_EXAMPLES`: 自动加载示例（默认True）
- `MILVUS_EXAMPLES_DIR`: 示例文件目录（默认examples）

**运行模式检测**：

```python
def _is_milvus_lite(self) -> bool:
    return self.uri.endswith(".db") or (
        not self.uri.startswith(("http://", "https://")) and "://" not in self.uri
    )
```

## 数据模型

### Document 对象

```python
class Document:
    id: str                    # 文档唯一标识
    url: str | None = None     # 文档来源URL
    title: str | None = None   # 文档标题
    chunks: list[Chunk] = []   # 内容块列表

    def to_dict(self) -> dict:
        # 转换为字典格式，合并所有内容块
```

### Chunk 对象

```python
class Chunk:
    content: str      # 文本内容
    similarity: float # 相似度分数

    def __init__(self, content: str, similarity: float):
        self.content = content
        self.similarity = similarity
```

### Resource 对象

```python
class Resource(BaseModel):
    uri: str         # 资源标识URI
    title: str       # 资源标题
    description: str | None = None  # 资源描述
```

## 配置管理

### 环境变量配置

通过 `src/config/tools.py` 中的枚举类管理：

```python
class RAGProvider(enum.Enum):
    RAGFLOW = "ragflow"
    VIKINGDB_KNOWLEDGE_BASE = "vikingdb_knowledge_base"
    MILVUS = "milvus"

SELECTED_RAG_PROVIDER = os.getenv("RAG_PROVIDER")
```

### 使用示例

```python
from src.rag import build_retriever, Retriever

# 构建检索器
retriever = build_retriever()

# 列出可用资源
resources = retriever.list_resources("机器学习")

# 查询相关文档
documents = retriever.query_relevant_documents(
    "如何使用向量数据库？",
    resources=resources[:3]  # 限制检索范围
)

# 处理检索结果
for doc in documents:
    print(f"文档: {doc.title}")
    for chunk in doc.chunks:
        print(f"  内容块: {chunk.content[:100]}...")
        print(f"  相似度: {chunk.similarity}")
```

## 设计模式

### 1. 工厂模式

- `build_retriever()` 函数根据配置动态创建检索器实例
- 支持运行时切换不同的RAG提供者

### 2. 策略模式

- 不同提供者实现相同的检索接口
- 用户可以根据需求选择最适合的检索策略

### 3. 模板方法模式

- 提供者实现遵循统一的调用模式
- 认证、请求构建、响应处理等步骤标准化

## 扩展性

### 添加新的提供者

1. 继承 `Retriever` 抽象基类
2. 实现 `list_resources()` 和 `query_relevant_documents()` 方法
3. 在 `RAGProvider` 枚举中添加新类型
4. 在 `build_retriever()` 函数中添加创建逻辑

### 自定义嵌入模型

Milvus提供者支持自定义嵌入模型：

```python
class CustomEmbeddings:
    def embed_query(self, text: str) -> List[float]:
        # 实现自定义嵌入逻辑
        pass

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # 批量嵌入逻辑
        pass
```

## 性能优化

### 1. 延迟连接

- 所有提供者都采用延迟连接策略
- 只在首次调用时建立连接

### 2. 资源管理

- Milvus提供者支持显式的资源清理
- 实现了 `close()` 方法和 `__del__` 析构函数

### 3. 缓存策略

- 嵌入向量缓存（通过LangChain自动处理）
- 示例文档去重（基于文件哈希）

## 错误处理

### 1. 配置验证

- 启动时检查必要的环境变量
- 提供清晰的错误信息

### 2. 网络异常

- 自动重试机制（通过requests库）
- 优雅的降级处理

### 3. 数据验证

- 输入参数类型检查
- 响应数据格式验证

## 安全考虑

### 1. 认证机制

- RAGFlow: Bearer Token认证
- VikingDB: HMAC-SHA256签名认证
- Milvus: 用户名/密码认证

### 2. 数据保护

- 敏感信息通过环境变量管理
- API密钥不在代码中硬编码

### 3. 访问控制

- 支持资源级别的访问控制
- 通过URI过滤机制实现数据隔离

## 监控和日志

### 1. 日志记录

- 使用Python标准logging模块
- 关键操作记录详细日志

### 2. 性能监控

- 嵌入生成时间监控
- 检索延迟统计
- 错误率跟踪

## 测试策略

### 1. 单元测试

- 每个提供者独立测试
- 模拟外部依赖

### 2. 集成测试

- 端到端检索流程测试
- 多提供者切换测试

### 3. 性能测试

- 大规模数据检索测试
- 并发访问测试

## 最佳实践

### 1. 环境配置

```bash
# RAGFlow配置
export RAGFLOW_API_URL="https://api.ragflow.com"
export RAGFLOW_API_KEY="your-api-key"
export RAGFLOW_PAGE_SIZE=10

# Milvus配置
export MILVUS_URI="./milvus.db"
export MILVUS_EMBEDDING_PROVIDER="openai"
export MILVUS_EMBEDDING_MODEL="text-embedding-ada-002"
```

### 2. 代码使用

```python
# 推荐的使用模式
retriever = build_retriever()
if retriever:
    try:
        resources = retriever.list_resources()
        documents = retriever.query_relevant_documents(query, resources)
        # 处理结果
    finally:
        if hasattr(retriever, 'close'):
            retriever.close()
```

### 3. 错误处理

```python
try:
    retriever = build_retriever()
    if not retriever:
        raise ValueError("RAG provider not configured")

    documents = retriever.query_relevant_documents(query)
    return process_documents(documents)

except Exception as e:
    logger.error(f"RAG retrieval failed: {e}")
    return fallback_response()
```

## 总结

`src/rag` 模块提供了一个灵活、可扩展的RAG系统架构，支持多种向量数据库和知识库服务。通过统一的抽象接口和工厂模式，用户可以轻松切换不同的检索策略，满足各种应用场景的需求。模块的设计充分考虑了安全性、性能和可维护性，是一个企业级的RAG解决方案。
