"""
知识库数据模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class KnowledgeBaseStatus(str, enum.Enum):
    """知识库状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROCESSING = "processing"


class FileStatus(str, enum.Enum):
    """文件处理状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class KnowledgeBase(Base):
    """知识库模型"""
    __tablename__ = "knowledge_bases"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(KnowledgeBaseStatus), default=KnowledgeBaseStatus.ACTIVE)
    
    # LightRAG 工作目录
    working_dir = Column(String(500), nullable=False, unique=True)
    
    # 所有者
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="knowledge_bases")
    
    # 文件关系
    files = relationship("KnowledgeFile", back_populates="knowledge_base", cascade="all, delete-orphan")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, name='{self.name}')>"


class KnowledgeFile(Base):
    """知识库文件模型"""
    __tablename__ = "knowledge_files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # 字节
    file_type = Column(String(50), nullable=False)  # pdf, txt, docx, etc.
    
    # MinIO 存储路径
    minio_path = Column(String(1000), nullable=False)
    
    # 处理状态
    status = Column(SQLEnum(FileStatus), default=FileStatus.PENDING)
    error_message = Column(Text, nullable=True)
    
    # Celery 任务 ID
    task_id = Column(String(255), nullable=True)
    
    # 所属知识库
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    knowledge_base = relationship("KnowledgeBase", back_populates="files")
    
    # 上传者
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    uploader = relationship("User")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<KnowledgeFile(id={self.id}, filename='{self.filename}', status='{self.status}')>"
