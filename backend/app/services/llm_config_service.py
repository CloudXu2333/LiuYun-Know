"""
LLM 配置服务
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.llm_config import UserLLMConfig
from app.models.user import User
from app.schemas.llm_config import UserLLMConfigCreate, UserLLMConfigUpdate


class LLMConfigService:
    """LLM 配置服务"""
    
    @staticmethod
    async def create_config(
        db: AsyncSession,
        user: User,
        config_data: UserLLMConfigCreate
    ) -> UserLLMConfig:
        """创建配置"""
        # 如果设置为默认，先取消其他默认配置
        if config_data.is_default:
            await LLMConfigService._unset_all_defaults(db, user.id)
        
        # 自动设置 base_url（如果未提供）
        base_url = config_data.base_url
        if not base_url:
            base_url = LLMConfigService._get_default_base_url(config_data.provider)
        
        # 自动检测 API 标准
        api_standard = config_data.api_standard or LLMConfigService._detect_api_standard(
            config_data.provider, 
            config_data.model
        )
        
        config = UserLLMConfig(
            user_id=user.id,
            name=config_data.name,
            provider=config_data.provider,
            model=config_data.model,
            api_key=config_data.api_key,  # TODO: 加密存储
            base_url=base_url,
            api_standard=api_standard,
            description=config_data.description,
            is_default=config_data.is_default
        )
        
        db.add(config)
        await db.flush()
        await db.refresh(config)
        
        return config
    
    @staticmethod
    def _get_default_base_url(provider: str) -> str:
        """根据提供商获取默认 Base URL"""
        provider_urls = {
            "302ai": "https://api.302.ai/v1",
            "deepseek": "https://api.deepseek.com",
            "openai": "https://api.openai.com/v1",
            "anthropic": "https://api.anthropic.com",
            "google": "https://generativelanguage.googleapis.com/v1beta"
        }
        return provider_urls.get(provider, "https://api.openai.com/v1")
    
    @staticmethod
    def _detect_api_standard(provider: str, model: str) -> str:
        """检测 API 标准"""
        # 根据模型名称检测
        if "gemini" in model.lower():
            return "gemini"
        elif "claude" in model.lower():
            return "anthropic"
        elif "gpt" in model.lower() or "deepseek" in model.lower():
            return "openai"
        
        # 根据提供商检测
        provider_standards = {
            "google": "gemini",
            "anthropic": "anthropic",
            "302ai": "openai",  # 302.AI 使用 OpenAI 兼容接口
            "deepseek": "openai",
            "openai": "openai"
        }
        return provider_standards.get(provider, "openai")
    
    @staticmethod
    async def get_user_configs(
        db: AsyncSession,
        user: User
    ) -> List[UserLLMConfig]:
        """获取用户的所有配置"""
        result = await db.execute(
            select(UserLLMConfig)
            .where(UserLLMConfig.user_id == user.id)
            .order_by(UserLLMConfig.is_default.desc(), UserLLMConfig.created_at.desc())
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_config(
        db: AsyncSession,
        config_id: str,
        user: User
    ) -> Optional[UserLLMConfig]:
        """获取单个配置"""
        result = await db.execute(
            select(UserLLMConfig).where(
                UserLLMConfig.id == config_id,
                UserLLMConfig.user_id == user.id
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_config(
        db: AsyncSession,
        config: UserLLMConfig,
        config_data: UserLLMConfigUpdate
    ) -> UserLLMConfig:
        """更新配置"""
        update_data = config_data.model_dump(exclude_unset=True)
        
        # 如果设置为默认，先取消其他默认配置
        if update_data.get('is_default'):
            await LLMConfigService._unset_all_defaults(db, config.user_id)
        
        for field, value in update_data.items():
            setattr(config, field, value)
        
        await db.flush()
        await db.refresh(config)
        
        return config
    
    @staticmethod
    async def delete_config(
        db: AsyncSession,
        config: UserLLMConfig
    ) -> bool:
        """删除配置"""
        await db.delete(config)
        await db.flush()
        return True
    
    @staticmethod
    async def _unset_all_defaults(db: AsyncSession, user_id: str):
        """取消用户的所有默认配置"""
        result = await db.execute(
            select(UserLLMConfig).where(
                UserLLMConfig.user_id == user_id,
                UserLLMConfig.is_default == True
            )
        )
        configs = result.scalars().all()
        for config in configs:
            config.is_default = False
        await db.flush()


# ============ 平台级 LLM 配置服务 ============

from app.models.llm_config import PlatformLLMConfig
from app.schemas.llm_config import PlatformLLMConfigCreate, PlatformLLMConfigUpdate


class PlatformLLMConfigService:
    """平台级 LLM 配置服务"""
    
    @staticmethod
    async def create_config(
        db: AsyncSession,
        config_data: PlatformLLMConfigCreate
    ) -> PlatformLLMConfig:
        """创建平台配置"""
        config = PlatformLLMConfig(
            name=config_data.name,
            provider=config_data.provider,
            model=config_data.model,
            api_key=config_data.api_key,
            base_url=config_data.base_url,
            api_standard=config_data.api_standard or "openai",
            max_context_tokens=config_data.max_context_tokens,
            description=config_data.description,
            is_active=config_data.is_active,
            sort_order=config_data.sort_order
        )
        
        db.add(config)
        await db.flush()
        await db.refresh(config)
        
        return config
    
    @staticmethod
    async def get_all_configs(db: AsyncSession) -> List[PlatformLLMConfig]:
        """获取所有平台配置（管理员用）"""
        result = await db.execute(
            select(PlatformLLMConfig)
            .order_by(PlatformLLMConfig.sort_order, PlatformLLMConfig.created_at.desc())
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_active_configs(db: AsyncSession) -> List[PlatformLLMConfig]:
        """获取所有启用的平台配置（普通用户用）"""
        result = await db.execute(
            select(PlatformLLMConfig)
            .where(PlatformLLMConfig.is_active == True)
            .order_by(PlatformLLMConfig.sort_order, PlatformLLMConfig.created_at.desc())
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_config(db: AsyncSession, config_id: str) -> Optional[PlatformLLMConfig]:
        """获取单个配置"""
        result = await db.execute(
            select(PlatformLLMConfig).where(PlatformLLMConfig.id == config_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_config(
        db: AsyncSession,
        config: PlatformLLMConfig,
        config_data: PlatformLLMConfigUpdate
    ) -> PlatformLLMConfig:
        """更新配置"""
        update_data = config_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(config, field, value)
        
        await db.flush()
        await db.refresh(config)
        
        return config
    
    @staticmethod
    async def delete_config(db: AsyncSession, config: PlatformLLMConfig) -> bool:
        """删除配置"""
        await db.delete(config)
        await db.flush()
        return True
