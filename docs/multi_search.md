# 多种搜索引擎对 Deer-Flow 执行流程的影响分析

## 概述

本文档详细分析了在 deer-flow 项目中采用多种搜索引擎对执行流程的影响。通过对项目代码的深入分析，阐述了多搜索引擎集成对系统架构、执行性能、用户体验等方面的影响。

## 当前搜索引擎架构

### 支持的搜索引擎

Deer-Flow 项目目前支持多种搜索引擎：

- **Tavily** (默认) - 高级搜索引擎，支持图片搜索和原始内容
- **DuckDuckGo** - 基础网页搜索
- **Brave Search** - Brave 搜索引擎
- **ArXiv** - 学术论文搜索
- **Wikipedia** - 维基百科搜索

### 搜索引擎配置

```python
# 从 src/tools/search.py 可以看出
SELECTED_SEARCH_ENGINE = os.getenv("SEARCH_API", SearchEngine.TAVILY.value)

# 配置文件支持
def get_search_config():
    config = load_yaml_config("conf.yaml")
    search_config = config.get("SEARCH_ENGINE", {})
    return search_config
```

### 搜索引擎工具化

所有搜索引擎都被封装为 LangChain 工具，并通过装饰器提供日志记录功能：

```python
# 创建带日志的搜索工具
LoggedTavilySearch = create_logged_tool(TavilySearchWithImages)
LoggedDuckDuckGoSearch = create_logged_tool(DuckDuckGoSearchResults)
LoggedBraveSearch = create_logged_tool(BraveSearch)
LoggedArxivSearch = create_logged_tool(ArxivQueryRun)
LoggedWikipediaSearch = create_logged_tool(WikipediaQueryRun)
```

## 执行流程中的搜索引擎使用

### 1. 背景调查阶段 (`background_investigation_node`)

背景调查节点是搜索引擎的主要使用场景，用于收集用户查询的背景信息：

```python
# src/graph/nodes.py:52-75
def background_investigation_node(state: State, config: RunnableConfig):
    logger.info("background investigation node is running.")
    configurable = Configuration.from_runnable_config(config)
    query = state.get("research_topic")
    background_investigation_results = None

    if SELECTED_SEARCH_ENGINE == SearchEngine.TAVILY.value:
        # 直接使用 Tavily 进行搜索
        searched_content = LoggedTavilySearch(
            max_results=configurable.max_search_results
        ).invoke(query)
        # 处理搜索结果
        if isinstance(searched_content, tuple):
            searched_content = searched_content[0]
        if isinstance(searched_content, list):
            background_investigation_results = [
                f"## {elem['title']}\n\n{elem['content']}" for elem in searched_content
            ]
            return {
                "background_investigation_results": "\n\n".join(
                    background_investigation_results
                )
            }
    else:
        # 使用其他搜索引擎
        background_investigation_results = get_web_search_tool(
            configurable.max_search_results
        ).invoke(query)

    return {
        "background_investigation_results": json.dumps(
            background_investigation_results, ensure_ascii=False
        )
    }
```

### 2. 研究阶段 (`researcher_node`) 的深入分析

#### 当前研究阶段的搜索引擎支持现状

经过深入代码分析，**研究阶段目前并不支持多种搜索引擎**。让我详细说明：

##### 1. 当前实现机制

在 `researcher_node` 中 (`src/graph/nodes.py:486`)：

```python
async def researcher_node(state: State, config: RunnableConfig) -> Command[Literal["research_team"]]:
    """Researcher node that do research"""
    logger.info("Researcher node is researching.")
    configurable = Configuration.from_runnable_config(config)
    tools = [get_web_search_tool(configurable.max_search_results), crawl_tool]
    retriever_tool = get_retriever_tool(state.get("resources", []))
    if retriever_tool:
        tools.insert(0, retriever_tool)  # 本地搜索工具优先插入
    logger.info(f"Researcher tools: {tools}")
    return await _setup_and_execute_agent_step(state, config, "researcher", tools)
```

##### 2. 关键发现

