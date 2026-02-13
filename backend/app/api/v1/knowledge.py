"""
知识库路由
"""
from typing import List, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from minio import Minio

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
    
    logger.info(f"========== 文档上传请求 ==========")
    logger.info(f"用户: {current_user.username}")
    logger.info(f"文件名: {file.filename}")
    logger.info(f"Content-Type: {file.content_type}")
    logger.info(f"知识库ID: {collection_id}")
    
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
    """处理文档向量化（增强版，支持图片、OCR、页面映射）"""
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from app.knowledge.retrieval import retrieval_service
    from app.models.knowledge import Document
    from app.models.document_rich import DocumentPage, DocumentElement, DocumentChunk
    from sqlalchemy import select
    from minio import Minio
    from app.core.config import settings
    from app.services.rich_document_processor import RichDocumentProcessor
    import uuid
    import os
    import json
    
    logger.info(f"========== 开始文档向量化（富媒体模式） ==========")
    logger.info(f"文档ID: {doc_id}")
    logger.info(f"知识库ID: {kb_id}")
    logger.info(f"Collection: {collection_name}")
    logger.info(f"文件路径: {file_path}")
    
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        # 初始化MinIO客户端
        minio_client = Minio(
            settings.MINIO_ENDPOINT.replace('http://', '').replace('https://', ''),
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )
        
        # 如果是PDF，使用富媒体处理器
        if file_ext == '.pdf':
            await _process_pdf_rich_media(
                doc_id, kb_id, collection_name, file_path, file_content,
                minio_client, db
            )
        else:
            # 非PDF文档，使用原有逻辑
            await _process_simple_document(
                doc_id, kb_id, collection_name, file_path, file_content,
                file_ext, db
            )
        
        logger.info(f"========== 文档向量化完成 ==========")
        
    except Exception as e:
        logger.error(f"文档向量化失败: {str(e)}")
        # 更新文档状态为失败
        doc_query = select(Document).where(Document.id == doc_id)
        result = await db.execute(doc_query)
        document = result.scalar_one()
        document.status = "failed"
        document.error_message = str(e)
        await db.commit()
        raise


