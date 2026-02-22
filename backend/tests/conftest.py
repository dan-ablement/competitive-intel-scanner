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


@pytest.fixture
def make_competitor():
    """Factory to create mock Competitor objects."""
    def _make(name="Test Competitor", is_active=True, content_types=None):
        return SimpleNamespace(
            id=uuid.uuid4(),
            name=name,
            is_active=is_active,
            content_types=content_types or [],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    return _make


@pytest.fixture
def make_user():
    """Factory to create mock User objects."""
    def _make(role="viewer", email="test@example.com", name="Test User"):
        return SimpleNamespace(
            id=uuid.uuid4(),
            email=email,
            name=name,
            role=role,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    return _make


@pytest.fixture
def make_content_output():
    """Factory to create mock ContentOutput objects."""
    def _make(
        competitor=None,
        content='{"key": "val"}',
        status="draft",
        template_id=None,
        content_type="Competitive Battle Card",
        title="Test Output",
        **kwargs,
    ):
        comp = competitor or SimpleNamespace(id=uuid.uuid4(), name="Test Competitor")
        defaults = dict(
            id=uuid.uuid4(),
            competitor_id=comp.id,
            competitor=comp,
            content_type=content_type,
            title=title,
            content=content,
            sections=None,
            source_card_ids=None,
            version=1,
            status=status,
            template_id=template_id or uuid.uuid4(),
            google_doc_id=None,
            google_doc_url=None,
            approver=None,
            approved_by=None,
            approved_at=None,
            published_at=None,
            error_message=None,
            raw_llm_output=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)
    return _make


@pytest.fixture
def make_content_template():
    """Factory to create mock ContentTemplate objects."""
    def _make(
        content_type="Competitive Battle Card",
        name="Battle Card Template",
        description="A template for battle cards",
        sections=None,
        doc_name_pattern=None,
        is_active=True,
    ):
        return SimpleNamespace(
            id=uuid.uuid4(),
            content_type=content_type,
            name=name,
            description=description,
            sections=sections,
            doc_name_pattern=doc_name_pattern,
            is_active=is_active,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    return _make

