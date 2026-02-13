"""
知识库检索服务
支持向量检索、关键词检索、混合检索
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pymilvus import connections, Collection, utility
from app.core.config import settings
from app.core.logger import logger


@dataclass
class SearchResult:
    """检索结果"""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    source: str


class RetrievalService:
    """检索服务"""
    
    def __init__(self):
        self._connected = False
    
    async def connect(self):
        """连接Milvus"""
        if not self._connected:
            connections.connect(
                alias="default",
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT,
                user=settings.MILVUS_USER or None,
                password=settings.MILVUS_PASSWORD or None
            )
            self._connected = True
    
    async def disconnect(self):
        """断开连接"""
        if self._connected:
            connections.disconnect("default")
            self._connected = False
    
    async def vector_search(
        self,
        collection_name: str,
        query_text: str = None,
        query_vector: List[float] = None,
        top_k: int = 10,
        score_threshold: float = 0.7,
        filter_expr: str = None
    ) -> List[Dict[str, Any]]:
        """
        向量检索
        
        Args:
            collection_name: 集合名称
            query_text: 查询文本（将自动转换为向量）
            query_vector: 查询向量
            top_k: 返回数量
            score_threshold: 相似度阈值
            filter_expr: 过滤表达式
        
        Returns:
            检索结果列表
        """
        logger.info(f"========== 开始向量检索 ==========")
        logger.info(f"Collection: {collection_name}")
        logger.info(f"查询文本: {query_text[:100] if query_text else 'N/A'}...")
        logger.info(f"Top K: {top_k}, 相似度阈值: {score_threshold}")
        
        await self.connect()
        
        # 如果提供的是文本，需要先转换为向量
        if query_text and not query_vector:
            logger.info(f"将查询文本转换为向量...")
            query_vector = await self._text_to_vector(query_text)
            logger.info(f"向量转换完成，维度: {len(query_vector)}")
        
        if not query_vector:
            raise ValueError("Must provide either query_text or query_vector")
        
        logger.info(f"加载 Milvus Collection: {collection_name}")
        collection = Collection(collection_name)
        collection.load()
        
        # 获取集合信息
        num_entities = collection.num_entities
        logger.info(f"Collection 中共有 {num_entities} 条向量记录")
        
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        
        logger.info(f"执行 Milvus 向量搜索（相似度算法: COSINE）...")
        results = collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=filter_expr,
            output_fields=["content", "metadata", "source"]
        )
        
        logger.info(f"Milvus 检索完成")
        
        search_results = []
        for hits in results:
            logger.info(f"找到 {len(hits)} 条原始结果")
            for i, hit in enumerate(hits):
                if hit.score >= score_threshold:
                    search_results.append({
                        "id": str(hit.id),
                        "content": hit.entity.get("content", ""),
                        "score": float(hit.score),
                        "metadata": hit.entity.get("metadata", {}),
                        "source": hit.entity.get("source", "")
                    })
                    if i < 3:  # 打印前3条结果
                        content_preview = hit.entity.get("content", "")[:100].replace('\n', ' ')
                        logger.info(f"  结果 {i+1}: 分数={hit.score:.4f}, 内容={content_preview}...")
                else:
                    logger.debug(f"  结果 {i+1} 被过滤（分数 {hit.score:.4f} < 阈值 {score_threshold}）")
        
        logger.info(f"========== 检索完成 ==========")
        logger.info(f"✅ 过滤后返回 {len(search_results)} 条结果")
        logger.info(f"====================================")
        
        return search_results
    
    async def _text_to_vector(self, text: str) -> List[float]:
        """将文本转换为向量"""
        try:
            from sentence_transformers import SentenceTransformer
            import time
            
            # 如果没有加载模型，先加载
            if not hasattr(self, '_embedding_model'):
                model_path = settings.EMBEDDING_MODEL or 'BAAI/bge-m3'
                logger.info(f"🔄 正在加载 Embedding 模型: {model_path}")
                
                # 检查是否是本地路径
                import os
                if os.path.exists(model_path):
                    logger.info(f"💾 从本地路径加载模型: {model_path}")
                    start_time = time.time()
                    self._embedding_model = SentenceTransformer(
                        model_path,
                        device=settings.EMBEDDING_DEVICE or 'cpu'
                    )
                    load_time = time.time() - start_time
                    logger.info(f"✅ Embedding 模型加载成功（耗时: {load_time:.2f}s）")
                else:
                    logger.info(f"🌐 从 HuggingFace 下载模型: {model_path}")
                    start_time = time.time()
                    self._embedding_model = SentenceTransformer(
                        model_path,
                        device=settings.EMBEDDING_DEVICE or 'cpu',
                        cache_folder=settings.EMBEDDING_CACHE_FOLDER
                    )
                    load_time = time.time() - start_time
                    logger.info(f"✅ Embedding 模型加载成功（耗时: {load_time:.2f}s）")
            
            # 生成向量
            start_time = time.time()
            vector = self._embedding_model.encode(text, normalize_embeddings=True)
            encode_time = time.time() - start_time
            logger.info(f"🧬 文本编码完成（耗时: {encode_time:.3f}s, 维度: {len(vector)}）")
            
            return vector.tolist()
        except Exception as e:
            logger.error(f"❌ Embedding 模型加载或编码失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # 如果模型加载失败，返回零向量（仅供测试）
            return [0.0] * settings.EMBEDDING_DIMENSION
    
    async def keyword_search(
        self,
        collection_name: str,
        query_text: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        关键词检索 (BM25)
        
        Args:
            collection_name: 集合名称
            query_text: 查询文本
            top_k: 返回数量
        
        Returns:
            检索结果列表
        """
        # 简单实现：使用向量检索作为后备
        # TODO: 实现真正的 BM25 关键词检索
        # 可以使用 Elasticsearch 或 rank_bm25
        return await self.vector_search(
            collection_name=collection_name,
            query_text=query_text,
            top_k=top_k,
            score_threshold=0.0  # 关键词检索不使用阈值
        )
    
    async def hybrid_search(
        self,
        collection_name: str,
        query_text: str,
        top_k: int = 10,
        score_threshold: float = 0.7,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        混合检索 (向量 + 关键词)
        
        Args:
            collection_name: 集合名称
            query_text: 查询文本
            top_k: 返回数量
            score_threshold: 相似度阈值
            vector_weight: 向量检索权重
            keyword_weight: 关键词检索权重
        
        Returns:
            融合后的检索结果列表
        """
        # 目前简化实现：直接使用向量检索
        # TODO: 实现真正的混合检索（向量 + BM25）
        return await self.vector_search(
            collection_name=collection_name,
            query_text=query_text,
            top_k=top_k,
            score_threshold=score_threshold
        )
    
    def _merge_results(
        self,
        vector_results: List[SearchResult],
        keyword_results: List[SearchResult],
        vector_weight: float,
        keyword_weight: float
    ) -> List[SearchResult]:
        """融合检索结果"""
        result_map: Dict[str, SearchResult] = {}
        
        # 处理向量检索结果
        for r in vector_results:
            if r.id not in result_map:
                result_map[r.id] = SearchResult(
                    id=r.id,
                    content=r.content,
                    score=r.score * vector_weight,
                    metadata=r.metadata,
                    source=r.source
                )
            else:
                result_map[r.id].score += r.score * vector_weight
        
        # 处理关键词检索结果
        for r in keyword_results:
            if r.id not in result_map:
                result_map[r.id] = SearchResult(
                    id=r.id,
                    content=r.content,
                    score=r.score * keyword_weight,
                    metadata=r.metadata,
                    source=r.source
                )
            else:
                result_map[r.id].score += r.score * keyword_weight
        
        return list(result_map.values())
    
    async def add_texts(
        self,
        collection_name: str,
        texts: List[str],
        metadatas: List[Dict[str, Any]] = None
    ):
        """添加文本到集合"""
        logger.info(f"========== 开始向量化存储 ==========")
        logger.info(f"集合名称: {collection_name}")
        logger.info(f"文本数量: {len(texts)}")
        
        await self.connect()
        
        # 生成 embeddings
        logger.info(f"开始批量生成 {len(texts)} 个向量...")
        vectors = []
        import time
        start_time = time.time()
        
        for i, text in enumerate(texts):
            vector = await self._text_to_vector(text)
            vectors.append(vector)
            if (i + 1) % 5 == 0 or (i + 1) == len(texts):
                logger.info(f"  进度: {i+1}/{len(texts)} ({(i+1)/len(texts)*100:.1f}%)")
        
        total_time = time.time() - start_time
        logger.info(f"向量生成完成（总耗时: {total_time:.2f}s, 平均: {total_time/len(texts):.3f}s/文本）")
        
        # 准备数据
        logger.info(f"准备插入数据...")
        entities = [
            vectors,  # embedding field
            texts,    # content field
            metadatas if metadatas else [{} for _ in texts],  # metadata field
            [meta.get("source", "") for meta in (metadatas or [{} for _ in texts])]  # source field
        ]
        
        logger.info(f"开始插入到 Milvus Collection: {collection_name}")
        collection = Collection(collection_name)
        collection.insert(entities)
        logger.info(f"数据插入完成，执行 flush...")
        collection.flush()
        logger.info(f"✅ Flush 完成！")
        logger.info(f"========== 向量化存储完成 ==========")
    
    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """对检索结果进行重排序"""
        # TODO: 集成 BGE-Reranker 模型
        # 目前直接返回原结果
        results = []
        for i, doc in enumerate(documents[:top_n]):
            results.append({
                "id": str(i),
                "content": doc,
                "score": 1.0 - (i * 0.1),  # 模拟分数
                "metadata": {},
                "source": ""
            })
        return results
    
    async def search(
        self,
        collection_name: str,
        query: str,
        query_vector: List[float],
        mode: str = "hybrid",
        top_k: int = 10,
        threshold: float = 0.7
    ) -> List[SearchResult]:
        """
        统一检索接口
        
        Args:
            collection_name: 集合名称
            query: 查询文本
            query_vector: 查询向量
            mode: 检索模式 (vector/keyword/hybrid)
            top_k: 返回数量
            threshold: 相似度阈值
        
        Returns:
            检索结果列表
        """
        if mode == "vector":
            return await self.vector_search(
                collection_name, query_vector, top_k, threshold
            )
        elif mode == "keyword":
            return await self.keyword_search(
                collection_name, query, top_k
            )
        else:  # hybrid
            return await self.hybrid_search(
                collection_name, query, query_vector, top_k, threshold
            )


class RerankService:
    """重排序服务"""
    
    def __init__(self):
        self.model = None
    
    async def load_model(self):
        """加载重排序模型"""
        # TODO: 加载BGE-Reranker模型
        # from FlagEmbedding import FlagReranker
        # self.model = FlagReranker('BAAI/bge-reranker-v2-m3')
        pass
    
    async def rerank(
        self,
        query: str,
        results: List[SearchResult],
        top_n: int = 5
    ) -> List[SearchResult]:
        """
        对检索结果进行重排序
        
        Args:
            query: 查询文本
            results: 检索结果
            top_n: 返回数量
        
        Returns:
            重排序后的结果
        """
        if not self.model:
            # 如果没有加载模型，直接返回原结果
            return results[:top_n]
        
        # TODO: 使用模型进行重排序
        # pairs = [[query, r.content] for r in results]
        # scores = self.model.compute_score(pairs)
        # ...
        
        return results[:top_n]


# 全局实例
retrieval_service = RetrievalService()
rerank_service = RerankService()
