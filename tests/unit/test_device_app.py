import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demo" / "device"))
import app as device  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DEVICE_CONF", str(tmp_path / "device.conf"))
    monkeypatch.setenv("DEVICE_LOG", str(tmp_path / "device.log"))
    device.STATE["fault"] = False
    c = TestClient(device.app)
    c.post("/login", data={"username": "admin", "password": "admin"})
    return c


def save(client, value="10.0.0.5"):
    return client.post(
        "/settings",
        data={"syslog_server": value},
        headers={"X-Run-Id": "abc123"},
    )


def test_save_persists(client):
    assert "Saved" in save(client).text
    assert client.get("/api/settings").json() == {"syslog_server": "10.0.0.5"}


def test_fault_says_saved_but_does_not_persist(client):
    client.post("/api/fault", json={"enabled": True})
    assert "Saved" in save(client).text
    assert client.get("/api/settings").json() == {}
    log = Path(device.log_path()).read_text()
    assert "persist failed" in log and "run_id=abc123" in log


def test_settings_requires_login():
    anon = TestClient(device.app)
    assert anon.get("/settings", follow_redirects=False).status_code == 303