async def _process_pdf_rich_media(
    doc_id: str,
    kb_id: str,
    collection_name: str,
    file_path: str,
    file_content: bytes,
    minio_client: Minio,
    db: AsyncSession
):
    """处理PDF文档（富媒体模式）"""
    import fitz  # PyMuPDF
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from app.knowledge.retrieval import retrieval_service
    from app.models.knowledge import Document
    from app.models.document_rich import DocumentPage, DocumentElement, DocumentChunk
    from app.services.rich_document_processor import RichDocumentProcessor
    from sqlalchemy import select
    import uuid
    import json
    
    try:
        logger.info(f"[步骤1/6] 打开PDF文档...")
        pdf_doc = fitz.open(stream=file_content, filetype="pdf")
        page_count = len(pdf_doc)
        logger.info(f"PDF总页数: {page_count}")
    except Exception as e:
        logger.error(f"打开PDF文档失败: {str(e)}")
        raise ValueError(f"无法解析PDF文档: {str(e)}")
    
    # 初始化处理器
    try:
        processor = RichDocumentProcessor(minio_client)
    except Exception as e:
        logger.error(f"初始化文档处理器失败: {str(e)}")
        pdf_doc.close()
        raise ValueError(f"初始化失败: {str(e)}")
    
    # 统计信息
    total_images = 0
    total_chunks = 0
    has_images = False
    has_tables = False
    
    # 文本分块器
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=50,
        length_function=len
    )
    
    logger.info(f"[步骤2/6] 逐页处理PDF...")
    
    # 逐页处理
    for page_num in range(page_count):
        try:
            # 处理单个页面
            page_data = await processor.process_pdf_page(
                pdf_doc, page_num, doc_id, kb_id
            )
            
            # 创建页面记录
            page_id = str(uuid.uuid4())
            page_record = DocumentPage(
                id=page_id,
                document_id=doc_id,
                **page_data['page_info']
            )
            db.add(page_record)
            
            # 创建图片元素记录
            page_elements = []
            for img_info in page_data['images']:
                element = DocumentElement(
                    id=img_info['element_id'],
                    document_id=doc_id,
                    page_id=page_id,
                    element_type=img_info['element_type'],
                    element_path=img_info['element_path'],
                    thumbnail_path=img_info['thumbnail_path'],
                    position=json.dumps(img_info['position']) if img_info['position'] else None,
                    ocr_text=img_info['ocr_text'],
                    metadata=json.dumps(img_info['metadata'])
                )
                db.add(element)
                page_elements.append(img_info['element_id'])
                total_images += 1
            
            # 更新统计
            if page_data['has_images']:
                has_images = True
            if page_data['has_tables']:
                has_tables = True
            
            # 分块处理页面文本
            if page_data['text'].strip():
                chunks = text_splitter.split_text(page_data['text'])
                logger.info(f"  第 {page_num + 1} 页生成 {len(chunks)} 个分块")
                
                for chunk_idx, chunk_text in enumerate(chunks):
                    chunk_id = str(uuid.uuid4())
                    
                    # 创建分块记录（先不生成向量，等待批量处理）
                    chunk_record = DocumentChunk(
                        id=chunk_id,
                        document_id=doc_id,
                        page_id=page_id,
                        chunk_index=total_chunks,
                        content=chunk_text,
                        vector_id=f"vec_{chunk_id}",  # Milvus向量ID
                        start_position=json.dumps({"page": page_num + 1}),
                        related_elements=json.dumps(page_elements) if page_elements else None
                    )
                    db.add(chunk_record)
                    total_chunks += 1
        
        except Exception as e:
            logger.error(f"  处理第 {page_num + 1} 页失败: {str(e)}")
            # 继续处理下一页
    
    pdf_doc.close()
    
    logger.info(f"[步骤3/6] 批量生成向量...")
    # 查询所有chunks
    from sqlalchemy import select
    chunks_query = select(DocumentChunk).where(DocumentChunk.document_id == doc_id)
    chunks_result = await db.execute(chunks_query)
    all_chunks = chunks_result.scalars().all()
    
    if all_chunks:
        texts = [chunk.content for chunk in all_chunks]
        metadatas = [
            {
                "chunk_id": chunk.id,
                "document_id": doc_id,
                "kb_id": kb_id,
                "page_id": chunk.page_id,
                "source": file_path
            }
            for chunk in all_chunks
        ]
        
        logger.info(f"[步骤4/6] 批量存储到Milvus（共 {len(texts)} 个向量）...")
        
        try:
            await retrieval_service.connect()
        except Exception as e:
            logger.error(f"连接Milvus失败: {str(e)}")
            raise ConnectionError(f"无法连接到向量数据库: {str(e)}")
        
        # 分批插入，每批100条
        batch_size = 100
        failed_batches = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_metadatas = metadatas[i:i + batch_size]
            batch_num = i//batch_size + 1
            total_batches = (len(texts) + batch_size - 1) // batch_size
            
            logger.info(f"  插入第 {batch_num}/{total_batches} 批，{len(batch_texts)} 条记录...")
            try:
                await retrieval_service.add_texts(
                    collection_name=collection_name,
                    texts=batch_texts,
                    metadatas=batch_metadatas
                )
                logger.info(f"  ✅ 第 {batch_num}/{total_batches} 批插入成功")
            except Exception as e:
                error_msg = f"第 {batch_num}/{total_batches} 批插入失败: {str(e)}"
                logger.error(f"  ❌ {error_msg}")
                failed_batches.append((batch_num, str(e)))
        
        # 检查是否有失败的批次
        if failed_batches:
            error_summary = "; ".join([f"批次{num}: {err}" for num, err in failed_batches])
            logger.error(f"向量插入部分失败: {error_summary}")
            raise RuntimeError(f"{len(failed_batches)}/{total_batches} 个批次插入失败: {error_summary}")
    else:
        logger.warning("未找到需要向量化的分块")
    
    logger.info(f"[步骤5/6] 提交数据库...")
    await db.commit()
    
    logger.info(f"[步骤6/6] 更新文档状态...")
    # 更新文档状态
    doc_query = select(Document).where(Document.id == doc_id)
    result = await db.execute(doc_query)
    document = result.scalar_one()
    
    document.status = "completed"
    document.chunk_count = total_chunks
    document.content_type = "mixed" if (has_images or has_tables) else "text"
    document.page_count = page_count
    document.has_images = has_images
    document.has_tables = has_tables
    await db.commit()
    
    logger.info(f"✅ PDF处理完成")
    logger.info(f"  总页数: {page_count}")
    logger.info(f"  总分块数: {total_chunks}")
    logger.info(f"  图片数量: {total_images}")
    logger.info(f"  内容类型: {document.content_type}")


