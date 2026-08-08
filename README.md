# Assistant IA de service client — Teranga Telecom

Assistant conversationnel RAG (Retrieval-Augmented Generation), omnicanal, avec ticketing et escalade vers un agent humain — projet de fin de stage ESMT (Projet 7).

## Fonctionnalités

- **Recherche hybride** (vectorielle + lexicale) sur une base documentaire réelle
- **Génération avec citation obligatoire** de la source, refus explicite si l'information n'est pas disponible
- **Garde-fous** : filtrage hors périmètre, anonymisation PII des journaux, blocage de tout engagement commercial généré par le modèle
- **Deux canaux** : widget web et bot Telegram
- **Ticketing automatique** avec interface agent, en cas de refus
- **Observabilité** : dashboard Grafana avec 9 métriques (résolution, escalade, latence, feedback...)
- **Déploiement HTTPS** via nginx (certificat auto-signé en local, Let's Encrypt sur un vrai VPS)

## Prérequis

- Docker et Docker Compose v2
- Une clé API Anthropic ou OpenAI (optionnel — le modèle par défaut, Mistral 7B, tourne localement via Ollama)

## Démarrage rapide

```bash
git clone https://github.com/strong4124/assistant-ia.git
cd assistant-ia
cp .env.example .env
# éditer .env : définir des mots de passe (POSTGRES_PASSWORD, JWT_SECRET_KEY,
# GRAFANA_ADMIN_PASSWORD) et, si besoin, une cle API et le token du bot Telegram
docker compose up -d --build
```

Le premier démarrage télécharge le modèle Mistral via Ollama et peut prendre quelques minutes.

## Vérifier que tout fonctionne

```bash
curl -sk https://localhost/health
```

Doit répondre `{"status":"ok"}`.

## Accès aux services

| Service | URL | Remarque |
|---|---|---|
| Widget client | `https://<ip-ou-domaine>/` | Certificat auto-signé en local — accepter l'avertissement du navigateur |
| Interface agent | `https://<ip-ou-domaine>/agent/tickets` | File de tickets d'escalade |
| API (documentation) | `https://<ip-ou-domaine>/docs` | Documentation OpenAPI interactive |
| Bot Telegram | `@Assistant_Teranga_Telecom_bot` | Fonctionne indépendamment, en polling |
| Grafana | `http://localhost:3000` (via tunnel SSH) | `ssh -L 3000:localhost:3000 user@serveur` — login `admin`, mot de passe dans `.env` |
| Prometheus | `http://localhost:9090` (via tunnel SSH) | `ssh -L 9090:localhost:9090 user@serveur` |

## Architecture

Client (web / Telegram)
│
nginx (HTTPS)
│
FastAPI ── recherche hybride (Qdrant + PostgreSQL)
│ └── génération (Ollama/Mistral local, ou API)
│ └── validation côté serveur (garde-fous)
│
PostgreSQL (sessions, messages, tickets, feedback)
│
Prometheus → Grafana (dashboard qualité)


## Structure du dépôt

assistant-ia/
├── docker-compose.yml
├── nginx/ # reverse proxy, config HTTPS
├── backend/
│ └── app/
│ ├── api/ # endpoints REST (chat, tickets, interface agent)
│ ├── channels/ # connecteur Telegram
│ ├── services/
│ │ ├── ingestion/ # chargement, découpage, embeddings
│ │ ├── retrieval/ # recherche hybride
│ │ ├── generation/ # prompt, appel LLM, validation
│ │ └── guardrails/ # filtre hors périmètre
│ └── scripts/ # ingestion, débogage, évaluation
├── frontend/ # widget web React
├── data/
│ ├── corpus/ # documentation source (Teranga Telecom)
│ └── eval/ # jeu de test annoté + résultats d'évaluation
└── monitoring/ # provisioning Prometheus + Grafana


## Évaluation

Un jeu de 60 questions-réponses annotées permet de mesurer automatiquement la qualité du pipeline :

```bash
docker compose exec api python -m app.scripts.run_evaluation
```

Résultats écrits dans `data/eval/results.csv`. Voir le rapport d'ingénierie pour l'analyse détaillée des résultats.

## Sécurité

- Aucun secret dans le dépôt : toutes les valeurs sensibles passent par `.env` (non versionné)
- Services internes (PostgreSQL, Qdrant, Ollama, Prometheus, Grafana) accessibles uniquement en local sur le serveur, jamais exposés publiquement
- Pare-feu limité aux ports 22 (SSH), 80 et 443

## Déclaration d'usage d'IA

Le développement de ce projet s'est appuyé sur l'assistant Claude (Anthropic) pour la conception, la génération de code, le diagnostic d'anomalies et la rédaction de la documentation. Voir la section dédiée du rapport d'ingénierie pour le détail complet.

## Auteur

Tegawendé Abdoul Rachid ZONGO — ESMT Dakar, filière Réseaux et Services de Télécommunications
