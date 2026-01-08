"""
认证服务
"""
import logging
from typing import Optional, Tuple
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.auth import RegisterRequest, Token
from app.schemas.user import UserCreate
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token
)
from app.core.redis_client import redis_client
from app.services.user_service import UserService
from app.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """认证服务类"""
    
    @staticmethod
    async def register(
        db: AsyncSession,
        register_data: RegisterRequest
    ) -> User:
        """
        用户注册
        
        Args:
            db: 数据库会话
            register_data: 注册数据
        
        Returns:
            创建的用户对象
        
        Raises:
            HTTPException: 验证失败或用户已存在
        """
        # 验证密码确认
        if register_data.password != register_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="两次密码输入不一致"
            )
        
        # 检查用户名是否存在
        if await UserService.check_username_exists(db, register_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已被注册"
            )
        
        # 检查邮箱是否存在
        if await UserService.check_email_exists(db, register_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
        
        # 创建用户
        user_create = UserCreate(
            username=register_data.username,
            email=register_data.email,
            password=register_data.password
        )
        
        user = await UserService.create(db, user_create)
        
        return user
    
    @staticmethod
    async def authenticate(
        db: AsyncSession,
        username: str,
        password: str
    ) -> Optional[User]:
        """
        认证用户

        Args:
            db: 数据库会话
            username: 用户名或邮箱
            password: 密码

        Returns:
            用户对象，认证失败返回 None
        """
        logger.info(f"🔐 尝试登录 - 用户名: {username}")

        user = await UserService.get_by_username_or_email(db, username)

        if not user:
            logger.warning(f"❌ 用户不存在: {username}")
            return None

        logger.info(f"✅ 找到用户: {user.username} ({user.email})")

        if not verify_password(password, user.hashed_password):
            logger.warning(f"❌ 密码错误 - 用户: {username}")
            return None

        logger.info(f"✅ 密码验证成功 - 用户: {username}")

        if not user.is_active:
            logger.warning(f"❌ 用户已禁用 - 用户: {username}")
            return None

        logger.info(f"✅ 认证成功 - 用户: {username}")
        return user
    
    @staticmethod
    async def login(db: AsyncSession, username: str, password: str) -> Token:
        """
        用户登录

        Args:
            db: 数据库会话
            username: 用户名或邮箱
            password: 密码

        Returns:
            Token 对象

        Raises:
            HTTPException: 认证失败
        """
        logger.info(f"🔑 开始登录流程 - 用户: {username}")

        user = await AuthService.authenticate(db, username, password)

        if not user:
            logger.warning(f"❌ 登录失败 - 用户名或密码错误: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 生成 token
        logger.info(f"🔑 生成 Token - 用户ID: {user.id}")
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username}
        )

        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "username": user.username}
        )

        # 存储 token 到 Redis
        access_expire = settings.access_token_expire_minutes * 60
        refresh_expire = settings.refresh_token_expire_days * 24 * 60 * 60

        await redis_client.store_token(str(user.id), access_token, access_expire)
        await redis_client.store_token(str(user.id), refresh_token, refresh_expire)

        logger.info(f"✅ 登录成功 - 用户: {username}, 用户ID: {user.id}")

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
    
    @staticmethod
    async def refresh_access_token(refresh_token: str) -> Token:
        """
        刷新访问令牌
        
        Args:
            refresh_token: 刷新令牌
        
        Returns:
            新的 Token 对象
        
        Raises:
            HTTPException: token 无效
        """
        # 验证 refresh token
        payload = verify_token(refresh_token, token_type="refresh")
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = payload.get("sub")
        username = payload.get("username")
        
        # 检查 token 是否在 Redis 中
        is_valid = await redis_client.verify_token(user_id, refresh_token)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="刷新令牌已失效",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 生成新的 access token
        new_access_token = create_access_token(
            data={"sub": user_id, "username": username}
        )
        
        # 存储新 token 到 Redis
        access_expire = settings.access_token_expire_minutes * 60
        await redis_client.store_token(user_id, new_access_token, access_expire)
        
        return Token(
            access_token=new_access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
    
    @staticmethod
    async def logout(user_id: str, token: str):
        """
        用户登出
        
        Args:
            user_id: 用户 ID
            token: 当前 token
        """
        await redis_client.revoke_token(user_id, token)

