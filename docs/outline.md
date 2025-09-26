# deer-flow分章节独立实现报告的证据分析

## 发现的关键证据

### 1. **Plan模型定义** (deerflow-ds/src/prompts/planner_model.py)

- Plan模型包含steps列表，每个Step代表一个独立章节
- 每个Step都有execution_res字段存储执行结果

```python
class Plan(BaseModel):
    title: str
    steps: List[Step] = Field(
        default_factory=list,
        description="Research & Processing steps to get more context"
    )

class Step(BaseModel):
    title: str
    description: str = Field(..., description="Specify exactly what data to collect")
    step_type: StepType = Field(..., description="Indicates the nature of the step")
    execution_res: Optional[str] = Field(
        default=None, description="The Step execution result"
    )
```

### 2. **分章节执行机制** (deerflow-ds/src/graph/nodes.py:398-610)

- `_execute_agent_step`函数独立执行每个步骤
- 通过`current_plan.steps`遍历所有未执行步骤
- 每个步骤完成时更新`execution_res`字段

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
```

### 3. **Planner统一规划** (deerflow-ds/src/graph/nodes.py:174-247)

- planner_node负责生成完整的步骤计划
- 计划包含多个独立的research/processing步骤

### 4. **DeepResearch适配器架构** (src/deep_research/adapter.py:235-382)

- planner_node: 生成步骤计划
- select_task_node: 选择当前任务
- deepresearch_node: 执行具体任务
- synthesizer_node: 合成最终结果

```python
def select_task_node(state: ResearchState) -> Dict[str, Any]:
    plan = state.get("plan", []) or []
    index = state.get("current_task_index", 0)
    if index >= len(plan):
        return {"executor_ready": False, "active_task_index": None}
    task = plan[index]
    message = HumanMessage(
        content=f"请执行第{index + 1}步任务：{task}",
        additional_kwargs={"task_index": index, "role": "planner_instructions"},
    )
    return {
        "messages": [message],
        "executor_ready": True,
        "active_task_index": index,
    }
```

### 5. **报告整合机制** (deerflow-ds/src/graph/nodes.py:353-390)

- reporter_node在所有步骤完成后整合结果
- 将所有observations合并为最终报告

```python
for observation in observations:
    invoke_messages.append(
        HumanMessage(
            content=f"Below are some observations for the research task:\n\n{observation}",
            name="observation",
        )
    )
```

## 工作流程

1. Planner生成包含多个步骤的计划
2. 研究团队按顺序独立执行每个步骤
3. 每个步骤的结果存储在step.execution_res中
4. 所有步骤完成后，Reporter整合生成最终报告

Reporter节点使用固定报告模板，但这个模板是用于最终报告整合，不是用于planner生成章节：
step是researcher专注的信息收集角度，不是最终报告的章节。比如研究AI市场，step可能是"市场规模分析"、"公司战略调研"、"技术趋势预测"，但这些不会直接成为报告的章节标题，而是会被Reporter重新整合到标准的报告模板中。

### Report Structure

  1. **Title**
  2. **Key Points**
  3. **Overview**
  4. **Detailed Analysis**
  5. **Survey Note** (可选)
  6. **Key Citations**

这证明了deer-flow确实采用了"planner统一做规划，分章节独立实现"的架构。
