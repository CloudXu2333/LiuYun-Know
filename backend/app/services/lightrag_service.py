"""
LightRAG 知识图谱服务
"""
import os
import json
import asyncio
import numpy as np
from typing import Optional, Dict, List, Any
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc
from lightrag.kg.shared_storage import initialize_pipeline_status
from neo4j import AsyncGraphDatabase
from app.config import settings


# ============ Neo4j 客户端（模块级别单例）============

class Neo4jClient:
    """Neo4j 异步客户端（单例模式）"""
    _instance = None
    _driver = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def get_driver(self):
        """获取或创建 Neo4j 驱动"""
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
        return self._driver
    
    async def close(self):
        """关闭连接"""
        if self._driver:
            await self._driver.close()
            self._driver = None
    
    async def execute_query(self, query: str, parameters: dict = None) -> List[Dict]:
        """执行 Cypher 查询"""
        driver = await self.get_driver()
        async with driver.session() as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records


# 模块级别的 Neo4j 客户端实例
_neo4j_client: Optional[Neo4jClient] = None


def get_neo4j_client() -> Neo4jClient:
    """获取 Neo4j 客户端单例"""
    global _neo4j_client
    if _neo4j_client is None:
        _neo4j_client = Neo4jClient()
    return _neo4j_client


class LightRAGService:
    """LightRAG 服务类"""
    
    def __init__(self):
        self._rag_instances: Dict[str, LightRAG] = {}
        # 不在这里初始化 Neo4j 客户端，使用模块级别的单例
    
    async def _create_llm_func(self, prompt, system_prompt=None, history_messages=[], **kwargs):
        """创建 LLM 函数（使用 DeepSeek 模型进行实体抽取）"""
        return await openai_complete_if_cache(
            model="deepseek-chat",
            prompt=prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_api_base,
            **kwargs
        )
    
    async def _create_embedding_func(self, texts: list[str]) -> np.ndarray:
        """创建 Embedding 函数（使用千问 Embedding）"""
        return await openai_embed(
            texts,
            model=settings.embedding_model,
            api_key=settings.qwen_api_key,
            base_url=settings.qwen_api_base,
        )
    
    async def get_or_create_rag(self, working_dir: str) -> LightRAG:
        """
        获取或创建 RAG 实例
        
        Args:
            working_dir: 工作目录
            
        Returns:
            LightRAG 实例
        """
        if working_dir in self._rag_instances:
            return self._rag_instances[working_dir]
        
        # 确保目录存在
        os.makedirs(working_dir, exist_ok=True)
        
        # 检测现有的 workspace 目录，兼容旧版本数据
        workspace = None
        if os.path.exists(working_dir):
            for item in os.listdir(working_dir):
                item_path = os.path.join(working_dir, item)
                if os.path.isdir(item_path) and item.startswith('kb_'):
                    workspace = item
                    print(f"[LightRAG] 检测到现有 workspace: {workspace}")
                    break
        
        # 如果没有找到现有目录，使用计算的 workspace 标签
        if not workspace:
            workspace = self._get_workspace_label(working_dir)
            print(f"[LightRAG] 使用新 workspace: {workspace}")
        
        # 创建 Embedding 函数
        embedding_func = EmbeddingFunc(
            embedding_dim=1024,  # text-embedding-v3/v4 的维度
            func=self._create_embedding_func
        )
        
        # 创建 LightRAG 实例，传入 workspace 参数以隔离不同知识库的数据
        rag = LightRAG(
            working_dir=working_dir,
            workspace=workspace,  # 每个知识库使用独立的 workspace
            graph_storage="Neo4JStorage",
            llm_model_func=self._create_llm_func,
            embedding_func=embedding_func,
            addon_params={
                "language": "Chinese",
            },
        )
        
        # 初始化存储和管道状态
        await rag.initialize_storages()
        await initialize_pipeline_status()
        
        self._rag_instances[working_dir] = rag
        print(f"✅ LightRAG 实例已创建: {working_dir}, workspace: {workspace}")
        
        return rag
    
    async def insert_text(self, working_dir: str, text: str):
        """
        插入文本到知识库
        
        Args:
            working_dir: 工作目录
            text: 文本内容
        """
        rag = await self.get_or_create_rag(working_dir)
        await rag.ainsert(text)
        print(f"✅ 文本已插入到知识库: {working_dir}")
    
    async def query(
        self,
        working_dir: str,
        query_text: str,
        mode: str = "mix",
        top_k: int = 5
    ) -> str:
        """
        查询知识库
        
        Args:
            working_dir: 工作目录
            query_text: 查询文本
            mode: 查询模式 (naive, local, global, hybrid, mix)
            top_k: 返回结果数量
            
        Returns:
            查询结果
        """
        rag = await self.get_or_create_rag(working_dir)
        result = await rag.aquery(
            query_text,
            param=QueryParam(mode=mode, top_k=top_k)
        )
        return result
    
    async def query_with_sources(
        self,
        working_dir: str,
        query_text: str,
        mode: str = "mix",
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        查询知识库并返回原始检索来源
        
        Args:
            working_dir: 工作目录
            query_text: 查询文本
            mode: 查询模式 (naive, local, global, hybrid, mix)
            top_k: 返回结果数量
            
        Returns:
            {context: 原始上下文, graph_data: 图谱数据, chunks: 文档分片}
        """
        rag = await self.get_or_create_rag(working_dir)
        
        # 获取原始检索上下文（不经过 AI 整合）
        context = await rag.aquery(
            query_text,
            param=QueryParam(mode=mode, top_k=top_k, only_need_context=True)
        )
        
        # 解析上下文，分离图谱数据和文档分片
        parsed = self._parse_lightrag_context(context)
        
        return {
            'context': context,
            'graph_data': parsed.get('graph_data', {}),
            'chunks': parsed.get('chunks', [])
        }
    
    def _parse_lightrag_context(self, context: str) -> Dict[str, Any]:
        """
        解析 LightRAG 返回的上下文，分离图谱数据和文档分片
        
        LightRAG only_need_context=True 返回格式：
        Knowledge Graph Data (Entity):```json{...}```
        Knowledge Graph Data (Relationship):```json{...}```
        Document Chunks (Each entry has a reference_id...):```json{...}{...}```
        Reference Document List:```...```
        
        Args:
            context: 原始上下文字符串
            
        Returns:
            {graph_data: {entities: [], relationships: []}, chunks: []}
        """
        import re
        import json
        
        result = {
            'graph_data': {
                'entities': [],
                'relationships': []
            },
            'chunks': []
        }
        
        if not context:
            return result
        
        # 解析实体数据
        entity_pattern = r'Knowledge Graph Data \(Entity\):\s*```json\s*(.*?)\s*```'
        entity_matches = re.findall(entity_pattern, context, re.DOTALL)
        for match in entity_matches:
            # 可能有多个 JSON 对象
            json_objects = re.findall(r'\{[^{}]+\}', match)
            for json_str in json_objects:
                try:
                    entity = json.loads(json_str)
                    if entity.get('entity'):
                        result['graph_data']['entities'].append({
                            'name': entity.get('entity', ''),
                            'type': entity.get('type', 'entity'),
                            'description': entity.get('description', '')
                        })
                except json.JSONDecodeError:
                    pass
        
        # 解析关系数据
        rel_pattern = r'Knowledge Graph Data \(Relationship\):\s*```json\s*(.*?)\s*```'
        rel_matches = re.findall(rel_pattern, context, re.DOTALL)
        for match in rel_matches:
            json_objects = re.findall(r'\{[^{}]+\}', match)
            for json_str in json_objects:
                try:
                    rel = json.loads(json_str)
                    if rel.get('entity1') and rel.get('entity2'):
                        result['graph_data']['relationships'].append({
                            'source': rel.get('entity1', ''),
                            'target': rel.get('entity2', ''),
                            'description': rel.get('description', '')
                        })
                except json.JSONDecodeError:
                    pass
        
        # 解析文档分片
        chunks_pattern = r'Document Chunks[^:]*:\s*```json\s*(.*?)\s*```'
        chunks_matches = re.findall(chunks_pattern, context, re.DOTALL)
        for match in chunks_matches:
            # 提取所有 JSON 对象
            json_objects = re.findall(r'\{[^{}]+\}', match)
            for idx, json_str in enumerate(json_objects, 1):
                try:
                    chunk = json.loads(json_str)
                    content = chunk.get('content', '')
                    # 过滤太短或无意义的内容
                    if content and len(content) > 10:
                        # 过滤掉只有页码或乱码的内容
                        if not re.match(r'^---\s*第\s*\d+\s*页\s*$', content.strip()):
                            result['chunks'].append({
                                'index': len(result['chunks']) + 1,
                                'content': content,
                                'reference_id': chunk.get('reference_id', '')
                            })
                except json.JSONDecodeError:
                    pass
        
        print(f"[LightRAG Parse] Entities: {len(result['graph_data']['entities'])}, "
              f"Relationships: {len(result['graph_data']['relationships'])}, "
              f"Chunks: {len(result['chunks'])}")
        
        return result
    
    def remove_rag_instance(self, working_dir: str):
        """
        移除 RAG 实例（删除知识库时调用）
        
        Args:
            working_dir: 工作目录
        """
        if working_dir in self._rag_instances:
            del self._rag_instances[working_dir]
            print(f"✅ LightRAG 实例已移除: {working_dir}")
    
    # ============ 辅助方法 ============
    
    def _get_workspace_label(self, working_dir: str) -> str:
        """
        从 working_dir 生成 Neo4j 的 workspace 标签
        每个知识库使用不同的 workspace 来隔离数据
        
        Args:
            working_dir: 知识库的工作目录
            
        Returns:
            workspace 标签（基于 working_dir 的哈希）
        """
        import hashlib
        # 直接使用 working_dir 字符串生成哈希，不依赖当前工作目录
        # 统一使用正斜杠，确保跨平台一致性
        normalized_path = working_dir.replace('\\', '/')
        # 使用 MD5 哈希的前 16 位作为 workspace 标签
        hash_value = hashlib.md5(normalized_path.encode()).hexdigest()[:16]
        return f"kb_{hash_value}"
    
    def _read_json_file(self, file_path: str) -> Dict[str, Any]:
        """读取JSON文件"""
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 读取JSON文件失败 {file_path}: {e}")
                return {}
        return {}
    
    def _write_json_file(self, file_path: str, data: Dict[str, Any]) -> bool:
        """写入JSON文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"⚠️ 写入JSON文件失败 {file_path}: {e}")
            return False
    
    # ============ 数据读取方法（从 Neo4j）============
    
    def _get_storage_dir(self, working_dir: str) -> str:
        """
        获取实际的存储目录（可能是 working_dir 或 working_dir/workspace）
        自动检测现有的 workspace 目录，兼容旧版本数据
        
        Args:
            working_dir: 工作目录
            
        Returns:
            实际存储目录路径
        """
        # 处理相对路径：如果是 ./rag_storage 开头，尝试在 backend 目录下查找
        actual_working_dir = working_dir
        if not os.path.exists(working_dir) and working_dir.startswith('./rag_storage'):
            # 尝试在 backend 目录下查找
            backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), working_dir.lstrip('./'))
            if os.path.exists(backend_path):
                actual_working_dir = backend_path
                print(f"[_get_storage_dir] 使用 backend 目录下的路径: {actual_working_dir}")
        
        print(f"[_get_storage_dir] working_dir: {working_dir}")
        print(f"[_get_storage_dir] actual_working_dir: {actual_working_dir}")
        print(f"[_get_storage_dir] actual_working_dir exists: {os.path.exists(actual_working_dir)}")
        
        # 首先检查 working_dir 下是否有任何 kb_ 开头的子目录
        if os.path.exists(actual_working_dir):
            items = os.listdir(actual_working_dir)
            print(f"[_get_storage_dir] items in working_dir: {items}")
            for item in items:
                item_path = os.path.join(actual_working_dir, item)
                if os.path.isdir(item_path) and item.startswith('kb_'):
                    # 找到现有的 workspace 目录
                    print(f"[_get_storage_dir] found existing workspace: {item_path}")
                    return item_path
        
        # 如果没有找到现有目录，使用计算的 workspace 标签
        workspace = self._get_workspace_label(working_dir)
        workspace_dir = os.path.join(actual_working_dir, workspace)
        
        if os.path.exists(workspace_dir):
            print(f"[_get_storage_dir] using computed workspace: {workspace_dir}")
            return workspace_dir
        
        # 否则返回 working_dir 本身
        print(f"[_get_storage_dir] using working_dir itself: {actual_working_dir}")
        return actual_working_dir
    
    async def get_chunks(self, working_dir: str) -> List[Dict[str, Any]]:
        """
        获取分片数据（从本地 JSON 文件，chunks 不存储在 Neo4j）
        
        Args:
            working_dir: 工作目录
            
        Returns:
            分片列表
        """
        storage_dir = self._get_storage_dir(working_dir)
        chunks_file = os.path.join(storage_dir, 'kv_store_text_chunks.json')
        
        print(f"[get_chunks] working_dir: {working_dir}")
        print(f"[get_chunks] storage_dir: {storage_dir}")
        print(f"[get_chunks] chunks_file: {chunks_file}")
        print(f"[get_chunks] file exists: {os.path.exists(chunks_file)}")
        
        chunks_data = self._read_json_file(chunks_file)
        print(f"[get_chunks] chunks count: {len(chunks_data)}")
        
        result = []
        for chunk_id, chunk_info in chunks_data.items():
            result.append({
                'id': chunk_id,
                'content': chunk_info.get('content', ''),
                'tokens': chunk_info.get('tokens', 0),
                'chunk_order_index': chunk_info.get('chunk_order_index', 0),
                'full_doc_id': chunk_info.get('full_doc_id', ''),
                'file_path': chunk_info.get('file_path', 'unknown'),
                'create_time': chunk_info.get('create_time', 0),
            })
        
        # 按chunk_order_index排序
        result.sort(key=lambda x: x['chunk_order_index'])
        return result
    
    async def get_entities_from_neo4j(self, working_dir: str) -> List[Dict[str, Any]]:
        """
        从 Neo4j 获取实体数据（包含描述）
        
        Args:
            working_dir: 工作目录
            
        Returns:
            实体列表
        """
        workspace = self._get_workspace_label(working_dir)
        
        # LightRAG 使用 workspace 作为节点标签，entity_id 作为实体标识
        query = f"""
        MATCH (e:`{workspace}`)
        RETURN e.entity_id AS name, 
               e.entity_type AS type, 
               e.description AS description,
               e.source_id AS source_id
        ORDER BY e.entity_id
        """
        
        try:
            records = await get_neo4j_client().execute_query(query, {})
            
            result = []
            for record in records:
                if record.get('name'):  # 确保有实体名称
                    result.append({
                        'id': record['name'],
                        'name': record['name'],
                        'type': record.get('type') or 'entity',
                        'description': record.get('description'),
                        'source_id': record.get('source_id'),
                    })
            
            return result
        except Exception as e:
            print(f"⚠️ 从 Neo4j 获取实体失败: {e}")
            # 回退到本地文件
            return await self._get_entities_from_file(working_dir)
    
    async def get_relations_from_neo4j(self, working_dir: str) -> List[Dict[str, Any]]:
        """
        从 Neo4j 获取关系数据（包含关系描述）
        
        Args:
            working_dir: 工作目录
            
        Returns:
            关系列表
        """
        workspace = self._get_workspace_label(working_dir)
        
        # LightRAG 使用 DIRECTED 作为关系类型
        query = f"""
        MATCH (s:`{workspace}`)-[r:DIRECTED]->(t:`{workspace}`)
        RETURN s.entity_id AS source, 
               t.entity_id AS target, 
               r.description AS description,
               r.keywords AS keywords,
               r.weight AS weight,
               r.source_id AS source_id
        """
        
        try:
            records = await get_neo4j_client().execute_query(query, {})
            
            result = []
            for idx, record in enumerate(records):
                # 从 description 或 keywords 中提取关系标签
                description = record.get('description') or ''
                keywords = record.get('keywords') or ''
                
                # 优先使用 keywords，否则使用 description 的前 30 个字符
                if keywords:
                    label = keywords.split(',')[0].strip() if ',' in keywords else keywords.strip()
                elif description:
                    label = description[:30] + '...' if len(description) > 30 else description
                else:
                    label = '相关'
                
                if record.get('source') and record.get('target'):  # 确保有源和目标
                    result.append({
                        'id': f"rel:{idx}",
                        'source': record['source'],
                        'target': record['target'],
                        'label': label,
                        'description': description,
                        'keywords': keywords,
                        'weight': record.get('weight', 1.0),
                        'source_id': record.get('source_id'),
                    })
            
            return result
        except Exception as e:
            print(f"⚠️ 从 Neo4j 获取关系失败: {e}")
            # 回退到本地文件
            return await self._get_relations_from_file(working_dir)
    
    async def _get_entities_from_file(self, working_dir: str) -> List[Dict[str, Any]]:
        """从本地 JSON 文件获取实体（回退方案）"""
        storage_dir = self._get_storage_dir(working_dir)
        entities_file = os.path.join(storage_dir, 'kv_store_full_entities.json')
        entities_data = self._read_json_file(entities_file)
        
        result = []
        for doc_id, doc_info in entities_data.items():
            entity_names = doc_info.get('entity_names', [])
            for entity_name in entity_names:
                result.append({
                    'id': entity_name,
                    'name': entity_name,
                    'type': 'entity',
                    'description': None,
                })
        
        return result
    
    async def _get_relations_from_file(self, working_dir: str) -> List[Dict[str, Any]]:
        """从本地 JSON 文件获取关系（回退方案）"""
        storage_dir = self._get_storage_dir(working_dir)
        relations_file = os.path.join(storage_dir, 'kv_store_full_relations.json')
        relations_data = self._read_json_file(relations_file)
        
        result = []
        for doc_id, doc_info in relations_data.items():
            relation_pairs = doc_info.get('relation_pairs', [])
            for idx, pair in enumerate(relation_pairs):
                if len(pair) >= 2:
                    result.append({
                        'id': f"{doc_id}:rel:{idx}",
                        'source': pair[0],
                        'target': pair[1],
                        'label': '相关',
                        'description': None,
                    })
        
        return result
    
    # 保持向后兼容的别名
    async def get_entities(self, working_dir: str) -> List[Dict[str, Any]]:
        """获取实体数据（优先从 Neo4j）"""
        return await self.get_entities_from_neo4j(working_dir)
    
    async def get_relations(self, working_dir: str) -> List[Dict[str, Any]]:
        """获取关系数据（优先从 Neo4j）"""
        return await self.get_relations_from_neo4j(working_dir)

    async def get_graph_data(self, working_dir: str, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """
        获取知识图谱数据（节点和边）- 从 Neo4j 读取
        
        Args:
            working_dir: 工作目录
            skip: 跳过数量
            limit: 限制数量
            
        Returns:
            图谱数据 {nodes, edges, total_nodes, total_edges}
        """
        entities = await self.get_entities(working_dir)
        relations = await self.get_relations(working_dir)
        
        total_nodes = len(entities)
        total_edges = len(relations)
        
        # 分页处理节点
        paginated_entities = entities[skip:skip + limit]
        
        # 构建节点ID集合
        node_names = {e['name'] for e in paginated_entities}
        
        # 过滤只包含当前节点的边
        filtered_relations = [
            r for r in relations 
            if r['source'] in node_names and r['target'] in node_names
        ]
        
        nodes = [
            {
                'id': e['name'],
                'label': e['name'],
                'type': e.get('type') or 'entity',
                'description': e.get('description'),  # 包含描述
            }
            for e in paginated_entities
        ]
        
        edges = [
            {
                'id': r['id'],
                'source': r['source'],
                'target': r['target'],
                'label': r['label'],  # 真实的关系标签
                'description': r.get('description'),  # 关系描述
            }
            for r in filtered_relations
        ]
        
        return {
            'nodes': nodes,
            'edges': edges,
            'total_nodes': total_nodes,
            'total_edges': total_edges,
        }
    
    async def get_stats(self, working_dir: str) -> Dict[str, int]:
        """
        获取知识库统计信息
        
        Args:
            working_dir: 工作目录
            
        Returns:
            统计信息
        """
        chunks = await self.get_chunks(working_dir)
        entities = await self.get_entities(working_dir)
        relations = await self.get_relations(working_dir)
        
        total_tokens = sum(c.get('tokens', 0) for c in chunks)
        
        return {
            'total_chunks': len(chunks),
            'total_entities': len(entities),
            'total_relations': len(relations),
            'total_tokens': total_tokens,
        }
    
    async def get_entity_detail(self, working_dir: str, entity_name: str) -> Optional[Dict[str, Any]]:
        """
        获取实体详情（从 Neo4j）
        
        Args:
            working_dir: 工作目录
            entity_name: 实体名称
            
        Returns:
            实体详情
        """
        workspace = self._get_workspace_label(working_dir)
        
        # 查询实体详情
        entity_query = f"""
        MATCH (e:`{workspace}` {{entity_id: $entity_id}})
        RETURN e.entity_id AS name, 
               e.entity_type AS type, 
               e.description AS description,
               e.source_id AS source_id
        """
        
        # 查询相关关系（双向）
        relations_query = f"""
        MATCH (e:`{workspace}` {{entity_id: $entity_id}})-[r:DIRECTED]-(other:`{workspace}`)
        RETURN e.entity_id AS source,
               other.entity_id AS target,
               r.description AS description,
               r.keywords AS keywords,
               type(r) AS rel_type,
               CASE WHEN startNode(r) = e THEN 'outgoing' ELSE 'incoming' END AS direction
        """
        
        try:
            # 获取实体
            entity_records = await get_neo4j_client().execute_query(
                entity_query, 
                {"entity_id": entity_name}
            )
            
            if not entity_records:
                return None
            
            entity = entity_records[0]
            
            # 获取关系
            relation_records = await get_neo4j_client().execute_query(
                relations_query,
                {"entity_id": entity_name}
            )
            
            related_relations = []
            for idx, r in enumerate(relation_records):
                keywords = r.get('keywords') or ''
                description = r.get('description') or ''
                
                if keywords:
                    label = keywords.split(',')[0].strip() if ',' in keywords else keywords.strip()
                elif description:
                    label = description[:30] + '...' if len(description) > 30 else description
                else:
                    label = '相关'
                
                related_relations.append({
                    'id': f"rel:{idx}",
                    'source': r['source'] if r['direction'] == 'outgoing' else r['target'],
                    'target': r['target'] if r['direction'] == 'outgoing' else r['source'],
                    'label': label,
                    'description': description,
                    'direction': r['direction'],
                })
            
            # 获取相关分片
            chunks = await self.get_chunks(working_dir)
            source_id = entity.get('source_id') or ''
            source_chunk_ids = source_id.split('<SEP>') if source_id else []
            source_chunks = [c for c in chunks if c['id'] in source_chunk_ids]
            
            return {
                'id': entity['name'],
                'name': entity['name'],
                'type': entity.get('type') or 'entity',
                'description': entity.get('description'),
                'relations': related_relations,
                'source_chunks': source_chunks,
            }
            
        except Exception as e:
            print(f"⚠️ 从 Neo4j 获取实体详情失败: {e}")
            # 回退到本地文件方式
            return await self._get_entity_detail_from_file(working_dir, entity_name)
    
    async def _get_entity_detail_from_file(self, working_dir: str, entity_name: str) -> Optional[Dict[str, Any]]:
        """从本地文件获取实体详情（回退方案）"""
        entities = await self._get_entities_from_file(working_dir)
        relations = await self._get_relations_from_file(working_dir)
        chunks = await self.get_chunks(working_dir)
        
        # 查找实体
        entity = None
        for e in entities:
            if e['name'] == entity_name:
                entity = e
                break
        
        if not entity:
            return None
        
        # 查找相关关系
        related_relations = [
            r for r in relations 
            if r['source'] == entity_name or r['target'] == entity_name
        ]
        
        # 查找相关分片
        storage_dir = self._get_storage_dir(working_dir)
        entity_chunks_file = os.path.join(storage_dir, 'kv_store_entity_chunks.json')
        entity_chunks_data = self._read_json_file(entity_chunks_file)
        
        source_chunk_ids = []
        for key, value in entity_chunks_data.items():
            if entity_name.lower() in key.lower():
                if isinstance(value, dict) and 'chunk_ids' in value:
                    source_chunk_ids.extend(value['chunk_ids'])
        
        source_chunks = [c for c in chunks if c['id'] in source_chunk_ids]
        
        return {
            'id': entity['id'],
            'name': entity['name'],
            'type': entity.get('type') or 'entity',
            'description': None,
            'relations': related_relations,
            'source_chunks': source_chunks,
        }
    
    async def delete_entity(self, working_dir: str, entity_name: str) -> bool:
        """
        删除实体及其相关关系（同时从 Neo4j 和本地文件删除）
        
        Args:
            working_dir: 工作目录
            entity_name: 实体名称
            
        Returns:
            是否成功
        """
        workspace = self._get_workspace_label(working_dir)
        storage_dir = self._get_storage_dir(working_dir)
        
        # 从 Neo4j 删除
        delete_query = f"""
        MATCH (e:`{workspace}` {{entity_id: $entity_id}})
        DETACH DELETE e
        """
        
        try:
            await get_neo4j_client().execute_query(
                delete_query,
                {"entity_id": entity_name}
            )
            print(f"✅ 从 Neo4j 删除实体: {entity_name}")
        except Exception as e:
            print(f"⚠️ 从 Neo4j 删除实体失败: {e}")
        
        # 同时从本地文件删除
        entities_file = os.path.join(storage_dir, 'kv_store_full_entities.json')
        entities_data = self._read_json_file(entities_file)
        
        modified = False
        for doc_id, doc_info in entities_data.items():
            entity_names = doc_info.get('entity_names', [])
            if entity_name in entity_names:
                entity_names.remove(entity_name)
                doc_info['entity_names'] = entity_names
                doc_info['count'] = len(entity_names)
                modified = True
        
        if modified:
            self._write_json_file(entities_file, entities_data)
        
        # 删除相关关系
        relations_file = os.path.join(storage_dir, 'kv_store_full_relations.json')
        relations_data = self._read_json_file(relations_file)
        
        for doc_id, doc_info in relations_data.items():
            relation_pairs = doc_info.get('relation_pairs', [])
            new_pairs = [
                pair for pair in relation_pairs 
                if entity_name not in pair
            ]
            if len(new_pairs) != len(relation_pairs):
                doc_info['relation_pairs'] = new_pairs
                doc_info['count'] = len(new_pairs)
                modified = True
        
        if modified:
            self._write_json_file(relations_file, relations_data)
        
        return True
    
    async def delete_relation(self, working_dir: str, source: str, target: str) -> bool:
        """
        删除关系（同时从 Neo4j 和本地文件删除）
        
        Args:
            working_dir: 工作目录
            source: 源实体
            target: 目标实体
            
        Returns:
            是否成功
        """
        workspace = self._get_workspace_label(working_dir)
        storage_dir = self._get_storage_dir(working_dir)
        
        # 从 Neo4j 删除（双向匹配）
        delete_query = f"""
        MATCH (s:`{workspace}` {{entity_id: $source}})-[r:DIRECTED]-(t:`{workspace}` {{entity_id: $target}})
        DELETE r
        """
        
        try:
            await get_neo4j_client().execute_query(
                delete_query,
                {"source": source, "target": target}
            )
            print(f"✅ 从 Neo4j 删除关系: {source} -> {target}")
        except Exception as e:
            print(f"⚠️ 从 Neo4j 删除关系失败: {e}")
        
        # 同时从本地文件删除
        relations_file = os.path.join(storage_dir, 'kv_store_full_relations.json')
        relations_data = self._read_json_file(relations_file)
        
        modified = False
        for doc_id, doc_info in relations_data.items():
            relation_pairs = doc_info.get('relation_pairs', [])
            new_pairs = [
                pair for pair in relation_pairs 
                if not (pair[0] == source and pair[1] == target)
            ]
            if len(new_pairs) != len(relation_pairs):
                doc_info['relation_pairs'] = new_pairs
                doc_info['count'] = len(new_pairs)
                modified = True
        
        if modified:
            self._write_json_file(relations_file, relations_data)
        
        return modified
    
    async def delete_chunks_by_file(self, working_dir: str, file_path: str) -> int:
        """
        根据文件路径删除相关的分片数据
        
        Args:
            working_dir: 工作目录
            file_path: 文件路径标识
            
        Returns:
            删除的分片数量
        """
        storage_dir = self._get_storage_dir(working_dir)
        chunks_file = os.path.join(storage_dir, 'kv_store_text_chunks.json')
        chunks_data = self._read_json_file(chunks_file)
        
        # 找出要删除的 chunk IDs
        chunks_to_delete = []
        for chunk_id, chunk_info in chunks_data.items():
            chunk_file_path = chunk_info.get('file_path', '')
            full_doc_id = chunk_info.get('full_doc_id', '')
            # 匹配文件路径或文档ID
            if file_path in chunk_file_path or file_path in full_doc_id:
                chunks_to_delete.append(chunk_id)
        
        # 删除分片
        for chunk_id in chunks_to_delete:
            del chunks_data[chunk_id]
        
        if chunks_to_delete:
            self._write_json_file(chunks_file, chunks_data)
            print(f"✅ 删除了 {len(chunks_to_delete)} 个分片")
        
        return len(chunks_to_delete)
    
    async def delete_all_data(self, working_dir: str) -> bool:
        """
        删除知识库的所有数据（Neo4j 图谱 + 本地文件）
        
        Args:
            working_dir: 工作目录
            
        Returns:
            是否成功
        """
        workspace = self._get_workspace_label(working_dir)
        storage_dir = self._get_storage_dir(working_dir)
        
        # 1. 从 Neo4j 删除该 workspace 的所有节点和关系
        delete_query = f"""
        MATCH (n:`{workspace}`)
        DETACH DELETE n
        """
        
        try:
            await get_neo4j_client().execute_query(delete_query, {})
            print(f"✅ 从 Neo4j 删除知识库数据: {workspace}")
        except Exception as e:
            print(f"⚠️ 从 Neo4j 删除知识库数据失败: {e}")
        
        # 2. 删除本地 JSON 文件中的数据（同时检查 working_dir 和 storage_dir）
        json_files = [
            'kv_store_text_chunks.json',
            'kv_store_full_entities.json',
            'kv_store_full_relations.json',
            'kv_store_entity_chunks.json',
            'kv_store_llm_response_cache.json',
        ]
        
        # 删除 storage_dir 中的文件
        for json_file in json_files:
            file_path = os.path.join(storage_dir, json_file)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"✅ 删除本地文件: {json_file}")
                except Exception as e:
                    print(f"⚠️ 删除本地文件失败 {json_file}: {e}")
        
        # 也尝试删除 working_dir 中的文件（兼容旧版本）
        if storage_dir != working_dir:
            for json_file in json_files:
                file_path = os.path.join(working_dir, json_file)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
        
        return True
    
    async def delete_by_doc_id(self, working_dir: str, doc_id: str) -> bool:
        """
        使用 LightRAG 官方 API 删除文档
        
        Args:
            working_dir: 工作目录
            doc_id: 文档 ID
            
        Returns:
            是否成功删除
        """
        try:
            rag = await self.get_or_create_rag(working_dir)
            await rag.adelete_by_doc_id(doc_id)
            print(f"✅ 使用 LightRAG API 删除文档: {doc_id}")
            return True
        except Exception as e:
            print(f"⚠️ LightRAG API 删除失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def get_doc_ids_by_file_path(self, working_dir: str, file_path: str) -> list:
        """
        根据文件路径获取对应的 doc_id 列表
        
        LightRAG 使用 file_paths 参数插入时，会在 text_chunks 的 file_path 字段记录文件名
        
        Args:
            working_dir: 工作目录
            file_path: 文件路径/文件名
            
        Returns:
            doc_id 列表
        """
        storage_dir = self._get_storage_dir(working_dir)
        print(f"📂 查找文件 '{file_path}' 对应的 doc_id...")
        print(f"   存储目录: {storage_dir}")
        
        doc_ids = set()
        
        # 方法1：从 text_chunks 中查找（推荐，因为 file_path 字段在这里）
        chunks_file = os.path.join(storage_dir, 'kv_store_text_chunks.json')
        chunks_data = self._read_json_file(chunks_file)
        print(f"   分片总数: {len(chunks_data)}")
        
        for chunk_id, chunk_info in chunks_data.items():
            chunk_file_path = chunk_info.get('file_path', '')
            # 精确匹配或包含匹配
            if chunk_file_path == file_path or file_path in chunk_file_path:
                full_doc_id = chunk_info.get('full_doc_id', '')
                if full_doc_id:
                    doc_ids.add(full_doc_id)
                    print(f"   ✓ 匹配分片: file_path={chunk_file_path}, doc_id={full_doc_id[:50]}...")
        
        # 方法2：从 full_docs 中查找（备用）
        if not doc_ids:
            full_docs_file = os.path.join(storage_dir, 'kv_store_full_docs.json')
            full_docs_data = self._read_json_file(full_docs_file)
            print(f"   full_docs 总数: {len(full_docs_data)}")
            
            for doc_id, doc_info in full_docs_data.items():
                # 检查 doc_info 中是否包含文件路径
                if isinstance(doc_info, dict):
                    doc_file_path = doc_info.get('file_path', '')
                    if file_path in doc_file_path or file_path == doc_file_path:
                        doc_ids.add(doc_id)
                        print(f"   ✓ 从 full_docs 匹配: {doc_id[:50]}...")
                elif isinstance(doc_info, str) and file_path in doc_info:
                    doc_ids.add(doc_id)
                    print(f"   ✓ 从 full_docs 内容匹配: {doc_id[:50]}...")
        
        result = list(doc_ids)
        print(f"📋 文件 '{file_path}' 对应的 doc_ids: {len(result)} 个")
        for doc_id in result:
            print(f"   - {doc_id[:60]}...")
        
        return result
    
    async def delete_file_related_data(
        self, working_dir: str, file_identifier: str, delete_all: bool = False
    ) -> dict:
        """
        删除与特定文件相关的所有数据（分片、实体、关系）
        使用 LightRAG 官方 adelete_by_doc_id API
        
        Args:
            working_dir: 工作目录
            file_identifier: 文件标识（文件名或路径）
            delete_all: 是否删除所有数据（当知识库只有一个文件时使用）
            
        Returns:
            删除统计 {chunks, entities, relations, docs}
        """
        deleted_stats = {'chunks': 0, 'entities': 0, 'relations': 0, 'docs': 0}
        storage_dir = self._get_storage_dir(working_dir)
        workspace = self._get_workspace_label(working_dir)
        
        print(f"=" * 60)
        print(f"🗑️ 开始删除文件相关数据")
        print(f"   文件标识: {file_identifier}")
        print(f"   工作目录: {working_dir}")
        print(f"   存储目录: {storage_dir}")
        print(f"   workspace: {workspace}")
        print(f"   删除所有: {delete_all}")
        print(f"=" * 60)
        
        # 获取要删除的 doc_ids
        doc_ids_to_delete = []
        
        if delete_all:
            # 删除所有文档：从 full_docs 获取所有 doc_id
            full_docs_file = os.path.join(storage_dir, 'kv_store_full_docs.json')
            full_docs_data = self._read_json_file(full_docs_file)
            doc_ids_to_delete = list(full_docs_data.keys())
            print(f"📋 delete_all=True，将删除所有 {len(doc_ids_to_delete)} 个文档")
        else:
            # 根据文件名查找对应的 doc_id
            doc_ids_to_delete = await self.get_doc_ids_by_file_path(working_dir, file_identifier)
            print(f"📋 找到 {len(doc_ids_to_delete)} 个匹配的文档 ID")
        
        if not doc_ids_to_delete:
            print(f"⚠️ 没有找到要删除的文档")
            print(f"   这可能是因为文件是在功能更新前上传的（file_path 为 unknown_source）")
            print(f"   建议：删除整个知识库并重新上传文件")
            return deleted_stats
        
        # 使用 LightRAG 官方 API 删除每个文档
        print(f"\n🔄 使用 LightRAG 官方 API 删除文档...")
        for doc_id in doc_ids_to_delete:
            try:
                print(f"   删除文档: {doc_id[:60]}...")
                success = await self.delete_by_doc_id(working_dir, doc_id)
                if success:
                    deleted_stats['docs'] += 1
                    print(f"   ✅ 删除成功")
                else:
                    print(f"   ⚠️ 删除返回 False")
            except Exception as e:
                print(f"   ❌ 删除失败: {e}")
        
        # 统计删除后的数据
        print(f"\n📊 验证删除结果...")
        try:
            # 检查剩余分片数
            chunks_file = os.path.join(storage_dir, 'kv_store_text_chunks.json')
            chunks_data = self._read_json_file(chunks_file)
            print(f"   剩余分片数: {len(chunks_data)}")
            
            # 检查剩余文档数
            full_docs_file = os.path.join(storage_dir, 'kv_store_full_docs.json')
            full_docs_data = self._read_json_file(full_docs_file)
            print(f"   剩余文档数: {len(full_docs_data)}")
            
            # 检查 Neo4j 节点数
            neo4j_client = get_neo4j_client()
            count_query = f"MATCH (n:`{workspace}`) RETURN count(n) as total"
            count_result = await neo4j_client.execute_query(count_query)
            total_nodes = count_result[0].get('total', 0) if count_result else 0
            print(f"   Neo4j 节点数: {total_nodes}")
            
        except Exception as e:
            print(f"   ⚠️ 验证时出错: {e}")
        
        # 设置统计信息（官方 API 会自动清理所有相关数据）
        deleted_stats['chunks'] = deleted_stats['docs']  # 每个 doc 对应多个 chunks
        deleted_stats['entities'] = deleted_stats['docs']  # 估算值
        
        print(f"\n✅ 文件相关数据删除完成")
        print(f"   删除文档数: {deleted_stats['docs']}")
        return deleted_stats


# 创建全局实例
lightrag_service = LightRAGService()
