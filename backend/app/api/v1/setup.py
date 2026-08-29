from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.response import ok
from app.core.config_manager import ConfigManager
from app.core.security import hash_password
from app.models.user import User
from app.schemas.setup import SetupRequest


router = APIRouter(prefix="/setup", tags=["setup"])


def _manager(request: Request, db: Session) -> ConfigManager:
    manager = ConfigManager(db, request.app.state.settings)
    manager.seed_defaults()
    return manager


@router.get("")
def setup_status(request: Request, db: Session = Depends(get_db)):
    manager = _manager(request, db)
    values = manager.get_values()
    return ok({"setup_completed": bool(values.get("setup_completed", False)), "defaults": manager.get_all()})


@router.post("")
def complete_setup(payload: SetupRequest, request: Request, db: Session = Depends(get_db)):
    manager = _manager(request, db)
    if bool(manager.get_values().get("setup_completed", False)):
        raise HTTPException(status_code=409, detail="系统已完成初始化")
    if db.scalar(select(User).where(User.username == payload.username)) is not None:
        raise HTTPException(status_code=409, detail="管理员账号已存在")
    user = User(username=payload.username, password_hash=hash_password(payload.password), role="admin")
    db.add(user)
    try:
        db.flush()
        manager.set_values(
            {
                "llm_mode": payload.llm_mode,
                "llm_model": payload.llm_model,
                "llm_base_url": payload.llm_base_url,
                "llm_api_key": payload.llm_api_key,
                "llm_temperature": payload.llm_temperature,
                "llm_max_tokens": payload.llm_max_tokens,
                "llm_timeout": payload.llm_timeout,
                "llm_max_retries": payload.llm_max_retries,
                "prometheus_url": payload.prometheus_url,
                "prometheus_token": payload.prometheus_token,
                "setup_completed": True,
            },
            actor=payload.username,
        )
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="管理员账号已存在") from exc
    return ok({"setup_completed": True, "username": user.username}, "初始化完成")