async def _process_simple_document(
    doc_id: str,
    kb_id: str,
    collection_name: str,
    file_path: str,
    file_content: bytes,
    file_ext: str,
    db: AsyncSession
):
    """处理简单文档（TXT/Word）"""
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import TextLoader, Docx2txtLoader
    from app.knowledge.retrieval import retrieval_service
    from app.models.knowledge import Document
    from sqlalchemy import select
    import tempfile
    import os
    
    logger.info(f"[简单模式] 处理文档类型: {file_ext}")
    
    # 写入临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        tmp.write(file_content)
        tmp_path = tmp.name
    
    try:
        # 加载文档
        if file_ext in ['.txt', '.md']:
            loader = TextLoader(tmp_path, encoding='utf-8')
        elif file_ext in ['.doc', '.docx']:
            loader = Docx2txtLoader(tmp_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        documents = loader.load()
        
        # 分块
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=50,
            length_function=len
        )
        chunks = text_splitter.split_documents(documents)
        
        # 向量化
        await retrieval_service.connect()
        texts = [chunk.page_content for chunk in chunks]
        metadatas = [
            {
                "document_id": doc_id,
                "kb_id": kb_id,
                "source": file_path
            }
            for chunk in chunks
        ]
        
        await retrieval_service.add_texts(
            collection_name=collection_name,
            texts=texts,
            metadatas=metadatas
        )
        
        # 更新文档状态
        doc_query = select(Document).where(Document.id == doc_id)
        result = await db.execute(doc_query)
        document = result.scalar_one()
        
        document.status = "completed"
        document.chunk_count = len(chunks)
        document.content_type = "text"
        await db.commit()
        
        logger.info(f"✅ 简单文档处理完成，共 {len(chunks)} 个分块")
    
    finally:
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

