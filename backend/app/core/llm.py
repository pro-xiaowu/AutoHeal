from collections.abc import Mapping

from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.core.settings import Settings


_DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "azure": "https://api.openai.com/v1",
    "zhipu": "https://open.bigmodel.cn/api/paas/v4",
}


def get_llm(config: Mapping[str, object], settings: Settings | None = None):
    mode = str(config.get("llm_mode", "local"))
    model = str(config.get("llm_model", "qwen2.5:7b"))
    temperature = float(config.get("llm_temperature", 0.1))
    max_tokens = int(config.get("llm_max_tokens", 2048))
    timeout = int(config.get("llm_timeout", config.get("llm_timeout_seconds", 60)))
    max_retries = int(config.get("llm_max_retries", 3))
    base_url = str(config.get("llm_base_url") or _DEFAULT_BASE_URLS.get(mode, ""))
    if mode == "local":
        return ChatOllama(
            model=model,
            base_url=base_url or (settings.llm_base_url if settings else "http://ollama:11434"),
            temperature=temperature,
            num_predict=max_tokens,
        )
    if mode not in _DEFAULT_BASE_URLS:
        raise ValueError(f"Unsupported LLM mode: {mode}")
    api_key = str(config.get("llm_api_key", ""))
    if not api_key:
        raise ValueError("API key is required for cloud LLM modes")
    return ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        max_retries=max_retries,
    )
