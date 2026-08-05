from app.core.config import settings
from app.services.ingestion.loader import load_corpus
from app.services.ingestion.chunker import chunk_document
from app.services.ingestion.indexer import index_chunks, COLLECTION_NAME
from app.services.ingestion.lexical_indexer import index_chunks_lexical


def main() -> None:
    documents = load_corpus(settings.corpus_dir)
    if not documents:
        print(f"Aucun document trouve dans {settings.corpus_dir}")
        return

    all_chunks = []
    for doc in documents:
        all_chunks.extend(chunk_document(doc))

    print(f"{len(documents)} documents charges, {len(all_chunks)} chunks a indexer...")

    vector_count = index_chunks(all_chunks)
    print(f"{vector_count} points indexes dans Qdrant (collection '{COLLECTION_NAME}').")

    lexical_count = index_chunks_lexical(all_chunks)
    print(f"{lexical_count} chunks indexes dans PostgreSQL (recherche lexicale).")


if __name__ == "__main__":
    main()
