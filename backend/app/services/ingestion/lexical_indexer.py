from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import settings
from app.models import ChunkRecord
from app.services.ingestion.chunker import DocumentChunk

SYNC_DATABASE_URL = (
    f"postgresql+psycopg2://{quote_plus(settings.postgres_user)}:{quote_plus(settings.postgres_password)}"
    f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
)

# Moteur synchrone dedie aux scripts d'ingestion (par opposition au moteur
# async de app/db.py utilise au runtime par l'API). Un script batch n'a pas
# besoin d'async ; ca evite de melanger deux styles de session inutilement.
_engine = create_engine(SYNC_DATABASE_URL, future=True)


def index_chunks_lexical(chunks: list[DocumentChunk]) -> int:
    """Upsert des chunks dans PostgreSQL pour la recherche lexicale.
    Idempotent : chunk_id est la cle primaire, un re-import met a jour la ligne existante
    plutot que d'en creer une nouvelle. search_vector n'est jamais ecrit directement,
    Postgres le recalcule automatiquement a partir de "content"."""
    if not chunks:
        return 0

    with _engine.begin() as conn:
        for chunk in chunks:
            stmt = pg_insert(ChunkRecord).values(
                chunk_id=chunk.chunk_id,
                doc_id=chunk.doc_id,
                category=chunk.category,
                title=chunk.title,
                source_file=chunk.source_file,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["chunk_id"],
                set_={
                    "doc_id": stmt.excluded.doc_id,
                    "category": stmt.excluded.category,
                    "title": stmt.excluded.title,
                    "source_file": stmt.excluded.source_file,
                    "chunk_index": stmt.excluded.chunk_index,
                    "content": stmt.excluded.content,
                },
            )
            conn.execute(stmt)

    return len(chunks)
