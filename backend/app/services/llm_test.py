import time
from collections.abc import Mapping

import httpx

from app.core.llm import get_llm
from app.core.settings import Settings


def _category_for_error(error: Exception) -> str:
    message = str(error).lower()
    if "401" in message or "403" in message or "api key" in message or "unauthorized" in message:
        return "authentication"
    if isinstance(error, (httpx.TimeoutException, TimeoutError)) or "timeout" in message:
        return "timeout"
    if "not found" in message or "model" in message and "exist" in message:
        return "model_not_found"
    return "unreachable"


def test_llm_connection(config: Mapping[str, object], settings: Settings) -> dict[str, object]:
    started = time.perf_counter()
    mode = str(config.get("llm_mode", "local"))
    try:
        if mode == "local":
            base_url = str(config.get("llm_base_url") or settings.llm_base_url).rstrip("/")
            timeout = float(config.get("llm_timeout", settings.llm_timeout_seconds))
            response = httpx.get(f"{base_url}/api/tags", timeout=timeout)
            response.raise_for_status()
            models = response.json().get("models", [])
            target = str(config.get("llm_model", settings.llm_model))
            names = {str(item.get("name", "")) for item in models}
            if target not in names and f"{target}:latest" not in names:
                return {
                    "ok": False,
                    "provider": "ollama",
                    "category": "model_not_found",
                    "message": f"模型不存在：{target}",
                    "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                }
            return {
                "ok": True,
                "provider": "ollama",
                "category": "ok",
                "message": "Ollama 服务和模型可用",
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            }
        llm = get_llm(config, settings)
        llm.invoke("Reply with OK")
        return {
            "ok": True,
            "provider": mode,
            "category": "ok",
            "message": "LLM 连接成功",
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }
    except ValueError as exc:
        return {
            "ok": False,
            "provider": mode,
            "category": "invalid_configuration",
            "message": str(exc),
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }
    except Exception as exc:
        return {
            "ok": False,
            "provider": mode,
            "category": _category_for_error(exc),
            "message": "LLM 连接失败，请检查地址、模型和凭据",
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }
