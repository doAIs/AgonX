from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.sql import func
from backend.app.core.database import Base


class ModelConfig(Base):
    """模型配置"""
    __tablename__ = "model_configs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)  # openai, qwen, deepseek, glm
    model_type = Column(String(20), nullable=False)  # llm, embedding
    api_key = Column(String(500), nullable=False)
    base_url = Column(String(500), nullable=True)
    is_default = Column(Boolean, default=False)
    
    # LLM参数
    temperature = Column(Float, default=0.7)
    top_p = Column(Float, default=0.9)
    max_tokens = Column(Integer, default=4096)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ModelConfig(id={self.id}, name={self.name}, provider={self.provider})>"
