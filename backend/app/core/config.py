from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://learnpath:learnpath@localhost:5432/learnpath"
    secret_key: str = "dev-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536
    llm_base_url: str | None = None  # set to point at any OpenAI-compatible endpoint

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
