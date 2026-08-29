from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AutoHeal"
    environment: str = "development"
    database_url: str = "sqlite:///./autoheal.db"
    redis_url: str = "redis://localhost:6379/0"
    chroma_url: str = "http://localhost:8001"
    secret_key: str = "development-secret-key"
    fernet_key: str = "development-fernet-key"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    llm_mode: str = "local"
    llm_model: str = "qwen2.5:7b"
    llm_base_url: str = "http://localhost:11434"
    llm_temperature: float = 0.2
    llm_timeout_seconds: int = 120

    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    prometheus_path: str = "/metrics"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("environment")
    @classmethod
    def normalize_environment(cls, value: str):
        return value.lower()

    @model_validator(mode="after")
    def validate_production_secrets(self):
        if self.environment == "production":
            placeholders = {
                "development-secret-key": "SECRET_KEY",
                "development-fernet-key": "FERNET_KEY",
                "": "SECRET_KEY or FERNET_KEY",
            }
            if self.secret_key in placeholders:
                raise ValueError(f"{placeholders[self.secret_key]} must be explicitly configured in production")
            if self.fernet_key in ("", "development-fernet-key"):
                raise ValueError("FERNET_KEY must be explicitly configured in production")
        return self
