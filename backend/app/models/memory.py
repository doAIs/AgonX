from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.sql import func
from backend.app.core.database import Base


class LongTermMemory(Base):
    """长期记忆模型"""
    __tablename__ = "long_term_memories"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    importance = Column(Float, default=0.5)  # 重要度 0-1
    category = Column(String(50), nullable=True)  # 记忆分类
    vector_id = Column(String(100), nullable=True)  # Milvus中的向量ID
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<LongTermMemory(id={self.id}, importance={self.importance})>"
