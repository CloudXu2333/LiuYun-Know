"""
FastAPI 应用入口
"""
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.config import settings
from app.core.database import init_db, close_db
from app.core.redis_client import redis_client
from app.api import auth, users, chat, knowledge_base, llm_config, memory, diagram, mcp_tool

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


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

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求的详细信息"""
    start_time = time.time()

    # 记录请求信息
    logger.info(f"📥 收到请求")
    logger.info(f"   方法: {request.method}")
    logger.info(f"   路径: {request.url.path}")
    logger.info(f"   客户端: {request.client.host if request.client else 'unknown'}")

    # 处理请求
    try:
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        # 记录响应信息
        logger.info(f"📤 响应状态: {response.status_code}")
        logger.info(f"   处理时间: {process_time:.3f}秒")

        # 添加处理时间到响应头
        response.headers["X-Process-Time"] = str(process_time)
        return response

    except Exception as e:
        # 记录异常
        process_time = time.time() - start_time
        logger.error(f"💥 请求处理异常")
        logger.error(f"   路径: {request.url.path}")
        logger.error(f"   异常: {str(e)}")
        logger.error(f"   处理时间: {process_time:.3f}秒")
        raise

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
        port=8001,  # 修改为 8001 避免与 VSCode 调试器冲突
        reload=settings.debug,
    )

