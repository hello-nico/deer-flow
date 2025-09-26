# Deer-Flow LLM API 调用机制

## 概述

Deer-Flow 项目采用灵活的多提供商 LLM 调用架构，支持多种主流 LLM 服务提供商，通过配置驱动的方式管理不同 Agent 和场景下的模型调用。

## 架构设计

### 核心组件

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Config Layer  │────│   LLM Factory   │────│  Agent Layer    │
│                 │    │                 │    │                 │
│ • conf.yaml     │    │ • get_llm_by_type│    │ • coordinator   │
│ • env vars      │    │ • caching       │    │ • planner       │
│ • loader        │    │ • provider reg  │    │ • researcher    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 配置系统

### 1. 配置文件结构

**主配置文件**: `conf.yaml`

```yaml
# 基础模型配置
BASIC_MODEL:
  base_url: https://openrouter.ai/api/v1
  model: "google/gemini-2.5-flash"
  api_key: your-api-key
  max_retries: 3
  verify_ssl: true

# 推理模型配置
REASONING_MODEL:
  base_url: https://api.deepseek.com/v1
  model: "deepseek-reasoner"
  api_key: your-api-key
  max_retries: 3

# 视觉模型配置
VISION_MODEL:
  base_url: https://openrouter.ai/api/v1
  model: "gpt-4o"
  api_key: your-api-key

# 代码模型配置
CODE_MODEL:
  base_url: https://api.deepseek.com/v1
  model: "deepseek-coder"
  api_key: your-api-key
```

### 2. 环境变量覆盖

支持通过环境变量覆盖 YAML 配置，格式为：`{LLM_TYPE}_MODEL__{KEY}`

```bash
# 示例环境变量配置
export BASIC_MODEL__api_key="your-api-key"
export BASIC_MODEL__base_url="https://your-custom-endpoint"
export REASONING_MODEL__model="deepseek-reasoner"
```

### 3. 配置加载优先级

1. 环境变量（最高优先级）
2. YAML 配置文件
3. 默认值（最低优先级）

## 支持的 LLM 提供商

### 1. OpenAI 兼容接口

**适用提供商**: OpenRouter、DeepSeek、本地部署模型等

```python
# 配置示例
BASIC_MODEL:
  base_url: https://openrouter.ai/api/v1
  model: "google/gemini-2.5-flash"
  api_key: your-api-key
```

**实现**: 使用 `langchain_openai.ChatOpenAI`

### 2. Azure OpenAI

**自动检测**: 当配置中包含 `azure_endpoint` 时自动启用

```python
# 配置示例
BASIC_MODEL:
  azure_endpoint: https://your-resource.openai.azure.com
  azure_deployment: your-deployment-name
  api_version: 2024-02-15-preview
  api_key: your-api-key
```

**实现**: 使用 `langchain_openai.AzureChatOpenAI`

### 3. Google AI Studio

**平台标识**: `google_aistudio` 或 `google-aistudio`

```python
# 配置示例
BASIC_MODEL:
  platform: "google_aistudio"
  model: "gemini-2.5-flash"
  api_key: your-gemini-api-key
```

**实现**: 使用 `langchain_google_genai.ChatGoogleGenerativeAI`

### 4. DashScope (通义千问)

**自动检测**: 当 `base_url` 包含 "dashscope." 时自动启用

```python
# 配置示例
BASIC_MODEL:
  base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
  model: "qwen-max-latest"
  api_key: your-api-key
```

**实现**: 自定义 `ChatDashscope` 类，增强流式支持

## Agent-LLM 映射

### Agent 类型分配

```python
# src/config/agents.py
AGENT_LLM_MAP: dict[str, LLMType] = {
    "coordinator": "basic",        # 协调器使用基础模型
    "planner": "basic",           # 规划器使用基础模型
    "researcher": "basic",        # 研究员使用基础模型
    "coder": "code",             # 编码器使用代码模型
    "reporter": "basic",         # 报告器使用基础模型
    "podcast_script_writer": "basic",    # 播客脚本编写器
    "ppt_composer": "basic",             # PPT 组合器
    "prose_writer": "basic",             # 散文作家
    "prompt_enhancer": "basic",          # 提示增强器
}
```

### LLM 类型定义

```python
LLMType = Literal["basic", "reasoning", "vision", "code"]
```

## API 调用模式

### 1. 同步调用

**使用场景**: 快速响应、简单任务

```python
# 获取 LLM 实例
llm = get_llm_by_type("basic")

# 同步调用
response = llm.invoke(messages)
print(response.content)
```

**实际应用**: `src/graph/nodes.py:207`

```python
def planner_node(state: State, config: RunnableConfig):
    # ... 其他代码
    response = llm.invoke(messages)
    full_response = response.model_dump_json(indent=4, exclude_none=True)
```

### 2. 流式调用

**使用场景**: 实时响应、长文本生成

```python
# 流式调用
response = llm.stream(messages)
for chunk in response:
    # 处理流式数据
    full_response += chunk.content
    yield chunk
```

**实际应用**: `src/graph/nodes.py:210`

