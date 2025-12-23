import os
import sys
import asyncio
import numpy as np
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc
from lightrag.kg.shared_storage import initialize_pipeline_status

# Check for DeepSeek API Key
if "DEEPSEEK_API_KEY" not in os.environ:
    print("Warning: DEEPSEEK_API_KEY environment variable is not set.")
    print("Please set it before running this script, or the API calls will fail.")
    print("Example: set DEEPSEEK_API_KEY=sk-...")

# Check for DashScope (Qwen) API Key
if "DASHSCOPE_API_KEY" not in os.environ:
    print("Warning: DASHSCOPE_API_KEY environment variable is not set.")
    print("Please set it before running this script, or the API calls will fail.")
    print("Example: set DASHSCOPE_API_KEY=sk-...")

# Define the working directory
WORKING_DIR = "./rag_storage"

# Create the directory if it doesn't exist
if not os.path.exists(WORKING_DIR):
    os.makedirs(WORKING_DIR)

print(f"Initializing LightRAG in {WORKING_DIR}...")

# 定义 DeepSeek 的 LLM 函数
async def deepseek_llm(prompt, system_prompt=None, history_messages=[], **kwargs):
    return await openai_complete_if_cache(
        model="deepseek-chat",
        prompt=prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        api_key=os.environ.get("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        **kwargs
    )

async def qwen_embedding(texts: list[str]) -> np.ndarray:
    return await openai_embed(
        texts,
        model="text-embedding-v3",
        api_key=os.environ.get("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )


embedding_func = EmbeddingFunc(embedding_dim=1024, func=qwen_embedding)

async def main():
    try:
        # Initialize LightRAG with DeepSeek
        rag = LightRAG(
            working_dir=WORKING_DIR,
            graph_storage="Neo4JStorage",
            llm_model_func=deepseek_llm,
            embedding_func=embedding_func,
            addon_params={
                "language": "Chinese",
            },
        )
        
        # 显式初始化存储和管道状态 (LightRAG 新版本要求)
        # 必须先调用 initialize_storages 初始化所有数据库文件
        await rag.initialize_storages()
        # 然后初始化 pipeline 状态
        await initialize_pipeline_status()
        
    except Exception as e:
        print(f"Failed to initialize LightRAG: {e}")
        return

    # 示例文本内容 (关于西游记的简介，适合展示实体和关系)
    text_content = """
    《西游记》是中国古典四大名著之一，作者是明代的吴承恩。
    书主要描写了唐僧（玄奘）、孙悟空、猪八戒、沙僧师徒四人去西天（天竺）取经的故事。
    孙悟空本是花果山的一只石猴，后大闹天宫，被如来佛祖压在五行山下。
    五百年后，唐僧路过五行山，救出孙悟空，收其为大徒弟。
    猪八戒原是天蓬元帅，因触犯天条被贬下凡，后在高老庄被唐僧收为二徒弟。
    沙僧原是卷帘大将，在流沙河被收为三徒弟。
    师徒四人历经九九八十一难，终于取得真经。
    """

    # 插入数据
    print("\n正在向 LightRAG 插入数据 (构建知识图谱)...")
    try:
        # 使用异步插入方法
        await rag.ainsert(text_content)
        print("数据插入完成。")
    except Exception as e:
        print(f"插入数据时出错: {e}")

    # 查询示例
    query_text = "请简述孙悟空的经历以及他和唐僧的关系。"

    print(f"\n当前查询问题: '{query_text}'")

    # 1. Naive Mode (朴素模式)
    # 这种模式类似传统 RAG，主要依靠字面匹配和向量相似度。
    print("\n--- 模式 1: Naive (朴素模式 - 类似传统 RAG) ---")
    try:
        # 使用异步查询方法
        result_naive = await rag.aquery(query_text, param=QueryParam(mode="naive"))
        print("回答结果:")
        print(result_naive)
    except Exception as e:
        print(f"Naive 模式查询出错: {e}")

    # 2. Mix Mode (混合模式 - 推荐)
    # 这种模式结合了知识图谱（实体关系）和向量检索。
    # 它能更好地理解 "孙悟空" 和 "唐僧" 之间的 "师徒" 关系，即使原文中这两个词距离较远。
    print("\n--- 模式 2: Mix (混合模式 - 结合知识图谱 + 向量) ---")
    try:
        # 使用异步查询方法
        result_mix = await rag.aquery(query_text, param=QueryParam(mode="mix"))
        print("回答结果:")
        print(result_mix)
    except Exception as e:
        print(f"Mix 模式查询出错: {e}")

    print("\n演示结束。")

if __name__ == "__main__":
    asyncio.run(main())
