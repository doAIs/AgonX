import uuid
import json
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.api.deps import get_db
from backend.app.core.security import get_current_active_user
from backend.app.models import User, ChatSession, ChatMessage
from backend.app.schemas import (
    SessionCreate, SessionUpdate, SessionResponse,
    MessageCreate, MessageResponse, ApiResponse, PaginatedResponse
)

router = APIRouter(prefix="/chat", tags=["对话"])


@router.get("/sessions", response_model=ApiResponse[PaginatedResponse[SessionResponse]])
async def get_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取会话列表"""
    # 查询总数
    count_query = select(func.count()).select_from(ChatSession).where(
        ChatSession.user_id == current_user.id
    )
    total = (await db.execute(count_query)).scalar() or 0
    
    # 查询会话
    query = (
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    # 获取每个会话的消息数量
    items = []
    for session in sessions:
        msg_count_query = select(func.count()).select_from(ChatMessage).where(
            ChatMessage.session_id == session.id
        )
        msg_count = (await db.execute(msg_count_query)).scalar() or 0
        items.append(SessionResponse(
            id=session.id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=msg_count
        ))
    
    return ApiResponse(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )
    )


@router.post("/sessions", response_model=ApiResponse[SessionResponse])
async def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建新会话"""
    session = ChatSession(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        title=session_data.title or "新对话"
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return ApiResponse(
        data=SessionResponse(
            id=session.id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=0
        )
    )


@router.get("/sessions/{session_id}/messages", response_model=ApiResponse[list[MessageResponse]])
async def get_session_messages(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取会话消息"""
    # 验证会话所有权
    session_query = select(ChatSession).where(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    )
    session = (await db.execute(session_query)).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 获取消息
    msg_query = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    result = await db.execute(msg_query)
    messages = result.scalars().all()
    
    return ApiResponse(
        data=[
            MessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                images=msg.images,
                agent_name=msg.agent_name,
                timestamp=msg.created_at
            )
            for msg in messages
        ]
    )


@router.delete("/sessions/{session_id}", response_model=ApiResponse)
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除会话"""
    session_query = select(ChatSession).where(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    )
    session = (await db.execute(session_query)).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    await db.delete(session)
    await db.commit()
    
    return ApiResponse(message="删除成功")


@router.put("/sessions/{session_id}", response_model=ApiResponse[SessionResponse])
async def update_session(
    session_id: str,
    session_data: SessionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新会话"""
    session_query = select(ChatSession).where(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    )
    session = (await db.execute(session_query)).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    if session_data.title:
        session.title = session_data.title
    
    await db.commit()
    await db.refresh(session)
    
    return ApiResponse(
        data=SessionResponse(
            id=session.id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=0
        )
    )


async def generate_stream_response(
    session_id: str,
    content: str,
    user_id: int,
    db: AsyncSession
) -> AsyncGenerator[str, None]:
    """生成流式响应"""
    # 保存用户消息
    user_msg = ChatMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="user",
        content=content
    )
    db.add(user_msg)
    await db.commit()
    
    # 发送开始事件
    yield f"data: {json.dumps({'event': 'start', 'data': ''})}\n\n"
    
    # 模拟多智能体响应 (实际使用时会调用LangGraph)
    response_parts = [
        ("researcher", "正在检索相关信息..."),
        ("analyzer", "分析检索结果..."),
        ("responder", f"根据您的问题「{content}」，我来为您解答：\n\n这是一个演示响应，实际使用时会调用后端的多智能体系统。")
    ]
    
    full_response = ""
    for agent_name, text in response_parts:
        yield f"data: {json.dumps({'event': 'agent', 'data': agent_name})}\n\n"
        
        for char in text:
            full_response += char
            yield f"data: {json.dumps({'event': 'message', 'data': char})}\n\n"
    
    # 保存AI消息
    ai_msg = ChatMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="assistant",
        content=full_response,
        agent_name="AgonX"
    )
    db.add(ai_msg)
    await db.commit()
    
    # 发送完成事件
    yield f"data: {json.dumps({'event': 'done', 'data': ''})}\n\n"


@router.post("/message")
async def send_message(
    session_id: str = Query(...),
    content: str = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """发送消息 (SSE流式响应)"""
    # 验证会话
    session_query = select(ChatSession).where(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    )
    session = (await db.execute(session_query)).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return StreamingResponse(
        generate_stream_response(session_id, content, current_user.id, db),
        media_type="text/event-stream"
    )
