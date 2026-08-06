import sys

from app.services.generation.rag_pipeline import answer_question


def main() -> None:
    question = sys.argv[1] if len(sys.argv) > 1 else "Comment configurer l'APN sur Android ?"
    result = answer_question(question)

    print(f"Question : {question}\n")
    if result["refused"]:
        print(f"REFUS ({result['refusal_reason']})")
    else:
        print(f"Reponse : {result['answer']}")
        print(f"Sources : {', '.join(result['sources'])}")


if __name__ == "__main__":
    main()
