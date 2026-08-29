from collections.abc import Mapping

import httpx

from app.core.config_manager import resolve_base_url, resolve_timeout, validate_provider_format
from app.core.settings import Settings


def _result(provider: str, api_format: str, models: list[str], *, category: str = "ok", message: str = "ok") -> dict[str, object]:
    unique = sorted(set(models))
    empty = not unique
    return {
        "ok": category == "ok" and not empty,
        "provider": provider,
        "api_format": api_format,
        "models": unique,
        "manual_input": empty or category != "ok",
        "category": "empty" if category == "ok" and empty else category,
        "message": "未发现可用模型，请手动输入" if category == "ok" and empty else message,
    }


def _error_result(provider: str, api_format: str, category: str) -> dict[str, object]:
    messages = {
        "authentication": "模型服务认证失败，请检查 API Key",
        "timeout": "模型服务请求超时，请检查地址或超时设置",
        "unreachable": "模型服务不可达，请检查地址和网络",
        "unsupported": "该模型服务不支持模型列表发现，请手动输入",
    }
    return _result(provider, api_format, [], category=category, message=messages[category])


def discover_models(config: Mapping[str, object], settings: Settings) -> dict[str, object]:
    provider = str(config.get("llm_provider", "ollama"))
    api_format = str(config.get("llm_api_format", "ollama"))
    try:
        validate_provider_format(config)
    except ValueError:
        return _error_result(provider, api_format, "unsupported")
    base_url = resolve_base_url(config, provider, settings).rstrip("/")
    timeout = resolve_timeout(config, settings)
    api_key = str(config.get("llm_api_key", ""))
    try:
        if api_format == "ollama":
            response = httpx.get(f"{base_url}/api/tags", timeout=timeout)
            field = "name"
            items = response.json().get("models", [])
        elif api_format == "anthropic_messages":
            response = httpx.get(
                f"{base_url}/v1/models",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
                timeout=timeout,
            )
            field = "id"
            items = response.json().get("data", [])
        else:
            response = httpx.get(
                f"{base_url}/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=timeout,
            )
            field = "id"
            items = response.json().get("data", [])
        if response.status_code in (401, 403):
            return _error_result(provider, api_format, "authentication")
        if response.status_code == 404 and api_format == "anthropic_messages":
            return _error_result(provider, api_format, "unsupported")
        if response.status_code >= 400:
            response.raise_for_status()
        if not isinstance(items, list):
            return _error_result(provider, api_format, "unreachable")
        models = [str(item.get(field)) for item in items if isinstance(item, dict) and item.get(field)]
        return _result(provider, api_format, models)
    except httpx.TimeoutException:
        return _error_result(provider, api_format, "timeout")
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in (401, 403):
            return _error_result(provider, api_format, "authentication")
        if exc.response.status_code == 404 and api_format == "anthropic_messages":
            return _error_result(provider, api_format, "unsupported")
        return _error_result(provider, api_format, "unreachable")
    except (httpx.TransportError, ValueError, TypeError, KeyError):
        return _error_result(provider, api_format, "unreachable")
