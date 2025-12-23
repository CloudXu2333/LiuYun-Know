"""
MCP 流程图服务 - 真正的 MCP 客户端实现

通过 stdio 与 MCP Server 进程通信，使用官方 MCP SDK

MCP 协议核心概念：
1. Server: 提供工具(tools)、资源(resources)、提示(prompts)的服务端
2. Client: 调用 Server 能力的客户端
3. Transport: 通信层，支持 stdio、HTTP SSE 等
4. JSON-RPC 2.0: 底层消息格式
"""
import json
import asyncio
import sys
import os
from typing import Optional, Dict, Any, List
from pathlib import Path
from contextlib import asynccontextmanager

# 使用官方 MCP SDK
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPDiagramService:
    """
    MCP 流程图服务
    
    管理与 Draw.io MCP Server 的通信
    
    调用流程：
    1. stdio_client 启动 MCP Server 子进程
    2. ClientSession 处理 JSON-RPC 通信
    3. 调用 session.call_tool() 执行工具
    4. 返回结果
    """
    
    def __init__(self):
        # MCP Server 脚本路径（位于 services 目录下）
        self.server_script = str(
            Path(__file__).parent / "drawio_mcp_server.py"
        )
        self._tools_cache: List[Dict] = []
    
    @asynccontextmanager
    async def _get_session(self):
        """
        获取 MCP 会话（上下文管理器）
        
        每次调用都会启动一个新的 MCP Server 进程
        这是最简单的实现方式，适合低频调用场景
        
        如果需要高频调用，可以维护一个长连接的 session
        """
        # 配置 Server 启动参数
        server_params = StdioServerParameters(
            command=sys.executable,  # Python 解释器路径
            args=[self.server_script],  # MCP Server 脚本
            env=None  # 继承当前环境变量
        )
        
        # 启动 MCP Server 并建立连接
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # 初始化会话（MCP 协议要求）
                await session.initialize()
                yield session
    
    async def get_tools_from_server(self) -> List[Dict]:
        """
        从 MCP Server 动态获取工具定义
        
        这是 MCP 的核心优势：
        - 工具定义由 Server 提供
        - 客户端不需要硬编码工具 schema
        - Server 更新后客户端自动获取新能力
        """
        async with self._get_session() as session:
            result = await session.list_tools()
            tools = []
            for tool in result.tools:
                tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                })
            self._tools_cache = tools
            return tools
    
    def get_tools(self) -> List[Dict]:
        """
        获取工具定义（OpenAI Function Calling 格式）
        
        将 MCP 工具定义转换为 OpenAI 格式供 LLM 使用
        
        注意：这里使用静态定义是为了避免每次请求都启动 Server
        实际项目中可以：
        1. 启动时调用 get_tools_from_server() 缓存
        2. 或者维护一个长连接的 session
        """
        return [{
            "type": "function",
            "function": {
                "name": "create_diagram",
                "description": "创建 Draw.io 流程图。当用户要求创建、生成、画流程图时调用此工具。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "流程图标题"
                        },
                        "nodes": {
                            "type": "array",
                            "description": "节点列表",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string", "description": "节点唯一ID"},
                                    "label": {"type": "string", "description": "节点显示文字"},
                                    "x": {"type": "number", "description": "X坐标"},
                                    "y": {"type": "number", "description": "Y坐标"},
                                    "width": {"type": "number", "description": "宽度"},
                                    "height": {"type": "number", "description": "高度"},
                                    "shape": {"type": "string", "description": "形状"},
                                    "fillColor": {"type": "string", "description": "填充颜色"},
                                    "strokeColor": {"type": "string", "description": "边框颜色"}
                                },
                                "required": ["id", "label", "x", "y", "width", "height", "shape", "fillColor", "strokeColor"]
                            }
                        },
                        "edges": {
                            "type": "array",
                            "description": "连接线列表",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "from": {"type": "string"},
                                    "to": {"type": "string"},
                                    "label": {"type": "string"}
                                },
                                "required": ["from", "to"]
                            }
                        }
                    },
                    "required": ["title", "nodes", "edges"]
                }
            }
        }]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用 MCP 工具
        
        这是真正的 MCP 调用流程：
        
        1. stdio_client 启动 drawio_mcp_server.py 子进程
        2. 通过 stdin/stdout 建立 JSON-RPC 通信
        3. ClientSession.initialize() 完成握手
        4. session.call_tool() 发送工具调用请求
        5. Server 执行 @app.call_tool() 装饰的函数
        6. 返回 TextContent 结果
        
        Args:
            name: 工具名称 (如 "create_diagram")
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        try:
            async with self._get_session() as session:
                # 调用 MCP 工具
                # 这会发送 JSON-RPC 请求到 Server
                result = await session.call_tool(name, arguments)
                
                # 解析返回的 TextContent
                for content in result.content:
                    if content.type == "text":
                        try:
                            return json.loads(content.text)
                        except json.JSONDecodeError:
                            return {"success": True, "message": content.text}
                
                return {"success": False, "error": "无返回内容"}
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "error": f"MCP 调用失败: {str(e)}"}


# 全局实例
mcp_diagram_service = MCPDiagramService()
