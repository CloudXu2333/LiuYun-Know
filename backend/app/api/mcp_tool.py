"""
MCP 工具 API 路由
"""
import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.dependencies import get_current_user, get_current_superuser
from app.models.user import User
from app.models.mcp_tool import MCPTool, MCPToolType
from app.schemas.mcp_tool import (
    MCPToolCreate,
    MCPToolUpdate,
    MCPToolResponse,
    MCPToolListResponse,
    MCPConfigBase,
    MCPServerToolsResponse,
    MCPTestConnectionResponse,
    MCPServerTool
)
from app.services.mcp_service import mcp_service

router = APIRouter(prefix="/mcp-tools", tags=["MCP Tools"])


def _model_to_response(tool: MCPTool) -> MCPToolResponse:
    """将数据库模型转换为响应模型"""
    config_dict = json.loads(tool.config_json)
    return MCPToolResponse(
        id=tool.id,
        name=tool.name,
        description=tool.description,
        tool_type=tool.tool_type,
        config=MCPConfigBase(**config_dict),
        user_id=tool.user_id,
        enabled=tool.enabled,
        created_at=tool.created_at,
        updated_at=tool.updated_at
    )


@router.get("", response_model=MCPToolListResponse)
async def list_mcp_tools(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取 MCP 工具列表
    返回平台工具和当前用户的自定义工具
    """
    # 获取平台工具
    platform_result = await db.execute(
        select(MCPTool).where(MCPTool.tool_type == MCPToolType.PLATFORM)
    )
    platform_tools = platform_result.scalars().all()
    
    # 获取用户工具
    user_result = await db.execute(
        select(MCPTool).where(
            and_(
                MCPTool.tool_type == MCPToolType.USER,
                MCPTool.user_id == current_user.id
            )
        )
    )
    user_tools = user_result.scalars().all()
    
    return MCPToolListResponse(
        platform_tools=[_model_to_response(t) for t in platform_tools],
        user_tools=[_model_to_response(t) for t in user_tools]
    )


@router.post("", response_model=MCPToolResponse, status_code=status.HTTP_201_CREATED)
async def create_mcp_tool(
    tool_data: MCPToolCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建用户自定义 MCP 工具"""
    # 检查名称是否重复
    existing = await db.execute(
        select(MCPTool).where(
            and_(
                MCPTool.name == tool_data.name,
                MCPTool.user_id == current_user.id
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="工具名称已存在"
        )
    
    # 创建工具
    tool = MCPTool(
        name=tool_data.name,
        description=tool_data.description,
        tool_type=MCPToolType.USER,
        config_json=tool_data.config.model_dump_json(),
        user_id=current_user.id,
        enabled=tool_data.enabled
    )
    
    db.add(tool)
    await db.commit()
    await db.refresh(tool)
    
    return _model_to_response(tool)


@router.get("/{tool_id}", response_model=MCPToolResponse)
async def get_mcp_tool(
    tool_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个 MCP 工具详情"""
    result = await db.execute(
        select(MCPTool).where(MCPTool.id == tool_id)
    )
    tool = result.scalar_one_or_none()
    
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工具不存在"
        )
    
    # 检查权限：平台工具所有人可见，用户工具只有创建者可见
    if tool.tool_type == MCPToolType.USER and tool.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此工具"
        )
    
    return _model_to_response(tool)


@router.put("/{tool_id}", response_model=MCPToolResponse)
async def update_mcp_tool(
    tool_id: str,
    tool_data: MCPToolUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新 MCP 工具（仅限用户自己的工具）"""
    result = await db.execute(
        select(MCPTool).where(MCPTool.id == tool_id)
    )
    tool = result.scalar_one_or_none()
    
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工具不存在"
        )
    
    # 只能修改自己的工具
    if tool.tool_type == MCPToolType.PLATFORM:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无法修改平台工具"
        )
    
    if tool.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此工具"
        )
    
    # 更新字段
    if tool_data.name is not None:
        tool.name = tool_data.name
    if tool_data.description is not None:
        tool.description = tool_data.description
    if tool_data.config is not None:
        tool.config_json = tool_data.config.model_dump_json()
    if tool_data.enabled is not None:
        tool.enabled = tool_data.enabled
    
    await db.commit()
    await db.refresh(tool)
    
    return _model_to_response(tool)


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mcp_tool(
    tool_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除 MCP 工具（仅限用户自己的工具）"""
    result = await db.execute(
        select(MCPTool).where(MCPTool.id == tool_id)
    )
    tool = result.scalar_one_or_none()
    
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工具不存在"
        )
    
    if tool.tool_type == MCPToolType.PLATFORM:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无法删除平台工具"
        )
    
    if tool.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此工具"
        )
    
    # 停止可能运行中的 MCP Server
    await mcp_service.stop_server(tool_id)
    
    await db.delete(tool)
    await db.commit()


@router.post("/{tool_id}/test", response_model=MCPTestConnectionResponse)
async def test_mcp_connection(
    tool_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试 MCP 工具连接"""
    result = await db.execute(
        select(MCPTool).where(MCPTool.id == tool_id)
    )
    tool = result.scalar_one_or_none()
    
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工具不存在"
        )
    
    # 检查权限
    if tool.tool_type == MCPToolType.USER and tool.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此工具"
        )
    
    # 解析配置
    config = json.loads(tool.config_json)
    
    # 测试连接
    test_result = await mcp_service.test_connection(
        command=config["command"],
        args=config.get("args", []),
        env=config.get("env", {})
    )
    
    return MCPTestConnectionResponse(
        success=test_result["success"],
        message=test_result["message"],
        tools_count=test_result["tools_count"],
        tools=[
            MCPServerTool(
                name=t.get("name", ""),
                description=t.get("description"),
                input_schema=t.get("inputSchema", {})
            )
            for t in test_result.get("tools", [])
        ]
    )


