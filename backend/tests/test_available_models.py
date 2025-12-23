"""
测试所有可用的 LLM 模型
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.ai.llm_manager import llm_manager


# 从环境变量读取配置
API_302_KEY = os.getenv("OPENAI_API_KEY")
API_302_BASE = os.getenv("OPENAI_API_BASE", "https://api.302.ai/v1")

# DeepSeek 配置（优先使用专用配置）
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
DEEPSEEK_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")


async def test_model(name, model, api_key, base_url):
    """测试单个模型"""
    print(f"\n测试 {name}...")
    messages = [{"role": "user", "content": "说'你好'"}]
    
    try:
        response = await llm_manager.chat_completion(
            messages=messages,
            model=model,
            api_key=api_key,
            base_url=base_url,
            max_tokens=50
        )
        content = response.choices[0].message.content
        print(f"  ✅ {name}: {content[:50]}...")
        return True
    except Exception as e:
        print(f"  ❌ {name}: {str(e)[:100]}")
        return False


async def main():
    print("=" * 60)
    print("测试所有可用的 LLM 模型")
    print("=" * 60)
    
    results = {}
    
    # 测试 302.AI 模型
    print("\n【302.AI 模型】")
    models_302 = [
        ("Claude 4.5 Sonnet", "claude-sonnet-4-5-20250929"),
        ("Claude 4.5 Opus", "claude-opus-4-5-20251101"),
        ("GPT 5.2", "gpt-5.2"),
        ("GPT 5.1", "gpt-5.1"),
        ("Gemini 3.0 Pro", "gemini-3-pro-preview"),
        ("Gemini 2.5 Pro", "gemini-2.5-pro"),
    ]
    
    for name, model in models_302:
        results[name] = await test_model(name, model, API_302_KEY, API_302_BASE)
    
    # 测试 DeepSeek 模型
    print("\n【DeepSeek 模型】")
    results["DeepSeek Chat"] = await test_model(
        "DeepSeek Chat", "deepseek-chat", DEEPSEEK_KEY, DEEPSEEK_BASE
    )
    
    # 统计结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"\n成功: {success_count}/{total_count}")
    print("\n可用模型:")
    for name, success in results.items():
        if success:
            print(f"  ✅ {name}")
    
    print("\n不可用模型:")
    for name, success in results.items():
        if not success:
            print(f"  ❌ {name}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
