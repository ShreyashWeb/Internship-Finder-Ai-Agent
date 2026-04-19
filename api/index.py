from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="Internship Finder AI Agent API", version="1.0.0")


@app.get("/")
def root() -> dict[str, str]:
    return {
        "status": "ok",
        "message": "Internship Finder AI Agent API is live on Vercel.",
        "hint": "Use /health for health checks.",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}
