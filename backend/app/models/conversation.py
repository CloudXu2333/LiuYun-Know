"""
对话相关数据模型
"""
import uuid
import json
from datetime import datetime
from sqlalchemy import Boolean, Column, String, DateTime, Text, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class MessageRole(str, enum.Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Conversation(Base):
    """对话会话表"""
    
    __tablename__ = "conversations"
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False, default="新对话")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # 关系
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, title={self.title}, user_id={self.user_id})>"


class Message(Base):
    """对话消息表"""
    
    __tablename__ = "messages"
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    conversation_id = Column(
        String(36),
        ForeignKey("conversations.id"),
        nullable=False,
        index=True
    )
    role = Column(SQLEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    tokens = Column(Integer, default=0)  # token 数量
    model = Column(String(100), nullable=True)  # 使用的模型
    metadata_json = Column(Text, nullable=True)  # 存储额外元数据（JSON格式）：webSources, sources 等
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    conversation = relationship("Conversation", back_populates="messages")
    
    def get_metadata(self):
        """获取元数据字典"""
        if self.metadata_json:
            try:
                return json.loads(self.metadata_json)
            except:
                return {}
        return {}
    
    def set_metadata(self, value):
        """设置元数据"""
        if value:
            self.metadata_json = json.dumps(value, ensure_ascii=False)
        else:
            self.metadata_json = None
    
    # 为 Pydantic 提供 metadata 属性访问（通过 __getattr__）
    @property
    def msg_metadata(self):
        """元数据属性（避免与 SQLAlchemy Base.metadata 冲突）"""
        return self.get_metadata()
    
    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"

