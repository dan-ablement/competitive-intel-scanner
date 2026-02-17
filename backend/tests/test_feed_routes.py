"""Tests for backend.routes.feeds._feed_to_response helper."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from backend.routes.feeds import _feed_to_response


# ---------------------------------------------------------------------------
# RSS feed serialization
# ---------------------------------------------------------------------------

class TestFeedToResponseRSS:
    """_feed_to_response for feed_type='rss'."""

    def test_rss_basic_fields(self, make_feed):
        """RSS feed serializes core fields correctly."""
        feed = make_feed(feed_type="rss", name="My RSS", url="https://example.com/rss")
        result = _feed_to_response(feed)

        assert result["name"] == "My RSS"
        assert result["url"] == "https://example.com/rss"
        assert result["feed_type"] == "rss"
        assert result["is_active"] is True
        assert result["error_count"] == 0
        assert result["id"] == str(feed.id)
        assert result["created_by"] == str(feed.created_by)

    def test_rss_no_twitter_fields(self, make_feed):
        """RSS feed has None for all twitter-specific top-level fields."""
        feed = make_feed(feed_type="rss")
        result = _feed_to_response(feed)

        assert result["twitter_config"] is None
        assert result["x_username"] is None
        assert result["x_user_id"] is None
        assert result["backfill_completed"] is None
        assert result["include_retweets"] is None
        assert result["include_replies"] is None

    def test_rss_competitor_name(self, make_feed):
        """RSS feed includes competitor name when competitor is set."""
        comp = SimpleNamespace(id=uuid.uuid4(), name="Acme Corp")
        feed = make_feed(feed_type="rss", competitor=comp)
        result = _feed_to_response(feed)

        assert result["competitor_name"] == "Acme Corp"
        assert result["competitor_id"] == str(comp.id)


# ---------------------------------------------------------------------------
# Web scrape feed serialization
# ---------------------------------------------------------------------------

class TestFeedToResponseWebScrape:
    """_feed_to_response for feed_type='web_scrape'."""

    def test_web_scrape_basic(self, make_feed):
        """Web scrape feed serializes with correct feed_type."""
        feed = make_feed(
            feed_type="web_scrape",
            name="Blog Scraper",
            url="https://example.com/blog",
        )
        feed.css_selector = "article a"
        result = _feed_to_response(feed)

        assert result["feed_type"] == "web_scrape"
        assert result["css_selector"] == "article a"
        assert result["name"] == "Blog Scraper"

    def test_web_scrape_no_twitter_fields(self, make_feed):
        """Web scrape feed has None for twitter fields."""
        feed = make_feed(feed_type="web_scrape")
        result = _feed_to_response(feed)

        assert result["twitter_config"] is None
        assert result["x_username"] is None


# ---------------------------------------------------------------------------
# Twitter feed serialization
# ---------------------------------------------------------------------------

class TestFeedToResponseTwitter:
    """_feed_to_response for feed_type='twitter'."""

    def test_twitter_includes_config(self, make_feed, make_twitter_config):
        """Twitter feed includes nested twitter_config dict."""
        tc = make_twitter_config(
            x_username="openai",
            x_user_id="999",
            include_retweets=True,
            include_replies=False,
            backfill_completed=True,
            last_tweet_id="111222",
        )
        feed = make_feed(feed_type="twitter", name="OpenAI", twitter_config=tc)
        result = _feed_to_response(feed)

        assert result["feed_type"] == "twitter"
        assert result["twitter_config"] is not None
        assert result["twitter_config"]["x_username"] == "openai"
        assert result["twitter_config"]["x_user_id"] == "999"
        assert result["twitter_config"]["include_retweets"] is True
        assert result["twitter_config"]["include_replies"] is False
        assert result["twitter_config"]["backfill_completed"] is True
        assert result["twitter_config"]["last_tweet_id"] == "111222"

    def test_twitter_top_level_fields(self, make_feed, make_twitter_config):
        """Twitter fields are flattened to top level for frontend convenience."""
        tc = make_twitter_config(
            x_username="anthropic",
            x_user_id="888",
            backfill_completed=False,
            include_retweets=False,
            include_replies=True,
        )
        feed = make_feed(feed_type="twitter", twitter_config=tc)
        result = _feed_to_response(feed)

        assert result["x_username"] == "anthropic"
        assert result["x_user_id"] == "888"
        assert result["backfill_completed"] is False
        assert result["include_retweets"] is False
        assert result["include_replies"] is True

    def test_twitter_without_config_fallback(self, make_feed):
        """Twitter feed without twitter_config still serializes (graceful)."""
        feed = make_feed(feed_type="twitter", twitter_config=None)
        result = _feed_to_response(feed)

        assert result["feed_type"] == "twitter"
        assert result["twitter_config"] is None
        assert result["x_username"] is None

