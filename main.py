"""
Kodeye — Intelligent Code Analysis and Documentation Generation System
M.Tech Dissertation | BITS Pilani WILP | Shyam Kishore V (2024TM93034)
Supervisor: Mr. Malaya Rout | Exafluence, Bangalore

Run:
    poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.routers import analyze, settings as settings_router

app = FastAPI(
    title="Kodeye",
    description="Intelligent Code Analysis and Documentation Generation System",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)
app.include_router(settings_router.router)

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index = STATIC_DIR / "index.html"
    if index.exists():
        return HTMLResponse(content=index.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>index.html not found in /static</h1>", status_code=404)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
