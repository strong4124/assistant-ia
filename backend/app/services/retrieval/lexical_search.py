from sqlalchemy import text

from app.services.ingestion.lexical_indexer import _engine

LEXEMES_SQL = text("""
    SELECT tsvector_to_array(to_tsvector('french', :query)) AS lexemes
""")

LEXICAL_SEARCH_SQL = text("""
    SELECT chunk_id, doc_id, category, title, source_file, chunk_index, content,
           ts_rank(search_vector, to_tsquery('french', :or_query)) AS rank
    FROM document_chunks
    WHERE search_vector @@ to_tsquery('french', :or_query)
    ORDER BY rank DESC
    LIMIT :limit
""")


def lexical_search(query: str, limit: int = 5) -> list[dict]:
    with _engine.connect() as conn:
        lexemes = conn.execute(LEXEMES_SQL, {"query": query}).scalar_one()
        if not lexemes:
            return []

        or_query = " | ".join(lexemes)
        rows = conn.execute(
            LEXICAL_SEARCH_SQL, {"or_query": or_query, "limit": limit}
        ).mappings().all()

    return [dict(row) for row in rows]
