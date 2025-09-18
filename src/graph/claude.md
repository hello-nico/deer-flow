# Graph 模块文档

## 概述

`src/graph` 模块是 Deer Flow 深度研究框架的核心工作流引擎，基于 LangGraph 实现了一个多智能体协作的研究系统。该模块定义了完整的研究流程，从需求分析到最终报告生成的端到端自动化。

## 目录结构

```
src/graph/
├── __init__.py          # 模块入口，导出主要的图构建函数
├── types.py            # 状态定义和数据模型
├── nodes.py            # 各种节点（智能体）的实现
├── builder.py          # 图构建器和工作流定义
└── checkpoint.py       # 检查点和持久化存储
```

## 核心架构

### 1. 状态管理 (types.py)

#### State 类

- **继承**: `langgraph.graph.MessagesState`
- **用途**: 定义工作流中的全局状态，贯穿所有节点
- **关键字段**:
  - `locale`: 语言环境 (默认: "en-US")
  - `research_topic`: 研究主题
  - `observations`: 观察记录列表
  - `resources`: 资源列表 (RAG 相关)
  - `plan_iterations`: 计划迭代次数
  - `current_plan`: 当前计划 (Plan 对象或字符串)
  - `final_report`: 最终报告
  - `auto_accepted_plan`: 是否自动接受计划
  - `enable_background_investigation`: 是否启用背景调查
  - `background_investigation_results`: 背景调查结果

### 2. 节点实现 (nodes.py)

#### 协调器节点 (coordinator_node)

- **职责**: 与用户交互，理解需求，决定是否启动研究流程
- **工具**: `handoff_to_planner` - 交接给规划器
- **输出**: 设置研究主题和语言环境，决定下一步流向

#### 背景调查节点 (background_investigation_node)

- **职责**: 在规划前进行初步搜索，收集背景信息
- **搜索引擎**: 支持 Tavily 和其他搜索引擎
- **输出**: 背景调查结果 JSON 格式

#### 规划器节点 (planner_node)

- **职责**: 生成详细的研究计划
- **输入**: 用户需求 + 背景调查结果
- **LLM 选择**:
  - 支持深度思考模式 (reasoning LLM)
  - 基础模式 (basic LLM with structured output)
  - 其他配置的 LLM
- **输出**: 结构化的研究计划或直接进入报告阶段

#### 人工反馈节点 (human_feedback_node)

- **职责**: 处理用户对计划的反馈
- **功能**:
  - 支持计划编辑 (`[EDIT_PLAN]`)
  - 支持计划接受 (`[ACCEPTED]`)
  - 自动接受模式
- **错误处理**: JSON 解析失败时的降级处理

#### 研究团队节点 (research_team_node)

- **职责**: 协调研究任务分配
- **逻辑**: 根据步骤类型分配给相应的研究员或编码器

#### 研究员节点 (researcher_node)

- **职责**: 执行研究型任务
- **工具**:
  - 网络搜索工具
  - 爬虫工具
  - 本地检索工具 (RAG)
- **MCP 支持**: 集成 Model Context Protocol 工具

#### 编码器节点 (coder_node)

- **职责**: 执行代码分析任务
- **工具**: Python REPL 工具
- **MCP 支持**: 集成开发相关工具

#### 报告器节点 (reporter_node)

- **职责**: 生成最终研究报告
- **输入**: 所有观察结果和计划信息
- **格式要求**:
  - 结构化报告 (关键点、概述、详细分析)
  - 引用格式规范
  - 优先使用 Markdown 表格

### 3. 图构建器 (builder.py)

#### 工作流结构

```
START → coordinator → background_investigator → planner → human_feedback → research_team → reporter → END
                                    ↑                                      ↓
                                    └──────────────────────────────────────┘
```

#### 条件路由逻辑

- `continue_to_running_research_team`: 根据步骤完成状态和类型决定下一个节点
- 步骤类型映射:
  - `StepType.RESEARCH` → researcher_node
  - `StepType.PROCESSING` → coder_node

#### 图构建选项

- `build_graph()`: 无记忆版本
- `build_graph_with_memory()`: 带持久化记忆版本

### 4. 检查点系统 (checkpoint.py)

#### ChatStreamManager 类

- **功能**: 管理聊天消息流的持久化存储
- **存储后端**:
  - MongoDB (推荐)
  - PostgreSQL
  - 内存存储 (临时)
- **特性**:
  - 分块处理流式消息
  - 自动合并完成的消息
  - 线程安全的设计
- **数据结构**:
  - `thread_id`: 会话标识
  - `messages`: 消息列表
  - `ts`: 时间戳

## 依赖关系

### 外部模块依赖

- `src.prompts.planner_model`: Plan 和 Step 数据模型
- `src.prompts.template`: 提示词模板系统
- `src.agents`: 智能体创建和管理
- `src.tools`: 各种工具 (搜索、爬虫、代码执行等)
- `src.rag`: 检索增强生成功能
- `src.llms`: 大语言模型接口
- `src.config`: 配置管理

### LangGraph 依赖

- `langgraph.graph`: 图构建基础
- `langgraph.checkpoint`: 检查点功能
- `langgraph.store`: 存储抽象
- `langgraph.types`: Command 类型等

## 关键特性

### 1. 多智能体协作

- 不同专业能力的智能体分工协作
- 通过 LangGraph 的状态传递实现信息共享

### 2. 灵活的计划管理

- 支持人工干预和自动执行
- 计划迭代和优化机制

### 3. 工具集成

- 支持 MCP (Model Context Protocol)
- 可扩展的工具系统

### 4. 持久化支持

- 多种数据库后端
- 流式消息处理

### 5. 错误处理和降级

- JSON 解析容错
- LLM 响应异常处理
- 工具调用失败恢复

## 配置选项

### 环境变量

- `LANGGRAPH_CHECKPOINT_SAVER`: 启用检查点保存
- `LANGGRAPH_CHECKPOINT_DB_URL`: 数据库连接 URL
- `AGENT_RECURSION_LIMIT`: 智能体递归限制

### 智能体配置

- 通过 `AGENT_LLM_MAP` 配置不同智能体的 LLM 类型
- 支持深度思考模式
- 搜索引擎选择

## 使用示例

```python
from src.graph import build_graph_with_memory

# 构建带记忆的图
graph = build_graph_with_memory()

# 执行工作流
result = graph.invoke({
    "messages": [("user", "研究人工智能的最新发展")],
    "locale": "zh-CN"
})

# 获取最终报告
final_report = result["final_report"]
```

## 扩展指南

### 添加新的节点类型

1. 在 `nodes.py` 中实现节点函数
2. 在 `builder.py` 中注册节点
3. 更新条件路由逻辑

### 集成新的工具

1. 实现工具函数
2. 在相应节点中添加工具调用
3. 配置 MCP 服务器（如需要）

### 自定义状态

1. 扩展 `State` 类
2. 更新相关节点的状态处理逻辑

## 注意事项

1. **线程安全**: 在多线程环境中使用时需要注意状态一致性
2. **资源管理**: 及时关闭数据库连接
3. **错误恢复**: 实现适当的错误处理和恢复机制
4. **性能优化**: 大量数据传输时考虑流式处理
5. **安全性**: 工具调用时注意权限控制
