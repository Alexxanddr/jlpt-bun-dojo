import pytest
from fastapi.testclient import TestClient

from trainer import app as module


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "trainer.db"))
    monkeypatch.setenv("APP_PASSWORD", "test-password-long-enough")
    monkeypatch.setenv("APP_ORIGIN", "http://testserver")
    module.credentials.clear()
    module.requests_window.clear()
    with TestClient(module.app) as c:
        yield c


@pytest.fixture
def authenticated(client):
    r = client.post("/api/login", json={"password": "test-password-long-enough"},
                    headers={"x-trainer-request": "1"})
    assert r.status_code == 200
    client.headers["x-trainer-request"] = "1"
    return client


@pytest.fixture
def passwordless(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "trainer.db"))
    monkeypatch.delenv("APP_PASSWORD", raising=False)
    monkeypatch.setenv("APP_ORIGIN", "http://testserver")
    module.credentials.clear()
    module.requests_window.clear()
    with TestClient(module.app) as c:
        yield c
