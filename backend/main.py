from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routes import auth, feeds, competitors, augment_profile, cards, briefings, suggestions, system

app = FastAPI(title="Competitive Intelligence Scanner")

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

