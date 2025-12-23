"""
WebSearchService 属性测试
"""
import sys
import os

# 添加 backend 目录到 Python 路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, ".env"))

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from app.schemas.web_search import SearchResult, WebSearchResponse
from app.services.web_search_service import WebSearchService


class TestAPIKeyConfiguration:
    """Property 4: API Key Configuration - 测试 API 密钥配置"""

    def test_no_api_keys_disables_service(self):
        """没有 API 密钥时服务应该被禁用"""
        with patch("app.services.web_search_service.settings") as mock_settings:
            mock_settings.tavily_api_key = ""
            mock_settings.firecrawl_api_key = ""
            mock_settings.web_search_timeout = 30
            mock_settings.web_search_max_results = 10

            service = WebSearchService()
            assert service.enabled is False
            assert service.tavily_enabled is False
            assert service.firecrawl_enabled is False

    def test_only_tavily_key_enables_tavily(self):
        """只有 Tavily 密钥时只启用 Tavily"""
        with patch("app.services.web_search_service.settings") as mock_settings:
            mock_settings.tavily_api_key = "test-tavily-key"
            mock_settings.firecrawl_api_key = ""
            mock_settings.web_search_timeout = 30
            mock_settings.web_search_max_results = 10

            with patch("app.services.web_search_service.TavilyClient"):
                service = WebSearchService()
                assert service.enabled is True
                assert service.tavily_enabled is True
                assert service.firecrawl_enabled is False

    def test_only_firecrawl_key_enables_firecrawl(self):
        """只有 Firecrawl 密钥时只启用 Firecrawl"""
        with patch("app.services.web_search_service.settings") as mock_settings:
            mock_settings.tavily_api_key = ""
            mock_settings.firecrawl_api_key = "test-firecrawl-key"
            mock_settings.web_search_timeout = 30
            mock_settings.web_search_max_results = 10

            with patch("app.services.web_search_service.FirecrawlApp"):
                service = WebSearchService()
                assert service.enabled is True
                assert service.tavily_enabled is False
                assert service.firecrawl_enabled is True

    def test_both_keys_enable_both_services(self):
        """两个密钥都有时启用两个服务"""
        with patch("app.services.web_search_service.settings") as mock_settings:
            mock_settings.tavily_api_key = "test-tavily-key"
            mock_settings.firecrawl_api_key = "test-firecrawl-key"
            mock_settings.web_search_timeout = 30
            mock_settings.web_search_max_results = 10

            with patch("app.services.web_search_service.TavilyClient"):
                with patch("app.services.web_search_service.FirecrawlApp"):
                    service = WebSearchService()
                    assert service.enabled is True
                    assert service.tavily_enabled is True
                    assert service.firecrawl_enabled is True


class TestURLDeduplication:
    """Property 2: URL Deduplication - 测试 URL 去重"""

    def test_removes_duplicate_urls(self):
        """应该移除重复的 URL"""
        service = WebSearchService()
        service.tavily_enabled = False
        service.firecrawl_enabled = False

        results = [
            SearchResult(url="https://example.com/page1", title="Page 1", snippet="Content 1", source="tavily"),
            SearchResult(url="https://example.com/page1", title="Page 1 Dup", snippet="Content 1 Dup", source="firecrawl"),
            SearchResult(url="https://example.com/page2", title="Page 2", snippet="Content 2", source="tavily"),
        ]

        merged = service._merge_and_dedupe(results)
        assert len(merged) == 2
        urls = [r.url for r in merged]
        assert "https://example.com/page1" in urls
        assert "https://example.com/page2" in urls

    def test_normalizes_urls_for_dedup(self):
        """应该标准化 URL 进行去重（去除尾部斜杠）"""
        service = WebSearchService()
        service.tavily_enabled = False
        service.firecrawl_enabled = False

        results = [
            SearchResult(url="https://example.com/page/", title="Page", snippet="Content", source="tavily"),
            SearchResult(url="https://example.com/page", title="Page", snippet="Content", source="firecrawl"),
        ]

        merged = service._merge_and_dedupe(results)
        assert len(merged) == 1

    def test_preserves_unique_urls(self):
        """应该保留所有唯一的 URL"""
        service = WebSearchService()
        service.tavily_enabled = False
        service.firecrawl_enabled = False

        results = [
            SearchResult(url="https://example1.com", title="Page 1", snippet="Content 1", source="tavily"),
            SearchResult(url="https://example2.com", title="Page 2", snippet="Content 2", source="firecrawl"),
            SearchResult(url="https://example3.com", title="Page 3", snippet="Content 3", source="tavily"),
        ]

        merged = service._merge_and_dedupe(results)
        assert len(merged) == 3


