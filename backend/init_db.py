"""
数据库初始化脚本
- 创建所有表
- 插入默认管理员账号 admin/admin
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from app.core.database import engine, AsyncSessionLocal, Base
from app.core.security import get_password_hash
from app.models.user import User


async def init_database():
    """初始化数据库"""
    print("🚀 开始初始化数据库...")
    
    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库表创建完成")
    
    # 创建默认管理员账号
    async with AsyncSessionLocal() as db:
        # 检查是否已存在 admin 用户
        result = await db.execute(
            select(User).where(User.username == "admin")
        )
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print("ℹ️  管理员账号已存在，跳过创建")
        else:
            admin_user = User(
                username="admin",
                email="admin@liuyun.local",
                hashed_password=get_password_hash("admin"),
                is_active=True,
                is_superuser=True
            )
            db.add(admin_user)
            await db.commit()
            print("✅ 默认管理员账号创建成功")
            print("   用户名: admin")
            print("   密码: admin")
            print("   ⚠️  请登录后立即修改密码！")
    
    print("\n🎉 数据库初始化完成！")


if __name__ == "__main__":
    asyncio.run(init_database())
