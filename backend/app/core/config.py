from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333


settings = Settings()
