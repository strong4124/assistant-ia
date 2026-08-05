from sqlalchemy import String, Text, Integer, Index, Computed
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


# Nommee ChunkRecord (et non DocumentChunk) pour ne pas entrer en conflit
# avec le dataclass DocumentChunk du module de chunking (app.services.ingestion.chunker).
class ChunkRecord(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        Index("ix_document_chunks_search_vector", "search_vector", postgresql_using="gin"),
    )

    chunk_id: Mapped[str] = mapped_column(String(512), primary_key=True)
    doc_id: Mapped[str] = mapped_column(String(512), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_file: Mapped[str] = mapped_column(String(512), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Colonne generee automatiquement par PostgreSQL a partir de "content" :
    # jamais ecrite directement, recalculee par la base a chaque insert/update.
    search_vector: Mapped[str] = mapped_column(
        TSVECTOR, Computed("to_tsvector('french', content)", persisted=True)
    )
