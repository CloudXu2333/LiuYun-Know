"""
长期记忆 API 接口
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.memory import (
    LongTermMemoryCreate,
    LongTermMemoryUpdate,
    LongTermMemoryResponse,
    LongTermMemoryList,
    MEMORY_CATEGORIES
)
from app.services.memory_service import memory_service
from app.ai.llm_manager import llm_manager
from app.config import settings

router = APIRouter(prefix="/memory", tags=["memory"])


class AutoExtractRequest(BaseModel):
    """AI自动提取记忆请求"""
    content: str  # 要提取的内容
    config_id: Optional[str] = None  # 用户配置 ID
    platform_config_id: Optional[str] = None  # 平台配置 ID


class AutoExtractResponse(BaseModel):
    """AI自动提取记忆响应"""
    title: str
    content: str
    category: str
    priority: int


@router.get("/categories")
async def get_categories():
    """获取记忆分类选项"""
    return MEMORY_CATEGORIES


@router.get("", response_model=LongTermMemoryList)
async def list_memories(
    category: Optional[str] = None,
    active_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的长期记忆列表"""
    memories, total = await memory_service.get_user_memories(
        db=db,
        user_id=current_user.id,
        category=category,
        active_only=active_only,
        skip=skip,
        limit=limit
    )
    
    return LongTermMemoryList(
        items=memories,
        total=total
    )


@router.get("/{memory_id}", response_model=LongTermMemoryResponse)
async def get_memory(
    memory_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单条长期记忆"""
    memory = await memory_service.get_memory_by_id(db, memory_id, current_user.id)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记忆不存在"
        )
    return memory


@router.post("", response_model=LongTermMemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    memory_data: LongTermMemoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建长期记忆"""
    memory = await memory_service.create_memory(
        db=db,
        user_id=current_user.id,
        memory_data=memory_data
    )
    return memory


@router.put("/{memory_id}", response_model=LongTermMemoryResponse)
async def update_memory(
    memory_id: str,
    memory_data: LongTermMemoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新长期记忆"""
    memory = await memory_service.update_memory(
        db=db,
        memory_id=memory_id,
        user_id=current_user.id,
        memory_data=memory_data
    )
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记忆不存在"
        )
    return memory


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除长期记忆"""
    success = await memory_service.delete_memory(
        db=db,
        memory_id=memory_id,
        user_id=current_user.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记忆不存在"
        )


@router.post("/{memory_id}/toggle", response_model=LongTermMemoryResponse)
async def toggle_memory(
    memory_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """切换记忆的启用/禁用状态"""
    memory = await memory_service.toggle_memory(
        db=db,
        memory_id=memory_id,
        user_id=current_user.id
    )
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记忆不存在"
        )
    return memory


@router.post("/auto-extract", response_model=AutoExtractResponse)
async def auto_extract_memory(
    request: AutoExtractRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """AI自动提取记忆：分析内容并返回标题、分类、优先级"""
    import json
    from app.services.llm_config_service import LLMConfigService, PlatformLLMConfigService
    
    system_prompt = """你是一个记忆提取助手。用户会给你一段内容，你需要分析并提取出适合作为长期记忆存储的信息。

请返回JSON格式，包含以下字段：
- title: 简短的标题（不超过50字）
- content: 提炼后的核心内容（保留关键信息）
- category: 分类，只能是以下之一：
  - general: 通用信息
  - preference: 用户偏好（如喜好、习惯）
  - fact: 事实信息（如个人信息、重要数据）
  - instruction: 指令规则（如特殊要求、注意事项）
- priority: 优先级 0-100（越重要越高）

只返回JSON，不要其他内容。"""

    user_prompt = f"请分析以下内容并提取记忆：\n\n{request.content}"
    
    try:
        # 确定使用的 API 配置
        use_api_key = None
        use_base_url = None
        model = None
        
        # 优先使用平台配置
        if request.platform_config_id:
            platform_config = await PlatformLLMConfigService.get_config(db, request.platform_config_id)
            if platform_config and platform_config.is_active:
                use_api_key = platform_config.api_key
                use_base_url = platform_config.base_url
                model = platform_config.model
                print(f"[Memory] Using platform config: {platform_config.name}")
        # 其次使用用户配置
        elif request.config_id:
            user_config = await LLMConfigService.get_config(db, request.config_id, current_user)
            if user_config:
                use_api_key = user_config.api_key
                use_base_url = user_config.base_url
                model = user_config.model
                print(f"[Memory] Using user config: {user_config.name}")
        
        # 如果没有配置，使用默认配置
        if not use_api_key:
            use_api_key = settings.deepseek_api_key or settings.openai_api_key
            use_base_url = settings.deepseek_api_base or settings.openai_api_base
            model = "deepseek-chat" if settings.deepseek_api_key else settings.default_model
        
        client = llm_manager.get_client(
            api_key=use_api_key,
            base_url=use_base_url
        )
        
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # 清理可能的markdown代码块
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
        result_text = result_text.strip()
        
        result = json.loads(result_text)
        
        return AutoExtractResponse(
            title=result.get("title", "未命名记忆")[:200],
            content=result.get("content", request.content),
            category=result.get("category", "general") if result.get("category") in ["general", "preference", "fact", "instruction"] else "general",
            priority=min(100, max(0, int(result.get("priority", 50))))
        )
        
    except json.JSONDecodeError:
        # JSON解析失败，返回默认值
        return AutoExtractResponse(
            title=request.content[:50] + "..." if len(request.content) > 50 else request.content,
            content=request.content,
            category="general",
            priority=50
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI提取失败: {str(e)}"
        )
