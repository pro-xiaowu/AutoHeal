from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.response import ok
from app.core.config_manager import ConfigManager
from app.models.user import User


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview")
def overview(request: Request, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    values = ConfigManager(db, request.app.state.settings)
    values.seed_defaults()
    config = values.get_values()
    canonical = config.get("llm_provider") is not None and config.get("llm_api_format") is not None
    provider = str(config.get("llm_provider", "ollama"))
    api_format = str(config.get("llm_api_format", "ollama"))
    if not canonical and config.get("llm_mode") is not None:
        legacy_mode = str(config["llm_mode"])
        provider, api_format = {
            "local": ("ollama", "ollama"),
            "openai": ("openai", "openai_chat"),
            "deepseek": ("deepseek", "openai_chat"),
            "qwen": ("qwen", "openai_chat"),
            "zhipu": ("zhipu", "openai_chat"),
            "azure": ("custom", "openai_chat"),
        }.get(legacy_mode, ("custom", "openai_chat"))
    return ok(
        {
            "setup_completed": bool(config.get("setup_completed", False)),
            "llm_provider": provider,
            "llm_api_format": api_format,
            "llm_migration_required": bool(config.get("llm_migration_required", False)),
            "llm_model": config.get("llm_model", "qwen2.5:7b"),
            "dependencies": {
                "database": "ok",
                "redis": "configured",
                "chromadb": "configured",
                "ollama": "configured" if provider == "ollama" else "not_required",
            },
        }
    )
