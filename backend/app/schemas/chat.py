import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    channel: str = Field(..., examples=["web", "telegram"])
    external_user_id: str
    language: str = "fr"


class SessionOut(BaseModel):
    id: uuid.UUID
    channel: str
    external_user_id: str
    language: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    session_id: uuid.UUID
    content: str


class MessageOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    sources: list[str]
    refused: bool
    refusal_reason: str | None
    ticket_id: uuid.UUID | None = None
    created_at: datetime


class FeedbackCreate(BaseModel):
    message_id: uuid.UUID
    is_positive: bool


class FeedbackOut(BaseModel):
    id: uuid.UUID
    message_id: uuid.UUID
    is_positive: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TicketOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    status: str
    summary: str
    reason: str | None
    assigned_agent: str | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None

    class Config:
        from_attributes = True


class TicketUpdate(BaseModel):
    status: str | None = None
    assigned_agent: str | None = None


class ConversationMessageOut(BaseModel):
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class TicketDetailOut(TicketOut):
    channel: str
    external_user_id: str
    messages: list[ConversationMessageOut]
