"""
用户管理 API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.dependencies import get_current_user, get_current_superuser
from app.schemas.user import User as UserSchema, UserUpdate, PasswordChange, AdminUserCreate, AdminUserUpdate, UserListResponse, MemorySettingsUpdate, MemorySettingsResponse
from app.services.user_service import UserService
from app.core.security import verify_password, get_password_hash
from app.models.user import User

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("/me", response_model=UserSchema)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    获取个人信息
    
    Args:
        current_user: 当前用户
    
    Returns:
        用户信息
    """
    return current_user


@router.put("/me", response_model=UserSchema)
async def update_my_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新个人信息
    
    Args:
        user_data: 更新数据
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        更新后的用户信息
    """
    # 检查用户名是否已被其他用户使用
    if user_data.username and user_data.username != current_user.username:
        existing_user = await UserService.get_by_username(db, user_data.username)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已被使用"
            )
    
    # 检查邮箱是否已被其他用户使用
    if user_data.email and user_data.email != current_user.email:
        existing_user = await UserService.get_by_email(db, user_data.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被使用"
            )
    
    updated_user = await UserService.update(db, current_user, user_data)
    return updated_user


@router.put("/password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    修改密码
    
    Args:
        password_data: 密码数据
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        成功消息
    """
    # 验证旧密码
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )
    
    # 验证新密码确认
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="两次密码输入不一致"
        )
    
    # 更新密码
    await UserService.update_password(db, current_user, password_data.new_password)
    
    return {"message": "密码修改成功"}


# ============ 记忆设置 API ============

@router.get("/me/memory-settings", response_model=MemorySettingsResponse)
async def get_memory_settings(current_user: User = Depends(get_current_user)):
    """
    获取用户的记忆设置
    
    Returns:
        记忆设置（memory_top_k, core_memory_threshold, auto_merge_memory）
    """
    return MemorySettingsResponse(
        memory_top_k=current_user.memory_top_k,
        core_memory_threshold=current_user.core_memory_threshold,
        auto_merge_memory=getattr(current_user, 'auto_merge_memory', True)
    )


@router.put("/me/memory-settings", response_model=MemorySettingsResponse)
async def update_memory_settings(
    settings: MemorySettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户的记忆设置
    
    Args:
        settings: 记忆设置
            - memory_top_k: 普通记忆检索数量 (1-20)，默认5
            - core_memory_threshold: 核心记忆优先级阈值 (0-100)，默认80
            - auto_merge_memory: 自动合并冲突记忆，默认True
    
    Returns:
        更新后的记忆设置
    
    说明:
        - 核心记忆（priority >= threshold）：每次对话必定加载
        - 普通记忆（priority < threshold）：根据对话内容检索 top_k 条相关记忆
        - 自动合并：添加记忆时自动检测冲突并合并
    """
    if settings.memory_top_k is not None:
        current_user.memory_top_k = settings.memory_top_k
    
    if settings.core_memory_threshold is not None:
        current_user.core_memory_threshold = settings.core_memory_threshold
    
    if settings.auto_merge_memory is not None:
        current_user.auto_merge_memory = settings.auto_merge_memory
    
    await db.commit()
    await db.refresh(current_user)
    
    return MemorySettingsResponse(
        memory_top_k=current_user.memory_top_k,
        core_memory_threshold=current_user.core_memory_threshold,
        auto_merge_memory=getattr(current_user, 'auto_merge_memory', True)
    )



# ============ 管理员用户管理 API ============

@router.get("/admin/list", response_model=UserListResponse)
async def admin_list_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    管理员获取用户列表
    
    Args:
        page: 页码
        page_size: 每页数量
        search: 搜索关键词（用户名或邮箱）
        current_user: 当前管理员用户
        db: 数据库会话
    
    Returns:
        用户列表和总数
    """
    # 构建查询
    query = select(User)
    count_query = select(func.count(User.id))
    
    # 搜索过滤
    if search:
        search_filter = (User.username.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    
    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    offset = (page - 1) * page_size
    query = query.order_by(User.created_at.desc()).offset(offset).limit(page_size)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return UserListResponse(
        items=users,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/admin/create", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def admin_create_user(
    user_data: AdminUserCreate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    管理员创建用户
    
    Args:
        user_data: 用户数据
        current_user: 当前管理员用户
        db: 数据库会话
    
    Returns:
        创建的用户
    """
    # 检查用户名是否已存在
    existing_user = await UserService.get_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    existing_email = await UserService.get_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在"
        )
    
    # 创建用户
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        is_active=user_data.is_active,
        is_superuser=user_data.is_superuser
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@router.put("/admin/{user_id}", response_model=UserSchema)
async def admin_update_user(
    user_id: str,
    user_data: AdminUserUpdate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    管理员更新用户信息
    
    Args:
        user_id: 用户ID
        user_data: 更新数据
        current_user: 当前管理员用户
        db: 数据库会话
    
    Returns:
        更新后的用户
    """
    # 获取用户
    user = await UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 不能修改自己的管理员状态
    if str(user.id) == str(current_user.id) and user_data.is_superuser is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能取消自己的管理员权限"
        )
    
    # 检查用户名是否已被其他用户使用
    if user_data.username and user_data.username != user.username:
        existing_user = await UserService.get_by_username(db, user_data.username)
        if existing_user and str(existing_user.id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已被使用"
            )
    
    # 检查邮箱是否已被其他用户使用
    if user_data.email and user_data.email != user.email:
        existing_user = await UserService.get_by_email(db, user_data.email)
        if existing_user and str(existing_user.id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被使用"
            )
    
    # 更新字段
    if user_data.username is not None:
        user.username = user_data.username
    if user_data.email is not None:
        user.email = user_data.email
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.is_superuser is not None:
        user.is_superuser = user_data.is_superuser
    if user_data.password:
        user.hashed_password = get_password_hash(user_data.password)
    
    await db.commit()
    await db.refresh(user)
    
    return user


@router.delete("/admin/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_user(
    user_id: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    管理员删除用户
    
    Args:
        user_id: 用户ID
        current_user: 当前管理员用户
        db: 数据库会话
    """
    # 不能删除自己
    if str(current_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    # 获取用户
    user = await UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    await db.delete(user)
    await db.commit()
    
    return None
