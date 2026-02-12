"""
导出路由
"""
from fastapi import APIRouter, Depends
from backend.app.api.deps import get_db
from backend.app.core.security import get_current_active_user
from backend.app.models.user import User
from backend.app.schemas.common import ApiResponse

router = APIRouter(prefix="/export", tags=["导出"])

@router.post("/pdf", response_model=ApiResponse[dict])
async def export_to_pdf(
    current_user: User = Depends(get_current_active_user)
):
    """导出为PDF"""
    return ApiResponse(data={"url": ""})
