from pydantic import BaseModel
from typing import TypeVar, Generic, List, Optional, Any

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """通用API响应"""
    code: int = 200
    message: str = "success"
    data: Optional[T] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    items: List[T]
    total: int
    page: int
    page_size: int


class ErrorResponse(BaseModel):
    """错误响应"""
    code: int
    message: str
    detail: Optional[Any] = None
