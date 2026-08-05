from app.services.ingestion.embedder import embed_texts
from app.services.ingestion.indexer import get_qdrant_client, COLLECTION_NAME


def vector_search(query: str, limit: int = 5) -> list[dict]:
    vector = embed_texts([query])[0]
    client = get_qdrant_client()
    results = client.query_points(collection_name=COLLECTION_NAME, query=vector, limit=limit).points
    return [
        {
            "chunk_id": r.payload["chunk_id"],
            "doc_id": r.payload["doc_id"],
            "category": r.payload["category"],
            "title": r.payload["title"],
            "source_file": r.payload["source_file"],
            "chunk_index": r.payload["chunk_index"],
            "content": r.payload["content"],
            "score": r.score,
        }
        for r in results
    ]
