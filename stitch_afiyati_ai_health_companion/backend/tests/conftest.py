from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture()
def app_settings(tmp_path: Path) -> Settings:
    return Settings(
        data_dir=tmp_path / "data",
        database_path=tmp_path / "data" / "test.db",
        qdrant_path=tmp_path / "data" / "qdrant",
        secret_key="test-secret-key",
        food_data_enabled=False,
        cofid_enabled=False,
    )


@pytest.fixture()
def client(app_settings: Settings):
    app = create_app(app_settings)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": "test@example.com", "password": "safe-password-123"},
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['token']}"}
