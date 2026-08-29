from fastapi import FastAPI

from app.core.settings import Settings


def create_app() -> FastAPI:
    settings = Settings()
    app = FastAPI(title=settings.app_name)

    @app.get("/api/v1/health")
    def health() -> dict:
        return {"code": 0, "message": "ok", "data": {"status": "ok"}}

    return app


app = create_app()
