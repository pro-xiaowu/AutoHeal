from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.response import ok
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.auth import LoginData, LoginRequest, UserSummary


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=dict)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token(str(user.id), user.role, request.app.state.settings)
    data = LoginData(
        access_token=token,
        user=UserSummary(id=user.id, username=user.username, role=user.role),
    )
    return ok(data.model_dump())
