from fastapi import APIRouter

from app.api.v1 import auth, chat, knowledge, agents, memory, settings, export

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(chat.router)
api_router.include_router(knowledge.router)
api_router.include_router(agents.router)
api_router.include_router(memory.router)
api_router.include_router(settings.router)
api_router.include_router(export.router)
