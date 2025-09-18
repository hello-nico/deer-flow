# Config 目录文档

## 概述

`src/config` 目录负责管理 Deer Flow 研究框架的配置系统。该目录采用模块化设计，将不同类型的配置分散到专门的文件中，实现了清晰的职责分离。

## 目录结构

```
src/config/
├── __init__.py           # 主要配置定义和导出
├── configuration.py     # 核心配置类和递归限制管理
├── loader.py            # 配置加载工具和环境变量处理
├── agents.py            # 代理与LLM类型映射配置
├── tools.py             # 工具相关配置（搜索引擎、RAG提供者）
├── questions.py         # 内置研究问题库
└── report_style.py      # 报告风格枚举定义
```

## 核心组件

### 1. 主配置模块 (`__init__.py`)

**功能**：
- 导出所有主要配置项
- 定义团队成员配置
- 加载环境变量

**关键配置**：
- `TEAM_MEMBER_CONFIGURATIONS`: 定义研究团队成员配置
  - `researcher`: 负责信息搜索和研究分析
  - `coder`: 负责代码实现和数学计算
- `TEAM_MEMBERS`: 团队成员列表

**依赖**：
- `dotenv`: 自动加载环境变量

### 2. 核心配置类 (`configuration.py`)

**功能**：
- 定义 `Configuration` 数据类
- 管理研究过程的配置参数
- 从 LangChain RunnableConfig 创建配置实例

**主要配置项**：
```python
@dataclass
class Configuration:
    resources: list[Resource]           # 研究资源列表
    max_plan_iterations: int = 1        # 计划迭代次数上限
    max_step_num: int = 3               # 计划步骤数上限
    max_search_results: int = 3          # 搜索结果数量上限
    mcp_settings: dict = None           # MCP工具设置
    report_style: str = "academic"       # 报告风格
    enable_deep_thinking: bool = False  # 是否启用深度思考
```

**特殊功能**：
- `get_recursion_limit()`: 获取递归限制，支持环境变量配置
- `from_runnable_config()`: 从 LangChain 配置创建实例

### 3. 配置加载器 (`loader.py`)

**功能**：
- 提供环境变量读取工具函数
- 支持YAML配置文件加载
- 环境变量替换功能
- 配置缓存机制

**核心函数**：
- `get_bool_env()`: 读取布尔型环境变量
- `get_str_env()`: 读取字符串型环境变量
- `get_int_env()`: 读取整型环境变量
- `load_yaml_config()`: 加载并处理YAML配置文件
- `replace_env_vars()`: 替换字符串中的环境变量引用

**特性**：
- 支持环境变量缓存 (`_config_cache`)
- 递归处理嵌套字典中的环境变量
- 支持 `$VAR` 语法的环境变量引用

### 4. 代理配置 (`agents.py`)

**功能**：
- 定义LLM类型枚举
- 建立代理与LLM类型的映射关系

**配置内容**：
```python
# LLM类型定义
LLMType = Literal["basic", "reasoning", "vision", "code"]

# 代理-LLM映射
AGENT_LLM_MAP = {
    "coordinator": "basic",
    "planner": "basic",
    "researcher": "basic",
    "coder": "basic",
    "reporter": "basic",
    "podcast_script_writer": "basic",
    "ppt_composer": "basic",
    "prose_writer": "basic",
    "prompt_enhancer": "basic",
}
```

### 5. 工具配置 (`tools.py`)

**功能**：
- 定义搜索引擎枚举
- 配置RAG提供者选项
- 管理工具相关的环境变量

**配置项**：
- `SearchEngine`: 支持的搜索引擎枚举
  - `TAVILY`: Tavily搜索引擎
  - `DUCKDUCKGO`: DuckDuckGo搜索引擎
  - `BRAVE_SEARCH`: Brave搜索引擎
  - `ARXIV`: ArXiv学术搜索
  - `WIKIPEDIA`: 维基百科搜索

- `RAGProvider`: RAG提供者枚举
  - `RAGFLOW`: RAGFlow提供者
  - `VIKINGDB_KNOWLEDGE_BASE`: VikingDB知识库
  - `MILVUS`: Milvus向量数据库

**环境变量**：
- `SEARCH_API`: 选择的搜索引擎
- `RAG_PROVIDER`: 选择的RAG提供者

### 6. 问题库 (`questions.py`)

**功能**：
- 提供内置的研究问题库
- 支持中英文双语问题

**内容**：
- `BUILT_IN_QUESTIONS`: 英文研究问题列表
- `BUILT_IN_QUESTIONS_ZH_CN`: 中文研究问题列表

**主题覆盖**：
- AI在医疗保健的应用
- 量子计算与密码学
- 可再生能源技术
- 气候变化影响
- AI伦理问题
- 网络安全趋势
- 区块链技术应用
- 自然语言处理进展
- 机器学习在金融领域的应用
- 电动汽车环境影响

### 7. 报告风格 (`report_style.py`)

**功能**：
- 定义报告输出风格枚举

**风格选项**：
- `ACADEMIC`: 学术风格
- `POPULAR_SCIENCE`: 科普风格
- `NEWS`: 新闻风格
- `SOCIAL_MEDIA`: 社交媒体风格

## 环境变量支持

系统支持以下环境变量配置：

### 应用配置
- `DEBUG`: 调试模式
- `APP_ENV`: 应用环境
- `AGENT_RECURSION_LIMIT`: 代理递归限制

### 工具配置
- `SEARCH_API`: 搜索引擎选择
- `TAVILY_API_KEY`: Tavily API密钥
- `BRAVE_SEARCH_API_KEY`: Brave搜索API密钥
- `RAG_PROVIDER`: RAG提供者选择

### RAG提供者配置
- `RAGFLOW_API_URL`: RAGFlow API地址
- `RAGFLOW_API_KEY`: RAGFlow API密钥
- `MILVUS_URI`: Milvus数据库URI
- `VIKINGDB_KNOWLEDGE_BASE_API_URL`: VikingDB API地址

## 配置加载流程

1. **环境变量加载**: 通过 `dotenv` 自动加载 `.env` 文件
2. **配置文件处理**: 使用 `loader.py` 中的函数处理YAML配置文件
3. **环境变量替换**: 递归替换配置中的环境变量引用
4. **配置缓存**: 将处理后的配置缓存以提高性能
5. **运行时配置**: 通过 `Configuration.from_runnable_config()` 创建运行时配置

## 设计模式

### 1. 数据类模式
使用 `@dataclass` 装饰器定义配置类，提供清晰的结构和默认值。

### 2. 工厂模式
`from_runnable_config()` 方法作为工厂方法，根据不同输入创建配置实例。

### 3. 缓存模式
配置文件加载结果缓存，避免重复IO操作。

### 4. 策略模式
通过枚举定义不同的策略选项（如搜索引擎、报告风格等）。

## 扩展指南

### 添加新的配置项
1. 在相应的配置文件中添加新配置
2. 更新 `__init__.py` 中的导出列表
3. 如需要，添加环境变量支持

### 添加新的工具配置
1. 在 `tools.py` 中添加新的枚举值
2. 更新环境变量处理逻辑
3. 添加相应的配置验证

### 添加新的代理类型
1. 在 `agents.py` 中更新 `AGENT_LLM_MAP`
2. 确保新代理有对应的LLM类型配置

## 最佳实践

1. **环境变量优先**: 使用环境变量覆盖默认配置值
2. **配置验证**: 在加载配置时进行必要的验证
3. **缓存管理**: 合理使用配置缓存提高性能
4. **类型安全**: 使用类型注解确保配置类型安全
5. **文档更新**: 添加新配置时同步更新文档