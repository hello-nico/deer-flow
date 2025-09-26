# src/prompts 目录分析文档

## 目录概述

`src/prompts` 目录是 DeerFlow 多智能体研究框架的核心提示词管理系统，包含了各个角色的提示词模板、数据模型和模板引擎。该目录采用模块化设计，支持动态提示词生成和多语言适配。

## 目录结构

```
src/prompts/
├── __init__.py                 # 模块导出接口
├── template.py                 # Jinja2 模板引擎
├── planner_model.py           # Planner 角色的数据模型
├── planner.md                  # Planner 角色提示词
├── researcher.md               # Researcher 角色提示词
├── reporter.md                 # Reporter 角色提示词
├── coordinator.md             # Coordinator 角色提示词
├── coder.md                    # Coder 角色提示词
├── podcast/                    # 播客相关提示词
│   └── podcast_script_writer.md
├── ppt/                        # 演示文稿相关提示词
│   └── ppt_composer.md
├── prompt_enhancer/            # 提示词增强工具
│   └── prompt_enhancer.md
└── prose/                      # 文本处理工具
    ├── prose_continue.md
    ├── prose_fix.md
    ├── prose_improver.md
    ├── prose_longer.md
    ├── prose_shorter.md
    └── prose_zap.md
```

## 核心组件分析

### 1. 模板引擎系统 (`template.py`)

**功能**: 基于 Jinja2 的动态提示词生成系统

**核心特性**:
- 使用 Jinja2 模板引擎加载 `.md` 文件
- 支持变量替换和动态内容生成
- 自动注入时间戳和配置参数
- 与 LangGraph 的 AgentState 集成

**主要函数**:
- `get_prompt_template()`: 加载原始模板
- `apply_prompt_template()`: 应用变量并格式化为消息列表

**变量注入**:
- `CURRENT_TIME`: 当前时间戳
- AgentState 中的所有变量
- Configuration 配置参数

### 2. 数据模型定义 (`planner_model.py`)

**Plan 模型**:
```python
class Plan(BaseModel):
    locale: str                    # 语言环境 (en-US/zh-CN)
    has_enough_context: bool      # 上下文充足性判断
    thought: str                   # 思考过程
    title: str                     # 计划标题
    steps: List[Step]             # 执行步骤列表
```

**Step 模型**:
```python
class Step(BaseModel):
    need_search: bool              # 是否需要搜索
    title: str                     # 步骤标题
    description: str               # 详细描述
    step_type: StepType            # 步骤类型 (research/processing)
    execution_res: Optional[str]   # 执行结果
```

## 角色提示词设计

### 1. Planner (规划者)

**角色定位**: 专业深度研究员，负责制定信息收集计划

**核心职责**:
- 分析用户需求，制定研究计划
- 评估上下文充足性
- 分解任务为可执行的步骤
- 确保信息收集的全面性和深度

**关键特性**:
- 严格的信息质量标准
- 8个维度的分析框架
- 步骤类型区分 (research/processing)
- 动态步骤数量限制

### 2. Researcher (研究员)

**角色定位**: 信息搜集专家，负责执行搜索任务

**工具支持**:
- 内置工具: web_search, crawl_tool, local_search_tool
- 动态加载工具: 专业化搜索工具、地图工具等

**工作流程**:
1. 理解问题
2. 评估可用工具
3. 制定解决方案
4. 执行搜索
5. 综合信息

**输出要求**:
- 结构化 Markdown 格式
- 按主题而非工具组织
- 严格的引用格式
- 多语言支持

### 3. Reporter (报告员)

**角色定位**: 专业报告撰写者，支持多种写作风格

**写作风格支持**:
- `academic`: 学术严谨风格
- `popular_science`: 科普传播风格
- `news`: 新闻报道风格
- `social_media`: 社交媒体风格 (支持中英文)

**报告结构**:
1. 标题
2. 关键要点
3. 概述
4. 详细分析
5. 调查笔记 (风格化)
6. 关键引用

