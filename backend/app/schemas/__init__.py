# 导出所有schemas
from app.schemas.user import (
    UserBase, UserCreate, UserLogin, UserResponse, Token, TokenData
)
from app.schemas.chat import (
    SessionCreate, SessionUpdate, SessionResponse,
    MessageCreate, MessageResponse, ChatEvent
)
from app.schemas.knowledge import (
    KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse,
    RetrievalConfigUpdate, RetrievalConfigResponse,
    DocumentResponse, SearchRequest, SearchResult
)
from app.schemas.common import ApiResponse, PaginatedResponse, ErrorResponse

__all__ = [
    # User
    "UserBase", "UserCreate", "UserLogin", "UserResponse", "Token", "TokenData",
    # Chat
    "SessionCreate", "SessionUpdate", "SessionResponse",
    "MessageCreate", "MessageResponse", "ChatEvent",
    # Knowledge
    "KnowledgeBaseCreate", "KnowledgeBaseUpdate", "KnowledgeBaseResponse",
    "RetrievalConfigUpdate", "RetrievalConfigResponse",
    "DocumentResponse", "SearchRequest", "SearchResult",
    # Common
    "ApiResponse", "PaginatedResponse", "ErrorResponse"
]
