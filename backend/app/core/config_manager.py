from collections.abc import Mapping

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decrypt_secret, encrypt_secret
from app.core.settings import Settings
from app.models.audit import AuditLog
from app.models.system_config import SystemConfig


DEFAULT_CONFIGS: tuple[dict[str, object], ...] = (
    {"key": "setup_completed", "value": False, "secret": False, "category": "system", "description": "是否完成首次安装"},
    {"key": "llm_mode", "value": "local", "secret": False, "category": "ai_engine", "description": "LLM 调用模式"},
    {"key": "llm_model", "value": "qwen2.5:7b", "secret": False, "category": "ai_engine", "description": "LLM 模型名称"},
    {"key": "llm_base_url", "value": "http://ollama:11434", "secret": False, "category": "ai_engine", "description": "LLM 服务地址"},
    {"key": "llm_api_key", "value": "", "secret": True, "category": "ai_engine", "description": "LLM API 密钥"},
    {"key": "llm_temperature", "value": 0.1, "secret": False, "category": "ai_engine", "description": "LLM 温度"},
    {"key": "llm_max_tokens", "value": 2048, "secret": False, "category": "ai_engine", "description": "最大输出 Token"},
    {"key": "llm_timeout", "value": 60, "secret": False, "category": "ai_engine", "description": "请求超时秒数"},
    {"key": "llm_max_retries", "value": 3, "secret": False, "category": "ai_engine", "description": "失败重试次数"},
    {"key": "prometheus_url", "value": "", "secret": False, "category": "alert_source", "description": "Prometheus 地址"},
    {"key": "prometheus_token", "value": "", "secret": True, "category": "alert_source", "description": "Prometheus 访问令牌"},
)

_CLOUD_MODES = {"openai", "deepseek", "qwen", "azure", "zhipu"}
_INT_KEYS = {"llm_max_tokens", "llm_timeout", "llm_max_retries"}
_FLOAT_KEYS = {"llm_temperature"}
_BOOL_KEYS = {"setup_completed"}


class ConfigManager:
    def __init__(self, session: Session, settings: Settings):
        self.session = session
        self.settings = settings

    def seed_defaults(self) -> None:
        existing = {row.config_key for row in self.session.scalars(select(SystemConfig)).all()}
        settings_values = {
            "llm_mode": self.settings.llm_mode,
            "llm_model": self.settings.llm_model,
            "llm_base_url": self.settings.llm_base_url,
            "llm_api_key": self.settings.llm_api_key,
            "llm_temperature": self.settings.llm_temperature,
            "llm_max_tokens": self.settings.llm_max_tokens,
            "llm_timeout": self.settings.llm_timeout_seconds,
            "llm_max_retries": self.settings.llm_max_retries,
            "prometheus_url": self.settings.prometheus_url,
            "prometheus_token": self.settings.prometheus_token,
        }
        for item in DEFAULT_CONFIGS:
            key = str(item["key"])
            if key in existing:
                continue
            value = settings_values.get(key, item["value"])
            if item["secret"] and value:
                value = encrypt_secret(str(value), self.settings)
            self.session.add(
                SystemConfig(
                    config_key=key,
                    config_value=self._serialize(value),
                    is_secret=bool(item["secret"]),
                    category=str(item["category"]),
                    description=str(item["description"]),
                )
            )
        self.session.commit()

    def _rows(self) -> list[SystemConfig]:
        return list(self.session.scalars(select(SystemConfig).order_by(SystemConfig.category, SystemConfig.config_key)))

    def get_all(self, mask_secrets: bool = True) -> dict[str, dict[str, object]]:
        result: dict[str, dict[str, object]] = {}
        for row in self._rows():
            raw = row.config_value or ""
            is_set = bool(raw)
            value: object = "********" if row.is_secret and mask_secrets and is_set else self._parse(row.config_key, raw)
            result[row.config_key] = {
                "value": value,
                "is_set": is_set,
                "is_secret": row.is_secret,
                "category": row.category,
                "description": row.description,
            }
        return result

    def get_values(self) -> dict[str, object]:
        values: dict[str, object] = {}
        for row in self._rows():
            raw = row.config_value or ""
            if row.is_secret and raw:
                raw = decrypt_secret(raw, self.settings)
            values[row.config_key] = self._parse(row.config_key, raw)
        return values

    def set_values(self, values: Mapping[str, object], actor: str | None = None) -> None:
        rows = {row.config_key: row for row in self._rows()}
        unknown = set(values) - set(rows)
        if unknown:
            raise ValueError(f"Unknown configuration key: {sorted(unknown)[0]}")
        current = self.get_values()
        merged = {**current, **values}
        mode = str(merged.get("llm_mode", "local"))
        if mode not in {"local", *_CLOUD_MODES}:
            raise ValueError("Unsupported LLM mode")
        if mode in _CLOUD_MODES and not str(merged.get("llm_api_key", "")).strip():
            raise ValueError("API key is required for cloud LLM modes")
        for key, value in values.items():
            row = rows[key]
            serialized = self._serialize(value)
            if row.is_secret and str(value):
                serialized = encrypt_secret(str(value), self.settings)
            row.config_value = serialized
        self.session.add(
            AuditLog(actor=actor, action="config.update", category="system_config", success=True, detail=f"updated={','.join(values)}")
        )
        self.session.commit()

    @staticmethod
    def _serialize(value: object) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        return "" if value is None else str(value)

    @staticmethod
    def _parse(key: str, value: str) -> object:
        if key in _BOOL_KEYS:
            return value.lower() == "true"
        if key in _INT_KEYS:
            return int(value) if value else 0
        if key in _FLOAT_KEYS:
            return float(value) if value else 0.0
        return value
