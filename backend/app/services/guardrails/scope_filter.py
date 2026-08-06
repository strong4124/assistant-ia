import re

# Detecte les demandes clairement hors sujet pour un assistant de service
# client telecom - AVANT d'appeler la recherche hybride et le LLM, pour
# eviter un cycle Mistral de 30-190s sur une question qui n'a de toute
# facon rien a voir avec l'operateur. Distinct du refus RAG (qui gere le
# cas ou l'info EST liee au telecom mais absente de la base).
_OUT_OF_SCOPE_PATTERNS = [
    r"po[eè]me|poesie|chanson\b",
    r"recette de cuisine",
    r"raconte(-moi)? une histoire",
    r"\b(ecris|genere)\b.*\b(code|script|programme)\b",
    r"qui est le pr[ée]sident",
    r"capitale de\b",
    r"m[eé]t[eé]o (a|à|de|du|pour)\b",
    r"horoscope",
    r"blague|joke\b",
    # tentatives de contournement d'instructions (prompt injection)
    r"ignore (les|tes|toutes les) (instructions|regles|r[eè]gles)",
    r"oublie (tes|les) (instructions|regles|r[eè]gles)",
    r"tu es maintenant\b",
    r"nouveau (prompt|r[oô]le)\b",
    r"(montre|affiche|donne).*(prompt systeme|instructions systeme)",
]
_OUT_OF_SCOPE_RE = re.compile("|".join(_OUT_OF_SCOPE_PATTERNS), re.IGNORECASE)


def is_out_of_scope(text: str) -> bool:
    """True si la demande est manifestement hors du perimetre d'un
    assistant de service client telecom (ou tente de detourner ses
    instructions), independamment de ce que contient la base documentaire."""
    return bool(_OUT_OF_SCOPE_RE.search(text))
