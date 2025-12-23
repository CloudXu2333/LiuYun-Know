"""
记忆相关的 Pydantic Schema
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class LongTermMemoryBase(BaseModel):
    """长期记忆基础 Schema"""
    title: str = Field(..., min_length=1, max_length=200, description="记忆标题")
    content: str = Field(..., min_length=1, description="记忆内容")
    category: str = Field(default="general", description="分类: general, preference, fact, instruction")
    priority: int = Field(default=0, ge=0, le=100, description="优先级 0-100")
    is_active: bool = Field(default=True, description="是否启用")


class LongTermMemoryCreate(LongTermMemoryBase):
    """创建长期记忆"""
    pass


class LongTermMemoryUpdate(BaseModel):
    """更新长期记忆"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = None
    priority: Optional[int] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None


class LongTermMemoryResponse(LongTermMemoryBase):
    """长期记忆响应"""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LongTermMemoryList(BaseModel):
    """长期记忆列表响应"""
    items: List[LongTermMemoryResponse]
    total: int


# 记忆分类选项
MEMORY_CATEGORIES = [
    {"value": "general", "label": "通用", "description": "一般性记忆"},
    {"value": "preference", "label": "偏好", "description": "用户偏好设置"},
    {"value": "fact", "label": "事实", "description": "重要事实信息"},
    {"value": "instruction", "label": "指令", "description": "特殊指令或规则"},
]
