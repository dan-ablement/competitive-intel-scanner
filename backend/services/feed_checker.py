from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import feedparser
from sqlalchemy.orm import Session

from backend.models.check_run import CheckRun
from backend.models.feed import RSSFeed
from backend.models.feed_item import FeedItem
from backend.services.llm_analyzer import LLMAnalyzer
from backend.services.twitter_ingester import TwitterIngester
from backend.services.web_scraper import WebScraper

logger = logging.getLogger(__name__)


class FeedChecker:
    """Fetches RSS feeds, parses items, and creates check_run records."""

    def __init__(self, db: Session):
        self.db = db
        self.analyzer = LLMAnalyzer()
        self.web_scraper = WebScraper()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> CheckRun:
        """Execute a full feed-check run.

        1. Create a check_run with status='running'
        2. Iterate all active feeds
        3. For each feed: fetch, parse, dedup, insert new items
        4. Update check_run with counts and status
        """
        check_run = self._create_check_run()
        feeds_checked = 0
        new_items_total = 0
        errors: list[str] = []

        active_feeds = (
            self.db.query(RSSFeed)
            .filter(RSSFeed.is_active == True)  # noqa: E712
            .all()
        )

        for feed in active_feeds:
            try:
                new_items = self._process_feed(feed)
                feeds_checked += 1
                new_items_total += new_items
            except Exception as exc:
                feeds_checked += 1
                error_msg = f"Feed '{feed.name}' ({feed.id}): {exc}"
                logger.error(error_msg)
                errors.append(error_msg)
                self._record_feed_error(feed, str(exc))

        # Run LLM analysis on unprocessed items
        cards_generated = 0
        if new_items_total > 0:
            try:
                cards_generated = self.analyzer.process_unprocessed_items(
                    self.db, check_run_id=check_run.id,
                )
            except Exception as exc:
                logger.exception("LLM analysis phase failed")
                errors.append(f"LLM analysis: {exc}")

        # Finalize check_run
        check_run.feeds_checked = feeds_checked
        check_run.new_items_found = new_items_total
        check_run.cards_generated = cards_generated
        check_run.completed_at = datetime.now(timezone.utc)

        if errors:
            check_run.error_log = "\n".join(errors)
            # Only mark as failed if ALL feeds errored
            if feeds_checked > 0 and len(errors) == len(active_feeds):
                check_run.status = "failed"
            else:
                check_run.status = "completed"
        else:
            check_run.status = "completed"

        self.db.commit()
        self.db.refresh(check_run)
        return check_run

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _create_check_run(self) -> CheckRun:
        """Create a new check_run record with status='running'."""
        now = datetime.now(timezone.utc)
        check_run = CheckRun(
            id=uuid.uuid4(),
            scheduled_time=now,
            started_at=now,
            status="running",
            feeds_checked=0,
            new_items_found=0,
            cards_generated=0,
        )
        self.db.add(check_run)
        self.db.commit()
        self.db.refresh(check_run)
        return check_run

    def _process_feed(self, feed: RSSFeed) -> int:
        """Fetch and parse a single feed. Returns count of new items inserted."""
        # Dispatch based on feed type
        if feed.feed_type == "web_scrape":
            return self.web_scraper.process_feed(feed, self.db)

        if feed.feed_type == "twitter":
            return self._process_twitter_feed(feed)

        # Default: RSS feed processing
        now = datetime.now(timezone.utc)
        feed.last_checked_at = now

        parsed = feedparser.parse(feed.url)

        # Check for hard parse failures
        if parsed.bozo and not parsed.entries:
            error_msg = str(parsed.bozo_exception) if parsed.bozo_exception else "Unknown parse error"
            raise RuntimeError(f"Failed to parse feed: {error_msg}")

        new_count = 0
        for entry in parsed.entries:
            guid = self._extract_guid(entry)
            if not guid:
                continue

            # Dedup: skip if (feed_id, guid) already exists
            existing = (
                self.db.query(FeedItem.id)
                .filter(FeedItem.feed_id == feed.id, FeedItem.guid == guid)
                .first()
            )
            if existing:
                continue

            item = self._entry_to_feed_item(feed.id, entry, guid)
            if item:
                self.db.add(item)
                new_count += 1

        # Success: reset error state, update timestamps
        feed.last_successful_at = now
        feed.error_count = 0
        feed.last_error = None
        self.db.commit()

        return new_count

    def _record_feed_error(self, feed: RSSFeed, error: str) -> None:
        """Increment error_count and set last_error on a feed."""
        feed.error_count = (feed.error_count or 0) + 1
        feed.last_error = error
        feed.last_checked_at = datetime.now(timezone.utc)
        self.db.commit()

    def _extract_guid(self, entry) -> Optional[str]:
        """Extract a unique identifier from a feed entry."""
        # Prefer explicit id/guid, fall back to link
        guid = getattr(entry, "id", None) or getattr(entry, "guid", None)
        if guid:
            return str(guid)
        link = getattr(entry, "link", None)
        if link:
            return str(link)
        return None

    def _entry_to_feed_item(self, feed_id: uuid.UUID, entry, guid: str) -> Optional[FeedItem]:
        """Convert a feedparser entry to a FeedItem model instance."""
        title = getattr(entry, "title", "") or "Untitled"
        link = getattr(entry, "link", "") or ""

        # Author
        author = getattr(entry, "author", None)

        # Published date
        published_at = self._parse_published(entry)

        # Content: prefer content field, fall back to summary/description
        raw_content = self._extract_content(entry)

        return FeedItem(
            id=uuid.uuid4(),
            feed_id=feed_id,
            guid=guid,
            title=title[:500] if title else "Untitled",
            url=link[:2000] if link else "",
            author=author[:500] if author else None,
            published_at=published_at,
            raw_content=raw_content or "",
            is_processed=False,
        )

    def _parse_published(self, entry) -> datetime:
        """Parse the published date from a feed entry."""
        # feedparser normalizes dates into published_parsed (time.struct_time)
        parsed_time = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
        if parsed_time:
            try:
                from calendar import timegm
                return datetime.fromtimestamp(timegm(parsed_time), tz=timezone.utc)
            except (ValueError, OverflowError, OSError):
                pass
        return datetime.now(timezone.utc)

    def _extract_content(self, entry) -> str:
        """Extract the best available content from a feed entry."""
        # feedparser stores content as a list of dicts
        content_list = getattr(entry, "content", None)
        if content_list and isinstance(content_list, list):
            for c in content_list:
                value = c.get("value", "")
                if value:
                    return value

        # Fall back to summary
        summary = getattr(entry, "summary", None) or getattr(entry, "description", None)
        if summary:
            return summary

        return ""


    # ------------------------------------------------------------------
    # Twitter helpers
    # ------------------------------------------------------------------

    def _process_twitter_feed(self, feed: RSSFeed) -> int:
        """Fetch tweets for a Twitter feed and insert new items. Returns count of new items."""
        config = feed.twitter_config
        if not config:
            raise RuntimeError("Twitter feed is missing its TwitterSourceConfig")

        now = datetime.now(timezone.utc)
        feed.last_checked_at = now

        ingester = TwitterIngester()

        async def _fetch() -> list[dict]:
            try:
                if config.backfill_completed and config.last_tweet_id:
                    return await ingester.fetch_tweets_incremental(
                        config.x_user_id, config,
                    )
                else:
                    return await ingester.fetch_tweets_backfill(
                        config.x_user_id, config,
                        backfill_days=config.initial_backfill_days,
                    )
            finally:
                await ingester.close()

        # Run async fetch in sync context
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    tweets = pool.submit(asyncio.run, _fetch()).result()
            else:
                tweets = loop.run_until_complete(_fetch())
        except RuntimeError:
            tweets = asyncio.run(_fetch())

        new_count = 0
        latest_tweet_id: str | None = None

        for tweet in tweets:
            item_dict = ingester.tweet_to_feed_item(
                tweet, feed_id=feed.id, x_username=config.x_username,
            )
            guid = item_dict["guid"]

            # Dedup: skip if (feed_id, guid) already exists
            existing = (
                self.db.query(FeedItem.id)
                .filter(FeedItem.feed_id == feed.id, FeedItem.guid == guid)
                .first()
            )
            if existing:
                continue

            item = FeedItem(
                id=uuid.uuid4(),
                feed_id=item_dict["feed_id"],
                guid=guid,
                title=item_dict["title"],
                url=item_dict["url"],
                author=item_dict["author"],
                published_at=item_dict["published_at"],
                raw_content=item_dict["raw_content"],
                raw_metadata=item_dict["raw_metadata"],
                is_processed=False,
            )
            self.db.add(item)
            new_count += 1

            # Track the highest tweet ID for since_id on next run
            if latest_tweet_id is None or guid > latest_tweet_id:
                latest_tweet_id = guid

        # Update config state
        if latest_tweet_id:
            config.last_tweet_id = latest_tweet_id
        if not config.backfill_completed:
            config.backfill_completed = True

        # Success: reset error state, update timestamps
        feed.last_successful_at = now
        feed.error_count = 0
        feed.last_error = None
        self.db.commit()

        return new_count
