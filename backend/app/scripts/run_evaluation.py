"""
Rejoue le jeu de test annote (data/eval/qa_testset.json) contre le pipeline
reel, et mesure : exactitude sur les refus attendus, rappel de la source
citee, latence. Verrou anti-double-lancement (evite la corruption par
ecriture concurrente) et reprise automatique sur un CSV deja partiellement
rempli (evite de reperdre des heures de calcul si le run est interrompu).
"""
import asyncio
import csv
import json
import time
from pathlib import Path

#from app.services.generation.generator import generate_answer
#from app.services.retrieval.hybrid_search import hybrid_search

from app.services.guardrails.scope_filter import is_out_of_scope

TESTSET_PATH = Path("data/eval/qa_testset.json")
RESULTS_PATH = Path("data/eval/results.csv")
LOCK_PATH = Path("data/eval/.run_evaluation.lock")

FIELDNAMES = [
    "id", "category", "question",
    "expected_refused", "actual_refused",
    "expected_source", "actual_sources", "source_found_in_topk",
    "latency_seconds", "refusal_correct",
]


def _load_completed_ids() -> set[str]:
    if not RESULTS_PATH.exists():
        return set()
    try:
        with open(RESULTS_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return {row["id"] for row in reader if row.get("id")}
    except Exception:
        return set()

async def evaluate_one(entry: dict) -> dict:
    question = entry["question"]

    start = time.perf_counter()
    if is_out_of_scope(question):
        result = {"answer": "", "sources": [], "refused": True, "refusal_reason": "hors_perimetre_filtre"}
        chunks = []
    else:
        chunks = hybrid_search(question, limit=3)
        result = await generate_answer(question, chunks)
    latency = time.perf_counter() - start


    return {
        "id": entry["id"],
        "category": entry["category"],
        "question": question,
        "expected_refused": entry["expected_refused"],
        "actual_refused": result["refused"],
        "expected_source": expected_source or "",
        "actual_sources": "; ".join(actual_sources),
        "source_found_in_topk": source_found_in_topk if source_found_in_topk is not None else "",
        "latency_seconds": round(latency, 1),
        "refusal_correct": refusal_correct,
    }


async def main():
    if LOCK_PATH.exists():
        print(f"Verrou present ({LOCK_PATH}) : une evaluation semble deja en cours.")
        return

    LOCK_PATH.touch()
    try:
        testset = json.loads(TESTSET_PATH.read_text())
        completed_ids = _load_completed_ids()
        remaining = [e for e in testset if e["id"] not in completed_ids]

        print(f"{len(testset)} questions au total, {len(completed_ids)} deja traitees, "
              f"{len(remaining)} restantes.")

        RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        file_is_new = not completed_ids
        mode = "w" if file_is_new else "a"

        with open(RESULTS_PATH, mode, newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if file_is_new:
                writer.writeheader()
                f.flush()

            for i, entry in enumerate(remaining, start=1):
                row = await evaluate_one(entry)
                writer.writerow(row)
                f.flush()
                print(f"[{i}/{len(remaining)}] {row['id']} - refused={row['actual_refused']} "
                      f"(attendu {row['expected_refused']}) - {row['latency_seconds']}s")

        print("Evaluation terminee.")
    finally:
        LOCK_PATH.unlink(missing_ok=True)


if __name__ == "__main__":
    asyncio.run(main())
