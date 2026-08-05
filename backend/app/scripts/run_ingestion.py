from app.core.config import settings
from app.services.ingestion.loader import load_corpus
from app.services.ingestion.chunker import chunk_document
from app.services.ingestion.indexer import index_chunks, COLLECTION_NAME


def main() -> None:
    documents = load_corpus(settings.corpus_dir)
    if not documents:
        print(f"Aucun document trouve dans {settings.corpus_dir}")
        return

    all_chunks = []
    for doc in documents:
        all_chunks.extend(chunk_document(doc))

    print(f"{len(documents)} documents charges, {len(all_chunks)} chunks a indexer...")
    count = index_chunks(all_chunks)
    print(f"{count} points indexes dans Qdrant (collection '{COLLECTION_NAME}').")


if __name__ == "__main__":
    main()
