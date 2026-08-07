"""
Rejoue le jeu de test annote (data/eval/qa_testset.json) contre le pipeline
reel (hybrid_search + generate_answer + validate_and_correct), et mesure :
exactitude sur les refus attendus, rappel de la source citee, latence.
Concu pour tourner en arriere-plan (nohup) vu la latence Mistral (30-190s/appel).
Ecrit les resultats au fur et a mesure dans un CSV, pour pouvoir consulter
la progression sans attendre la fin du run complet.
"""
import asyncio
import csv
import json
import time
from pathlib import Path

from app.services.generation.generator import generate_answer
from app.services.retrieval.hybrid_search import hybrid_search

TESTSET_PATH = Path("data/eval/qa_testset.json")
RESULTS_PATH = Path("data/eval/results.csv")

FIELDNAMES = [
    "id", "category", "question",
    "expected_refused", "actual_refused",
    "expected_source", "actual_sources", "source_found_in_topk",
    "latency_seconds", "refusal_correct",
]


async def evaluate_one(entry: dict) -> dict:
    question = entry["question"]

    start = time.perf_counter()
    chunks = hybrid_search(question, limit=3)
    result = await generate_answer(question, chunks)
    latency = time.perf_counter() - start

    actual_sources = result["sources"]
    expected_source = entry["expected_source"]

    # Rappel : la source attendue apparait-elle parmi les chunks recuperes
    # (top-k), independamment de ce que le LLM a fini par citer ?
    retrieved_titles = {c["title"] for c in chunks}
    source_found_in_topk = expected_source in retrieved_titles if expected_source else None

    refusal_correct = result["refused"] == entry["expected_refused"]

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
    testset = json.loads(TESTSET_PATH.read_text())
    print(f"{len(testset)} questions a evaluer. Resultats ecrits au fur et a mesure dans {RESULTS_PATH}")

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()

        for i, entry in enumerate(testset, start=1):
            row = await evaluate_one(entry)
            writer.writerow(row)
            f.flush()  # visible immediatement, meme en cours de run
            print(f"[{i}/{len(testset)}] {row['id']} - refused={row['actual_refused']} "
                  f"(attendu {row['expected_refused']}) - {row['latency_seconds']}s")

    print("Evaluation terminee.")


if __name__ == "__main__":
    asyncio.run(main())
