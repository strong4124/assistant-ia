import sys

from app.services.retrieval.vector_search import vector_search
from app.services.retrieval.lexical_search import lexical_search
from app.services.retrieval.hybrid_search import hybrid_search


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else "Comment configurer l'APN sur Android ?"
    print(f"Requete : {query}\n")

    print("--- Vectoriel ---")
    for r in vector_search(query, limit=3):
        print(f"score={r['score']:.3f} | {r['title']} (chunk {r['chunk_index']})")

    print("\n--- Lexical ---")
    for r in lexical_search(query, limit=3):
        print(f"rank={r['rank']:.4f} | {r['title']} (chunk {r['chunk_index']})")

    print("\n--- Hybride (RRF) ---")
    for r in hybrid_search(query, limit=3):
        print(f"rrf={r['rrf_score']:.4f} | {r['title']} (chunk {r['chunk_index']})")


if __name__ == "__main__":
    main()
