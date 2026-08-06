import re

# Vocabulaire déclenchant un refus systématique côté serveur, indépendamment
# de ce que dit le modèle — garde-fou anti-engagement commercial/contractuel.
_COMMERCIAL_ENGAGEMENT_PATTERNS = [
    r"rembours\w*",
    r"geste\s+commercial\w*",
    r"compensat\w*",
    r"d[ée]dommag\w*",
    r"r[ée]silia\w*\s+gratuit\w*",
    r"annuler?\s+les?\s+frais",
    r"offert\w*\s+gratuitement",
    r"exon[ée]r\w*",
    r"avoir\s+un\s+geste",
]
_COMMERCIAL_ENGAGEMENT_RE = re.compile(
    "|".join(_COMMERCIAL_ENGAGEMENT_PATTERNS), re.IGNORECASE
)

# Préfixes bruts que le modèle recopie parfois depuis le contexte au lieu
# d'extraire le titre propre (ex: "Extrait 1 - Source : Configuration de l'APN").
_RAW_LABEL_PREFIX_RE = re.compile(
    r"^\s*Extrait\s+\d+\s*-?\s*Source\s*:\s*", re.IGNORECASE
)


def _clean_source(raw_source: str, valid_titles: set[str]) -> str | None:
    """Ne retourne un titre que s'il correspond réellement à un chunk fourni."""
    candidate = _RAW_LABEL_PREFIX_RE.sub("", raw_source).strip()

    if candidate in valid_titles:
        return candidate

    # Tolérance : le modèle a pu tronquer ou légèrement reformuler le titre.
    for title in valid_titles:
        if candidate and (candidate in title or title in candidate):
            return title

    return None


def validate_and_correct(parsed: dict, chunks: list[dict], question: str) -> dict:
    """Recroise la réponse du modèle avec les données réelles côté serveur.
    Ne fait jamais confiance à `refused`/`sources` tels quels."""
    valid_titles = {chunk["title"] for chunk in chunks}

    # 1. Garde-fou commercial : priorité absolue, indépendant du modèle.
    text_to_check = f"{question} {parsed.get('answer', '')}"
    if _COMMERCIAL_ENGAGEMENT_RE.search(text_to_check):
        return {
            "answer": "",
            "sources": [],
            "refused": True,
            "refusal_reason": "hors_perimetre",
        }

    # 2. Si le modèle a déjà refusé, on normalise sans plus chercher.
    if parsed.get("refused"):
        reason = parsed.get("refusal_reason") or "hors_base"
        return {"answer": "", "sources": [], "refused": True, "refusal_reason": reason}

    # 3. Nettoyage des sources annoncées comme valides.
    cleaned_sources = []
    for raw in parsed.get("sources", []):
        cleaned = _clean_source(str(raw), valid_titles)
        if cleaned and cleaned not in cleaned_sources:
            cleaned_sources.append(cleaned)

    # 4. Aucune source réelle retrouvée -> on force le refus, quoi qu'ait dit le modèle.
    if not cleaned_sources:
        return {
            "answer": "",
            "sources": [],
            "refused": True,
            "refusal_reason": "hors_base",
        }

    return {
        "answer": parsed.get("answer", ""),
        "sources": cleaned_sources,
        "refused": False,
        "refusal_reason": None,
    }
