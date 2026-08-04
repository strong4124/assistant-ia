from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
import asyncpg
from qdrant_client import QdrantClient

from app.core.config import settings

app = FastAPI(title="Assistant IA Service Client - API")


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
