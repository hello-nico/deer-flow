import json
import os
import re
import time
from typing import Dict, Iterable, List, Optional, Union

import requests
import tiktoken
from openai import OpenAI
from qwen_agent.tools.base import BaseTool, register_tool

from prompt import EXTRACTOR_PROMPT

VISIT_SERVER_TIMEOUT = int(os.getenv("VISIT_SERVER_TIMEOUT", 200))
WEBCONTENT_MAXLENGTH = int(os.getenv("WEBCONTENT_MAXLENGTH", 150000))

JINA_API_KEYS = os.getenv("JINA_API_KEYS", "")


@staticmethod
def truncate_to_tokens(text: str, max_tokens: int = 95000) -> str:
    encoding = tiktoken.get_encoding("cl100k_base")
    
    tokens = encoding.encode(text)
    if len(tokens) <= max_tokens:
        return text
    
    truncated_tokens = tokens[:max_tokens]
    return encoding.decode(truncated_tokens)

OSS_JSON_FORMAT = """# Response Formats
## visit_content
{"properties":{"rational":{"type":"string","description":"Locate the **specific sections/data** directly related to the user's goal within the webpage content"},"evidence":{"type":"string","description":"Identify and extract the **most relevant information** from the content, never miss any important information, output the **full original context** of the content as far as possible, it can be more than three paragraphs.","summary":{"type":"string","description":"Organize into a concise paragraph with logical flow, prioritizing clarity and judge the contribution of the information to the goal."}}}}"""


