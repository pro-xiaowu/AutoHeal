from collections.abc import Mapping

from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.core.config_manager import DEFAULT_BASE_URLS, resolve_base_url, resolve_timeout, validate_provider_format
from app.core.responses_adapter import OpenAIResponsesAdapter
from app.core.settings import Settings


def get_llm(config: Mapping[str, object], settings: Settings | None = None):
    values = dict(config)
    if "llm_provider" not in values:
        legacy_mode = str(values.get("llm_mode", "local"))
        values["llm_provider"] = "ollama" if legacy_mode == "local" else legacy_mode
        values.setdefault("llm_api_format", "ollama" if legacy_mode == "local" else "openai_chat")
    provider = str(values.get("llm_provider", "ollama"))
    api_format = str(values.get("llm_api_format", "ollama"))
    runtime_settings = settings or Settings()
    model = str(values.get("llm_model") or runtime_settings.llm_model)
    temperature = float(values.get("llm_temperature", 0.1))
    max_tokens = int(values.get("llm_max_tokens", 2048))
    timeout = resolve_timeout(values, runtime_settings)
    max_retries = int(values.get("llm_max_retries", 3))
    base_url = resolve_base_url(values, provider, runtime_settings)
    api_key = str(values.get("llm_api_key", ""))
    validate_provider_format({**values, "llm_provider": provider, "llm_api_format": api_format, "llm_api_key": api_key})
    if api_format == "ollama":
        return ChatOllama(model=model, base_url=base_url or DEFAULT_BASE_URLS["ollama"], temperature=temperature, num_predict=max_tokens)
    if api_format == "openai_chat":
        return ChatOpenAI(api_key=api_key, base_url=base_url, model=model, temperature=temperature, max_tokens=max_tokens, timeout=timeout, max_retries=max_retries)
    if api_format == "anthropic_messages":
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as exc:
            raise ValueError("Anthropic provider requires langchain-anthropic") from exc
        return ChatAnthropic(model=model, anthropic_api_key=api_key, anthropic_api_url=base_url, temperature=temperature, max_tokens=max_tokens, timeout=timeout, max_retries=max_retries)
    if api_format == "openai_responses":
        if provider not in {"openai", "custom"}:
            raise ValueError("Responses format is supported only by OpenAI or Custom providers")
        return OpenAIResponsesAdapter(base_url=base_url, api_key=api_key, model=model, timeout=timeout)
    raise ValueError("Unsupported LLM API format")
