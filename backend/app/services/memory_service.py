"""
记忆服务 - 长期记忆的增删查改（异步版本）
支持核心记忆（高优先级）必定加载 + 普通记忆向量检索
支持冲突检测和自动合并
使用千问 Embedding 模型进行向量相似度匹配
"""
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, func
from app.models.memory import LongTermMemory
from app.schemas.memory import LongTermMemoryCreate, LongTermMemoryUpdate
from app.services.embedding_service import embedding_service


class MemoryService:
    """记忆服务"""
    
    async def get_core_memories(
        self,
        db: AsyncSession,
        user_id: str,
        threshold: int = 80
    ) -> List[LongTermMemory]:
        """
        获取核心记忆（优先级 >= threshold 的记忆，必定加载）
        
        Args:
            db: 数据库会话
            user_id: 用户 ID
            threshold: 核心记忆优先级阈值，默认 80
            
        Returns:
            核心记忆列表
        """
        query = select(LongTermMemory).where(
            and_(
                LongTermMemory.user_id == user_id,
                LongTermMemory.is_active == True,
                LongTermMemory.priority >= threshold
            )
        ).order_by(
            desc(LongTermMemory.priority),
            desc(LongTermMemory.created_at)
        )
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_normal_memories(
        self,
        db: AsyncSession,
        user_id: str,
        threshold: int = 80
    ) -> List[LongTermMemory]:
        """
        获取普通记忆（优先级 < threshold 的记忆，用于向量检索）
        
        Args:
            db: 数据库会话
            user_id: 用户 ID
            threshold: 核心记忆优先级阈值，默认 80
            
        Returns:
            普通记忆列表
        """
        query = select(LongTermMemory).where(
            and_(
                LongTermMemory.user_id == user_id,
                LongTermMemory.is_active == True,
                LongTermMemory.priority < threshold
            )
        ).order_by(
            desc(LongTermMemory.priority),
            desc(LongTermMemory.created_at)
        )
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_memories_for_context(
        self,
        db: AsyncSession,
        user_id: str,
        query_text: str = None,
        top_k: int = 5,
        threshold: int = 80
    ) -> Tuple[List[LongTermMemory], List[LongTermMemory]]:
        """
        获取用于上下文的记忆：核心记忆 + 相关普通记忆
        使用向量相似度检索普通记忆
        
        Args:
            db: 数据库会话
            user_id: 用户 ID
            query_text: 用户查询文本（用于向量检索）
            top_k: 普通记忆检索数量
            threshold: 核心记忆优先级阈值
            
        Returns:
            (核心记忆列表, 普通记忆列表)
        """
        # 1. 获取核心记忆（必定加载）
        core_memories = await self.get_core_memories(db, user_id, threshold)
        
        # 2. 获取普通记忆
        normal_memories = await self.get_normal_memories(db, user_id, threshold)
        
        # 3. 如果有查询文本，进行向量相似度检索
        if query_text and normal_memories:
            selected_normal = await self._vector_search_memories(
                query_text, normal_memories, top_k
            )
        else:
            # 没有查询文本，按优先级取 top_k
            selected_normal = normal_memories[:top_k]
        
        return core_memories, selected_normal
    
    async def _vector_search_memories(
        self,
        query_text: str,
        memories: List[LongTermMemory],
        top_k: int = 5,
        min_similarity: float = 0.3
    ) -> List[LongTermMemory]:
        """
        使用向量相似度检索记忆
        
        Args:
            query_text: 查询文本
            memories: 候选记忆列表
            top_k: 返回数量
            min_similarity: 最小相似度阈值
            
        Returns:
            相似度最高的记忆列表
        """
        if not memories:
            return []
        
        print(f"[Memory] Vector search: query='{query_text[:50]}...', candidates={len(memories)}")
        
        # 获取查询文本的 embedding
        query_embedding = await embedding_service.get_embedding(query_text)
        
        # 收集所有记忆的 embedding
        scored_memories = []
        memories_need_embedding = []
        
        for memory in memories:
            memory_embedding = memory.get_embedding_vector()
            if memory_embedding:
                # 已有 embedding，直接计算相似度
                similarity = embedding_service.cosine_similarity(query_embedding, memory_embedding)
                scored_memories.append((memory, similarity))
                print(f"[Memory] '{memory.title}' similarity: {similarity:.3f} (cached)")
            else:
                # 需要生成 embedding
                memories_need_embedding.append(memory)
        
        # 批量生成缺失的 embedding
        if memories_need_embedding:
            print(f"[Memory] Generating embeddings for {len(memories_need_embedding)} memories...")
            texts = [f"{m.title} {m.content}" for m in memories_need_embedding]
            embeddings = await embedding_service.get_embeddings(texts)
            
            for memory, emb in zip(memories_need_embedding, embeddings):
                # 保存 embedding 到数据库（下次可复用）
                memory.set_embedding_vector(emb)
                similarity = embedding_service.cosine_similarity(query_embedding, emb)
                scored_memories.append((memory, similarity))
                print(f"[Memory] '{memory.title}' similarity: {similarity:.3f} (new)")
        
        # 按相似度降序排序
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        
        # 过滤低相似度，取 top_k
        result = [m for m, score in scored_memories[:top_k] if score >= min_similarity]
        print(f"[Memory] Vector search result: {len(result)} memories (min_sim={min_similarity})")
        
        return result
    
    async def get_user_memories(
        self,
        db: AsyncSession,
        user_id: str,
        category: Optional[str] = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[LongTermMemory], int]:
        """
        获取用户的长期记忆列表
        
        Args:
            db: 数据库会话
            user_id: 用户 ID
            category: 分类筛选
            active_only: 是否只返回启用的记忆
            skip: 跳过数量
            limit: 返回数量
            
        Returns:
            (记忆列表, 总数)
        """
        # 构建查询
        query = select(LongTermMemory).where(LongTermMemory.user_id == user_id)
        
        if category:
            query = query.where(LongTermMemory.category == category)
        
        if active_only:
            query = query.where(LongTermMemory.is_active == True)
        
        # 获取总数
        count_result = await db.execute(
            select(LongTermMemory.id).where(LongTermMemory.user_id == user_id)
            .where(LongTermMemory.category == category if category else True)
            .where(LongTermMemory.is_active == True if active_only else True)
        )
        total = len(count_result.all())
        
        # 获取分页数据
        query = query.order_by(
            desc(LongTermMemory.priority),
            desc(LongTermMemory.created_at)
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        memories = result.scalars().all()
        
        return list(memories), total
    
    async def get_active_memories(self, db: AsyncSession, user_id: str) -> List[LongTermMemory]:
        """
        获取用户所有启用的长期记忆（用于构建上下文）
        
        Args:
            db: 数据库会话
            user_id: 用户 ID
            
        Returns:
            启用的记忆列表（按优先级排序）
        """
        query = select(LongTermMemory).where(
            LongTermMemory.user_id == user_id,
            LongTermMemory.is_active == True
        ).order_by(
            desc(LongTermMemory.priority),
            desc(LongTermMemory.created_at)
        )
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_memory_by_id(
        self,
        db: AsyncSession,
        memory_id: str,
        user_id: str
    ) -> Optional[LongTermMemory]:
        """获取单条记忆"""
        query = select(LongTermMemory).where(
            LongTermMemory.id == memory_id,
            LongTermMemory.user_id == user_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_memory(
        self,
        db: AsyncSession,
        user_id: str,
        memory_data: LongTermMemoryCreate
    ) -> LongTermMemory:
        """创建长期记忆（同时生成 embedding）"""
        memory = LongTermMemory(
            user_id=user_id,
            title=memory_data.title,
            content=memory_data.content,
            category=memory_data.category,
            priority=memory_data.priority,
            is_active=memory_data.is_active
        )
        
        # 生成 embedding
        try:
            text = f"{memory_data.title} {memory_data.content}"
            embedding = await embedding_service.get_embedding(text)
            memory.set_embedding_vector(embedding)
            print(f"[Memory] Generated embedding for new memory: {memory_data.title}")
        except Exception as e:
            print(f"[Memory] Failed to generate embedding: {e}")
        
        db.add(memory)
        await db.flush()
        await db.refresh(memory)
        return memory
    
    async def update_memory(
        self,
        db: AsyncSession,
        memory_id: str,
        user_id: str,
        memory_data: LongTermMemoryUpdate
    ) -> Optional[LongTermMemory]:
        """更新长期记忆（内容变化时重新生成 embedding）"""
        memory = await self.get_memory_by_id(db, memory_id, user_id)
        if not memory:
            return None
        
        update_data = memory_data.model_dump(exclude_unset=True)
        
        # 检查是否需要更新 embedding（标题或内容变化）
        need_update_embedding = 'title' in update_data or 'content' in update_data
        
        for field, value in update_data.items():
            setattr(memory, field, value)
        
        # 重新生成 embedding
        if need_update_embedding:
            try:
                text = f"{memory.title} {memory.content}"
                embedding = await embedding_service.get_embedding(text)
                memory.set_embedding_vector(embedding)
                print(f"[Memory] Updated embedding for memory: {memory.title}")
            except Exception as e:
                print(f"[Memory] Failed to update embedding: {e}")
        
        await db.flush()
        await db.refresh(memory)
        return memory
    
    async def delete_memory(
        self,
        db: AsyncSession,
        memory_id: str,
        user_id: str
    ) -> bool:
        """删除长期记忆"""
        memory = await self.get_memory_by_id(db, memory_id, user_id)
        if not memory:
            return False
        
        await db.delete(memory)
        await db.flush()
        return True
    
    async def toggle_memory(
        self,
        db: AsyncSession,
        memory_id: str,
        user_id: str
    ) -> Optional[LongTermMemory]:
        """切换记忆的启用状态"""
        memory = await self.get_memory_by_id(db, memory_id, user_id)
        if not memory:
            return None
        
        memory.is_active = not memory.is_active
        await db.flush()
        await db.refresh(memory)
        return memory
    
    async def get_all_active_memories(
        self,
        db: AsyncSession,
        user_id: str
    ) -> List[LongTermMemory]:
        """获取用户所有启用的记忆"""
        query = select(LongTermMemory).where(
            and_(
                LongTermMemory.user_id == user_id,
                LongTermMemory.is_active == True
            )
        ).order_by(desc(LongTermMemory.priority))
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def estimate_memory_tokens(
        self,
        db: AsyncSession,
        user_id: str
    ) -> int:
        """
        估算用户记忆的总 token 数
        简单估算：中文约 2 字符/token，英文约 4 字符/token
        这里用 2.5 字符/token 作为平均值
        """
        memories = await self.get_all_active_memories(db, user_id)
        total_chars = sum(len(m.title) + len(m.content) for m in memories)
        return int(total_chars / 2.5)
    
    async def check_memory_limit(
        self,
        db: AsyncSession,
        user_id: str,
        max_context_tokens: int = 65536
    ) -> Dict[str, Any]:
        """
        检查记忆是否超过上下文限制的 50%
        
        Returns:
            {
                "current_tokens": int,
                "limit_tokens": int,  # 50% of max_context_tokens
                "percentage": float,
                "warning": bool,
                "message": str
            }
        """
        current_tokens = await self.estimate_memory_tokens(db, user_id)
        limit_tokens = max_context_tokens // 2  # 50%
        percentage = (current_tokens / limit_tokens) * 100 if limit_tokens > 0 else 0
        
        warning = percentage >= 100
        
        if warning:
            message = f"记忆已占用上下文的 {percentage:.1f}%（{current_tokens}/{limit_tokens} tokens），建议合并相似记忆"
        elif percentage >= 80:
            message = f"记忆已占用上下文的 {percentage:.1f}%，接近限制"
        else:
            message = ""
        
        return {
            "current_tokens": current_tokens,
            "limit_tokens": limit_tokens,
            "percentage": round(percentage, 1),
            "warning": warning,
            "message": message
        }
    
    async def _calculate_vector_similarity(self, text1: str, text2: str) -> float:
        """
        计算两段文本的向量相似度（使用千问 Embedding）
        返回 0-1 之间的相似度分数
        """
        if not text1 or not text2:
            return 0.0
        
        try:
            embeddings = await embedding_service.get_embeddings([text1, text2])
            if len(embeddings) == 2:
                return embedding_service.cosine_similarity(embeddings[0], embeddings[1])
        except Exception as e:
            print(f"[Memory] Vector similarity failed: {e}")
        
        return 0.0
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        计算两段文本的简单相似度（基于词汇重叠）- 同步版本，作为备用
        返回 0-1 之间的相似度分数
        """
        # 简单的字符级别相似度
        if not text1 or not text2:
            return 0.0
        
        # 转小写，分词（简单按字符）
        set1 = set(text1.lower())
        set2 = set(text2.lower())
        
        # Jaccard 相似度
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    async def get_memories_for_conflict_check(
        self,
        db: AsyncSession,
        user_id: str,
        new_content: str,
        new_title: str,
        threshold: int = 80,
        top_k: int = 5
    ) -> List[LongTermMemory]:
        """
        获取用于冲突检测的记忆：
        1. 优先级 >= threshold 的核心记忆：全部参与
        2. 优先级 < threshold 的普通记忆：使用向量相似度取 top_k 条
        
        Args:
            db: 数据库会话
            user_id: 用户 ID
            new_content: 新记忆内容
            new_title: 新记忆标题
            threshold: 核心记忆阈值
            top_k: 普通记忆取多少条
            
        Returns:
            需要参与冲突检测的记忆列表
        """
        # 1. 获取核心记忆（全部参与）
        core_memories = await self.get_core_memories(db, user_id, threshold)
        print(f"[Memory] Core memories (priority >= {threshold}): {len(core_memories)}")
        
        # 2. 获取普通记忆
        normal_memories = await self.get_normal_memories(db, user_id, threshold)
        print(f"[Memory] Normal memories (priority < {threshold}): {len(normal_memories)}")
        
        # 3. 对普通记忆使用向量相似度排序，取 top_k
        new_text = f"{new_title} {new_content}"
        print(f"[Memory] New memory text: {new_text[:100]}...")
        
        selected_normal = []
        if normal_memories:
            # 使用向量相似度检索
            selected_normal = await self._vector_search_memories(
                new_text, 
                normal_memories, 
                top_k=top_k,
                min_similarity=0.3  # 冲突检测用较低阈值
            )
            print(f"[Memory] Selected normal memories by vector similarity: {len(selected_normal)}")
            for m in selected_normal:
                print(f"[Memory]   - {m.title}")
        
        # 合并返回
        total = core_memories + selected_normal
        print(f"[Memory] Total memories for conflict check: {len(total)}")
        return total
    
    async def detect_conflicts(
        self,
        db: AsyncSession,
        user_id: str,
        new_content: str,
        new_title: str,
        llm_client,
        model: str,
        threshold: int = 80,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        使用 AI 检测新记忆与现有记忆的冲突
        
        优化策略：
        - 优先级 >= threshold 的核心记忆：全部参与检测
        - 优先级 < threshold 的普通记忆：只取相似度高的 top_k 条
        
        Returns:
            {
                "has_conflict": bool,
                "conflict_type": str,  # "contradiction", "duplicate", "update", "none"
                "conflicting_memory_id": str or None,
                "suggested_action": str,  # "merge", "replace", "keep_both", "none"
                "merged_content": dict or None  # 如果建议合并，包含合并后的内容
            }
        """
        import json
        
        # 获取需要检测的记忆（核心记忆 + 相似的普通记忆）
        memories = await self.get_memories_for_conflict_check(
            db, user_id, new_content, new_title, threshold, top_k
        )
        
        if not memories:
            return {
                "has_conflict": False,
                "conflict_type": "none",
                "conflicting_memory_id": None,
                "suggested_action": "none",
                "merged_content": None
            }
        
        # 构建现有记忆列表
        memories_text = "\n".join([
            f"[ID:{m.id}] 标题: {m.title}\n内容: {m.content}\n分类: {m.category}, 优先级: {m.priority}"
            for m in memories
        ])
        
        print(f"[Memory] Conflict check: {len(memories)} memories to compare")
        
        system_prompt = """你是一个记忆冲突检测助手。用户要添加一条新记忆，你需要检查它是否与现有记忆存在关联，需要合并或更新。

检测类型：
1. duplicate（重复）：新记忆与某条旧记忆内容基本相同
2. update（更新/补充）：新记忆是对旧记忆的更新、补充或同类信息扩展
   - 例如：旧记忆"喜欢苹果"，新记忆"喜欢梨" → 应该合并为"喜欢苹果和梨"
   - 例如：旧记忆"不喜欢馒头"，新记忆"不喜欢花卷" → 应该合并为"不喜欢馒头和花卷"
   - 同一主题的偏好应该合并到一起
3. contradiction（矛盾）：新旧记忆中对同一事物的态度相反
   - 例如：旧记忆"喜欢苹果和西瓜"，新记忆"不喜欢苹果"
   - 处理方式：更新矛盾部分，保留不冲突的部分
   - 合并结果应该是："喜欢西瓜，不喜欢苹果" 或分成两条记忆
4. none（无关联）：新记忆与现有记忆完全无关

重要规则：
- 同类型的偏好（如都是喜欢的水果、都是不喜欢的食物）应该合并到一条记忆中
- 遇到矛盾时，以新记忆为准更新矛盾部分，但要保留旧记忆中不冲突的内容
- 合并后的内容要完整，不能丢失旧记忆中的有效信息

请返回JSON格式：
{
    "has_conflict": true/false,
    "conflict_type": "duplicate/update/contradiction/none",
    "conflicting_memory_id": "关联记忆的ID，无关联则为null",
    "suggested_action": "merge/replace/keep_both/none",
    "merged_content": {
        "title": "合并后的标题",
        "content": "合并后的内容（整合新旧信息，矛盾部分以新记忆为准，保留不冲突的旧内容）",
        "category": "分类",
        "priority": 优先级数字（取两者平均值）
    } // 如果建议合并，否则为null
}

只返回JSON，不要其他内容。"""

        user_prompt = f"""现有记忆：
{memories_text}

新记忆：
标题: {new_title}
内容: {new_content}

请检测新记忆是否与现有记忆有关联（重复、补充、矛盾），如果有，建议如何处理。
注意：如果有矛盾，合并时要保留旧记忆中不冲突的部分。"""

        try:
            response = await llm_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            result_text = response.choices[0].message.content.strip()
            print(f"[Memory] AI response: {result_text[:500]}...")
            
            # 清理可能的markdown代码块
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            result_text = result_text.strip()
            
            result = json.loads(result_text)
            
            print(f"[Memory] Conflict result: has_conflict={result.get('has_conflict')}, type={result.get('conflict_type')}, action={result.get('suggested_action')}")
            
            return {
                "has_conflict": result.get("has_conflict", False),
                "conflict_type": result.get("conflict_type", "none"),
                "conflicting_memory_id": result.get("conflicting_memory_id"),
                "suggested_action": result.get("suggested_action", "none"),
                "merged_content": result.get("merged_content")
            }
            
        except Exception as e:
            print(f"[Memory] Conflict detection failed: {e}")
            return {
                "has_conflict": False,
                "conflict_type": "none",
                "conflicting_memory_id": None,
                "suggested_action": "none",
                "merged_content": None
            }
    
    async def merge_memories(
        self,
        db: AsyncSession,
        user_id: str,
        old_memory_id: str,
        merged_data: Dict[str, Any]
    ) -> Optional[LongTermMemory]:
        """
        合并记忆：更新旧记忆为合并后的内容（同时更新 embedding）
        
        Args:
            db: 数据库会话
            user_id: 用户 ID
            old_memory_id: 要更新的旧记忆 ID
            merged_data: 合并后的数据 {title, content, category, priority}
        
        Returns:
            更新后的记忆
        """
        memory = await self.get_memory_by_id(db, old_memory_id, user_id)
        if not memory:
            return None
        
        # 更新记忆内容
        memory.title = merged_data.get("title", memory.title)
        memory.content = merged_data.get("content", memory.content)
        memory.category = merged_data.get("category", memory.category)
        
        # 优先级取平均值
        old_priority = memory.priority
        new_priority = merged_data.get("priority", old_priority)
        memory.priority = (old_priority + new_priority) // 2
        
        # 重新生成 embedding
        try:
            text = f"{memory.title} {memory.content}"
            embedding = await embedding_service.get_embedding(text)
            memory.set_embedding_vector(embedding)
            print(f"[Memory] Updated embedding for merged memory: {memory.title}")
        except Exception as e:
            print(f"[Memory] Failed to update embedding: {e}")
        
        await db.flush()
        await db.refresh(memory)
        return memory
    
    def format_memories_for_context(
        self, 
        memories: List[LongTermMemory] = None,
        core_memories: List[LongTermMemory] = None,
        normal_memories: List[LongTermMemory] = None
    ) -> str:
        """
        将记忆格式化为上下文字符串
        
        Args:
            memories: 记忆列表（兼容旧接口）
            core_memories: 核心记忆列表
            normal_memories: 普通记忆列表
            
        Returns:
            格式化的记忆字符串
        """
        # 兼容旧接口
        if memories is not None and core_memories is None and normal_memories is None:
            if not memories:
                return ""
            
            lines = ["【用户长期记忆】"]
            
            for i, memory in enumerate(memories, 1):
                category_label = {
                    "general": "通用",
                    "preference": "偏好",
                    "fact": "事实",
                    "instruction": "指令"
                }.get(memory.category, memory.category)
                
                lines.append(f"[记忆{i}] [{category_label}] {memory.title}")
                lines.append(f"内容: {memory.content}")
                lines.append("")
            
            lines.append("【重要】如果回答中使用了长期记忆的信息，请使用 [记忆X] 格式标注（X为对应编号）。")
            
            return "\n".join(lines)
        
        # 新接口：区分核心记忆和普通记忆
        core_memories = core_memories or []
        normal_memories = normal_memories or []
        
        if not core_memories and not normal_memories:
            return ""
        
        lines = ["【用户长期记忆】"]
        memory_index = 1
        
        # 核心记忆（必定加载）
        if core_memories:
            lines.append("\n--- 核心记忆（重要信息，始终生效）---")
            for memory in core_memories:
                category_label = {
                    "general": "通用",
                    "preference": "偏好",
                    "fact": "事实",
                    "instruction": "指令"
                }.get(memory.category, memory.category)
                
                lines.append(f"[记忆{memory_index}] [{category_label}] {memory.title}")
                lines.append(f"内容: {memory.content}")
                lines.append("")
                memory_index += 1
        
        # 普通记忆（相关检索）
        if normal_memories:
            lines.append("\n--- 相关记忆（根据当前对话检索）---")
            for memory in normal_memories:
                category_label = {
                    "general": "通用",
                    "preference": "偏好",
                    "fact": "事实",
                    "instruction": "指令"
                }.get(memory.category, memory.category)
                
                lines.append(f"[记忆{memory_index}] [{category_label}] {memory.title}")
                lines.append(f"内容: {memory.content}")
                lines.append("")
                memory_index += 1
        
        lines.append("【重要】如果回答中使用了长期记忆的信息，请使用 [记忆X] 格式标注（X为对应编号）。")
        
        return "\n".join(lines)


# 创建全局实例
memory_service = MemoryService()
