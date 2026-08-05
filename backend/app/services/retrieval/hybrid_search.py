from app.services.retrieval.vector_search import vector_search
from app.services.retrieval.lexical_search import lexical_search

RRF_K = 60  # constante standard de la Reciprocal Rank Fusion (litterature IR)


def hybrid_search(query: str, limit: int = 5, candidate_pool: int = 10) -> list[dict]:
    """
    Fusionne recherche vectorielle et recherche lexicale par Reciprocal Rank Fusion.
    score_RRF(chunk) = somme, sur chaque liste ou il apparait, de 1 / (RRF_K + rang)
    Un chunk bien classe dans les deux listes remonte naturellement en tete,
    sans avoir a ponderer/normaliser des scores de nature differente.
    """
    vector_results = vector_search(query, limit=candidate_pool)
    lexical_results = lexical_search(query, limit=candidate_pool)

    fused: dict[str, dict] = {}

    for rank, item in enumerate(vector_results, start=1):
        chunk_id = item["chunk_id"]
        fused.setdefault(chunk_id, {"chunk": item, "rrf_score": 0.0})
        fused[chunk_id]["rrf_score"] += 1 / (RRF_K + rank)

    for rank, item in enumerate(lexical_results, start=1):
        chunk_id = item["chunk_id"]
        fused.setdefault(chunk_id, {"chunk": item, "rrf_score": 0.0})
        fused[chunk_id]["rrf_score"] += 1 / (RRF_K + rank)

    ranked = sorted(fused.values(), key=lambda x: x["rrf_score"], reverse=True)
    return [{**entry["chunk"], "rrf_score": entry["rrf_score"]} for entry in ranked[:limit]]