@register_tool('visit', allow_overwrite=True)
class Visit(BaseTool):
    # The `description` tells the agent the functionality of this tool.
    name = 'visit'
    description = 'Visit webpage(s) and return the summary of the content.'
    # The `parameters` tell the agent what input parameters the tool has.
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": ["string", "array"],
                "items": {
                    "type": "string"
                    },
                "minItems": 1,
                "description": "The URL(s) of the webpage(s) to visit. Can be a single URL or an array of URLs."
        },
        "goal": {
                "type": "string",
                "description": "The goal of the visit for webpage(s)."
        }
        },
        "required": ["url", "goal"]
    }
    # The `call` method is the main function of the tool.
    def call(self, params: Union[str, dict], **kwargs) -> str:
        try:
            url = params["url"]
            goal = params["goal"]
        except Exception:
            return "[Visit] Invalid request format: Input must be a JSON object containing 'url' and 'goal' fields"

        os.makedirs("log", exist_ok=True)

        if isinstance(url, str):
            response = self.readpage_jina(url, goal)
        else:
            response_blocks = []
            assert isinstance(url, List)
            start_time = time.time()
            for item in url:
                if time.time() - start_time > 900:
                    response_blocks.append(self._build_empty_response(item, goal))
                    continue
                try:
                    response_blocks.append(self.readpage_jina(item, goal))
                except Exception as exc:  # noqa: BLE001
                    response_blocks.append(f"Error fetching {item}: {exc}")
            response = "\n=======\n".join(response_blocks)

        preview = response[:500] + ("..." if len(response) > 500 else "")
        print(f"[visit] Summary length {len(response)}; preview: {preview}")
        return response.strip()
        
    def call_server(self, msgs: List[Dict[str, str]], max_retries: int = 2) -> str:
        api_key = os.environ.get("API_KEY")
        url_llm = os.environ.get("API_BASE")
        model_name = os.environ.get("SUMMARY_MODEL_NAME", "")
        if not (api_key and url_llm and model_name):
            return ""

        client = OpenAI(api_key=api_key, base_url=url_llm)
        for attempt in range(max_retries):
            try:
                chat_response = client.chat.completions.create(
                    model=model_name,
                    messages=msgs,
                    temperature=0.7,
                )
            except Exception as exc:  # noqa: BLE001
                if attempt == max_retries - 1:
                    return ""
                continue

            if not chat_response.choices:
                continue
            content = chat_response.choices[0].message.content or ""
            if not content:
                continue

            left = content.find("{")
            right = content.rfind("}")
            if left != -1 and right != -1 and left <= right:
                return content[left : right + 1]
            return content

        return ""


    def jina_readpage(self, url: str) -> str:
        """
        Read webpage content using Jina service.

        Args:
            url: The URL to read
            goal: The goal/purpose of reading the page

        Returns:
            str: The webpage content or error message
        """
        max_retries = 3
        timeout = 50

        # 检查 API Key 是否存在
        if not JINA_API_KEYS or JINA_API_KEYS.strip() == "":
            return "[visit] JINA_API_KEYS not configured. Please set the environment variable."

        for attempt in range(max_retries):
            headers = {
                "Authorization": f"Bearer {JINA_API_KEYS}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
            try:
                response = requests.get(
                    f"https://r.jina.ai/{url}",
                    headers=headers,
                    timeout=timeout
                )
                if response.status_code == 200:
                    webpage_content = response.text
                    # 检查是否返回了有效的内容
                    if webpage_content and len(webpage_content.strip()) > 0:
                        return webpage_content
                    else:
                        print(f"[visit] Empty content returned for URL: {url}")
                        continue
                else:
                    print(f"[visit] HTTP {response.status_code} for URL: {url}")
                    print(f"[visit] Response: {response.text}")
                    if response.status_code == 401:
                        return "[visit] Invalid JINA_API_KEYS. Please check your API key."
                    elif response.status_code == 429:
                        # Rate limited, wait longer
                        time.sleep(2)
                        continue
                    else:
                        raise ValueError(f"jina readpage error: HTTP {response.status_code}")
            except requests.exceptions.Timeout:
                print(f"[visit] Timeout for URL: {url}")
                if attempt == max_retries - 1:
                    return "[visit] Failed to read page due to timeout."
                time.sleep(1)
            except requests.exceptions.ConnectionError:
                print(f"[visit] Connection error for URL: {url}")
                if attempt == max_retries - 1:
                    return "[visit] Failed to read page due to connection error."
                time.sleep(1)
            except Exception as e:
                print(f"[visit] Error for URL {url}: {str(e)}")
                if attempt == max_retries - 1:
                    return f"[visit] Failed to read page: {str(e)}"
                time.sleep(0.5)

        return "[visit] Failed to read page."

    def html_readpage_jina(self, url: str) -> str:
        max_attempts = 8
        for attempt in range(max_attempts):
            print(f"[visit] Attempt {attempt + 1}/{max_attempts} to read URL: {url}")
            content = self.jina_readpage(url)
            service = "jina"
            print(f"[visit] Using service: {service}")

            # 检查是否获取到了有效内容
            if content and not content.startswith("[visit] Failed to read page.") and content != "[visit] Empty content." and not content.startswith("[document_parser]"):
                # 验证内容质量
                if len(content.strip()) > 100:  # 确保内容不是太短
                    print(f"[visit] Successfully retrieved content, length: {len(content)}")
                    return content
                else:
                    print(f"[visit] Content too short: {len(content)} characters")
            else:
                print(f"[visit] Failed to get valid content: {content[:100] if content else 'No content'}...")

            # 在重试之间添加延迟
            if attempt < max_attempts - 1:
                time.sleep(1)

        return "[visit] Failed to read page."

    def readpage_jina(self, url: str, goal: str) -> str:
        """
        Attempt to read webpage content by alternating between jina and aidata services.
        
        Args:
            url: The URL to read
            goal: The goal/purpose of reading the page
            
        Returns:
            str: The webpage content or error message
        """
   
        summary_page_func = self.call_server
        max_retries = int(os.getenv('VISIT_SERVER_MAX_RETRIES', 1))

        content = self.html_readpage_jina(url)
        if not self._is_valid_content(content):
            return self._build_empty_response(url, goal)

        truncated = truncate_to_tokens(content, max_tokens=95000)
        summary = self._summarize_content(truncated, goal, summary_page_func, max_retries)
        if summary:
            return self._format_summary(url, goal, summary)

        fallback = self._fallback_extract(truncated, goal)
        return self._format_summary(url, goal, fallback)

    def _build_empty_response(self, url: str, goal: str) -> str:
        useful_information = (
            f"The useful information in {url} for user goal {goal} as follows: \n\n"
            "Evidence in page: \nThe provided webpage content could not be accessed. Please check the URL or file format.\n\n"
            "Summary: \nThe webpage content could not be processed, and therefore, no information is available.\n\n"
        )
        return useful_information

    def _is_valid_content(self, content: Optional[str]) -> bool:
        if not content:
            return False
        if content.startswith("[visit] Failed to read page"):
            return False
        if content == "[visit] Empty content.":
            return False
        if content.startswith("[document_parser]"):
            return False
        return True

    def _summarize_content(
        self,
        content: str,
        goal: str,
        summarizer,
        max_retries: int,
    ) -> Optional[Dict[str, str]]:
        prompt = EXTRACTOR_PROMPT.format(webpage_content=content, goal=goal)
        messages = [{"role": "user", "content": prompt}]

        attempt = 0
        truncated = content
        while attempt < 3:
            raw = summarizer(messages, max_retries=max_retries)
            if not raw:
                attempt += 1
                truncated = truncated[: int(len(truncated) * 0.7)] if len(truncated) > 2000 else truncated
                messages = [{"role": "user", "content": EXTRACTOR_PROMPT.format(webpage_content=truncated, goal=goal)}]
                continue

            raw = raw.replace("```json", "").replace("```", "").strip()
            parsed = self._safe_json_loads(raw)
            if parsed:
                return parsed

            attempt += 1
            truncated = truncated[: int(len(truncated) * 0.7)] if len(truncated) > 2000 else truncated
            messages = [{"role": "user", "content": EXTRACTOR_PROMPT.format(webpage_content=truncated, goal=goal)}]

        return None

    def _safe_json_loads(self, payload: str) -> Optional[Dict[str, str]]:
        if not payload:
            return None
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return None
        if not isinstance(data, dict):
            return None
        evidence = data.get("evidence")
        summary = data.get("summary")
        if not evidence or not summary:
            return None
        return {
            "evidence": str(evidence),
            "summary": str(summary),
            "rational": str(data.get("rational", "")),
        }

    def _fallback_extract(self, content: str, goal: str) -> Dict[str, str]:
        paragraphs = [para.strip() for para in content.splitlines() if para.strip()]
        keywords = [item.lower() for item in re.findall(r"[\w]+", goal) if len(item) > 1]

        evidence_blocks: List[str] = []
        if keywords:
            for para in paragraphs:
                text_lower = para.lower()
                if any(keyword in text_lower for keyword in keywords):
                    evidence_blocks.append(para)
                if len("\n\n".join(evidence_blocks)) > 1500:
                    break

        if not evidence_blocks:
            evidence_blocks = paragraphs[:3]

        evidence_text = "\n\n".join(evidence_blocks)[:2000]
        summary_text = self._simple_summarize(evidence_blocks, goal)

        return {
            "rational": "Extracted directly from webpage due to summarizer fallback.",
            "evidence": evidence_text,
            "summary": summary_text,
        }

    def _simple_summarize(self, paragraphs: Iterable[str], goal: str) -> str:
        joined = " ".join(paragraphs)
        snippet = joined[:600]
        suffix = "..." if len(joined) > 600 else ""
        return f"Based on the captured passages related to '{goal}', key points include: {snippet}{suffix}"

    def _format_summary(self, url: str, goal: str, summary: Dict[str, str]) -> str:
        evidence = summary.get("evidence", "The provided webpage content could not be accessed.")
        summary_text = summary.get("summary", "The webpage content could not be processed.")
        body = (
            f"The useful information in {url} for user goal {goal} as follows: \n\n"
            f"Evidence in page: \n{evidence}\n\n"
            f"Summary: \n{summary_text}\n\n"
        )
        return body

    