**研究阶段只有一个 Web 搜索工具**：

- `get_web_search_tool()` 函数返回**单一**的搜索引擎实例
- 通过 `SELECTED_SEARCH_ENGINE` 环境变量决定使用哪个搜索引擎
- 研究员只能使用一个配置的搜索引擎

**get_web_search_tool 函数的实现** (`src/tools/search.py:43`)：

```python
def get_web_search_tool(max_search_results: int):
    search_config = get_search_config()

    if SELECTED_SEARCH_ENGINE == SearchEngine.TAVILY.value:
        # 返回 Tavily 搜索工具
        return LoggedTavilySearch(...)
    elif SELECTED_SEARCH_ENGINE == SearchEngine.DUCKDUCKGO.value:
        # 返回 DuckDuckGo 搜索工具
        return LoggedDuckDuckGoSearch(...)
    # 其他搜索引擎...
```

##### 3. 研究阶段的工具集

当前研究阶段的工具集：

```python
tools = [
    get_web_search_tool(configurable.max_search_results),  # 单一搜索引擎
    crawl_tool,                                           # 爬虫工具
    retriever_tool,                                       # 本地检索工具（如果有）
]
```

#### 本地搜索的优先级机制

##### 1. 工具插入顺序决定优先级

在 `researcher_node` 中的关键代码：

```python
tools = [get_web_search_tool(configurable.max_search_results), crawl_tool]
retriever_tool = get_retriever_tool(state.get("resources", []))
if retriever_tool:
    tools.insert(0, retriever_tool)  # 插入到第一个位置
```

**关键点**：

- 初始工具列表：`[web_search_tool, crawl_tool]`
- 如果 `retriever_tool` 存在，使用 `tools.insert(0, retriever_tool)` 将其插入到**第一个位置**
- 最终工具列表：`[local_search_tool, web_search_tool, crawl_tool]`

##### 2. 本地搜索工具的描述

在 `RetrieverTool` 类中 (`src/tools/retriever.py:26`)：

```python
class RetrieverTool(BaseTool):
    name: str = "local_search_tool"
    description: str = "Useful for retrieving information from the file with `rag://` uri prefix, it should be higher priority than the web search or writing code. Input should be a search keywords."
```

**工具描述明确说明**：

- "it should be higher priority than the web search or writing code"
- 明确指示 LLM 优先使用本地搜索工具

##### 3. 本地搜索工具的创建逻辑

`get_retriever_tool` 函数 (`src/tools/retriever.py:53-61`)：

```python
def get_retriever_tool(resources: List[Resource]) -> RetrieverTool | None:
    if not resources:
        return None
    logger.info(f"create retriever tool: {SELECTED_RAG_PROVIDER}")
    retriever = build_retriever()

    if not retriever:
        return None
    return RetrieverTool(retriever=retriever, resources=resources)
```

**创建条件**：

- 只有当 `resources` 不为空时才会创建本地搜索工具
- `resources` 来自 `state.get("resources", [])`
- RAG 系统必须正确配置和初始化

#### 工具选择和优先级设计

##### 1. LLM 工具选择机制

当 LLM 决定使用哪个工具时：

1. **工具顺序影响**：在工具列表中排在前面的工具更容易被选中
2. **描述影响**：`RetrieverTool` 的描述明确说明它应该具有更高的优先级
3. **语义匹配**：LLM 会根据查询内容选择最合适的工具

##### 2. 实际使用场景

**有本地搜索的情况**：

```
工具列表：[local_search_tool, web_search_tool, crawl_tool]

查询："查找公司内部关于机器学习的文档"
→ LLM 优先选择 local_search_tool
→ 在本地知识库中搜索
→ 如果本地没有结果，可能会使用 web_search_tool
```

**没有本地搜索的情况**：

```
工具列表：[web_search_tool, crawl_tool]

