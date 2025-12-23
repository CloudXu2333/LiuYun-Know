"""
对话相关 Pydantic 模型
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    """消息基础模型"""
    role: str
    content: str


class MessageCreate(BaseModel):
    """创建消息模型"""
    content: str = Field(..., min_length=1, description="消息内容")


class MessageResponse(MessageBase):
    """消息响应模型"""
    id: UUID
    conversation_id: UUID
    tokens: int
    model: Optional[str]
    created_at: datetime
    metadata: Optional[dict] = None  # 额外元数据：web_sources, sources 等
    
    class Config:
        from_attributes = True
    
    @classmethod
    def model_validate(cls, obj, **kwargs):
        """自定义验证，处理 msg_metadata 到 metadata 的映射"""
        if hasattr(obj, 'msg_metadata'):
            # 创建一个临时字典来存储数据
            data = {
                'id': obj.id,
                'conversation_id': obj.conversation_id,
                'role': obj.role.value if hasattr(obj.role, 'value') else obj.role,
                'content': obj.content,
                'tokens': obj.tokens,
                'model': obj.model,
                'created_at': obj.created_at,
                'metadata': obj.msg_metadata
            }
            return cls(**data)
        return super().model_validate(obj, **kwargs)


class ConversationBase(BaseModel):
    """对话基础模型"""
    title: str = Field(default="新对话", max_length=200)


class ConversationCreate(ConversationBase):
    """创建对话模型"""
    pass


class ConversationUpdate(BaseModel):
    """更新对话模型"""
    title: Optional[str] = Field(None, max_length=200)


class ConversationResponse(ConversationBase):
    """对话响应模型"""
    id: UUID
    user_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class ConversationDetail(ConversationResponse):
    """对话详情模型（包含消息）"""
    messages: List[MessageResponse] = []


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., min_length=1, max_length=4000, description="用户消息")
    conversation_id: Optional[UUID] = Field(None, description="对话 ID，不传则创建新对话")
    stream: bool = Field(default=False, description="是否流式返回")
    enable_web_search: bool = Field(default=False, description="是否启用联网搜索")


class ChatResponse(BaseModel):
    """聊天响应模型"""
    conversation_id: UUID
    message: MessageResponse
    reply: MessageResponse

