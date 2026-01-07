"""
知识库 API 路由
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from typing import Optional
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    KnowledgeBaseDetailResponse,
    FileUploadResponse,
    KnowledgeFileResponse,
    KnowledgeQueryRequest,
    KnowledgeQueryResponse,
    KnowledgeBaseStatsResponse,
    PaginatedChunkResponse,
    ChunkResponse,
    GraphDataResponse,
    GraphNodeResponse,
    GraphEdgeResponse,
    EntityDetailResponse,
    BatchDeleteRequest,
)
from app.services.knowledge_base_service import knowledge_base_service


router = APIRouter(prefix="/knowledge-bases", tags=["知识库"])


@router.post("", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建知识库"""
    kb = await knowledge_base_service.create_knowledge_base(db, kb_data, current_user.id)
    kb.file_count = 0
    return kb


@router.get("", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """列出用户的知识库"""
    return await knowledge_base_service.list_knowledge_bases(db, current_user.id, skip, limit)


@router.get("/{kb_id}", response_model=KnowledgeBaseDetailResponse)
async def get_knowledge_base(
    kb_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取知识库详情"""
    kb = await knowledge_base_service.get_knowledge_base(db, kb_id, current_user.id, load_files=True)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    # 添加文件计数
    kb.file_count = len(kb.files)
    return kb


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: int,
    kb_data: KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新知识库"""
    kb = await knowledge_base_service.update_knowledge_base(db, kb_id, current_user.id, kb_data)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    # 获取文件计数
    files = await knowledge_base_service.list_files(db, kb_id, current_user.id)
    kb.file_count = len(files) if files else 0
    return kb


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    kb_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除知识库"""
    success = await knowledge_base_service.delete_knowledge_base(db, kb_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return None


# ============ 文件管理 ============

@router.post("/{kb_id}/files", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    kb_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传文件到知识库"""
    # 检查文件类型
    allowed_types = ["pdf", "txt", "md", "markdown", "doc", "docx", "csv", "xlsx", "xls"]
    file_ext = file.filename.split(".")[-1].lower()
    
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。支持的类型: {', '.join(allowed_types)}"
        )
    
    file_record = await knowledge_base_service.upload_file(db, kb_id, current_user.id, file)
    if not file_record:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    return file_record


@router.get("/{kb_id}/files", response_model=List[KnowledgeFileResponse])
async def list_files(
    kb_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """列出知识库的文件"""
    files = await knowledge_base_service.list_files(db, kb_id, current_user.id)
    if files is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return files


@router.delete("/{kb_id}/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    kb_id: int,
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除文件"""
    success = await knowledge_base_service.delete_file(db, file_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="文件不存在")
    return None


# ============ 知识库查询 ============

@router.post("/{kb_id}/query", response_model=KnowledgeQueryResponse)
async def query_knowledge_base(
    kb_id: int,
    query_data: KnowledgeQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """查询知识库"""
    result = await knowledge_base_service.query_knowledge_base(
        db, kb_id, current_user.id, query_data
    )
    
    if result is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    return KnowledgeQueryResponse(
        answer=result,
        mode=query_data.mode,
        knowledge_base_id=kb_id,
        query=query_data.query
    )


# ============ 统计信息 ============

@router.get("/{kb_id}/stats", response_model=KnowledgeBaseStatsResponse)
async def get_knowledge_base_stats(
    kb_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取知识库统计信息"""
    stats = await knowledge_base_service.get_knowledge_base_stats(db, kb_id, current_user.id)
    if stats is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return stats


# ============ 分片数据 ============

@router.get("/{kb_id}/chunks", response_model=PaginatedChunkResponse)
async def get_chunks(
    kb_id: int,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取知识库分片数据"""
    result = await knowledge_base_service.get_chunks(db, kb_id, current_user.id, skip, limit, search)
    if result is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return result


# ============ 知识图谱 ============

@router.get("/{kb_id}/graph", response_model=GraphDataResponse)
async def get_knowledge_graph(
    kb_id: int,
    skip: int = 0,
    limit: int = 100,
    entity_type: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取知识图谱数据"""
    result = await knowledge_base_service.get_graph_data(
        db, kb_id, current_user.id, skip, limit, entity_type, search
    )
    if result is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return result


@router.get("/{kb_id}/entities/{entity_name}", response_model=EntityDetailResponse)
async def get_entity_detail(
    kb_id: int,
    entity_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取实体详情"""
    result = await knowledge_base_service.get_entity_detail(db, kb_id, current_user.id, entity_name)
    if result is None:
        raise HTTPException(status_code=404, detail="实体不存在")
    return result


@router.delete("/{kb_id}/entities/{entity_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entity(
    kb_id: int,
    entity_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除实体"""
    success = await knowledge_base_service.delete_entity(db, kb_id, current_user.id, entity_name)
    if not success:
        raise HTTPException(status_code=404, detail="实体不存在")
    return None


@router.delete("/{kb_id}/relations", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relation(
    kb_id: int,
    source: str,
    target: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除关系"""
    success = await knowledge_base_service.delete_relation(db, kb_id, current_user.id, source, target)
    if not success:
        raise HTTPException(status_code=404, detail="关系不存在")
    return None


# ============ 文件操作扩展 ============

@router.post("/{kb_id}/files/{file_id}/retry", response_model=FileUploadResponse)
async def retry_file_processing(
    kb_id: int,
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """重试文件处理"""
    result = await knowledge_base_service.retry_file_processing(db, kb_id, current_user.id, file_id)
    if result is None:
        raise HTTPException(status_code=404, detail="文件不存在")
    return result


@router.get("/{kb_id}/files/{file_id}/preview-url")
async def get_file_preview_url(
    kb_id: int,
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取文件预览URL"""
    kb = await knowledge_base_service.get_knowledge_base(db, kb_id, current_user.id)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    files = await knowledge_base_service.list_files(db, kb_id, current_user.id)
    file_record = next((f for f in files if f.id == file_id), None)
    if not file_record:
        raise HTTPException(status_code=404, detail="文件不存在")

    url = knowledge_base_service.get_file_preview_url(kb_id, file_record)
    return {"url": url}


@router.get("/{kb_id}/files/{file_id}/download")
async def download_file(
    kb_id: int,
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载文件（通过后端代理）"""
    from fastapi.responses import StreamingResponse
    from app.services.minio_service import minio_service
    import io
    from urllib.parse import quote

    kb = await knowledge_base_service.get_knowledge_base(db, kb_id, current_user.id)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    files = await knowledge_base_service.list_files(db, kb_id, current_user.id)
    file_record = next((f for f in files if f.id == file_id), None)
    if not file_record:
        raise HTTPException(status_code=404, detail="文件不存在")

    try:
        # 从 MinIO 获取文件流
        file_stream = minio_service.get_file_stream(file_record.minio_path)

        # 读取文件内容
        file_content = io.BytesIO(file_stream.read())
        file_content.seek(0)

        # 对文件名进行 URL 编码，支持中文
        encoded_filename = quote(file_record.original_filename)

        # 返回文件流
        return StreamingResponse(
            file_content,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件下载失败: {str(e)}")


@router.delete("/{kb_id}/files/batch", status_code=status.HTTP_204_NO_CONTENT)
async def batch_delete_files(
    kb_id: int,
    request: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量删除文件"""
    deleted_count = await knowledge_base_service.batch_delete_files(
        db, kb_id, current_user.id, request.file_ids
    )
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="没有文件被删除")
    return None



# ============ 图谱导出 ============

@router.get("/{kb_id}/graph/export")
async def export_knowledge_graph(
    kb_id: int,
    format: str = "json",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出知识图谱数据"""
    from fastapi.responses import JSONResponse, StreamingResponse
    import csv
    import io
    
    result = await knowledge_base_service.get_graph_data(
        db, kb_id, current_user.id, skip=0, limit=10000
    )
    if result is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    if format == "csv":
        # 导出CSV格式
        output = io.StringIO()
        
        # 写入节点
        output.write("# Nodes\n")
        writer = csv.writer(output)
        writer.writerow(["id", "label", "type"])
        for node in result['nodes']:
            writer.writerow([node['id'], node['label'], node['type']])
        
        output.write("\n# Edges\n")
        writer.writerow(["source", "target", "label"])
        for edge in result['edges']:
            writer.writerow([edge['source'], edge['target'], edge['label']])
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=knowledge_graph_{kb_id}.csv"}
        )
    else:
        # 默认JSON格式
        return JSONResponse(
            content=result,
            headers={"Content-Disposition": f"attachment; filename=knowledge_graph_{kb_id}.json"}
        )
