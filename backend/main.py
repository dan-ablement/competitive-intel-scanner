import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from backend.config import settings
from backend.routes import auth, feeds, competitors, augment_profile, cards, briefings, suggestions, system

logger = logging.getLogger(__name__)

app = FastAPI(title="Competitive Intelligence Scanner")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# Session middleware — must be added before CORS so sessions work on all routes
app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(feeds.router, prefix="/api/feeds", tags=["feeds"])
app.include_router(competitors.router, prefix="/api/competitors", tags=["competitors"])
app.include_router(augment_profile.router, prefix="/api/augment-profile", tags=["augment-profile"])
app.include_router(cards.router, prefix="/api/cards", tags=["cards"])
app.include_router(briefings.router, prefix="/api/briefings", tags=["briefings"])
app.include_router(suggestions.router, prefix="/api/suggestions", tags=["suggestions"])
app.include_router(system.router, prefix="/api", tags=["system"])

# Static file serving with SPA fallback
static_dir = Path("./static")
if static_dir.is_dir():
    # Mount static assets (JS, CSS, images) at /assets
    assets_dir = static_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # Serve other static files (favicon, etc.)
    @app.get("/vite.svg")
    async def vite_svg():
        return FileResponse(static_dir / "vite.svg")

    # SPA catch-all: serve index.html for all non-API routes
    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return JSONResponse(status_code=404, content={"detail": "Not Found"})

