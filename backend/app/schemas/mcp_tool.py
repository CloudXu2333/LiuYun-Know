"""
MCP 工具相关 Pydantic 模型
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class MCPToolType(str, Enum):
    """MCP 工具类型"""
    PLATFORM = "platform"
    USER = "user"


class MCPConfigBase(BaseModel):
    """MCP stdio 配置基础模型"""
    command: str = Field(..., description="执行命令，如 npx, python, node")
    args: List[str] = Field(default_factory=list, description="命令参数")
    env: Dict[str, str] = Field(default_factory=dict, description="环境变量")


class MCPToolBase(BaseModel):
    """MCP 工具基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="工具名称")
    description: Optional[str] = Field(None, max_length=500, description="工具描述")


class MCPToolCreate(MCPToolBase):
    """创建 MCP 工具请求"""
    config: MCPConfigBase = Field(..., description="stdio 格式配置")
    enabled: bool = Field(default=True, description="是否启用")


class MCPToolUpdate(BaseModel):
    """更新 MCP 工具请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    config: Optional[MCPConfigBase] = None
    enabled: Optional[bool] = None


class MCPToolResponse(MCPToolBase):
    """MCP 工具响应模型"""
    id: str
    tool_type: MCPToolType
    config: MCPConfigBase
    user_id: Optional[str] = None
    enabled: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MCPToolListResponse(BaseModel):
    """MCP 工具列表响应"""
    platform_tools: List[MCPToolResponse] = Field(default_factory=list, description="平台工具")
    user_tools: List[MCPToolResponse] = Field(default_factory=list, description="用户自定义工具")


# MCP Server 返回的工具信息
class MCPServerTool(BaseModel):
    """MCP Server 提供的单个工具"""
    name: str = Field(..., description="工具名称")
    description: Optional[str] = Field(None, description="工具描述")
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="输入参数 schema")


class MCPServerToolsResponse(BaseModel):
    """获取 MCP Server 工具列表响应"""
    tools: List[MCPServerTool] = Field(default_factory=list)
    error: Optional[str] = None


class MCPTestConnectionResponse(BaseModel):
    """测试 MCP 连接响应"""
    success: bool
    message: str
    tools_count: int = 0
    tools: List[MCPServerTool] = Field(default_factory=list)
