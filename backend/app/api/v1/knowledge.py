"""
知识库路由
"""
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func

from backend.app.api.deps import get_db
from backend.app.core.security import get_current_active_user
from backend.app.models.user import User
from backend.app.schemas.knowledge import (
    KnowledgeBaseCreate, KnowledgeBaseResponse, KnowledgeBaseUpdate,
    RetrievalConfigUpdate, RetrievalConfigResponse, DocumentResponse,
    SearchRequest, SearchResult
)
from backend.app.schemas.common import ApiResponse, PaginatedResponse
from backend.app.services.knowledge_service import KnowledgeService
from backend.app.core.logger import logger

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
    return ApiResponse(data=KnowledgeBaseResponse.model_validate(kb))

@router.get("/collections", response_model=ApiResponse[List[KnowledgeBaseResponse]])
async def list_knowledge_bases(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取所有知识库列表"""
    logger.info(f"用户 {current_user.username} 请求获取知识库列表")
    kb_service = KnowledgeService(db)
    kbs = await kb_service.get_user_knowledge_bases(current_user.id)
    logger.info(f"找到 {len(kbs)} 个知识库")
    return ApiResponse(data=[KnowledgeBaseResponse.model_validate(kb) for kb in kbs])

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
    return ApiResponse(data=KnowledgeBaseResponse.model_validate(kb))

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

@router.get("/collections/{kb_id}/documents", response_model=ApiResponse[PaginatedResponse[DocumentResponse]])
async def list_documents(
    kb_id: str,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取知识库文档列表"""
    # 简单实现，后续可移入 service
    from sqlalchemy import select
    from app.models.knowledge import Document
    
    # 验证权限
    kb_service = KnowledgeService(db)
    kb = await kb_service.get_knowledge_base(kb_id)
    if not kb or kb.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
        
    result = await db.execute(
        select(Document).where(Document.knowledge_base_id == kb_id)
        .offset((page - 1) * page_size).limit(page_size)
    )
    docs = result.scalars().all()
    
    total_result = await db.execute(
        select(func.count()).select_from(Document).where(Document.knowledge_base_id == kb_id)
    )
    total = total_result.scalar()
    
    return ApiResponse(data=PaginatedResponse(
        items=[DocumentResponse.model_validate(doc) for doc in docs],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    ))

@router.post("/upload")
async def upload_document(
    collection_id: str = File(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """上传文档接口"""
    import uuid
    import os
    from minio import Minio
    from minio.error import S3Error
    from app.core.config import settings
    from app.models.knowledge import Document
    
    logger.info(f"用户 {current_user.username} 上传文件: {file.filename} 到知识库: {collection_id}")
    
    # 验证知识库权限
    kb_service = KnowledgeService(db)
    kb = await kb_service.get_knowledge_base(collection_id)
    if not kb or kb.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    try:
        # 1. 初始化 MinIO 客户端
        minio_client = Minio(
            settings.MINIO_ENDPOINT.replace('http://', '').replace('https://', ''),
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )
        
        # 确保 bucket 存在
        bucket_name = "agonx-documents"
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
        
        # 2. 生成文件路径
        doc_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file.filename)[1]
        object_name = f"{collection_id}/{doc_id}{file_ext}"
        
        # 3. 上传文件到 MinIO
        file_content = await file.read()
        file_size = len(file_content)
        
        from io import BytesIO
        minio_client.put_object(
            bucket_name,
            object_name,
            BytesIO(file_content),
            length=file_size,
            content_type=file.content_type or 'application/octet-stream'
        )
        
        # 4. 创建文档记录
        document = Document(
            id=doc_id,
            knowledge_base_id=collection_id,
            filename=file.filename,
            file_path=object_name,
            file_size=file_size,
            file_type=file_ext,
            status="processing"
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        # 5. 异步触发向量化任务（后台处理）
        # TODO: 实现异步任务队列（Celery 或 asyncio task）
        # 暂时同步处理
        try:
            await _process_document_vectorization(
                doc_id, 
                collection_id, 
                kb.collection_name,
                object_name, 
                file_content, 
                db
            )
        except Exception as e:
            logger.error(f"向量化失败: {str(e)}")
            document.status = "failed"
            document.error_message = str(e)
            await db.commit()
        
        logger.info(f"文档上传成功: {file.filename}")
        return ApiResponse(
            message="文件已上传，正在处理",
            data={"document_id": doc_id, "status": document.status}
        )
    
    except S3Error as e:
        logger.error(f"MinIO 上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")
    except Exception as e:
        logger.error(f"文档上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


async def _process_document_vectorization(
    doc_id: str,
    kb_id: str,
    collection_name: str,
    file_path: str,
    file_content: bytes,
    db: AsyncSession
):
    """处理文档向量化"""
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
    from app.knowledge.retrieval import retrieval_service
    from app.models.knowledge import Document
    from sqlalchemy import select
    import tempfile
    import os
    
    logger.info(f"开始处理文档 {doc_id} 的向量化")
    
    # 1. 将文件写入临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_path)[1]) as tmp:
        tmp.write(file_content)
        tmp_path = tmp.name
    
    try:
        # 2. 根据文件类型加载文档
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            loader = PyPDFLoader(tmp_path)
        elif file_ext in ['.txt', '.md']:
            loader = TextLoader(tmp_path, encoding='utf-8')
        elif file_ext in ['.doc', '.docx']:
            loader = Docx2txtLoader(tmp_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        documents = loader.load()
        
        # 3. 文档分块
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=50,
            length_function=len
        )
        chunks = text_splitter.split_documents(documents)
        
        # 4. 生成 embedding 并存储到 Milvus
        await retrieval_service.connect()
        
        texts = [chunk.page_content for chunk in chunks]
        metadatas = [
            {
                "document_id": doc_id,
                "kb_id": kb_id,
                "page": chunk.metadata.get("page", 0),
                "source": file_path
            }
            for chunk in chunks
        ]
        
        # 使用 retrieval_service 插入向量
        await retrieval_service.add_texts(
            collection_name=collection_name,
            texts=texts,
            metadatas=metadatas
        )
        
        # 5. 更新文档状态
        doc_query = select(Document).where(Document.id == doc_id)
        result = await db.execute(doc_query)
        document = result.scalar_one()
        
        document.status = "completed"
        document.chunk_count = len(chunks)
        await db.commit()
        
        logger.info(f"文档 {doc_id} 向量化完成，共 {len(chunks)} 个分块")
        
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

@router.post("/search", response_model=ApiResponse[List[SearchResult]])
async def search_knowledge(
    search_req: SearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """知识库检索接口"""
    logger.info(f"用户 {current_user.username} 请求检索: {search_req.query}")
    
    # 验证权限
    kb_service = KnowledgeService(db)
    kb = await kb_service.get_knowledge_base(search_req.collection_id)
    if not kb or kb.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    try:
        from app.knowledge.retrieval import retrieval_service
        
        # 连接 Milvus
        await retrieval_service.connect()
        
        # 根据检索模式进行检索
        search_mode = search_req.search_mode or kb.search_mode
        top_k = search_req.top_k or kb.top_k
        
        if search_mode == "vector":
            # 纯向量检索
            results = await retrieval_service.vector_search(
                collection_name=kb.collection_name,
                query_text=search_req.query,
                top_k=top_k,
                score_threshold=search_req.similarity_threshold or kb.similarity_threshold
            )
        elif search_mode == "keyword":
            # 关键词检索（简单实现，可使用 BM25）
            results = await retrieval_service.keyword_search(
                collection_name=kb.collection_name,
                query_text=search_req.query,
                top_k=top_k
            )
        elif search_mode == "hybrid":
            # 混合检索
            results = await retrieval_service.hybrid_search(
                collection_name=kb.collection_name,
                query_text=search_req.query,
                top_k=top_k,
                score_threshold=search_req.similarity_threshold or kb.similarity_threshold
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported search mode: {search_mode}")
        
        # 如果启用 Reranker，进行重排序
        if kb.rerank_enabled and results:
            results = await retrieval_service.rerank(
                query=search_req.query,
                documents=[r["content"] for r in results],
                top_n=kb.top_n
            )
        
        # 转换为响应格式
        search_results = [
            SearchResult(
                id=str(r.get("id", "")),
                content=r.get("content", ""),
                score=float(r.get("score", 0.0)),
                metadata=r.get("metadata", {}),
                source=r.get("source", "")
            )
            for r in results
        ]
        
        logger.info(f"检索完成，返回 {len(search_results)} 条结果")
        return ApiResponse(data=search_results)
    
    except Exception as e:
        logger.error(f"检索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.delete("/documents/{document_id}", response_model=ApiResponse[None])
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除文档"""
    from app.models.knowledge import Document
    from sqlalchemy import select
    
    # 查找文档
    doc_query = select(Document).where(Document.id == document_id)
    result = await db.execute(doc_query)
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # 验证权限（通过知识库）
    kb_service = KnowledgeService(db)
    kb = await kb_service.get_knowledge_base(document.knowledge_base_id)
    if not kb or kb.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # 删除文档
    await db.delete(document)
    await db.commit()
    
    logger.info(f"用户 {current_user.username} 删除文档: {document.filename}")
    return ApiResponse(message="文档已删除")

