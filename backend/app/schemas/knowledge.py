from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime


# 知识库相关
class KnowledgeBaseCreate(BaseModel):
    name: str
    description: Optional[str] = None


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class RetrievalConfigUpdate(BaseModel):
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    top_k: Optional[int] = None
    top_n: Optional[int] = None
    similarity_threshold: Optional[float] = None
    search_mode: Optional[str] = None
    rerank_enabled: Optional[bool] = None


class RetrievalConfigResponse(BaseModel):
    chunk_size: int
    chunk_overlap: int
    top_k: int
    top_n: int
    similarity_threshold: float
    search_mode: str
    rerank_enabled: bool


class KnowledgeBaseResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    document_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


# 文档相关
class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_size: int
    chunk_count: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# 检索相关
class SearchRequest(BaseModel):
    collection_id: str
    query: str
    top_k: Optional[int] = 10
    similarity_threshold: Optional[float] = 0.7
    search_mode: Optional[str] = "hybrid"


class SearchResult(BaseModel):
    id: str
    content: str
    score: float
    metadata: Optional[Dict[str, Any]] = None
    source: str
