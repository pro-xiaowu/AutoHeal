from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_core import PydanticCustomError

class SetupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=255)
    llm_provider: Literal["ollama", "openai", "anthropic", "deepseek", "qwen", "zhipu", "custom"] = "ollama"
    llm_api_format: Literal["ollama", "openai_chat", "openai_responses", "anthropic_messages"] = "ollama"
    llm_model: str = Field(default="qwen2.5:7b", min_length=1, max_length=255)
    llm_base_url: str = "http://ollama:11434"
    llm_api_key: str = ""
    llm_temperature: float = Field(default=0.1, ge=0, le=1)
    llm_max_tokens: int = Field(default=2048, ge=1, le=200000)
    llm_timeout: int = Field(default=60, ge=1, le=3600)
    llm_max_retries: int = Field(default=3, ge=0, le=20)
    prometheus_url: str = ""
    prometheus_token: str = ""

    @model_validator(mode="after")
    def validate_provider_configuration(self):
        formats = {
            "ollama": {"ollama"},
            "openai": {"openai_chat", "openai_responses"},
            "anthropic": {"anthropic_messages"},
            "deepseek": {"openai_chat"},
            "qwen": {"openai_chat"},
            "zhipu": {"openai_chat"},
            "custom": {"openai_chat", "openai_responses", "anthropic_messages"},
        }
        if self.llm_api_format not in formats[self.llm_provider]:
            raise PydanticCustomError("provider_format", "Unsupported provider and API format combination")
        return self
