# LightRAG 本地搜索功能集成测试方案

## 1. 测试环境准备

### 1.1 环境配置要求

```bash
# 后端服务配置
RAG_PROVIDER=lightrag
LIGHTRAG_API_URL=http://localhost:8000/
LIGHTRAG_API_KEY=your_api_key
LIGHTRAG_MAX_RESULTS=10
LIGHTRAG_MIN_SCORE=0.3
LIGHTRAG_TIMEOUT=30

# 启动 deer-flow 后端服务
python server.py --host localhost --port 8080
```

### 1.2 LightRAG 服务配置

```bash
# 确保 LightRAG 服务运行在 http://localhost:8000
# API 端点：
# - POST /api/v1/retrieve - 文档检索
# - GET /api/v1/resources - 资源列表
# - GET /api/v1/health - 健康检查
```

## 2. 后端 API 测试

### 2.1 RAG 配置接口测试

**接口**: `GET /api/rag/config`
**目的**: 验证 LightRAG 提供商配置是否正确加载

**测试用例**:

```bash
# 测试配置获取
curl -X GET "http://localhost:8080/api/rag/config" \
  -H "Content-Type: application/json"

# 预期响应
{
  "provider": "lightrag"
}
```

### 2.2 资源列表接口测试

**接口**: `GET /api/rag/resources`
**目的**: 验证能否正确获取 LightRAG 中的知识库资源

**测试用例**:

```bash
# 测试获取所有资源
curl -X GET "http://localhost:8080/api/rag/resources" \
  -H "Content-Type: application/json"

# 测试带查询参数的资源搜索
curl -X GET "http://localhost:8080/api/rag/resources?query=技术文档" \
  -H "Content-Type: application/json"

# 预期响应格式
{
  "resources": [
    {
      "uri": "lightrag://resource1",
      "title": "技术文档",
      "description": "技术相关文档"
    }
  ]
}
```

### 2.3 聊天接口中的 RAG 功能测试

**接口**: `POST /api/chat/stream`
**目的**: 验证在聊天过程中能否正确使用 LightRAG 进行检索

**测试用例**:

```bash
# 测试带资源的聊天请求
curl -X POST "http://localhost:8080/api/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "请解释什么是机器学习"
      }
    ],
    "resources": [
      {
        "uri": "lightrag://ml_docs",
        "title": "机器学习文档",
        "description": "机器学习相关资料"
      }
    ],
    "thread_id": "test-thread-001"
  }'
```

## 3. 前端功能测试

### 3.1 资源发现功能测试

**测试场景**: 前端页面加载时自动获取可用的知识库资源

**测试步骤**:

1. 访问前端页面 `http://localhost:3000`
2. 检查侧边栏或资源选择器是否显示 LightRAG 资源
3. 验证资源列表是否能正确加载

**预期结果**:

- 资源列表显示格式: `[资源名称] (lightrag://resource_id)`
- 支持资源搜索过滤
- 支持多选资源进行检索

### 3.2 聊天界面功能测试

**测试场景**: 用户选择资源后进行对话

**测试步骤**:

1. 在资源列表中选择一个或多个 LightRAG 资源
2. 在聊天输入框中输入相关问题
3. 发送消息并观察响应

**预期结果**:

- 系统应该优先使用选中的 LightRAG 资源进行检索
- 在回复中应该包含引用的来源信息
- 检索结果应该具有相关性

### 3.3 错误处理测试

**测试场景**: 各种异常情况的处理

**测试用例**:

1. **LightRAG 服务不可用**
   - 停止 LightRAG 服务
   - 尝试进行检索
   - 预期: 优雅降级，显示错误信息但不崩溃

2. **无效资源 URI**
   - 使用格式错误的 URI 进行测试
   - 预期: 系统应该能够识别并忽略无效资源

3. **网络超时**
   - 模拟网络延迟或超时
   - 预期: 显示超时错误信息

## 4. 集成测试场景

### 4.1 完整检索流程测试

**场景**: 用户选择特定知识库，询问相关问题

**测试数据**:

```
知识库: 技术文档 (lightrag://tech_docs)
问题: "什么是微服务架构？"
```

**测试验证点**:

