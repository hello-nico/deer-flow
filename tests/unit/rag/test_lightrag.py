# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock, patch

import pytest

from src.rag.lightrag import LightRAGProvider, parse_lightrag_uri


# 简化的测试，只验证两个主要接口
def test_parse_lightrag_uri_valid():
    """测试 LightRAG URI 解析 - 支持新的简短格式"""
    # 测试新格式
    assert parse_lightrag_uri("lightrag://space1") == "space1"
    assert parse_lightrag_uri("lightrag://default") == "default"

    # 测试旧格式（向后兼容）
    assert parse_lightrag_uri("lightrag://resource/123") == "123"

    # 测试无效格式
    assert parse_lightrag_uri("http://space1") is None
    assert parse_lightrag_uri("lightrag://") is None


def test_query_relevant_documents_api_format():
    """测试文档查询 API 响应格式"""
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("LIGHTRAG_API_URL", "http://localhost:9621")

    provider = LightRAGProvider()

    # 模拟 API 响应格式
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "result": {
            "chunks": [
                {
                    "doc_id": "document1.pdf",
                    "content": "Retrieval Augmented Generation (RAG) 是一种结合检索和生成的人工智能技术...",
                    "score": 0.85,
                    "similarity": 0.85,
                    "id": "chunk_1",
                    "chunk_index": 0
                }
            ]
        }
    }

    with patch("src.rag.lightrag.requests.post", return_value=mock_response):
        docs = provider.query_relevant_documents("什么是RAG")

        # 验证返回结果
        assert len(docs) == 1
        assert docs[0].id == "document1.pdf"
        assert len(docs[0].chunks) == 1
        assert docs[0].chunks[0].content == "Retrieval Augmented Generation (RAG) 是一种结合检索和生成的人工智能技术..."
        assert docs[0].chunks[0].similarity == 0.85


def test_query_relevant_documents_merge_chunks():
    """多个 chunk 应合并到同一文档"""
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("LIGHTRAG_API_URL", "http://localhost:9621")

    provider = LightRAGProvider()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "result": {
            "chunks": [
                {
                    "doc_id": "doc-1",
                    "content": "部分内容 A",
                    "score": 0.9,
                },
                {
                    "doc_id": "doc-1",
                    "content": "部分内容 B",
                    "similarity": 0.8,
                    "url": "https://example.com/doc-1",
                    "title": "Doc Title",
                },
            ]
        }
    }

    with patch("src.rag.lightrag.requests.post", return_value=mock_response):
        docs = provider.query_relevant_documents("test")

        assert len(docs) == 1
        doc = docs[0]
        assert doc.id == "doc-1"
        assert doc.url == "https://example.com/doc-1"
        assert doc.title == "Doc Title"
        assert [chunk.content for chunk in doc.chunks] == ["部分内容 A", "部分内容 B"]


def test_list_resources_api_format():
    """测试资源列表 API 响应格式"""
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("LIGHTRAG_API_URL", "http://localhost:9621")

    provider = LightRAGProvider()

    # 模拟 API 响应格式
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "resources": ["default", "space1"]
    }

    with patch("src.rag.lightrag.requests.get", return_value=mock_response):
        resources = provider.list_resources()

        # 验证返回结果
        assert len(resources) == 2
        assert resources[0].uri == "lightrag://default"
        assert resources[0].title == "default"
        assert resources[1].uri == "lightrag://space1"
        assert resources[1].title == "space1"


def test_query_relevant_documents_with_resources():
    """测试带资源过滤的文档查询"""
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("LIGHTRAG_API_URL", "http://localhost:9621")

    provider = LightRAGProvider()

    # 创建测试资源
    from src.rag.retriever import Resource
    test_resource = Resource(
        uri="lightrag://space1",
        title="space1",
        description="Test space"
    )

    # 模拟 API 响应
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "result": {
            "chunks": []
        }
    }

    with patch("src.rag.lightrag.requests.post", return_value=mock_response):
        # 验证资源参数被正确传递
        provider.query_relevant_documents("test query", [test_resource])

        # 检查请求是否包含正确的参数
        from src.rag.lightrag import requests
        requests.post.assert_called_once()
        call_args = requests.post.call_args
        payload = call_args[1]['json']

        assert "resources" in payload
        assert "space1" in payload["resources"]


def test_list_resources_get_request():
    """验证 list_resources 使用 GET 请求"""
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("LIGHTRAG_API_URL", "http://localhost:9621")

    provider = LightRAGProvider()

    # 模拟 API 响应
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "resources": []
    }

    with patch("src.rag.lightrag.requests.get", return_value=mock_response):
        provider.list_resources("search query")

        # 验证使用了 GET 请求
        from src.rag.lightrag import requests
        requests.get.assert_called_once()

        # 验证查询参数
        call_args = requests.get.call_args
        params = call_args[1]['params']
        assert params["query"] == "search query"


def test_list_resources_uri_cleanup():
    """资源列表应正确解析带 schema 的 URI"""
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("LIGHTRAG_API_URL", "http://localhost:9621")

    provider = LightRAGProvider()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "resources": [
            {"uri": "lightrag://resource/space1", "title": "Space 1", "description": "desc"},
            "default",
        ]
    }

    with patch("src.rag.lightrag.requests.get", return_value=mock_response):
        resources = provider.list_resources()

        assert len(resources) == 2
        assert resources[0].uri == "lightrag://space1"
        assert resources[0].title == "Space 1"
        assert resources[0].description == "desc"

        assert resources[1].uri == "lightrag://default"
        assert resources[1].description == ""


if __name__ == "__main__":
    # 运行主要测试
    test_parse_lightrag_uri_valid()
    print("✓ URI 解析测试通过")

    test_query_relevant_documents_api_format()
    print("✓ 文档查询测试通过")

    test_list_resources_api_format()
    print("✓ 资源列表测试通过")

    test_query_relevant_documents_with_resources()
    print("✓ 带资源过滤的查询测试通过")

    test_list_resources_get_request()
    print("✓ GET 请求测试通过")

    print("\n所有主要接口测试通过！")
