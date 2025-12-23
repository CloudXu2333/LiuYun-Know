"""
数据库连接和会话管理
"""
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings


def ensure_database_dir():
    """确保数据库目录存在"""
    print("📁 检查数据库目录...")
    # 从数据库 URL 中提取文件路径
    db_url = settings.database_url
    print(f"   数据库 URL: {db_url}")
    
    if "sqlite" in db_url:
        # 提取 SQLite 文件路径
        # 格式: sqlite+aiosqlite:///./data/sqlite/liuyun_know.db
        file_path = db_url.split("///")[-1]
        print(f"   文件路径: {file_path}")
        
        # 如果是相对路径，转换为绝对路径
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.getcwd(), file_path)
            print(f"   绝对路径: {file_path}")
        
        # 创建目录
        db_dir = os.path.dirname(file_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"✅ 已创建数据库目录: {db_dir}")
        else:
            print(f"✅ 数据库目录已存在: {db_dir}")


# 确保数据库目录存在
print("="*50)
ensure_database_dir()
print("="*50)

# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    # SQLite 优化配置
    connect_args={
        "check_same_thread": False,
        "timeout": 30,  # 增加超时时间到 30 秒
    } if "sqlite" in settings.database_url else {},
    pool_pre_ping=True,  # 连接前检查连接是否有效
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 创建基类
Base = declarative_base()


async def get_db() -> AsyncSession:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库"""
    # 导入所有模型以确保它们被注册到 Base.metadata
    from app.models import User, Conversation, Message, KnowledgeBase, KnowledgeFile, UserLLMConfig, LongTermMemory
    
    async with engine.begin() as conn:
        # 创建表
        await conn.run_sync(Base.metadata.create_all)
        
        # 如果是 SQLite，启用 WAL 模式以提高并发性能
        if "sqlite" in settings.database_url:
            await conn.exec_driver_sql("PRAGMA journal_mode=WAL")
            await conn.exec_driver_sql("PRAGMA synchronous=NORMAL")
            await conn.exec_driver_sql("PRAGMA cache_size=10000")
            print("✅ SQLite 已启用 WAL 模式，提高并发性能")


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()

