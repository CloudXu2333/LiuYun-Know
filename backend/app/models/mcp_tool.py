"""
MCP 工具数据模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class MCPToolType(str, enum.Enum):
    """MCP 工具类型"""
    PLATFORM = "platform"  # 平台内置工具
    USER = "user"  # 用户自定义工具


class MCPTool(Base):
    """MCP 工具配置表"""
    
    __tablename__ = "mcp_tools"
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    
    # 基本信息
    name = Column(String(100), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    
    # 工具类型：平台/用户
    tool_type = Column(
        SQLEnum(MCPToolType),
        default=MCPToolType.USER,
        nullable=False,
        index=True
    )
    
    # stdio 格式的 JSON 配置
    # 格式: {"command": "npx", "args": [...], "env": {...}}
    config_json = Column(Text, nullable=False)
    
    # 所属用户（平台工具为 null）
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    
    # 状态
    enabled = Column(Boolean, default=True, nullable=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # 关系
    user = relationship("User", backref="mcp_tools")
    
    def __repr__(self):
        return f"<MCPTool(id={self.id}, name={self.name}, type={self.tool_type})>"
