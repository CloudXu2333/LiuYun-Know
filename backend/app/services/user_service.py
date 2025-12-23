"""
用户服务
"""
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash


class UserService:
    """用户服务类"""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id) -> Optional[User]:
        """通过 ID 获取用户"""
        # 转换为字符串格式（带连字符的 UUID）
        if isinstance(user_id, UUID):
            user_id_str = str(user_id)
        else:
            user_id_str = str(user_id)
            # 如果是 32 位无连字符格式，转换为标准 UUID 格式
            if len(user_id_str) == 32 and '-' not in user_id_str:
                user_id_str = f"{user_id_str[:8]}-{user_id_str[8:12]}-{user_id_str[12:16]}-{user_id_str[16:20]}-{user_id_str[20:]}"
        
        result = await db.execute(select(User).where(User.id == user_id_str))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_username_or_email(
        db: AsyncSession,
        identifier: str
    ) -> Optional[User]:
        """通过用户名或邮箱获取用户"""
        result = await db.execute(
            select(User).where(
                (User.username == identifier) | (User.email == identifier)
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(db: AsyncSession, user_data: UserCreate) -> User:
        """创建用户"""
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            is_active=True,
            is_superuser=False,
        )
        
        db.add(db_user)
        await db.flush()
        await db.refresh(db_user)
        
        return db_user
    
    @staticmethod
    async def update(
        db: AsyncSession,
        user: User,
        user_data: UserUpdate
    ) -> User:
        """更新用户信息"""
        update_data = user_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await db.flush()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def update_password(
        db: AsyncSession,
        user: User,
        new_password: str
    ) -> User:
        """更新用户密码"""
        user.hashed_password = get_password_hash(new_password)
        
        await db.flush()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def delete(db: AsyncSession, user: User) -> bool:
        """删除用户"""
        await db.delete(user)
        await db.flush()
        return True
    
    @staticmethod
    async def check_username_exists(db: AsyncSession, username: str) -> bool:
        """检查用户名是否存在"""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none() is not None
    
    @staticmethod
    async def check_email_exists(db: AsyncSession, email: str) -> bool:
        """检查邮箱是否存在"""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none() is not None

