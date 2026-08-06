from app.services.guardrails.scope_filter import is_out_of_scope

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatSession, Message, Ticket
from app.services.generation.generator import generate_answer
from app.services.retrieval.hybrid_search import hybrid_search


async def process_user_message(db: AsyncSession, session: ChatSession, content: str) -> dict:
    """
    Point d'entree UNIQUE du pipeline conversationnel (recherche + generation
    + escalade). Utilise par tous les canaux (API web, Telegram, futurs
    canaux) pour garantir un comportement identique partout - en particulier
    l'escalade automatique, qui doit s'appliquer sur tous les canaux et pas
    seulement celui ou elle a ete ecrite en premier.
    """
    db.add(Message(session_id=session.id, role="user", content=content))

    if is_out_of_scope(content):
        result = {
            "answer": "",
            "sources": [],
            "refused": True,
            "refusal_reason": "hors_perimetre_filtre",
        }
    else:
        chunks = hybrid_search(content, limit=3)
        result = await generate_answer(content, chunks)

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

    ticket_id = None
    if result["refused"] and result["refusal_reason"] != "hors_perimetre_filtre":
        summary = (
            f"Question non resolue par l'assistant (motif : {result['refusal_reason']}).\n"
            f"Derniere question du client : {content}"
        )
        ticket = Ticket(
            session_id=session.id,
            status="open",
            summary=summary,
            reason=result["refusal_reason"],
        )
        db.add(ticket)
        await db.flush()  # necessaire pour obtenir ticket.id avant le commit
        ticket_id = ticket.id

    await db.commit()
    await db.refresh(assistant_message)

    return {
        "message": assistant_message,
        "answer": result["answer"],
        "sources": result["sources"],
        "refused": result["refused"],
        "refusal_reason": result["refusal_reason"],
        "ticket_id": ticket_id,
    }
