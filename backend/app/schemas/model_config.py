from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ModelConfigBase(BaseModel):
    """模型配置基础Schema"""
    model_config = ConfigDict(protected_namespaces=())
    
    name: str
    provider: str  # openai, anthropic, deepseek, qwen, glm
    model_type: str  # llm, embedding
    api_key: str
    base_url: Optional[str] = None
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    max_tokens: Optional[int] = 4096


class ModelConfigCreate(ModelConfigBase):
    """创建模型配置"""
    pass


class ModelConfigUpdate(BaseModel):
    """更新模型配置"""
    name: Optional[str] = None
    provider: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None


class ModelConfigResponse(BaseModel):
    """模型配置响应"""
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)
    
    id: int
    user_id: int
    name: str
    provider: str
    model_type: str
    api_key: str  # 注意：实际应用中应该脱敏
    base_url: Optional[str]
    is_default: bool
    temperature: float
    top_p: float
    max_tokens: int
    created_at: datetime
    updated_at: datetime