@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """下载文档"""
    from app.models.knowledge import Document
    from sqlalchemy import select
    from fastapi.responses import StreamingResponse
    from minio import Minio
    from app.core.config import settings
    import io
    
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
    
    try:
        # 从 MinIO 下载文件
        minio_client = Minio(
            settings.MINIO_ENDPOINT.replace('http://', '').replace('https://', ''),
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )
        
        bucket_name = "agonx-documents"
        response = minio_client.get_object(bucket_name, document.file_path)
        
        # 读取文件内容
        file_content = response.read()
        response.close()
        response.release_conn()
        
        logger.info(f"用户 {current_user.username} 下载文档: {document.filename}")
        
        # 返回文件流
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type='application/octet-stream',
            headers={
                'Content-Disposition': f'attachment; filename="{document.filename}"'
            }
        )
    except Exception as e:
        logger.error(f"文档下载失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

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


@router.post("/search/enhanced", response_model=ApiResponse[List[Dict]])
async def enhanced_search(
    search_req: SearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """增强检索接口（返回页面预览、关联图片、上下文等）"""
    from app.models.document_rich import DocumentPage, DocumentElement, DocumentChunk
    from sqlalchemy.orm import selectinload
    from app.core.config import settings
    import json
    
    logger.info(f"用户 {current_user.username} 请求增强检索: {search_req.query}")
    
    # 验证权限
    kb_service = KnowledgeService(db)
    kb = await kb_service.get_knowledge_base(search_req.collection_id)
    if not kb or kb.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    try:
        from app.knowledge.retrieval import retrieval_service
        
        # 1. 向量检索
        logger.info(f"步骤1: 执行向量检索...")
        try:
            await retrieval_service.connect()
        except Exception as e:
            logger.error(f"连接Milvus失败: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"向量数据库服务不可用: {str(e)}"
            )
        
        search_mode = search_req.search_mode or kb.search_mode
        top_k = search_req.top_k or kb.top_k
        
        try:
            results = await retrieval_service.vector_search(
                collection_name=kb.collection_name,
                query_text=search_req.query,
                top_k=top_k,
                score_threshold=search_req.similarity_threshold or kb.similarity_threshold
            )
        except Exception as e:
            logger.error(f"向量检索失败: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"检索失败: {str(e)}"
            )
        
        if not results:
            logger.info("未找到相关结果")
            return ApiResponse(data=[])
        
        logger.info(f"步骤2: 找到 {len(results)} 条原始结果，开始查询增强信息...")
        
        # 2. 查询关联的chunk记录
        chunk_ids = []
        for r in results:
            chunk_id = r.get("metadata", {}).get("chunk_id")
            if chunk_id:
                chunk_ids.append(chunk_id)
        
        if not chunk_ids:
            # 如果没有chunk_id，返回基础结果
            logger.warning("未找到chunk_id，返回基础结果")
            return ApiResponse(data=[
                {
                    "content": r["content"],
                    "score": r["score"],
                    "metadata": r.get("metadata", {})
                }
                for r in results
            ])
        
        # 查询chunks及关联数据
        from sqlalchemy import select
        chunks_query = (
            select(DocumentChunk)
            .where(DocumentChunk.id.in_(chunk_ids))
            .options(
                selectinload(DocumentChunk.page).selectinload(DocumentPage.elements),
                selectinload(DocumentChunk.document)
            )
        )
        chunks_result = await db.execute(chunks_query)
        chunks = chunks_result.scalars().all()
        
        # 3. 构建增强结果
        logger.info(f"步骤3: 构建增强结果...")
        enhanced_results = []
        
        for chunk in chunks:
            # 获取上下文chunk
            context = await _get_context_chunks(chunk, db, context_window=1)
            
            # 获取关联图片
            related_images = []
            if chunk.related_elements:
                try:
                    element_ids = json.loads(chunk.related_elements)
                    if element_ids:
                        elements_query = select(DocumentElement).where(
                            DocumentElement.id.in_(element_ids),
                            DocumentElement.element_type == 'image'
                        )
                        elements_result = await db.execute(elements_query)
                        elements = elements_result.scalars().all()
                        
                        for elem in elements:
                            related_images.append({
                                "url": _get_minio_url(elem.element_path),
                                "thumbnail_url": _get_minio_url(elem.thumbnail_path) if elem.thumbnail_path else None,
                                "ocr_text": elem.ocr_text,
                                "position": json.loads(elem.position) if elem.position else None
                            })
                except Exception as e:
                    logger.error(f"获取关联图片失败: {str(e)}")
            
            # 获取页面信息
            page_info = None
            if chunk.page:
                page_info = {
                    "page_number": chunk.page.page_number,
                    "page_image_url": _get_minio_url(chunk.page.page_image_path) if chunk.page.page_image_path else None,
                    "thumbnail_url": _get_minio_url(chunk.page.page_thumbnail_path) if chunk.page.page_thumbnail_path else None,
                    "width": chunk.page.width,
                    "height": chunk.page.height
                }
            
            # 组装结果
            enhanced_results.append({
                "id": chunk.id,
                "content": chunk.content,
                "score": next((r["score"] for r in results if r.get("metadata", {}).get("chunk_id") == chunk.id), 0.0),
                "context": context,
                "page_info": page_info,
                "related_images": related_images,
                "document": {
                    "id": chunk.document.id,
                    "filename": chunk.document.filename,
                    "download_url": f"/api/v1/knowledge/documents/{chunk.document.id}/download"
                } if chunk.document else None,
                "metadata": {
                    "chunk_index": chunk.chunk_index,
                    "page_id": chunk.page_id
                }
            })
        
        logger.info(f"增强检索完成，返回 {len(enhanced_results)} 条结果")
        return ApiResponse(data=enhanced_results)
    
    except Exception as e:
        logger.error(f"增强检索失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Enhanced search failed: {str(e)}")


async def _get_context_chunks(
    chunk: 'DocumentChunk',
    db: AsyncSession,
    context_window: int = 1
) -> Dict[str, List[str]]:
    """获取上下文chunk"""
    from app.models.document_rich import DocumentChunk
    from sqlalchemy import select, and_
    
    context = {"before": [], "after": []}
    
    try:
        # 获取前N个chunk
        if context_window > 0:
            before_query = (
                select(DocumentChunk)
                .where(
                    and_(
                        DocumentChunk.document_id == chunk.document_id,
                        DocumentChunk.chunk_index < chunk.chunk_index,
                        DocumentChunk.chunk_index >= chunk.chunk_index - context_window
                    )
                )
                .order_by(DocumentChunk.chunk_index)
            )
            before_result = await db.execute(before_query)
            before_chunks = before_result.scalars().all()
            context["before"] = [c.content for c in before_chunks]
            
            # 获取后N个chunk
            after_query = (
                select(DocumentChunk)
                .where(
                    and_(
                        DocumentChunk.document_id == chunk.document_id,
                        DocumentChunk.chunk_index > chunk.chunk_index,
                        DocumentChunk.chunk_index <= chunk.chunk_index + context_window
                    )
                )
                .order_by(DocumentChunk.chunk_index)
            )
            after_result = await db.execute(after_query)
            after_chunks = after_result.scalars().all()
            context["after"] = [c.content for c in after_chunks]
    
    except Exception as e:
        logger.error(f"获取上下文失败: {str(e)}")
    
    return context


def _get_minio_url(object_path: str) -> str:
    """生成MinIO访问链接（带签名）"""
    if not object_path:
        return None
    
    from app.core.config import settings
    from minio import Minio
    from datetime import timedelta
    
    try:
        # 创建MinIO客户端
        minio_client = Minio(
            settings.MINIO_ENDPOINT.replace('http://', '').replace('https://', ''),
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )
        
        bucket = "agonx-documents"
        
        # 生成预签名URL，有效期7天
        url = minio_client.presigned_get_object(
            bucket_name=bucket,
            object_name=object_path,
            expires=timedelta(days=7)
        )
        
        return url
    except Exception as e:
        logger.error(f"生成MinIO URL失败: {str(e)}")
        # 降级为直接链接
        endpoint = settings.MINIO_ENDPOINT
        bucket = "agonx-documents"
        return f"{endpoint}/{bucket}/{object_path}"