@router.post("/test-config", response_model=MCPTestConnectionResponse)
async def test_mcp_config(
    config: MCPConfigBase,
    current_user: User = Depends(get_current_user)
):
    """测试 MCP 配置（不保存）"""
    test_result = await mcp_service.test_connection(
        command=config.command,
        args=config.args,
        env=config.env
    )
    
    return MCPTestConnectionResponse(
        success=test_result["success"],
        message=test_result["message"],
        tools_count=test_result["tools_count"],
        tools=[
            MCPServerTool(
                name=t.get("name", ""),
                description=t.get("description"),
                input_schema=t.get("inputSchema", {})
            )
            for t in test_result.get("tools", [])
        ]
    )


@router.get("/{tool_id}/server-tools", response_model=MCPServerToolsResponse)
async def get_server_tools(
    tool_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取 MCP Server 提供的工具列表"""
    result = await db.execute(
        select(MCPTool).where(MCPTool.id == tool_id)
    )
    tool = result.scalar_one_or_none()
    
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工具不存在"
        )
    
    # 检查权限
    if tool.tool_type == MCPToolType.USER and tool.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此工具"
        )
    
    # 如果未连接，先启动
    if not mcp_service.is_connected(tool_id):
        config = json.loads(tool.config_json)
        success = await mcp_service.start_server(
            tool_id=tool_id,
            command=config["command"],
            args=config.get("args", []),
            env=config.get("env", {})
        )
        if not success:
            return MCPServerToolsResponse(
                tools=[],
                error="无法连接到 MCP Server"
            )
    
    # 获取工具列表
    tools = await mcp_service.get_tools(tool_id)
    
    return MCPServerToolsResponse(
        tools=[
            MCPServerTool(
                name=t.get("name", ""),
                description=t.get("description"),
                input_schema=t.get("inputSchema", {})
            )
            for t in tools
        ]
    )


# ============ 管理员接口 ============

@router.post("/platform", response_model=MCPToolResponse, status_code=status.HTTP_201_CREATED)
async def create_platform_tool(
    tool_data: MCPToolCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """创建平台 MCP 工具（仅管理员）"""
    # 检查名称是否重复
    existing = await db.execute(
        select(MCPTool).where(
            and_(
                MCPTool.name == tool_data.name,
                MCPTool.tool_type == MCPToolType.PLATFORM
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="平台工具名称已存在"
        )
    
    tool = MCPTool(
        name=tool_data.name,
        description=tool_data.description,
        tool_type=MCPToolType.PLATFORM,
        config_json=tool_data.config.model_dump_json(),
        user_id=None,
        enabled=tool_data.enabled
    )
    
    db.add(tool)
    await db.commit()
    await db.refresh(tool)
    
    return _model_to_response(tool)


@router.put("/platform/{tool_id}", response_model=MCPToolResponse)
async def update_platform_tool(
    tool_id: str,
    tool_data: MCPToolUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """更新平台 MCP 工具（仅管理员）"""
    result = await db.execute(
        select(MCPTool).where(
            and_(
                MCPTool.id == tool_id,
                MCPTool.tool_type == MCPToolType.PLATFORM
            )
        )
    )
    tool = result.scalar_one_or_none()
    
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="平台工具不存在"
        )
    
    if tool_data.name is not None:
        tool.name = tool_data.name
    if tool_data.description is not None:
        tool.description = tool_data.description
    if tool_data.config is not None:
        tool.config_json = tool_data.config.model_dump_json()
    if tool_data.enabled is not None:
        tool.enabled = tool_data.enabled
    
    await db.commit()
    await db.refresh(tool)
    
    return _model_to_response(tool)


@router.delete("/platform/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_platform_tool(
    tool_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """删除平台 MCP 工具（仅管理员）"""
    result = await db.execute(
        select(MCPTool).where(
            and_(
                MCPTool.id == tool_id,
                MCPTool.tool_type == MCPToolType.PLATFORM
            )
        )
    )
    tool = result.scalar_one_or_none()
    
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="平台工具不存在"
        )
    
    await mcp_service.stop_server(tool_id)
    await db.delete(tool)
    await db.commit()
