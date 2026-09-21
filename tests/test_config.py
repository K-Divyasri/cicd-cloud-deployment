"""Tests for 12-factor config loading and, importantly, that the secret key is
never exposed in the public config."""
from tldr.config import load_settings


def test_defaults_when_env_empty(monkeypatch):
    for k in ("APP_ENV", "GIT_SHA", "TLDR_MODEL", "GEMINI_API_KEY", "PORT"):
        monkeypatch.delenv(k, raising=False)
    s = load_settings()
    assert s.app_env == "development"
    assert s.git_sha == "dev"
    assert s.model == "offline"
    assert s.port == 8000
    assert s.has_gemini_key is False


def test_reads_from_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("GIT_SHA", "deadbeef")
    monkeypatch.setenv("PORT", "9090")
    s = load_settings()
    assert s.app_env == "production"
    assert s.git_sha == "deadbeef"
    assert s.port == 9090


def test_public_dict_never_leaks_the_key(monkeypatch):
    monkeypatch.setenv("TLDR_MODEL", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "super-secret-value")
    s = load_settings()
    public = s.public_dict()
    assert "super-secret-value" not in str(public)
    assert "gemini_api_key" not in public


def test_gemini_without_key_reports_offline(monkeypatch):
    monkeypatch.setenv("TLDR_MODEL", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    s = load_settings()
    # If you ask for gemini but supply no key, /version honestly says offline.
    assert s.public_dict()["model"] == "offline"
