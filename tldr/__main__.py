"""
Run the app: `python -m tldr`

It listens on $PORT (default 8000) and host 0.0.0.0. Binding to 0.0.0.0 (not
127.0.0.1) is what lets traffic reach the process from OUTSIDE the container -
a mistake that costs people hours when their local app works but the deployed
one "can't be reached." Reading $PORT is what lets hosts like Cloud Run tell you
which port to use.
"""
import uvicorn

from .config import load_settings

if __name__ == "__main__":
    settings = load_settings()
    uvicorn.run("tldr.app:app", host="0.0.0.0", port=settings.port, log_level="info")
