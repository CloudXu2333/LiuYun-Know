"""
记忆服务 - 长期记忆的增删查改（异步版本）
支持核心记忆（高优先级）必定加载 + 普通记忆向量检索
"""
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from app.models.memory import LongTermMemory
from app.schemas.memory import LongTermMemoryCreate, LongTermMemoryUpdate


class MemoryService:
    """记忆服务"""
    
    async def get_core_memories(
        self,
        db: AsyncSession,
        user_id: str,
        threshold: int = 80
    ) -> List[LongTermMemory]:
        """
        获取核心记忆（优先级 >= threshold 的记忆，必定加载）
        
        Args:
            db: 数据库会话
            user_id: 用户 ID
            threshold: 核心记忆优先级阈值，默认 80
            
        Returns:
            核心记忆列表
        """
        query = select(LongTermMemory).where(
            and_(
                LongTermMemory.user_id == user_id,
                LongTermMemory.is_active == True,
                LongTermMemory.priority >= threshold
            )
        ).order_by(
            desc(LongTermMemory.priority),
            desc(LongTermMemory.created_at)
        )
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_normal_memories(
        self,
        db: AsyncSession,
        user_id: str,
        threshold: int = 80
    ) -> List[LongTermMemory]:
        """
        获取普通记忆（优先级 < threshold 的记忆，用于向量检索）
        
        Args:
            db: 数据库会话
            user_id: 用户 ID
            threshold: 核心记忆优先级阈值，默认 80
            
        Returns:
            普通记忆列表
        """
        query = select(LongTermMemory).where(
            and_(
                LongTermMemory.user_id == user_id,
                LongTermMemory.is_active == True,
                LongTermMemory.priority < threshold
            )
        ).order_by(
            desc(LongTermMemory.priority),
            desc(LongTermMemory.created_at)
        )
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_memories_for_context(
        self,
        db: AsyncSession,
        user_id: str,
        query_text: str = None,
        top_k: int = 5,
        threshold: int = 80
    ) -> Tuple[List[LongTermMemory], List[LongTermMemory]]:
        """
        获取用于上下文的记忆：核心记忆 + 相关普通记忆
        
        Args:
            db: 数据库会话
            user_id: 用户 ID
            query_text: 用户查询文本（用于向量检索）
            top_k: 普通记忆检索数量
            threshold: 核心记忆优先级阈值
            
        Returns:
            (核心记忆列表, 普通记忆列表)
        """
        # 1. 获取核心记忆（必定加载）
        core_memories = await self.get_core_memories(db, user_id, threshold)
        
        # 2. 获取普通记忆
        normal_memories = await self.get_normal_memories(db, user_id, threshold)
        
        # 3. 如果有查询文本，进行向量相似度检索；否则按优先级取 top_k
        if query_text and normal_memories:
            # TODO: 实现向量检索
            # 目前先按优先级排序取 top_k
            selected_normal = normal_memories[:top_k]
        else:
            selected_normal = normal_memories[:top_k]
        
        return core_memories, selected_normal
    
    async def get_user_memories(
        self,
        db: AsyncSession,
        user_id: str,
        category: Optional[str] = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[LongTermMemory], int]:
        """
        获取用户的长期记忆列表
        
        Args:
            db: 数据库会话
            user_id: 用户 ID
            category: 分类筛选
            active_only: 是否只返回启用的记忆
            skip: 跳过数量
            limit: 返回数量
            
        Returns:
            (记忆列表, 总数)
        """
        # 构建查询
        query = select(LongTermMemory).where(LongTermMemory.user_id == user_id)
        
        if category:
            query = query.where(LongTermMemory.category == category)
        
        if active_only:
            query = query.where(LongTermMemory.is_active == True)
        
        # 获取总数
        count_result = await db.execute(
            select(LongTermMemory.id).where(LongTermMemory.user_id == user_id)
            .where(LongTermMemory.category == category if category else True)
            .where(LongTermMemory.is_active == True if active_only else True)
        )
        total = len(count_result.all())
        
        # 获取分页数据
        query = query.order_by(
            desc(LongTermMemory.priority),
            desc(LongTermMemory.created_at)
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        memories = result.scalars().all()
        
        return list(memories), total
    
    async def get_active_memories(self, db: AsyncSession, user_id: str) -> List[LongTermMemory]:
        """
        获取用户所有启用的长期记忆（用于构建上下文）
        
        Args:
            db: 数据库会话
            user_id: 用户 ID
            
        Returns:
            启用的记忆列表（按优先级排序）
        """
        query = select(LongTermMemory).where(
            LongTermMemory.user_id == user_id,
            LongTermMemory.is_active == True
        ).order_by(
            desc(LongTermMemory.priority),
            desc(LongTermMemory.created_at)
        )
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_memory_by_id(
        self,
        db: AsyncSession,
        memory_id: str,
        user_id: str
    ) -> Optional[LongTermMemory]:
        """获取单条记忆"""
        query = select(LongTermMemory).where(
            LongTermMemory.id == memory_id,
            LongTermMemory.user_id == user_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_memory(
        self,
        db: AsyncSession,
        user_id: str,
        memory_data: LongTermMemoryCreate
    ) -> LongTermMemory:
        """创建长期记忆"""
        memory = LongTermMemory(
            user_id=user_id,
            title=memory_data.title,
            content=memory_data.content,
            category=memory_data.category,
            priority=memory_data.priority,
            is_active=memory_data.is_active
        )
        db.add(memory)
        await db.flush()
        await db.refresh(memory)
        return memory
    
    async def update_memory(
        self,
        db: AsyncSession,
        memory_id: str,
        user_id: str,
        memory_data: LongTermMemoryUpdate
    ) -> Optional[LongTermMemory]:
        """更新长期记忆"""
        memory = await self.get_memory_by_id(db, memory_id, user_id)
        if not memory:
            return None
        
        update_data = memory_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(memory, field, value)
        
        await db.flush()
        await db.refresh(memory)
        return memory
    
    async def delete_memory(
        self,
        db: AsyncSession,
        memory_id: str,
        user_id: str
    ) -> bool:
        """删除长期记忆"""
        memory = await self.get_memory_by_id(db, memory_id, user_id)
        if not memory:
            return False
        
        await db.delete(memory)
        await db.flush()
        return True
    
    async def toggle_memory(
        self,
        db: AsyncSession,
        memory_id: str,
        user_id: str
    ) -> Optional[LongTermMemory]:
        """切换记忆的启用状态"""
        memory = await self.get_memory_by_id(db, memory_id, user_id)
        if not memory:
            return None
        
        memory.is_active = not memory.is_active
        await db.flush()
        await db.refresh(memory)
        return memory
    
    def format_memories_for_context(
        self, 
        memories: List[LongTermMemory] = None,
        core_memories: List[LongTermMemory] = None,
        normal_memories: List[LongTermMemory] = None
    ) -> str:
        """
        将记忆格式化为上下文字符串
        
        Args:
            memories: 记忆列表（兼容旧接口）
            core_memories: 核心记忆列表
            normal_memories: 普通记忆列表
            
        Returns:
            格式化的记忆字符串
        """
        # 兼容旧接口
        if memories is not None and core_memories is None and normal_memories is None:
            if not memories:
                return ""
            
            lines = ["【用户长期记忆】"]
            
            for i, memory in enumerate(memories, 1):
                category_label = {
                    "general": "通用",
                    "preference": "偏好",
                    "fact": "事实",
                    "instruction": "指令"
                }.get(memory.category, memory.category)
                
                lines.append(f"[记忆{i}] [{category_label}] {memory.title}")
                lines.append(f"内容: {memory.content}")
                lines.append("")
            
            lines.append("【重要】如果回答中使用了长期记忆的信息，请使用 [记忆X] 格式标注（X为对应编号）。")
            
            return "\n".join(lines)
        
        # 新接口：区分核心记忆和普通记忆
        core_memories = core_memories or []
        normal_memories = normal_memories or []
        
        if not core_memories and not normal_memories:
            return ""
        
        lines = ["【用户长期记忆】"]
        memory_index = 1
        
        # 核心记忆（必定加载）
        if core_memories:
            lines.append("\n--- 核心记忆（重要信息，始终生效）---")
            for memory in core_memories:
                category_label = {
                    "general": "通用",
                    "preference": "偏好",
                    "fact": "事实",
                    "instruction": "指令"
                }.get(memory.category, memory.category)
                
                lines.append(f"[记忆{memory_index}] [{category_label}] {memory.title}")
                lines.append(f"内容: {memory.content}")
                lines.append("")
                memory_index += 1
        
        # 普通记忆（相关检索）
        if normal_memories:
            lines.append("\n--- 相关记忆（根据当前对话检索）---")
            for memory in normal_memories:
                category_label = {
                    "general": "通用",
                    "preference": "偏好",
                    "fact": "事实",
                    "instruction": "指令"
                }.get(memory.category, memory.category)
                
                lines.append(f"[记忆{memory_index}] [{category_label}] {memory.title}")
                lines.append(f"内容: {memory.content}")
                lines.append("")
                memory_index += 1
        
        lines.append("【重要】如果回答中使用了长期记忆的信息，请使用 [记忆X] 格式标注（X为对应编号）。")
        
        return "\n".join(lines)


# 创建全局实例
memory_service = MemoryService()
