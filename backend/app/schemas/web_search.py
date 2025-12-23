"""
联网搜索相关数据模型
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class SearchResult(BaseModel):
    """单个搜索结果"""
    url: str = Field(..., description="网页URL")
    title: str = Field(..., description="网页标题")
    snippet: str = Field(..., description="内容摘要")
    source: str = Field(..., description="来源: tavily 或 firecrawl")
    published_date: Optional[str] = Field(None, description="发布日期")
    score: float = Field(default=0.0, description="相关性分数")


class WebSearchResponse(BaseModel):
    """搜索响应"""
    results: List[SearchResult] = Field(default_factory=list, description="搜索结果列表")
    query: str = Field(..., description="搜索查询")
    total_results: int = Field(default=0, description="总结果数")
    search_time_ms: int = Field(default=0, description="搜索耗时(毫秒)")
    sources_used: List[str] = Field(default_factory=list, description="使用的搜索源")
    errors: List[str] = Field(default_factory=list, description="搜索过程中的错误")


class StreamEvent(BaseModel):
    """流式事件"""
    type: str = Field(..., description="事件类型: search_start, search_complete, content, done, error")
    content: Optional[str] = Field(None, description="内容(content类型时)")
    sources: Optional[List[dict]] = Field(None, description="来源列表(search_complete类型时)")
    error: Optional[str] = Field(None, description="错误信息(error类型时)")