查询："查找关于机器学习的最新研究"
→ LLM 使用 web_search_tool
→ 在网络上搜索
```

##### 3. 优先级设计的优势

这种优先级设计符合信息检索的最佳实践：

1. **优先使用本地知识**：更相关、更可靠、更安全
2. **fallback 到网络搜索**：当本地没有结果时再查询网络
3. **减少 API 成本**：优先使用本地资源减少外部 API 调用
4. **提高响应速度**：本地搜索通常比网络搜索更快

#### 与背景调查阶段的对比

**背景调查阶段** (`background_investigation_node`)：

- 对 Tavily 有特殊处理逻辑
- 对其他搜索引擎使用通用的 `get_web_search_tool()`
- **同样只支持单一搜索引擎**

**研究阶段** (`researcher_node`)：

- 直接使用 `get_web_search_tool()` 获取搜索工具
- **只支持单一搜索引擎**
- 但支持本地搜索的优先级机制

### 3. 完整执行流程

```
用户输入 → 协调器 → 背景调查 → 规划器 → 研究团队 → 研究员 → 报告器
           └── 使用单一搜索引擎 ──┘
```

## 采用多种搜索引擎的执行流程影响

### 1. 背景调查阶段的扩展

**当前流程**：

```
用户输入 → 协调器 → 背景调查 → 规划器 → 研究团队 → 研究员 → 报告器
           └── 使用单一搜索引擎 ──┘
```

**多搜索引擎流程**：

```
用户输入 → 协调器 → 背景调查 → 规划器 → 研究团队 → 研究员 → 报告器
           └── 并行使用多个搜索引擎 ──┘
           └── 结果聚合和排序 ──────┘
```

### 2. 对系统架构的影响

#### 需要修改的核心组件

**1. 背景调查节点** (`src/graph/nodes.py:47-80`)

- 当前只支持单一搜索引擎
- 需要改为并行调用多个搜索引擎
- 增加结果聚合和去重逻辑
- 添加结果质量评估机制

**2. 搜索工具配置** (`src/tools/search.py`)

- 需要支持同时创建多个搜索引擎实例
- 增加搜索引擎优先级配置
- 添加结果质量评估机制
- 支持搜索引擎的动态启用/禁用

**3. 配置管理** (`src/config/tools.py`)

- 添加多搜索引擎配置选项
- 支持搜索引擎启用/禁用配置
- 支持特定任务类型的搜索引擎映射
- 添加搜索引擎权重配置

### 3. 对执行性能的影响

#### 优势

**更全面的信息覆盖**：

- 不同搜索引擎有不同的索引和算法
- 某些搜索引擎在特定领域有优势（如 ArXiv 在学术论文领域）
- 减少信息遗漏的风险

**更高的成功率**：

- 当一个搜索引擎失败时，其他可以继续工作
- 避免单一搜索引擎的服务中断影响
- 提高系统的整体可用性

**更好的结果质量**：

- 通过聚合和去重获得更准确的结果
- 减少单一搜索引擎的偏见
- 提供更多样化的信息来源

#### 挑战

**执行时间增加**：

- 并行调用多个搜索引擎会增加总执行时间
- 网络延迟可能成为瓶颈
- 需要考虑超时和错误处理

**API 成本增加**：

- 多个搜索引擎的 API 调用会产生更多费用
- 需要监控和控制使用量
- 可能需要实现智能的搜索引擎选择策略

**结果复杂度**：

- 需要处理不同搜索引擎返回的不同格式结果
- 实现有效的结果排序和去重算法
- 增加系统复杂度

### 4. 对具体执行步骤的影响

#### 背景调查阶段的改进

**当前实现**：

```python
def background_investigation_node(state: State, config: RunnableConfig):
    # 只使用单一搜索引擎
    if SELECTED_SEARCH_ENGINE == SearchEngine.TAVILY.value:
        # 使用 Tavily
        searched_content = LoggedTavilySearch(
            max_results=configurable.max_search_results
        ).invoke(query)
    else:
        # 使用其他搜索引擎
        background_investigation_results = get_web_search_tool(
            configurable.max_search_results
        ).invoke(query)
