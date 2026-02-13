"""
富媒体文档数据模型
支持图片、表格、OCR等
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, Float, Enum, JSON, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class DocumentPage(Base):
    """文档页面模型"""
    __tablename__ = "document_pages"
    
    id = Column(String(36), primary_key=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False, comment="页码（从1开始）")
    page_image_path = Column(String(500), comment="MinIO中页面截图路径")
    page_thumbnail_path = Column(String(500), comment="缩略图路径")
    width = Column(Integer, comment="页面宽度")
    height = Column(Integer, comment="页面高度")
    has_text = Column(Boolean, default=True, comment="是否包含文本")
    has_images = Column(Boolean, default=False, comment="是否包含图片")
    has_tables = Column(Boolean, default=False, comment="是否包含表格")
    ocr_text = Column(Text, comment="OCR识别的文本")
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # 关系
    document = relationship("Document", back_populates="pages")
    elements = relationship("DocumentElement", back_populates="page", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="page")


class DocumentElement(Base):
    """文档元素模型（图片、表格等）"""
    __tablename__ = "document_elements"
    
    id = Column(String(36), primary_key=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    page_id = Column(String(36), ForeignKey("document_pages.id", ondelete="CASCADE"), nullable=False)
    element_type = Column(
        Enum('image', 'table', 'chart', 'formula', 'diagram', name='element_type_enum'),
        nullable=False,
        comment="元素类型"
    )
    element_path = Column(String(500), comment="MinIO中元素文件路径")
    thumbnail_path = Column(String(500), comment="缩略图路径")
    position = Column(JSON, comment="位置信息 {x, y, width, height}")
    ocr_text = Column(Text, comment="OCR识别的文字")
    description = Column(Text, comment="AI生成的描述")
    meta_info = Column(JSON, comment="额外元数据")  # 注意：不能使用'metadata'作为字段名，因为它是SQLAlchemy的保留字
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # 关系
    document = relationship("Document", back_populates="elements")
    page = relationship("DocumentPage", back_populates="elements")
    ocr_tasks = relationship("OCRTask", back_populates="element", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """文档分块模型"""
    __tablename__ = "document_chunks"
    
    id = Column(String(36), primary_key=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    page_id = Column(String(36), ForeignKey("document_pages.id", ondelete="SET NULL"))
    chunk_index = Column(Integer, nullable=False, comment="分块索引")
    content = Column(Text, nullable=False, comment="分块文本内容")
    vector_id = Column(String(100), comment="Milvus中的向量ID")
    start_position = Column(JSON, comment="起始位置")
    end_position = Column(JSON, comment="结束位置")
    related_elements = Column(JSON, comment="关联的元素ID列表")
    prev_chunk_id = Column(String(36), comment="上一个分块ID")
    next_chunk_id = Column(String(36), comment="下一个分块ID")
    token_count = Column(Integer, comment="Token数量")
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # 关系
    document = relationship("Document", back_populates="chunks")
    page = relationship("DocumentPage", back_populates="chunks")


class OCRTask(Base):
    """OCR任务模型"""
    __tablename__ = "ocr_tasks"
    
    id = Column(String(36), primary_key=True)
    element_id = Column(String(36), ForeignKey("document_elements.id", ondelete="CASCADE"), nullable=False)
    status = Column(
        Enum('pending', 'processing', 'completed', 'failed', name='ocr_status_enum'),
        default='pending'
    )
    ocr_engine = Column(String(50), comment="OCR引擎")
    result_text = Column(Text, comment="识别结果")
    confidence = Column(Float, comment="置信度")
    error_message = Column(Text, comment="错误信息")
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # 关系
    element = relationship("DocumentElement", back_populates="ocr_tasks")
