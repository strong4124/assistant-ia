import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db  # ajuste si ta dependance s'appelle differemment
from app.models import ChatSession, Feedback, Message
from app.schemas.chat import (
    FeedbackCreate,
    FeedbackOut,
    MessageCreate,
    MessageOut,
    SessionCreate,
    SessionOut,
)
from app.services.generation.generator import generate_answer
from app.services.retrieval.hybrid_search import hybrid_search

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

    # 1. Enregistre le message utilisateur
    user_message = Message(session_id=session.id, role="user", content=payload.content)
    db.add(user_message)

    # 2. Recherche hybride + generation validee (RAG complet)
    chunks = hybrid_search(payload.content, limit=3)
    result = generate_answer(payload.content, chunks)

    # 3. Enregistre la reponse assistant. refused/refusal_reason stockes dans
    # la colonne JSONB 'sources' faute de colonnes dediees pour l'instant.
    assistant_message = Message(
        session_id=session.id,
        role="assistant",
        content=result["answer"],
        sources={
            "cited": result["sources"],
            "refused": result["refused"],
            "refusal_reason": result["refusal_reason"],
        },
    )
    db.add(assistant_message)
    await db.commit()
    await db.refresh(assistant_message)

    return MessageOut(
        id=assistant_message.id,
        session_id=assistant_message.session_id,
        role=assistant_message.role,
        content=assistant_message.content,
        sources=result["sources"],
        refused=result["refused"],
        refusal_reason=result["refusal_reason"],
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
