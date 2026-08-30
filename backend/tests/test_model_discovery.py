from unittest.mock import patch

import httpx

from app.services.model_discovery import discover_models


def test_ollama_models_are_sorted_and_normalized():
    response = httpx.Response(200, json={"models": [{"name": "qwen2.5:7b"}, {"name": "llama3.1:8b"}]})
    with patch("app.services.model_discovery.httpx.get", return_value=response):
        result = discover_models({"llm_provider": "ollama", "llm_api_format": "ollama"}, _settings())
    assert result["models"] == ["llama3.1:8b", "qwen2.5:7b"]
    assert result["manual_input"] is False


def test_openai_models_use_bearer_header():
    response = httpx.Response(200, json={"data": [{"id": "gpt-4o-mini"}]})
    with patch("app.services.model_discovery.httpx.get", return_value=response) as get:
        result = discover_models({"llm_provider": "openai", "llm_api_format": "openai_chat", "llm_api_key": "key"}, _settings())
    assert result["models"] == ["gpt-4o-mini"]
    assert get.call_args.kwargs["headers"] == {"Authorization": "Bearer key"}


def test_anthropic_models_use_required_headers():
    response = httpx.Response(200, json={"data": [{"id": "claude-sonnet"}]})
    with patch("app.services.model_discovery.httpx.get", return_value=response) as get:
        result = discover_models({"llm_provider": "anthropic", "llm_api_format": "anthropic_messages", "llm_api_key": "key"}, _settings())
    assert result["models"] == ["claude-sonnet"]
    assert get.call_args.kwargs["headers"]["x-api-key"] == "key"
    assert get.call_args.kwargs["headers"]["anthropic-version"] == "2023-06-01"


def test_empty_result_and_timeout_allow_manual_input():
    response = httpx.Response(200, json={"data": []})
    with patch("app.services.model_discovery.httpx.get", return_value=response):
        empty = discover_models({"llm_provider": "openai", "llm_api_format": "openai_chat", "llm_api_key": "key"}, _settings())
    with patch("app.services.model_discovery.httpx.get", side_effect=httpx.ReadTimeout("slow")):
        timeout = discover_models({"llm_provider": "openai", "llm_api_format": "openai_chat", "llm_api_key": "key"}, _settings())
    assert empty["category"] == "empty" and empty["manual_input"] is True
    assert timeout["category"] == "timeout" and timeout["manual_input"] is True


def _settings():
    from app.core.settings import Settings

    return Settings(_env_file=None, fernet_key="0Vv2P6W3Jj3X7P0zZt3Tq1b6c4l5w2x8s9d0f1g2h3i=")
