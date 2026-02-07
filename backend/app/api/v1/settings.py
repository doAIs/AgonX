"""
配置路由
"""
from fastapi import APIRouter, Depends
from app.api.deps import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/settings", tags=["配置"])

@router.get("/models", response_model=ApiResponse[list])
async def get_model_configs(
    current_user: User = Depends(get_current_active_user)
):
    """获取模型配置"""
    return ApiResponse(data=[])
