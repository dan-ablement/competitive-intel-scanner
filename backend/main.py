import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

app.mount("/", StaticFiles(directory="./static", html=True), name="static")

