"""
知识库 Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============ 知识库 Schemas ============

class KnowledgeBaseCreate(BaseModel):
    """创建知识库"""
    name: str = Field(..., min_length=1, max_length=255, description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    status: Optional[str] = Field(None, description="知识库状态")


class KnowledgeBaseResponse(BaseModel):
    """知识库响应"""
    id: int
    name: str
    description: Optional[str]
    status: str
    working_dir: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
    file_count: int = 0
    
    class Config:
        from_attributes = True


# ============ 文件 Schemas ============

class FileUploadResponse(BaseModel):
    """文件上传响应"""
    id: int
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    status: str
    task_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class KnowledgeFileResponse(BaseModel):
    """知识库文件响应"""
    id: int
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    status: str
    error_message: Optional[str]
    task_id: Optional[str]
    knowledge_base_id: int
    uploaded_by: str
    created_at: datetime
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class KnowledgeBaseDetailResponse(KnowledgeBaseResponse):
    """知识库详情响应（包含文件列表）"""
    files: List[KnowledgeFileResponse] = []


# ============ 查询 Schemas ============

class KnowledgeQueryRequest(BaseModel):
    """知识库查询请求"""
    query: str = Field(..., min_length=1, description="查询问题")
    mode: str = Field(default="mix", description="查询模式: naive, local, global, hybrid, mix")
    top_k: int = Field(default=5, ge=1, le=20, description="返回结果数量")


class KnowledgeQueryResponse(BaseModel):
    """知识库查询响应"""
    answer: str
    mode: str
    knowledge_base_id: int
    query: str


# ============ 统计 Schemas ============

class KnowledgeBaseStatsResponse(BaseModel):
    """知识库统计响应"""
    total_files: int = Field(description="文件总数")
    completed_files: int = Field(description="已完成文件数")
    processing_files: int = Field(description="处理中文件数")
    failed_files: int = Field(description="失败文件数")
    pending_files: int = Field(description="等待中文件数")
    total_chunks: int = Field(description="分片总数")
    total_entities: int = Field(description="实体总数")
    total_relations: int = Field(description="关系总数")
    total_tokens: int = Field(description="Token总数")


# ============ 分片 Schemas ============

class ChunkResponse(BaseModel):
    """分片响应"""
    id: str
    content: str
    tokens: int
    chunk_order_index: int
    full_doc_id: str
    file_path: str
    create_time: int


class PaginatedChunkResponse(BaseModel):
    """分页分片响应"""
    items: List[ChunkResponse]
    total: int
    skip: int
    limit: int


# ============ 知识图谱 Schemas ============

class GraphNodeResponse(BaseModel):
    """图谱节点响应"""
    id: str
    label: str
    type: str = "entity"


class GraphEdgeResponse(BaseModel):
    """图谱边响应"""
    id: str
    source: str
    target: str
    label: str


class GraphDataResponse(BaseModel):
    """图谱数据响应"""
    nodes: List[GraphNodeResponse]
    edges: List[GraphEdgeResponse]
    total_nodes: int
    total_edges: int


class EntityDetailResponse(BaseModel):
    """实体详情响应"""
    id: str
    name: str
    type: str
    description: Optional[str] = None
    relations: List[GraphEdgeResponse] = []
    source_chunks: List[ChunkResponse] = []


class EntityUpdateRequest(BaseModel):
    """实体更新请求"""
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    file_ids: List[int] = Field(..., description="要删除的文件ID列表")
