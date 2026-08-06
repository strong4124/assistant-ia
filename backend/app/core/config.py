from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333

    corpus_dir: str = "/app/data/corpus"

    generation_backend: str = "ollama"  # "ollama" ou "anthropic"

    anthropic_api_key: str = ""
    generation_model: str = "claude-sonnet-5"

    ollama_host: str = "ollama"
    ollama_port: int = 11434
    ollama_model: str = "mistral"

    min_rrf_score: float = 0.01
    telegram_bot_token: str | None = None


settings = Settings()
