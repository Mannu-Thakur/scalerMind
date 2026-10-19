from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    database_url: str = "postgresql+asyncpg://scalermind:local_development_only@localhost:5432/scalermind"
    redis_url: str = "redis://localhost:6379/0"


settings = Settings()