```

**多搜索引擎实现**：

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def background_investigation_node_multi_engine(state: State, config: RunnableConfig):
    logger.info("background investigation node with multiple search engines is running.")
    configurable = Configuration.from_runnable_config(config)
    query = state.get("research_topic")

    # 并行调用多个搜索引擎
    search_tasks = []

    # 根据配置启用不同的搜索引擎
    if SearchEngine.TAVILY.value in enabled_search_engines:
        search_tasks.append(tavily_search(query, configurable.max_search_results))

    if SearchEngine.DUCKDUCKGO.value in enabled_search_engines:
        search_tasks.append(duckduckgo_search(query, configurable.max_search_results))

    if SearchEngine.BRAVE_SEARCH.value in enabled_search_engines:
        search_tasks.append(brave_search(query, configurable.max_search_results))

    # 并行执行搜索
    search_results = await asyncio.gather(*search_tasks, return_exceptions=True)

    # 聚合和排序结果
    aggregated_results = aggregate_search_results(search_results)

    return {
        "background_investigation_results": aggregated_results
    }

def aggregate_search_results(search_results):
    """
    聚合多个搜索引擎的结果
    - 去重：基于 URL 和内容相似度
    - 排序：基于相关性分数和搜索引擎权重
    - 格式化：统一不同搜索引擎的输出格式
    """
    # 实现结果聚合逻辑
    pass
```

#### 研究阶段的扩展

**当前工具集**：

```python
# 研究员只能使用单一的 Web 搜索工具
researcher_tools = [
    get_web_search_tool(max_search_results),
    get_retriever_tool(),
    crawl_tool,
]
```

**多搜索引擎工具集**：

```python
# 研究员可以访问多个搜索引擎工具
researcher_tools = [
    get_tavily_search_tool(max_search_results),
    get_duckduckgo_search_tool(max_search_results),
    get_brave_search_tool(max_search_results),
    get_arxiv_search_tool(max_search_results),
    get_wikipedia_search_tool(max_search_results),
    get_retriever_tool(),
    crawl_tool,
]
```

### 5. 对用户体验的影响

#### 优势

**更准确的背景信息**：

- 多搜索引擎提供更全面的背景调查
- 减少信息偏差和盲点
- 提供更多样化的信息来源

**更可靠的研究结果**：

- 减少单一搜索引擎的偏差
- 提供交叉验证的信息来源
- 增强研究的可信度

**更丰富的内容类型**：

- 不同搜索引擎擅长不同类型的内容
- 支持多媒体内容的搜索（如 Tavily 的图片搜索）
- 提供更专业领域的信息（如 ArXiv 的学术论文）

#### 需要考虑的因素

**配置复杂性**：

- 用户需要配置多个搜索引擎的 API 密钥
- 需要提供清晰的配置文档
- 可能需要实现配置向导

**成本控制**：

- 需要监控和管理多个搜索引擎的使用成本
- 可能需要实现智能的搜索引擎选择策略
- 提供成本预算和限制功能

**结果质量**：

- 需要建立有效的结果排序和过滤机制
- 实现个性化结果优先级
- 提供结果质量反馈机制

## 技术实现建议

### 1. 配置扩展

```python
# 在 src/config/tools.py 中添加多搜索引擎配置
class MultiSearchEngineConfig:
    # 启用的搜索引擎列表
    enabled_engines: List[SearchEngine] = [
        SearchEngine.TAVILY,
        SearchEngine.DUCKDUCKGO,
    ]

    # 搜索引擎权重配置
    engine_weights: Dict[SearchEngine, float] = {
        SearchEngine.TAVILY: 1.0,
        SearchEngine.DUCKDUCKGO: 0.8,
        SearchEngine.BRAVE_SEARCH: 0.7,
    }

    # 任务类型映射
    task_engine_mapping: Dict[str, List[SearchEngine]] = {
        "academic_research": [SearchEngine.ARXIV, SearchEngine.TAVILY],
        "general_search": [SearchEngine.TAVILY, SearchEngine.DUCKDUCKGO],
        "quick_fact_check": [SearchEngine.WIKIPEDIA, SearchEngine.DUCKDUCKGO],
    }
```

