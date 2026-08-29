from unittest.mock import Mock, patch

import httpx

from app.core.llm import get_llm
from app.core.settings import Settings
from app.services.llm_test import test_llm_connection


def config(**overrides):
    result = {
        "llm_mode": "local",
        "llm_model": "qwen2.5:7b",
        "llm_base_url": "http://ollama:11434",
        "llm_api_key": "",
        "llm_temperature": 0.1,
        "llm_max_tokens": 2048,
        "llm_timeout": 60,
        "llm_max_retries": 3,
    }
    result.update(overrides)
    return result


def test_llm_factory_selects_ollama_or_openai_compatible_provider():
    settings = Settings(_env_file=None, fernet_key="0Vv2P6W3Jj3X7P0zZt3Tq1b6c4l5w2x8s9d0f1g2h3i=")
    with patch("app.core.llm.ChatOllama") as ollama:
        get_llm(config(), settings)
        ollama.assert_called_once()

    with patch("app.core.llm.ChatOpenAI") as openai:
        get_llm(config(llm_mode="openai", llm_api_key="sk-test", llm_model="gpt-4o-mini"), settings)
        openai.assert_called_once()


def test_local_connection_reports_missing_model():
    response = httpx.Response(200, json={"models": [{"name": "other:latest"}]})
    with patch("app.services.llm_test.httpx.get", return_value=response):
        result = test_llm_connection(config(), Settings(_env_file=None))
    assert result["ok"] is False
    assert result["category"] == "model_not_found"


def test_api_connection_normalizes_authentication_failure():
    fake_llm = Mock()
    fake_llm.invoke.side_effect = Exception("401 invalid api key")
    with patch("app.services.llm_test.get_llm", return_value=fake_llm):
        result = test_llm_connection(
            config(llm_mode="openai", llm_api_key="sk-test"), Settings(_env_file=None)
        )
    assert result["ok"] is False
    assert result["category"] == "authentication"
