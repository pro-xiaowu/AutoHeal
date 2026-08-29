from fastapi.testclient import TestClient

from app.core.settings import Settings
from app.main import create_app


def make_client(tmp_path):
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'api.db'}",
        fernet_key="0Vv2P6W3Jj3X7P0zZt3Tq1b6c4l5w2x8s9d0f1g2h3i=",
        secret_key="test-secret",
    )
    return TestClient(create_app(settings))


def test_setup_creates_admin_and_login_returns_jwt(tmp_path):
    client = make_client(tmp_path)
    payload = {
        "username": "admin",
        "password": "strong-password",
        "llm_provider": "ollama",
        "llm_api_format": "ollama",
        "llm_model": "qwen2.5:7b",
        "llm_base_url": "http://ollama:11434",
    }

    setup_response = client.post("/api/v1/setup", json=payload)
    assert setup_response.status_code == 200
    assert setup_response.json()["code"] == 0
    assert setup_response.json()["data"]["setup_completed"] is True

    login_response = client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "strong-password"}
    )
    assert login_response.status_code == 200
    assert login_response.json()["data"]["access_token"]


def test_setup_is_locked_after_first_completion(tmp_path):
    client = make_client(tmp_path)
    payload = {"username": "admin", "password": "strong-password", "llm_provider": "ollama", "llm_api_format": "ollama"}
    assert client.post("/api/v1/setup", json=payload).status_code == 200

    response = client.post("/api/v1/setup", json=payload)

    assert response.status_code == 409
    assert response.json()["code"] != 0
    assert "data" in response.json()


def test_cloud_setup_requires_api_key(tmp_path):
    client = make_client(tmp_path)
    response = client.post(
        "/api/v1/setup",
        json={"username": "admin", "password": "strong-password", "llm_provider": "openai", "llm_api_format": "openai_chat"},
    )

    assert response.status_code == 422
    assert "API key" in response.json()["message"]


def test_setup_rejects_legacy_mode_and_azure_provider(tmp_path):
    client = make_client(tmp_path)
    legacy = client.post(
        "/api/v1/setup",
        json={"username": "admin", "password": "strong-password", "llm_mode": "local"},
    )
    assert legacy.status_code == 422

    azure = client.post(
        "/api/v1/setup",
        json={"username": "admin", "password": "strong-password", "llm_provider": "azure", "llm_api_format": "openai_chat", "llm_api_key": "secret"},
    )
    assert azure.status_code == 422
