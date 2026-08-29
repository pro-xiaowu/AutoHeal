from typing import Any

from pydantic import BaseModel, Field


class ConfigUpdateRequest(BaseModel):
    values: dict[str, Any] = Field(min_length=1)


class LlmTestRequest(BaseModel):
    values: dict[str, Any] = Field(default_factory=dict)


class ModelDiscoveryRequest(BaseModel):
    values: dict[str, Any] = Field(default_factory=dict)
