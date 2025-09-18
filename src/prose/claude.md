# Prose 模块文档

## 概述

`src/prose` 模块是 deer-flow 研究框架中的文本处理核心组件，提供多种文本操作功能。该模块基于 LangGraph 框架构建，实现了灵活的文本生成、修改和优化工作流程。

## 目录结构

```
src/prose/
├── graph/
│   ├── state.py              # 状态定义
│   ├── builder.py            # 工作流构建器
│   ├── prose_continue_node.py    # 继续写作节点
│   ├── prose_improve_node.py     # 改进文本节点
│   ├── prose_shorter_node.py     # 缩短文本节点
│   ├── prose_longer_node.py      # 扩展文本节点
│   ├── prose_fix_node.py         # 修复文本节点
│   └── prose_zap_node.py         # 自定义命令节点
└── claude.md                  # 本文档
```

## 核心组件

### 1. 状态管理 (ProseState)

**文件**: `graph/state.py`

`ProseState` 类继承自 `MessagesState`，定义了文本处理过程中的状态结构：

- `content`: 待处理的文本内容
- `option`: 文本处理选项（continue, improve, shorter, longer, fix, zap）
- `command`: 用户自定义命令（仅用于 zap 模式）
- `output`: 处理后的输出结果

### 2. 工作流构建器 (Builder)

**文件**: `graph/builder.py`

`build_graph()` 函数构建了完整的有向图工作流程：

- **入口**: START 节点
- **路由**: 通过 `optional_node` 函数根据 option 值路由到对应的处理节点
- **节点**: 6个专门的处理节点
- **出口**: END 节点

### 3. 处理节点

所有节点都遵循相同的实现模式：
- 使用专用的提示词模板
- 调用配置的 LLM 模型
- 返回处理后的文本结果

#### prose_continue_node
- **功能**: 基于现有文本继续写作
- **特点**: 优先考虑文本末尾的上下文，限制输出200字符

#### prose_improve_node
- **功能**: 改进现有文本质量
- **特点**: 优化文本表达，限制输出200字符

#### prose_shorter_node
- **功能**: 缩短文本长度
- **特点**: 保持核心含义的同时精简文本

#### prose_longer_node
- **功能**: 扩展文本内容
- **特点**: 在保持原意的基础上丰富内容

#### prose_fix_node
- **功能**: 修复文本问题
- **特点**: 纠正语法、拼写等错误

#### prose_zap_node
- **功能**: 执行自定义命令
- **特点**: 接受用户自定义命令进行灵活的文本操作

## 工作流程

### 1. 状态初始化
```python
state = {
    "content": "待处理的文本",
    "option": "处理选项",
    "command": "自定义命令",
    "output": ""
}
```

### 2. 路由决策
```python
def optional_node(state: ProseState):
    return state["option"]  # 返回对应的处理节点
```

### 3. 节点处理
每个节点执行相同的处理模式：
1. 记录处理日志
2. 获取 LLM 模型
3. 构建消息（系统提示 + 用户内容）
4. 调用模型生成结果
5. 返回输出

### 4. 流式输出
支持流式响应，实时显示处理结果。

## 外部系统集成

### 1. API 接口
- **端点**: `/api/prose/generate`
- **方法**: POST
- **请求**: `GenerateProseRequest`
- **响应**: StreamingResponse（SSE 格式）

### 2. 请求格式
```python
class GenerateProseRequest(BaseModel):
    prompt: str      # 待处理文本
    option: str     # 处理选项
    command: Optional[str]  # 自定义命令
```

### 3. 配置管理
- **LLM 配置**: 通过 `AGENT_LLM_MAP` 配置为 "basic" 类型
- **提示词模板**: 存储在 `src/prompts/prose/` 目录
- **模型选择**: 支持多种 LLM 提供商

### 4. 日志系统
- 集成标准 logging 模块
- 记录处理过程和结果
- 便于调试和监控

## 提示词模板

每个处理节点都有专门的提示词模板：

- `prose_continue.md`: 继续写作提示
- `prose_improver.md`: 文本改进提示
- `prose_shorter.md`: 文本缩短提示
- `prose_longer.md`: 文本扩展提示
- `prose_fix.md`: 文本修复提示
- `prose_zap.md`: 自定义命令提示

## 技术栈

- **框架**: LangGraph
- **LLM**: LangChain 集成
- **消息格式**: LangChain Schema
- **异步支持**: asyncio
- **API 框架**: FastAPI
- **日志**: logging

## 使用示例

### 基本使用
```python
from src.prose.graph.builder import build_graph

# 构建工作流
workflow = build_graph()

# 执行处理
events = workflow.astream({
    "content": "北京天气晴朗",
    "option": "continue"
})

# 流式处理结果
async for _, event in events:
    print(event[0].content)
```

### API 调用
```bash
curl -X POST http://localhost:8000/api/prose/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "北京天气晴朗",
    "option": "continue",
    "command": ""
  }'
```

## 错误处理

- 异常捕获和日志记录
- HTTP 500 错误响应
- 详细的错误信息输出

## 扩展性

### 添加新的处理节点
1. 创建新的节点函数
2. 在 `builder.py` 中注册节点
3. 添加对应的路由规则
4. 创建提示词模板

### 自定义提示词
修改 `src/prompts/prose/` 目录下的模板文件即可调整各个节点的行为。

## 性能考虑

- 流式处理提供实时反馈
- 200字符限制确保响应速度
- 异步处理提高并发性能
- 合理的日志级别避免性能损耗

## 维护和开发

- 代码结构清晰，易于理解和维护
- 每个节点功能单一，便于测试
- 统一的接口设计，便于扩展
- 完整的文档和注释支持