1. 是否正确调用了 LightRAG 的检索接口
2. 检索结果是否相关
3. 回答是否基于检索到的内容
4. 是否显示来源引用

### 4.2 多资源检索测试

**场景**: 用户同时选择多个知识库进行检索

**测试数据**:

```
资源1: lightrag://api_docs
资源2: lightrag://design_docs
问题: "如何设计 RESTful API？"
```

**测试验证点**:

1. 是否同时在多个资源中进行检索
2. 结果是否按相关性排序
3. 是否能识别不同资源的来源

### 4.3 边界条件测试

**测试用例**:

1. **空查询**: 输入空字符串或无意义内容
2. **长查询**: 输入超长查询文本
3. **特殊字符**: 输入包含特殊字符的查询
4. **中文查询**: 测试中文检索效果

## 5. 性能测试

### 5.1 响应时间测试

**测试目标**: 验证检索响应时间在可接受范围内

**测试方法**:

```python
import time
import requests

def test_response_time():
    start_time = time.time()

    response = requests.post(
        "http://localhost:8080/api/chat/stream",
        json={
            "messages": [{"role": "user", "content": "测试查询"}],
            "resources": [{"uri": "lightrag://test", "title": "测试资源"}]
        }
    )

    end_time = time.time()
    print(f"响应时间: {end_time - start_time:.2f}秒")

    # 预期: 响应时间 < 10秒
    assert end_time - start_time < 10
```

### 5.2 并发测试

**测试目标**: 验证系统在并发请求下的稳定性

**测试方法**:

```python
import concurrent.futures
import threading

def test_concurrent_requests():
    def make_request():
        requests.post(
            "http://localhost:8080/api/chat/stream",
            json={
                "messages": [{"role": "user", "content": f"并发测试 {threading.get_ident()}"}],
                "resources": [{"uri": "lightrag://test", "title": "测试资源"}]
            }
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(20)]
        concurrent.futures.wait(futures)

    print("并发测试完成")
```

## 6. 自动化测试脚本

### 6.1 Python 测试脚本

```python
#!/usr/bin/env python3
"""
LightRAG 集成测试脚本
"""
import requests
import json
import time

class LightRAGTester:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url

    def test_rag_config(self):
        """测试 RAG 配置"""
        response = requests.get(f"{self.base_url}/api/rag/config")
        assert response.status_code == 200
        config = response.json()
        assert config["provider"] == "lightrag"
        print("✓ RAG 配置测试通过")

    def test_resources_list(self):
        """测试资源列表"""
        response = requests.get(f"{self.base_url}/api/rag/resources")
        assert response.status_code == 200
        resources = response.json()
        assert "resources" in resources
        print("✓ 资源列表测试通过")

    def test_chat_with_rag(self):
        """测试带 RAG 的聊天"""
        payload = {
            "messages": [{"role": "user", "content": "什么是人工智能？"}],
            "resources": [
                {
                    "uri": "lightrag://ai_docs",
                    "title": "AI 文档",
                    "description": "人工智能相关文档"
                }
            ],
            "thread_id": "test-thread-001"
        }

        response = requests.post(
            f"{self.base_url}/api/chat/stream",
            json=payload,
            stream=True
        )

        assert response.status_code == 200
        print("✓ 聊天 RAG 测试通过")

    def run_all_tests(self):
        """运行所有测试"""
        print("开始 LightRAG 集成测试...")

        try:
            self.test_rag_config()
            self.test_resources_list()
            self.test_chat_with_rag()
            print("🎉 所有测试通过!")
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            raise

if __name__ == "__main__":
    tester = LightRAGTester()
    tester.run_all_tests()
```

### 6.2 Shell 测试脚本

```bash
#!/bin/bash
# LightRAG 集成测试脚本

set -e

BASE_URL="http://localhost:8080"
echo "开始 LightRAG 集成测试..."

# 测试 RAG 配置
echo "1. 测试 RAG 配置..."
curl -s -X GET "$BASE_URL/api/rag/config" | jq -e '.provider == "lightrag"'

# 测试资源列表
echo "2. 测试资源列表..."
curl -s -X GET "$BASE_URL/api/rag/resources" | jq -e '.resources'

# 测试聊天功能
echo "3. 测试聊天功能..."
curl -s -X POST "$BASE_URL/api/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "测试查询"}],
    "resources": [{"uri": "lightrag://test", "title": "测试资源"}],
    "thread_id": "test-shell"
  }' | head -n 5

echo "✅ 所有测试完成!"
```

