"""
知识库路由
"""
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.knowledge import (
    KnowledgeBaseCreate, KnowledgeBaseResponse, KnowledgeBaseUpdate,
    RetrievalConfigUpdate, RetrievalConfigResponse, DocumentResponse,
    SearchRequest, SearchResult
)
from app.schemas.common import ApiResponse, PaginatedResponse
from app.services.knowledge_service import KnowledgeService
from app.core.logger import logger

router = APIRouter(prefix="/knowledge", tags=["知识库"])

@router.post("/collections", response_model=ApiResponse[KnowledgeBaseResponse])
async def create_knowledge_base(
    kb_in: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建知识库集合"""
    logger.info(f"用户 {current_user.username} 请求创建知识库: {kb_in.name}")
    kb_service = KnowledgeService(db)
    kb = await kb_service.create_knowledge_base(current_user.id, kb_in)
    return ApiResponse(data=KnowledgeBaseResponse.from_orm(kb))

@router.get("/collections", response_model=ApiResponse[List[KnowledgeBaseResponse]])
async def list_knowledge_bases(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取所有知识库列表"""
    kb_service = KnowledgeService(db)
    kbs = await kb_service.get_user_knowledge_bases(current_user.id)
    return ApiResponse(data=[KnowledgeBaseResponse.from_orm(kb) for kb in kbs])

@router.get("/collections/{kb_id}", response_model=ApiResponse[KnowledgeBaseResponse])
async def get_knowledge_base(
    kb_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取指定知识库详情"""
    kb_service = KnowledgeService(db)
    kb = await kb_service.get_knowledge_base(kb_id)
    if not kb or kb.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return ApiResponse(data=KnowledgeBaseResponse.from_orm(kb))

@router.delete("/collections/{kb_id}", response_model=ApiResponse[None])
async def delete_knowledge_base(
    kb_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除知识库"""
    kb_service = KnowledgeService(db)
    kb = await kb_service.get_knowledge_base(kb_id)
    if not kb or kb.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    await kb_service.delete_knowledge_base(kb_id)
    return ApiResponse(message="知识库已删除")

@router.get("/collections/{kb_id}/config", response_model=ApiResponse[RetrievalConfigResponse])
async def get_retrieval_config(
    kb_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取检索配置"""
    kb_service = KnowledgeService(db)
    kb = await kb_service.get_knowledge_base(kb_id)
    if not kb or kb.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    return ApiResponse(data=RetrievalConfigResponse(
        chunk_size=kb.chunk_size,
        chunk_overlap=kb.chunk_overlap,
        top_k=kb.top_k,
        top_n=kb.top_n,
        similarity_threshold=kb.similarity_threshold,
        search_mode=kb.search_mode,
        rerank_enabled=kb.rerank_enabled
    ))

@router.put("/collections/{kb_id}/config", response_model=ApiResponse[RetrievalConfigResponse])
async def update_retrieval_config(
    kb_id: str,
    config: RetrievalConfigUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新检索配置"""
    kb_service = KnowledgeService(db)
    kb = await kb_service.get_knowledge_base(kb_id)
    if not kb or kb.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    updated_kb = await kb_service.update_retrieval_config(kb_id, config)
    return ApiResponse(data=RetrievalConfigResponse(
        chunk_size=updated_kb.chunk_size,
        chunk_overlap=updated_kb.chunk_overlap,
        top_k=updated_kb.top_k,
        top_n=updated_kb.top_n,
        similarity_threshold=updated_kb.similarity_threshold,
        search_mode=updated_kb.search_mode,
        rerank_enabled=updated_kb.rerank_enabled
    ))
