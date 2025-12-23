"""
联网搜索服务
并行调用 Tavily 和 Firecrawl API 获取搜索结果
"""
import asyncio
import time
import re
from typing import List, Optional
from tavily import TavilyClient

from app.config import settings
from app.schemas.web_search import SearchResult, WebSearchResponse


class WebSearchService:
    """联网搜索服务"""

    def __init__(self):
        """初始化搜索服务，检查 API 密钥可用性"""
        self.tavily_client: Optional[TavilyClient] = None
        self.firecrawl_client = None  # 使用新版 Firecrawl SDK
        self.tavily_enabled = False
        self.firecrawl_enabled = False

        print(f"🔍 [WebSearchService] 初始化中...")
        print(f"🔍 [WebSearchService] tavily_api_key: {'已配置' if settings.tavily_api_key else '未配置'}")
        print(f"🔍 [WebSearchService] firecrawl_api_key: {'已配置' if settings.firecrawl_api_key else '未配置'}")

        # 初始化 Tavily
        if settings.tavily_api_key:
            try:
                self.tavily_client = TavilyClient(api_key=settings.tavily_api_key)
                self.tavily_enabled = True
                print(f"✅ [WebSearchService] Tavily 初始化成功")
            except Exception as e:
                print(f"⚠️ [WebSearchService] Tavily 初始化失败: {e}")

        # 初始化 Firecrawl（使用新版 SDK）
        if settings.firecrawl_api_key:
            try:
                from firecrawl import Firecrawl
                self.firecrawl_client = Firecrawl(api_key=settings.firecrawl_api_key)
                self.firecrawl_enabled = True
                print(f"✅ [WebSearchService] Firecrawl 初始化成功（新版 SDK）")
            except ImportError:
                # 回退到旧版 SDK
                try:
                    from firecrawl import FirecrawlApp
                    self.firecrawl_client = FirecrawlApp(api_key=settings.firecrawl_api_key)
                    self.firecrawl_enabled = True
                    print(f"✅ [WebSearchService] Firecrawl 初始化成功（旧版 SDK）")
                except Exception as e:
                    print(f"⚠️ [WebSearchService] Firecrawl 初始化失败: {e}")
            except Exception as e:
                print(f"⚠️ [WebSearchService] Firecrawl 初始化失败: {e}")
        
        print(f"🔍 [WebSearchService] 初始化完成 - enabled: {self.enabled}")

    @property
    def enabled(self) -> bool:
        """检查是否有任何搜索源可用"""
        return self.tavily_enabled or self.firecrawl_enabled

    async def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        timeout: Optional[float] = None,
        use_tavily: bool = True,
        use_firecrawl: bool = True,
        firecrawl_scrape_content: bool = False
    ) -> WebSearchResponse:
        """
        执行联网搜索

        Args:
            query: 搜索查询
            max_results: 每个源的最大结果数
            timeout: 超时时间（秒）
            use_tavily: 是否使用 Tavily 搜索
            use_firecrawl: 是否使用 Firecrawl 搜索
            firecrawl_scrape_content: Firecrawl 是否抓取页面内容（一体化模式）

        Returns:
            WebSearchResponse: 包含搜索结果和元数据
        """
        if max_results is None:
            max_results = settings.web_search_max_results
        if timeout is None:
            timeout = settings.web_search_timeout

        start_time = time.time()
        all_results: List[SearchResult] = []
        sources_used: List[str] = []
        errors: List[str] = []

        # 构建搜索任务（根据用户选择）
        tasks = []
        task_sources = []

        if self.tavily_enabled and use_tavily:
            tasks.append(self._tavily_search(query, max_results))
            task_sources.append("tavily")

        if self.firecrawl_enabled and use_firecrawl:
            tasks.append(self._firecrawl_search(query, max_results, firecrawl_scrape_content))
            task_sources.append("firecrawl")

        if not tasks:
            return WebSearchResponse(
                results=[],
                query=query,
                total_results=0,
                search_time_ms=0,
                sources_used=[],
                errors=["没有可用的搜索服务，请配置 Tavily 或 Firecrawl API 密钥"]
            )

        # 并行执行搜索，带超时控制
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout
            )

            for i, result in enumerate(results):
                source = task_sources[i]
                if isinstance(result, Exception):
                    errors.append(f"{source} 搜索失败: {str(result)}")
                elif isinstance(result, list):
                    all_results.extend(result)
                    sources_used.append(source)

        except asyncio.TimeoutError:
            errors.append(f"搜索超时（{timeout}秒）")
            # 超时时尝试获取已完成的结果
            for task in tasks:
                if hasattr(task, 'result') and not task.done():
                    task.cancel()

        # 合并去重
        merged_results = self._merge_and_dedupe(all_results)

        # 时效性排序
        if self._is_time_sensitive_query(query):
            merged_results = self._sort_by_recency(merged_results)

        search_time_ms = int((time.time() - start_time) * 1000)

        return WebSearchResponse(
            results=merged_results,
            query=query,
            total_results=len(merged_results),
            search_time_ms=search_time_ms,
            sources_used=sources_used,
            errors=errors
        )

    async def _tavily_search(self, query: str, max_results: int) -> List[SearchResult]:
        """Tavily 搜索"""
        if not self.tavily_client:
            return []

        try:
            # 清理查询：限制长度，移除可能导致问题的字符
            clean_query = query[:500].strip()
            # 移除可能导致 API 错误的特殊字符
            clean_query = re.sub(r'[<>{}|\[\]\\]', ' ', clean_query)
            
            # Tavily 是同步 API，在线程池中执行
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.tavily_client.search(
                    query=clean_query,
                    max_results=max_results,
                    include_answer=False
                )
            )

            results = []
            for item in response.get("results", []):
                results.append(SearchResult(
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    snippet=item.get("content", "")[:500],
                    source="tavily",
                    published_date=item.get("published_date"),
                    score=item.get("score", 0.0)
                ))
            return results

        except Exception as e:
            raise Exception(f"Tavily API 错误: {str(e)}")

    async def _firecrawl_search(self, query: str, max_results: int, scrape_content: bool = False) -> List[SearchResult]:
        """
        Firecrawl 搜索
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            scrape_content: 是否抓取页面内容（一体化模式，会消耗更多时间和积分）
        """
        if not self.firecrawl_client:
            return []

        try:
            # 清理查询：限制长度
            clean_query = query[:500].strip()
            
            # Firecrawl 是同步 API，在线程池中执行
            loop = asyncio.get_event_loop()
            
            # 检测是新版还是旧版 SDK
            is_new_sdk = hasattr(self.firecrawl_client, 'search') and not hasattr(self.firecrawl_client, 'scrape_url')
            
            if is_new_sdk:
                # 新版 SDK (Firecrawl 类)
                if scrape_content:
                    # 一体化模式：搜索 + 抓取内容
                    response = await loop.run_in_executor(
                        None,
                        lambda: self.firecrawl_client.search(
                            query=clean_query,
                            limit=max_results,
                            scrape_options={
                                "formats": ["markdown"],
                            }
                        )
                    )
                else:
                    # 仅搜索模式
                    response = await loop.run_in_executor(
                        None,
                        lambda: self.firecrawl_client.search(
                            query=clean_query,
                            limit=max_results
                        )
                    )
                
                results = []
                # 新版 SDK 返回对象，有 web 和 news 属性
                if hasattr(response, 'web') and response.web:
                    for item in response.web:
                        url = item.url if hasattr(item, 'url') else ''
                        title = item.title if hasattr(item, 'title') else 'No title'
                        description = item.description if hasattr(item, 'description') else ''
                        # 一体化模式下可能有 markdown 内容
                        markdown = item.markdown if hasattr(item, 'markdown') else ''
                        snippet = markdown[:500] if markdown else description[:500]
                        
                        results.append(SearchResult(
                            url=url,
                            title=title,
                            snippet=snippet,
                            source="firecrawl",
                            published_date=None,
                            score=0.0
                        ))
                
                if hasattr(response, 'news') and response.news:
                    for item in response.news:
                        url = item.url if hasattr(item, 'url') else ''
                        title = item.title if hasattr(item, 'title') else 'No title'
                        snippet = item.snippet if hasattr(item, 'snippet') else ''
                        date = item.date if hasattr(item, 'date') else None
                        
                        results.append(SearchResult(
                            url=url,
                            title=title,
                            snippet=snippet[:500],
                            source="firecrawl-news",
                            published_date=date,
                            score=0.0
                        ))
                
                # 如果有 data 属性（一体化模式返回）
                if hasattr(response, 'data') and response.data:
                    data = response.data if isinstance(response.data, list) else [response.data]
                    for item in data:
                        if isinstance(item, dict):
                            url = item.get('url', '')
                            title = item.get('title', 'No title')
                            markdown = item.get('markdown', '')
                            description = item.get('description', '')
                        else:
                            url = getattr(item, 'url', '')
                            title = getattr(item, 'title', 'No title')
                            markdown = getattr(item, 'markdown', '')
                            description = getattr(item, 'description', '')
                        
                        snippet = markdown[:500] if markdown else description[:500]
                        results.append(SearchResult(
                            url=url,
                            title=title,
                            snippet=snippet,
                            source="firecrawl-scrape",
                            published_date=None,
                            score=0.0
                        ))
                
                return results
            else:
                # 旧版 SDK (FirecrawlApp 类)
                response = await loop.run_in_executor(
                    None,
                    lambda: self.firecrawl_client.search(
                        query=clean_query,
                        params={"limit": max_results}
                    )
                )

                results = []
                items = response if isinstance(response, list) else response.get("data", [])

                for item in items:
                    results.append(SearchResult(
                        url=item.get("url", ""),
                        title=item.get("title", item.get("metadata", {}).get("title", "")),
                        snippet=item.get("description", item.get("markdown", ""))[:500],
                        source="firecrawl",
                        published_date=item.get("metadata", {}).get("publishedDate"),
                        score=item.get("score", 0.0)
                    ))
                return results

        except Exception as e:
            raise Exception(f"Firecrawl API 错误: {str(e)}")

    def _merge_and_dedupe(self, results: List[SearchResult]) -> List[SearchResult]:
        """合并去重搜索结果，按 URL 去重"""
        seen_urls = set()
        unique_results = []

        for result in results:
            # 标准化 URL（去除尾部斜杠和查询参数进行比较）
            normalized_url = result.url.rstrip("/").split("?")[0].lower()
            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                unique_results.append(result)

        return unique_results

    def _select_top_results(
        self,
        results: List[SearchResult],
        query: str,
        limit: int = 5
    ) -> List[SearchResult]:
        """基于相关性选择 top N 结果"""
        if len(results) <= limit:
            return results

        # 简单的相关性评分：基于标题和摘要中查询词的出现次数
        query_terms = set(query.lower().split())

        def relevance_score(result: SearchResult) -> float:
            text = f"{result.title} {result.snippet}".lower()
            matches = sum(1 for term in query_terms if term in text)
            # 结合原始分数和关键词匹配
            return result.score + matches * 0.1

        sorted_results = sorted(results, key=relevance_score, reverse=True)
        return sorted_results[:limit]

    def _is_time_sensitive_query(self, query: str) -> bool:
        """检测是否为时效性查询"""
        time_keywords = [
            "最新", "今天", "现在", "刚刚", "最近",
            "今日", "本周", "本月", "2024", "2025",
            "latest", "today", "now", "recent", "new"
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in time_keywords)

    def _sort_by_recency(self, results: List[SearchResult]) -> List[SearchResult]:
        """按时效性排序，有日期的优先"""
        def recency_key(result: SearchResult):
            if result.published_date:
                return (0, result.published_date)
            return (1, "")

        return sorted(results, key=recency_key)

    def format_context(self, results: List[SearchResult]) -> str:
        """格式化搜索结果为 LLM 上下文"""
        if not results:
            return ""

        lines = ["【联网搜索结果】", "以下是从互联网搜索到的相关信息，请基于这些信息回答用户问题。", ""]

        for i, result in enumerate(results, 1):
            # 限制摘要长度为 500 字符
            snippet = result.snippet[:500] if len(result.snippet) > 500 else result.snippet
            lines.append(f"[来源{i}] {result.title}")
            lines.append(f"URL: {result.url}")
            lines.append(f"内容: {snippet}")
            lines.append("")

        lines.append("请在回答中适当引用来源，使用 [来源X] 格式标注。")

        return "\n".join(lines)


# 创建全局实例
web_search_service = WebSearchService()