### 2. 结果聚合算法

```python
class SearchResultsAggregator:
    def __init__(self, config: MultiSearchEngineConfig):
        self.config = config

    def aggregate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        聚合多个搜索引擎的结果
        1. 去重：基于 URL 和内容相似度
        2. 排序：基于相关性分数和搜索引擎权重
        3. 格式化：统一输出格式
        """
        # 实现聚合逻辑
        pass

    def deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """基于 URL 和内容相似度去重"""
        pass

    def rank_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """基于相关性分数和搜索引擎权重排序"""
        pass
```

### 3. 异步搜索实现

```python
import asyncio
from typing import List, Dict, Any

class MultiSearchEngine:
    def __init__(self, config: MultiSearchEngineConfig):
        self.config = config
        self.engines = self._initialize_engines()

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """并行调用多个搜索引擎"""
        tasks = []

        for engine in self.config.enabled_engines:
            if engine in self.engines:
                task = self._search_with_engine(engine, query, max_results)
                tasks.append(task)

        # 并行执行搜索
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 聚合结果
        valid_results = [r for r in results if not isinstance(r, Exception)]
        aggregator = SearchResultsAggregator(self.config)
        return aggregator.aggregate_results(valid_results)

    async def _search_with_engine(self, engine: SearchEngine, query: str, max_results: int):
        """使用特定搜索引擎进行搜索"""
        search_tool = self.engines[engine]
        return await search_tool.ainvoke({"query": query, "max_results": max_results})
```

### 4. 性能优化

```python
# 使用缓存减少重复搜索
from functools import lru_cache

class CachedMultiSearchEngine(MultiSearchEngine):
    @lru_cache(maxsize=1000)
    async def cached_search(self, query: str, max_results: int) -> List[SearchResult]:
        """带缓存的搜索"""
        return await self.search(query, max_results)

    def get_cache_stats(self):
        """获取缓存统计信息"""
        return {
            "cache_info": self.cached_search.cache_info(),
            "hit_rate": self._calculate_hit_rate(),
        }
```

## 总结

采用多种搜索引擎会显著影响 deer-flow 的执行流程，主要表现在：

### 1. 架构复杂度增加

- 需要支持并行搜索、结果聚合和质量评估
- 增加配置管理的复杂性
- 需要实现新的组件和服务

### 2. 执行时间增加

- 并行调用多个搜索引擎会增加总执行时间
- 需要考虑超时和错误处理
- 网络延迟可能成为瓶颈

### 3. API 成本增加

- 多个搜索引擎的 API 调用会产生更多费用
- 需要监控和管理使用成本
- 可能需要实现智能的搜索引擎选择策略

### 4. 结果质量提升

- 通过聚合多个搜索引擎的结果获得更全面的信息
- 减少单一搜索引擎的偏见
- 提供更可靠和多样化的信息来源

### 5. 系统可靠性提高

- 减少对单一搜索引擎的依赖
- 提高系统的整体可用性
- 增强容错能力

这种改进对于提高系统的信息检索能力和可靠性是有益的，但需要仔细考虑性能和成本的影响。建议采用渐进式的实现方式，先在关键节点（如背景调查）实现多搜索引擎支持，然后根据实际效果和用户反馈逐步扩展到其他节点。

## 改进建议和实施路径

### 1. 短期改进（高优先级）

#### 1.1 研究阶段的多搜索引擎支持

**当前问题**：

- 研究阶段只支持单一搜索引擎
- 缺乏交叉验证和信息多样性

**改进方案**：

