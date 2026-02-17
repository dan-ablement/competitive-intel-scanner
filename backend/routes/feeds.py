from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional

import feedparser
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session, joinedload

from backend.database import get_db, SessionLocal
from backend.models.feed import RSSFeed
from backend.utils import utc_isoformat
from backend.models.feed_item import FeedItem
from backend.models.competitor import Competitor
from backend.models.twitter_source_config import TwitterSourceConfig
from backend.models.user import User
from backend.routes.auth import get_current_user
from backend.services.twitter_ingester import TwitterIngester, TwitterAPIError

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class FeedCreate(BaseModel):
    name: str
    url: Optional[str] = None
    competitor_id: Optional[str] = None
    feed_type: Optional[str] = "rss"
    css_selector: Optional[str] = None
    # Twitter-specific fields
    x_username: Optional[str] = None
    include_retweets: Optional[bool] = False
    include_replies: Optional[bool] = False
    initial_backfill_days: Optional[int] = 30


class FeedUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    competitor_id: Optional[str] = None
    is_active: Optional[bool] = None
    feed_type: Optional[str] = None
    css_selector: Optional[str] = None


class TwitterConfigResponse(BaseModel):
    x_username: str
    x_user_id: Optional[str] = None
    last_tweet_id: Optional[str] = None
    initial_backfill_days: int = 30
    backfill_completed: bool = False
    include_retweets: bool = False
    include_replies: bool = False


class FeedResponse(BaseModel):
    id: str
    name: str
    url: Optional[str] = None
    competitor_id: Optional[str]
    competitor_name: Optional[str] = None
    feed_type: str = "rss"
    css_selector: Optional[str] = None
    is_active: bool
    last_checked_at: Optional[str]
    last_successful_at: Optional[str]
    error_count: int
    last_error: Optional[str]
    created_by: str
    created_at: str
    updated_at: str
    twitter_config: Optional[TwitterConfigResponse] = None
    x_username: Optional[str] = None
    x_user_id: Optional[str] = None
    backfill_completed: Optional[bool] = None
    include_retweets: Optional[bool] = None
    include_replies: Optional[bool] = None


class TestFeedResponse(BaseModel):
    success: bool
    message: str
    item_count: int = 0


class ValidateTwitterRequest(BaseModel):
    username: str


class ValidateTwitterResponse(BaseModel):
    valid: bool
    username: Optional[str] = None
    user_id: Optional[str] = None
    name: Optional[str] = None
    followers_count: Optional[int] = None
    tweet_count: Optional[int] = None
    description: Optional[str] = None
    profile_image_url: Optional[str] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _feed_to_response(feed: RSSFeed) -> dict:
    """Serialize an RSSFeed model to a dict matching FeedResponse."""
    competitor_name = feed.competitor.name if feed.competitor else None

    twitter_config_data = None
    if feed.feed_type == "twitter" and feed.twitter_config:
        tc = feed.twitter_config
        twitter_config_data = {
            "x_username": tc.x_username,
            "x_user_id": tc.x_user_id,
            "last_tweet_id": tc.last_tweet_id,
            "initial_backfill_days": tc.initial_backfill_days,
            "backfill_completed": tc.backfill_completed,
            "include_retweets": tc.include_retweets,
            "include_replies": tc.include_replies,
        }

    return {
        "id": str(feed.id),
        "name": feed.name,
        "url": feed.url,
        "competitor_id": str(feed.competitor_id) if feed.competitor_id else None,
        "competitor_name": competitor_name,
        "feed_type": feed.feed_type or "rss",
        "css_selector": feed.css_selector,
        "is_active": feed.is_active,
        "last_checked_at": utc_isoformat(feed.last_checked_at),
        "last_successful_at": utc_isoformat(feed.last_successful_at),
        "error_count": feed.error_count,
        "last_error": feed.last_error,
        "created_by": str(feed.created_by),
        "created_at": utc_isoformat(feed.created_at),
        "updated_at": utc_isoformat(feed.updated_at),
        "twitter_config": twitter_config_data,
        "x_username": twitter_config_data["x_username"] if twitter_config_data else None,
        "x_user_id": twitter_config_data["x_user_id"] if twitter_config_data else None,
        "backfill_completed": twitter_config_data["backfill_completed"] if twitter_config_data else None,
        "include_retweets": twitter_config_data["include_retweets"] if twitter_config_data else None,
        "include_replies": twitter_config_data["include_replies"] if twitter_config_data else None,
    }