class TestFaultTolerance:
    """Property 3: Fault Tolerance - 测试容错处理"""

    @pytest.mark.asyncio
    async def test_returns_results_when_one_source_fails(self):
        """一个源失败时应该返回另一个源的结果"""
        with patch("app.services.web_search_service.settings") as mock_settings:
            mock_settings.tavily_api_key = "test-key"
            mock_settings.firecrawl_api_key = "test-key"
            mock_settings.web_search_timeout = 30
            mock_settings.web_search_max_results = 10

            service = WebSearchService()
            service.tavily_enabled = True
            service.firecrawl_enabled = True

            # Mock Tavily 成功，Firecrawl 失败
            async def mock_tavily_search(query, max_results):
                return [SearchResult(url="https://tavily.com", title="Tavily Result", snippet="Content", source="tavily")]

            async def mock_firecrawl_search(query, max_results):
                raise Exception("Firecrawl API Error")

            service._tavily_search = mock_tavily_search
            service._firecrawl_search = mock_firecrawl_search

            response = await service.search("test query")

            assert len(response.results) == 1
            assert response.results[0].source == "tavily"
            assert len(response.errors) == 1
            assert "firecrawl" in response.errors[0].lower()

    @pytest.mark.asyncio
    async def test_returns_empty_when_both_fail(self):
        """两个源都失败时应该返回空结果和错误信息"""
        with patch("app.services.web_search_service.settings") as mock_settings:
            mock_settings.tavily_api_key = "test-key"
            mock_settings.firecrawl_api_key = "test-key"
            mock_settings.web_search_timeout = 30
            mock_settings.web_search_max_results = 10

            service = WebSearchService()
            service.tavily_enabled = True
            service.firecrawl_enabled = True

            async def mock_failing_search(query, max_results):
                raise Exception("API Error")

            service._tavily_search = mock_failing_search
            service._firecrawl_search = mock_failing_search

            response = await service.search("test query")

            assert len(response.results) == 0
            assert len(response.errors) == 2


class TestTimeoutHandling:
    """Property 5: Timeout Handling - 测试超时处理"""

    @pytest.mark.asyncio
    async def test_respects_timeout(self):
        """搜索应该在超时时间内完成"""
        with patch("app.services.web_search_service.settings") as mock_settings:
            mock_settings.tavily_api_key = "test-key"
            mock_settings.firecrawl_api_key = ""
            mock_settings.web_search_timeout = 1
            mock_settings.web_search_max_results = 10

            service = WebSearchService()
            service.tavily_enabled = True
            service.firecrawl_enabled = False

            async def slow_search(query, max_results):
                await asyncio.sleep(5)  # 模拟慢搜索
                return []

            service._tavily_search = slow_search

            response = await service.search("test query", timeout=1)

            # 应该超时并返回错误
            assert "超时" in str(response.errors)


class TestContextFormatting:
    """Property 6: Context Formatting - 测试上下文格式化"""

    def test_formats_context_correctly(self):
        """应该正确格式化搜索结果为 LLM 上下文"""
        service = WebSearchService()
        service.tavily_enabled = False
        service.firecrawl_enabled = False

        results = [
            SearchResult(url="https://example.com/1", title="Title 1", snippet="Content 1", source="tavily"),
            SearchResult(url="https://example.com/2", title="Title 2", snippet="Content 2", source="firecrawl"),
        ]

        context = service.format_context(results)

        assert "【联网搜索结果】" in context
        assert "[来源1] Title 1" in context
        assert "[来源2] Title 2" in context
        assert "https://example.com/1" in context
        assert "https://example.com/2" in context
        assert "[来源X]" in context

    def test_limits_snippet_length(self):
        """应该限制摘要长度为 500 字符"""
        service = WebSearchService()
        service.tavily_enabled = False
        service.firecrawl_enabled = False

        long_snippet = "A" * 1000
        results = [
            SearchResult(url="https://example.com", title="Title", snippet=long_snippet, source="tavily"),
        ]

        context = service.format_context(results)

        # 检查内容中的摘要不超过 500 字符
        assert "A" * 501 not in context

    def test_empty_results_returns_empty_string(self):
        """空结果应该返回空字符串"""
        service = WebSearchService()
        service.tavily_enabled = False
        service.firecrawl_enabled = False

        context = service.format_context([])
        assert context == ""


class TestResultLimit:
    """Property 7: Result Limit - 测试结果数量限制"""

    def test_limits_results_to_five(self):
        """应该限制结果数量为 5"""
        service = WebSearchService()
        service.tavily_enabled = False
        service.firecrawl_enabled = False

        results = [
            SearchResult(url=f"https://example.com/{i}", title=f"Title {i}", snippet=f"Content {i}", source="tavily")
            for i in range(10)
        ]

        selected = service._select_top_results(results, "test query", limit=5)
        assert len(selected) == 5

    def test_returns_all_if_less_than_limit(self):
        """结果少于限制时应该返回所有结果"""
        service = WebSearchService()
        service.tavily_enabled = False
        service.firecrawl_enabled = False

        results = [
            SearchResult(url=f"https://example.com/{i}", title=f"Title {i}", snippet=f"Content {i}", source="tavily")
            for i in range(3)
        ]

        selected = service._select_top_results(results, "test query", limit=5)
        assert len(selected) == 3


class TestTimeSensitiveQuery:
    """Property 8: Time-Sensitive Query Handling - 测试时效性查询处理"""

    def test_detects_time_sensitive_keywords(self):
        """应该检测时效性关键词"""
        service = WebSearchService()
        service.tavily_enabled = False
        service.firecrawl_enabled = False

        assert service._is_time_sensitive_query("最新的 Python 教程") is True
        assert service._is_time_sensitive_query("今天的新闻") is True
        assert service._is_time_sensitive_query("latest news") is True
        assert service._is_time_sensitive_query("Python 基础教程") is False

    def test_sorts_by_recency(self):
        """应该按时效性排序"""
        service = WebSearchService()
        service.tavily_enabled = False
        service.firecrawl_enabled = False

        results = [
            SearchResult(url="https://example.com/1", title="Old", snippet="Content", source="tavily", published_date=None),
            SearchResult(url="https://example.com/2", title="New", snippet="Content", source="tavily", published_date="2025-01-01"),
            SearchResult(url="https://example.com/3", title="Newer", snippet="Content", source="tavily", published_date="2025-06-01"),
        ]

        sorted_results = service._sort_by_recency(results)

        # 有日期的应该排在前面
        assert sorted_results[0].published_date is not None
        assert sorted_results[1].published_date is not None
        assert sorted_results[2].published_date is None
