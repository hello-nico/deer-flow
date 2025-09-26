# Tools目录文档

## 概述

`src/tools` 目录是Deer Flow研究框架的核心工具集合，提供了各种搜索、爬虫、代码执行和多媒体处理工具。该目录采用模块化设计，支持多种搜索引擎和第三方服务集成。

## 目录结构

```
tools/
├── __init__.py              # 工具模块入口，导出主要工具
├── decorators.py            # 工具装饰器和日志混入类
├── search.py               # 搜索工具工厂，支持多种搜索引擎
├── crawl.py                # 网页爬虫工具
├── python_repl.py          # Python代码执行工具
├── retriever.py            # RAG检索工具
├── tts.py                  # 文本转语音工具（字节跳动TTS）
└── tavily_search/          # Tavily搜索增强工具
    ├── __init__.py
    ├── tavily_search_api_wrapper.py
    └── tavily_search_results_with_images.py
```

## 核心工具

### 1. 搜索工具 (`search.py`)

**功能**：提供多种搜索引擎的统一接口，支持：
- Tavily搜索（默认）
- DuckDuckGo搜索
- Brave搜索
- Arxiv学术搜索
- Wikipedia维基百科搜索

**主要接口**：
```python
def get_web_search_tool(max_search_results: int) -> BaseTool
```

**配置方式**：
- 环境变量：`SEARCH_API`（默认值：`tavily`）
- 配置文件：`conf.yaml`中的`SEARCH_ENGINE`部分
- Tavily支持域名包含/排除配置：`include_domains`、`exclude_domains`

**特性**：
- 所有搜索工具都经过日志装饰器增强
- Tavily搜索支持图片和图片描述
- 支持搜索结果数量配置
- 异步搜索支持

### 2. 爬虫工具 (`crawl.py`)

**功能**：网页内容抓取和Markdown格式转换

**主要接口**：
```python
@tool
@log_io
def crawl_tool(url: str) -> str
```

**特性**：
- 基于LangChain的`@tool`装饰器
- 自动输入输出日志记录
- 返回URL和爬取内容的Markdown格式
- 错误处理和日志记录
- 内容限制为前1000字符

### 3. Python REPL工具 (`python_repl.py`)

**功能**：安全的Python代码执行环境

**主要接口**：
```python
@tool
@log_io
def python_repl_tool(code: str) -> str
```

**配置方式**：
- 环境变量：`ENABLE_PYTHON_REPL`（默认：`false`）
- 支持值：`true`/`1`/`yes`/`on`

**特性**：
- 安全开关控制
- 输入验证和类型检查
- 错误消息格式化
- 执行结果标准化输出
- 错误模式检测

### 4. RAG检索工具 (`retriever.py`)

**功能**：本地知识库检索工具，支持多种RAG提供商

**主要接口**：
```python
def get_retriever_tool(resources: List[Resource]) -> RetrieverTool | None
```

**支持的RAG提供商**：
- RAGFlow
- VikingDB Knowledge Base
- Milvus

**特性**：
- 基于LangChain BaseTool的自定义实现
- 支持同步和异步操作
- 资源验证和空值处理
- 检索结果格式化为字典列表

### 5. 文本转语音工具 (`tts.py`)

**功能**：基于字节跳动火山引擎的TTS服务

**主要类**：
```python
class VolcengineTTS:
    def __init__(self, appid: str, access_token: str, ...)
    def text_to_speech(self, text: str, ...) -> Dict[str, Any]
```

**特性**：
- 支持多种音频参数调节（语速、音量、音调）
- 支持多种编码格式（默认MP3）
- UUID生成用户ID
- 完整的错误处理和日志记录
- Base64编码的音频数据返回

### 6. Tavily搜索增强工具 (`tavily_search/`)

**功能**：Tavily搜索引擎的增强实现，支持图片搜索

**主要组件**：
- `EnhancedTavilySearchAPIWrapper`：增强的API包装器
- `TavilySearchWithImages`：支持图片的搜索工具

**特性**：
- 继承自LangChain Tavily工具
- 支持图片和图片描述搜索
- 异步搜索支持
- 结果清理和格式化
- 详细的文档和使用示例