```python
async def researcher_node_multi_engine(state: State, config: RunnableConfig):
    """支持多搜索引擎的研究节点"""
    configurable = Configuration.from_runnable_config(config)

    # 创建多个搜索引擎工具
    search_tools = []

    # 根据配置启用不同的搜索引擎
    if SearchEngine.TAVILY.value in enabled_search_engines:
        search_tools.append(get_tavily_search_tool(configurable.max_search_results))

    if SearchEngine.DUCKDUCKGO.value in enabled_search_engines:
        search_tools.append(get_duckduckgo_search_tool(configurable.max_search_results))

    if SearchEngine.BRAVE_SEARCH.value in enabled_search_engines:
        search_tools.append(get_brave_search_tool(configurable.max_search_results))

    # 添加其他工具
    tools = search_tools + [crawl_tool]

    # 保持本地搜索的优先级
    retriever_tool = get_retriever_tool(state.get("resources", []))
    if retriever_tool:
        tools.insert(0, retriever_tool)

    logger.info(f"Researcher tools (multi-engine): {tools}")
    return await _setup_and_execute_agent_step(state, config, "researcher", tools)
```

#### 1.2 智能搜索引擎选择机制

**基于查询类型的搜索引擎选择**：

```python
class IntelligentSearchEngineSelector:
    def __init__(self):
        self.query_type_patterns = {
            'academic': [r'research', r'paper', r'study', r'academic'],
            'news': [r'latest', r'recent', r'news', r'current'],
            'technical': [r'code', r'programming', r'technical', r'development'],
            'general': [r'what', r'how', r'why', r'when', r'where']
        }

    def select_engines(self, query: str) -> List[SearchEngine]:
        """根据查询类型选择合适的搜索引擎"""
        query_lower = query.lower()

        # 学术查询优先使用 ArXiv
        if any(pattern in query_lower for pattern in self.query_type_patterns['academic']):
            return [SearchEngine.ARXIV, SearchEngine.TAVILY]

        # 新闻查询优先使用 Tavily
        if any(pattern in query_lower for pattern in self.query_type_patterns['news']):
            return [SearchEngine.TAVILY, SearchEngine.DUCKDUCKGO]

        # 技术查询优先使用 Tavily
        if any(pattern in query_lower for pattern in self.query_type_patterns['technical']):
            return [SearchEngine.TAVILY, SearchEngine.BRAVE_SEARCH]

        # 默认使用所有启用的搜索引擎
        return list(enabled_search_engines)
```

### 2. 中期改进（中等优先级）

#### 2.1 搜索结果聚合和质量评估

```python
class SearchResultAggregator:
    def __init__(self, config: MultiSearchEngineConfig):
        self.config = config
        self.quality_scorer = SearchResultQualityScorer()

    def aggregate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """聚合多个搜索引擎的结果"""
        # 1. 去重
        deduplicated_results = self.deduplicate_results(results)

        # 2. 质量评分
        scored_results = self.score_results(deduplicated_results)

        # 3. 排序
        sorted_results = self.sort_results(scored_results)

        # 4. 格式化
        return self.format_results(sorted_results)

    def deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """基于 URL 和内容相似度去重"""
        seen_urls = set()
        unique_results = []

        for result in results:
            url = result.get('url', '')
            if url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)

        return unique_results
```

#### 2.2 搜索引擎性能监控

```python
class SearchEngineMonitor:
    def __init__(self):
        self.metrics = {
            'response_times': defaultdict(list),
            'success_rates': defaultdict(int),
            'result_counts': defaultdict(int),
            'error_counts': defaultdict(int)
        }

    def record_search(self, engine: SearchEngine, response_time: float,
                     success: bool, result_count: int):
        """记录搜索性能指标"""
        self.metrics['response_times'][engine].append(response_time)
        self.metrics['success_rates'][engine] += 1 if success else 0
        self.metrics['result_counts'][engine] += result_count
        if not success:
            self.metrics['error_counts'][engine] += 1

    def get_engine_performance(self, engine: SearchEngine) -> Dict:
        """获取搜索引擎性能统计"""
        response_times = self.metrics['response_times'][engine]
        return {
            'avg_response_time': sum(response_times) / len(response_times) if response_times else 0,
            'success_rate': self.metrics['success_rates'][engine] / max(1, sum(self.metrics['success_rates'].values())),
            'avg_results': self.metrics['result_counts'][engine] / max(1, sum(self.metrics['result_counts'].values())),
            'error_count': self.metrics['error_counts'][engine]
        }
```

