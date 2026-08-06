import asyncio
from app.services.generation.validator import validate_and_correct

import json

import httpx

from app.core.config import settings
from app.services.generation.prompt import SYSTEM_PROMPT, build_user_prompt


def _call_ollama(system_prompt: str, user_prompt: str) -> str:
    url = f"http://{settings.ollama_host}:{settings.ollama_port}/api/chat"
    payload = {
        "model": settings.ollama_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "format": "json",
        "stream": False,
        "keep_alive": "10m",  # evite de recharger le modele en memoire a chaque appel
        "options": {
            "temperature": 0.1,
            "num_predict": 500,  # borne dure : empeche une generation qui ne terminerait jamais
        },
    }
    response = httpx.post(url, json=payload, timeout=240.0)
    response.raise_for_status()
    return response.json()["message"]["content"]


def _call_anthropic(system_prompt: str, user_prompt: str) -> str:
    from anthropic import Anthropic

    client = Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.generation_model,
        max_tokens=1000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text if response.content else ""


_BACKENDS = {
    "ollama": _call_ollama,
    "anthropic": _call_anthropic,
}


#def generate_answer(question: str, chunks: list[dict]) -> dict:
async def generate_answer(question: str, chunks: list[dict]) -> dict:
    user_prompt = build_user_prompt(question, chunks)
    call = _BACKENDS[settings.generation_backend]
    import asyncio
    raw_text = await asyncio.to_thread(call, SYSTEM_PROMPT, user_prompt)

    try:
        parsed = json.loads(raw_text)
    except (json.JSONDecodeError, AttributeError):
        parsed = {"answer": "", "sources": [], "refused": True, "refusal_reason": "erreur_format_reponse"}

    return validate_and_correct(parsed, chunks, question)
