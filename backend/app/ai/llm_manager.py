"""
LLM 管理器 - 支持动态切换模型和自定义 API 配置
"""
from typing import List, Dict, Any, AsyncGenerator, Optional
import openai
from openai import AsyncOpenAI
from app.config import settings
from app.schemas.llm_config import (
    LLMProvider, LLMModelInfo, LLMConfigResponse,
    DEFAULT_PROVIDERS, DEFAULT_MODELS
)


class LLMManager:
    """LLM 管理器类 - 支持动态配置"""
    
    def __init__(self):
        """初始化默认配置"""
        self.default_api_key = settings.openai_api_key
        self.default_base_url = settings.openai_api_base
        self.default_model = settings.default_model
        
        # Embedding 配置（保持不变）
        self.embedding_api_key = settings.qwen_api_key if settings.qwen_api_key else settings.openai_api_key
        self.embedding_base_url = settings.qwen_api_base if settings.qwen_api_key else settings.openai_api_base
        self.embedding_model = settings.embedding_model
    
    def get_client(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> AsyncOpenAI:
        """
        获取 OpenAI 客户端
        
        Args:
            api_key: 自定义 API Key
            base_url: 自定义 Base URL
        
        Returns:
            AsyncOpenAI 客户端
        """
        return AsyncOpenAI(
            api_key=api_key or self.default_api_key,
            base_url=base_url or self.default_base_url,
        )
    
    def get_embedding_client(self) -> AsyncOpenAI:
        """获取 Embedding 客户端"""
        return AsyncOpenAI(
            api_key=self.embedding_api_key,
            base_url=self.embedding_base_url,
        )
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        stream: bool = False,
    ) -> Any:
        """
        聊天补全
        
        Args:
            messages: 消息列表
            model: 模型名称
            api_key: 自定义 API Key
            base_url: 自定义 Base URL
            temperature: 温度参数
            max_tokens: 最大 token 数
            stream: 是否流式返回
        
        Returns:
            响应对象或流式生成器
        """
        client = self.get_client(api_key, base_url)
        use_model = model or self.default_model
        
        try:
            response = await client.chat.completions.create(
                model=use_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
            )
            return response
        except openai.APIError as e:
            raise Exception(f"API 错误: {str(e)}")
        except Exception as e:
            raise Exception(f"LLM 请求失败: {str(e)}")
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天补全
        
        Args:
            messages: 消息列表
            model: 模型名称
            api_key: 自定义 API Key
            base_url: 自定义 Base URL
            temperature: 温度参数
            max_tokens: 最大 token 数
        
        Yields:
            逐字返回的文本片段
        """
        client = self.get_client(api_key, base_url)
        use_model = model or self.default_model
        
        try:
            stream = await client.chat.completions.create(
                model=use_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content is not None:
                        yield delta.content
        except openai.APIError as e:
            raise Exception(f"API 错误: {str(e)}")
        except Exception as e:
            raise Exception(f"LLM 流式请求失败: {str(e)}")
    
    async def get_embedding(self, text: str, model: Optional[str] = None) -> List[float]:
        """获取文本嵌入向量"""
        client = self.get_embedding_client()
        use_model = model or self.embedding_model
        
        try:
            response = await client.embeddings.create(
                model=use_model,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"嵌入向量生成失败: {str(e)}")
    
    async def get_embeddings_batch(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        """批量获取文本嵌入向量"""
        client = self.get_embedding_client()
        use_model = model or self.embedding_model
        
        try:
            response = await client.embeddings.create(
                model=use_model,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            raise Exception(f"批量嵌入向量生成失败: {str(e)}")
    
    def get_providers(self) -> List[LLMProvider]:
        """获取所有提供商"""
        return DEFAULT_PROVIDERS
    
    def get_models(self, provider_id: Optional[str] = None) -> List[LLMModelInfo]:
        """获取模型列表"""
        if provider_id:
            return [m for m in DEFAULT_MODELS if m.provider == provider_id]
        return DEFAULT_MODELS
    
    def get_config_response(self) -> LLMConfigResponse:
        """获取当前配置响应"""
        return LLMConfigResponse(
            current_provider="302ai",
            current_model=self.default_model,
            use_custom_api=False,
            providers=self.get_providers(),
            models=self.get_models()
        )


# 创建全局 LLM 管理器实例
llm_manager = LLMManager()
