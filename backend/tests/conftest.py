"""Shared test fixtures for backend tests."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, AsyncMock

import pytest


# ---------------------------------------------------------------------------
# Mock Settings
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_settings(monkeypatch):
    """Patch backend.config.settings with test values."""
    fake = SimpleNamespace(
        DATABASE_URL="sqlite:///:memory:",
        ANTHROPIC_API_KEY="test-key",
        GOOGLE_CLIENT_ID="test-client-id",
        GOOGLE_CLIENT_SECRET="test-client-secret",
        ALLOWED_DOMAIN="example.com",
        SESSION_SECRET="test-secret",
        X_BEARER_TOKEN="test-bearer-token",
    )
    monkeypatch.setattr("backend.config.settings", fake)
    return fake


# ---------------------------------------------------------------------------
# Mock DB Session
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db():
    """Return a MagicMock that behaves like a SQLAlchemy Session."""
    db = MagicMock()
    db.query.return_value = db
    db.filter.return_value = db
    db.options.return_value = db
    db.order_by.return_value = db
    db.all.return_value = []
    db.first.return_value = None
    db.commit.return_value = None
    db.refresh.return_value = None
    db.add.return_value = None
    db.close.return_value = None
    return db


# ---------------------------------------------------------------------------
# Mock httpx AsyncClient
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_httpx_client():
    """Return an AsyncMock that behaves like httpx.AsyncClient."""
    client = AsyncMock()
    client.is_closed = False
    client.aclose = AsyncMock()
    return client


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def make_feed():
    """Factory to create mock RSSFeed objects."""
    def _make(
        feed_type="rss",
        name="Test Feed",
        url="https://example.com/feed.xml",
        competitor=None,
        twitter_config=None,
        is_active=True,
    ):
        feed = SimpleNamespace(
            id=uuid.uuid4(),
            name=name,
            url=url,
            competitor_id=competitor.id if competitor else None,
            competitor=competitor,
            feed_type=feed_type,
            css_selector=None,
            is_active=is_active,
            last_checked_at=None,
            last_successful_at=None,
            error_count=0,
            last_error=None,
            created_by=uuid.uuid4(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            twitter_config=twitter_config,
        )
        return feed
    return _make


@pytest.fixture
def make_twitter_config():
    """Factory to create mock TwitterSourceConfig objects."""
    def _make(
        x_username="testuser",
        x_user_id="12345",
        include_retweets=False,
        include_replies=False,
        backfill_completed=False,
        last_tweet_id=None,
        initial_backfill_days=30,
    ):
        return SimpleNamespace(
            id=uuid.uuid4(),
            feed_id=uuid.uuid4(),
            x_username=x_username,
            x_user_id=x_user_id,
            last_tweet_id=last_tweet_id,
            initial_backfill_days=initial_backfill_days,
            backfill_completed=backfill_completed,
            include_retweets=include_retweets,
            include_replies=include_replies,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    return _make

