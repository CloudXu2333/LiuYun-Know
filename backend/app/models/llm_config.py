"""
LLM 配置模型
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Integer
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
    max_context_tokens = Column(Integer, default=65536, nullable=False)  # 最大上下文 token 数，默认 64k
    
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


class PlatformLLMConfig(Base):
    """平台级 LLM 配置 - 所有用户可用"""
    __tablename__ = "platform_llm_configs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # 配置信息
    name = Column(String(100), nullable=False)  # 配置名称，如 "GPT-4o"
    provider = Column(String(50), nullable=False)  # 提供商 ID
    model = Column(String(100), nullable=False)  # 模型名称
    api_key = Column(Text, nullable=False)  # API Key
    base_url = Column(String(500), nullable=False)  # Base URL
    api_standard = Column(String(50), default="openai", nullable=False)  # API 标准
    max_context_tokens = Column(Integer, default=65536, nullable=False)  # 最大上下文 token 数
    
    # 元数据
    description = Column(String(500), nullable=True)  # 描述
    is_active = Column(Boolean, default=True)  # 是否启用
    sort_order = Column(Integer, default=0)  # 排序顺序
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<PlatformLLMConfig {self.name} ({self.model})>"
