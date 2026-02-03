from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class KnowledgeBase(Base):
    """知识库模型"""
    __tablename__ = "knowledge_bases"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    collection_name = Column(String(100), unique=True, nullable=False)  # Milvus集合名
    
    # 检索配置
    chunk_size = Column(Integer, default=512)
    chunk_overlap = Column(Integer, default=50)
    top_k = Column(Integer, default=10)
    top_n = Column(Integer, default=5)
    similarity_threshold = Column(Float, default=0.7)
    search_mode = Column(String(20), default="hybrid")  # vector, keyword, hybrid
    rerank_enabled = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, name={self.name})>"


class Document(Base):
    """文档模型"""
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, index=True)
    knowledge_base_id = Column(String(36), ForeignKey("knowledge_bases.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # MinIO路径
    file_size = Column(Integer, default=0)
    file_type = Column(String(50), nullable=True)
    chunk_count = Column(Integer, default=0)
    status = Column(String(20), default="processing")  # processing, completed, failed
    error_message = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename})>"
