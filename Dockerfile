# A Docker image is a frozen, self-contained snapshot of your app + everything it
# needs to run. This one is read top-to-bottom; each instruction is a cached LAYER.
# The ORDER matters: put things that rarely change first, so a code edit doesn't
# force a slow reinstall of dependencies. See knowledge/04_docker_fundamentals.md.

FROM python:3.12-slim

# Baked in at build time by CI (`docker build --build-arg GIT_SHA=$(git rev-parse HEAD)`).
# This is how /version can honestly report which commit produced this exact image -
# invaluable when you're staring at a production bug asking "wait, is the fix even deployed?"
ARG GIT_SHA=dev

# Sensible Python defaults for containers.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    GIT_SHA=${GIT_SHA}

WORKDIR /app

# --- dependency layer (changes rarely) -------------------------------------
# Copy ONLY requirements first. As long as this file doesn't change, Docker
# reuses the cached "pip install" layer even when your source code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- application layer (changes often) -------------------------------------
COPY tldr ./tldr

# Run as a non-root user. If the app is ever compromised, the attacker isn't root
# inside the container. A basic, expected security practice for production images.
RUN useradd --create-home appuser
USER appuser

# Documents the port; the app actually listens on $PORT (default 8000).
EXPOSE 8000

# The host/orchestrator uses this to know if the container is healthy. We use
# Python (already installed) so we don't need to add curl to a slim image.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8000')+'/health')" || exit 1

# Exec form (a real PID 1, so signals/shutdown work). `python -m tldr` reads $PORT
# and binds 0.0.0.0 so traffic from outside the container can reach it.
CMD ["python", "-m", "tldr"]
