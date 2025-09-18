# PPT 生成模块文档

## 概述

PPT 生成模块是 deer-flow 研究框架中的专门组件，负责将文本内容转换为专业的 PowerPoint 演示文稿。该模块采用基于 LangGraph 的工作流设计，实现了内容生成和文件编译的自动化流程。

## 目录结构

```
src/ppt/
├── graph/
│   ├── state.py              # PPT 生成状态管理
│   ├── builder.py            # 工作流构建器
│   ├── ppt_composer_node.py  # PPT 内容生成节点
│   └── ppt_generator_node.py # PPT 文件生成节点
└── claude.md                 # 本文档
```

## 核心组件

### 1. 状态管理 (state.py)

**PPTState** 类继承自 LangGraph 的 MessagesState，定义了 PPT 生成过程中的数据流：

- **input**: 输入的文本内容（字符串）
- **generated_file_path**: 生成的 PPT 文件路径（输出）
- **ppt_content**: 生成的 PPT 内容（字符串）
- **ppt_file_path**: 临时 Markdown 文件路径

### 2. 工作流构建器 (builder.py)

**build_graph()** 函数创建了一个两阶段的线性工作流：

```
START → ppt_composer → ppt_generator → END
```

- **ppt_composer**: 内容生成节点
- **ppt_generator**: 文件编译节点

### 3. PPT 内容生成节点 (ppt_composer_node.py)

**功能**: 将输入文本转换为 Markdown 格式的 PPT 内容

**实现细节**:
- 使用配置的 LLM 模型（通过 `AGENT_LLM_MAP["ppt_composer"]`）
- 调用专门的提示词模板 (`ppt/ppt_composer.md`)
- 生成专业的 Markdown 格式演示文稿
- 将结果保存为临时文件

**依赖项**:
- `src.config.agents.AGENT_LLM_MAP`
- `src.llms.llm.get_llm_by_type`
- `src.prompts.template.get_prompt_template`

### 4. PPT 文件生成节点 (ppt_generator_node.py)

**功能**: 将 Markdown 内容编译为最终的 PPTX 文件

**实现细节**:
- 使用 Marp CLI 工具进行转换
- 生成唯一的文件名（使用 UUID）
- 自动清理临时文件
- 返回生成的 PPT 文件路径

**依赖项**:
- Marp CLI（外部依赖，需要单独安装）

## 工作流程

### 阶段 1: 内容生成
1. 接收用户输入的文本内容
2. 调用 LLM 进行内容处理和格式化
3. 生成符合 Marp 规范的 Markdown 文件
4. 保存为临时文件

### 阶段 2: 文件编译
1. 读取临时 Markdown 文件
2. 使用 Marp CLI 转换为 PPTX 格式
3. 生成最终的演示文稿文件
4. 清理临时文件

## 外部集成

### API 端点
- **POST `/api/ppt/generate`**: 接收文本内容，返回 PPT 文件

### 请求模型
```python
class GeneratePPTRequest(BaseModel):
    content: str = Field(..., description="The content of the ppt")
```

### 配置集成
- **代理配置**: 在 `src/config/agents.py` 中定义 `ppt_composer` 代理
- **LLM 映射**: 使用 "basic" 类型的 LLM
- **提示词**: 专用提示词模板位于 `src/prompts/ppt/ppt_composer.md`

## 提示词系统

PPT 生成使用专门的提示词模板，确保输出质量：

### 核心指导原则
- 直接开始演示文稿内容，无需介绍性语句
- 使用标准 Markdown 格式（标题、列表、分隔符等）
- 每页幻灯片聚焦一个主要观点
- 只使用源内容中提供的图片 URL

### 输出格式规范
- 使用 `#` 表示标题页
- 使用 `##` 表示幻灯片标题
- 使用 `---` 分隔幻灯片
- 支持有序和无序列表
- 支持代码块和图片

## 依赖项要求

### 系统依赖
- **Marp CLI**: 用于 Markdown 到 PPTX 的转换
  - 安装: `npm install -g @marp-team/marp-cli`

### Python 依赖
- LangGraph (工作流引擎)
- LangChain (LLM 集成)
- uuid (文件名生成)
- subprocess (外部工具调用)

## 使用示例

### 直接使用工作流
```python
from src.ppt.graph.builder import build_graph

workflow = build_graph()
final_state = workflow.invoke({"input": report_content})
ppt_path = final_state["generated_file_path"]
```

### 通过 API 使用
```python
import requests

response = requests.post(
    "http://localhost:8000/api/ppt/generate",
    json={"content": "演示文稿内容"}
)

# 保存 PPT 文件
with open("output.pptx", "wb") as f:
    f.write(response.content)
```

## 设计模式

### 1. 状态机模式
使用 LangGraph 的状态图管理生成流程，确保数据在各节点间正确传递。

### 2. 节点分离
将内容生成和文件编译分离为独立节点，提高模块化和可维护性。

### 3. 临时文件管理
自动创建和清理临时文件，避免资源泄漏。

## 错误处理

### 当前实现
- 基本的异常处理在 API 层面
- 临时文件在成功生成后自动清理

### 改进建议
- 添加节点级别的错误处理
- 实现 Marp CLI 可用性检查
- 添加内容验证机制

## 扩展性

### 可能的扩展方向
1. **多语言支持**: 添加国际化功能
2. **模板系统**: 支持不同的 PPT 模板
3. **图片处理**: 自动优化和插入图片
4. **样式自定义**: 允许用户自定义样式和主题
5. **批量生成**: 支持批量 PPT 生成

## 维护说明

### 关键维护点
1. **提示词模板**: 定期更新和优化提示词
2. **Marp CLI**: 确保 CLI 版本兼容性
3. **LLM 配置**: 根据模型性能调整配置
4. **错误日志**: 监控和改进错误处理

### 测试建议
1. 单元测试各个节点的功能
2. 集成测试完整工作流
3. 性能测试大规模内容处理
4. 兼容性测试不同输入格式