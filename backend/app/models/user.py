"""
用户数据模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, String, DateTime, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    """用户表模型"""
    
    __tablename__ = "users"
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # 记忆设置
    memory_top_k = Column(Integer, default=5, nullable=False)  # 普通记忆向量检索数量，默认5条
    core_memory_threshold = Column(Integer, default=80, nullable=False)  # 核心记忆优先级阈值，默认80
    auto_merge_memory = Column(Boolean, default=True, nullable=False)  # 自动合并冲突记忆，默认开启
    
    # 关系
    knowledge_bases = relationship("KnowledgeBase", back_populates="owner")
    llm_configs = relationship("UserLLMConfig", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"

