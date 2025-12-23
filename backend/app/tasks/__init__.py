"""
Celery 任务包
"""
from app.tasks.file_processing import process_file_task

__all__ = ["process_file_task"]
