"""
LangGraph 工具定义
定义 Agent 可以使用的工具函数
"""
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class WebSearchInput(BaseModel):
    """网络搜索输入参数"""
    query: str = Field(description="搜索查询关键词")
    max_results: int = Field(default=5, description="最大结果数量")


class KBQueryInput(BaseModel):
    """知识库查询输入参数"""
    query: str = Field(description="查询问题")
    mode: str = Field(default="mix", description="查询模式: naive, local, global, hybrid, mix")
    top_k: int = Field(default=5, description="返回结果数量")


@tool("web_search", args_schema=WebSearchInput)
async def web_search_tool(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    联网搜索工具 - 从互联网搜索相关信息
    当用户问题需要最新信息、实时数据或知识库中没有的内容时使用
    """
    from app.services.web_search_service import web_search_service
    
    if not web_search_service.enabled:
        return {
            "success": False,
            "error": "联网搜索服务未启用",
            "results": []
        }
    
    try:
        response = await web_search_service.search(
            query=query,
            max_results=max_results,
            use_tavily=True,
            use_firecrawl=True
        )
        
        # 筛选 top 结果
        top_results = web_search_service._select_top_results(
            response.results, query, limit=max_results
        )
        
        results = [
            {
                "url": r.url,
                "title": r.title,
                "snippet": r.snippet[:500] if len(r.snippet) > 500 else r.snippet,
                "source": r.source
            }
            for r in top_results
        ]
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "total": len(results)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": []
        }


@tool("knowledge_base_query", args_schema=KBQueryInput)
async def kb_query_tool(
    query: str,
    mode: str = "mix",
    top_k: int = 5,
    # 这些参数会在运行时通过 config 注入
    working_dir: str = "",
    kb_name: str = ""
) -> Dict[str, Any]:
    """
    知识库查询工具 - 从本地知识库检索相关信息
    当用户问题与已上传的文档、知识库内容相关时使用
    """
    from app.services.lightrag_service import lightrag_service
    
    if not working_dir:
        return {
            "success": False,
            "error": "未指定知识库",
            "context": "",
            "graph_data": {},
            "chunks": []
        }
    
    try:
        response = await lightrag_service.query_with_sources(
            working_dir=working_dir,
            query_text=query,
            mode=mode,
            top_k=top_k
        )
        
        return {
            "success": True,
            "kb_name": kb_name,
            "context": response.get('context', ''),
            "graph_data": response.get('graph_data', {}),
            "chunks": response.get('chunks', [])
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "context": "",
            "graph_data": {},
            "chunks": []
        }


def get_tools():
    """获取所有可用工具"""
    return [web_search_tool, kb_query_tool]


def format_web_search_context(results: List[Dict]) -> str:
    """格式化网络搜索结果为上下文"""
    if not results:
        return ""
    
    lines = [
        "【联网搜索结果】",
        "以下是从互联网搜索到的相关信息：",
        ""
    ]
    
    for i, r in enumerate(results, 1):
        lines.append(f"[来源{i}] {r.get('title', 'No title')}")
        lines.append(f"URL: {r.get('url', '')}")
        lines.append(f"内容: {r.get('snippet', '')}")
        lines.append("")
    
    lines.append("请在回答中适当引用来源，使用 [来源X] 格式标注。")
    return "\n".join(lines)


def format_kb_context(kb_name: str, chunks: List[Dict], graph_data: Dict) -> str:
    """格式化知识库检索结果为上下文"""
    if not chunks and not graph_data.get('entities'):
        return ""
    
    source_parts = []
    
    # 处理文档分片
    for idx, chunk in enumerate(chunks[:10], 1):
        content = chunk.get('content', '')
        if content and len(content) > 10:
            source_parts.append(f"[来源{idx}]\n{content[:600]}")
    
    # 如果没有分片，使用图谱实体描述
    if not source_parts and graph_data.get('entities'):
        for idx, entity in enumerate(graph_data['entities'][:5], 1):
            desc = entity.get('description', '')
            if desc:
                source_parts.append(f"[来源{idx}]\n{entity.get('name', '')}: {desc[:400]}")
    
    if not source_parts:
        return ""
    
    sources_text = "\n\n".join(source_parts)
    
    return f"""以下是从知识库「{kb_name}」中检索到的相关信息，每条信息都有编号标记：

{sources_text}

【重要】请基于以上知识库内容回答用户问题。在回答中引用知识库内容时，请在相关句子末尾添加引用标记，格式为 [1]、[2] 等，对应上面的来源编号。

如果知识库内容不足以回答问题，可以结合你的知识进行补充，但要明确说明哪些是来自知识库的信息（带引用标记），哪些是你的补充。"""
