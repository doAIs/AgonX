"""
记忆路由
"""
from fastapi import APIRouter, Depends
from app.api.deps import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/memory", tags=["记忆"])

@router.get("/long-term", response_model=ApiResponse[list])
async def list_long_term_memories(
    current_user: User = Depends(get_current_active_user)
):
    """获取长期记忆列表"""
    return ApiResponse(data=[])
