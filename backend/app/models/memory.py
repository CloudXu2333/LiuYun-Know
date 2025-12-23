"""
记忆数据模型
- 长期记忆：跨对话持久化，每次对话都会加载
- 短期记忆：当前对话的上下文（由 context_manager 处理）
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


class LongTermMemory(Base):
    """长期记忆表 - 跨对话持久化"""
    
    __tablename__ = "long_term_memories"
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # 记忆内容
    title = Column(String(200), nullable=False)  # 记忆标题/简述
    content = Column(Text, nullable=False)  # 记忆详细内容
    
    # 分类和优先级
    category = Column(String(50), default="general")  # 分类：general, preference, fact, instruction
    priority = Column(Integer, default=0)  # 优先级，数字越大越重要
    
    # 状态
    is_active = Column(Boolean, default=True, nullable=False)  # 是否启用
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<LongTermMemory(id={self.id}, title={self.title}, user_id={self.user_id})>"
