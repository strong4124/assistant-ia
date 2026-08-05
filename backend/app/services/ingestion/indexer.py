import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from app.core.config import settings
from app.services.ingestion.chunker import DocumentChunk
from app.services.ingestion.embedder import EMBEDDING_DIM, embed_texts

COLLECTION_NAME = "corpus_teranga"


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def ensure_collection(client: QdrantClient) -> None:
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )


def index_chunks(chunks: list[DocumentChunk]) -> int:
    if not chunks:
        return 0

    client = get_qdrant_client()
    ensure_collection(client)

    vectors = embed_texts([c.content for c in chunks])

    points = [
        PointStruct(
            # id deterministe derive du chunk_id : re-indexer le meme chunk
            # ecrase le point existant au lieu d'en creer un doublon (idempotence).
            id=str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.chunk_id)),
            vector=vector,
            payload={
                "chunk_id": chunk.chunk_id,
                "doc_id": chunk.doc_id,
                "category": chunk.category,
                "title": chunk.title,
                "source_file": chunk.source_file,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
            },
        )
        for chunk, vector in zip(chunks, vectors)
    ]

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)
