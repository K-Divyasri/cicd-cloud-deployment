"""End-to-end API tests using FastAPI's TestClient. This is exactly how CI checks
the service before it's allowed to deploy - no server, no network, just the app.

Using TestClient as a context manager runs the lifespan (startup), so /ready
flips to 200 - which is what we assert."""
from fastapi.testclient import TestClient

from tldr.app import app
from tldr import __version__


def test_health_is_always_ok():
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


def test_ready_after_startup():
    with TestClient(app) as client:  # context manager fires startup
        r = client.get("/ready")
        assert r.status_code == 200
        assert r.json()["status"] == "ready"


def test_version_reports_build():
    with TestClient(app) as client:
        r = client.get("/version")
        assert r.status_code == 200
        assert r.json()["version"] == __version__
        assert "git_sha" in r.json()


def test_summarize_returns_a_summary():
    with TestClient(app) as client:
        text = ("Continuous integration runs your tests automatically on every push. "
                "It catches breakage before it reaches users. "
                "Continuous deployment then ships the passing build for you.")
        r = client.post("/summarize", json={"text": text})
        assert r.status_code == 200
        body = r.json()
        assert body["model"] == "offline"
        assert body["words"] > 0
        assert len(body["summary"]) > 0


def test_summarize_validates_input():
    with TestClient(app) as client:
        r = client.post("/summarize", json={})  # missing 'text'
        assert r.status_code == 422  # FastAPI validation error
