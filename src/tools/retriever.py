# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import logging
import os
from typing import List, Optional, Type

from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.config.tools import SELECTED_RAG_PROVIDER
from src.rag import Document, Resource, Retriever, build_retriever

logger = logging.getLogger(__name__)


class RetrieverInput(BaseModel):
    keywords: str = Field(description="search keywords to look up")


class RetrieverTool(BaseTool):
    name: str = "local_search_tool"
    description: str = (
        "Useful for retrieving information from the local knowledge base with `rag://` URIs. "
        "Prefer web_search for broad or time-sensitive information; use this tool when you specifically need local resources or to supplement evidence from local documents. "
        "Input should be search keywords."
    )
    args_schema: Type[BaseModel] = RetrieverInput

    retriever: Retriever = Field(default_factory=Retriever)
    resources: list[Resource] = Field(default_factory=list)

    def _run(
        self,
        keywords: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> list[Document]:
        logger.info(
            f"Retriever tool query: {keywords}", extra={"resources": self.resources}
        )
        documents = self.retriever.query_relevant_documents(keywords, self.resources)
        if not documents:
            return "No results found from the local knowledge base."

        # Post-process to control context size
        try:
            max_docs = int(os.getenv("RAG_TOOL_MAX_DOCS", "3"))
        except ValueError:
            max_docs = 3
        try:
            max_chunks_per_doc = int(os.getenv("RAG_TOOL_MAX_CHUNKS_PER_DOC", "5"))
        except ValueError:
            max_chunks_per_doc = 5
        try:
            max_chars_per_doc = int(os.getenv("RAG_TOOL_MAX_CHARS_PER_DOC", "4000"))
        except ValueError:
            max_chars_per_doc = 4000
        try:
            max_total_chars = int(os.getenv("RAG_TOOL_MAX_TOTAL_CHARS", "8000"))
        except ValueError:
            max_total_chars = 8000

        trimmed_docs = []
        seen_hashes = set()
        for doc in documents[:max_docs]:
            # sort chunks by similarity desc if available
            chunks = getattr(doc, "chunks", []) or []
            try:
                chunks = sorted(
                    [c for c in chunks if getattr(c, "content", None)],
                    key=lambda c: getattr(c, "similarity", 0.0),
                    reverse=True,
                )
            except Exception:
                pass

            selected = chunks[:max_chunks_per_doc]
            content = "\n\n".join(getattr(c, "content", "") for c in selected)
            if len(content) > max_chars_per_doc:
                content = content[:max_chars_per_doc] + "\n\n...[truncated]"

            h = hash(content)
            if content and h not in seen_hashes:
                seen_hashes.add(h)
                trimmed_docs.append(
                    {
                        "id": getattr(doc, "id", ""),
                        **({"url": doc.url} if getattr(doc, "url", None) else {}),
                        **({"title": doc.title} if getattr(doc, "title", None) else {}),
                        "content": content,
                    }
                )

        # Enforce total characters cap across all docs
        total_chars = sum(len(d.get("content", "")) for d in trimmed_docs)
        if total_chars > max_total_chars and trimmed_docs:
            # Simple proportional trimming to fit within cap
            scale = max_total_chars / max(total_chars, 1)
            new_total = 0
            for d in trimmed_docs:
                content = d.get("content", "")
                new_len = int(len(content) * scale)
                d["content"] = content[: new_len] + ("\n\n...[truncated]" if len(content) > new_len else "")
                new_total += len(d["content"])
            total_chars = new_total

        logger.info(
            "Retriever output trimmed.",
            extra={
                "docs": len(trimmed_docs),
                "max_chunks_per_doc": max_chunks_per_doc,
                "max_chars_per_doc": max_chars_per_doc,
                "max_total_chars": max_total_chars,
                "total_chars_after_trim": total_chars,
                **({"max_total_tokens": max_total_tokens} if "max_total_tokens" in locals() and max_total_tokens else {}),
            },
        )
        return trimmed_docs

    async def _arun(
        self,
        keywords: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> list[Document]:
        return self._run(keywords, run_manager.get_sync())


def get_retriever_tool(resources: List[Resource]) -> RetrieverTool | None:
    if not resources:
        return None
    logger.info(f"create retriever tool: {SELECTED_RAG_PROVIDER}")
    retriever = build_retriever()

    if not retriever:
        return None
    return RetrieverTool(retriever=retriever, resources=resources)
