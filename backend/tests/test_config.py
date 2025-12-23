"""
测试配置加载
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.config import settings

print("=" * 60)
print("配置测试")
print("=" * 60)

print("\n【LLM 配置】")
print(f"OPENAI_API_KEY: {settings.openai_api_key[:20] if settings.openai_api_key else 'None'}...")
print(f"OPENAI_API_BASE: {settings.openai_api_base}")
print(f"DEFAULT_MODEL: {settings.default_model}")

print("\n【DeepSeek 配置】")
print(f"DEEPSEEK_API_KEY: {settings.deepseek_api_key[:20] if settings.deepseek_api_key else 'None'}...")
print(f"DEEPSEEK_API_BASE: {settings.deepseek_api_base}")

print("\n【Embedding 配置】")
print(f"QWEN_API_KEY: {settings.qwen_api_key[:20] if settings.qwen_api_key else 'None'}...")
print(f"QWEN_API_BASE: {settings.qwen_api_base}")
print(f"EMBEDDING_MODEL: {settings.embedding_model}")

print("\n" + "=" * 60)
print("配置加载完成")
print("=" * 60)
