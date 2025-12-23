"""
检查 Celery 配置和连接
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

def check_redis():
    """检查 Redis 连接"""
    print("1️⃣ 检查 Redis 连接...")
    try:
        import redis
        from app.config import settings
        
        # 解析 Redis URL
        if settings.celery_broker_url.startswith('redis://'):
            parts = settings.celery_broker_url.replace('redis://', '').split('/')
            host_port = parts[0].split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 6379
            db = int(parts[1]) if len(parts) > 1 else 0
            
            r = redis.Redis(host=host, port=port, db=db)
            r.ping()
            print(f"✅ Redis 连接成功: {host}:{port}/{db}")
            return True
        else:
            print("❌ 无法解析 Redis URL")
            return False
    except Exception as e:
        print(f"❌ Redis 连接失败: {e}")
        return False


def check_celery_app():
    """检查 Celery 应用"""
    print("\n2️⃣ 检查 Celery 应用...")
    try:
        from app.core.celery_app import celery_app
        print(f"✅ Celery 应用加载成功")
        print(f"   Broker: {celery_app.conf.broker_url}")
        print(f"   Backend: {celery_app.conf.result_backend}")
        return True
    except Exception as e:
        print(f"❌ Celery 应用加载失败: {e}")
        return False


def check_tasks():
    """检查任务注册"""
    print("\n3️⃣ 检查任务注册...")
    try:
        from app.core.celery_app import celery_app
        tasks = list(celery_app.tasks.keys())
        
        print(f"✅ 已注册 {len(tasks)} 个任务:")
        for task in tasks:
            if not task.startswith('celery.'):
                print(f"   - {task}")
        
        # 检查我们的任务
        if 'process_file' in tasks or 'app.tasks.file_processing.process_file_task' in tasks:
            print("✅ 文件处理任务已注册")
            return True
        else:
            print("⚠️ 文件处理任务未找到")
            return False
    except Exception as e:
        print(f"❌ 检查任务失败: {e}")
        return False


def check_worker():
    """检查 Worker 状态"""
    print("\n4️⃣ 检查 Worker 状态...")
    try:
        from app.core.celery_app import celery_app
        
        # 检查活跃的 worker
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            print(f"✅ 发现 {len(active_workers)} 个活跃的 Worker:")
            for worker_name in active_workers.keys():
                print(f"   - {worker_name}")
            return True
        else:
            print("⚠️ 没有发现活跃的 Worker")
            print("\n请启动 Celery Worker:")
            print("   celery -A app.core.celery_app worker --loglevel=info --pool=solo")
            return False
    except Exception as e:
        print(f"❌ 检查 Worker 失败: {e}")
        return False


def check_database():
    """检查数据库连接"""
    print("\n5️⃣ 检查数据库连接...")
    try:
        import asyncio
        from app.core.database import AsyncSessionLocal
        from app.models.knowledge_base import KnowledgeFile
        from sqlalchemy import select
        
        async def test_db():
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(KnowledgeFile).limit(1))
                return result.scalar_one_or_none()
        
        asyncio.run(test_db())
        print("✅ 数据库连接成功")
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


def main():
    print("="*60)
    print("Celery 配置检查")
    print("="*60)
    
    results = []
    results.append(("Redis", check_redis()))
    results.append(("Celery App", check_celery_app()))
    results.append(("Tasks", check_tasks()))
    results.append(("Worker", check_worker()))
    results.append(("Database", check_database()))
    
    print("\n" + "="*60)
    print("检查结果汇总")
    print("="*60)
    
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")
    
    all_passed = all(success for _, success in results)
    
    if all_passed:
        print("\n🎉 所有检查通过！Celery 配置正常。")
    else:
        print("\n⚠️ 部分检查失败，请根据上面的提示修复问题。")
    
    print("="*60)


if __name__ == "__main__":
    main()
