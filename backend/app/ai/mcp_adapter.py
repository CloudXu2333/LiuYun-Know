"""
MCP 工具适配器
将 MCP Server 的工具转换为 LangChain Tool 格式，供 LangGraph Agent 使用
"""
import json
import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field, create_model

from app.services.mcp_service import mcp_service


@dataclass
class MCPToolConfig:
    """MCP 工具配置"""
    tool_id: str  # 数据库中的 MCP 工具 ID
    command: str
    args: List[str]
    env: Dict[str, str]


class MCPToolWrapper(BaseTool):
    """
    MCP 工具包装器
    将 MCP Server 的工具包装为 LangChain Tool
    """
    name: str = ""
    description: str = ""
    mcp_tool_id: str = ""  # 数据库中的 MCP 配置 ID
    mcp_tool_name: str = ""  # MCP Server 中的工具名称
    args_schema: Optional[type[BaseModel]] = None
    
    def __init__(
        self,
        name: str,
        description: str,
        mcp_tool_id: str,
        mcp_tool_name: str,
        input_schema: Dict[str, Any] = None,
        **kwargs
    ):
        # 动态创建 args_schema
        schema_class = self._create_schema(name, input_schema or {})
        
        super().__init__(
            name=name,
            description=description or f"MCP 工具: {name}",
            mcp_tool_id=mcp_tool_id,
            mcp_tool_name=mcp_tool_name,
            args_schema=schema_class,
            **kwargs
        )
    
    def _create_schema(self, name: str, input_schema: Dict[str, Any]) -> type[BaseModel]:
        """根据 MCP 工具的 inputSchema 动态创建 Pydantic 模型"""
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        
        fields = {}
        for prop_name, prop_info in properties.items():
            prop_type = prop_info.get("type", "string")
            prop_desc = prop_info.get("description", "")
            default = ... if prop_name in required else None
            
            # 映射 JSON Schema 类型到 Python 类型
            type_mapping = {
                "string": str,
                "integer": int,
                "number": float,
                "boolean": bool,
                "array": list,
                "object": dict
            }
            python_type = type_mapping.get(prop_type, str)
            
            if default is None:
                fields[prop_name] = (Optional[python_type], Field(default=None, description=prop_desc))
            else:
                fields[prop_name] = (python_type, Field(..., description=prop_desc))
        
        # 如果没有定义任何字段，添加一个可选的 input 字段
        if not fields:
            fields["input"] = (Optional[str], Field(default=None, description="输入参数"))
        
        # 创建动态模型
        model_name = f"{name.replace('-', '_').replace(' ', '_')}Input"
        return create_model(model_name, **fields)
    
    def _run(self, **kwargs) -> str:
        """同步执行（不推荐）"""
        return asyncio.run(self._arun(**kwargs))
    
    async def _arun(self, **kwargs) -> str:
        """异步执行 MCP 工具"""
        try:
            result = await mcp_service.call_tool(
                tool_id=self.mcp_tool_id,
                tool_name=self.mcp_tool_name,
                arguments=kwargs
            )
            
            if "error" in result:
                raise ToolException(result["error"])
            
            # 将结果转换为字符串
            if isinstance(result, dict):
                # 检查是否有 content 字段（MCP 标准响应格式）
                if "content" in result:
                    contents = result["content"]
                    if isinstance(contents, list):
                        text_parts = []
                        for item in contents:
                            if isinstance(item, dict) and item.get("type") == "text":
                                text_parts.append(item.get("text", ""))
                        return "\n".join(text_parts) if text_parts else json.dumps(result, ensure_ascii=False)
                return json.dumps(result, ensure_ascii=False, indent=2)
            return str(result)
        except ToolException:
            raise
        except Exception as e:
            raise ToolException(f"MCP 工具调用失败: {str(e)}")


