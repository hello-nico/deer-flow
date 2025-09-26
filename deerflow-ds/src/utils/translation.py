# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import logging
import re
from typing import Optional
from langchain.schema import HumanMessage
from src.llms.llm import get_llm_by_type

logger = logging.getLogger(__name__)

# Detect common CJK character ranges to avoid false "English" positives when
# queries mix locales (e.g. "Self-RAG 研究计划 locale zh-CN").  Once any CJK
# rune shows up we should force translation to ensure outbound searches stay in
# English.
CJK_CHAR_PATTERN = re.compile(
    r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\u3000-\u303f\u3040-\u30ff\u31f0-\u31ff\uac00-\ud7a3\uff00-\uffef]"
)


def translate_to_en(text: str) -> str:
    """
    Translate text to English.

    Args:
        text: Input text to translate

    Returns:
        English translation of the text, or original text if translation fails
    """
    if not text or not text.strip():
        return text

    # Check if text is already in English (basic check)
    if _is_likely_english(text):
        return text

    try:
        # 使用基础模型进行翻译
        llm = get_llm_by_type("basic")

        # 构建翻译消息
        translation_prompt = f"""You are a professional translator. Your task is to translate the given text to English accurately.

Translation Requirements:
1. Accuracy: Translate the text precisely while preserving the original meaning and intent
2. Natural English: Ensure the translation reads naturally in English
3. Terminology: Translate technical terms and concepts correctly
4. Format: Maintain the original formatting and structure
5. Completeness: Translate all parts of the text, nothing should be omitted

Input Text:
{text}

Output Instructions:
- Provide only the English translation, nothing else
- Do not include any explanations, notes, or comments
- Do not translate emojis, hashtags, or metadata unless they are part of the main content
- If the text is already in English, return it as-is
- Keep the same tone and style as the original

Translation:"""

        messages = [HumanMessage(content=translation_prompt)]

        # 调用 LLM
        response = llm.invoke(messages)
        translated_text = getattr(response, "content", "").strip()

        if not translated_text:
            logger.warning("Translation result empty, falling back to original text")
            return text

        logger.info("Translated text: '%s' -> '%s'", text, translated_text)
        return translated_text

    except Exception as e:
        logger.error(f"Translation failed for text '{text}': {e}")
        # Fallback to original text
        return text


def _is_likely_english(text: str) -> bool:
    """
    Basic check if text is likely in English.

    Args:
        text: Text to check

    Returns:
        True if text appears to be in English
    """
    if not text or not text.strip():
        return True

    # If we spot any CJK characters, treat it as non-English immediately.
    if CJK_CHAR_PATTERN.search(text):
        return False

    # Simple heuristic: if text contains mostly ASCII characters and common English words
    # This is a basic implementation and could be improved

    # Check for non-ASCII characters
    ascii_ratio = sum(1 for c in text if ord(c) < 128) / len(text)

    # If less than 80% ASCII, likely not English (reduced threshold)
    if ascii_ratio < 0.8:
        return False

    # Check for common English words for texts with words
    common_english_words = {
        'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have',
        'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you',
        'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they',
        'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my',
        'one', 'all', 'would', 'there', 'their', 'what', 'so',
        'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me'
    }

    words = re.findall(r'\b\w+\b', text.lower())
    if words and len(words) >= 3:  # Only check for texts with 3+ words
        english_word_count = sum(1 for word in words if word in common_english_words)
        english_ratio = english_word_count / len(words)

        # If more than 20% of words are common English words, likely English (reduced threshold)
        if english_ratio > 0.2:
            return True

    # For short texts or mostly ASCII content, be more lenient
    return ascii_ratio > 0.8
