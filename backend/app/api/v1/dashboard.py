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
    return ok(
        {
            "setup_completed": bool(config.get("setup_completed", False)),
            "llm_mode": config.get("llm_mode", "local"),
            "llm_model": config.get("llm_model", "qwen2.5:7b"),
            "dependencies": {
                "database": "ok",
                "redis": "configured",
                "chromadb": "configured",
                "ollama": "configured" if config.get("llm_mode") == "local" else "not_required",
            },
        }
    )
