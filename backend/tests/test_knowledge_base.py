"""
知识库功能测试脚本
"""
import asyncio
import requests
import os
from pathlib import Path

# API 配置
BASE_URL = "http://localhost:8000/api"
USERNAME = "test_user"
PASSWORD = "test_password"
EMAIL = "test@example.com"

# 全局变量
access_token = None
kb_id = None


def register_user():
    """注册用户"""
    print("\n1️⃣ 注册用户...")
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "username": USERNAME,
            "email": EMAIL,
            "password": PASSWORD
        }
    )
    if response.status_code == 201:
        print("✅ 用户注册成功")
        return True
    elif response.status_code == 400:
        print("ℹ️ 用户已存在，跳过注册")
        return True
    else:
        print(f"❌ 注册失败: {response.text}")
        return False


def login():
    """登录获取 token"""
    global access_token
    print("\n2️⃣ 用户登录...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": USERNAME,
            "password": PASSWORD
        }
    )
    if response.status_code == 200:
        data = response.json()
        access_token = data["access_token"]
        print(f"✅ 登录成功，Token: {access_token[:20]}...")
        return True
    else:
        print(f"❌ 登录失败: {response.text}")
        return False


def create_knowledge_base():
    """创建知识库"""
    global kb_id
    print("\n3️⃣ 创建知识库...")
    response = requests.post(
        f"{BASE_URL}/knowledge-bases",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "name": "测试知识库",
            "description": "这是一个用于测试的知识库"
        }
    )
    if response.status_code == 201:
        data = response.json()
        kb_id = data["id"]
        print(f"✅ 知识库创建成功，ID: {kb_id}")
        print(f"   名称: {data['name']}")
        print(f"   工作目录: {data['working_dir']}")
        return True
    else:
        print(f"❌ 创建失败: {response.text}")
        return False


def list_knowledge_bases():
    """列出知识库"""
    print("\n4️⃣ 列出知识库...")
    response = requests.get(
        f"{BASE_URL}/knowledge-bases",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 共有 {len(data)} 个知识库:")
        for kb in data:
            print(f"   - ID: {kb['id']}, 名称: {kb['name']}, 文件数: {kb['file_count']}")
        return True
    else:
        print(f"❌ 获取失败: {response.text}")
        return False


def upload_file():
    """上传文件"""
    print("\n5️⃣ 上传文件...")
    
    # 创建测试文本文件
    test_file_path = "test_document.txt"
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write("""
《西游记》是中国古典四大名著之一，作者是明代的吴承恩。
书主要描写了唐僧（玄奘）、孙悟空、猪八戒、沙僧师徒四人去西天（天竺）取经的故事。
孙悟空本是花果山的一只石猴，后大闹天宫，被如来佛祖压在五行山下。
五百年后，唐僧路过五行山，救出孙悟空，收其为大徒弟。
猪八戒原是天蓬元帅，因触犯天条被贬下凡，后在高老庄被唐僧收为二徒弟。
沙僧原是卷帘大将，在流沙河被收为三徒弟。
师徒四人历经九九八十一难，终于取得真经。
        """)
    
    try:
        with open(test_file_path, "rb") as f:
            response = requests.post(
                f"{BASE_URL}/knowledge-bases/{kb_id}/files",
                headers={"Authorization": f"Bearer {access_token}"},
                files={"file": (test_file_path, f, "text/plain")}
            )
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ 文件上传成功")
            print(f"   文件名: {data['original_filename']}")
            print(f"   大小: {data['file_size']} 字节")
            print(f"   状态: {data['status']}")
            print(f"   任务ID: {data['task_id']}")
            return True
        else:
            print(f"❌ 上传失败: {response.text}")
            return False
    finally:
        # 清理测试文件
        if os.path.exists(test_file_path):
            os.remove(test_file_path)


def check_file_status():
    """检查文件处理状态"""
    print("\n6️⃣ 检查文件处理状态...")
    print("⏳ 等待文件处理（可能需要几秒钟）...")
    
    import time
    max_retries = 30
    for i in range(max_retries):
        response = requests.get(
            f"{BASE_URL}/knowledge-bases/{kb_id}/files",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            files = response.json()
            if files:
                file = files[0]
                status = file['status']
                print(f"   [{i+1}/{max_retries}] 状态: {status}")
                
                if status == "completed":
                    print(f"✅ 文件处理完成")
                    return True
                elif status == "failed":
                    print(f"❌ 文件处理失败: {file.get('error_message', '未知错误')}")
                    return False
        
        time.sleep(2)
    
    print("⚠️ 超时：文件处理时间过长")
    return False


def query_knowledge_base():
    """查询知识库"""
    print("\n7️⃣ 查询知识库...")
    
    queries = [
        "请简述孙悟空的经历",
        "唐僧有几个徒弟？他们分别是谁？",
        "师徒四人经历了多少难？"
    ]
    
    for query in queries:
        print(f"\n   问题: {query}")
        response = requests.post(
            f"{BASE_URL}/knowledge-bases/{kb_id}/query",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "query": query,
                "mode": "mix",
                "top_k": 5
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   回答: {data['answer'][:200]}...")
        else:
            print(f"   ❌ 查询失败: {response.text}")
    
    return True


def cleanup():
    """清理测试数据"""
    print("\n8️⃣ 清理测试数据...")
    if kb_id:
        response = requests.delete(
            f"{BASE_URL}/knowledge-bases/{kb_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if response.status_code == 204:
            print("✅ 知识库已删除")
        else:
            print(f"⚠️ 删除失败: {response.text}")


def main():
    """主函数"""
    print("="*60)
    print("知识库功能测试")
    print("="*60)
    
    try:
        # 1. 注册用户
        if not register_user():
            return
        
        # 2. 登录
        if not login():
            return
        
        # 3. 创建知识库
        if not create_knowledge_base():
            return
        
        # 4. 列出知识库
        list_knowledge_bases()
        
        # 5. 上传文件
        if not upload_file():
            return
        
        # 6. 检查文件处理状态
        if not check_file_status():
            print("⚠️ 文件处理未完成，但继续测试查询功能")
        
        # 7. 查询知识库
        query_knowledge_base()
        
        print("\n" + "="*60)
        print("✅ 测试完成！")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被中断")
    except Exception as e:
        print(f"\n\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理
        # cleanup()  # 取消注释以自动清理测试数据
        pass


if __name__ == "__main__":
    main()
