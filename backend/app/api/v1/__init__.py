from fastapi import APIRouter

from app.api.v1 import auth, chat

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(chat.router)

# 后续添加更多路由
# api_router.include_router(knowledge.router)
# api_router.include_router(agents.router)
# api_router.include_router(memory.router)
# api_router.include_router(settings.router)
# api_router.include_router(export.router)