### 3. 长期改进（低优先级）

#### 3.1 自适应搜索引擎选择

```python
class AdaptiveSearchEngineSelector:
    def __init__(self, monitor: SearchEngineMonitor):
        self.monitor = monitor
        self.user_feedback = defaultdict(list)

    def select_best_engines(self, query: str, max_engines: int = 3) -> List[SearchEngine]:
        """基于历史性能和用户反馈选择最佳搜索引擎"""
        engine_scores = {}

        for engine in enabled_search_engines:
            # 基于性能评分
            performance_score = self._calculate_performance_score(engine)

            # 基于用户反馈评分
            feedback_score = self._calculate_feedback_score(engine)

            # 基于查询相关性评分
            relevance_score = self._calculate_relevance_score(query, engine)

            # 综合评分
            engine_scores[engine] = (
                performance_score * 0.4 +
                feedback_score * 0.3 +
                relevance_score * 0.3
            )

        # 返回评分最高的搜索引擎
        sorted_engines = sorted(engine_scores.items(), key=lambda x: x[1], reverse=True)
        return [engine for engine, score in sorted_engines[:max_engines]]

    def record_user_feedback(self, engine: SearchEngine, query: str, rating: int):
        """记录用户反馈"""
        self.user_feedback[engine].append({
            'query': query,
            'rating': rating,
            'timestamp': datetime.now()
        })
```

#### 3.2 搜索引擎负载均衡

```python
class SearchEngineLoadBalancer:
    def __init__(self):
        self.rate_limits = {
            SearchEngine.TAVILY: {'requests_per_minute': 100, 'current_usage': 0},
            SearchEngine.DUCKDUCKGO: {'requests_per_minute': 200, 'current_usage': 0},
            SearchEngine.BRAVE_SEARCH: {'requests_per_minute': 150, 'current_usage': 0},
            SearchEngine.ARXIV: {'requests_per_minute': 50, 'current_usage': 0},
            SearchEngine.WIKIPEDIA: {'requests_per_minute': 300, 'current_usage': 0}
        }
        self.reset_time = time.time() + 60  # 重置时间

    def can_use_engine(self, engine: SearchEngine) -> bool:
        """检查是否可以使用搜索引擎"""
        if time.time() > self.reset_time:
            self._reset_usage()

        limit = self.rate_limits[engine]
        return limit['current_usage'] < limit['requests_per_minute']

    def record_usage(self, engine: SearchEngine):
        """记录搜索引擎使用"""
        self.rate_limits[engine]['current_usage'] += 1

    def _reset_usage(self):
        """重置使用计数"""
        for engine in self.rate_limits:
            self.rate_limits[engine]['current_usage'] = 0
        self.reset_time = time.time() + 60
```

### 4. 实施建议

#### 4.1 实施优先级

1. **第一阶段**：研究阶段的多搜索引擎支持
2. **第二阶段**：智能搜索引擎选择机制
3. **第三阶段**：搜索结果聚合和质量评估
4. **第四阶段**：搜索引擎性能监控
5. **第五阶段**：自适应搜索引擎选择和负载均衡

#### 4.2 风险控制

1. **渐进式部署**：先在测试环境验证，再逐步推广到生产环境
2. **性能监控**：实时监控多搜索引擎对系统性能的影响
3. **成本控制**：设置搜索引擎使用预算和限制
4. **回滚机制**：保留单搜索引擎版本作为回滚选项

#### 4.3 测试策略

1. **单元测试**：确保每个搜索引擎工具的功能正确
2. **集成测试**：验证多搜索引擎的协同工作
3. **性能测试**：评估对系统响应时间的影响
4. **用户测试**：收集用户对多搜索引擎功能的反馈

通过这些改进，deer-flow 项目可以实现真正的多搜索引擎支持，提供更全面、更可靠的信息检索能力，同时保持系统的性能和成本效益。
