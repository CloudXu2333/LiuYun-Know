from minio import Minio
from minio.error import S3Error
import os
import sys

# MinIO 配置信息
MINIO_ENDPOINT = "localhost:9091"  # MinIO API 地址 (注意不是 Console 地址)
MINIO_ACCESS_KEY = "minioadmin"    # Access Key (默认)
MINIO_SECRET_KEY = "minioadmin"    # Secret Key (默认)
BUCKET_NAME = "test-bucket"        # 桶名称

def get_minio_client():
    """创建并返回 MinIO 客户端"""
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False  # 如果使用 HTTPS，请设置为 True
    )
    return client

def create_bucket_if_not_exists(client, bucket_name):
    """如果桶不存在，则创建桶"""
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            print(f"Bucket '{bucket_name}' created successfully.")
        else:
            print(f"Bucket '{bucket_name}' already exists.")
    except S3Error as e:
        print(f"Error creating bucket: {e}")

def upload_file(client, bucket_name, file_path, object_name=None):
    """上传文件到 MinIO"""
    if object_name is None:
        object_name = os.path.basename(file_path)
    
    try:
        client.fput_object(bucket_name, object_name, file_path)
        print(f"'{file_path}' is successfully uploaded as '{object_name}' to bucket '{bucket_name}'.")
        return True
    except S3Error as e:
        print(f"Error uploading file: {e}")
        return False

def download_file(client, bucket_name, object_name, file_path):
    """从 MinIO 下载文件"""
    try:
        client.fget_object(bucket_name, object_name, file_path)
        print(f"'{object_name}' is successfully downloaded to '{file_path}'.")
    except S3Error as e:
        print(f"Error downloading file: {e}")

def list_objects(client, bucket_name):
    """列出桶中的对象"""
    try:
        objects = client.list_objects(bucket_name)
        print(f"Objects in bucket '{bucket_name}':")
        for obj in objects:
            print(f" - {obj.object_name} (size: {obj.size})")
    except S3Error as e:
        print(f"Error listing objects: {e}")

def main():
    # 1. 初始化客户端
    client = get_minio_client()
    
    # 2. 确保存储桶存在
    create_bucket_if_not_exists(client, BUCKET_NAME)
    
    # 3. 示例：上传一个文件（这里使用脚本自身作为测试文件）
    test_file = __file__
    object_name = "scripts/" + os.path.basename(test_file)
    
    print("\n--- Uploading ---")
    if upload_file(client, BUCKET_NAME, test_file, object_name):
        
        # 4. 列出文件
        print("\n--- Listing ---")
        list_objects(client, BUCKET_NAME)
        
        # 5. 下载文件
        print("\n--- Downloading ---")
        download_path = "downloaded_" + os.path.basename(test_file)
        download_file(client, BUCKET_NAME, object_name, download_path)
        
        # 清理下载的测试文件
        if os.path.exists(download_path):
            os.remove(download_path)
            print(f"Cleaned up local file: {download_path}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        print("Tip: Make sure MinIO server is running and `minio` library is installed (`pip install minio`).")
