"""
LangGraph Agent 核心逻辑
实现基于状态图的对话 Agent
"""
import json
from typing import TypedDict, Annotated, Sequence, Optional, List, Dict, Any, AsyncGenerator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator

from app.ai.llm_manager import llm_manager
from app.ai.tools import (
    web_search_tool, kb_query_tool,
    format_web_search_context, format_kb_context
)


class AgentState(TypedDict):
    """Agent 状态定义"""
    # 消息历史
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # 用户原始问题
    user_query: str
    # 系统提示词
    system_prompt: str
    # 是否启用联网搜索
    enable_web_search: bool
    # 知识库配置
    kb_working_dir: Optional[str]
    kb_name: Optional[str]
    # 搜索结果
    web_search_results: List[Dict]
    # 知识库检索结果
    kb_results: Dict[str, Any]
    # 思考步骤（用于前端显示）
    thinking_steps: List[str]
    # 最终回复
    final_response: str
    # LLM 配置
    model: str
    api_key: Optional[str]
    base_url: Optional[str]


class ConversationAgent:
    """对话 Agent - 基于 LangGraph 实现"""
    
    def __init__(self):
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """构建状态图"""
        workflow = StateGraph(AgentState)
        
        # 添加节点
        workflow.add_node("analyze", self._analyze_node)
        workflow.add_node("web_search", self._web_search_node)
        workflow.add_node("kb_query", self._kb_query_node)
        workflow.add_node("generate", self._generate_node)
        
        # 设置入口
        workflow.set_entry_point("analyze")
        
        # 添加条件边
        workflow.add_conditional_edges(
            "analyze",
            self._route_after_analyze,
            {
                "web_search": "web_search",
                "kb_query": "kb_query",
                "generate": "generate"
            }
        )
        
        # web_search 后的路由
        workflow.add_conditional_edges(
            "web_search",
            self._route_after_web_search,
            {
                "kb_query": "kb_query",
                "generate": "generate"
            }
        )
        
        # kb_query 后直接生成
        workflow.add_edge("kb_query", "generate")
        
        # generate 结束
        workflow.add_edge("generate", END)
        
        return workflow.compile()
    
    async def _analyze_node(self, state: AgentState) -> Dict[str, Any]:
        """分析节点 - 分析用户问题，决定下一步"""
        thinking_steps = list(state.get("thinking_steps", []))
        thinking_steps.append("正在分析问题...")
        
        return {"thinking_steps": thinking_steps}
    
    def _route_after_analyze(self, state: AgentState) -> str:
        """分析后的路由决策"""
        # 如果启用了联网搜索，先执行搜索
        if state.get("enable_web_search"):
            return "web_search"
        # 如果有知识库，查询知识库
        if state.get("kb_working_dir"):
            return "kb_query"
        # 否则直接生成
        return "generate"
    
    async def _web_search_node(self, state: AgentState) -> Dict[str, Any]:
        """联网搜索节点"""
        thinking_steps = list(state.get("thinking_steps", []))
        thinking_steps.append("正在联网搜索...")
        
        try:
            result = await web_search_tool.ainvoke({
                "query": state["user_query"],
                "max_results": 5
            })
            
            if result.get("success") and result.get("results"):
                results = result["results"]
                thinking_steps.append(f"✓ 搜索完成，获取到 {len(results)} 条结果")
                return {
                    "web_search_results": results,
                    "thinking_steps": thinking_steps
                }
            else:
                error = result.get("error", "未找到相关结果")
                thinking_steps.append(f"⚠ 联网搜索：{error}")
                return {
                    "web_search_results": [],
                    "thinking_steps": thinking_steps
                }
        except Exception as e:
            thinking_steps.append(f"⚠ 搜索出错: {str(e)[:50]}")
            return {
                "web_search_results": [],
                "thinking_steps": thinking_steps
            }
    
    def _route_after_web_search(self, state: AgentState) -> str:
        """搜索后的路由决策"""
        if state.get("kb_working_dir"):
            return "kb_query"
        return "generate"
    
    async def _kb_query_node(self, state: AgentState) -> Dict[str, Any]:
        """知识库查询节点"""
        thinking_steps = list(state.get("thinking_steps", []))
        kb_name = state.get("kb_name", "知识库")
        thinking_steps.append(f"正在查询知识库「{kb_name}」...")
        
        try:
            # 直接调用 lightrag_service，因为 tool 需要额外参数
            from app.services.lightrag_service import lightrag_service
            
            response = await lightrag_service.query_with_sources(
                working_dir=state["kb_working_dir"],
                query_text=state["user_query"],
                mode="mix",
                top_k=5
            )
            
            graph_data = response.get('graph_data', {})
            chunks = response.get('chunks', [])
            
            entity_count = len(graph_data.get('entities', []))
            rel_count = len(graph_data.get('relationships', []))
            chunk_count = len(chunks)
            
            thinking_steps.append(
                f"✓ 检索到 {entity_count} 个实体、{rel_count} 个关系、{chunk_count} 个文档片段"
            )
            
            return {
                "kb_results": {
                    "kb_name": kb_name,
                    "context": response.get('context', ''),
                    "graph_data": graph_data,
                    "chunks": chunks
                },
                "thinking_steps": thinking_steps
            }
        except Exception as e:
            thinking_steps.append(f"⚠ 知识库查询出错: {str(e)[:50]}")
            return {
                "kb_results": {},
                "thinking_steps": thinking_steps
            }
    
    async def _generate_node(self, state: AgentState) -> Dict[str, Any]:
        """生成回复节点"""
        thinking_steps = list(state.get("thinking_steps", []))
        
        # 构建系统提示词
        system_prompt = state.get("system_prompt", "你是一个有帮助的AI助手。请用中文回答问题。")
        
        # 添加联网搜索上下文
        web_results = state.get("web_search_results", [])
        if web_results:
            web_context = format_web_search_context(web_results)
            system_prompt = f"{system_prompt}\n\n{web_context}"
        
        # 添加知识库上下文
        kb_results = state.get("kb_results", {})
        if kb_results and (kb_results.get("chunks") or kb_results.get("graph_data", {}).get("entities")):
            kb_context = format_kb_context(
                kb_results.get("kb_name", "知识库"),
                kb_results.get("chunks", []),
                kb_results.get("graph_data", {})
            )
            if kb_context:
                system_prompt = f"{system_prompt}\n\n{kb_context}"
        
        # 构建上下文信息
        context_info = []
        if kb_results:
            context_info.append("知识库内容")
        if web_results:
            context_info.append(f"{len(web_results)}个网络来源")
        
        if context_info:
            context_str = "、".join(context_info)
            thinking_steps.append(f"已整合上下文：{context_str}")
        
        model = state.get("model", "deepseek-chat")
        thinking_steps.append(f"正在使用 {model} 生成回答...")
        
        # 构建消息
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加历史消息
        for msg in state.get("messages", []):
            if isinstance(msg, HumanMessage):
                messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                messages.append({"role": "assistant", "content": msg.content})
        
        # 添加当前问题
        messages.append({"role": "user", "content": state["user_query"]})
        
        # 调用 LLM（非流式，用于获取完整回复）
        try:
            response = await llm_manager.chat_completion(
                messages=messages,
                model=model,
                api_key=state.get("api_key"),
                base_url=state.get("base_url"),
                stream=False
            )
            
            final_response = response.choices[0].message.content
            
            return {
                "final_response": final_response,
                "thinking_steps": thinking_steps
            }
        except Exception as e:
            return {
                "final_response": f"生成回复时出错: {str(e)}",
                "thinking_steps": thinking_steps
            }
    
    async def _extract_search_query(
        self,
        user_query: str,
        history_messages: List[Dict[str, str]] = None,
        model: str = "deepseek-chat",
        api_key: str = None,
        base_url: str = None
    ) -> str:
        """
        使用 AI 分析用户问题和历史对话，提取最佳搜索关键词
        
        Args:
            user_query: 用户当前问题
            history_messages: 历史对话消息
            model: 模型名称
            api_key: API Key
            base_url: API Base URL
            
        Returns:
            优化后的搜索关键词
        """
        # 构建历史对话上下文
        context = ""
        if history_messages and len(history_messages) > 0:
            # 只取最近的几轮对话
            recent_messages = history_messages[-6:]  # 最近3轮对话
            context_parts = []
            for msg in recent_messages:
                role = "用户" if msg.get("role") == "user" else "AI"
                content = msg.get("content", "")[:200]  # 截断过长内容
                context_parts.append(f"{role}: {content}")
            context = "\n".join(context_parts)
        
        # 构建提示词
        prompt = f"""请根据用户的问题和对话历史，提取最适合用于网络搜索的关键词。

要求：
1. 关键词应该简洁、精准，适合搜索引擎
2. 如果问题中有指代词（如"它"、"这个"），请根据上下文替换为具体内容
3. 只返回搜索关键词，不要其他解释
4. 关键词长度控制在50字以内

{"对话历史：" + chr(10) + context + chr(10) if context else ""}
用户当前问题：{user_query}

搜索关键词："""

        try:
            response = await llm_manager.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                api_key=api_key,
                base_url=base_url,
                max_tokens=100,
                temperature=0.3
            )
            
            search_query = response.choices[0].message.content.strip()
            # 清理可能的引号和多余空格
            search_query = search_query.strip('"\'').strip()
            
            # 如果提取失败或结果太长，使用原始问题
            if not search_query or len(search_query) > 100:
                return user_query
            
            return search_query
        except Exception as e:
            print(f"⚠️ 提取搜索关键词失败: {e}")
            return user_query
    
    async def run(
        self,
        user_query: str,
        history_messages: List[Dict[str, str]] = None,
        enable_web_search: bool = False,
        kb_working_dir: str = None,
        kb_name: str = None,
        model: str = "deepseek-chat",
        api_key: str = None,
        base_url: str = None,
        system_prompt: str = None
    ) -> Dict[str, Any]:
        """
        运行 Agent（非流式）
        
        Returns:
            {
                "response": str,
                "thinking_steps": List[str],
                "web_sources": List[Dict],
                "kb_sources": Dict
            }
        """
        # 转换历史消息
        messages = []
        if history_messages:
            for msg in history_messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
        
        # 初始状态
        initial_state: AgentState = {
            "messages": messages,
            "user_query": user_query,
            "system_prompt": system_prompt or "你是一个有帮助的AI助手。请用中文回答问题。",
            "enable_web_search": enable_web_search,
            "kb_working_dir": kb_working_dir,
            "kb_name": kb_name,
            "web_search_results": [],
            "kb_results": {},
            "thinking_steps": [],
            "final_response": "",
            "model": model,
            "api_key": api_key,
            "base_url": base_url
        }
        
        # 运行图
        final_state = await self.graph.ainvoke(initial_state)
        
        # 构建返回结果
        result = {
            "response": final_state.get("final_response", ""),
            "thinking_steps": final_state.get("thinking_steps", []),
            "web_sources": [],
            "kb_sources": None
        }
        
        # 处理网络搜索来源
        web_results = final_state.get("web_search_results", [])
        if web_results:
            result["web_sources"] = [
                {
                    "url": r.get("url", ""),
                    "title": r.get("title", ""),
                    "snippet": r.get("snippet", "")[:200]
                }
                for r in web_results
            ]
        
        # 处理知识库来源
        kb_results = final_state.get("kb_results", {})
        if kb_results:
            result["kb_sources"] = {
                "kb_name": kb_results.get("kb_name", ""),
                "graph_data": kb_results.get("graph_data", {}),
                "chunks": [
                    {"index": idx + 1, "content": c.get("content", "")}
                    for idx, c in enumerate(kb_results.get("chunks", [])[:10])
                ]
            }
        
        return result


    async def run_stream(
        self,
        user_query: str,
        history_messages: List[Dict[str, str]] = None,
        enable_web_search: bool = False,
        kb_working_dir: str = None,
        kb_name: str = None,
        model: str = "deepseek-chat",
        api_key: str = None,
        base_url: str = None,
        system_prompt: str = None,
        max_context_tokens: int = 16000,
        db = None,  # 数据库会话（用于获取长期记忆）
        user_id: str = None,  # 用户 ID（用于获取长期记忆）
        memory_top_k: int = 5,  # 普通记忆检索数量
        core_memory_threshold: int = 80  # 核心记忆优先级阈值
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式运行 Agent
        
        Args:
            max_context_tokens: 最大上下文 token 数，超过时自动压缩旧消息
            db: 数据库会话（用于获取长期记忆）
            user_id: 用户 ID（用于获取长期记忆）
            memory_top_k: 普通记忆检索数量（用户可配置）
            core_memory_threshold: 核心记忆优先级阈值（用户可配置）
        
        Yields:
            事件字典，包含 type 和相关数据
            - {"type": "thinking_step", "step": str}
            - {"type": "search_start"}
            - {"type": "search_complete", "sources": List}
            - {"type": "kb_sources", "sources": Dict}
            - {"type": "content", "content": str}
            - {"type": "context_info", "info": Dict}
            - {"type": "done", "model": str, "sources": Dict}
        """
        from app.ai.context_manager import context_manager
        
        # 转换历史消息
        messages = []
        if history_messages:
            for msg in history_messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
        
        thinking_steps = []
        web_sources = []
        kb_sources = None
        
        # Step 1: 分析问题
        thinking_steps.append("正在分析问题...")
        yield {"type": "thinking_step", "step": "正在分析问题..."}
        
        # Step 2: 联网搜索（如果启用）
        if enable_web_search:
            yield {"type": "search_start"}
            
            # 使用 AI 分析历史对话，提取搜索关键词
            search_query = await self._extract_search_query(
                user_query=user_query,
                history_messages=history_messages,
                model=model,
                api_key=api_key,
                base_url=base_url
            )
            
            step = f"正在搜索: {search_query}"
            thinking_steps.append(step)
            yield {"type": "thinking_step", "step": step}
            
            try:
                from app.services.web_search_service import web_search_service
                
                if web_search_service.enabled:
                    response = await web_search_service.search(
                        query=search_query,
                        max_results=5,
                        use_tavily=True,
                        use_firecrawl=True
                    )
                    
                    if response.results:
                        top_results = web_search_service._select_top_results(
                            response.results, user_query, limit=5
                        )
                        
                        step = f"✓ 搜索完成，获取到 {len(top_results)} 条结果"
                        thinking_steps.append(step)
                        yield {"type": "thinking_step", "step": step}
                        
                        web_sources = [
                            {
                                "url": r.url,
                                "title": r.title,
                                "snippet": r.snippet[:200] if len(r.snippet) > 200 else r.snippet
                            }
                            for r in top_results
                        ]
                        
                        yield {"type": "search_complete", "sources": web_sources}
                    else:
                        error_msg = response.errors[0] if response.errors else "未找到相关结果"
                        step = f"⚠ 联网搜索：{error_msg}"
                        thinking_steps.append(step)
                        yield {"type": "thinking_step", "step": step}
                        yield {"type": "search_complete", "sources": []}
                else:
                    step = "⚠ 联网搜索服务未启用"
                    thinking_steps.append(step)
                    yield {"type": "thinking_step", "step": step}
                    yield {"type": "search_complete", "sources": []}
                    
            except Exception as e:
                step = f"⚠ 搜索出错: {str(e)[:50]}"
                thinking_steps.append(step)
                yield {"type": "thinking_step", "step": step}
                yield {"type": "search_error", "error": str(e)}
        
        # Step 3: 知识库查询（如果有）
        if kb_working_dir:
            step = f"正在查询知识库「{kb_name or '知识库'}」..."
            thinking_steps.append(step)
            yield {"type": "thinking_step", "step": step}
            
            try:
                from app.services.lightrag_service import lightrag_service
                
                response = await lightrag_service.query_with_sources(
                    working_dir=kb_working_dir,
                    query_text=user_query,
                    mode="mix",
                    top_k=5
                )
                
                graph_data = response.get('graph_data', {})
                chunks = response.get('chunks', [])
                
                entity_count = len(graph_data.get('entities', []))
                rel_count = len(graph_data.get('relationships', []))
                chunk_count = len(chunks)
                
                step = f"✓ 检索到 {entity_count} 个实体、{rel_count} 个关系、{chunk_count} 个文档片段"
                thinking_steps.append(step)
                yield {"type": "thinking_step", "step": step}
                
                kb_sources = {
                    "kb_name": kb_name or "知识库",
                    "graph_data": graph_data,
                    "chunks": [
                        {"index": idx + 1, "content": c.get("content", "")}
                        for idx, c in enumerate(chunks[:10])
                    ]
                }
                
                yield {"type": "kb_sources", "sources": kb_sources}
                
            except Exception as e:
                step = f"⚠ 知识库查询出错: {str(e)[:50]}"
                thinking_steps.append(step)
                yield {"type": "thinking_step", "step": step}
        
        # Step 4: 构建上下文并生成回复
        final_system_prompt = system_prompt or "你是一个有帮助的AI助手。请用中文回答问题。"
        
        # 添加联网搜索上下文
        if web_sources:
            web_context = format_web_search_context([
                {"title": s["title"], "url": s["url"], "snippet": s["snippet"]}
                for s in web_sources
            ])
            final_system_prompt = f"{final_system_prompt}\n\n{web_context}"
        
        # 添加知识库上下文
        if kb_sources and (kb_sources.get("chunks") or kb_sources.get("graph_data", {}).get("entities")):
            kb_context = format_kb_context(
                kb_sources.get("kb_name", "知识库"),
                kb_sources.get("chunks", []),
                kb_sources.get("graph_data", {})
            )
            if kb_context:
                final_system_prompt = f"{final_system_prompt}\n\n{kb_context}"
        
        # 构建上下文信息提示
        context_info = []
        if kb_sources:
            context_info.append("知识库内容")
        if web_sources:
            context_info.append(f"{len(web_sources)}个网络来源")
        if history_messages and len(history_messages) > 0:
            context_info.append(f"{len(history_messages)}条历史对话")
        
        if context_info:
            context_str = "、".join(context_info)
            step = f"已整合上下文：{context_str}"
            thinking_steps.append(step)
            yield {"type": "thinking_step", "step": step}
        
        step = f"正在使用 {model} 生成回答..."
        thinking_steps.append(step)
        yield {"type": "thinking_step", "step": step}
        
        # 使用上下文管理器构建消息列表（自动处理 token 限制、压缩和长期记忆）
        context_result = await context_manager.build_context(
            system_prompt=final_system_prompt,
            history_messages=history_messages or [],
            current_query=user_query,
            max_tokens=max_context_tokens,
            model=model,
            api_key=api_key,
            base_url=base_url,
            db=db,
            user_id=user_id,
            memory_top_k=memory_top_k,
            core_memory_threshold=core_memory_threshold
        )
        
        llm_messages = context_result["messages"]
        
        # 发送上下文信息
        context_info_data = {
            "total_tokens": context_result["total_tokens"],
            "compressed": context_result["compressed"],
            "original_count": context_result["original_count"],
            "final_count": context_result["final_count"],
            "long_term_memory_included": context_result.get("long_term_memory_included", False)
        }
        yield {"type": "context_info", "info": context_info_data}
        
        # 如果包含长期记忆，添加思考步骤并发送记忆详情
        if context_result.get("long_term_memory_included"):
            memories = context_result.get("long_term_memories", [])
            core_count = context_result.get("core_memory_count", 0)
            normal_count = context_result.get("normal_memory_count", 0)
            step = f"📚 已加载用户长期记忆（核心记忆 {core_count} 条 + 相关记忆 {normal_count} 条）"
            thinking_steps.append(step)
            yield {"type": "thinking_step", "step": step}
            # 发送长时记忆来源
            yield {"type": "memory_sources", "memories": memories}
        
        # 如果进行了压缩，添加思考步骤
        if context_result["compressed"]:
            step = f"📝 历史消息已压缩（{context_result['original_count']}条→{context_result['final_count']}条摘要）"
            thinking_steps.append(step)
            yield {"type": "thinking_step", "step": step}
        
        # 流式生成回复
        try:
            async for chunk in llm_manager.chat_completion_stream(
                messages=llm_messages,
                model=model,
                api_key=api_key,
                base_url=base_url
            ):
                yield {"type": "content", "content": chunk}
        except Exception as e:
            yield {"type": "error", "error": str(e)}
            return
        
        # 完成
        done_data = {"type": "done", "model": model}
        if kb_sources:
            done_data["sources"] = kb_sources
        yield done_data


# 创建全局 Agent 实例
conversation_agent = ConversationAgent()
