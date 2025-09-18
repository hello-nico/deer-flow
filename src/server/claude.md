# Server模块文档

## 概述

`src/server`模块是DeerFlow项目的FastAPI API服务层，提供了完整的Web API接口，支持聊天对话、文本转语音、播客生成、PPT生成等多种AI功能。该模块采用现代化的FastAPI框架，支持异步处理、流式响应和多种数据格式。

## 目录结构

```
src/server/
├── __init__.py          # 模块初始化，导出app实例
├── app.py              # 主应用文件，包含所有API端点
├── chat_request.py     # 聊天相关的请求/响应模型
├── config_request.py   # 配置相关的请求/响应模型
├── rag_request.py      # RAG相关的请求/响应模型
├── mcp_request.py      # MCP服务器相关的请求/响应模型
└── mcp_utils.py        # MCP工具加载和连接工具
```

## 核心组件

### 1. FastAPI应用 (app.py)

**主要功能：**
- 提供完整的RESTful API服务
- 支持流式响应（Server-Sent Events）
- 集成LangGraph工作流引擎
- 支持多种AI模型和工具

**关键特性：**
- **CORS支持**: 可配置的跨域资源共享
- **流式聊天**: 实时对话响应
- **多模态支持**: 文本、音频、文档生成
- **MCP集成**: Model Context Protocol支持
- **检查点支持**: PostgreSQL和MongoDB持久化

**API端点：**

#### 聊天相关
- `POST /api/chat/stream` - 流式聊天对话
- `POST /api/tts` - 文本转语音
- `POST /api/prompt/enhance` - 提示词增强

#### 内容生成
- `POST /api/podcast/generate` - 播客生成
- `POST /api/ppt/generate` - PPT生成
- `POST /api/prose/generate` - 散文生成

#### 配置管理
- `GET /api/config` - 获取服务器配置
- `GET /api/rag/config` - 获取RAG配置
- `GET /api/rag/resources` - 获取RAG资源

#### MCP服务
- `POST /api/mcp/server/metadata` - 获取MCP服务器元数据

### 2. 请求/响应模型

#### 聊天模型 (chat_request.py)
- `ChatRequest`: 聊天请求主体，包含消息历史、资源、配置等
- `ChatMessage`: 单条聊天消息
- `ContentItem`: 多模态内容项（文本、图片等）
- `TTSRequest`: 文本转语音请求
- `GeneratePodcastRequest`: 播客生成请求
- `GeneratePPTRequest`: PPT生成请求
- `GenerateProseRequest`: 散文生成请求
- `EnhancePromptRequest`: 提示词增强请求

#### 配置模型 (config_request.py)
- `ConfigResponse`: 服务器配置响应

#### RAG模型 (rag_request.py)
- `RAGConfigResponse`: RAG配置响应
- `RAGResourceRequest`: RAG资源请求
- `RAGResourcesResponse`: RAG资源响应

#### MCP模型 (mcp_request.py)
- `MCPServerMetadataRequest`: MCP服务器元数据请求
- `MCPServerMetadataResponse`: MCP服务器元数据响应

### 3. MCP工具支持 (mcp_utils.py)

**功能特性：**
- 支持多种MCP服务器连接类型（stdio、sse、streamable_http）
- 异步工具加载和管理
- 超时控制和错误处理
- 环境变量和HTTP头支持

**支持的传输类型：**
- `stdio`: 标准输入输出连接
- `sse`: Server-Sent Events连接
- `streamable_http`: 可流式HTTP连接

## 技术架构

### 1. 流式响应机制
使用Server-Sent Events (SSE)实现实时响应：
- 事件类型：message_chunk、tool_calls、tool_call_result、interrupt
- 支持工具调用和结果返回
- 实时状态更新和错误处理

### 2. 工作流集成
与LangGraph深度集成：
- 支持复杂的多步骤AI工作流
- 检查点持久化（PostgreSQL/MongoDB）
- 内存存储支持
- 递归限制和超时控制

### 3. 配置管理
- 环境变量驱动配置
- 动态模型选择
- RAG提供者配置
- 报告样式定制

## 关键配置

### 环境变量
- `ALLOWED_ORIGINS`: CORS允许的源
- `ENABLE_MCP_SERVER_CONFIGURATION`: MCP功能开关
- `LANGGRAPH_CHECKPOINT_SAVER`: 检查点持久化开关
- `LANGGRAPH_CHECKPOINT_DB_URL`: 检查点数据库URL
- `VOLCENGINE_TTS_APPID`: 语音合成应用ID
- `VOLCENGINE_TTS_ACCESS_TOKEN`: 语音合成访问令牌

### 报告样式
- `ACADEMIC`: 学术风格
- `POPULAR_SCIENCE`: 科普风格
- `NEWS`: 新闻风格
- `SOCIAL_MEDIA`: 社交媒体风格

## 错误处理

### 统一错误响应
- 内部服务器错误保护
- 详细的错误日志记录
- 客户端友好的错误消息
- 异常传播和恢复

### 特定错误处理
- MCP服务器连接错误
- TTS服务调用错误
- 工作流执行错误
- 资源访问错误

## 安全特性

### CORS配置
- 可配置的允许源列表
- 支持凭据传输
- 限制HTTP方法

### 输入验证
- Pydantic模型验证
- 类型安全的数据处理
- 参数校验和清理

### MCP安全
- 服务器配置开关
- 超时控制
- 环境变量隔离

## 性能优化

### 异步处理
- 全异步I/O操作
- 并发请求处理
- 流式响应优化

### 资源管理
- 连接池管理
- 内存使用优化
- 超时控制

### 缓存策略
- 检查点缓存
- 模型配置缓存
- 资源列表缓存

## 扩展性

### 插件架构
- MCP工具支持
- 可扩展的RAG提供者
- 模块化的工作流组件

### 配置驱动
- 环境变量配置
- 动态模型选择
- 可配置的处理参数

## 监控和日志

### 日志记录
- 结构化日志输出
- 请求跟踪ID
- 错误堆栈记录

### 监控指标
- 请求处理时间
- 错误率统计
- 资源使用情况

## 使用示例

### 基本聊天
```python
from src.server import app
import uvicorn

# 启动服务器
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 流式聊天请求
```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat/stream",
    json={
        "messages": [{"role": "user", "content": "Hello"}],
        "thread_id": "unique-conversation-id"
    },
    stream=True
)
```

## 最佳实践

1. **错误处理**: 始终使用适当的HTTP状态码
2. **日志记录**: 记录足够的调试信息
3. **资源管理**: 使用异步上下文管理器
4. **配置验证**: 验证所有输入参数
5. **性能考虑**: 避免阻塞操作
6. **安全考虑**: 验证和清理所有输入

## 维护和更新

- 定期更新依赖项
- 监控API使用情况
- 优化性能瓶颈
- 添加新的API端点
- 改进错误处理机制