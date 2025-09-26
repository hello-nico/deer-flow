# researcher_node 输入输出分析

## 概述

`researcher_node` 是 deer-flow 中负责执行研究任务的核心节点，它接收当前研究步骤的信息，使用各种工具收集信息，并返回研究结果。

## 输入结构

### 1. 主要输入来源 (deerflow-ds/src/graph/nodes.py:431-437)

```python
agent_input = {
    "messages": [
        HumanMessage(
            content=f"""# Research Topic

{plan_title}

{completed_steps_info}
# Current Step

## Title

{current_step.title}

## Description

{current_step.description}

## Locale

{state.get('locale', 'en-US')}"""
        )
    ]
}
```

### 2. 具体输入组件

#### 核心信息
- **plan_title**: 整个研究计划的标题
- **current_step.title**: 当前步骤的标题
- **current_step.description**: 当前步骤的详细描述
- **locale**: 语言环境设置

#### 上下文信息
- **completed_steps_info**: 已完成步骤的信息
  - 包含之前所有step的标题和执行结果
  - 格式：`<finding>\n{step.execution_res}\n</finding>`

#### 工具相关 (deerflow-ds/src/graph/nodes.py:439-461)
- **resources_info**: 用户提供的资源文件信息
- **citation reminder**: 引用格式提醒
- **search tools**: 网络搜索和爬虫工具
- **retriever_tool**: 本地检索工具（可选）

### 3. 工具配置 (deerflow-ds/src/graph/nodes.py:578-591)

```python
async def researcher_node(state: State, config: RunnableConfig):
    logger.info("Researcher node is researching.")
    configurable = Configuration.from_runnable_config(config)
    tools = [get_web_search_tool(configurable.max_search_results), crawl_tool]
    disable_local = os.getenv("RAG_DISABLE_LOCAL_SEARCH", "false").lower() in ("1", "true", "yes")
    if not disable_local:
        retriever_tool = get_retriever_tool(state.get("resources", []))
        if retriever_tool:
            tools.append(retriever_tool)
    logger.info(f"Researcher tools: {tools}")
    return await _setup_and_execute_agent_step(state, config, "researcher", tools)
```

## 输出结构

### 1. 直接输出 (deerflow-ds/src/graph/nodes.py:492-497)

```python
response_content = result["messages"][-1].content
current_step.execution_res = response_content
```

### 2. State更新 (deerflow-ds/src/graph/nodes.py:499-510)

```python
return Command(
    update={
        "messages": [
            HumanMessage(
                content=response_content,
                name=agent_name,  # "researcher"
            )
        ],
        "observations": observations + [response_content],  # 追加到observations列表
    },
    goto="research_team",
)
```

### 3. 具体输出组件

#### 主要输出
- **response_content**: 研究结果的具体内容
- **current_step.execution_res**: 更新当前step的执行结果

#### State更新
- **messages**: 添加researcher的回复消息
- **observations**: 将研究结果追加到observations列表中

## 数据流转过程

```
输入：
├── 研究主题 (plan_title)
├── 当前步骤信息 (current_step.title, current_step.description)
├── 已完成步骤结果 (completed_steps_info)
├── 资源文件信息 (resources_info)
└── 语言设置 (locale)

↓ researcher_node处理

输出：
├── step.execution_res (直接更新step结果)
├── state.messages (添加消息记录)
└── state.observations (追加到观察列表)

↓ 流转到 research_team节点
```

## 关键特点

### 1. 上下文感知
- 知道之前步骤的执行结果
- 可以基于已完成的研究进行后续工作
- 避免重复研究相同内容

### 2. 步骤聚焦
- 只关注当前step的具体任务
- 按照planner定义的具体描述进行信息收集
- 确保每个研究角度得到充分覆盖

### 3. 结果双存储
- 既更新step.execution_res，又追加到observations
- step.execution_res用于步骤完成状态跟踪
- observations用于最终报告生成

### 4. 工具丰富
- **web_search_tool**: 网络搜索工具
- **crawl_tool**: 网页爬虫工具
- **retriever_tool**: 本地检索工具（可选）
- **python_repl_tool**: 代码执行工具（coder_node专用）

### 5. 格式规范
- 有明确的引用格式要求
- 避免在文本中包含内联引用
- 统一的引用格式：`- [Source Title](URL)`

## 执行流程

### 1. 步骤选择 (deerflow-ds/src/graph/nodes.py:406-418)

```python
# Find the first unexecuted step
current_step = None
completed_steps = []
for step in current_plan.steps:
    if not step.execution_res:
        current_step = step
        break
    else:
        completed_steps.append(step)

if not current_step:
    logger.warning("No unexecuted step found")
    return Command(goto="research_team")
```

### 2. 输入构建 (deerflow-ds/src/graph/nodes.py:422-437)

```python
# Format completed steps information
completed_steps_info = ""
if completed_steps:
    completed_steps_info = "# Completed Research Steps\n\n"
    for i, step in enumerate(completed_steps):
        completed_steps_info += f"## Completed Step {i + 1}: {step.title}\n\n"
        completed_steps_info += f"<finding>\n{step.execution_res}\n</finding>\n\n"
```

### 3. 结果处理 (deerflow-ds/src/graph/nodes.py:491-510)

```python
# Process the result
response_content = result["messages"][-1].content
logger.debug(f"{agent_name.capitalize()} full response: {response_content}")

# Update the step with the execution result
current_step.execution_res = response_content
logger.info(f"Step '{current_step.title}' execution completed by {agent_name}")

return Command(
    update={
        "messages": [
            HumanMessage(
                content=response_content,
                name=agent_name,
            )
        ],
        "observations": observations + [response_content],
    },
    goto="research_team",
)
```

## 实际应用示例

假设研究"什么是RAG"，planner可能生成以下步骤：

### Step 1: RAG基本概念研究
- **输入**:
  - plan_title: "RAG技术研究"
  - current_step.title: "RAG基本概念研究"
  - current_step.description: "收集RAG的定义、工作原理、核心组件等基本信息"
- **输出**: RAG的基本概念、架构图、工作流程等详细信息

### Step 2: RAG应用场景分析
- **输入**:
  - plan_title: "RAG技术研究"
  - current_step.title: "RAG应用场景分析"
  - current_step.description: "调研RAG在不同领域的应用案例和效果"
  - completed_steps_info: 包含Step 1的研究结果
- **输出**: RAG在企业搜索、客服系统、知识管理等领域的应用案例

### Step 3: RAG技术发展趋势
- **输入**:
  - plan_title: "RAG技术研究"
  - current_step.title: "RAG技术发展趋势"
  - current_step.description: "收集RAG技术的最新发展方向和未来趋势"
  - completed_steps_info: 包含Step 1和Step 2的研究结果
- **输出**: RAG技术的最新进展、挑战和未来发展方向

这样的设计确保了每个researcher_node都能专注于特定步骤，同时保持整体研究的连贯性和完整性。