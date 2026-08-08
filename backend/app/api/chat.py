from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import ChatSession, Feedback, Message
from app.schemas.chat import (
    FeedbackCreate,
    FeedbackOut,
    MessageCreate,
    MessageOut,
    SessionCreate,
    SessionOut,
)
from app.services.conversation import process_user_message

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/sessions", response_model=SessionOut, status_code=201)
async def create_session(payload: SessionCreate, db: AsyncSession = Depends(get_db)):
    session = ChatSession(
        channel=payload.channel,
        external_user_id=payload.external_user_id,
        language=payload.language,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.post("/messages", response_model=MessageOut, status_code=201)
async def post_message(payload: MessageCreate, db: AsyncSession = Depends(get_db)):
    session = await db.get(ChatSession, payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session introuvable")

    result = await process_user_message(db, session, payload.content)
    assistant_message = result["message"]

    return MessageOut(
        id=assistant_message.id,
        session_id=assistant_message.session_id,
        role=assistant_message.role,
        content=assistant_message.content,
        sources=result["sources"],
        refused=result["refused"],
        refusal_reason=result["refusal_reason"],
        ticket_id=result["ticket_id"],
        created_at=assistant_message.created_at,
    )


@router.post("/feedback", response_model=FeedbackOut, status_code=201)
async def post_feedback(payload: FeedbackCreate, db: AsyncSession = Depends(get_db)):
    message = await db.get(Message, payload.message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Message introuvable")

    feedback = Feedback(message_id=payload.message_id, is_positive=payload.is_positive)
    db.add(feedback)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Feedback deja enregistre pour ce message")
    await db.refresh(feedback)
    return feedback
