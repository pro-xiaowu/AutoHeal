from fastapi.testclient import TestClient

from app.core.settings import Settings
from app.main import create_app


def make_authenticated_client(tmp_path):
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'config-api.db'}",
        fernet_key="0Vv2P6W3Jj3X7P0zZt3Tq1b6c4l5w2x8s9d0f1g2h3i=",
        secret_key="test-secret",
    )
    client = TestClient(create_app(settings))
    client.post(
        "/api/v1/setup",
        json={"username": "admin", "password": "strong-password", "llm_mode": "local"},
    )
    token = client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "strong-password"}
    ).json()["data"]["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def test_config_requires_jwt_and_masks_secret(tmp_path):
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'unauthorized.db'}",
        fernet_key="0Vv2P6W3Jj3X7P0zZt3Tq1b6c4l5w2x8s9d0f1g2h3i=",
        secret_key="test-secret",
    )
    anonymous = TestClient(create_app(settings))
    assert anonymous.get("/api/v1/config").status_code == 401

    client = make_authenticated_client(tmp_path)
    update = client.put("/api/v1/config", json={"values": {"llm_api_key": "sk-secret"}})
    assert update.status_code == 200
    config = client.get("/api/v1/config").json()["data"]
    assert config["llm_api_key"]["value"] == "********"
    assert "sk-secret" not in client.get("/api/v1/config").text


def test_config_update_returns_unified_error_for_invalid_mode(tmp_path):
    client = make_authenticated_client(tmp_path)
    response = client.put("/api/v1/config", json={"values": {"llm_mode": "invalid"}})

    assert response.status_code == 422
    assert response.json()["code"] != 0
    assert set(response.json()) == {"code", "message", "data"}


def test_saving_other_settings_preserves_existing_prometheus_token(tmp_path):
    client = make_authenticated_client(tmp_path)
    assert client.put(
        "/api/v1/config",
        json={"values": {"prometheus_token": "prom-secret"}},
    ).status_code == 200

    response = client.put(
        "/api/v1/config",
        json={"values": {"llm_model": "new-model", "prometheus_token": ""}},
    )

    assert response.status_code == 200
    config = client.get("/api/v1/config").json()["data"]
    assert config["prometheus_token"]["is_set"] is True
    assert config["llm_model"]["value"] == "new-model"