```python
if AGENT_LLM_MAP["planner"] == "basic" and not configurable.enable_deep_thinking:
    response = llm.invoke(messages)
    full_response = response.model_dump_json(indent=4, exclude_none=True)
else:
    response = llm.stream(messages)
    for chunk in response:
        full_response += chunk.content
```

### 3. 异步流式调用

**使用场景**: 工作流执行、并发处理

```python
# 异步流式处理
async for event in graph_instance.astream(
    input, config, stream_mode=["messages", "updates"], subgraphs=True
):
    # 处理事件流
    if isinstance(event_data, tuple):
        message_chunk, message_metadata = event_data
        # 处理消息块
```

**实际应用**: `src/workflow.py:79`

### 4. 结构化输出调用

**使用场景**: 需要特定格式输出的任务

```python
# 结构化输出
llm = get_llm_by_type("basic").with_structured_output(
    Plan, method="json_mode"
)
response = llm.invoke(messages)
# response 为 Plan 对象
```

**实际应用**: `src/podcast/graph/script_writer_node.py:22`

## LLM 工厂机制

### 核心函数

```python
# src/llms/llm.py
def get_llm_by_type(llm_type: LLMType) -> BaseChatModel:
    """
    根据类型获取 LLM 实例

    Args:
        llm_type: LLM 类型 ("basic", "reasoning", "vision", "code")

    Returns:
        BaseChatModel: 配置好的 LLM 实例
    """
```

### 缓存机制

- **LLM 实例缓存**: 避免重复初始化
- **配置缓存**: 配置文件和缓存提升性能

### 错误处理

```python
try:
    llm = get_llm_by_type("basic")
    response = llm.invoke(messages)
except Exception as e:
    logger.error(f"LLM call failed: {e}")
    # 错误处理逻辑
```

## 高级特性

### 1. SSL 配置

```python
# 支持自签名证书
BASIC_MODEL:
  base_url: https://your-custom-endpoint
  verify_ssl: false  # 禁用 SSL 验证
```

### 2. 重试机制

```python
# 默认重试配置
BASIC_MODEL:
  max_retries: 3  # 默认重试次数
```

### 3. 自定义 HTTP 客户端

```python
# 自定义客户端配置
import httpx

BASIC_MODEL:
  http_client: httpx.Client(verify=False)
```

## 监控和调试

### 1. 日志记录

```python
import logging
logger = logging.getLogger(__name__)

# LLM 调用日志
logger.info(f"Calling LLM: {llm_type}, model: {model_name}")
logger.debug(f"Input messages: {messages}")
logger.debug(f"Response: {response}")
```

### 2. 性能监控

```python
import time

start_time = time.time()
response = llm.invoke(messages)
end_time = time.time()

logger.info(f"LLM call took {end_time - start_time:.2f} seconds")
```

## 最佳实践

### 1. 配置管理

- 使用环境变量管理敏感信息（API keys）
- 为不同环境（开发、测试、生产）使用不同的配置文件
- 定期轮换 API keys

### 2. 错误处理

- 实现适当的重试逻辑
- 记录详细的错误信息
- 提供优雅的降级机制

### 3. 性能优化

- 使用 LLM 实例缓存
- 对批量操作使用异步调用
- 监控 API 调用延迟和成功率

### 4. 成本控制

- 监控 token 使用量
- 为不同 Agent 选择合适的模型
- 实现请求缓存机制

## 故障排除

### 常见问题

1. **API Key 错误**

   ```
   Error: 401 Authentication Error
   ```

   - 检查 API key 是否正确
   - 验证环境变量设置

2. **网络连接问题**

   ```
   Error: Connection timeout
   ```

   - 检查网络连接
   - 验证 `base_url` 配置

3. **模型不可用**

   ```
   Error: Model not found
   ```

   - 检查模型名称
   - 验证提供商支持

### 调试技巧

1. **启用详细日志**

   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **测试配置**

   ```python
   from src.llms.llm import get_llm_by_type
   llm = get_llm_by_type("basic")
   print(f"LLM configured: {llm.model}")
   ```

3. **使用测试端点**

   ```python
   # 使用 OpenAI 测试端点
   BASIC_MODEL:
     base_url: https://api.openai.com/v1
     model: gpt-3.5-turbo
   ```

## 扩展新的 LLM 提供商

### 1. 创建提供商类

```python
# src/llms/providers/new_provider.py
from langchain_openai import ChatOpenAI

class ChatNewProvider(ChatOpenAI):
    """新的 LLM 提供商实现"""
    pass
```

### 2. 注册提供商

```python
# src/llms/llm.py
def get_llm_by_type(llm_type: LLMType) -> BaseChatModel:
    # ... 现有代码
    if "new_provider" in base_url:
        return ChatNewProvider(**config)
```

### 3. 添加配置示例

```yaml
# conf.yaml
BASIC_MODEL:
  base_url: https://new-provider.com/api/v1
  model: "new-model"
  api_key: your-api-key
```

这种灵活的架构设计使得 Deer-Flow 能够轻松适配各种 LLM 提供商，同时保持代码的简洁性和可维护性。
