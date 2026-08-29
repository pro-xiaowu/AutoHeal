from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.response import ok
from app.core.config_manager import ConfigManager
from app.models.user import User
from app.schemas.config import ConfigUpdateRequest, LlmTestRequest
from app.services.llm_test import test_llm_connection


router = APIRouter(prefix="/config", tags=["config"])


def _manager(request: Request, db: Session) -> ConfigManager:
    manager = ConfigManager(db, request.app.state.settings)
    manager.seed_defaults()
    return manager


@router.get("")
def get_config(request: Request, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return ok(_manager(request, db).get_all())


@router.put("")
def update_config(
    payload: ConfigUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if "setup_completed" in payload.values:
        raise HTTPException(status_code=422, detail="setup_completed 只能由安装向导设置")
    try:
        manager = _manager(request, db)
        manager.set_values(payload.values, actor=user.username)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ok(manager.get_all(), "配置已保存")


@router.post("/test/llm")
def test_llm(
    payload: LlmTestRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    manager = _manager(request, db)
    current = manager.get_values()
    values: dict[str, Any] = {**current, **payload.values}
    if payload.values.get("llm_api_key") == "********":
        values["llm_api_key"] = current.get("llm_api_key", "")
    return ok(test_llm_connection(values, request.app.state.settings))
