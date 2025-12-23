"""
LLM 配置模型
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserLLMConfig(Base):
    """用户 LLM 配置"""
    __tablename__ = "user_llm_configs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 配置信息
    name = Column(String(100), nullable=False)  # 配置名称，如 "我的 GPT-4"
    provider = Column(String(50), nullable=False)  # 提供商 ID
    model = Column(String(100), nullable=False)  # 模型名称
    api_key = Column(Text, nullable=False)  # API Key（加密存储）
    base_url = Column(String(500), nullable=False)  # Base URL
    api_standard = Column(String(50), default="openai", nullable=False)  # API 标准：openai/gemini/anthropic
    
    # 元数据
    description = Column(String(500), nullable=True)  # 描述
    is_default = Column(Boolean, default=False)  # 是否为默认配置
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    user = relationship("User", back_populates="llm_configs")
    
    def __repr__(self):
        return f"<UserLLMConfig {self.name} ({self.model})>"