def _twitter_backfill_task(feed_id_str: str) -> None:
    """Background task: run initial tweet backfill for a newly created Twitter feed."""
    from backend.services.feed_checker import FeedChecker

    db = SessionLocal()
    try:
        feed = (
            db.query(RSSFeed)
            .options(joinedload(RSSFeed.twitter_config))
            .filter(RSSFeed.id == uuid.UUID(feed_id_str))
            .first()
        )
        if not feed or not feed.twitter_config:
            logger.warning("Backfill task: feed %s not found or missing twitter config", feed_id_str)
            return

        checker = FeedChecker(db)
        new_items = checker._process_twitter_feed(feed)
        logger.info("Twitter backfill complete for feed %s: %d new items", feed_id_str, new_items)
    except Exception:
        logger.exception("Twitter backfill failed for feed %s", feed_id_str)
    finally:
        db.close()




# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("", response_model=list[FeedResponse])
def list_feeds(db: Session = Depends(get_db)):
    """List all feeds, ordered by name."""
    feeds = (
        db.query(RSSFeed)
        .options(joinedload(RSSFeed.competitor), joinedload(RSSFeed.twitter_config))
        .order_by(RSSFeed.name)
        .all()
    )
    return [_feed_to_response(f) for f in feeds]


@router.post("", response_model=FeedResponse, status_code=201)
def create_feed(
    body: FeedCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new feed (RSS, web_scrape, or twitter)."""
    is_twitter = (body.feed_type == "twitter")

    # Validate: twitter feeds require x_username, non-twitter require url
    if is_twitter:
        if not body.x_username:
            raise HTTPException(status_code=422, detail="x_username is required for Twitter feeds.")
    else:
        if not body.url:
            raise HTTPException(status_code=422, detail="url is required for RSS/web_scrape feeds.")

    # Check for duplicate URL (only for non-twitter feeds that have a URL)
    if body.url:
        existing = db.query(RSSFeed).filter(RSSFeed.url == body.url).first()
        if existing:
            raise HTTPException(status_code=409, detail="A feed with this URL already exists.")

    # Check for duplicate Twitter username
    if is_twitter:
        existing_twitter = (
            db.query(TwitterSourceConfig)
            .filter(TwitterSourceConfig.x_username == body.x_username.lstrip("@").strip())
            .first()
        )
        if existing_twitter:
            raise HTTPException(status_code=409, detail="A feed for this Twitter/X account already exists.")

    # Validate competitor_id if provided
    competitor_id_val = None
    if body.competitor_id:
        comp = db.query(Competitor).filter(Competitor.id == uuid.UUID(body.competitor_id)).first()
        if not comp:
            raise HTTPException(status_code=404, detail="Competitor not found.")
        competitor_id_val = comp.id

    feed_id = uuid.uuid4()
    feed = RSSFeed(
        id=feed_id,
        name=body.name,
        url=body.url,
        competitor_id=competitor_id_val,
        feed_type=body.feed_type or "rss",
        css_selector=body.css_selector,
        is_active=True,
        error_count=0,
        created_by=current_user.id,
    )
    db.add(feed)

    # Create TwitterSourceConfig for twitter feeds
    x_user_id: str | None = None
    if is_twitter:
        clean_username = body.x_username.lstrip("@").strip()

        # Resolve username to get x_user_id synchronously
        ingester = TwitterIngester()
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    user_data = pool.submit(
                        asyncio.run,
                        ingester.resolve_username(clean_username),
                    ).result()
            else:
                user_data = loop.run_until_complete(
                    ingester.resolve_username(clean_username)
                )
        except RuntimeError:
            user_data = asyncio.run(ingester.resolve_username(clean_username))

        x_user_id = user_data["id"]

        twitter_config = TwitterSourceConfig(
            id=uuid.uuid4(),
            feed_id=feed_id,
            x_username=clean_username,
            x_user_id=x_user_id,
            initial_backfill_days=body.initial_backfill_days or 30,
            include_retweets=body.include_retweets or False,
            include_replies=body.include_replies or False,
        )
        db.add(twitter_config)

    db.commit()
    db.refresh(feed)

    # Kick off backfill in background for twitter feeds
    if is_twitter and x_user_id:
        background_tasks.add_task(_twitter_backfill_task, str(feed_id))

    # Eagerly load relationships for response
    feed = (
        db.query(RSSFeed)
        .options(joinedload(RSSFeed.competitor), joinedload(RSSFeed.twitter_config))
        .filter(RSSFeed.id == feed.id)
        .first()
    )
    return _feed_to_response(feed)



@router.post("/validate-twitter", response_model=ValidateTwitterResponse)
def validate_twitter(body: ValidateTwitterRequest):
    """Validate a Twitter/X username by resolving it via the X API.

    Returns user info if valid, or an error message if not found / API error.
    """
    ingester = TwitterIngester()

    async def _resolve():
        try:
            return await ingester.resolve_username(body.username)
        finally:
            await ingester.close()

    try:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    user_data = pool.submit(asyncio.run, _resolve()).result()
            else:
                user_data = loop.run_until_complete(_resolve())
        except RuntimeError:
            user_data = asyncio.run(_resolve())

        metrics = user_data.get("public_metrics", {})
        return {
            "valid": True,
            "username": user_data.get("username"),
            "user_id": user_data.get("id"),
            "name": user_data.get("name"),
            "followers_count": metrics.get("followers_count"),
            "tweet_count": metrics.get("tweet_count"),
            "description": user_data.get("description"),
            "profile_image_url": user_data.get("profile_image_url"),
        }
    except TwitterAPIError as exc:
        return {
            "valid": False,
            "error": exc.message,
        }
    except Exception as exc:
        return {
            "valid": False,
            "error": f"Failed to validate username: {str(exc)}",
        }



@router.put("/{feed_id}", response_model=FeedResponse)
def update_feed(feed_id: str, body: FeedUpdate, db: Session = Depends(get_db)):
    """Update an existing feed."""
    feed = (
        db.query(RSSFeed)
        .options(joinedload(RSSFeed.competitor), joinedload(RSSFeed.twitter_config))
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
    if body.feed_type is not None:
        feed.feed_type = body.feed_type
    if body.css_selector is not None:
        feed.css_selector = body.css_selector if body.css_selector != "" else None

    db.commit()
    db.refresh(feed)

    # Re-load with relationships
    feed = (
        db.query(RSSFeed)
        .options(joinedload(RSSFeed.competitor), joinedload(RSSFeed.twitter_config))
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

    return _test_feed_url(feed.url, feed_type=feed.feed_type, css_selector=feed.css_selector)


@router.post("/test-url", response_model=TestFeedResponse)
def test_feed_url(body: dict, db: Session = Depends(get_db)):
    """Test-fetch an arbitrary URL (before creating a feed)."""
    url = body.get("url", "")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required.")
    feed_type = body.get("feed_type", "rss")
    css_selector = body.get("css_selector")
    return _test_feed_url(url, feed_type=feed_type, css_selector=css_selector)


def _test_feed_url(url: str, feed_type: str = "rss", css_selector: str | None = None) -> dict:
    """Attempt to parse a feed URL and return results."""
    if feed_type == "web_scrape":
        return _test_web_scrape_url(url, css_selector)

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


def _test_web_scrape_url(url: str, css_selector: str | None = None) -> dict:
    """Test a web scrape URL by crawling only the listing page and counting article links.

    This is lightweight — it does NOT crawl individual articles, so it completes quickly.
    """
    import asyncio
    from backend.services.web_scraper import WebScraper

    try:
        scraper = WebScraper()
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result = pool.submit(
                        asyncio.run,
                        scraper.test_listing(url, css_selector),
                    ).result()
            else:
                result = loop.run_until_complete(
                    scraper.test_listing(url, css_selector)
                )
        except RuntimeError:
            result = asyncio.run(scraper.test_listing(url, css_selector))

        if not result.get("valid"):
            return {
                "success": False,
                "message": "Failed to crawl listing page. Check the URL and try again.",
                "item_count": 0,
            }

        count = result.get("article_count", 0)
        if count == 0:
            return {
                "success": True,
                "message": "Page crawled successfully but no article links were found. "
                           "Try providing a CSS selector to help identify article links.",
                "item_count": 0,
            }

        return {
            "success": True,
            "message": f"Found {count} article link(s) on listing page.",
            "item_count": count,
        }
    except Exception as exc:
        return {"success": False, "message": f"Error crawling page: {str(exc)}", "item_count": 0}
