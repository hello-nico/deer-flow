# DeerFlow Web 前端文档

## 📋 概述

DeerFlow Web 是一个基于 Next.js 的现代化研究框架前端界面，采用 React 19、TypeScript 和 Tailwind CSS 构建。该前端为 DeerFlow AI 研究助手提供了用户友好的交互界面，支持多语言、实时流式响应和深度思考功能。

## 🛠️ 技术栈

### 核心框架
- **Next.js 15.4.7** - React 全栈框架，支持 Turbopack 开发模式
- **React 19.0.0** - 最新的 React 版本
- **TypeScript 5.8.2** - 类型安全的 JavaScript 超集
- **Tailwind CSS 4.0.15** - 原子化 CSS 框架
- **Zustand 5.0.3** - 轻量级状态管理

### UI 组件库
- **Radix UI** - 无样式的可访问性组件基础
- **Shadcn/ui** - 基于 Radix UI 的组件库
- **Lucide React** - 现代化图标库
- **Framer Motion 12.6.5** - 动画库

### 编辑器和文档处理
- **TipTap 2.12.0** - 富文本编辑器
- **React Markdown 10.1.0** - Markdown 渲染
- **KaTeX** - 数学公式渲染
- **Highlight.js** - 代码高亮

### 工具库
- **React Hook Form 7.56.1** + **Zod 3.24.3** - 表单处理和验证
- **next-intl 4.3.1** - 国际化支持
- **next-themes 0.4.6** - 主题切换
- **immer 10.1.1** - 不可变数据操作

## 📁 目录结构

```
web/
├── src/
│   ├── app/                          # Next.js App Router
│   │   ├── chat/                     # 聊天界面
│   │   ├── landing/                  # 首页营销页面
│   │   └── settings/                 # 设置页面
│   ├── components/                   # React 组件
│   │   ├── deer-flow/               # 项目特定组件
│   │   ├── editor/                  # 富文本编辑器
│   │   ├── magicui/                 # 特效组件
│   │   └── ui/                      # 基础 UI 组件
│   ├── core/                        # 核心功能模块
│   │   ├── api/                     # API 调用和类型
│   │   ├── config/                  # 配置管理
│   │   ├── mcp/                     # MCP 工具集成
│   │   ├── messages/                # 消息处理
│   │   ├── rehype/                  # Markdown 处理
│   │   ├── replay/                  # 回放功能
│   │   ├── sse/                     # 服务器推送事件
│   │   ├── store/                   # 状态管理
│   │   └── utils/                   # 工具函数
│   ├── hooks/                       # React Hooks
│   ├── lib/                         # 库文件
│   ├── styles/                      # 样式文件
│   └── typings/                     # TypeScript 类型定义
├── public/                          # 静态资源
│   ├── images/                      # 图片资源
│   ├── mock/                        # 模拟数据
│   └── replay/                      # 回放数据
├── docs/                            # 项目文档
└── messages/                        # 国际化文本
```

## 🎯 核心功能模块

### 1. 聊天界面 (`src/app/chat/`)
- **主聊天窗口**: 支持实时流式对话
- **消息列表**: 显示用户和 AI 的对话历史
- **输入框**: 支持文本输入和文件上传
- **思考块**: 显示 AI 的深度思考过程
- **计划卡片**: 展示研究计划和执行步骤

### 2. 状态管理 (`src/core/store/`)
- **全局状态**: 使用 Zustand 管理应用状态
- **消息状态**: 管理对话消息和流式更新
- **设置状态**: 用户配置和应用偏好
- **实时更新**: 支持流式数据的实时状态同步

### 3. API 集成 (`src/core/api/`)
- **聊天 API**: 与后端服务进行流式通信
- **MCP 集成**: 支持多工具协作协议
- **RAG 功能**: 检索增强生成功能
- **错误处理**: 完善的错误处理和重试机制

### 4. 深度思考功能
- **思考过程展示**: 实时显示 AI 的推理过程
- **智能折叠**: 思考完成后自动折叠，保持界面整洁
- **主题切换**: 思考阶段使用特殊主题，完成后恢复默认
- **流式支持**: 支持推理内容的实时流式显示