class MCPToolManager:
    """
    MCP 工具管理器
    负责加载、管理和提供 MCP 工具
    """
    
    def __init__(self):
        self._tools_cache: Dict[str, List[BaseTool]] = {}  # {tool_id: [tools]}
        self._lock = asyncio.Lock()
    
    async def load_tools(self, tool_configs: List[Dict[str, Any]]) -> List[BaseTool]:
        """
        加载 MCP 工具
        
        Args:
            tool_configs: MCP 工具配置列表，每个配置包含:
                - id: 工具 ID
                - config: {"command": str, "args": list, "env": dict}
                
        Returns:
            LangChain Tool 列表
        """
        all_tools = []
        
        for config in tool_configs:
            tool_id = config["id"]
            mcp_config = config["config"]
            
            # 检查缓存
            if tool_id in self._tools_cache:
                all_tools.extend(self._tools_cache[tool_id])
                continue
            
            # 启动 MCP Server
            success = await mcp_service.start_server(
                tool_id=tool_id,
                command=mcp_config["command"],
                args=mcp_config.get("args", []),
                env=mcp_config.get("env", {})
            )
            
            if not success:
                print(f"⚠️ 无法启动 MCP Server: {tool_id}")
                continue
            
            # 获取工具列表
            server_tools = await mcp_service.get_tools(tool_id)
            
            # 转换为 LangChain Tool
            wrapped_tools = []
            for st in server_tools:
                tool = MCPToolWrapper(
                    name=f"mcp_{tool_id[:8]}_{st['name']}",
                    description=st.get("description", f"MCP 工具: {st['name']}"),
                    mcp_tool_id=tool_id,
                    mcp_tool_name=st["name"],
                    input_schema=st.get("inputSchema", {})
                )
                wrapped_tools.append(tool)
            
            # 缓存
            self._tools_cache[tool_id] = wrapped_tools
            all_tools.extend(wrapped_tools)
        
        return all_tools
    
    async def get_tools_for_ids(self, tool_ids: List[str]) -> List[BaseTool]:
        """根据工具 ID 列表获取已加载的工具"""
        tools = []
        for tool_id in tool_ids:
            if tool_id in self._tools_cache:
                tools.extend(self._tools_cache[tool_id])
        return tools
    
    def clear_cache(self, tool_id: str = None):
        """清除缓存"""
        if tool_id:
            self._tools_cache.pop(tool_id, None)
        else:
            self._tools_cache.clear()
    
    async def shutdown(self):
        """关闭所有 MCP 连接"""
        await mcp_service.shutdown()
        self._tools_cache.clear()


# 全局 MCP 工具管理器
mcp_tool_manager = MCPToolManager()


async def get_mcp_tools_from_db(
    db,
    user_id: str,
    tool_ids: List[str] = None
) -> List[BaseTool]:
    """
    从数据库加载用户的 MCP 工具
    
    Args:
        db: 数据库会话
        user_id: 用户 ID
        tool_ids: 指定的工具 ID 列表，为空则加载所有启用的工具
        
    Returns:
        LangChain Tool 列表
    """
    from sqlalchemy import select, and_, or_
    from app.models.mcp_tool import MCPTool, MCPToolType
    
    # 构建查询条件
    conditions = [MCPTool.enabled == True]
    
    if tool_ids:
        conditions.append(MCPTool.id.in_(tool_ids))
    
    # 查询平台工具和用户工具
    conditions.append(
        or_(
            MCPTool.tool_type == MCPToolType.PLATFORM,
            and_(
                MCPTool.tool_type == MCPToolType.USER,
                MCPTool.user_id == user_id
            )
        )
    )
    
    result = await db.execute(
        select(MCPTool).where(and_(*conditions))
    )
    mcp_tools = result.scalars().all()
    
    # 转换为配置格式
    tool_configs = []
    for tool in mcp_tools:
        config = json.loads(tool.config_json)
        tool_configs.append({
            "id": tool.id,
            "name": tool.name,
            "config": config
        })
    
    # 加载工具
    return await mcp_tool_manager.load_tools(tool_configs)
