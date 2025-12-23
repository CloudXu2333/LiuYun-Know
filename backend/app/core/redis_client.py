"""
Redis 客户端封装
"""
import json
from typing import Optional, Any
from redis import asyncio as aioredis
from app.config import settings


class RedisClient:
    """Redis 客户端封装类"""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
    
    async def connect(self):
        """连接 Redis"""
        self.redis = await aioredis.from_url(
            f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
            password=settings.redis_password if settings.redis_password else None,
            encoding="utf-8",
            decode_responses=True,
        )
    
    async def close(self):
        """关闭 Redis 连接"""
        if self.redis:
            await self.redis.close()
    
    async def get(self, key: str) -> Optional[str]:
        """获取值"""
        if not self.redis:
            await self.connect()
        return await self.redis.get(key)
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """
        设置值
        
        Args:
            key: 键
            value: 值
            expire: 过期时间（秒）
        
        Returns:
            是否成功
        """
        if not self.redis:
            await self.connect()
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        return await self.redis.set(key, value, ex=expire)
    
    async def delete(self, key: str) -> int:
        """删除键"""
        if not self.redis:
            await self.connect()
        return await self.redis.delete(key)
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self.redis:
            await self.connect()
        return await self.redis.exists(key) > 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        if not self.redis:
            await self.connect()
        return await self.redis.expire(key, seconds)
    
    async def ttl(self, key: str) -> int:
        """获取剩余生存时间"""
        if not self.redis:
            await self.connect()
        return await self.redis.ttl(key)
    
    async def store_token(self, user_id: str, token: str, expire: int):
        """
        存储用户 token
        
        Args:
            user_id: 用户 ID
            token: token 字符串
            expire: 过期时间（秒）
        """
        key = f"token:{user_id}:{token}"
        await self.set(key, "1", expire)
    
    async def verify_token(self, user_id: str, token: str) -> bool:
        """
        验证 token 是否在 Redis 中
        
        Args:
            user_id: 用户 ID
            token: token 字符串
        
        Returns:
            是否有效
        """
        key = f"token:{user_id}:{token}"
        return await self.exists(key)
    
    async def revoke_token(self, user_id: str, token: str):
        """
        撤销 token（登出时使用）
        
        Args:
            user_id: 用户 ID
            token: token 字符串
        """
        key = f"token:{user_id}:{token}"
        await self.delete(key)
    
    async def revoke_all_tokens(self, user_id: str):
        """
        撤销用户所有 token
        
        Args:
            user_id: 用户 ID
        """
        if not self.redis:
            await self.connect()
        
        pattern = f"token:{user_id}:*"
        cursor = 0
        
        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break


# 创建全局 Redis 客户端实例
redis_client = RedisClient()

