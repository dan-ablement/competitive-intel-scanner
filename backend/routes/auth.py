"""Auth routes: Google SSO login, callback, logout, current user."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.services.auth_service import (
    oauth,
    validate_domain,
    get_or_create_user,
    user_to_dict,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency: extract current user from session or raise 401."""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        # Session references a deleted user — clear it
        request.session.clear()
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.get("/google")
async def google_login(request: Request):
    """Initiate Google SSO — redirect user to Google consent screen."""
    redirect_uri = request.url_for("google_callback")
    # Ensure HTTPS in production (behind a proxy)
    redirect_uri = str(redirect_uri)
    if request.headers.get("x-forwarded-proto") == "https":
        redirect_uri = redirect_uri.replace("http://", "https://", 1)
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Google SSO callback — validate domain, create/get user, set session."""
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    if user_info is None:
        raise HTTPException(status_code=400, detail="Failed to get user info from Google")

    email = user_info.get("email", "")
    if not validate_domain(email):
        raise HTTPException(
            status_code=403,
            detail=f"Only @{__import__('backend.config', fromlist=['settings']).settings.ALLOWED_DOMAIN} emails are allowed",
        )

    google_id = user_info["sub"]
    name = user_info.get("name", email.split("@")[0])

    user = get_or_create_user(db, google_id=google_id, email=email, name=name)

    # Store OAuth tokens for Google Docs integration
    refresh_token = token.get("refresh_token")
    access_token = token.get("access_token")
    logger.info(
        "OAuth callback: refresh_token=%s, access_token=%s",
        "present" if refresh_token else "MISSING",
        "present" if access_token else "MISSING",
    )
    if refresh_token:
        user.google_refresh_token = refresh_token
    if access_token:
        user.google_access_token = access_token
    if refresh_token or access_token:
        db.commit()

    # Store user ID in session
    request.session["user_id"] = str(user.id)

    return RedirectResponse(url="/", status_code=302)


@router.post("/logout")
async def logout(request: Request):
    """Clear the session."""
    request.session.clear()
    return {"ok": True}


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return user_to_dict(current_user)
