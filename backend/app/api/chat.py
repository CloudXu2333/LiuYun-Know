"""
对话相关 API - 对话管理（CRUD）
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationDetail,
    MessageResponse,
)
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["对话"])


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建新对话
    
    Args:
        conversation_data: 对话数据
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        创建的对话
    """
    conversation = await ChatService.create_conversation(db, current_user, conversation_data)
    return conversation


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户的对话列表
    
    Args:
        skip: 跳过数量
        limit: 返回数量
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        对话列表
    """
    conversations = await ChatService.get_user_conversations(db, current_user, skip, limit)
    
    # 为每个对话添加消息数量
    result = []
    for conv in conversations:
        conv_dict = ConversationResponse.model_validate(conv).model_dump()
        message_count = await ChatService.get_message_count(db, conv.id)
        conv_dict["message_count"] = message_count
        result.append(conv_dict)
    
    return result


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取对话详情（包含消息）
    
    Args:
        conversation_id: 对话 ID
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        对话详情
    """
    conversation = await ChatService.get_conversation(db, str(conversation_id), current_user)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    messages = await ChatService.get_conversation_messages(db, conversation_id)
    
    return ConversationDetail(
        **ConversationResponse.model_validate(conversation).model_dump(),
        messages=[MessageResponse.model_validate(msg) for msg in messages]
    )


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    conversation_data: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新对话
    
    Args:
        conversation_id: 对话 ID
        conversation_data: 更新数据
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        更新后的对话
    """
    conversation = await ChatService.get_conversation(db, conversation_id, current_user)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    updated_conversation = await ChatService.update_conversation(db, conversation, conversation_data)
    return updated_conversation


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除对话
    
    Args:
        conversation_id: 对话 ID
        current_user: 当前用户
        db: 数据库会话
    """
    conversation = await ChatService.get_conversation(db, conversation_id, current_user)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    await ChatService.delete_conversation(db, conversation)
    return None


@router.get("/history", response_model=List[ConversationResponse])
async def get_chat_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取对话历史（简化接口，兼容旧版）
    
    Args:
        limit: 返回数量
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        对话列表
    """
    conversations = await ChatService.get_user_conversations(db, current_user, 0, limit)
    return conversations