**格式特色**:
- 动态风格切换
- 表格数据展示
- 图片集成
- 严格的引用规范

### 4. Coordinator (协调者)

**角色定位**: 前台接待员，处理用户交互

**职责分类**:
1. **直接处理**: 问候、闲聊
2. **礼貌拒绝**: 安全风险请求
3. **转交规划**: 研究性问题

**核心功能**:
- 多语言支持
- 请求分类和路由
- 安全过滤
- 上下文收集

### 5. Coder (程序员)

**角色定位**: Python 脚本专家

**专长领域**:
- 数据分析和算法实现
- 金融数据处理 (yfinance)
- 数学计算和统计
- 代码优化和调试

**技术栈**:
- pandas, numpy
- yfinance
- 标准库支持

## 专业工具模块

### 1. Prompt Enhancer (提示词增强器)

**功能**: 优化用户提示词，提高 AI 输出质量

**增强策略**:
- 添加具体性和上下文
- 改善结构和清晰度
- 适配不同写作风格
- 保持用户原始意图

**风格化增强**:
- 学术风格: 方法论、理论框架
- 科普风格: 可访问性、故事性
- 新闻风格: 新闻价值、平衡性
- 社交媒体: 参与度、分享性

### 2. PPT Composer (演示文稿生成器)

**功能**: 将内容转换为 Markdown 格式的演示文稿

**格式规范**:
- `#` 标题页
- `##` 幻灯片标题
- `---` 分页符
- 列表和代码块

**工作流程**:
1. 理解用户需求
2. 提取核心内容
3. 组织结构
4. 创建 Markdown
5. 优化审查

### 3. Prose Tools (文本处理工具集)

**功能集合**:
- `prose_improver`: 文本改进 (200字符限制)
- `prose_longer`: 文本扩展
- `prose_shorter`: 文本缩短
- `prose_continue`: 文本续写
- `prose_fix`: 文本修正
- `prose_zap`: 文本清理

### 4. Podcast Script Writer (播客脚本生成器)

**功能**: 生成专业的播客脚本内容

**特色**: 专门的对话式内容生成，支持播客节目格式

## 技术特点

### 1. 模板化设计
- 使用 Jinja2 实现动态模板
- 支持条件渲染和循环
- 变量注入和配置管理

### 2. 多语言支持
- 基于 locale 参数的语言切换
- 中英文风格适配
- 文化本地化考虑

### 3. 类型安全
- Pydantic 模型验证
- 明确的数据结构定义
- 运行时类型检查

### 4. 模块化架构
- 角色职责分离
- 工具插件化
- 可扩展的设计模式

## 使用模式

### 1. 基本流程
```python
from src.prompts import apply_prompt_template

# 应用模板生成系统提示
messages = apply_prompt_template("planner", state, config)
```

### 2. 动态配置
- 通过 Configuration 对象注入参数
- 支持运行时配置调整
- 环境变量集成

### 3. 扩展机制
- 新增角色: 创建 .md 文件和对应模型
- 新增工具: 在提示词中声明工具接口
- 新增风格: 在 reporter.md 中添加风格分支

## 设计原则

1. **单一职责**: 每个角色专注特定任务
2. **配置驱动**: 通过配置控制行为
3. **类型安全**: 使用 Pydantic 确保数据完整性
4. **可扩展性**: 模块化设计便于功能扩展
5. **用户友好**: 清晰的接口和文档

## 维护建议

1. **版本控制**: 对提示词变更进行版本管理
2. **测试覆盖**: 为新增功能编写测试用例
3. **文档更新**: 及时更新角色职责说明
4. **性能优化**: 监控模板渲染性能
5. **安全审计**: 定期检查提示词安全性

## 总结

`src/prompts` 目录实现了一个完整的多智能体提示词管理系统，通过模板化、模块化和类型安全的设计，支持复杂的研究任务执行。系统具有良好的可扩展性和维护性，为 DeerFlow 框架提供了强大的提示词管理能力。