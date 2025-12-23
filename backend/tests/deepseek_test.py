"""
测试 DeepSeek API
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.ai.llm_manager import llm_manager


async def test_deepseek_chat():
    """测试 DeepSeek Chat"""
    print("=" * 50)
    print("测试 DeepSeek Chat")
    print("=" * 50)
    
    # 优先使用 DeepSeek 专用配置，否则使用通用配置
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
    
    messages = [
        {"role": "system", "content": "你是一个有帮助的AI助手。"},
        {"role": "user", "content": "用一句话介绍你自己。"}
    ]
    
    try:
        print("\n1. 测试普通对话...")
        response = await llm_manager.chat_completion(
            messages=messages,
            model="deepseek-chat",
            api_key=api_key,
            base_url=base_url,
            max_tokens=100
        )
        content = response.choices[0].message.content
        print(f"   回复: {content}")
        
        print("\n2. 测试流式对话...")
        print("   回复: ", end="", flush=True)
        async for chunk in llm_manager.chat_completion_stream(
            messages=messages,
            model="deepseek-chat",
            api_key=api_key,
            base_url=base_url,
            max_tokens=100
        ):
            print(chunk, end="", flush=True)
        print()
        
        print("\n✅ DeepSeek 测试成功!")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")


async def test_deepseek_coder():
    """测试 DeepSeek Coder"""
    print("\n" + "=" * 50)
    print("测试 DeepSeek Coder")
    print("=" * 50)
    
    # 优先使用 DeepSeek 专用配置，否则使用通用配置
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
    
    messages = [
        {"role": "user", "content": "写一个 Python 函数计算斐波那契数列"}
    ]
    
    try:
        print("\n测试代码生成...")
        response = await llm_manager.chat_completion(
            messages=messages,
            model="deepseek-coder",
            api_key=api_key,
            base_url=base_url,
            max_tokens=200
        )
        content = response.choices[0].message.content
        print(f"   回复:\n{content}")
        
        print("\n✅ DeepSeek Coder 测试成功!")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")


async def main():
    await test_deepseek_chat()
    await test_deepseek_coder()
    
    print("\n" + "=" * 50)
    print("所有测试完成!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
