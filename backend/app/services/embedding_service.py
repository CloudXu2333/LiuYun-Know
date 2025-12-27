"""
Embedding 服务 - 使用千问 Embedding 模型生成文本向量
"""
import numpy as np
from typing import List, Optional
from openai import AsyncOpenAI
from app.config import settings


class EmbeddingService:
    """Embedding 服务（使用千问 text-embedding-v4）"""
    
    def __init__(self):
        self._client: Optional[AsyncOpenAI] = None
        self.model = settings.embedding_model  # text-embedding-v4
        self.dimension = 1024  # text-embedding-v4 的维度
    
    def _get_client(self) -> AsyncOpenAI:
        """获取或创建 OpenAI 客户端"""
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=settings.qwen_api_key,
                base_url=settings.qwen_api_base
            )
        return self._client
    
    async def get_embedding(self, text: str) -> List[float]:
        """
        获取单个文本的 embedding 向量
        
        Args:
            text: 输入文本
            
        Returns:
            embedding 向量（1024维）
        """
        if not text or not text.strip():
            return [0.0] * self.dimension
        
        try:
            client = self._get_client()
            response = await client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[Embedding] 获取 embedding 失败: {e}")
            return [0.0] * self.dimension
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        批量获取文本的 embedding 向量
        
        Args:
            texts: 输入文本列表
            
        Returns:
            embedding 向量列表
        """
        if not texts:
            return []
        
        # 过滤空文本
        valid_texts = [t if t and t.strip() else " " for t in texts]
        
        try:
            client = self._get_client()
            response = await client.embeddings.create(
                model=self.model,
                input=valid_texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"[Embedding] 批量获取 embedding 失败: {e}")
            return [[0.0] * self.dimension for _ in texts]
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            相似度分数 (0-1)
        """
        if not vec1 or not vec2:
            return 0.0
        
        arr1 = np.array(vec1)
        arr2 = np.array(vec2)
        
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(arr1, arr2) / (norm1 * norm2))
    
    def rank_by_similarity(
        self,
        query_embedding: List[float],
        embeddings: List[List[float]],
        top_k: int = 5
    ) -> List[tuple]:
        """
        根据相似度排序
        
        Args:
            query_embedding: 查询向量
            embeddings: 候选向量列表
            top_k: 返回前 k 个
            
        Returns:
            [(index, similarity), ...] 按相似度降序排列
        """
        scores = []
        for idx, emb in enumerate(embeddings):
            sim = self.cosine_similarity(query_embedding, emb)
            scores.append((idx, sim))
        
        # 按相似度降序排序
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[:top_k]


# 创建全局实例
embedding_service = EmbeddingService()
