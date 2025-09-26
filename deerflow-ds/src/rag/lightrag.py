# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import os
import json
import logging
from typing import Optional
from urllib.parse import urlparse

import requests

from src.rag.retriever import Chunk, Document, Resource, Retriever

logger = logging.getLogger(__name__)


class LightRAGProvider(Retriever):
    """
    LightRAGProvider 适配新版 LightRAG 检索接口：
    - 资源列表：GET /api/v1/resources
    - 检索：POST /api/v1/retrieve
      * 本地检索：local_search=true（返回 chunks）
      * 背景检索：background_search=true（返回 background/entities/relationships）
    """

    api_url: str
    api_key: Optional[str]
    local_search_max_results: int = 3
    background_search_max_results: int = 20
    min_score: float = 0.65
    timeout: int = 30
    debug_log_body: bool = False
    log_max_chars: int = 2000
    include_metadata: bool = True
    query_mode: str = "global"

    def __init__(self):
        api_url = os.getenv("LIGHTRAG_API_URL")
        if not api_url:
            raise ValueError("LIGHTRAG_API_URL is not set")
        if not api_url.endswith("/"):
            api_url += "/"
        self.api_url = api_url

        self.api_key = os.getenv("LIGHTRAG_API_KEY")
        
        self.local_search_max_results = os.getenv("LIGHTRAG_LOCAL_SEARCH_MAX_RESULTS") or self.local_search_max_results
        self.background_search_max_results = os.getenv("LIGHTRAG_BACKGROUND_SEARCH_MAX_RESULTS") or self.background_search_max_results

        min_score = os.getenv("LIGHTRAG_MIN_SCORE")
        if min_score:
            self.min_score = float(min_score)

        timeout = os.getenv("LIGHTRAG_TIMEOUT")
        if timeout:
            self.timeout = int(timeout)

        # Debug logging options for diagnostics
        self.debug_log_body = (
            os.getenv("LIGHTRAG_DEBUG_LOG_BODY", "false").lower() in ["1", "true", "yes"]
        )
        log_max_chars = os.getenv("LIGHTRAG_LOG_MAX_CHARS")
        if log_max_chars and str(log_max_chars).isdigit():
            self.log_max_chars = int(log_max_chars)

        include_metadata = os.getenv("LIGHTRAG_INCLUDE_METADATA", "true").lower()
        self.include_metadata = include_metadata in ["1", "true", "yes"]

        # 预留查询模式（当前接口以 background/local 两个布尔开关区分）
        self.query_mode = os.getenv("LIGHTRAG_QUERY_MODE", "global")

    def _auth_headers(self) -> dict:
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            # 优先 X-API-Key，兼容 Bearer
            headers["X-API-Key"] = self.api_key
            headers.setdefault("Authorization", f"Bearer {self.api_key}")
        return headers

    def query_relevant_documents(
        self, query: str, resources: list[Resource] = []
    ) -> list[Document]:
        """
        本地检索（local_search=true）：返回 chunks，映射为 Document/Chunk 以兼容上层工具。
        """
        headers = self._auth_headers()

        payload = {
            "query": query,
            "max_results": self.local_search_max_results,
            "local_search": True,
        }
        # 资源为必填（rag://<instance> 列表）
        if resources:
            resource_uris: list[str] = []
            for r in resources:
                if isinstance(getattr(r, "uri", None), str) and r.uri:
                    resource_uris.append(r.uri)
            if resource_uris:
                payload["resources"] = resource_uris
        else:
            logger.warning("LightRAG local_search called without resources; returning empty.")
            return []

        try:
            response = requests.post(
                f"{self.api_url}api/v1/retrieve",
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise Exception(f"Failed to connect to LightRAG service: {str(e)}")

        if response.status_code != 200:
            raise Exception(f"LightRAG API error: {response.status_code} - {response.text}")

        # Response diagnostics
        try:
            content_len = len(response.content) if response.content is not None else 0
        except Exception:
            content_len = -1
        logger.info(
            "LightRAG response received.",
            extra={
                "status": response.status_code,
                "content_length": content_len,
            },
        )
        if self.debug_log_body:
            try:
                body_preview = response.text[: self.log_max_chars]
                logger.info("LightRAG raw body (truncated)")
                logger.info(body_preview)
            except Exception:
                pass

        try:
            data = response.json()
        except Exception:
            logger.warning("LightRAG response is not a valid JSON. Returning empty documents.")
            return []

        # 新接口：{success, result, error, execution_time}, result.chunks
        result = data.get("result") if isinstance(data, dict) else None
        chunks = []
        if isinstance(result, dict) and isinstance(result.get("chunks"), list):
            chunks = result["chunks"]
        else:
            logger.info(
                "LightRAG returned no 'chunks' field.",
                extra={"has_result": isinstance(result, dict)},
            )
            if self.debug_log_body:
                try:
                    logger.info("LightRAG parsed JSON (truncated)")
                    logger.info(json.dumps(data, ensure_ascii=False)[: self.log_max_chars])
                except Exception:
                    pass
            return []

        logger.info("LightRAG chunks parsed.", extra={"chunks_count": len(chunks)})

        documents: dict[str, Document] = {}
        for item in chunks:
            doc_id, chunk = self._convert_to_document(item)
            if not doc_id:
                continue
            if doc_id not in documents:
                documents[doc_id] = Document(id=doc_id, url=None, title=None, chunks=[])
            document = documents[doc_id]

            # 新接口未返回 url/title，这里构造占位
            if not document.url:
                document.url = f"rag://{doc_id}"
            if not document.title:
                document.title = f"Document_{doc_id}"

            if chunk:
                document.chunks.append(chunk)

        return list(documents.values())

    def list_resources(self, query: str | None = None) -> list[Resource]:
        """
        获取可用资源列表（GET /api/v1/resources）。
        """
        headers = self._auth_headers()

        params = {}
        if query:
            params["query"] = query

        try:
            response = requests.get(
                f"{self.api_url}api/v1/resources",
                headers=headers,
                params=params,
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise Exception(f"Failed to connect to LightRAG service: {str(e)}")

        if response.status_code != 200:
            raise Exception(f"LightRAG API error: {response.status_code} - {response.text}")

        result = response.json()

        resources: list[Resource] = []
        if isinstance(result, dict) and "resources" in result:
            for item in result["resources"]:
                resource = self._convert_to_resource(item)
                if resource:
                    resources.append(resource)

        return resources

    def query_background_knowledge(
        self, query: str, resources: list[Resource] = []
    ) -> dict:
        """
        背景检索（background_search=true）：返回结构化先验（background/entities/relationships/metadata）。
        直接透传 result 字段，供上层节点压缩注入 Planner。
        """
        headers = self._auth_headers()

        payload = {
            "query": query,
            "max_results": self.background_search_max_results,
            "background_search": True,
        }
        if resources:
            uris = [r.uri for r in resources if isinstance(getattr(r, "uri", None), str) and r.uri]
            if uris:
                payload["resources"] = uris
        else:
            logger.warning("LightRAG background_search called without resources; returning empty.")
            return {}

        try:
            response = requests.post(
                f"{self.api_url}api/v1/retrieve",
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise Exception(f"Failed to connect to LightRAG service: {str(e)}")

        if response.status_code != 200:
            raise Exception(f"LightRAG API error: {response.status_code} - {response.text}")

        try:
            data = response.json()
        except Exception as e:
            raise Exception(f"LightRAG background response is not JSON: {e}")

        result = data.get("result") if isinstance(data, dict) else None
        if not isinstance(result, dict):
            logger.warning("LightRAG background result malformed. Returning empty dict.")
            return {}

        # 诊断日志
        try:
            entities_cnt = len(result.get("entities", []) or [])
            rels_cnt = len(result.get("relationships", []) or [])
            bg_len = len(result.get("background", "") or "")
            # 近似 tokens 统计（用于观察背景上下文规模）
            bg_tokens = (bg_len + 2) // 3 if bg_len else 0
        except Exception:
            entities_cnt, rels_cnt, bg_len, bg_tokens = -1, -1, -1, -1
        logger.info(f"LightRAG background parsed. entities: {entities_cnt}, relationships: {rels_cnt}, background_chars: {bg_len}, background_approx_tokens: {bg_tokens}")
        return result

    def _convert_to_document(self, item: dict) -> tuple[Optional[str], Optional[Chunk]]:
        """
        Convert LightRAG response item to Document object.
        """
        try:
            # 新接口字段：id/doc_id/content/chunk_index/score/similarity
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
                uri = item
                title = item
            else:
                raw_uri = item.get("uri")
                if raw_uri and isinstance(raw_uri, str):
                    uri = raw_uri
                    resource_id = parse_lightrag_uri(raw_uri) or raw_uri
                else:
                    resource_id = item.get("id") or item.get("name")
                    if not resource_id:
                        return None
                    uri = f"rag://{resource_id}"
                title = item.get("name") or item.get("title") or f"Resource_{resource_id}"
                description = item.get("description", "")

            return Resource(
                uri=uri,
                title=title,
                description=description,
            )
        except Exception:
            # 如果转换失败，返回None而不是抛出异常
            return None

    def check_health(self) -> bool:
        """
        Check if LightRAG service is healthy.
        """
        try:
            headers = self._auth_headers()
            response = requests.get(
                f"{self.api_url}api/v1/health",
                headers=headers,
                timeout=self.timeout,
            )
            return response.status_code == 200
        except Exception:
            return False


def parse_lightrag_uri(uri: str) -> Optional[str]:
    """
    Parse LightRAG URI and extract resource ID.
    Format: rag://{resource_id} or rag://resource/{resource_id}
    """
    try:
        parsed = urlparse(uri)
        if parsed.scheme != "rag":
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
