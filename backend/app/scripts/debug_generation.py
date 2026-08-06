import json
import sys
import time

from app.core.config import settings
from app.services.generation.generator import _BACKENDS, generate_answer
from app.services.generation.prompt import SYSTEM_PROMPT, build_user_prompt
from app.services.retrieval.hybrid_search import hybrid_search


def main() -> None:
    question = sys.argv[1] if len(sys.argv) > 1 else "Comment configurer l'APN sur Android ?"
    results = hybrid_search(question, limit=3)
    user_prompt = build_user_prompt(question, results)
    call = _BACKENDS[settings.generation_backend]

    start = time.perf_counter()
    raw = call(SYSTEM_PROMPT, user_prompt)
    elapsed = time.perf_counter() - start

    print(f"Backend : {settings.generation_backend}")
    print(f"Question : {question}")
    print(f"Duree : {elapsed:.1f}s\n")

    print("--- Sortie brute du modele ---")
    print(raw)

    print("\n--- Apres validate_and_correct (ce que voit l'utilisateur final) ---")
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, AttributeError):
        parsed = {"answer": "", "sources": [], "refused": True, "refusal_reason": "erreur_format_reponse"}

    from app.services.generation.validator import validate_and_correct
    corrected = validate_and_correct(parsed, results, question)
    print(json.dumps(corrected, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
