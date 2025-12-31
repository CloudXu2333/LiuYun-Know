"""
知识库服务层
"""
import os
import shutil
import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from fastapi import UploadFile
from app.models.knowledge_base import KnowledgeBase, KnowledgeFile, KnowledgeBaseStatus, FileStatus
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeQueryRequest
)
from app.services.minio_service import minio_service
from app.services.lightrag_service import lightrag_service
from app.tasks.file_processing import process_file_task


class KnowledgeBaseService:
    """知识库服务"""
    
    @staticmethod
    async def create_knowledge_base(db: AsyncSession, kb_data: KnowledgeBaseCreate, user_id: str) -> KnowledgeBase:
        """
        创建知识库
        
        Args:
            db: 数据库会话
            kb_data: 知识库数据
            user_id: 用户 ID
            
        Returns:
            创建的知识库
        """
        # 生成唯一的工作目录
        kb_id = str(uuid.uuid4())
        working_dir = f"./rag_storage/{user_id}/{kb_id}"
        
        # 创建知识库记录
        kb = KnowledgeBase(
            name=kb_data.name,
            description=kb_data.description,
            working_dir=working_dir,
            owner_id=user_id,
            status=KnowledgeBaseStatus.ACTIVE
        )
        
        db.add(kb)
        await db.commit()
        await db.refresh(kb)
        
        # 创建工作目录
        os.makedirs(working_dir, exist_ok=True)
        
        return kb
    
    @staticmethod
    async def get_knowledge_base(db: AsyncSession, kb_id: int, user_id: str, load_files: bool = False) -> Optional[KnowledgeBase]:
        """
        获取知识库
        
        Args:
            db: 数据库会话
            kb_id: 知识库 ID
            user_id: 用户 ID
            load_files: 是否预加载文件列表
            
        Returns:
            知识库或 None
        """
        query = select(KnowledgeBase).filter(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.owner_id == user_id
        )
        
        if load_files:
            query = query.options(selectinload(KnowledgeBase.files))
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_knowledge_bases(db: AsyncSession, user_id: str, skip: int = 0, limit: int = 100) -> List[KnowledgeBase]:
        """
        列出用户的知识库
        
        Args:
            db: 数据库会话
            user_id: 用户 ID
            skip: 跳过数量
            limit: 限制数量
            
        Returns:
            知识库列表
        """
        result = await db.execute(
            select(KnowledgeBase).filter(
                KnowledgeBase.owner_id == user_id
            ).offset(skip).limit(limit)
        )
        kbs = result.scalars().all()
        
        # 添加文件计数
        for kb in kbs:
            count_result = await db.execute(
                select(func.count(KnowledgeFile.id)).filter(
                    KnowledgeFile.knowledge_base_id == kb.id
                )
            )
            kb.file_count = count_result.scalar()
        
        return kbs
    
    @staticmethod
    async def update_knowledge_base(
        db: AsyncSession,
        kb_id: int,
        user_id: str,
        kb_data: KnowledgeBaseUpdate
    ) -> Optional[KnowledgeBase]:
        """
        更新知识库
        
        Args:
            db: 数据库会话
            kb_id: 知识库 ID
            user_id: 用户 ID
            kb_data: 更新数据
            
        Returns:
            更新后的知识库或 None
        """
        kb = await KnowledgeBaseService.get_knowledge_base(db, kb_id, user_id)
        if not kb:
            return None
        
        # 更新字段
        if kb_data.name is not None:
            kb.name = kb_data.name
        if kb_data.description is not None:
            kb.description = kb_data.description
        if kb_data.status is not None:
            kb.status = kb_data.status
        
        kb.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(kb)
        
        return kb
    
    @staticmethod
    async def delete_knowledge_base(db: AsyncSession, kb_id: int, user_id: str) -> bool:
        """
        删除知识库
        
        Args:
            db: 数据库会话
            kb_id: 知识库 ID
            user_id: 用户 ID
            
        Returns:
            是否成功删除
        """
        # 预加载文件列表
        kb = await KnowledgeBaseService.get_knowledge_base(db, kb_id, user_id, load_files=True)
        if not kb:
            return False
        
        working_dir = kb.working_dir
        
        # 1. 删除 Neo4j 中的所有图谱数据和本地 JSON 文件
        try:
            await lightrag_service.delete_all_data(working_dir)
            print(f"✅ 已删除知识库图谱数据: {kb_id}")
        except Exception as e:
            print(f"⚠️ 删除知识库图谱数据失败: {e}")
        
        # 2. 删除 MinIO 中的所有文件
        for file in kb.files:
            try:
                minio_service.delete_file(file.minio_path)
            except Exception as e:
                print(f"⚠️ 删除 MinIO 文件失败: {e}")
        
        # 3. 删除工作目录
        if os.path.exists(working_dir):
            try:
                shutil.rmtree(working_dir)
                print(f"✅ 已删除工作目录: {working_dir}")
            except Exception as e:
                print(f"⚠️ 删除工作目录失败: {e}")
        
        # 4. 移除 LightRAG 实例
        lightrag_service.remove_rag_instance(working_dir)
        
        # 5. 删除数据库记录（级联删除文件记录）
        await db.delete(kb)
        await db.commit()
        
        print(f"✅ 知识库删除完成: {kb_id}")
        return True
    
    @staticmethod
    async def upload_file(
        db: AsyncSession,
        kb_id: int,
        user_id: str,
        file: UploadFile
    ) -> Optional[KnowledgeFile]:
        """
        上传文件到知识库
        
        Args:
            db: 数据库会话
            kb_id: 知识库 ID
            user_id: 用户 ID
            file: 上传的文件
            
        Returns:
            文件记录或 None
        """
        # 检查知识库是否存在
        kb = await KnowledgeBaseService.get_knowledge_base(db, kb_id, user_id)
        if not kb:
            return None
        
        # 生成文件名
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        minio_path = f"knowledge_bases/{kb_id}/{unique_filename}"
        
        # 上传到 MinIO
        file_content = await file.read()
        await file.seek(0)
        
        from io import BytesIO
        minio_service.upload_file(
            BytesIO(file_content),
            minio_path,
            file.content_type or "application/octet-stream"
        )
        
        # 创建文件记录
        file_record = KnowledgeFile(
            filename=unique_filename,
            original_filename=file.filename,
            file_size=len(file_content),
            file_type=file_ext.lstrip('.').lower(),
            minio_path=minio_path,
            knowledge_base_id=kb_id,
            uploaded_by=user_id,
            status=FileStatus.PENDING
        )
        
        db.add(file_record)
        await db.commit()
        await db.refresh(file_record)
        
        # 提交 Celery 任务（Redis 锁确保同一知识库串行执行）
        task = process_file_task.delay(file_record.id)
        file_record.task_id = task.id
        await db.commit()
        
        return file_record
    
    @staticmethod
    async def list_files(db: AsyncSession, kb_id: int, user_id: str) -> Optional[List[KnowledgeFile]]:
        """
        列出知识库的文件
        
        Args:
            db: 数据库会话
            kb_id: 知识库 ID
            user_id: 用户 ID
            
        Returns:
            文件列表或 None
        """
        kb = await KnowledgeBaseService.get_knowledge_base(db, kb_id, user_id)
        if not kb:
            return None
        
        result = await db.execute(
            select(KnowledgeFile).filter(
                KnowledgeFile.knowledge_base_id == kb_id
            )
        )
        return result.scalars().all()
    
    @staticmethod
    async def delete_file(db: AsyncSession, file_id: int, user_id: str) -> bool:
        """
        删除文件及其相关的分片和图谱数据
        
        Args:
            db: 数据库会话
            file_id: 文件 ID
            user_id: 用户 ID
            
        Returns:
            是否成功删除
        """
        result = await db.execute(
            select(KnowledgeFile).join(KnowledgeBase).filter(
                KnowledgeFile.id == file_id,
                KnowledgeBase.owner_id == user_id
            )
        )
        file_record = result.scalar_one_or_none()
        
        if not file_record:
            return False
        
        # 获取知识库和文件数量
        kb_result = await db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == file_record.knowledge_base_id)
        )
        kb = kb_result.scalar_one_or_none()
        
        if kb:
            # 查询知识库中的文件数量
            file_count_result = await db.execute(
                select(func.count(KnowledgeFile.id)).filter(
                    KnowledgeFile.knowledge_base_id == kb.id
                )
            )
            file_count = file_count_result.scalar() or 0
            
            # 使用文件名作为标识删除相关的分片和图谱数据
            file_identifier = file_record.original_filename
            try:
                # 如果知识库只有这一个文件，删除所有数据
                delete_all = (file_count == 1)
                deleted_stats = await lightrag_service.delete_file_related_data(
                    kb.working_dir, 
                    file_identifier,
                    delete_all=delete_all
                )
                print(f"✅ 已删除文件相关数据: {deleted_stats}")
            except Exception as e:
                print(f"⚠️ 删除文件相关数据失败: {e}")
                import traceback
                traceback.print_exc()
        
        # 删除 MinIO 中的文件
        try:
            minio_service.delete_file(file_record.minio_path)
        except Exception as e:
            print(f"⚠️ 删除 MinIO 文件失败: {e}")
        
        # 删除数据库记录
        await db.delete(file_record)
        await db.commit()
        
        return True
    
    @staticmethod
    async def query_knowledge_base(
        db: AsyncSession,
        kb_id: int,
        user_id: str,
        query_data: KnowledgeQueryRequest
    ) -> Optional[str]:
        """
        查询知识库
        
        Args:
            db: 数据库会话
            kb_id: 知识库 ID
            user_id: 用户 ID
            query_data: 查询数据
            
        Returns:
            查询结果或 None
        """
        kb = await KnowledgeBaseService.get_knowledge_base(db, kb_id, user_id)
        if not kb:
            return None
        
        # 使用 LightRAG 查询
        result = await lightrag_service.query(
            kb.working_dir,
            query_data.query,
            mode=query_data.mode,
            top_k=query_data.top_k
        )
        
        return result
    
    @staticmethod
    async def get_knowledge_base_stats(db: AsyncSession, kb_id: int, user_id: str) -> Optional[dict]:
        """
        获取知识库统计信息
        
        Args:
            db: 数据库会话
            kb_id: 知识库 ID
            user_id: 用户 ID
            
        Returns:
            统计信息或 None
        """
        kb = await KnowledgeBaseService.get_knowledge_base(db, kb_id, user_id)
        if not kb:
            return None
        
        # 获取文件统计
        files = await KnowledgeBaseService.list_files(db, kb_id, user_id)
        total_files = len(files) if files else 0
        completed_files = sum(1 for f in files if f.status == FileStatus.COMPLETED) if files else 0
        processing_files = sum(1 for f in files if f.status == FileStatus.PROCESSING) if files else 0
        failed_files = sum(1 for f in files if f.status == FileStatus.FAILED) if files else 0
        pending_files = sum(1 for f in files if f.status == FileStatus.PENDING) if files else 0
        
        # 获取LightRAG统计
        rag_stats = await lightrag_service.get_stats(kb.working_dir)
        
        return {
            'total_files': total_files,
            'completed_files': completed_files,
            'processing_files': processing_files,
            'failed_files': failed_files,
            'pending_files': pending_files,
            'total_chunks': rag_stats.get('total_chunks', 0),
            'total_entities': rag_stats.get('total_entities', 0),
            'total_relations': rag_stats.get('total_relations', 0),
            'total_tokens': rag_stats.get('total_tokens', 0),
        }
    
    @staticmethod
    async def get_chunks(
        db: AsyncSession,
        kb_id: int,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None
    ) -> Optional[dict]:
        """
        获取知识库分片数据
        
        Args:
            db: 数据库会话
            kb_id: 知识库 ID
            user_id: 用户 ID
            skip: 跳过数量
            limit: 限制数量
            search: 搜索关键词
            
        Returns:
            分片数据或 None
        """
        kb = await KnowledgeBaseService.get_knowledge_base(db, kb_id, user_id)
        if not kb:
            return None
        
        chunks = await lightrag_service.get_chunks(kb.working_dir)
        
        # 搜索过滤
        if search:
            chunks = [c for c in chunks if search.lower() in c.get('content', '').lower()]
        
        total = len(chunks)
        items = chunks[skip:skip + limit]
        
        return {
            'items': items,
            'total': total,
            'skip': skip,
            'limit': limit,
        }
    
    @staticmethod
    async def get_graph_data(
        db: AsyncSession,
        kb_id: int,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        entity_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> Optional[dict]:
        """
        获取知识图谱数据
        
        Args:
            db: 数据库会话
            kb_id: 知识库 ID
            user_id: 用户 ID
            skip: 跳过数量
            limit: 限制数量
            entity_type: 实体类型过滤
            search: 搜索关键词
            
        Returns:
            图谱数据或 None
        """
        kb = await KnowledgeBaseService.get_knowledge_base(db, kb_id, user_id)
        if not kb:
            return None
        
        graph_data = await lightrag_service.get_graph_data(kb.working_dir, skip, limit)
        
        # 搜索过滤
        if search:
            graph_data['nodes'] = [
                n for n in graph_data['nodes'] 
                if search.lower() in n.get('label', '').lower()
            ]
            # 重新过滤边
            node_ids = {n['id'] for n in graph_data['nodes']}
            graph_data['edges'] = [
                e for e in graph_data['edges']
                if e['source'] in node_ids and e['target'] in node_ids
            ]
        
        return graph_data
    
    @staticmethod
    async def get_entity_detail(
        db: AsyncSession,
        kb_id: int,
        user_id: str,
        entity_name: str
    ) -> Optional[dict]:
        """
        获取实体详情
        """
        kb = await KnowledgeBaseService.get_knowledge_base(db, kb_id, user_id)
        if not kb:
            return None
        
        return await lightrag_service.get_entity_detail(kb.working_dir, entity_name)
    
    @staticmethod
    async def delete_entity(
        db: AsyncSession,
        kb_id: int,
        user_id: str,
        entity_name: str
    ) -> bool:
        """
        删除实体
        """
        kb = await KnowledgeBaseService.get_knowledge_base(db, kb_id, user_id)
        if not kb:
            return False
        
        return await lightrag_service.delete_entity(kb.working_dir, entity_name)
    
    @staticmethod
    async def delete_relation(
        db: AsyncSession,
        kb_id: int,
        user_id: str,
        source: str,
        target: str
    ) -> bool:
        """
        删除关系
        """
        kb = await KnowledgeBaseService.get_knowledge_base(db, kb_id, user_id)
        if not kb:
            return False
        
        return await lightrag_service.delete_relation(kb.working_dir, source, target)
    
    @staticmethod
    async def retry_file_processing(
        db: AsyncSession,
        kb_id: int,
        user_id: str,
        file_id: int
    ) -> Optional[KnowledgeFile]:
        """
        重试文件处理
        """
        kb = await KnowledgeBaseService.get_knowledge_base(db, kb_id, user_id)
        if not kb:
            return None
        
        result = await db.execute(
            select(KnowledgeFile).filter(
                KnowledgeFile.id == file_id,
                KnowledgeFile.knowledge_base_id == kb_id
            )
        )
        file_record = result.scalar_one_or_none()
        
        if not file_record:
            return None
        
        # 重置状态
        file_record.status = FileStatus.PENDING
        file_record.error_message = None
        
        # 重新提交任务
        task = process_file_task.delay(file_record.id)
        file_record.task_id = task.id
        
        await db.commit()
        await db.refresh(file_record)
        
        return file_record
    
    @staticmethod
    async def batch_delete_files(
        db: AsyncSession,
        kb_id: int,
        user_id: str,
        file_ids: List[int]
    ) -> int:
        """
        批量删除文件
        
        Returns:
            删除的文件数量
        """
        kb = await KnowledgeBaseService.get_knowledge_base(db, kb_id, user_id)
        if not kb:
            return 0
        
        deleted_count = 0
        for file_id in file_ids:
            if await KnowledgeBaseService.delete_file(db, file_id, user_id):
                deleted_count += 1
        
        return deleted_count
    
    @staticmethod
    def get_file_preview_url(kb_id: int, file_record: KnowledgeFile) -> str:
        """
        获取文件预览URL
        """
        return minio_service.get_presigned_url(file_record.minio_path)


knowledge_base_service = KnowledgeBaseService()
