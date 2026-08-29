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


def test_production_rejects_development_placeholder_secrets():
    with pytest.raises(ValueError, match="SECRET_KEY"):
        Settings(
            environment="production",
            secret_key="development-secret-key",
            fernet_key="development-fernet-key",
        )


def test_production_rejects_example_secret():
    with pytest.raises(ValueError, match="SECRET_KEY"):
        Settings(
            _env_file=None,
            environment="production",
            secret_key="change-me",
            fernet_key="0Vv2P6W3Jj3X7P0zZt3Tq1b6c4l5w2x8s9d0f1g2h3i=",
        )
