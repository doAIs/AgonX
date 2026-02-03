"""
知识库检索服务
支持向量检索、关键词检索、混合检索
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pymilvus import connections, Collection, utility
from app.core.config import settings


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
        query_vector: List[float],
        top_k: int = 10,
        threshold: float = 0.7,
        filter_expr: str = None
    ) -> List[SearchResult]:
        """
        向量检索
        
        Args:
            collection_name: 集合名称
            query_vector: 查询向量
            top_k: 返回数量
            threshold: 相似度阈值
            filter_expr: 过滤表达式
        
        Returns:
            检索结果列表
        """
        await self.connect()
        
        collection = Collection(collection_name)
        collection.load()
        
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        
        results = collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=filter_expr,
            output_fields=["content", "metadata", "source"]
        )
        
        search_results = []
        for hits in results:
            for hit in hits:
                if hit.score >= threshold:
                    search_results.append(SearchResult(
                        id=str(hit.id),
                        content=hit.entity.get("content", ""),
                        score=hit.score,
                        metadata=hit.entity.get("metadata", {}),
                        source=hit.entity.get("source", "")
                    ))
        
        return search_results
    
    async def keyword_search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        关键词检索 (BM25)
        
        Args:
            collection_name: 集合名称
            query: 查询文本
            top_k: 返回数量
        
        Returns:
            检索结果列表
        """
        # TODO: 实现BM25关键词检索
        # 可以使用Elasticsearch或自定义实现
        return []
    
    async def hybrid_search(
        self,
        collection_name: str,
        query: str,
        query_vector: List[float],
        top_k: int = 10,
        threshold: float = 0.7,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> List[SearchResult]:
        """
        混合检索 (向量 + 关键词)
        
        Args:
            collection_name: 集合名称
            query: 查询文本
            query_vector: 查询向量
            top_k: 返回数量
            threshold: 相似度阈值
            vector_weight: 向量检索权重
            keyword_weight: 关键词检索权重
        
        Returns:
            融合后的检索结果列表
        """
        # 向量检索
        vector_results = await self.vector_search(
            collection_name,
            query_vector,
            top_k * 2,
            threshold * 0.8  # 降低阈值以获取更多候选
        )
        
        # 关键词检索
        keyword_results = await self.keyword_search(
            collection_name,
            query,
            top_k * 2
        )
        
        # 融合结果
        merged = self._merge_results(
            vector_results,
            keyword_results,
            vector_weight,
            keyword_weight
        )
        
        # 按分数排序并截取
        merged.sort(key=lambda x: x.score, reverse=True)
        return merged[:top_k]
    
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
