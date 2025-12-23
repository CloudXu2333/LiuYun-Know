"""
用户管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.dependencies import get_current_user
from app.schemas.user import User as UserSchema, UserUpdate, PasswordChange
from app.services.user_service import UserService
from app.core.security import verify_password
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

