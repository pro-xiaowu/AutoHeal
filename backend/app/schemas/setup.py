from pydantic import BaseModel, Field, field_validator


_MODES = {"local", "openai", "deepseek", "qwen", "azure", "zhipu"}


class SetupRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=255)
    llm_mode: str = "local"
    llm_model: str = Field(default="qwen2.5:7b", min_length=1, max_length=255)
    llm_base_url: str = "http://ollama:11434"
    llm_api_key: str = ""
    llm_temperature: float = Field(default=0.1, ge=0, le=1)
    llm_max_tokens: int = Field(default=2048, ge=1, le=200000)
    llm_timeout: int = Field(default=60, ge=1, le=3600)
    llm_max_retries: int = Field(default=3, ge=0, le=20)
    prometheus_url: str = ""
    prometheus_token: str = ""

    @field_validator("llm_mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        if value not in _MODES:
            raise ValueError("Unsupported LLM mode")
        return value

    @field_validator("llm_api_key")
    @classmethod
    def validate_key_for_mode(cls, value: str, info):
        if info.data.get("llm_mode") in _MODES - {"local"} and not value.strip():
            raise ValueError("API key is required for cloud LLM modes")
        return value
