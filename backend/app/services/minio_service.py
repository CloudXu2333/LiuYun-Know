"""
MinIO 对象存储服务
"""
import os
from typing import BinaryIO
from minio import Minio
from minio.error import S3Error
from app.config import settings


class MinIOService:
    """MinIO 服务类"""
    
    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        self.bucket_name = settings.minio_bucket_name
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """确保存储桶存在"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"✅ MinIO bucket '{self.bucket_name}' created")
        except S3Error as e:
            print(f"❌ MinIO bucket error: {e}")
            raise
    
    def upload_file(self, file_data: BinaryIO, object_name: str, content_type: str = "application/octet-stream") -> str:
        """
        上传文件到 MinIO
        
        Args:
            file_data: 文件数据流
            object_name: 对象名称（路径）
            content_type: 文件类型
            
        Returns:
            object_name: 上传后的对象路径
        """
        try:
            # 获取文件大小
            file_data.seek(0, os.SEEK_END)
            file_size = file_data.tell()
            file_data.seek(0)
            
            self.client.put_object(
                self.bucket_name,
                object_name,
                file_data,
                length=file_size,
                content_type=content_type
            )
            return object_name
        except S3Error as e:
            print(f"❌ MinIO upload error: {e}")
            raise
    
    def download_file(self, object_name: str, file_path: str):
        """
        从 MinIO 下载文件
        
        Args:
            object_name: 对象名称（路径）
            file_path: 本地保存路径
        """
        try:
            self.client.fget_object(self.bucket_name, object_name, file_path)
        except S3Error as e:
            print(f"❌ MinIO download error: {e}")
            raise
    
    def get_file_stream(self, object_name: str):
        """
        获取文件流
        
        Args:
            object_name: 对象名称（路径）
            
        Returns:
            文件流对象
        """
        try:
            return self.client.get_object(self.bucket_name, object_name)
        except S3Error as e:
            print(f"❌ MinIO get stream error: {e}")
            raise
    
    def delete_file(self, object_name: str):
        """
        删除文件
        
        Args:
            object_name: 对象名称（路径）
        """
        try:
            self.client.remove_object(self.bucket_name, object_name)
        except S3Error as e:
            print(f"❌ MinIO delete error: {e}")
            raise
    
    def list_objects(self, prefix: str = ""):
        """
        列出对象
        
        Args:
            prefix: 对象前缀
            
        Returns:
            对象列表
        """
        try:
            return self.client.list_objects(self.bucket_name, prefix=prefix, recursive=True)
        except S3Error as e:
            print(f"❌ MinIO list error: {e}")
            raise
    
    def get_presigned_url(self, object_name: str, expires_hours: int = 1) -> str:
        """
        获取预签名URL用于文件预览/下载
        
        Args:
            object_name: 对象名称（路径）
            expires_hours: URL有效期（小时）
            
        Returns:
            预签名URL
        """
        from datetime import timedelta
        try:
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=timedelta(hours=expires_hours)
            )
            return url
        except S3Error as e:
            print(f"❌ MinIO presigned URL error: {e}")
            raise


# 创建全局实例
minio_service = MinIOService()
