"""
认证相关 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.dependencies import security, get_current_user
from app.schemas.auth import Token, LoginRequest, RegisterRequest, RefreshTokenRequest
from app.schemas.user import User as UserSchema
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register(
    register_data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册
    
    Args:
        register_data: 注册信息
        db: 数据库会话
    
    Returns:
        创建的用户信息
    """
    user = await AuthService.register(db, register_data)
    return user


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录
    
    Args:
        login_data: 登录信息
        db: 数据库会话
    
    Returns:
        JWT Token
    """
    token = await AuthService.login(db, login_data.username, login_data.password)
    return token


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_data: RefreshTokenRequest):
    """
    刷新访问令牌
    
    Args:
        refresh_data: 包含 refresh_token 的数据
    
    Returns:
        新的 JWT Token
    """
    token = await AuthService.refresh_access_token(refresh_data.refresh_token)
    return token


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user)
):
    """
    用户登出
    
    Args:
        credentials: 认证凭证
        current_user: 当前用户
    """
    token = credentials.credentials
    await AuthService.logout(str(current_user.id), token)
    return None


@router.get("/me", response_model=UserSchema)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前用户信息
    
    Args:
        current_user: 当前用户
    
    Returns:
        用户信息
    """
    return current_user

