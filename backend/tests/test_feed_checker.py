"""Tests for backend.services.feed_checker._process_feed routing."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from backend.services.feed_checker import FeedChecker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_checker(mock_db):
    """Create a FeedChecker with mocked dependencies."""
    with patch("backend.services.feed_checker.LLMAnalyzer"), \
         patch("backend.services.feed_checker.WebScraper") as MockScraper:
        checker = FeedChecker(mock_db)
        # Replace web_scraper with a mock that has process_feed
        checker.web_scraper = MockScraper.return_value
        return checker


# ---------------------------------------------------------------------------
# _process_feed routing
# ---------------------------------------------------------------------------

class TestProcessFeedRouting:
    """Verify _process_feed dispatches to the correct handler by feed_type."""

    def test_rss_feed_uses_feedparser(self, mock_db, make_feed):
        """feed_type='rss' goes through the feedparser path."""
        checker = _make_checker(mock_db)
        feed = make_feed(feed_type="rss", url="https://example.com/feed.xml")

        with patch("backend.services.feed_checker.feedparser") as mock_fp:
            mock_parsed = MagicMock()
            mock_parsed.bozo = False
            mock_parsed.entries = []
            mock_fp.parse.return_value = mock_parsed

            result = checker._process_feed(feed)

            mock_fp.parse.assert_called_once_with(feed.url)
            assert result == 0

    def test_web_scrape_delegates_to_web_scraper(self, mock_db, make_feed):
        """feed_type='web_scrape' delegates to self.web_scraper.process_feed."""
        checker = _make_checker(mock_db)
        feed = make_feed(feed_type="web_scrape", url="https://example.com/blog")

        checker.web_scraper.process_feed.return_value = 3

        result = checker._process_feed(feed)

        checker.web_scraper.process_feed.assert_called_once_with(feed, mock_db)
        assert result == 3

    def test_twitter_delegates_to_process_twitter_feed(self, mock_db, make_feed, make_twitter_config):
        """feed_type='twitter' delegates to _process_twitter_feed."""
        checker = _make_checker(mock_db)
        tc = make_twitter_config(x_username="test", x_user_id="123")
        feed = make_feed(feed_type="twitter", twitter_config=tc)

        with patch.object(checker, "_process_twitter_feed", return_value=5) as mock_twitter:
            result = checker._process_feed(feed)

            mock_twitter.assert_called_once_with(feed)
            assert result == 5


# ---------------------------------------------------------------------------
# RSS feed processing details
# ---------------------------------------------------------------------------

class TestProcessRSSFeed:
    """Test RSS-specific processing in _process_feed."""

    def test_rss_raises_on_bozo_no_entries(self, mock_db, make_feed):
        """RSS feed with bozo error and no entries raises RuntimeError."""
        checker = _make_checker(mock_db)
        feed = make_feed(feed_type="rss", url="https://bad.example.com/feed")

        with patch("backend.services.feed_checker.feedparser") as mock_fp:
            mock_parsed = MagicMock()
            mock_parsed.bozo = True
            mock_parsed.entries = []
            mock_parsed.bozo_exception = Exception("XML syntax error")
            mock_fp.parse.return_value = mock_parsed

            with pytest.raises(RuntimeError, match="Failed to parse feed"):
                checker._process_feed(feed)

    def test_rss_dedup_skips_existing_items(self, mock_db, make_feed):
        """RSS items with existing GUIDs are skipped (dedup)."""
        checker = _make_checker(mock_db)
        feed = make_feed(feed_type="rss", url="https://example.com/feed.xml")

        entry = SimpleNamespace(
            id="existing-guid-123",
            title="Old Article",
            link="https://example.com/old",
            author=None,
            published_parsed=None,
            updated_parsed=None,
            content=None,
            summary="Old content",
        )

        with patch("backend.services.feed_checker.feedparser") as mock_fp:
            mock_parsed = MagicMock()
            mock_parsed.bozo = False
            mock_parsed.entries = [entry]
            mock_fp.parse.return_value = mock_parsed

            # Simulate existing item found in DB
            mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()

            result = checker._process_feed(feed)
            assert result == 0  # No new items because dedup

