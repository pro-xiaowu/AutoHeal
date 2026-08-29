from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.response import failure
from app.api.v1 import auth, config, dashboard, health, setup
from app.core.config_manager import ConfigManager
from app.core.database import get_engine, init_db
from app.core.settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        init_db(app.state.engine)
        from sqlalchemy.orm import Session

        with Session(app.state.engine) as db:
            ConfigManager(db, settings).seed_defaults()
        yield

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = get_engine(settings.database_url)
    init_db(app.state.engine)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code, content=failure(str(exc.detail), code=exc.status_code))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content=failure("请求参数校验失败", code=422, data=exc.errors()))

    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(_: Request, exc: SQLAlchemyError):
        return JSONResponse(status_code=500, content=failure("数据库操作失败", code=500))

    app.include_router(health.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(setup.router, prefix="/api/v1")
    app.include_router(config.router, prefix="/api/v1")
    app.include_router(dashboard.router, prefix="/api/v1")

    return app


app = create_app()
