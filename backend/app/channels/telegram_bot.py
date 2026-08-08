import asyncio
import logging

import httpx
from sqlalchemy import select

from app.core.config import settings
from app.db import get_db
from app.models import ChatSession
from app.services.conversation import process_user_message

logger = logging.getLogger("p7-assistant.telegram")

TELEGRAM_API = f"https://api.telegram.org/bot{settings.telegram_bot_token}"


async def _get_db_session():
    gen = get_db()
    db = await gen.__anext__()
    return db, gen


async def _get_or_create_session(db, chat_id: int) -> ChatSession:
    external_user_id = f"telegram:{chat_id}"
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.channel == "telegram",
            ChatSession.external_user_id == external_user_id,
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        session = ChatSession(channel="telegram", external_user_id=external_user_id)
        db.add(session)
        await db.flush()
    return session


async def _handle_message(chat_id: int, text: str) -> None:
    db, gen = await _get_db_session()
    try:
        chat_session = await _get_or_create_session(db, chat_id)
        result = await process_user_message(db, chat_session, text)
    finally:
        await gen.aclose()

    if result["refused"]:
        short_id = str(result["ticket_id"])[:8] if result["ticket_id"] else "?"
        reply_text = (
            "Je n'ai pas trouve cette information dans ma base de connaissances. "
            f"Un ticket (#{short_id}) a ete cree, un agent va vous repondre."
        )
    else:
        reply_text = result["answer"]

    async with httpx.AsyncClient(timeout=30.0) as client:
        await client.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": reply_text},
        )


async def run_polling() -> None:
    if not settings.telegram_bot_token:
        logger.info("TELEGRAM_BOT_TOKEN absent, canal Telegram desactive")
        return

    logger.info("Demarrage du polling Telegram")
    offset = 0
    async with httpx.AsyncClient(timeout=40.0) as client:
        while True:
            try:
                resp = await client.get(
                    f"{TELEGRAM_API}/getUpdates",
                    params={"offset": offset, "timeout": 30},
                )
                resp.raise_for_status()
                updates = resp.json().get("result", [])
                for update in updates:
                    offset = update["update_id"] + 1
                    message = update.get("message")
                    if message and "text" in message:
                        chat_id = message["chat"]["id"]
                        text = message["text"]
                        logger.info("Message Telegram recu (chat_id=%s)", chat_id)
                        asyncio.create_task(_handle_message(chat_id, text))
            except Exception:
                logger.exception("Erreur dans la boucle de polling Telegram")
                await asyncio.sleep(5)
