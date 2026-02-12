"""
嵌入服务
支持多种嵌入模型
"""
from typing import List, Optional
from langchain_openai import OpenAIEmbeddings
from backend.app.core.config import settings


class EmbeddingService:
    """嵌入服务"""
    
    def __init__(
        self,
        model: str = None,
        api_key: str = None,
        base_url: str = None
    ):
        self.model = model or settings.DEFAULT_EMBEDDING_MODEL
        self.api_key = api_key or settings.DEFAULT_LLM_API_KEY
        self.base_url = base_url or settings.DEFAULT_LLM_BASE_URL
        self.dimension = settings.EMBEDDING_DIMENSION
        
        # 初始化嵌入模型
        self.embeddings = self._create_embeddings()
    
    def _create_embeddings(self) -> OpenAIEmbeddings:
        """创建嵌入模型"""
        return OpenAIEmbeddings(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    async def embed_text(self, text: str) -> List[float]:
        """
        将文本转换为向量
        
        Args:
            text: 输入文本
        
        Returns:
            向量列表
        """
        return await self.embeddings.aembed_query(text)
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量将文本转换为向量
        
        Args:
            texts: 输入文本列表
        
        Returns:
            向量列表的列表
        """
        return await self.embeddings.aembed_documents(texts)
    
    def get_dimension(self) -> int:
        """获取向量维度"""
        return self.dimension


# 全局实例
embedding_service = EmbeddingService()
