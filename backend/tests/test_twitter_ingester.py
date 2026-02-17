"""Tests for backend.services.twitter_ingester."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backend.services.twitter_ingester import TwitterIngester, TwitterAPIError


# ---------------------------------------------------------------------------
# _build_exclude_param
# ---------------------------------------------------------------------------

class TestBuildExcludeParam:
    """Unit tests for TwitterIngester._build_exclude_param."""

    def setup_method(self):
        self.ingester = TwitterIngester(bearer_token="test-token")

    def test_both_excluded(self, make_twitter_config):
        """Default: both retweets and replies excluded."""
        config = make_twitter_config(include_retweets=False, include_replies=False)
        assert self.ingester._build_exclude_param(config) == "retweets,replies"

    def test_include_retweets_only(self, make_twitter_config):
        """include_retweets=True → only replies excluded."""
        config = make_twitter_config(include_retweets=True, include_replies=False)
        assert self.ingester._build_exclude_param(config) == "replies"

    def test_include_replies_only(self, make_twitter_config):
        """include_replies=True → only retweets excluded."""
        config = make_twitter_config(include_retweets=False, include_replies=True)
        assert self.ingester._build_exclude_param(config) == "retweets"

    def test_both_included(self, make_twitter_config):
        """Both included → None (omit param)."""
        config = make_twitter_config(include_retweets=True, include_replies=True)
        assert self.ingester._build_exclude_param(config) is None


# ---------------------------------------------------------------------------
# resolve_username (validate_username equivalent)
# ---------------------------------------------------------------------------

class TestResolveUsername:
    """Tests for TwitterIngester.resolve_username."""

    @pytest.mark.asyncio
    async def test_valid_username(self, mock_settings):
        """Successful username resolution returns user data."""
        ingester = TwitterIngester(bearer_token="test-token")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": "12345",
                "name": "Test User",
                "username": "testuser",
                "public_metrics": {"followers_count": 100, "tweet_count": 50},
            }
        }

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        ingester._client = mock_client

        result = await ingester.resolve_username("testuser")
        assert result["id"] == "12345"
        assert result["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_invalid_username_not_found(self, mock_settings):
        """Username not found raises TwitterAPIError with 404."""
        ingester = TwitterIngester(bearer_token="test-token")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "errors": [{"detail": "Could not find user with username: [baduser]."}]
        }

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        ingester._client = mock_client

        with pytest.raises(TwitterAPIError) as exc_info:
            await ingester.resolve_username("baduser")
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_api_error_401(self, mock_settings):
        """401 response raises TwitterAPIError."""
        ingester = TwitterIngester(bearer_token="bad-token")

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.headers = {}

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        ingester._client = mock_client

        with pytest.raises(TwitterAPIError) as exc_info:
            await ingester.resolve_username("testuser")
        assert exc_info.value.status_code == 401
        assert "Bearer token" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_strips_at_sign(self, mock_settings):
        """Leading @ is stripped from username."""
        ingester = TwitterIngester(bearer_token="test-token")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"id": "99", "username": "someone", "name": "Someone"}
        }

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        ingester._client = mock_client

        await ingester.resolve_username("@someone")
        call_args = mock_client.get.call_args
        assert "/users/by/username/someone" in call_args[0][0]


# ---------------------------------------------------------------------------
# tweet_to_feed_item
# ---------------------------------------------------------------------------

class TestTweetToFeedItem:
    """Tests for TwitterIngester.tweet_to_feed_item."""

    def test_basic_conversion(self):
        ingester = TwitterIngester(bearer_token="test-token")
        feed_id = uuid.uuid4()
        tweet = {
            "id": "111222333",
            "text": "Hello world",
            "created_at": "2025-01-15T10:30:00Z",
            "public_metrics": {"like_count": 5},
            "lang": "en",
        }
        result = ingester.tweet_to_feed_item(tweet, feed_id, "testuser")

        assert result["guid"] == "111222333"
        assert result["url"] == "https://x.com/testuser/status/111222333"
        assert result["author"] == "testuser"
        assert result["raw_content"] == "Hello world"
        assert result["feed_id"] == feed_id
        assert result["is_processed"] is False

