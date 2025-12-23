"""
记忆服务 - 长期记忆的增删查改（异步版本）
"""
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.memory import LongTermMemory
from app.schemas.memory import LongTermMemoryCreate, LongTermMemoryUpdate


class MemoryService:
    """记忆服务"""
    
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
    
    def format_memories_for_context(self, memories: List[LongTermMemory]) -> str:
        """
        将记忆格式化为上下文字符串
        
        Args:
            memories: 记忆列表
            
        Returns:
            格式化的记忆字符串
        """
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
        
        lines.append("如果回答中使用了上述长期记忆的信息，请在相关内容后使用 [记忆X] 格式标注。")
        
        return "\n".join(lines)


# 创建全局实例
memory_service = MemoryService()
