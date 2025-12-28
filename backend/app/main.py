"""
FastAPI 应用入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.config import settings
from app.core.database import init_db, close_db
from app.core.redis_client import redis_client
from app.api import auth, users, chat, knowledge_base, llm_config, memory, diagram, mcp_tool


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("\n" + "="*50)
    print("🚀 正在启动应用...")
    print("="*50)
    
    try:
        # 初始化数据库
        print("📊 初始化数据库...")
        await init_db()
        print("✅ 数据库初始化完成")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise
    
    try:
        # 连接 Redis
        print("🔌 连接 Redis...")
        await redis_client.connect()
        print("✅ Redis 连接成功")
    except Exception as e:
        print(f"❌ Redis 连接失败: {e}")
        raise
    
    print("="*50)
    print("✨ 应用启动完成！")
    print("="*50 + "\n")
    
    yield
    
    # 关闭时执行
    print("\n" + "="*50)
    print("🛑 正在关闭应用...")
    print("="*50)
    
    try:
        # 关闭 Redis
        await redis_client.close()
        print("✅ Redis 连接已关闭")
    except Exception as e:
        print(f"⚠️ Redis 关闭警告: {e}")
    
    try:
        # 关闭数据库
        await close_db()
        print("✅ 数据库连接已关闭")
    except Exception as e:
        print(f"⚠️ 数据库关闭警告: {e}")
    
    print("="*50)
    print("👋 应用已安全关闭")
    print("="*50 + "\n")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI 知识库系统 - 基于 LangGraph 的智能对话和知识管理平台",
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求验证错误处理器 - 打印详细错误信息
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """捕获请求验证错误并打印详细信息"""
    print(f"\n{'='*50}")
    print(f"❌ 请求验证失败: {request.url}")
    print(f"   方法: {request.method}")
    print(f"   错误详情:")
    for error in exc.errors():
        print(f"   - 字段: {error.get('loc')}")
        print(f"     类型: {error.get('type')}")
        print(f"     消息: {error.get('msg')}")
        print(f"     输入: {error.get('input')}")
    print(f"{'='*50}\n")
    
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

# 注册路由
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(chat.router, prefix=settings.api_prefix)
app.include_router(knowledge_base.router, prefix=settings.api_prefix)
app.include_router(llm_config.router, prefix=settings.api_prefix)
app.include_router(memory.router, prefix=settings.api_prefix)
app.include_router(diagram.router, prefix=settings.api_prefix)
app.include_router(mcp_tool.router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Welcome to LiuYun-Know API",
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )

