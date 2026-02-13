from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

import feedparser
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session, joinedload

from backend.database import get_db
from backend.models.feed import RSSFeed
from backend.models.competitor import Competitor
from backend.models.user import User
from backend.routes.auth import get_current_user

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class FeedCreate(BaseModel):
    name: str
    url: str
    competitor_id: Optional[str] = None


class FeedUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    competitor_id: Optional[str] = None
    is_active: Optional[bool] = None


class FeedResponse(BaseModel):
    id: str
    name: str
    url: str
    competitor_id: Optional[str]
    competitor_name: Optional[str] = None
    is_active: bool
    last_checked_at: Optional[str]
    last_successful_at: Optional[str]
    error_count: int
    last_error: Optional[str]
    created_by: str
    created_at: str
    updated_at: str


class TestFeedResponse(BaseModel):
    success: bool
    message: str
    item_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _feed_to_response(feed: RSSFeed) -> dict:
    """Serialize an RSSFeed model to a dict matching FeedResponse."""
    competitor_name = feed.competitor.name if feed.competitor else None
    return {
        "id": str(feed.id),
        "name": feed.name,
        "url": feed.url,
        "competitor_id": str(feed.competitor_id) if feed.competitor_id else None,
        "competitor_name": competitor_name,
        "is_active": feed.is_active,
        "last_checked_at": feed.last_checked_at.isoformat() if feed.last_checked_at else None,
        "last_successful_at": feed.last_successful_at.isoformat() if feed.last_successful_at else None,
        "error_count": feed.error_count,
        "last_error": feed.last_error,
        "created_by": str(feed.created_by),
        "created_at": feed.created_at.isoformat() if feed.created_at else None,
        "updated_at": feed.updated_at.isoformat() if feed.updated_at else None,
    }



# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("", response_model=list[FeedResponse])
def list_feeds(db: Session = Depends(get_db)):
    """List all RSS feeds, ordered by name."""
    feeds = (
        db.query(RSSFeed)
        .options(joinedload(RSSFeed.competitor))
        .order_by(RSSFeed.name)
        .all()
    )
    return [_feed_to_response(f) for f in feeds]


@router.post("", response_model=FeedResponse, status_code=201)
def create_feed(body: FeedCreate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new RSS feed."""
    # Check for duplicate URL
    existing = db.query(RSSFeed).filter(RSSFeed.url == body.url).first()
    if existing:
        raise HTTPException(status_code=409, detail="A feed with this URL already exists.")

    # Validate competitor_id if provided
    competitor_id_val = None
    if body.competitor_id:
        comp = db.query(Competitor).filter(Competitor.id == uuid.UUID(body.competitor_id)).first()
        if not comp:
            raise HTTPException(status_code=404, detail="Competitor not found.")
        competitor_id_val = comp.id

    feed = RSSFeed(
        id=uuid.uuid4(),
        name=body.name,
        url=body.url,
        competitor_id=competitor_id_val,
        is_active=True,
        error_count=0,
        created_by=current_user.id,
    )
    db.add(feed)
    db.commit()
    db.refresh(feed)

    # Eagerly load competitor for response
    feed = (
        db.query(RSSFeed)
        .options(joinedload(RSSFeed.competitor))
        .filter(RSSFeed.id == feed.id)
        .first()
    )
    return _feed_to_response(feed)


@router.put("/{feed_id}", response_model=FeedResponse)
def update_feed(feed_id: str, body: FeedUpdate, db: Session = Depends(get_db)):
    """Update an existing RSS feed."""
    feed = (
        db.query(RSSFeed)
        .options(joinedload(RSSFeed.competitor))
        .filter(RSSFeed.id == uuid.UUID(feed_id))
        .first()
    )
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found.")

    if body.name is not None:
        feed.name = body.name
    if body.url is not None:
        # Check for duplicate URL (excluding self)
        dup = db.query(RSSFeed).filter(RSSFeed.url == body.url, RSSFeed.id != feed.id).first()
        if dup:
            raise HTTPException(status_code=409, detail="A feed with this URL already exists.")
        feed.url = body.url
    if body.competitor_id is not None:
        if body.competitor_id == "":
            feed.competitor_id = None
        else:
            comp = db.query(Competitor).filter(Competitor.id == uuid.UUID(body.competitor_id)).first()
            if not comp:
                raise HTTPException(status_code=404, detail="Competitor not found.")
            feed.competitor_id = comp.id
    if body.is_active is not None:
        feed.is_active = body.is_active

    db.commit()
    db.refresh(feed)

    # Re-load with competitor
    feed = (
        db.query(RSSFeed)
        .options(joinedload(RSSFeed.competitor))
        .filter(RSSFeed.id == feed.id)
        .first()
    )
    return _feed_to_response(feed)



@router.delete("/{feed_id}", status_code=204)
def delete_feed(feed_id: str, db: Session = Depends(get_db)):
    """Soft-delete a feed by setting is_active=False."""
    feed = db.query(RSSFeed).filter(RSSFeed.id == uuid.UUID(feed_id)).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found.")

    feed.is_active = False
    db.commit()
    return None


@router.post("/{feed_id}/test", response_model=TestFeedResponse)
def test_feed(feed_id: str, db: Session = Depends(get_db)):
    """Test-fetch an existing feed's URL and report success/failure with item count."""
    feed = db.query(RSSFeed).filter(RSSFeed.id == uuid.UUID(feed_id)).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found.")

    return _test_feed_url(feed.url)


@router.post("/test-url", response_model=TestFeedResponse)
def test_feed_url(body: dict, db: Session = Depends(get_db)):
    """Test-fetch an arbitrary URL (before creating a feed)."""
    url = body.get("url", "")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required.")
    return _test_feed_url(url)


def _test_feed_url(url: str) -> dict:
    """Attempt to parse an RSS feed URL and return results."""
    try:
        parsed = feedparser.parse(url)

        # feedparser doesn't raise on bad URLs; check for bozo errors
        if parsed.bozo and not parsed.entries:
            error_msg = str(parsed.bozo_exception) if parsed.bozo_exception else "Unknown parse error"
            return {"success": False, "message": f"Failed to parse feed: {error_msg}", "item_count": 0}

        if not parsed.entries and not parsed.feed.get("title"):
            return {"success": False, "message": "URL does not appear to be a valid RSS/Atom feed.", "item_count": 0}

        feed_title = parsed.feed.get("title", "Unknown")
        item_count = len(parsed.entries)
        return {
            "success": True,
            "message": f"Successfully parsed feed \"{feed_title}\" — {item_count} item(s) found.",
            "item_count": item_count,
        }
    except Exception as exc:
        return {"success": False, "message": f"Error fetching feed: {str(exc)}", "item_count": 0}
