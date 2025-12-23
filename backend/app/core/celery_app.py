"""
Celery 应用配置
"""
from celery import Celery
from app.config import settings

# 创建 Celery 应用
celery_app = Celery(
    "liuyun_know",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.file_processing"]
)

# Celery 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
    task_soft_time_limit=3300,  # 55分钟软超时
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)
