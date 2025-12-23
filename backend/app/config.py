"""
应用配置管理
"""
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用配置
    app_name: str = Field(default="LiuYun-Know", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    api_prefix: str = Field(default="/api", alias="API_PREFIX")
    
    # 安全配置
    secret_key: str = Field(..., alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # 数据库配置
    database_url: str = Field(..., alias="DATABASE_URL")
    
    # Redis 配置
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: str = Field(default="", alias="REDIS_PASSWORD")
    
    # MinIO 配置
    minio_endpoint: str = Field(default="localhost:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", alias="MINIO_SECRET_KEY")
    minio_bucket_name: str = Field(default="liuyun-know", alias="MINIO_BUCKET_NAME")
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")
    
    # Chroma 配置
    chroma_host: str = Field(default="localhost", alias="CHROMA_HOST")
    chroma_port: int = Field(default=8000, alias="CHROMA_PORT")
    chroma_persist_directory: str = Field(default="./data/chroma", alias="CHROMA_PERSIST_DIRECTORY")
    
    # Neo4j 配置
    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USERNAME")  # LightRAG 使用 NEO4J_USERNAME
    neo4j_password: str = Field(default="password", alias="NEO4J_PASSWORD")
    
    # Celery 配置
    celery_broker_url: str = Field(default="redis://localhost:6379/1", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", alias="CELERY_RESULT_BACKEND")
    
    # LLM API 配置（对话模型）
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_api_base: str = Field(default="https://api.openai.com/v1", alias="OPENAI_API_BASE")
    default_model: str = Field(default="gpt-3.5-turbo", alias="DEFAULT_MODEL")
    
    # DeepSeek API 配置（可选）
    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")
    deepseek_api_base: str = Field(default="https://api.deepseek.com", alias="DEEPSEEK_API_BASE")
    
    # Embedding 模型配置（专用千问）
    qwen_api_key: str = Field(default="", alias="QWEN_API_KEY")
    qwen_api_base: str = Field(default="https://dashscope.aliyuncs.com/compatible-mode/v1", alias="QWEN_API_BASE")
    embedding_model: str = Field(default="text-embedding-v4", alias="EMBEDDING_MODEL")
    
    # Firecrawl API
    firecrawl_api_key: str = Field(default="", alias="FIRECRAWL_API_KEY")
    
    # Tavily API
    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")
    
    # Web Search 配置
    web_search_timeout: int = Field(default=180, alias="WEB_SEARCH_TIMEOUT")  # 搜索超时时间（秒），默认3分钟
    web_search_max_results: int = Field(default=10, alias="WEB_SEARCH_MAX_RESULTS")  # 每个搜索引擎最大结果数
    
    # PaddlePaddle OCR 配置
    use_gpu: bool = Field(default=False, alias="USE_GPU")
    ocr_lang: str = Field(default="ch", alias="OCR_LANG")
    
    # PaddleOCR API 配置
    paddleocr_api_url: str = Field(
        default="https://xbmbgatds3k3k5d5.aistudio-app.com/layout-parsing",
        alias="PADDLEOCR_API_URL"
    )
    paddleocr_token: str = Field(
        default="",
        alias="PADDLEOCR_TOKEN"
    )
    
    # LightRAG 配置
    lightrag_graph_storage: str = Field(
        default="Neo4JStorage",
        alias="LIGHTRAG_GRAPH_STORAGE"
    )
    
    # CORS 配置
    cors_origins: Union[List[str], str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        alias="CORS_ORIGINS"
    )
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """解析 CORS origins，支持逗号分隔的字符串或列表"""
        if isinstance(v, str):
            # 如果是字符串，按逗号分割
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 创建全局配置实例
print("⚙️ 正在加载配置...")
settings = Settings()
print(f"✅ 配置加载成功")
print(f"   - 应用名称: {settings.app_name}")
print(f"   - 调试模式: {settings.debug}")
print(f"   - 数据库: {'SQLite' if 'sqlite' in settings.database_url else '其他'}")
print(f"   - Redis: {settings.redis_host}:{settings.redis_port}")
print(f"   - 对话模型: {settings.default_model}")
print(f"   - Embedding 模型: {settings.embedding_model}")
print(f"   - 图存储: {settings.lightrag_graph_storage}")
print(f"   - DeepSeek API: {'已配置' if settings.deepseek_api_key else '未配置'}")

