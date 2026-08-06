from app.core.config import settings
from app.services.retrieval.hybrid_search import hybrid_search
from app.services.generation.generator import generate_answer


def answer_question(question: str) -> dict:
    results = hybrid_search(question, limit=3)

    if not results or results[0]["rrf_score"] < settings.min_rrf_score:
        return {"answer": "", "sources": [], "refused": True, "refusal_reason": "hors_base"}

    return generate_answer(question, results)
