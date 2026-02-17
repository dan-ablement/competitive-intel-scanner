"""Tests for backend models — TwitterSourceConfig and RSSFeed."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace


# ---------------------------------------------------------------------------
# TwitterSourceConfig (via fixture — no DB needed)
# ---------------------------------------------------------------------------

class TestTwitterSourceConfig:
    """Test TwitterSourceConfig model creation via the make_twitter_config fixture."""

    def test_default_values(self, make_twitter_config):
        """Default config has expected defaults."""
        config = make_twitter_config()

        assert config.x_username == "testuser"
        assert config.x_user_id == "12345"
        assert config.include_retweets is False
        assert config.include_replies is False
        assert config.backfill_completed is False
        assert config.last_tweet_id is None
        assert config.initial_backfill_days == 30

    def test_custom_values(self, make_twitter_config):
        """Config with custom values stores them correctly."""
        config = make_twitter_config(
            x_username="anthropic",
            x_user_id="99999",
            include_retweets=True,
            include_replies=True,
            backfill_completed=True,
            last_tweet_id="555666",
            initial_backfill_days=7,
        )

        assert config.x_username == "anthropic"
        assert config.x_user_id == "99999"
        assert config.include_retweets is True
        assert config.include_replies is True
        assert config.backfill_completed is True
        assert config.last_tweet_id == "555666"
        assert config.initial_backfill_days == 7

    def test_has_uuid_id(self, make_twitter_config):
        """Config has a UUID id and feed_id."""
        config = make_twitter_config()
        assert isinstance(config.id, uuid.UUID)
        assert isinstance(config.feed_id, uuid.UUID)

    def test_has_timestamps(self, make_twitter_config):
        """Config has created_at and updated_at timestamps."""
        config = make_twitter_config()
        assert isinstance(config.created_at, datetime)
        assert isinstance(config.updated_at, datetime)


# ---------------------------------------------------------------------------
# RSSFeed (via fixture — no DB needed)
# ---------------------------------------------------------------------------

class TestRSSFeedModel:
    """Test RSSFeed model creation via the make_feed fixture."""

    def test_rss_feed_type(self, make_feed):
        """Default feed has feed_type='rss'."""
        feed = make_feed(feed_type="rss")
        assert feed.feed_type == "rss"

    def test_web_scrape_feed_type(self, make_feed):
        """Feed can have feed_type='web_scrape'."""
        feed = make_feed(feed_type="web_scrape")
        assert feed.feed_type == "web_scrape"

    def test_twitter_feed_type(self, make_feed):
        """Feed can have feed_type='twitter'."""
        feed = make_feed(feed_type="twitter")
        assert feed.feed_type == "twitter"

    def test_feed_defaults(self, make_feed):
        """Feed has expected default values."""
        feed = make_feed()
        assert feed.is_active is True
        assert feed.error_count == 0
        assert feed.last_error is None
        assert feed.last_checked_at is None
        assert feed.css_selector is None

    def test_feed_with_competitor(self, make_feed):
        """Feed can be associated with a competitor."""
        comp = SimpleNamespace(id=uuid.uuid4(), name="Rival Inc")
        feed = make_feed(competitor=comp)
        assert feed.competitor_id == comp.id
        assert feed.competitor.name == "Rival Inc"

    def test_feed_with_twitter_config(self, make_feed, make_twitter_config):
        """Feed can have a twitter_config attached."""
        tc = make_twitter_config(x_username="testaccount")
        feed = make_feed(feed_type="twitter", twitter_config=tc)
        assert feed.twitter_config is not None
        assert feed.twitter_config.x_username == "testaccount"

