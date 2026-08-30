import time
from collections.abc import Mapping

import httpx

from app.core.config_manager import normalize_provider_format, resolve_base_url, resolve_timeout, validate_provider_format
from app.core.llm import get_llm
from app.core.settings import Settings


def _category_for_error(error: Exception) -> str:
    message = str(error).lower()
    if "401" in message or "403" in message or "api key" in message or "unauthorized" in message:
        return "authentication"
    if isinstance(error, (httpx.TimeoutException, TimeoutError)) or "timeout" in message:
        return "timeout"
    if "not found" in message or ("model" in message and "exist" in message):
        return "model_not_found"
    return "unreachable"


def check_llm_connection(config: Mapping[str, object], settings: Settings) -> dict[str, object]:
    started = time.perf_counter()
    values = normalize_provider_format(config)
    provider = str(values.get("llm_provider", "ollama"))
    api_format = str(values.get("llm_api_format", "ollama"))
    try:
        validate_provider_format(values)
        if api_format == "ollama":
            base_url = resolve_base_url(values, provider, settings).rstrip("/")
            response = httpx.get(f"{base_url}/api/tags", timeout=resolve_timeout(config, settings))
            if response.status_code >= 400:
                response.raise_for_status()
            models = response.json().get("models", [])
            target = str(values.get("llm_model", settings.llm_model))
            names = {str(item.get("name", "")) for item in models if isinstance(item, dict)}
            if target not in names and f"{target}:latest" not in names:
                return {"ok": False, "provider": provider, "api_format": api_format, "category": "model_not_found", "message": f"模型不存在：{target}", "latency_ms": round((time.perf_counter() - started) * 1000, 2)}
        else:
            get_llm(values, settings).invoke("Reply with OK")
        return {"ok": True, "provider": provider, "api_format": api_format, "category": "ok", "message": "LLM 连接成功", "latency_ms": round((time.perf_counter() - started) * 1000, 2)}
    except ValueError as exc:
        return {"ok": False, "provider": provider, "api_format": api_format, "category": "invalid_configuration", "message": str(exc), "latency_ms": round((time.perf_counter() - started) * 1000, 2)}
    except Exception as exc:
        return {"ok": False, "provider": provider, "api_format": api_format, "category": _category_for_error(exc), "message": "LLM 连接失败，请检查地址、模型和凭据", "latency_ms": round((time.perf_counter() - started) * 1000, 2)}
