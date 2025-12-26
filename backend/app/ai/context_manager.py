"""
上下文管理器
- 长期记忆：跨对话持久化，每次对话都会加载
- 短期记忆：当前对话的上下文，按 token 限制压缩
"""
import tiktoken
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.llm_manager import llm_manager


class ContextManager:
    """上下文管理器 - 整合长期记忆和短期记忆"""
    
    def __init__(self, max_context_tokens: int = 65536):
        """
        初始化上下文管理器
        
        Args:
            max_context_tokens: 最大上下文 token 数（默认 16k）
        """
        self.max_context_tokens = max_context_tokens
        self._encoder = None
    
    @property
    def encoder(self):
        """懒加载 tokenizer"""
        if self._encoder is None:
            try:
                self._encoder = tiktoken.get_encoding("cl100k_base")
            except Exception:
                self._encoder = None
        return self._encoder
    
    def count_tokens(self, text: str) -> int:
        """计算文本的 token 数"""
        if self.encoder:
            return len(self.encoder.encode(text))
        else:
            return len(text) // 3
    
    def count_message_tokens(self, message: Dict[str, str]) -> int:
        """计算单条消息的 token 数"""
        content_tokens = self.count_tokens(message.get("content", ""))
        return content_tokens + 4
    
    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """计算消息列表的总 token 数"""
        return sum(self.count_message_tokens(msg) for msg in messages)
    
    async def compress_messages(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        api_key: str = None,
        base_url: str = None
    ) -> Dict[str, str]:
        """压缩多条消息为一条摘要"""
        if not messages:
            return None
        
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in messages
        ])
        
        compress_prompt = f"""请将以下对话历史压缩成一段简洁的摘要，保留关键信息和上下文：

{conversation_text}

要求：
1. 保留用户的主要问题和意图
2. 保留 AI 回答的关键结论
3. 保留重要的事实和数据
4. 使用第三人称描述
5. 控制在 200 字以内

摘要："""
        
        try:
            response = await llm_manager.chat_completion(
                messages=[{"role": "user", "content": compress_prompt}],
                model=model or "deepseek-chat",
                api_key=api_key,
                base_url=base_url,
                max_tokens=300,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip()
            
            return {
                "role": "system",
                "content": f"[历史对话摘要]\n{summary}"
            }
        except Exception as e:
            print(f"⚠️ 压缩消息失败: {e}")
            return {
                "role": "system",
                "content": f"[历史对话摘要]\n用户之前询问了相关问题，AI 进行了回答。"
            }
    
    async def get_long_term_memories(
        self, 
        db: AsyncSession, 
        user_id: str,
        query_text: str = None,
        top_k: int = 5,
        threshold: int = 80
    ) -> tuple:
        """
        获取用户的长期记忆并格式化
        
        新逻辑：
        1. 核心记忆（priority >= threshold）→ 必定加载
        2. 普通记忆（priority < threshold）→ 向量检索 top_k 条相关的
        
        Args:
            db: 数据库会话
            user_id: 用户 ID
            query_text: 用户查询文本（用于向量检索普通记忆）
            top_k: 普通记忆检索数量
            threshold: 核心记忆优先级阈值
            
        Returns:
            (格式化的长期记忆字符串, 记忆列表, 核心记忆数量, 普通记忆数量)
        """
        from app.services.memory_service import memory_service
        
        # 获取核心记忆和普通记忆
        core_memories, normal_memories = await memory_service.get_memories_for_context(
            db=db,
            user_id=user_id,
            query_text=query_text,
            top_k=top_k,
            threshold=threshold
        )
        
        # 格式化记忆
        formatted = memory_service.format_memories_for_context(
            core_memories=core_memories,
            normal_memories=normal_memories
        )
        
        # 合并记忆列表用于前端显示
        all_memories = core_memories + normal_memories
        memory_list = [
            {
                "id": str(m.id),
                "title": m.title,
                "category": m.category,
                "content": m.content,
                "priority": m.priority,
                "is_core": m.priority >= threshold
            }
            for m in all_memories
        ]
        
        return formatted, memory_list, len(core_memories), len(normal_memories)
    
    async def build_context(
        self,
        system_prompt: str,
        history_messages: List[Dict[str, str]],
        current_query: str,
        max_tokens: int = None,
        model: str = None,
        api_key: str = None,
        base_url: str = None,
        db: AsyncSession = None,
        user_id: str = None,
        memory_top_k: int = 5,
        core_memory_threshold: int = 80
    ) -> Dict[str, Any]:
        """
        构建上下文，整合长期记忆和短期记忆
        
        Args:
            system_prompt: 系统提示词
            history_messages: 历史消息列表（短期记忆）
            current_query: 当前用户问题
            max_tokens: 最大 token 数
            model: 模型名称
            api_key: API Key
            base_url: API Base URL
            db: 数据库会话（用于获取长期记忆）
            user_id: 用户 ID（用于获取长期记忆）
            memory_top_k: 普通记忆检索数量（用户可配置）
            core_memory_threshold: 核心记忆优先级阈值（用户可配置）
            
        Returns:
            {
                "messages": [...],
                "total_tokens": int,
                "compressed": bool,
                "original_count": int,
                "final_count": int,
                "long_term_memory_included": bool,
                "core_memory_count": int,
                "normal_memory_count": int
            }
        """
        max_tokens = max_tokens or self.max_context_tokens
        
        # 1. 获取长期记忆（核心记忆 + 普通记忆）
        long_term_memory = ""
        long_term_memory_included = False
        long_term_memory_list = []
        core_memory_count = 0
        normal_memory_count = 0
        
        if db and user_id:
            long_term_memory, long_term_memory_list, core_memory_count, normal_memory_count = await self.get_long_term_memories(
                db=db,
                user_id=user_id,
                query_text=current_query,
                top_k=memory_top_k,
                threshold=core_memory_threshold
            )
            if long_term_memory:
                long_term_memory_included = True
        
        # 2. 构建完整的系统提示词（包含长期记忆）
        full_system_prompt = system_prompt
        if long_term_memory:
            full_system_prompt = f"{system_prompt}\n\n{long_term_memory}"
        
        # 3. 计算固定部分的 token
        system_tokens = self.count_tokens(full_system_prompt) + 4
        query_tokens = self.count_tokens(current_query) + 4
        fixed_tokens = system_tokens + query_tokens
        
        # 4. 可用于短期记忆（历史消息）的 token 数
        available_tokens = max_tokens - fixed_tokens
        
        if available_tokens <= 0:
            return {
                "messages": [
                    {"role": "system", "content": full_system_prompt},
                    {"role": "user", "content": current_query}
                ],
                "total_tokens": fixed_tokens,
                "compressed": False,
                "original_count": len(history_messages),
                "final_count": 0,
                "long_term_memory_included": long_term_memory_included,
                "long_term_memories": long_term_memory_list,
                "core_memory_count": core_memory_count,
                "normal_memory_count": normal_memory_count
            }
        
        # 5. 处理短期记忆（从最新的消息开始保留）
        final_messages = []
        current_tokens = 0
        compressed = False
        
        for msg in reversed(history_messages):
            msg_tokens = self.count_message_tokens(msg)
            
            if current_tokens + msg_tokens <= available_tokens:
                final_messages.insert(0, msg)
                current_tokens += msg_tokens
            else:
                # 剩余的消息需要压缩
                remaining_messages = history_messages[:len(history_messages) - len(final_messages)]
                
                if remaining_messages:
                    summary = await self.compress_messages(
                        remaining_messages,
                        model=model,
                        api_key=api_key,
                        base_url=base_url
                    )
                    
                    if summary:
                        summary_tokens = self.count_message_tokens(summary)
                        if current_tokens + summary_tokens <= available_tokens:
                            final_messages.insert(0, summary)
                            current_tokens += summary_tokens
                            compressed = True
                
                break
        
        # 6. 组装最终消息列表
        messages = [{"role": "system", "content": full_system_prompt}]
        messages.extend(final_messages)
        messages.append({"role": "user", "content": current_query})
        
        total_tokens = fixed_tokens + current_tokens
        
        return {
            "messages": messages,
            "total_tokens": total_tokens,
            "compressed": compressed,
            "original_count": len(history_messages),
            "final_count": len(final_messages),
            "long_term_memory_included": long_term_memory_included,
            "long_term_memories": long_term_memory_list,
            "core_memory_count": core_memory_count,
            "normal_memory_count": normal_memory_count
        }


# 创建全局实例
context_manager = ContextManager(max_context_tokens=65536)
