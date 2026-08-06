import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import ChatSession, Message, Ticket
from app.schemas.chat import TicketDetailOut, TicketOut, TicketUpdate

router = APIRouter(prefix="/api/v1/tickets", tags=["tickets"])

VALID_STATUSES = {"open", "assigned", "in_progress", "resolved", "closed"}


@router.get("", response_model=list[TicketOut])
async def list_tickets(status: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    query = select(Ticket).order_by(Ticket.created_at.desc())
    if status:
        if status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Statut invalide, attendu parmi {sorted(VALID_STATUSES)}")
        query = query.where(Ticket.status == status)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{ticket_id}", response_model=TicketDetailOut)
async def get_ticket(ticket_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    ticket = await db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket introuvable")

    session = await db.get(ChatSession, ticket.session_id)
    result = await db.execute(
        select(Message).where(Message.session_id == ticket.session_id).order_by(Message.created_at)
    )
    messages = result.scalars().all()

    return TicketDetailOut(
        id=ticket.id,
        session_id=ticket.session_id,
        status=ticket.status,
        summary=ticket.summary,
        reason=ticket.reason,
        assigned_agent=ticket.assigned_agent,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        resolved_at=ticket.resolved_at,
        channel=session.channel,
        external_user_id=session.external_user_id,
        messages=messages,
    )


@router.patch("/{ticket_id}", response_model=TicketOut)
async def update_ticket(ticket_id: uuid.UUID, payload: TicketUpdate, db: AsyncSession = Depends(get_db)):
    ticket = await db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket introuvable")

    if payload.status is not None:
        if payload.status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Statut invalide, attendu parmi {sorted(VALID_STATUSES)}")
        ticket.status = payload.status
        if payload.status == "resolved":
            ticket.resolved_at = datetime.now(timezone.utc)

    if payload.assigned_agent is not None:
        ticket.assigned_agent = payload.assigned_agent

    await db.commit()
    await db.refresh(ticket)
    return ticket
