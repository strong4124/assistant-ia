from prometheus_client import Counter, Histogram

# Metriques metier exigees par le cahier des charges, au-dela des metriques
# HTTP generiques deja fournies par prometheus-fastapi-instrumentator.

messages_total = Counter(
    "p7_messages_total",
    "Nombre total de messages utilisateur traites",
    ["channel"],
)

resolutions_total = Counter(
    "p7_resolutions_total",
    "Reponses resolues automatiquement sans escalade (refused=false)",
    ["channel"],
)

escalations_total = Counter(
    "p7_escalations_total",
    "Tickets crees automatiquement (escalade vers un agent humain)",
    ["reason"],
)

generation_duration_seconds = Histogram(
    "p7_generation_duration_seconds",
    "Duree de l'appel au LLM de generation (Ollama ou API), en secondes",
    buckets=[1, 5, 10, 20, 30, 60, 90, 120, 180, 300],
)
