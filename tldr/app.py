"""
app.py - the FastAPI application.

Endpoints, and why each exists for a *deployed* service:
  GET  /          - a friendly root so hitting the URL in a browser shows something.
  GET  /health    - LIVENESS: "is the process up?" Always cheap, always 200. Hosts
                    and load balancers ping this to decide whether to restart you.
  GET  /ready     - READINESS: "are we ready to serve traffic?" Only 200 after
                    startup finishes. The difference between the two is a classic
                    deployment gotcha - see ../../knowledge/10_health_checks_and_deploy_safety.md.
  GET  /version   - which build is running (git SHA), env, and model. Priceless
                    when you're staring at production trying to tell what's deployed.
  POST /summarize - the actual work.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import __version__
from .config import load_settings
from .summarize import summarize

settings = load_settings()
# Flipped to True once startup has finished. Readiness reads this.
_state = {"ready": False}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pretend startup work: warming a model, opening a connection, loading data.
    # Until this finishes, /ready returns 503 so traffic isn't sent too early.
    _state["ready"] = True
    yield
    _state["ready"] = False


app = FastAPI(title="TL;DR API", version=__version__, lifespan=lifespan)


class SummarizeIn(BaseModel):
    text: str = Field(..., description="The text to summarise.")


@app.get("/")
def root():
    return {"service": "TL;DR API", "version": __version__,
            "docs": "/docs", "health": "/health"}


@app.get("/health")
def health():
    # Liveness: is the process alive at all? Keep this trivially cheap.
    return {"status": "ok"}


@app.get("/ready")
def ready():
    # Readiness: are we ready to take traffic? 503 while starting up.
    if _state["ready"]:
        return JSONResponse({"status": "ready"}, status_code=200)
    return JSONResponse({"status": "starting"}, status_code=503)


@app.get("/version")
def version():
    return {"version": __version__, **settings.public_dict()}


@app.post("/summarize")
def do_summarize(body: SummarizeIn):
    return summarize(body.text, settings)
