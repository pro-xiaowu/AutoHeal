from fastapi.testclient import TestClient

from app.main import create_app


def test_health_returns_standard_response_envelope():
    response = TestClient(create_app()).get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"code": 0, "message": "ok", "data": {"status": "ok"}}


def test_health_returns_503_when_database_is_unavailable(tmp_path):
    from app.core.settings import Settings

    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'health-broken.db'}",
        secret_key="test-secret",
        fernet_key="0Vv2P6W3Jj3X7P0zZt3Tq1b6c4l5w2x8s9d0f1g2h3i=",
    )
    client = TestClient(create_app(settings))

    class BrokenEngine:
        def connect(self):
            raise RuntimeError("database is unavailable")

    client.app.state.engine = BrokenEngine()
    response = client.get("/api/v1/health")

    assert response.status_code == 503
    assert response.json() == {"code": 503, "message": "数据库不可用", "data": None}


def test_unhandled_errors_keep_the_standard_response_envelope(tmp_path):
    from app.core.settings import Settings

    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'health-error.db'}",
        secret_key="test-secret",
        fernet_key="0Vv2P6W3Jj3X7P0zZt3Tq1b6c4l5w2x8s9d0f1g2h3i=",
    )
    app = create_app(settings)

    @app.get("/api/v1/test/unhandled")
    def unhandled():
        raise RuntimeError("private implementation detail")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/v1/test/unhandled")

    assert response.status_code == 500
    assert response.json() == {"code": 500, "message": "内部服务器错误", "data": None}
