# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.utils.translation import translate_to_en, _is_likely_english
from src.tools.search import PreprocessedTavilySearch
from src.tools.tavily_search.tavily_search_results_with_images import (
    TavilySearchWithImages,
)


class TestTranslation:
    """Test cases for translation utilities."""

    def test_translate_to_en_empty_string(self):
        """Test translation with empty string."""
        result = translate_to_en("")
        assert result == ""

    def test_translate_to_en_whitespace_string(self):
        """Test translation with whitespace string."""
        result = translate_to_en("   ")
        assert result == "   "

    def test_translate_to_en_english_text(self):
        """Test translation with English text (should return as-is)."""
        text = "This is an English text about artificial intelligence."
        result = translate_to_en(text)
        assert result == text

    @patch("src.utils.translation.get_llm_by_type")
    def test_translate_to_en_non_english_invokes_llm(self, mock_get_llm):
        """Non-English text should be translated using LLM."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Translated English text"
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        text = "这是一段中文文本"
        result = translate_to_en(text)

        assert result == "Translated English text"
        mock_llm.invoke.assert_called_once()

    @patch("src.utils.translation.get_llm_by_type")
    def test_translate_to_en_mixed_locale_invokes_llm(self, mock_get_llm):
        """Mixed language queries containing locale hints should trigger translation."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Self-RAG research plan"
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        text = "Self-RAG 研究计划 locale zh-CN"
        result = translate_to_en(text)

        assert result == "Self-RAG research plan"
        mock_llm.invoke.assert_called_once()

    @patch("src.utils.translation.get_llm_by_type", side_effect=Exception("mock failure"))
    def test_translate_to_en_translation_failure(self, mock_get_llm):
        """Translation failure should fallback to original text."""
        text = "这是一段中文文本"
        result = translate_to_en(text)
        assert result == text

    @patch("src.utils.translation.get_llm_by_type")
    def test_translate_to_en_skips_llm_for_english(self, mock_get_llm):
        """English text should bypass LLM translation."""
        text = "This is already in English."
        result = translate_to_en(text)
        assert result == text
        mock_get_llm.assert_not_called()

    def test_is_likely_english_empty_string(self):
        """Test English detection with empty string."""
        result = _is_likely_english("")
        assert result == True

    def test_is_likely_english_english_text(self):
        """Test English detection with English text."""
        text = "This is a comprehensive analysis of artificial intelligence and machine learning applications."
        result = _is_likely_english(text)
        assert result == True

    def test_is_likely_english_common_words(self):
        """Test English detection with common English words."""
        text = "The quick brown fox jumps over the lazy dog. This is a test of the system."
        result = _is_likely_english(text)
        assert result == True

    def test_is_likely_english_mixed_ascii(self):
        """Test English detection with mixed ASCII content."""
        text = "Hello World! 123 ABC xyz"
        result = _is_likely_english(text)
        # Should return True for mostly ASCII content
        assert result == True

    def test_is_likely_english_non_ascii_content(self):
        """Test English detection with non-ASCII content."""
        text = "这是一个中文文本，包含很多中文字符。"
        result = _is_likely_english(text)
        assert result == False

    def test_is_likely_english_mixed_content(self):
        """Test English detection with mixed content."""
        text = "This is a mix of English and 中文 text."
        result = _is_likely_english(text)
        # Presence of CJK characters should now force translation.
        assert result is False

    def test_is_likely_english_mixed_with_locale_hint(self):
        """Mixed locale queries containing zh-CN should trigger translation."""
        text = "Self-RAG 研究计划 locale zh-CN"
        result = _is_likely_english(text)
        assert result is False

    def test_is_likely_english_short_english(self):
        """Test English detection with short English text."""
        text = "Hello world"
        result = _is_likely_english(text)
        assert result == True

    def test_is_likely_english_short_non_english(self):
        """Test English detection with short non-English text."""
        text = "你好世界"
        result = _is_likely_english(text)
        assert result == False

    def test_is_likely_english_numeric_content(self):
        """Test English detection with numeric content."""
        text = "12345 67890"
        result = _is_likely_english(text)
        assert result == True  # Should be True as it's all ASCII

    def test_is_likely_english_special_characters(self):
        """Test English detection with special characters."""
        text = "Hello! @#$% World"
        result = _is_likely_english(text)
        assert result == True

    def test_is_likely_english_code_content(self):
        """Test English detection with code-like content."""
        text = "def hello_world(): print('Hello, World!')"
        result = _is_likely_english(text)
        # Code content is mostly ASCII, should return True
        assert result == True

    def test_preprocessed_tavily_search_run_translates(self):
        """Ensure sync Tavily tool enforces English queries."""
        tool = PreprocessedTavilySearch(name="web_search")

        with patch("src.tools.search.translate_to_en", return_value="english query") as mock_translate, \
            patch("src.tools.tavily_search.tavily_search_results_with_images.TavilySearchWithImages._run", return_value="ok") as mock_super_run:
            result = tool._run("中文查询")

        assert result == "ok"
        mock_translate.assert_called_once_with("中文查询")
        # super()._run is bound, so first positional arg is the translated query
        assert mock_super_run.call_args.args[0] == "english query"

    def test_preprocessed_tavily_search_arun_translates(self):
        """Ensure async Tavily tool enforces English queries."""
        tool = PreprocessedTavilySearch(name="web_search")

        async def _run_test():
            with patch("src.tools.search.translate_to_en", return_value="english query") as mock_translate, \
                patch.object(TavilySearchWithImages, "_arun", new_callable=AsyncMock) as mock_super_arun:
                mock_super_arun.return_value = "async-ok"
                result = await tool._arun("中文查询")

            assert result == "async-ok"
            mock_translate.assert_called_once_with("中文查询")
            assert mock_super_arun.await_args.args[0] == "english query"

        asyncio.run(_run_test())
