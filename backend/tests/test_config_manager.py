from sqlalchemy.orm import sessionmaker

from app.core.config_manager import ConfigManager
from app.core.database import Base, get_engine
from app.core.settings import Settings


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

    assert masked["llm_mode"]["value"] == "local"
    assert masked["llm_api_key"]["is_set"] is False
    assert values["llm_temperature"] == 0.1
    assert values["llm_max_tokens"] == 2048

    manager.set_values({"llm_api_key": "sk-test", "llm_temperature": 0.4})
    masked = manager.get_all()
    assert masked["llm_api_key"]["is_set"] is True
    assert masked["llm_api_key"]["value"] == "********"
    assert manager.get_values()["llm_api_key"] == "sk-test"
    session.close()


def test_cloud_modes_require_api_key_and_local_mode_does_not(tmp_path):
    manager, session = make_manager(tmp_path)
    manager.seed_defaults()

    manager.set_values({"llm_mode": "local", "llm_api_key": ""})
    manager.set_values({"llm_mode": "openai", "llm_api_key": "sk-test"})

    try:
        manager.set_values({"llm_mode": "deepseek", "llm_api_key": ""})
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
