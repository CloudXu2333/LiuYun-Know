"""
Celery Worker 启动脚本
"""
from app.core.celery_app import celery_app

# 导入任务模块以注册任务
from app.tasks import file_processing

if __name__ == "__main__":
    celery_app.start()
