"""
智能体路由
"""
from fastapi import APIRouter, Depends
from backend.app.api.deps import get_db
from backend.app.core.security import get_current_active_user
from backend.app.models.user import User
from backend.app.schemas.common import ApiResponse

router = APIRouter(prefix="/agents", tags=["智能体"])

@router.get("/", response_model=ApiResponse[list])
async def list_agents(
    current_user: User = Depends(get_current_active_user)
):
    """获取可用智能体列表"""
    agents = [
        {"id": "researcher", "name": "研究员", "description": "负责资料搜集与整理"},
        {"id": "analyzer", "name": "分析师", "description": "负责逻辑推理与深度分析"},
        {"id": "responder", "name": "响应者", "description": "负责最终答案生成"}
    ]
    return ApiResponse(data=agents)
