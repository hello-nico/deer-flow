# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import logging
import os
from typing import List, Optional

from langchain_community.tools import (
    BraveSearch,
    DuckDuckGoSearchResults,
    WikipediaQueryRun,
)
from langchain_community.tools.arxiv import ArxivQueryRun
from langchain_community.utilities import (
    ArxivAPIWrapper,
    BraveSearchWrapper,
    WikipediaAPIWrapper,
)

from src.config import SELECTED_SEARCH_ENGINE, SearchEngine, load_yaml_config
from src.tools.decorators import create_logged_tool
from src.tools.tavily_search.tavily_search_results_with_images import (
    TavilySearchWithImages,
)
from src.utils.translation import translate_to_en

logger = logging.getLogger(__name__)


class PreprocessedTavilySearch(TavilySearchWithImages):
    """Tavily search tool with automatic query preprocessing for English queries."""

    @staticmethod
    def _ensure_english(query: str) -> str:
        """Translate incoming queries to English when necessary."""
        processed_query = translate_to_en(query)
        if processed_query != query:
            logger.info(
                "Preprocessed search query: '%s' -> '%s'", query, processed_query
            )
        return processed_query

    def _run(self, query: str, run_manager=None, **kwargs):
        # Preprocess the query to ensure it's in English
        processed_query = self._ensure_english(query)
        return super()._run(processed_query, run_manager=run_manager, **kwargs)

    async def _arun(self, query: str, run_manager=None, **kwargs):
        # Ensure async path also gets English queries
        processed_query = self._ensure_english(query)
        return await super()._arun(processed_query, run_manager=run_manager, **kwargs)


def preprocess_search_query(query: str, enhanced_query_en: str = "") -> str:
    """
    Preprocess search query to ensure it's in English for optimal search results.

    Args:
        query: Original search query
        enhanced_query_en: Enhanced English query from prompt enhancer (if available)

    Returns:
        English query for searching
    """
    #优先使用增强后的英文查询
    if enhanced_query_en and enhanced_query_en.strip():
        logger.debug(f"Using enhanced English query: {enhanced_query_en}")
        return enhanced_query_en

    #如果没有增强查询，尝试翻译原始查询
    if query and query.strip():
        translated_query = translate_to_en(query)
        if translated_query != query:
            logger.info(f"Translated search query to English: '{query}' -> '{translated_query}'")
            return translated_query
        else:
            logger.debug("Query is already in English or translation failed")
            return query

    # Fallback to empty string
    return ""


# Create logged versions of the search tools
LoggedTavilySearch = create_logged_tool(PreprocessedTavilySearch)
LoggedDuckDuckGoSearch = create_logged_tool(DuckDuckGoSearchResults)
LoggedBraveSearch = create_logged_tool(BraveSearch)
LoggedArxivSearch = create_logged_tool(ArxivQueryRun)
LoggedWikipediaSearch = create_logged_tool(WikipediaQueryRun)


def get_search_config():
    config = load_yaml_config("conf.yaml")
    search_config = config.get("SEARCH_ENGINE", {})
    return search_config


def get_web_search_tool(max_search_results: int):
    search_config = get_search_config()

    if SELECTED_SEARCH_ENGINE == SearchEngine.TAVILY.value:
        # Only get and apply include/exclude domains for Tavily
        include_domains: Optional[List[str]] = search_config.get("include_domains", [])
        exclude_domains: Optional[List[str]] = search_config.get("exclude_domains", [])

        logger.info(
            f"Tavily search configuration loaded: include_domains={include_domains}, exclude_domains={exclude_domains}"
        )

        return LoggedTavilySearch(
            name="web_search",
            max_results=max_search_results,
            include_raw_content=True,
            include_images=True,
            include_image_descriptions=True,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
        )
    elif SELECTED_SEARCH_ENGINE == SearchEngine.DUCKDUCKGO.value:
        return LoggedDuckDuckGoSearch(
            name="web_search",
            num_results=max_search_results,
        )
    elif SELECTED_SEARCH_ENGINE == SearchEngine.BRAVE_SEARCH.value:
        return LoggedBraveSearch(
            name="web_search",
            search_wrapper=BraveSearchWrapper(
                api_key=os.getenv("BRAVE_SEARCH_API_KEY", ""),
                search_kwargs={"count": max_search_results},
            ),
        )
    elif SELECTED_SEARCH_ENGINE == SearchEngine.ARXIV.value:
        return LoggedArxivSearch(
            name="web_search",
            api_wrapper=ArxivAPIWrapper(
                top_k_results=max_search_results,
                load_max_docs=max_search_results,
                load_all_available_meta=True,
            ),
        )
    elif SELECTED_SEARCH_ENGINE == SearchEngine.WIKIPEDIA.value:
        wiki_lang = search_config.get("wikipedia_lang", "en")
        wiki_doc_content_chars_max = search_config.get(
            "wikipedia_doc_content_chars_max", 4000
        )
        return LoggedWikipediaSearch(
            name="web_search",
            api_wrapper=WikipediaAPIWrapper(
                lang=wiki_lang,
                top_k_results=max_search_results,
                load_all_available_meta=True,
                doc_content_chars_max=wiki_doc_content_chars_max,
            ),
        )
    else:
        raise ValueError(f"Unsupported search engine: {SELECTED_SEARCH_ENGINE}")