## 基础设施

### 装饰器系统 (`decorators.py`)

**主要组件**：
- `@log_io`：函数输入输出日志装饰器
- `LoggedToolMixin`：工具日志混入类
- `create_logged_tool`：日志工具工厂函数

**特性**：
- 自动记录工具调用参数
- 标准化日志格式
- 支持混入类继承
- 工具类名称自动生成

### 工具导出 (`__init__.py`)

**导出的工具**：
- `crawl_tool`：爬虫工具
- `python_repl_tool`：Python执行工具
- `get_web_search_tool`：搜索工具工厂
- `get_retriever_tool`：RAG检索工具
- `VolcengineTTS`：TTS服务类

## 依赖关系

### 外部依赖
- **LangChain生态**：`langchain_core`、`langchain_community`、`langchain_experimental`
- **搜索服务**：`langchain_tavily`、`tavily-python`
- **HTTP客户端**：`requests`、`aiohttp`
- **配置管理**：`pydantic`、`python-dotenv`
- **爬虫**：依赖`src.crawler.Crawler`
- **RAG系统**：依赖`src.rag`模块

### 内部依赖
- `src.config`：配置管理（搜索引擎、RAG提供商）
- `src.crawler`：爬虫实现
- `src.rag`：RAG检索系统
- `src.config.tools`：工具配置枚举

## 集成方式

### 在Agent中使用
```python
from src.tools import get_web_search_tool, get_retriever_tool

# 获取搜索工具
search_tool = get_web_search_tool(max_results=5)

# 获取RAG工具
rag_tool = get_retriever_tool(resources)
```

### 在Graph节点中使用
工具主要在`src/graph/nodes.py`中的各种节点函数中使用，支持：
- 背景调查节点
- 信息检索节点
- 代码执行节点

### 配置管理
1. **搜索引擎配置**：
   ```yaml
   # conf.yaml
   SEARCH_ENGINE:
     include_domains: ["example.com"]
     exclude_domains: ["spam.com"]
     wikipedia_lang: "zh"
     wikipedia_doc_content_chars_max: 4000
   ```

2. **环境变量配置**：
   ```bash
   export SEARCH_API=tavily
   export ENABLE_PYTHON_REPL=true
   export RAG_PROVIDER=ragflow
   export TAVILY_API_KEY=your_key
   export BRAVE_SEARCH_API_KEY=your_key
   ```

## 设计模式

### 工厂模式
- `get_web_search_tool`：根据配置创建不同的搜索工具
- `get_retriever_tool`：根据RAG提供商创建检索工具
- `create_logged_tool`：创建带日志的工具实例

### 装饰器模式
- `@log_io`：为工具函数添加日志功能
- `LoggedToolMixin`：为工具类添加日志功能

### 策略模式
- 支持多种搜索引擎的动态切换
- 支持多种RAG提供商的动态选择

## 错误处理

### 统一错误处理
- 所有工具都包含try-catch块
- 标准化的错误消息格式
- 详细的错误日志记录

### 安全机制
- Python REPL工具可禁用
- 输入验证和类型检查
- API密钥安全存储

## 扩展指南

### 添加新搜索引擎
1. 在`SearchEngine`枚举中添加新选项
2. 在`get_web_search_tool`中添加对应的case
3. 创建Logged工具实例
4. 添加相应的环境变量支持

### 添加新工具
1. 创建工具实现文件
2. 添加适当的装饰器
3. 在`__init__.py`中导出
4. 添加相应的配置支持

### 自定义日志行为
- 继承`LoggedToolMixin`
- 重写`_log_operation`方法
- 使用`create_logged_tool`工厂函数

## 最佳实践

1. **工具命名**：使用描述性的工具名称
2. **错误处理**：始终包含适当的错误处理
3. **日志记录**：使用统一的日志格式
4. **配置管理**：通过环境变量和配置文件管理
5. **类型注解**：使用完整的类型注解
6. **文档字符串**：提供详细的工具文档
7. **异步支持**：为长时间运行的操作提供异步版本