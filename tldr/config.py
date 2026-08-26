"""
config.py - all configuration comes from the environment (12-factor style).

Why this matters for deployment: the SAME image runs on your laptop, in CI, in
staging, and in production. What changes between them is not the code - it's the
environment. So anything that differs (which model, which port, the git commit
that built it, secret keys) is read from environment variables here, never
hardcoded and never committed.

Read ../../knowledge/07_secrets_and_config.md for the full story.
"""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_env: str          # "development" | "staging" | "production"
    git_sha: str          # the commit the running image was built from
    model: str            # "offline" (default, no key needed) | "gemini"
    gemini_api_key: str    # a SECRET - only ever arrives via the environment
    port: int             # the port to listen on; the host (e.g. Cloud Run) sets $PORT

    @property
    def has_gemini_key(self) -> bool:
        return bool(self.gemini_api_key)

    def public_dict(self) -> dict:
        """Config that is safe to expose (e.g. on /version). Never leak the key."""
        return {
            "app_env": self.app_env,
            "git_sha": self.git_sha,
            "model": self.model if (self.model != "gemini" or self.has_gemini_key) else "offline",
        }


def load_settings() -> Settings:
    """Build Settings from environment variables, with safe defaults so the app
    runs out of the box with nothing configured."""
    return Settings(
        app_env=os.environ.get("APP_ENV", "development"),
        git_sha=os.environ.get("GIT_SHA", "dev"),
        model=os.environ.get("TLDR_MODEL", "offline").lower(),
        gemini_api_key=os.environ.get("GEMINI_API_KEY", ""),
        # Cloud hosts inject $PORT and expect you to listen on it. Default 8000 locally.
        port=int(os.environ.get("PORT", "8000")),
    )
