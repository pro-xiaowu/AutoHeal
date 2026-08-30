import pytest
from sqlalchemy.orm import sessionmaker

from app.core.config_manager import ConfigManager, normalize_provider_format, validate_provider_format
from app.core.database import Base, get_engine
from app.core.settings import Settings
from app.models.system_config import SystemConfig


def make_manager(tmp_path, **settings_overrides):
    engine = get_engine(f"sqlite:///{tmp_path / 'config.db'}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    settings = Settings(_env_file=None, fernet_key="0Vv2P6W3Jj3X7P0zZt3Tq1b6c4l5w2x8s9d0f1g2h3i=", **settings_overrides)
    return ConfigManager(session, settings), session


def test_seed_defaults_masks_secrets_and_round_trips_values(tmp_path):
    manager, session = make_manager(tmp_path)

    manager.seed_defaults()
    masked = manager.get_all()
    values = manager.get_values()

    assert masked["llm_provider"]["value"] == "ollama"
    assert masked["llm_api_format"]["value"] == "ollama"
    assert masked["llm_api_key"]["is_set"] is False
    assert values["llm_temperature"] == 0.1
    assert values["llm_max_tokens"] == 2048

    manager.set_values({"llm_api_key": "sk-test", "llm_temperature": 0.4})
    masked = manager.get_all()
    assert masked["llm_api_key"]["is_set"] is True
    assert masked["llm_api_key"]["value"] == "********"
    assert manager.get_values()["llm_api_key"] == "sk-test"
    session.close()


def test_cloud_providers_require_api_key_and_local_provider_does_not(tmp_path):
    manager, session = make_manager(tmp_path)
    manager.seed_defaults()

    manager.set_values({"llm_provider": "ollama", "llm_api_format": "ollama", "llm_api_key": ""})
    manager.set_values({"llm_provider": "openai", "llm_api_format": "openai_chat", "llm_api_key": "sk-test"})

    try:
        manager.set_values({"llm_provider": "deepseek", "llm_api_format": "openai_chat", "llm_api_key": ""})
    except ValueError as exc:
        assert "API key" in str(exc)
    else:
        raise AssertionError("cloud mode without an API key should fail")
    session.close()


def test_environment_defaults_fill_only_missing_database_values(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "env-model")
    manager, session = make_manager(tmp_path, llm_model="env-model")
    manager.seed_defaults()
    assert manager.get_values()["llm_model"] == "env-model"
    manager.set_values({"llm_model": "database-model"})
    manager.seed_defaults()
    assert manager.get_values()["llm_model"] == "database-model"
    session.close()


def test_masked_secret_value_preserves_existing_secret(tmp_path):
    manager, session = make_manager(tmp_path)
    manager.seed_defaults()
    manager.set_values({"llm_api_key": "sk-real"})
    manager.set_values({"llm_api_key": "********"})
    assert manager.get_values()["llm_api_key"] == "sk-real"
    session.close()


def test_provider_environment_default_uses_matching_format(tmp_path):
    manager, session = make_manager(tmp_path, llm_provider="openai", llm_api_format="ollama")
    manager.seed_defaults()
    values = manager.get_values()
    assert values["llm_provider"] == "openai"
    assert values["llm_api_format"] == "openai_chat"
    session.close()


def test_legacy_local_mode_maps_to_ollama(tmp_path):
    manager, session = make_manager(tmp_path)
    session.add(SystemConfig(config_key="llm_mode", config_value="local", is_secret=False, category="ai_engine"))
    session.commit()

    manager.seed_defaults()

    values = manager.get_values()
    assert values["llm_provider"] == "ollama"
    assert values["llm_api_format"] == "ollama"


def test_legacy_azure_mode_requires_custom_reconfiguration(tmp_path):
    manager, session = make_manager(tmp_path)
    session.add(SystemConfig(config_key="llm_mode", config_value="azure", is_secret=False, category="ai_engine"))
    session.commit()

    manager.seed_defaults()

    values = manager.get_values()
    assert values["llm_provider"] == "custom"
    assert values["llm_api_format"] == "openai_chat"
    assert values["llm_migration_required"] is True


def test_normalize_provider_format_maps_legacy_mode():
    assert normalize_provider_format({"llm_mode": "deepseek"}) == {
        "llm_mode": "deepseek",
        "llm_provider": "deepseek",
        "llm_api_format": "openai_chat",
    }


def test_validate_provider_format_rejects_mismatch_and_missing_cloud_key():
    with pytest.raises(ValueError, match="Unsupported provider"):
        validate_provider_format({"llm_provider": "ollama", "llm_api_format": "openai_chat"})
    with pytest.raises(ValueError, match="API key"):
        validate_provider_format({"llm_provider": "openai", "llm_api_format": "openai_chat"})
