"""
知识库服务
处理知识库的创建、管理、文档上传及检索逻辑
"""
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, func

from app.models.knowledge import KnowledgeBase, Document
from app.schemas.knowledge import KnowledgeBaseCreate, KnowledgeBaseUpdate, RetrievalConfigUpdate
from app.knowledge.retrieval import retrieval_service
from app.core.logger import logger
from pymilvus import CollectionSchema, FieldSchema, DataType, Collection, connections, utility
from app.core.config import settings

class KnowledgeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_knowledge_base(self, user_id: int, kb_in: KnowledgeBaseCreate) -> KnowledgeBase:
        """创建知识库及Milvus集合"""
        kb_id = str(uuid.uuid4())
        # 集合名使用 agonx_前缀 + UUID 的一部分，确保唯一且符合命名规范
        collection_name = f"agonx_{kb_id.replace('-', '_')}"
        
        # 1. 在Milvus中创建集合
        await self._create_milvus_collection(collection_name)
        
        # 2. 在MySQL中保存元数据
        db_kb = KnowledgeBase(
            id=kb_id,
            user_id=user_id,
            name=kb_in.name,
            description=kb_in.description,
            collection_name=collection_name
        )
        self.db.add(db_kb)
        await self.db.commit()
        await self.db.refresh(db_kb)
        
        logger.info(f"知识库创建成功: {db_kb.name} (ID: {db_kb.id}, Collection: {collection_name})")
        return db_kb

    async def _create_milvus_collection(self, collection_name: str):
        """创建Milvus集合"""
        await retrieval_service.connect()
        
        if utility.has_collection(collection_name):
            return

        # 定义Schema
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=settings.EMBEDDING_DIMENSION),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="metadata", dtype=DataType.JSON),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=500)
        ]
        schema = CollectionSchema(fields, description="AgonX Knowledge Base Collection")
        
        collection = Collection(name=collection_name, schema=schema)
        
        # 创建索引
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        logger.info(f"Milvus集合创建并初始化索引成功: {collection_name}")

    async def get_user_knowledge_bases(self, user_id: int) -> List[KnowledgeBase]:
        """获取用户的所有知识库"""
        result = await self.db.execute(
            select(KnowledgeBase).where(KnowledgeBase.user_id == user_id)
        )
        return result.scalars().all()

    async def get_knowledge_base(self, kb_id: str) -> Optional[KnowledgeBase]:
        """通过ID获取知识库"""
        result = await self.db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        return result.scalar_one_or_none()

    async def delete_knowledge_base(self, kb_id: str):
        """删除知识库及关联数据"""
        kb = await self.get_knowledge_base(kb_id)
        if not kb:
            return
        
        # 1. 删除Milvus集合
        await retrieval_service.connect()
        if utility.has_collection(kb.collection_name):
            utility.drop_collection(kb.collection_name)
            logger.info(f"Milvus集合已删除: {kb.collection_name}")
        
        # 2. 删除MySQL中的记录 (由于CASCADE，会自动删除关联的Document)
        await self.db.delete(kb)
        await self.db.commit()
        logger.info(f"知识库记录已从数据库中删除: {kb_id}")

    async def update_retrieval_config(self, kb_id: str, config: RetrievalConfigUpdate) -> KnowledgeBase:
        """更新检索配置"""
        kb = await self.get_knowledge_base(kb_id)
        if not kb:
            raise ValueError("Knowledge base not found")
        
        for field, value in config.dict(exclude_unset=True).items():
            setattr(kb, field, value)
        
        await self.db.commit()
        await self.db.refresh(kb)
        return kb

