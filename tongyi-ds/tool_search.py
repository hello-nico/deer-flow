import http.client
import json
import os
from typing import List, Optional, Sequence, Union

import requests
from qwen_agent.tools.base import BaseTool, register_tool


SERPER_KEY = os.environ.get("SERPER_KEY_ID", "")
TAVILY_KEY = os.environ.get("TAVILY_API_KEY", "")
DEFAULT_PROVIDER = os.environ.get("SEARCH_PROVIDER", "auto").lower()


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


@register_tool("search", allow_overwrite=True)
class Search(BaseTool):
    name = "search"
    description = (
        "Performs batched web searches: supply an array 'query'; the tool retrieves the top"
        " 10 results for each query in one call."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Array of query strings. Include multiple complementary search queries in a single call.",
            },
            "provider": {
                "type": "string",
                "enum": ["auto", "serper", "tavily"],
                "description": "Search provider hint. Defaults to auto-detect based on configured API keys.",
            },
        },
        "required": ["query"],
    }

    def __init__(self, cfg: Optional[dict] = None):
        super().__init__(cfg)

    def call(self, params: Union[str, dict], **kwargs) -> str:
        try:
            query_param = params["query"]
        except Exception:
            return "[Search] Invalid request format: Input must be a JSON object containing 'query' field"

        provider_hint = str(params.get("provider", DEFAULT_PROVIDER)).lower()
        queries = self._normalize_queries(query_param)
        if not queries:
            return "[Search] No valid query string provided."

        responses = []
        for q in queries:
            response, provider = self._run_with_fallback(q, provider_hint)
            header = f"Provider: {provider}\n" if provider else ""
            responses.append(f"{header}{response}")
        return "\n=======\n".join(responses)

    def _normalize_queries(self, query: Union[str, Sequence[str]]) -> List[str]:
        if isinstance(query, str):
            query_list = [query]
        else:
            query_list = [item for item in query if isinstance(item, str)]
        return [item.strip() for item in query_list if item and item.strip()]

    def _run_with_fallback(self, query: str, provider_hint: str) -> (str, str):
        provider_order = self._resolve_provider_order(provider_hint)
        errors = []
        for provider in provider_order:
            if provider == "serper":
                result = self._search_serper(query)
            else:
                result = self._search_tavily(query)
            if result.success:
                return result.payload, provider
            errors.append(result.payload)
        fallback_msg = "\n".join(errors) if errors else "No search provider is configured."
        return fallback_msg or "Search failed without specific error.", ""

    def _resolve_provider_order(self, provider_hint: str) -> List[str]:
        if provider_hint in {"serper", "tavily"}:
            return [provider_hint]
        order: List[str] = []
        if SERPER_KEY:
            order.append("serper")
        if TAVILY_KEY:
            order.append("tavily")
        if not order:
            order = ["serper", "tavily"]
        return order

    def _search_serper(self, query: str):
        if not SERPER_KEY:
            return _SearchResult(False, "[Search] SERPER_KEY_ID not configured.")

        payload = {
            "q": query,
            "location": "China" if _contains_cjk(query) else "United States",
            "gl": "cn" if _contains_cjk(query) else "us",
            "hl": "zh-cn" if _contains_cjk(query) else "en",
        }

        headers = {
            "X-API-KEY": SERPER_KEY,
            "Content-Type": "application/json",
        }

        try:
            conn = http.client.HTTPSConnection("google.serper.dev", timeout=30)
            conn.request("POST", "/search", json.dumps(payload), headers)
            res = conn.getresponse()
            data = res.read()
            conn.close()
        except Exception as exc:  # noqa: BLE001
            return _SearchResult(False, f"[Search] Serper request error: {exc}")

        if res.status != 200:
            return _SearchResult(False, f"[Search] Serper HTTP {res.status}: {data.decode('utf-8', 'ignore')[:300]}")

        try:
            results = json.loads(data.decode("utf-8"))
        except json.JSONDecodeError:
            return _SearchResult(False, "[Search] Failed to decode Serper response.")

        organic = results.get("organic", [])
        if not organic:
            return _SearchResult(False, f"No results found for '{query}'. Try a broader query.")

        snippets = []
        for idx, page in enumerate(organic, start=1):
            date_info = f"\nDate published: {page['date']}" if page.get("date") else ""
            source_info = f"\nSource: {page['source']}" if page.get("source") else ""
            snippet_text = page.get("snippet", "").replace("Your browser can't play this video.", "")
            snippet_body = f"\n{snippet_text}" if snippet_text else ""
            snippets.append(
                f"{idx}. [{page.get('title', 'Untitled')}]({page.get('link', '')})"
                f"{date_info}{source_info}{snippet_body}"
            )

        body = "\n\n".join(snippets)
        content = (
            f"A Serper search for '{query}' found {len(snippets)} results:\n\n" "## Web Results\n" f"{body}"
        )
        return _SearchResult(True, content)

    def _search_tavily(self, query: str):
        if not TAVILY_KEY:
            return _SearchResult(False, "[Search] TAVILY_API_KEY not configured.")

        payload = {
            "api_key": TAVILY_KEY,
            "query": query,
            "search_depth": "advanced",
            "include_answer": True,
            "max_results": 10,
        }

        try:
            response = requests.post(
                "https://api.tavily.com/search",
                json=payload,
                timeout=30,
            )
        except requests.RequestException as exc:  # noqa: BLE001
            return _SearchResult(False, f"[Search] Tavily request error: {exc}")

        if response.status_code != 200:
            return _SearchResult(
                False,
                f"[Search] Tavily HTTP {response.status_code}: {response.text[:300]}",
            )

        try:
            data = response.json()
        except ValueError:
            return _SearchResult(False, "[Search] Failed to decode Tavily response.")

        results = data.get("results", [])
        if not results:
            return _SearchResult(False, f"No results found for '{query}' via Tavily.")

        snippets = []
        for idx, item in enumerate(results, start=1):
            snippet_text = item.get("content", "")
            source = item.get("author") or item.get("metadata", {}).get("source")
            source_info = f"\nSource: {source}" if source else ""
            snippets.append(
                f"{idx}. [{item.get('title', 'Untitled')}]({item.get('url', '')})"
                f"{source_info}\n{snippet_text}"
            )

        answer_block = data.get("answer")
        answer_text = f"Suggested answer: {answer_block}\n\n" if answer_block else ""
        body = "\n\n".join(snippets)
        content = (
            f"A Tavily search for '{query}' found {len(snippets)} results:\n\n"
            f"{answer_text}## Web Results\n{body}"
        )
        return _SearchResult(True, content)


class _SearchResult:
    def __init__(self, success: bool, payload: str):
        self.success = success
        self.payload = payload