### 5. 国际化支持
- **多语言**: 支持中文和英文
- **动态切换**: 用户可实时切换语言
- **本地化**: 所有界面文本都支持本地化

## 🔧 配置和构建

### 环境变量
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api  # 后端 API 地址
NEXT_PUBLIC_STATIC_WEBSITE_ONLY=false         # 是否为静态网站模式
AMPLITUDE_API_KEY=                            # 用户行为分析密钥
```

### 开发模式
```bash
# 使用 Turbopack 加速开发
pnpm dev

# 类型检查
pnpm typecheck

# 代码检查和格式化
pnpm lint && pnpm format:check
```

### 生产构建
```bash
# 构建生产版本
pnpm build

# 预览生产版本
pnpm preview
```

## 🎨 设计系统

### 颜色主题
- **浅色模式**: 默认的明亮配色
- **深色模式**: 适合夜间使用的深色配色
- **思考主题**: 深度思考时的特殊蓝色主题

### 组件规范
- **一致性**: 所有组件遵循统一的设计规范
- **可访问性**: 支持键盘导航和屏幕阅读器
- **响应式**: 适配不同屏幕尺寸

### 动画效果
- **流畅过渡**: 使用 Framer Motion 实现平滑动画
- **微交互**: 按钮悬停、点击等交互反馈
- **加载状态**: 优雅的加载动画和骨架屏

## 🚀 核心特性

### 1. 实时流式响应
- 支持 SSE (Server-Sent Events) 实现实时数据推送
- 逐字显示 AI 响应，提供更好的用户体验
- 支持中断和继续对话

### 2. 多工具协作
- 集成 MCP (Multi-tool Collaboration Protocol)
- 支持多种 AI 工具的协同工作
- 动态工具调用和结果展示

### 3. 研究工作流
- **计划制定**: AI 自动制定研究计划
- **步骤执行**: 按步骤执行研究任务
- **结果汇总**: 生成完整的研究报告

### 4. 回放功能
- 支持对话回放用于演示和调试
- 预置多个研究场景的回放数据
- 支持加速播放和正常速度

## 🔗 与后端集成

### API 端点
- `/api/chat/stream` - 流式聊天接口
- `/api/settings` - 设置管理接口
- `/api/rag` - RAG 功能接口

### 数据流
1. **用户输入** → 前端验证 → 发送到后端
2. **后端处理** → 流式返回事件 → 前端实时更新
3. **状态同步** → 前端状态管理 → UI 更新

### 错误处理
- 网络错误重试机制
- 友好的错误提示
- 降级处理方案

## 🧪 测试和调试

### 模拟数据
- `/public/mock/` - 包含各种测试场景的模拟数据
- 支持 URL 参数控制模拟模式
- 用于开发测试和功能演示

### 开发工具
- **React Scan** - 性能分析工具
- **ESLint** - 代码质量检查
- **Prettier** - 代码格式化
- **TypeScript** - 类型检查

## 📦 部署选项

### Docker 部署
```bash
# 构建镜像
docker build --build-arg NEXT_PUBLIC_API_URL=YOUR_API -t deer-flow-web .

# 运行容器
docker run -d -p 3000:3000 --env-file .env deer-flow-web
```

### Docker Compose
```yaml
# 使用 docker-compose.yml
docker compose build
docker compose up
```

## 🔄 开发工作流

### 代码规范
- 使用 ESLint 进行代码检查
- 使用 Prettier 进行代码格式化
- 使用 TypeScript 确保类型安全

### 提交前检查
```bash
pnpm check  # 运行所有检查
pnpm lint   # 代码检查
pnpm typecheck  # 类型检查
```

## 📚 相关文档

- [深度思考功能设计](./docs/thought-block-feature.md)
- [实现总结](./docs/implementation-summary.md)
- [交互流程测试](./docs/interaction-flow-test.md)
- [流式优化](./docs/streaming-improvements.md)

## 🤝 贡献指南

1. 遵循项目的代码规范
2. 确保类型安全
3. 添加必要的测试
4. 更新相关文档
5. 提交前运行完整检查

## 📄 许可证

本项目采用 MIT 许可证，详见项目根目录的 LICENSE 文件。