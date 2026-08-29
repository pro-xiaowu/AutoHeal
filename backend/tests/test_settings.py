import pytest

from app.core.settings import Settings


def test_settings_use_sqlite_and_local_llm_defaults(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings(_env_file=None)

    assert settings.database_url.startswith("sqlite")
    assert settings.llm_mode == "local"
    assert settings.llm_model == "qwen2.5:7b"


def test_production_requires_explicit_secrets():
    with pytest.raises(ValueError, match="SECRET_KEY"):
        Settings(environment="production", secret_key="", fernet_key="")
