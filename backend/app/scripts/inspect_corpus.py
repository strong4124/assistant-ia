from collections import defaultdict

from app.core.config import settings
from app.services.ingestion.loader import load_corpus
from app.services.ingestion.chunker import chunk_document


def main() -> None:
    documents = load_corpus(settings.corpus_dir)
    if not documents:
        print(f"Aucun document trouve dans {settings.corpus_dir}")
        return

    stats = defaultdict(lambda: {"docs": 0, "chunks": 0, "chars": 0})

    print(f"{'Document':<45} {'Categorie':<22} {'Chunks':>7} {'Caracteres':>11}")
    print("-" * 90)

    for doc in documents:
        chunks = chunk_document(doc)
        stats[doc.category]["docs"] += 1
        stats[doc.category]["chunks"] += len(chunks)
        stats[doc.category]["chars"] += len(doc.content)
        print(f"{doc.doc_id:<45} {doc.category:<22} {len(chunks):>7} {len(doc.content):>11}")

    print("-" * 90)
    total_chunks = sum(s["chunks"] for s in stats.values())
    print(f"Total : {len(documents)} documents, {total_chunks} chunks")


if __name__ == "__main__":
    main()
