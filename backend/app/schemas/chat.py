from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# 会话相关
class SessionCreate(BaseModel):
    title: Optional[str] = "新对话"


class SessionUpdate(BaseModel):
    title: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    
    class Config:
        from_attributes = True


# 消息相关
class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    images: Optional[List[str]] = None
    agent_name: Optional[str] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True


# SSE事件
class ChatEvent(BaseModel):
    event: str  # message, agent, done, error
    data: str
    agent_name: Optional[str] = None
