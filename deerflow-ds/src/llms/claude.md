# LLM 抽象层文档

## 概述

`src/llms` 目录提供了统一的LLM抽象层，支持多种大语言模型提供商和不同类型的模型配置。该模块基于 LangChain Core 构建，为上层应用提供一致的接口。

## 目录结构

```
src/llms/
├── __init__.py          # 包初始化文件
├── llm.py              # 核心LLM管理模块
└── providers/          # 模型提供商实现
    └── dashscope.py    # 通义千问/DashScope 支持
```

## 核心设计

### LLM 类型系统

系统支持四种LLM类型，通过 `src/config/agents.py` 中的 `LLMType` 定义：

```python
LLMType = Literal["basic", "reasoning", "vision", "code"]
```

每种类型对应不同的使用场景：

- **basic**: 基础模型，用于通用任务
- **reasoning**: 推理模型，用于复杂推理任务
- **vision**: 视觉模型，用于多模态任务
- **code**: 代码模型，用于编程任务

### 配置映射

LLM类型与配置文件的映射关系：

```python
_llm_type_config_keys = {
    "reasoning": "REASONING_MODEL",
    "basic": "BASIC_MODEL",
    "vision": "VISION_MODEL",
    "code": "CODE_MODEL",
}
```

## 支持的模型提供商

### 1. OpenAI 兼容模型

- **标准 OpenAI**: ChatOpenAI
- **Azure OpenAI**: AzureChatOpenAI
- **其他 OpenAI 兼容接口**: 通过 base_url 配置

### 2. Google AI Studio

- **原生支持**: 通过 `platform: "google_aistudio"` 配置
- **模型**: Gemini 系列 (gemini-1.5-pro, gemini-2.0-flash 等)

### 3. 通义千问 (DashScope)

- **提供商**: 阿里云 DashScope
- **特殊功能**: 支持推理模式 (enable_thinking)
- **实现**: 自定义 ChatDashscope 类

### 4. DeepSeek

- **推理模型**: ChatDeepSeek
- **特殊处理**: 自动映射 reasoning 类型到 DeepSeek

## 核心功能

### 1. 模型获取与缓存

```python
def get_llm_by_type(llm_type: LLMType) -> BaseChatModel:
    """获取指定类型的LLM实例，支持缓存"""
```

### 2. 配置管理

#### 配置文件支持

- 从 `conf.yaml` 文件读取配置
- 支持环境变量覆盖 (格式: `{LLM_TYPE}_MODEL__{KEY}`)
- 环境变量优先级高于配置文件

#### 环境变量示例

```bash
BASIC_MODEL__api_key=your_api_key
BASIC_MODEL__base_url=https://your-endpoint.com
REASONING_MODEL__model=your_model_name
```

### 3. 配置查询

```python
def get_configured_llm_models() -> dict[str, list[str]]:
    """获取所有已配置的模型列表"""
```

## 配置示例

### 基础 OpenAI 兼容模型

```yaml
BASIC_MODEL:
  base_url: https://ark.cn-beijing.volces.com/api/v3
  model: "doubao-1-5-pro-32k-250115"
  api_key: your_api_key
  max_retries: 3
  verify_ssl: true
```

### Google AI Studio 原生支持

```yaml
BASIC_MODEL:
  platform: "google_aistudio"
  model: "gemini-2.5-flash"
  api_key: your_google_api_key
  max_retries: 3
```

### Azure OpenAI

```yaml
BASIC_MODEL:
  model: "azure/gpt-4o-2024-08-06"
  azure_endpoint: $AZURE_OPENAI_ENDPOINT
  api_version: $OPENAI_API_VERSION
  api_key: $AZURE_OPENAI_API_KEY
```

### DeepSeek 推理模型

```yaml
REASONING_MODEL:
  base_url: https://api.deepseek.com
  model: "deepseek-reasoner"
  api_key: your_api_key
```

### 通义千问模型

```yaml
BASIC_MODEL:
  base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
  model: "qwen-max-latest"
  api_key: your_api_key
```

## 特殊功能

### 1. SSL 验证控制

```yaml
BASIC_MODEL:
  # 禁用SSL验证 (用于自签名证书)
  verify_ssl: false
```

### 2. 推理模式支持

DashScope 模型支持推理模式：

- 自动检测 base_url 是否包含 "dashscope."
- 根据 LLM 类型设置 `enable_thinking` 参数

### 3. 重试机制

- 默认 `max_retries: 3`
- 可通过配置覆盖

### 4. 自定义 HTTP 客户端

- 支持自定义 http_client 和 http_async_client
- 用于特殊网络配置

## DashScope 特殊实现

`ChatDashscope` 类扩展了 `ChatOpenAI`，提供：

1. **推理内容支持**: 处理 OpenAI 推理模型的 `reasoning_content`
2. **流式处理**: 增强的流式响应处理
3. **错误处理**: 改进的错误处理和重试机制
4. **消息转换**: 特殊的消息格式转换逻辑

## 使用模式

### 1. 基本使用

```python
from src.llms.llm import get_llm_by_type

# 获取基础模型
basic_llm = get_llm_by_type("basic")

# 获取推理模型
reasoning_llm = get_llm_by_type("reasoning")
```

### 2. 代理映射

系统通过 `AGENT_LLM_MAP` 将不同代理映射到适当的 LLM 类型：

```python
AGENT_LLM_MAP = {
    "coordinator": "basic",
    "planner": "basic",
    "researcher": "basic",
    "coder": "basic",
    # ... 其他代理
}
```

## 错误处理

1. **配置缺失**: 抛出 `ValueError` 当必需配置缺失时
2. **SSL 错误**: 支持禁用 SSL 验证
3. **API 错误**: 继承 LangChain 的错误处理机制
4. **网络错误**: 内置重试机制

## 性能优化

1. **实例缓存**: 相同类型的 LLM 实例会被缓存复用
2. **连接池**: 支持自定义 HTTP 客户端
3. **异步支持**: 支持异步客户端配置

## 扩展指南

### 添加新的模型提供商

1. 在 `providers/` 目录创建新的实现文件
2. 继承适当的 LangChain 基类
3. 在 `llm.py` 中添加创建逻辑
4. 更新配置检测逻辑

### 添加新的 LLM 类型

1. 更新 `src/config/agents.py` 中的 `LLMType`
2. 添加配置映射关系
3. 更新 `AGENT_LLM_MAP` 如果需要

## 注意事项

1. **配置文件路径**: 系统自动查找项目根目录的 `conf.yaml`
2. **环境变量优先级**: 环境变量覆盖配置文件设置
3. **缓存机制**: LLM 实例会被缓存，重启应用后生效
4. **SSL 安全**: 生产环境建议使用有效的 SSL 证书
5. **API 密钥**: 确保正确设置 API 密钥和相关权限

## 相关文件

- `/home/chencheng/py/src/deer-flow/src/config/agents.py`: LLM 类型定义和代理映射
- `/home/chencheng/py/src/deer-flow/conf.yaml.example`: 配置文件示例
- `/home/chencheng/py/src/deer-flow/docs/configuration_guide.md`: 详细配置指南
