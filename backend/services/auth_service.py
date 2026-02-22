"""Google SSO authentication service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from authlib.integrations.starlette_client import OAuth
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.user import User
from backend.utils import utc_isoformat

# Admin emails that get the 'admin' role on first login
ADMIN_EMAILS = {
    "diacono@augmentcode.com",
    "mollie@augmentcode.com",
    "mattarnold@augmentcode.com",
}

# Configure OAuth
oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile https://www.googleapis.com/auth/drive.file https://www.googleapis.com/auth/documents",
        "access_type": "offline",
        "prompt": "consent",
    },
)


def validate_domain(email: str) -> bool:
    """Check that the email belongs to the allowed domain."""
    domain = email.split("@")[-1].lower()
    return domain == settings.ALLOWED_DOMAIN.lower()


def get_or_create_user(db: Session, google_id: str, email: str, name: str) -> User:
    """Find existing user by google_id or create a new one.

    On first login, admin emails get role='admin', others get role='viewer'.
    """
    user = db.query(User).filter(User.google_id == google_id).first()
    if user is not None:
        # Update name/email in case they changed in Google
        user.name = name
        user.email = email
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        return user

    # Also check by email in case user was pre-created
    user = db.query(User).filter(User.email == email).first()
    if user is not None:
        user.google_id = google_id
        user.name = name
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        return user

    # Create new user
    role = "admin" if email.lower() in ADMIN_EMAILS else "viewer"
    user = User(
        id=uuid.uuid4(),
        email=email,
        name=name,
        role=role,
        google_id=google_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def user_to_dict(user: User) -> dict:
    """Serialize a User model to a dict for API responses."""
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "google_id": user.google_id,
        "created_at": utc_isoformat(user.created_at),
        "updated_at": utc_isoformat(user.updated_at),
    }
