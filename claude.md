# Project: DeerFlow - Deep Research Framework

## 概述

DeerFlow (Deep Exploration and Efficient Research Flow) 是一个基于LangGraph的深度研究框架，专注于结合语言模型与专业工具进行网络搜索、爬虫和Python代码执行等任务。该项目旨在通过智能代理工作流实现复杂的研究任务自动化。

## 架构设计

- **核心架构**: 基于LangGraph的状态图工作流系统
- **代理模式**: 多智能体协作，包括规划者、研究者、协调者、报告者等角色
- **工具集成**: 支持网络搜索、代码执行、爬虫、RAG检索等多种工具
- **模块化设计**: 可扩展的组件架构，支持自定义代理和工具

## 技术栈

- **语言**: Python 3.12+
- **核心框架**: LangGraph, LangChain, FastAPI
- **LLM支持**: OpenAI, DeepSeek, Google AI, Tavily等多种提供商
- **数据存储**: MongoDB, PostgreSQL, Milvus向量数据库
- **Web服务**: FastAPI + Uvicorn
- **部署**: Docker, Volcengine FaaS

## 项目结构

```bash
deer-flow/
├── src/                    # 核心源代码 → ./src/claude.md
│   ├── agents/            # 智能体定义和实现
│   ├── config/            # 配置管理和工具设置
│   ├── graph/             # LangGraph工作流定义
│   ├── llms/              # 大语言模型抽象层
│   ├── prompts/           # 提示词模板和管理
│   ├── rag/               # 检索增强生成组件
│   ├── server/            # FastAPI服务端
│   ├── tools/             # 工具函数和实现
│   ├── podcast/           # 播客生成功能
│   ├── ppt/               # PPT生成功能
│   ├── prose/             # 文本处理功能
│   └── utils/             # 通用工具函数
├── tests/                 # 测试套件 → ./tests/claude.md
├── docs/                  # 文档 → ./docs/claude.md
├── web/                   # Web前端 → ./web/claude.md
├── main.py               # 命令行入口点
├── server.py             # API服务器
└── pyproject.toml        # 项目配置
```

## 核心组件

### 智能体系统 (src/agents/)

- **规划者(Planner)**: 制定研究计划和步骤分解
- **研究者(Researcher)**: 执行网络搜索和信息收集
- **协调者(Coordinator)**: 协调多个研究任务
- **报告者(Reporter)**: 生成最终研究报告
- **编码者(Coder)**: 执行Python代码和数据分析

### 工作流引擎 (src/graph/)

- **状态管理**: 基于LangGraph的状态流转
- **节点执行**: 各个智能体的执行节点
- **检查点**: 支持中断和恢复的检查点机制
- **条件路由**: 基于状态的智能路由

### 工具生态 (src/tools/)

- **搜索工具**: DuckDuckGo, Tavily搜索
- **爬虫工具**: 网页内容提取和解析
- **代码执行**: Python REPL环境
- **RAG检索**: 向量数据库检索
- **TTS**: 文本转语音功能

## 关键入口点

- **主应用**: `main.py` - 命令行交互界面
- **API服务**: `server.py` - FastAPI服务器
- **工作流**: `src/workflow.py` - 核心工作流逻辑
- **配置**: `src/config/configuration.py` - 系统配置管理

## 开发工作流

1. **环境设置**: 使用uv进行依赖管理
2. **代码规范**: 使用ruff进行代码格式化和检查
3. **测试**: pytest框架，支持单元测试和集成测试
4. **部署**: Docker容器化部署

```bash
# 开发环境设置
uv sync
uv run python main.py --interactive

# 运行测试
uv run pytest tests/

# 代码检查
uv run ruff check src/
uv run ruff format src/
```

## 导航索引

📖 **完整导航**: [NAVIGATION.md](./NAVIGATION.md) - 详细的功能地图和快速导航

### 核心模块
- **配置管理**: [src/config/claude.md](./src/config/claude.md) - 系统配置、代理设置、工具配置
- **工作流定义**: [src/graph/claude.md](./src/graph/claude.md) - LangGraph状态图和节点定义
- **智能体实现**: [src/agents/claude.md](./src/agents/claude.md) - 各个智能体的具体实现
- **工具集成**: [src/tools/claude.md](./src/tools/claude.md) - 搜索、爬虫、代码执行等工具

### 支持系统
- **提示词管理**: [src/prompts/claude.md](./src/prompts/claude.md) - 各个角色的提示词模板
- **LLM抽象层**: [src/llms/claude.md](./src/llms/claude.md) - 大语言模型接口和提供商
- **RAG系统**: [src/rag/claude.md](./src/rag/claude.md) - 检索增强生成相关组件
- **服务接口**: [src/server/claude.md](./src/server/claude.md) - FastAPI API服务

### 扩展功能
- **播客生成**: [src/podcast/claude.md](./src/podcast/claude.md) - 音频内容生成
- **PPT生成**: [src/ppt/claude.md](./src/ppt/claude.md) - 演示文稿生成
- **文本处理**: [src/prose/claude.md](./src/prose/claude.md) - 文本编辑和优化

### 测试与前端
- **测试系统**: [tests/claude.md](./tests/claude.md) - 单元测试和集成测试
- **前端界面**: [web/claude.md](./web/claude.md) - Next.js Web应用

## 功能特性

- **多模态输出**: 支持文本、音频、PPT等多种格式
- **MCP集成**: 支持Model Context Protocol服务
- **背景研究**: 自动进行背景信息收集
- **多语言支持**: 中英文界面和提示词
- **容错处理**: 完善的错误处理和重试机制
- **可扩展性**: 模块化设计，易于添加新功能

## 部署选项

- **本地部署**: 命令行运行
- **Docker部署**: 容器化部署
- **云服务**: Volcengine FaaS一键部署
- **API服务**: RESTful API接口
