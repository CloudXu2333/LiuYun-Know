"""
LangGraph Agent 核心逻辑
实现基于状态图的对话 Agent，支持流式输出、MCP 工具调用、联网搜索和知识库查询
"""
import json
import re
from typing import TypedDict, Annotated, Sequence, Optional, List, Dict, Any, AsyncGenerator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
import operator
import asyncio

from app.ai.llm_manager import llm_manager
from app.ai.tools import (
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
    # 上下文管理配置
    max_context_tokens: int
    db: Any  # 数据库会话
    user_id: Optional[str]
    memory_top_k: int
    core_memory_threshold: int
    # 流式输出队列
    stream_queue: Optional[asyncio.Queue]
    # MCP 工具相关
    mcp_tool_ids: List[str]  # 启用的 MCP 工具 ID 列表
    mcp_tools_loaded: bool  # MCP 工具是否已加载
    mcp_tools: List[Any]  # 已加载的 MCP 工具
    tool_calls: List[Dict[str, Any]]  # 待执行的工具调用
    tool_results: List[Dict[str, Any]]  # 工具调用结果
    mcp_iteration: int  # MCP 工具调用迭代次数
    max_mcp_iterations: int  # 最大 MCP 迭代次数


class ConversationAgent:
    """
    对话 Agent - 基于 LangGraph 实现
    支持联网搜索、知识库查询、MCP 工具调用
    """
    
    def __init__(self):
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """构建状态图"""
        workflow = StateGraph(AgentState)
        
        # 添加节点
        workflow.add_node("analyze", self._analyze_node)
        workflow.add_node("web_search", self._web_search_node)
        workflow.add_node("kb_query", self._kb_query_node)
        workflow.add_node("mcp_think", self._mcp_think_node)
        workflow.add_node("mcp_act", self._mcp_act_node)
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
                "mcp_think": "mcp_think",
                "generate": "generate"
            }
        )
        
        # web_search 后的路由
        workflow.add_conditional_edges(
            "web_search",
            self._route_after_web_search,
            {
                "kb_query": "kb_query",
                "mcp_think": "mcp_think",
                "generate": "generate"
            }
        )
        
        # kb_query 后的路由
        workflow.add_conditional_edges(
            "kb_query",
            self._route_after_kb_query,
            {
                "mcp_think": "mcp_think",
                "generate": "generate"
            }
        )
        
        # MCP 思考后的路由
        workflow.add_conditional_edges(
            "mcp_think",
            self._route_after_mcp_think,
            {
                "mcp_act": "mcp_act",
                "generate": "generate"
            }
        )
        
        # MCP 执行后回到思考
        workflow.add_edge("mcp_act", "mcp_think")
        
        # generate 结束
        workflow.add_edge("generate", END)
        
        return workflow.compile()

    async def _analyze_node(self, state: AgentState) -> Dict[str, Any]:
        """分析节点 - 分析用户问题，决定下一步"""
        thinking_steps = list(state.get("thinking_steps", []))
        thinking_steps.append("正在分析问题...")
        
        if state.get("stream_queue"):
            await state["stream_queue"].put({
                "type": "thinking_step",
                "step": "正在分析问题..."
            })
        
        return {"thinking_steps": thinking_steps}
    
    def _route_after_analyze(self, state: AgentState) -> str:
        """分析后的路由决策"""
        # 如果启用了联网搜索，先执行搜索
        if state.get("enable_web_search"):
            return "web_search"
        # 如果有知识库，查询知识库
        if state.get("kb_working_dir"):
            return "kb_query"
        # 如果有 MCP 工具，进入 MCP 思考
        if state.get("mcp_tool_ids"):
            return "mcp_think"
        # 否则直接生成
        return "generate"
    
    async def _web_search_node(self, state: AgentState) -> Dict[str, Any]:
        """联网搜索节点"""
        thinking_steps = list(state.get("thinking_steps", []))
        stream_queue = state.get("stream_queue")
        
        if stream_queue:
            await stream_queue.put({"type": "search_start"})
        
        # 使用 AI 分析历史对话，提取搜索关键词
        history_messages = []
        for msg in state.get("messages", []):
            if isinstance(msg, HumanMessage):
                history_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history_messages.append({"role": "assistant", "content": msg.content})
        
        search_query = await self._extract_search_query(
            user_query=state["user_query"],
            history_messages=history_messages,
            model=state.get("model", "deepseek-chat"),
            api_key=state.get("api_key"),
            base_url=state.get("base_url")
        )
        
        step = f"正在搜索: {search_query}"
        thinking_steps.append(step)
        if stream_queue:
            await stream_queue.put({"type": "thinking_step", "step": step})
        
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
                        response.results, state["user_query"], limit=5
                    )
                    
                    results = [
                        {
                            "url": r.url,
                            "title": r.title,
                            "snippet": r.snippet[:200] if len(r.snippet) > 200 else r.snippet
                        }
                        for r in top_results
                    ]
                    
                    step = f"✓ 搜索完成，获取到 {len(results)} 条结果"
                    thinking_steps.append(step)
                    if stream_queue:
                        await stream_queue.put({"type": "thinking_step", "step": step})
                        await stream_queue.put({"type": "search_complete", "sources": results})
                    
                    return {"web_search_results": results, "thinking_steps": thinking_steps}
                else:
                    error = response.errors[0] if response.errors else "未找到相关结果"
                    step = f"⚠ 联网搜索：{error}"
                    thinking_steps.append(step)
                    if stream_queue:
                        await stream_queue.put({"type": "thinking_step", "step": step})
                        await stream_queue.put({"type": "search_complete", "sources": []})
                    return {"web_search_results": [], "thinking_steps": thinking_steps}
            else:
                step = "⚠ 联网搜索服务未启用"
                thinking_steps.append(step)
                if stream_queue:
                    await stream_queue.put({"type": "thinking_step", "step": step})
                    await stream_queue.put({"type": "search_complete", "sources": []})
                return {"web_search_results": [], "thinking_steps": thinking_steps}
        except Exception as e:
            step = f"⚠ 搜索出错: {str(e)[:50]}"
            thinking_steps.append(step)
            if stream_queue:
                await stream_queue.put({"type": "thinking_step", "step": step})
                await stream_queue.put({"type": "search_error", "error": str(e)})
            return {"web_search_results": [], "thinking_steps": thinking_steps}

    def _route_after_web_search(self, state: AgentState) -> str:
        """搜索后的路由决策"""
        if state.get("kb_working_dir"):
            return "kb_query"
        if state.get("mcp_tool_ids"):
            return "mcp_think"
        return "generate"
    
    async def _kb_query_node(self, state: AgentState) -> Dict[str, Any]:
        """知识库查询节点"""
        thinking_steps = list(state.get("thinking_steps", []))
        kb_name = state.get("kb_name", "知识库")
        stream_queue = state.get("stream_queue")
        
        step = f"正在查询知识库「{kb_name}」..."
        thinking_steps.append(step)
        if stream_queue:
            await stream_queue.put({"type": "thinking_step", "step": step})
        
        try:
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
            
            step = f"✓ 检索到 {entity_count} 个实体、{rel_count} 个关系、{chunk_count} 个文档片段"
            thinking_steps.append(step)
            if stream_queue:
                await stream_queue.put({"type": "thinking_step", "step": step})
            
            kb_results = {
                "kb_name": kb_name,
                "context": response.get('context', ''),
                "graph_data": graph_data,
                "chunks": chunks
            }
            
            if stream_queue:
                kb_sources = {
                    "kb_name": kb_name,
                    "graph_data": graph_data,
                    "chunks": [
                        {"index": idx + 1, "content": c.get("content", "")}
                        for idx, c in enumerate(chunks[:10])
                    ]
                }
                await stream_queue.put({"type": "kb_sources", "sources": kb_sources})
            
            return {"kb_results": kb_results, "thinking_steps": thinking_steps}
        except Exception as e:
            step = f"⚠ 知识库查询出错: {str(e)[:50]}"
            thinking_steps.append(step)
            if stream_queue:
                await stream_queue.put({"type": "thinking_step", "step": step})
            return {"kb_results": {}, "thinking_steps": thinking_steps}
    
    def _route_after_kb_query(self, state: AgentState) -> str:
        """知识库查询后的路由决策"""
        if state.get("mcp_tool_ids"):
            return "mcp_think"
        return "generate"

    async def _mcp_think_node(self, state: AgentState) -> Dict[str, Any]:
        """MCP 思考节点 - 决定是否需要调用工具"""
        thinking_steps = list(state.get("thinking_steps", []))
        stream_queue = state.get("stream_queue")
        mcp_iteration = state.get("mcp_iteration", 0) + 1
        max_iterations = state.get("max_mcp_iterations", 10)
        
        # 检查迭代次数
        if mcp_iteration > max_iterations:
            step = "⚠️ 达到最大迭代次数，停止工具调用"
            thinking_steps.append(step)
            if stream_queue:
                await stream_queue.put({"type": "thinking_step", "step": step})
            return {
                "thinking_steps": thinking_steps,
                "mcp_iteration": mcp_iteration,
                "tool_calls": []
            }
        
        # 加载 MCP 工具
        tools = state.get("mcp_tools", [])
        from app.ai.mcp_adapter import get_mcp_tools_from_db, mcp_tool_manager
        
        if state.get("mcp_tool_ids") and not state.get("mcp_tools_loaded"):
            step = "🔧 正在加载 MCP 工具..."
            thinking_steps.append(step)
            if stream_queue:
                await stream_queue.put({"type": "thinking_step", "step": step})
            
            try:
                tools = await get_mcp_tools_from_db(
                    db=state.get("db"),
                    user_id=state.get("user_id"),
                    tool_ids=state.get("mcp_tool_ids")
                )
                step = f"✓ 已加载 {len(tools)} 个 MCP 工具"
                thinking_steps.append(step)
                if stream_queue:
                    await stream_queue.put({"type": "thinking_step", "step": step})
                    await stream_queue.put({
                        "type": "mcp_tools_loaded",
                        "tools": [{"name": t.name, "description": t.description} for t in tools]
                    })
            except Exception as e:
                step = f"⚠️ 加载 MCP 工具失败: {str(e)[:50]}"
                thinking_steps.append(step)
                if stream_queue:
                    await stream_queue.put({"type": "thinking_step", "step": step})
                return {
                    "thinking_steps": thinking_steps,
                    "mcp_tools_loaded": True,
                    "mcp_tools": [],
                    "mcp_iteration": mcp_iteration,
                    "tool_calls": []
                }
        else:
            tools = await mcp_tool_manager.get_tools_for_ids(state.get("mcp_tool_ids", []))
        
        if not tools:
            return {
                "thinking_steps": thinking_steps,
                "mcp_tools_loaded": True,
                "mcp_tools": [],
                "mcp_iteration": mcp_iteration,
                "tool_calls": []
            }
        
        # 构建工具描述
        tool_desc_parts = [f"- {t.name}: {t.description}" for t in tools]
        tool_descriptions = "\n".join(tool_desc_parts)
        
        # 构建消息
        messages = list(state.get("messages", []))
        
        # 添加工具结果到消息
        tool_results = state.get("tool_results", [])
        if tool_results:
            for result in tool_results[-5:]:
                messages.append(AIMessage(content=f"工具调用: {result.get('tool_name', 'unknown')}"))
                messages.append(HumanMessage(content=f"工具结果:\n{result.get('result', '')}"))
        
        # 构建系统提示
        system_prompt = state.get("system_prompt", "你是一个有帮助的AI助手。")
        system_prompt += f"""

你可以使用以下工具来帮助回答问题：
{tool_descriptions}

如果需要使用工具，请按以下 JSON 格式回复：
{{"tool_call": {{"name": "工具名称", "arguments": {{"参数名": "参数值"}}}}}}

如果不需要使用工具，直接回答用户问题即可。
注意：每次只能调用一个工具。"""
        
        # 调用 LLM
        llm_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            if isinstance(msg, HumanMessage):
                llm_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                llm_messages.append({"role": "assistant", "content": msg.content})
        
        llm_messages.append({"role": "user", "content": state["user_query"]})
        
        try:
            response = await llm_manager.chat_completion(
                messages=llm_messages,
                model=state.get("model", "deepseek-chat"),
                api_key=state.get("api_key"),
                base_url=state.get("base_url"),
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            tool_call = self._parse_tool_call(content)
            
            if tool_call:
                step = f"🔧 准备调用工具: {tool_call['name']}"
                thinking_steps.append(step)
                if stream_queue:
                    await stream_queue.put({"type": "thinking_step", "step": step})
                
                return {
                    "thinking_steps": thinking_steps,
                    "mcp_iteration": mcp_iteration,
                    "mcp_tools_loaded": True,
                    "mcp_tools": tools,
                    "tool_calls": [tool_call],
                    "final_response": ""
                }
            else:
                # 不需要调用工具，让 _generate_node 处理生成（保留完整上下文）
                return {
                    "thinking_steps": thinking_steps,
                    "mcp_iteration": mcp_iteration,
                    "mcp_tools_loaded": True,
                    "mcp_tools": tools,
                    "final_response": "",  # 不在这里生成，让 generate 节点处理
                    "tool_calls": []
                }
                
        except Exception as e:
            step = f"⚠️ LLM 调用失败: {str(e)[:50]}"
            thinking_steps.append(step)
            if stream_queue:
                await stream_queue.put({"type": "thinking_step", "step": step})
            return {
                "thinking_steps": thinking_steps,
                "mcp_iteration": mcp_iteration,
                "mcp_tools_loaded": True,
                "mcp_tools": tools,
                "tool_calls": [],
                "final_response": f"抱歉，处理请求时出错: {str(e)}"
            }

    def _parse_tool_call(self, content: str) -> Optional[Dict[str, Any]]:
        """解析 LLM 输出中的工具调用"""
        # 尝试直接解析整个内容为 JSON
        try:
            data = json.loads(content.strip())
            if "tool_call" in data:
                tool_call = data["tool_call"]
                if "name" in tool_call:
                    return {
                        "name": tool_call["name"],
                        "arguments": tool_call.get("arguments", {})
                    }
        except json.JSONDecodeError:
            pass
        
        # 尝试从内容中提取 JSON
        # 查找 {"tool_call": ...} 模式
        start_idx = content.find('{"tool_call"')
        if start_idx != -1:
            # 找到匹配的结束括号
            brace_count = 0
            end_idx = start_idx
            for i, char in enumerate(content[start_idx:], start_idx):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            if end_idx > start_idx:
                try:
                    json_str = content[start_idx:end_idx]
                    data = json.loads(json_str)
                    if "tool_call" in data:
                        tool_call = data["tool_call"]
                        if "name" in tool_call:
                            return {
                                "name": tool_call["name"],
                                "arguments": tool_call.get("arguments", {})
                            }
                except json.JSONDecodeError:
                    pass
        
        # 尝试匹配 ```json ... ``` 代码块
        json_block_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
        if json_block_match:
            try:
                data = json.loads(json_block_match.group(1))
                if "tool_call" in data:
                    tool_call = data["tool_call"]
                    if "name" in tool_call:
                        return {
                            "name": tool_call["name"],
                            "arguments": tool_call.get("arguments", {})
                        }
                elif "name" in data:
                    return {
                        "name": data["name"],
                        "arguments": data.get("arguments", {})
                    }
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _route_after_mcp_think(self, state: AgentState) -> str:
        """MCP 思考后的路由决策"""
        if state.get("tool_calls"):
            return "mcp_act"
        return "generate"
    
    async def _mcp_act_node(self, state: AgentState) -> Dict[str, Any]:
        """MCP 执行节点 - 调用 MCP 工具"""
        thinking_steps = list(state.get("thinking_steps", []))
        tool_results = list(state.get("tool_results", []))
        stream_queue = state.get("stream_queue")
        
        tool_calls = state.get("tool_calls", [])
        if not tool_calls:
            return {"thinking_steps": thinking_steps, "tool_results": tool_results}
        
        # 获取工具
        from app.ai.mcp_adapter import mcp_tool_manager
        tools = state.get("mcp_tools", [])
        if not tools:
            tools = await mcp_tool_manager.get_tools_for_ids(state.get("mcp_tool_ids", []))
        tool_map = {t.name: t for t in tools}
        
        for call in tool_calls:
            tool_name = call.get("name", "")
            arguments = call.get("arguments", {})
            
            step = f"⚡ 执行工具: {tool_name}"
            thinking_steps.append(step)
            if stream_queue:
                await stream_queue.put({"type": "thinking_step", "step": step})
                await stream_queue.put({
                    "type": "tool_call_start",
                    "tool_name": tool_name,
                    "arguments": arguments
                })
            
            tool = tool_map.get(tool_name)
            if tool:
                try:
                    result = await tool._arun(**arguments)
                    
                    step = f"✓ 工具 {tool_name} 执行完成"
                    thinking_steps.append(step)
                    if stream_queue:
                        await stream_queue.put({"type": "thinking_step", "step": step})
                        await stream_queue.put({
                            "type": "tool_call_result",
                            "tool_name": tool_name,
                            "result": result[:500] if len(result) > 500 else result
                        })
                    
                    tool_results.append({
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "result": result
                    })
                except Exception as e:
                    error_msg = f"工具执行失败: {str(e)}"
                    step = f"⚠️ {error_msg}"
                    thinking_steps.append(step)
                    if stream_queue:
                        await stream_queue.put({"type": "thinking_step", "step": step})
                    
                    tool_results.append({
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "result": error_msg,
                        "error": True
                    })
            else:
                error_msg = f"工具 {tool_name} 不存在"
                step = f"⚠️ {error_msg}"
                thinking_steps.append(step)
                if stream_queue:
                    await stream_queue.put({"type": "thinking_step", "step": step})
                
                tool_results.append({
                    "tool_name": tool_name,
                    "result": error_msg,
                    "error": True
                })
        
        return {
            "thinking_steps": thinking_steps,
            "tool_results": tool_results,
            "tool_calls": []
        }

    async def _generate_node(self, state: AgentState) -> Dict[str, Any]:
        """生成回复节点 - 支持流式输出"""
        thinking_steps = list(state.get("thinking_steps", []))
        stream_queue = state.get("stream_queue")
        
        # 如果有 MCP 工具结果，基于结果生成回复
        tool_results = state.get("tool_results", [])
        if tool_results and state.get("mcp_tools_loaded"):
            return await self._generate_from_tool_results(state, thinking_steps, tool_results)
        
        # 构建系统提示词
        system_prompt = state.get("system_prompt", "你是一个有帮助的AI助手。请用中文回答问题。")
        
        # 添加联网搜索上下文
        web_results = state.get("web_search_results", [])
        if web_results:
            web_context = format_web_search_context([
                {"title": s["title"], "url": s["url"], "snippet": s["snippet"]}
                for s in web_results
            ])
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
        
        history_messages = []
        for msg in state.get("messages", []):
            if isinstance(msg, HumanMessage):
                history_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history_messages.append({"role": "assistant", "content": msg.content})
        
        if history_messages:
            context_info.append(f"{len(history_messages)}条历史对话")
        
        if context_info:
            context_str = "、".join(context_info)
            step = f"已整合上下文：{context_str}"
            thinking_steps.append(step)
            if stream_queue:
                await stream_queue.put({"type": "thinking_step", "step": step})
        
        model = state.get("model", "deepseek-chat")
        step = f"正在使用 {model} 生成回答..."
        thinking_steps.append(step)
        if stream_queue:
            await stream_queue.put({"type": "thinking_step", "step": step})
        
        # 使用上下文管理器构建消息列表
        from app.ai.context_manager import context_manager
        
        context_result = await context_manager.build_context(
            system_prompt=system_prompt,
            history_messages=history_messages,
            current_query=state["user_query"],
            max_tokens=state.get("max_context_tokens", 65536),
            model=model,
            api_key=state.get("api_key"),
            base_url=state.get("base_url"),
            db=state.get("db"),
            user_id=state.get("user_id"),
            memory_top_k=state.get("memory_top_k", 5),
            core_memory_threshold=state.get("core_memory_threshold", 80)
        )
        
        llm_messages = context_result["messages"]
        
        # 发送上下文信息
        if stream_queue:
            context_info_data = {
                "total_tokens": context_result["total_tokens"],
                "compressed": context_result["compressed"],
                "original_count": context_result["original_count"],
                "final_count": context_result["final_count"],
                "long_term_memory_included": context_result.get("long_term_memory_included", False)
            }
            await stream_queue.put({"type": "context_info", "info": context_info_data})
            
            # 显示历史对话信息
            history_count = len(history_messages)
            if history_count > 0:
                step = f"💬 已加载 {history_count} 条历史对话"
                thinking_steps.append(step)
                await stream_queue.put({"type": "thinking_step", "step": step})
            else:
                step = "💬 无历史对话记录"
                thinking_steps.append(step)
                await stream_queue.put({"type": "thinking_step", "step": step})
            
            # 显示长时记忆检索结果
            if context_result.get("long_term_memory_included"):
                memories = context_result.get("long_term_memories", [])
                core_count = context_result.get("core_memory_count", 0)
                normal_count = context_result.get("normal_memory_count", 0)
                step = f"📚 已加载用户长期记忆（核心记忆 {core_count} 条 + 相关记忆 {normal_count} 条）"
                thinking_steps.append(step)
                await stream_queue.put({"type": "thinking_step", "step": step})
                await stream_queue.put({"type": "memory_sources", "memories": memories})
            else:
                step = "📚 未检索到相关长期记忆"
                thinking_steps.append(step)
                await stream_queue.put({"type": "thinking_step", "step": step})
            
            # 显示历史消息压缩信息
            if context_result["compressed"]:
                step = f"📝 历史消息已压缩（{context_result['original_count']}条→{context_result['final_count']}条摘要）"
                thinking_steps.append(step)
                await stream_queue.put({"type": "thinking_step", "step": step})
        
        # 流式生成回复
        final_response = ""
        try:
            if stream_queue:
                async for chunk in llm_manager.chat_completion_stream(
                    messages=llm_messages,
                    model=model,
                    api_key=state.get("api_key"),
                    base_url=state.get("base_url")
                ):
                    final_response += chunk
                    await stream_queue.put({"type": "content", "content": chunk})
            else:
                response = await llm_manager.chat_completion(
                    messages=llm_messages,
                    model=model,
                    api_key=state.get("api_key"),
                    base_url=state.get("base_url"),
                    stream=False
                )
                final_response = response.choices[0].message.content
            
            return {"final_response": final_response, "thinking_steps": thinking_steps}
        except Exception as e:
            error_msg = f"生成回复时出错: {str(e)}"
            if stream_queue:
                await stream_queue.put({"type": "error", "error": str(e)})
            return {"final_response": error_msg, "thinking_steps": thinking_steps}

    async def _generate_from_tool_results(
        self,
        state: AgentState,
        thinking_steps: List[str],
        tool_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """基于工具结果生成回复"""
        stream_queue = state.get("stream_queue")
        
        # 构建系统提示词
        system_prompt = state.get("system_prompt", "你是一个有帮助的AI助手。")
        
        # 添加工具结果到系统提示
        tool_context = "\n\n你已经调用了以下工具获取信息：\n"
        for r in tool_results:
            tool_context += f"\n【{r.get('tool_name', 'unknown')}】\n{r.get('result', '')}\n"
        tool_context += "\n请根据以上工具结果，为用户生成一个完整、有帮助的回答。"
        system_prompt += tool_context
        
        # 添加联网搜索上下文
        web_results = state.get("web_search_results", [])
        if web_results:
            web_context = format_web_search_context([
                {"title": s["title"], "url": s["url"], "snippet": s["snippet"]}
                for s in web_results
            ])
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
        context_info = [f"{len(tool_results)}个工具结果"]
        if kb_results:
            context_info.append("知识库内容")
        if web_results:
            context_info.append(f"{len(web_results)}个网络来源")
        
        history_messages = []
        for msg in state.get("messages", []):
            if isinstance(msg, HumanMessage):
                history_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history_messages.append({"role": "assistant", "content": msg.content})
        
        if history_messages:
            context_info.append(f"{len(history_messages)}条历史对话")
        
        context_str = "、".join(context_info)
        step = f"已整合上下文：{context_str}"
        thinking_steps.append(step)
        if stream_queue:
            await stream_queue.put({"type": "thinking_step", "step": step})
        
        model = state.get("model", "deepseek-chat")
        step = f"正在使用 {model} 生成回答..."
        thinking_steps.append(step)
        if stream_queue:
            await stream_queue.put({"type": "thinking_step", "step": step})
        
        # 使用上下文管理器构建消息列表（包含长时记忆）
        from app.ai.context_manager import context_manager
        
        context_result = await context_manager.build_context(
            system_prompt=system_prompt,
            history_messages=history_messages,
            current_query=state["user_query"],
            max_tokens=state.get("max_context_tokens", 65536),
            model=model,
            api_key=state.get("api_key"),
            base_url=state.get("base_url"),
            db=state.get("db"),
            user_id=state.get("user_id"),
            memory_top_k=state.get("memory_top_k", 5),
            core_memory_threshold=state.get("core_memory_threshold", 80)
        )
        
        llm_messages = context_result["messages"]
        
        # 发送上下文信息
        if stream_queue:
            context_info_data = {
                "total_tokens": context_result["total_tokens"],
                "compressed": context_result["compressed"],
                "original_count": context_result["original_count"],
                "final_count": context_result["final_count"],
                "long_term_memory_included": context_result.get("long_term_memory_included", False)
            }
            await stream_queue.put({"type": "context_info", "info": context_info_data})
            
            # 显示历史对话信息
            history_count = len(history_messages)
            if history_count > 0:
                step = f"💬 已加载 {history_count} 条历史对话"
                thinking_steps.append(step)
                await stream_queue.put({"type": "thinking_step", "step": step})
            else:
                step = "💬 无历史对话记录"
                thinking_steps.append(step)
                await stream_queue.put({"type": "thinking_step", "step": step})
            
            # 显示长时记忆检索结果
            if context_result.get("long_term_memory_included"):
                memories = context_result.get("long_term_memories", [])
                core_count = context_result.get("core_memory_count", 0)
                normal_count = context_result.get("normal_memory_count", 0)
                step = f"📚 已加载用户长期记忆（核心记忆 {core_count} 条 + 相关记忆 {normal_count} 条）"
                thinking_steps.append(step)
                await stream_queue.put({"type": "thinking_step", "step": step})
                await stream_queue.put({"type": "memory_sources", "memories": memories})
            else:
                step = "📚 未检索到相关长期记忆"
                thinking_steps.append(step)
                await stream_queue.put({"type": "thinking_step", "step": step})
            
            # 显示历史消息压缩信息
            if context_result["compressed"]:
                step = f"📝 历史消息已压缩（{context_result['original_count']}条→{context_result['final_count']}条摘要）"
                thinking_steps.append(step)
                await stream_queue.put({"type": "thinking_step", "step": step})
        
        try:
            final_response = ""
            if stream_queue:
                async for chunk in llm_manager.chat_completion_stream(
                    messages=llm_messages,
                    model=model,
                    api_key=state.get("api_key"),
                    base_url=state.get("base_url")
                ):
                    final_response += chunk
                    await stream_queue.put({"type": "content", "content": chunk})
            else:
                response = await llm_manager.chat_completion(
                    messages=llm_messages,
                    model=model,
                    api_key=state.get("api_key"),
                    base_url=state.get("base_url")
                )
                final_response = response.choices[0].message.content
            
            return {"final_response": final_response, "thinking_steps": thinking_steps}
        except Exception as e:
            error_msg = f"生成回复失败: {str(e)}"
            if stream_queue:
                await stream_queue.put({"type": "error", "error": error_msg})
            return {"final_response": error_msg, "thinking_steps": thinking_steps}
    
    async def _extract_search_query(
        self,
        user_query: str,
        history_messages: List[Dict[str, str]] = None,
        model: str = "deepseek-chat",
        api_key: str = None,
        base_url: str = None
    ) -> str:
        """使用 AI 分析用户问题和历史对话，提取最佳搜索关键词"""
        context = ""
        if history_messages and len(history_messages) > 0:
            recent_messages = history_messages[-6:]
            context_parts = []
            for msg in recent_messages:
                role = "用户" if msg.get("role") == "user" else "AI"
                content = msg.get("content", "")[:200]
                context_parts.append(f"{role}: {content}")
            context = "\n".join(context_parts)
        
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
            search_query = search_query.strip('"\'').strip()
            
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
        """运行 Agent（非流式）"""
        messages = []
        if history_messages:
            for msg in history_messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
        
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
            "base_url": base_url,
            "max_context_tokens": 65536,
            "db": None,
            "user_id": None,
            "memory_top_k": 5,
            "core_memory_threshold": 80,
            "stream_queue": None,
            "mcp_tool_ids": [],
            "mcp_tools_loaded": False,
            "mcp_tools": [],
            "tool_calls": [],
            "tool_results": [],
            "mcp_iteration": 0,
            "max_mcp_iterations": 10
        }
        
        final_state = await self.graph.ainvoke(initial_state)
        
        result = {
            "response": final_state.get("final_response", ""),
            "thinking_steps": final_state.get("thinking_steps", []),
            "web_sources": [],
            "kb_sources": None
        }
        
        web_results = final_state.get("web_search_results", [])
        if web_results:
            result["web_sources"] = [
                {"url": r.get("url", ""), "title": r.get("title", ""), "snippet": r.get("snippet", "")[:200]}
                for r in web_results
            ]
        
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
        max_context_tokens: int = 65536,
        db = None,
        user_id: str = None,
        memory_top_k: int = 5,
        core_memory_threshold: int = 80,
        mcp_tool_ids: List[str] = None,
        max_mcp_iterations: int = 10
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式运行 Agent（使用 LangGraph）
        
        支持联网搜索、知识库查询、MCP 工具调用
        
        Yields:
            事件字典，包含 type 和相关数据
        """
        stream_queue = asyncio.Queue()
        
        messages = []
        if history_messages:
            for msg in history_messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
        
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
            "base_url": base_url,
            "max_context_tokens": max_context_tokens,
            "db": db,
            "user_id": user_id,
            "memory_top_k": memory_top_k,
            "core_memory_threshold": core_memory_threshold,
            "stream_queue": stream_queue,
            "mcp_tool_ids": mcp_tool_ids or [],
            "mcp_tools_loaded": False,
            "mcp_tools": [],
            "tool_calls": [],
            "tool_results": [],
            "mcp_iteration": 0,
            "max_mcp_iterations": max_mcp_iterations
        }
        
        async def run_graph():
            try:
                final_state = await self.graph.ainvoke(initial_state)
                done_data = {"type": "done", "model": model}
                
                kb_results = final_state.get("kb_results", {})
                if kb_results:
                    done_data["sources"] = {
                        "kb_name": kb_results.get("kb_name", ""),
                        "graph_data": kb_results.get("graph_data", {}),
                        "chunks": [
                            {"index": idx + 1, "content": c.get("content", "")}
                            for idx, c in enumerate(kb_results.get("chunks", [])[:10])
                        ]
                    }
                
                tool_results = final_state.get("tool_results", [])
                if tool_results:
                    done_data["tool_results"] = tool_results
                
                await stream_queue.put(done_data)
            except Exception as e:
                await stream_queue.put({"type": "error", "error": str(e)})
            finally:
                await stream_queue.put(None)
        
        graph_task = asyncio.create_task(run_graph())
        
        try:
            while True:
                event = await stream_queue.get()
                if event is None:
                    break
                yield event
        finally:
            if not graph_task.done():
                graph_task.cancel()
                try:
                    await graph_task
                except asyncio.CancelledError:
                    pass


# 创建全局 Agent 实例
conversation_agent = ConversationAgent()
