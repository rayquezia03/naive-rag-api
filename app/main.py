import os
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.routes.ingest import router as ingest_router
from app.routes.chat import router as chat_router

app = FastAPI(
    title="Naive RAG API",
    description="Retrieval-Augmented Generation over Markdown documents using Ollama + LangChain.",
    version="1.0.0",
)

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

app.include_router(ingest_router)
app.include_router(chat_router)

with open(os.path.join(_STATIC_DIR, "index.html"), encoding="utf-8") as _f:
    _INDEX_HTML = _f.read()


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


@app.get("/", response_class=HTMLResponse)
async def index():
    return _INDEX_HTML


@app.get("/health")
async def health():
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{settings.ollama_base_url}/api/tags", timeout=3.0)
        ollama_ok = r.status_code == 200
    except Exception:
        ollama_ok = False

    status = "ok" if ollama_ok else "degraded"
    return {"status": status, "ollama": ollama_ok}
