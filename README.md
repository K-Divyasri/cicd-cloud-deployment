# CI/CD Cloud Deployment

A tiny, real FastAPI service (`tldr-api`, `POST /summarize`) built to exercise CI/CD and cloud
deployment around it. The "AI" part (an offline extractive summarizer, with an optional real
LLM call) is intentionally small; the point of this project is everything around the app: tests
that run on every push, a Docker image, a CI pipeline, and a real deployment with a public URL.

## Run it locally (no Docker, no key)

```powershell
pip install -r requirements-dev.txt
python -m tldr
```

Visit http://localhost:8000/docs for interactive API docs, or:

```powershell
curl http://localhost:8000/health
curl -X POST http://localhost:8000/summarize -H "Content-Type: application/json" -d "{\"text\": \"Docker packages an app with everything it needs to run. The same image runs the same way everywhere.\"}"
```

## Run the tests

```powershell
pytest -q
```

15 tests, all offline: config loading (and that secrets never leak into `/version`), the
summarizer, and the full API via FastAPI's `TestClient`.

## Run it in Docker (this is the real proof it's "deployment ready")

```powershell
docker build -t tldr-api:local .
docker run -d --name tldr -p 8000:8000 tldr-api:local
curl http://localhost:8000/health
docker stop tldr; docker rm tldr
```

Verified while building this project: image builds (~456MB), all endpoints respond, and Docker's
own `HEALTHCHECK` reports `healthy` after the container starts.

## Project layout

```
tldr/               the package: app.py (FastAPI), summarize.py, config.py, __main__.py
tests/               pytest suite - config, summarizer, and full-API tests
Dockerfile           multi-layer image, non-root user, HEALTHCHECK, reads $PORT
.dockerignore        keeps secrets and junk out of the build context
.github/workflows/   ci.yml (test on every push) + deploy.yml (build, push, deploy on main)
render.yaml          Infrastructure-as-Code for the free host (Render)
.env.example         every config variable, documented - copy to .env, never commit it
```

## Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /` | friendly root |
| `GET /health` | liveness - "is the process up?" always cheap, always 200 |
| `GET /ready` | readiness - 503 until startup finishes, then 200 |
| `GET /version` | which build is running: app version, git SHA, env, model |
| `POST /summarize` | the actual work: `{"text": "..."}` -> a summary |

## Configuration (12-factor: everything from the environment)

See `.env.example`. Nothing is hardcoded; the same image runs in dev, CI, and production and just
reads different environment variables. `TLDR_MODEL=offline` (the default) needs no API key at all.

## Deploying it

`hosting/HOSTING_GUIDE.md` walks the actual free deployment to Render or Cloud Run.
