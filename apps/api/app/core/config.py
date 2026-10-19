from secrets import token_urlsafe
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEVELOPMENT_SIGNING_KEY = token_urlsafe(48)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    database_url: str = "postgresql+asyncpg://scalermind:local_development_only@localhost:5432/scalermind"
    redis_url: str = "redis://localhost:6379/0"
    app_env: Literal["development", "test", "production"] = "development"
    jwt_secret_key: SecretStr | None = None
    access_token_minutes: int = Field(default=15, ge=1, le=60)
    refresh_token_days: int = Field(default=7, ge=1, le=90)
    secure_auth_cookies: bool = False
    refresh_cookie_name: str = "scalermind_refresh"
    csrf_cookie_name: str = "scalermind_csrf"

    @field_validator("jwt_secret_key", mode="before")
    @classmethod
    def treat_empty_secret_as_unset(cls, value):
        return None if value is None or value == "" else value

    @model_validator(mode="after")
    def require_production_auth_settings(self):
        if self.app_env == "production":
            secret = self.jwt_secret_key.get_secret_value() if self.jwt_secret_key else ""
            if len(secret) < 32:
                raise ValueError("JWT_SECRET_KEY must contain at least 32 characters in production")
            if not self.secure_auth_cookies:
                raise ValueError("SECURE_AUTH_COOKIES must be true in production")
        return self

    @property
    def signing_key(self) -> str:
        if self.jwt_secret_key:
            return self.jwt_secret_key.get_secret_value()
        return _DEVELOPMENT_SIGNING_KEY


settings = Settings()
