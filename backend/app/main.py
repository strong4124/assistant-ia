from prometheus_fastapi_instrumentator import Instrumentator
import logging
from app.core.logging_filters import PIIRedactionFilter
logging.basicConfig(level=logging.INFO)
logging.getLogger().addFilter(PIIRedactionFilter())


import asyncio
from app.channels.telegram_bot import run_polling

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
import asyncpg
from qdrant_client import QdrantClient

from app.core.config import settings

app = FastAPI(title="Assistant IA Service Client - API")

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://192.168.118.133:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(run_polling())

from app.api import chat, tickets, agent_ui
app.include_router(chat.router)
app.include_router(tickets.router)
app.include_router(agent_ui.router)


@app.get("/health")
async def health():
    """Liveness : le process tourne, rien d'autre n'est verifie."""
    return {"status": "ok"}


@app.get("/health/ready")
async def health_ready():
    """Readiness : verifie que Postgres et Qdrant repondent reellement."""
    checks = {}

    try:
        conn = await asyncpg.connect(
            user=settings.postgres_user,
            password=settings.postgres_password,
            database=settings.postgres_db,
            host=settings.postgres_host,
            port=settings.postgres_port,
            timeout=3,
        )
        await conn.execute("SELECT 1")
        await conn.close()
        checks["postgres"] = "ok"
    except Exception as e:
        checks["postgres"] = f"error: {e}"

    try:
        client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port, timeout=3)
        client.get_collections()
        checks["qdrant"] = "ok"
    except Exception as e:
        checks["qdrant"] = f"error: {e}"

    all_ok = all(v == "ok" for v in checks.values())
    code = status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=code, content={"status": "ok" if all_ok else "degraded", "checks": checks})
