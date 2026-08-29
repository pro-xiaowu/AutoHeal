from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.response import failure, ok


router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request):
    try:
        with request.app.state.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content=failure("数据库不可用", code=503))
    return ok({"status": "ok"})