## 7. 测试数据准备

### 7.1 测试知识库数据

建议准备以下测试数据：

- 技术文档（包含常见技术概念）
- 产品文档（包含产品特性描述）
- API 文档（包含接口说明）

### 7.2 测试问题集

```json
{
  "test_questions": [
    {
      "category": "技术概念",
      "questions": [
        "什么是 RESTful API？",
        "解释微服务架构的优势",
        "什么是容器化技术？"
      ]
    },
    {
      "category": "产品特性",
      "questions": [
        "产品支持哪些部署方式？",
        "如何配置系统参数？",
        "产品的主要功能是什么？"
      ]
    },
    {
      "category": "API 使用",
      "questions": [
        "如何调用用户管理接口？",
        "认证流程是怎样的？",
        "错误码如何处理？"
      ]
    }
  ]
}
```

## 8. 监控和日志

### 8.1 关键指标监控

- API 响应时间
- 检索成功率
- 错误率统计
- 并发处理能力

### 8.2 日志检查点

```python
# 在 LightRAGProvider 中添加日志
import logging

logger = logging.getLogger(__name__)

class LightRAGProvider(Retriever):
    def query_relevant_documents(self, query: str, resources: list[Resource] = []):
        logger.info(f"开始检索查询: {query}")
        logger.info(f"使用资源: {[r.uri for r in resources]}")

        # ... 检索逻辑

        logger.info(f"检索完成，返回 {len(documents)} 个文档")
        return documents
```

## 9. 测试报告模板

### 9.1 测试结果汇总

```
LightRAG 集成测试报告
=====================

测试时间: 2025-01-18 10:00:00
测试环境: Development

测试结果概览:
- 总测试用例: 15
- 通过: 14
- 失败: 1
- 通过率: 93.3%

详细结果:
1. RAG 配置测试 ✓
2. 资源列表测试 ✓
3. 聊天功能测试 ✓
4. 错误处理测试 ✓
5. 性能测试 ✓
6. 并发测试 ✗ (响应超时)

问题分析:
- 并发测试中出现响应超时问题
- 建议优化 LightRAG 服务的并发处理能力
```

## 10. 上线前检查清单

### 10.1 功能检查

- [ ] LightRAG 服务正常运行
- [ ] deer-flow 后端服务配置正确
- [ ] 前端资源选择功能正常
- [ ] 检索结果相关性验证通过
- [ ] 错误处理机制完善

### 10.2 性能检查

- [ ] 单次检索响应时间 < 5秒
- [ ] 并发 10 用户无性能问题
- [ ] 内存使用稳定
- [ ] 网络带宽充足

### 10.3 安全检查

- [ ] API 密钥配置正确
- [ ] 网络访问权限控制
- [ ] 敏感信息不泄露
- [ ] 日志脱敏处理

## 11. 故障排除指南

### 11.1 常见问题

1. **资源列表为空**
   - 检查 LightRAG 服务是否运行
   - 验证 LIGHTRAG_API_URL 配置
   - 确认 LightRAG 中有可用数据

2. **检索结果不相关**
   - 检查查询参数是否正确
   - 验证 min_score 设置是否过高
   - 确认知识库数据质量

3. **响应超时**
   - 检查网络连接
   - 调整 timeout 参数
   - 优化 LightRAG 服务性能

### 11.2 调试命令

```bash
# 查看 deer-flow 服务日志
tail -f logs/deer-flow.log

# 测试 LightRAG 服务连接
curl http://localhost:8000/api/v1/health

# 检查环境变量配置
env | grep LIGHTRAG
```

这个测试方案提供了完整的 LightRAG 集成测试覆盖，包括单元测试、集成测试、性能测试和前端功能测试。通过这套测试方案，可以确保 LightRAG 在 deer-flow 项目中的稳定运行。
