from fastapi.testclient import TestClient

from app.main import create_app


def test_health_returns_standard_response_envelope():
    response = TestClient(create_app()).get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"code": 0, "message": "ok", "data": {"status": "ok"}}
