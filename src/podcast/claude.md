# Podcast 模块文档

## 概述

Podcast 模块是一个基于 LangGraph 的播客生成系统，能够将文本内容转换为双人对话形式的播客音频。该模块采用工作流模式，通过多个节点的协作完成从内容处理到音频生成的完整流程。

## 目录结构

```
src/podcast/
├── types.py                    # 数据类型定义
├── graph/                      # 工作流图相关组件
│   ├── state.py               # 工作流状态定义
│   ├── builder.py             # 工作流构建器
│   ├── script_writer_node.py  # 脚本编写节点
│   ├── tts_node.py            # 语音合成节点
│   └── audio_mixer_node.py    # 音频混合节点
└── claude.md                  # 本文档
```

## 核心组件

### 1. 数据模型 (`types.py`)

#### ScriptLine
- **功能**: 表示播客中的单行对话
- **字段**:
  - `speaker`: 说话人角色 ("male" | "female")
  - `paragraph`: 对话内容文本

#### Script
- **功能**: 完整的播客脚本
- **字段**:
  - `locale`: 语言环境 ("en" | "zh")
  - `lines`: 脚本行列表 (ScriptLine[])

### 2. 工作流状态 (`graph/state.py`)

#### PodcastState
继承自 LangGraph 的 MessagesState，管理播客生成过程中的状态：

**输入字段**:
- `input`: 原始输入内容 (str)

**输出字段**:
- `output`: 最终生成的音频数据 (bytes | None)

**中间状态**:
- `script`: 生成的播客脚本 (Script | None)
- `audio_chunks`: 音频片段列表 (bytes[])

### 3. 工作流构建器 (`graph/builder.py`)

#### 工作流程
采用线性工作流，包含三个主要节点：

```
START → script_writer → tts → audio_mixer → END
```

#### 节点功能
1. **script_writer**: 将输入内容转换为播客脚本
2. **tts**: 将脚本转换为音频片段
3. **audio_mixer**: 合并音频片段为最终音频

## 工作流节点详解

### 1. 脚本编写节点 (`script_writer_node.py`)

**功能**:
- 使用 LLM 将原始内容转换为双人对话脚本
- 支持中英文双语
- 生成符合播客风格的对话内容

**技术实现**:
- 使用 `get_llm_by_type()` 获取配置的 LLM
- 通过 `with_structured_output()` 确保 JSON 格式输出
- 使用系统提示词 "podcast/podcast_script_writer" 指导生成

**配置**:
- LLM 类型: `basic` (在 `config/agents.py` 中配置)
- 提示词模板: `podcast/podcast_script_writer.md`

### 2. 语音合成节点 (`tts_node.py`)

**功能**:
- 将脚本中的每行对话转换为音频
- 支持男声 (BV002_streaming) 和女声 (BV001_streaming)
- 使用字节火山引擎 TTS 服务

**技术实现**:
- 集成 `VolcengineTTS` 服务
- 根据说话人性别选择不同的声音类型
- 将 base64 编码的音频数据解码为字节
- 语音速度设置为 1.05 倍速

**环境变量配置**:
- `VOLCENGINE_TTS_APPID`: 字节火山 TTS 应用 ID
- `VOLCENGINE_TTS_ACCESS_TOKEN`: 访问令牌
- `VOLCENGINE_TTS_CLUSTER`: 集群名称 (默认: volcano_tts)

### 3. 音频混合节点 (`audio_mixer_node.py`)

**功能**:
- 将所有音频片段按顺序合并
- 生成最终的完整播客音频

**技术实现**:
- 使用字节串连接 (`b"".join()`) 合并音频片段
- 输出为原始音频数据 (bytes)

## 外部系统集成

### 1. LLM 服务
- **来源**: `src.llms.llm.get_llm_by_type()`
- **用途**: 脚本内容生成
- **配置**: 通过 `config/agents.py` 中的 `AGENT_LLM_MAP` 管理

### 2. TTS 服务
- **提供商**: 字节火山引擎 (Volcengine)
- **服务类**: `src.tools.tts.VolcengineTTS`
- **语音类型**:
  - 男声: BV002_streaming
  - 女声: BV001_streaming

### 3. 提示词系统
- **路径**: `src/prompts/podcast/podcast_script_writer.md`
- **风格**: "Hello Deer" 播客节目
- **特点**: 双人对话、自然口语化、10分钟时长

## API 接口

### 生成播客
- **端点**: `POST /api/podcast/generate`
- **输入**: 文本内容
- **输出**: 音频文件 (MP3 格式)
- **位置**: `src/server/app.py`

## 使用示例

```python
from src.podcast.graph.builder import build_graph

# 构建工作流
workflow = build_graph()

# 执行播客生成
content = "要转换为播客的内容"
result = workflow.invoke({"input": content})

# 获取生成的音频
audio_data = result["output"]

# 保存音频文件
with open("podcast.mp3", "wb") as f:
    f.write(audio_data)
```

## 配置要点

### 1. 代理配置
在 `config/agents.py` 中配置:
```python
"podcast_script_writer": "basic"
```

### 2. 环境变量
确保以下环境变量已设置:
- `VOLCENGINE_TTS_APPID`
- `VOLCENGINE_TTS_ACCESS_TOKEN`
- `VOLCENGINE_TTS_CLUSTER`

### 3. 提示词定制
编辑 `src/prompts/podcast/podcast_script_writer.md` 来调整:
- 播客风格和语调
- 对话结构
- 语言偏好
- 内容长度

## 扩展性设计

### 1. 节点扩展
- 可以轻松添加新的处理节点（如：音效添加、背景音乐）
- 支持并行处理节点

### 2. 语音扩展
- 支持添加更多语音类型
- 可集成其他 TTS 服务提供商

### 3. 语言扩展
- 当前支持中英文
- 可扩展支持更多语言

## 注意事项

1. **音频质量**: TTS 服务质量和网络连接会影响最终音频质量
2. **内容长度**: 建议输入内容适合生成 10 分钟左右的播客
3. **语言一致性**: 确保输入语言与目标播客语言匹配
4. **错误处理**: 各节点都有基础的错误处理和日志记录
5. **资源管理**: 音频数据在内存中处理，大文件可能需要流式处理

## 相关文档

- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [字节火山引擎 TTS 文档](https://www.volcengine.com/)
- [Pydantic 数据验证](https://pydantic-docs.helpmanual.io/)