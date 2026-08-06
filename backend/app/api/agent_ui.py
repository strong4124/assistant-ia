import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import ChatSession, Message, Ticket

router = APIRouter(prefix="/agent", tags=["agent-ui"])
templates = Jinja2Templates(directory="app/templates")

VALID_STATUSES = {"open", "assigned", "in_progress", "resolved", "closed"}


@router.get("/tickets")
async def tickets_list_page(
    request: Request, status: str | None = Query(None), db: AsyncSession = Depends(get_db)
):
    query = select(Ticket).order_by(Ticket.created_at.desc())
    if status and status in VALID_STATUSES:
        query = query.where(Ticket.status == status)
    result = await db.execute(query)
    tickets = result.scalars().all()
    return templates.TemplateResponse(
        request, "tickets.html", {"tickets": tickets, "current_status": status}
    )


@router.get("/tickets/{ticket_id}")
async def ticket_detail_page(request: Request, ticket_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    ticket = await db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket introuvable")

    session = await db.get(ChatSession, ticket.session_id)
    result = await db.execute(
        select(Message).where(Message.session_id == ticket.session_id).order_by(Message.created_at)
    )
    messages = result.scalars().all()

    ticket_view = {
        "id": ticket.id,
        "status": ticket.status,
        "reason": ticket.reason,
        "summary": ticket.summary,
        "assigned_agent": ticket.assigned_agent,
        "channel": session.channel,
        "external_user_id": session.external_user_id,
        "messages": messages,
    }
    return templates.TemplateResponse(request, "ticket_detail.html", {"ticket": ticket_view})
