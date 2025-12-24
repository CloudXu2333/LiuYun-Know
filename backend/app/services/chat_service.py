"""
对话服务 - 对话和消息的 CRUD 操作
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation import Conversation, Message, MessageRole
from app.models.user import User
from app.schemas.chat import ConversationCreate, ConversationUpdate


class ChatService:
    """对话服务类"""
    
    @staticmethod
    async def create_conversation(
        db: AsyncSession,
        user: User,
        conversation_data: ConversationCreate
    ) -> Conversation:
        """创建对话"""
        conversation = Conversation(
            user_id=user.id,
            title=conversation_data.title,
        )
        
        db.add(conversation)
        await db.flush()
        await db.refresh(conversation)
        
        return conversation
    
    @staticmethod
    async def get_conversation(
        db: AsyncSession,
        conversation_id: UUID,
        user: User
    ) -> Optional[Conversation]:
        """获取对话（验证所有权）"""
        # UUID 可能被 SQLAlchemy 绑定为不带连字符的 hex，这里统一转成标准字符串
        conversation_id_str = str(conversation_id)
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id_str,
                Conversation.user_id == user.id
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_conversations(
        db: AsyncSession,
        user: User,
        skip: int = 0,
        limit: int = 20
    ) -> List[Conversation]:
        """获取用户的对话列表"""
        result = await db.execute(
            select(Conversation)
            .where(Conversation.user_id == user.id)
            .order_by(desc(Conversation.updated_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def update_conversation(
        db: AsyncSession,
        conversation: Conversation,
        conversation_data: ConversationUpdate
    ) -> Conversation:
        """更新对话"""
        update_data = conversation_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(conversation, field, value)
        
        await db.flush()
        await db.refresh(conversation)
        
        return conversation
    
    @staticmethod
    async def delete_conversation(
        db: AsyncSession,
        conversation: Conversation
    ) -> bool:
        """删除对话"""
        await db.delete(conversation)
        await db.flush()
        return True
    
    @staticmethod
    async def get_conversation_messages(
        db: AsyncSession,
        conversation_id: UUID,
        limit: int = None,
        offset: int = 0
    ) -> List[Message]:
        """获取对话的消息列表（支持分页）"""
        conversation_id_str = str(conversation_id)
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id_str)
            .order_by(Message.created_at)
            .offset(offset)
        )
        if limit:
            query = query.limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_conversation_messages_count(
        db: AsyncSession,
        conversation_id: UUID
    ) -> int:
        """获取对话的消息总数"""
        from sqlalchemy import func
        conversation_id_str = str(conversation_id) 
        result = await db.execute(
            select(func.count(Message.id))
            .where(Message.conversation_id == conversation_id_str)
        )
        return result.scalar() or 0
    
    @staticmethod
    async def create_message(
        db: AsyncSession,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
        model: str = None,
        tokens: int = 0,
        metadata: dict = None
    ) -> Message:
        """创建消息"""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            model=model,
            tokens=tokens,
        )
        if metadata:
            message.set_metadata(metadata)
        
        db.add(message)
        await db.flush()
        await db.refresh(message)
        
        return message
    
    @staticmethod
    async def get_message_count(
        db: AsyncSession,
        conversation_id: UUID
    ) -> int:
        """获取对话的消息数量"""
        result = await db.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == conversation_id
            )
        )
        return result.scalar() or 0

