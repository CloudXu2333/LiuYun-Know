"""
LLM 配置相关 Pydantic 模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class LLMProvider(BaseModel):
    """LLM 提供商配置"""
    id: str = Field(..., description="提供商 ID")
    name: str = Field(..., description="提供商名称")
    base_url: str = Field(..., description="API Base URL")
    models: List[str] = Field(default_factory=list, description="支持的模型列表")


class LLMModelInfo(BaseModel):
    """LLM 模型信息"""
    id: str = Field(..., description="模型 ID")
    name: str = Field(..., description="模型显示名称")
    provider: str = Field(..., description="提供商 ID")
    description: Optional[str] = Field(None, description="模型描述")


class LLMConfigRequest(BaseModel):
    """LLM 配置请求"""
    provider: str = Field(..., description="提供商 ID: default/claude/gpt/gemini/custom")
    model: str = Field(..., description="模型名称")
    api_key: Optional[str] = Field(None, description="自定义 API Key（可选）")
    base_url: Optional[str] = Field(None, description="自定义 Base URL（可选）")


class LLMConfigResponse(BaseModel):
    """LLM 配置响应"""
    current_provider: str
    current_model: str
    use_custom_api: bool
    providers: List[LLMProvider]
    models: List[LLMModelInfo]


class WebSearchConfig(BaseModel):
    """联网搜索配置"""
    timeout: Optional[int] = Field(None, ge=10, le=300, description="搜索超时时间（秒），10-300")
    max_results: Optional[int] = Field(None, ge=1, le=20, description="每个搜索源最大结果数，1-20")
    use_tavily: bool = Field(default=True, description="是否使用 Tavily 搜索")
    use_firecrawl: bool = Field(default=True, description="是否使用 Firecrawl 搜索")
    # Firecrawl 高级选项
    firecrawl_scrape_content: bool = Field(default=False, description="Firecrawl 是否抓取页面内容（一体化模式）")


class ChatWithModelRequest(BaseModel):
    """带模型配置的聊天请求"""
    message: str = Field(..., min_length=1, max_length=4000, description="用户消息")
    conversation_id: Optional[str] = Field(None, description="对话 ID")
    stream: bool = Field(default=True, description="是否流式返回")
    # LLM 配置
    provider: Optional[str] = Field(None, description="提供商 ID")
    model: Optional[str] = Field(None, description="模型名称")
    api_key: Optional[str] = Field(None, description="自定义 API Key")
    base_url: Optional[str] = Field(None, description="自定义 Base URL")
    config_id: Optional[str] = Field(None, description="用户保存的配置 ID")
    # 知识库配置
    knowledge_base_id: Optional[str] = Field(None, description="知识库 ID")
    # 联网搜索配置
    enable_web_search: bool = Field(default=False, description="是否启用联网搜索")
    web_search_config: Optional[WebSearchConfig] = Field(None, description="联网搜索自定义配置")
    # 上下文配置
    max_context_tokens: int = Field(default=16000, ge=1000, description="最大上下文 token 数，超过时自动压缩旧消息")


class UserLLMConfigCreate(BaseModel):
    """创建用户 LLM 配置"""
    name: str = Field(..., min_length=1, max_length=100, description="配置名称")
    provider: str = Field(..., description="提供商 ID")
    model: str = Field(..., description="模型名称")
    api_key: str = Field(..., description="API Key")
    base_url: Optional[str] = Field(None, description="Base URL（可选，会根据 provider 自动设置）")
    api_standard: Optional[str] = Field("openai", description="API 标准：openai/gemini/anthropic")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    is_default: bool = Field(default=False, description="是否为默认配置")


class UserLLMConfigUpdate(BaseModel):
    """更新用户 LLM 配置"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    provider: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    api_standard: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)
    is_default: Optional[bool] = None


class UserLLMConfigResponse(BaseModel):
    """用户 LLM 配置响应"""
    id: str
    name: str
    provider: str
    model: str
    api_key: str  # 前端需要显示（部分隐藏）
    base_url: str
    api_standard: Optional[str] = "openai"
    description: Optional[str]
    is_default: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# 预定义的提供商和模型配置
DEFAULT_PROVIDERS = [
    LLMProvider(
        id="302ai",
        name="302.AI",
        base_url="https://api.302.ai/v1",
        models=["claude-sonnet-4-5-20250929", "claude-opus-4-5-20251101", 
                "gpt-5.2", "gpt-5.1", 
                "gemini-3-pro-preview", "gemini-2.5-pro"]
    ),
    LLMProvider(
        id="deepseek",
        name="DeepSeek",
        base_url="https://api.deepseek.com",
        models=["deepseek-chat"]
    ),
    LLMProvider(
        id="custom",
        name="自定义",
        base_url="",
        models=[]
    ),
]

DEFAULT_MODELS = [
    # 302.AI 模型（可用）
    LLMModelInfo(id="claude-sonnet-4-5-20250929", name="Claude 4.5 Sonnet", provider="302ai", description="最新 Claude 4.5 Sonnet"),
    LLMModelInfo(id="claude-opus-4-5-20251101", name="Claude 4.5 Opus", provider="302ai", description="Claude 4.5 Opus"),
    LLMModelInfo(id="gpt-5.2", name="GPT 5.2", provider="302ai", description="GPT 5.2"),
    LLMModelInfo(id="gpt-5.1", name="GPT 5.1", provider="302ai", description="GPT 5.1"),
    LLMModelInfo(id="gemini-3-pro-preview", name="Gemini 3.0 Pro", provider="302ai", description="Gemini 3.0 Pro Preview"),
    LLMModelInfo(id="gemini-2.5-pro", name="Gemini 2.5 Pro", provider="302ai", description="Gemini 2.5 Pro"),
    # DeepSeek 模型（可用）
    LLMModelInfo(id="deepseek-chat", name="DeepSeek Chat", provider="deepseek", description="DeepSeek 对话模型"),
]
