"""
Chat API endpoints — Q&A with streaming SSE responses.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import get_current_user_id
from app.models.chat import ChatMessage, ChatSession
from app.models.document import Document
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionListResponse,
    ChatSessionResponse,
)
from app.services.llm_service import chat_with_document, chat_with_document_stream

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    data: ChatSessionCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new chat session for a document."""
    # Verify document exists and belongs to user
    doc = await db.get(Document, data.document_id)
    if doc is None or str(doc.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.status != "ready":
        raise HTTPException(status_code=400, detail="Document is still processing")

    session = ChatSession(
        user_id=uuid.UUID(user_id),
        document_id=data.document_id,
        title=data.title or f"Chat about {doc.filename}",
    )
    db.add(session)
    await db.flush()

    return ChatSessionResponse(
        id=session.id,
        document_id=session.document_id,
        title=session.title,
        created_at=session.created_at,
        message_count=0,
    )


@router.get("/sessions", response_model=ChatSessionListResponse)
async def list_chat_sessions(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all chat sessions for the current user."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == uuid.UUID(user_id))
        .order_by(ChatSession.created_at.desc())
    )
    sessions = result.scalars().all()

    session_responses = []
    for session in sessions:
        # Count messages
        count_result = await db.execute(
            select(func.count()).where(ChatMessage.session_id == session.id)
        )
        message_count = count_result.scalar() or 0

        session_responses.append(
            ChatSessionResponse(
                id=session.id,
                document_id=session.document_id,
                title=session.title,
                created_at=session.created_at,
                message_count=message_count,
            )
        )

    return ChatSessionListResponse(sessions=session_responses, total=len(session_responses))


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    data: ChatMessageRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Send a message and get a streaming AI response via SSE.

    Returns a Server-Sent Events stream with:
    - `token` events: Individual response tokens
    - `metadata` events: Timestamps and source references
    - `done` event: Final complete response
    """
    # Verify session
    session = await db.get(ChatSession, uuid.UUID(session_id))
    if session is None or str(session.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # Get chat history
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
    )
    history_msgs = result.scalars().all()
    chat_history = [{"role": msg.role, "content": msg.content} for msg in history_msgs]

    # Save user message
    user_message = ChatMessage(
        session_id=session.id,
        role="user",
        content=data.content,
    )
    db.add(user_message)
    await db.flush()

    document_id = str(session.document_id)

    async def event_stream():
        """Generate SSE stream and save assistant message."""
        full_content = ""
        timestamps = None
        sources = None

        async for event in chat_with_document_stream(
            document_id=document_id,
            question=data.content,
            chat_history=chat_history,
        ):
            yield event

            # Parse the done event to get the full content
            if "event: done" in event:
                import json
                data_line = event.split("data: ", 1)[1].strip()
                done_data = json.loads(data_line)
                full_content = done_data.get("content", "")

            if "event: metadata" in event:
                import json
                data_line = event.split("data: ", 1)[1].strip()
                meta_data = json.loads(data_line)
                timestamps = meta_data.get("timestamps")
                sources = meta_data.get("sources")

        # Save assistant message after streaming completes
        async with db.begin():
            assistant_message = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=full_content,
                timestamps=timestamps,
                sources=sources,
            )
            db.add(assistant_message)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
async def get_chat_history(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get all messages in a chat session."""
    session = await db.get(ChatSession, uuid.UUID(session_id))
    if session is None or str(session.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Chat session not found")

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()

    return [ChatMessageResponse.model_validate(msg) for msg in messages]
