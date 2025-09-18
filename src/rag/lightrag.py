# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import os
from typing import Optional
from urllib.parse import urlparse

import requests

from src.rag.retriever import Chunk, Document, Resource, Retriever


class LightRAGProvider(Retriever):
    """
    LightRAGProvider is a provider that uses LightRAG to retrieve documents.
    """

    api_url: str
    api_key: Optional[str]
    max_results: int = 10
    min_score: float = 0.3
    timeout: int = 30

    def __init__(self):
        api_url = os.getenv("LIGHTRAG_API_URL")
        if not api_url:
            raise ValueError("LIGHTRAG_API_URL is not set")

        # 确保API URL以/结尾
        if not api_url.endswith("/"):
            api_url += "/"
        self.api_url = api_url

        self.api_key = os.getenv("LIGHTRAG_API_KEY")

        max_results = os.getenv("LIGHTRAG_MAX_RESULTS")
        if max_results:
            self.max_results = int(max_results)

        min_score = os.getenv("LIGHTRAG_MIN_SCORE")
        if min_score:
            self.min_score = float(min_score)

        timeout = os.getenv("LIGHTRAG_TIMEOUT")
        if timeout:
            self.timeout = int(timeout)

    def query_relevant_documents(
        self, query: str, resources: list[Resource] = []
    ) -> list[Document]:
        """
        Query relevant documents from LightRAG service.
        """
        headers = {
            "Content-Type": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "query": query,
            "max_results": self.max_results,
            "min_score": self.min_score,
        }

        # 如果指定了资源，添加到payload中
        if resources:
            resource_ids = []
            for resource in resources:
                resource_id = parse_lightrag_uri(resource.uri)
                if resource_id:
                    resource_ids.append(resource_id)

            if resource_ids:
                payload["resources"] = resource_ids

        try:
            response = requests.post(
                f"{self.api_url}api/v1/retrieve",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
        except requests.RequestException as e:
            raise Exception(f"Failed to connect to LightRAG service: {str(e)}")

        if response.status_code != 200:
            raise Exception(f"LightRAG API error: {response.status_code} - {response.text}")

        result = response.json()

        # 处理LightRAG响应格式
        documents: dict[str, Document] = {}
        if "result" in result and "chunks" in result["result"]:
            for item in result["result"]["chunks"]:
                doc_id, chunk = self._convert_to_document(item)
                if not doc_id:
                    continue

                if doc_id not in documents:
                    documents[doc_id] = Document(
                        id=doc_id,
                        url=None,
                        title=None,
                        chunks=[],
                    )

                document = documents[doc_id]

                # 回填缺失的基础信息，优先保留已有值
                if item.get("url"):
                    document.url = item.get("url")
                elif not document.url:
                    document.url = f"lightrag://{doc_id}"

                title = item.get("title") or item.get("document_name")
                if title:
                    document.title = title
                elif not document.title:
                    document.title = f"Document_{doc_id}"

                if chunk:
                    document.chunks.append(chunk)

        return list(documents.values())

    def list_resources(self, query: str | None = None) -> list[Resource]:
        """
        List available resources from LightRAG service.
        """
        headers = {}

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        params = {}
        if query:
            params["query"] = query

        try:
            response = requests.get(
                f"{self.api_url}api/v1/resources",
                headers=headers,
                params=params,
                timeout=self.timeout
            )
        except requests.RequestException as e:
            raise Exception(f"Failed to connect to LightRAG service: {str(e)}")

        if response.status_code != 200:
            raise Exception(f"LightRAG API error: {response.status_code} - {response.text}")

        result = response.json()

        resources = []
        if "resources" in result:
            for item in result["resources"]:
                resource = self._convert_to_resource(item)
                if resource:
                    resources.append(resource)

        return resources

    def _convert_to_document(self, item: dict) -> tuple[Optional[str], Optional[Chunk]]:
        """
        Convert LightRAG response item to Document object.
        """
        try:
            # 根据实际API响应格式提取字段
            doc_id = item.get("doc_id") or item.get("id") or item.get("document_id")
            if not doc_id:
                # 如果没有明确的doc_id，生成一个基于内容的ID
                content = item.get("content", "")
                doc_id = f"doc_{hash(content) % 10000}"

            content = item.get("content", "")
            # 优先使用score字段，其次使用similarity字段
            similarity = item.get("score", item.get("similarity", 0.0))

            chunk = None
            if content:
                chunk = Chunk(content=content, similarity=similarity)

            return doc_id, chunk
        except Exception:
            # 如果转换失败，返回None而不是抛出异常
            return None, None

    def _convert_to_resource(self, item: dict) -> Optional[Resource]:
        """
        Convert LightRAG resource item to Resource object.
        """
        try:
            description = ""
            if isinstance(item, str):
                resource_id = item
                title = item
            else:
                raw_uri = item.get("uri")
                resource_id = parse_lightrag_uri(raw_uri) if raw_uri else None
                if not resource_id:
                    resource_id = item.get("id") or item.get("name")
                if not resource_id:
                    return None

                title = item.get("name") or item.get("title") or f"Resource_{resource_id}"
                description = item.get("description", "")

            uri = f"lightrag://{resource_id}"

            return Resource(
                uri=uri,
                title=title,
                description=description
            )
        except Exception:
            # 如果转换失败，返回None而不是抛出异常
            return None

    def check_health(self) -> bool:
        """
        Check if LightRAG service is healthy.
        """
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = requests.get(
                f"{self.api_url}api/v1/health",
                headers=headers,
                timeout=self.timeout
            )
            return response.status_code == 200
        except Exception:
            return False


def parse_lightrag_uri(uri: str) -> Optional[str]:
    """
    Parse LightRAG URI and extract resource ID.
    Format: lightrag://{resource_id} or lightrag://resource/{resource_id}
    """
    try:
        parsed = urlparse(uri)
        if parsed.scheme != "lightrag":
            return None

        parts = [part for part in parsed.path.split("/") if part]

        if parsed.netloc and parsed.netloc != "resource":
            return parsed.netloc

        if parsed.netloc == "resource" and parts:
            return parts[0]

        if parts:
            return parts[0]

        return None
    except Exception:
        return None
