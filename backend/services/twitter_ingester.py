"""Twitter/X API ingestion service using X API v2 with Bearer token auth."""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING, Optional

import httpx

from backend.config import settings

if TYPE_CHECKING:
    from backend.models.twitter_source_config import TwitterSourceConfig

logger = logging.getLogger(__name__)

BASE_URL = "https://api.x.com/2"
TWEET_FIELDS = "created_at,public_metrics,entities,referenced_tweets,conversation_id,lang"
EXPANSIONS = "referenced_tweets.id"
MAX_RESULTS_PER_PAGE = 100


class TwitterAPIError(Exception):
    """Raised when the X API returns an error response."""

    def __init__(self, status_code: int, message: str, reset_time: Optional[int] = None):
        self.status_code = status_code
        self.message = message
        self.reset_time = reset_time
        super().__init__(f"Twitter API error {status_code}: {message}")


class TwitterIngester:
    """Fetches tweets from the X API v2 for competitor monitoring."""

    def __init__(self, bearer_token: Optional[str] = None):
        self.bearer_token = bearer_token or settings.X_BEARER_TOKEN
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.bearer_token}"}

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=BASE_URL,
                headers=self._headers,
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Raise TwitterAPIError with status-specific messages."""
        status = response.status_code
        if status < 400:
            return

        messages = {
            401: "Invalid or expired Bearer token",
            402: "X API credits exhausted",
            403: "Account is protected or suspended",
            404: "User or resource not found",
        }

        if status == 429:
            reset_header = response.headers.get("x-rate-limit-reset")
            reset_time = int(reset_header) if reset_header else None
            raise TwitterAPIError(
                status_code=429,
                message=f"Rate limited. Reset at: {reset_time}",
                reset_time=reset_time,
            )

        if status >= 500:
            raise TwitterAPIError(status, f"X API server error: {response.text}")

        message = messages.get(status, f"Unexpected error: {response.text}")
        raise TwitterAPIError(status, message)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def resolve_username(self, username: str) -> dict:
        """Resolve a Twitter username to user data.

        GET /2/users/by/username/{username}
        Returns dict with id, name, username, public_metrics, profile_image_url, description.
        """
        clean = username.lstrip("@").strip()
        client = await self._get_client()
        response = await client.get(
            f"/users/by/username/{clean}",
            params={"user.fields": "public_metrics,profile_image_url,description"},
        )
        self._handle_error_response(response)

        data = response.json()
        if "data" not in data:
            errors = data.get("errors", [{}])
            detail = errors[0].get("detail", "User not found") if errors else "User not found"
            raise TwitterAPIError(404, detail)

        return data["data"]

    async def fetch_tweets_backfill(
        self,
        x_user_id: str,
        config: TwitterSourceConfig,
        backfill_days: int = 30,
    ) -> list[dict]:
        """Fetch historical tweets using start_time for backfill.

        GET /2/users/{user_id}/tweets with start_time param.
        Handles pagination via next_token.
        """
        start_time = (datetime.now(timezone.utc) - timedelta(days=backfill_days)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        params: dict = {
            "tweet.fields": TWEET_FIELDS,
            "expansions": EXPANSIONS,
            "max_results": MAX_RESULTS_PER_PAGE,
            "start_time": start_time,
        }
        exclude = self._build_exclude_param(config)
        if exclude:
            params["exclude"] = exclude

        return await self._paginate_tweets(x_user_id, params)

    async def fetch_tweets_incremental(
        self,
        x_user_id: str,
        config: TwitterSourceConfig,
    ) -> list[dict]:
        """Fetch new tweets since last_tweet_id using since_id.

        GET /2/users/{user_id}/tweets with since_id param.
        Handles pagination via next_token.
        """
        params: dict = {
            "tweet.fields": TWEET_FIELDS,
            "expansions": EXPANSIONS,
            "max_results": MAX_RESULTS_PER_PAGE,
        }
        if config.last_tweet_id:
            params["since_id"] = config.last_tweet_id

        exclude = self._build_exclude_param(config)
        if exclude:
            params["exclude"] = exclude

        return await self._paginate_tweets(x_user_id, params)

    def tweet_to_feed_item(
        self,
        tweet: dict,
        feed_id,
        x_username: str,
    ) -> dict:
        """Transform a tweet API response into a FeedItem-compatible dict.

        Returns a plain dict (not an ORM object) for the route/service layer
        to create FeedItem instances from.
        """
        tweet_id = tweet["id"]
        text = tweet.get("text", "")
        created_at_str = tweet.get("created_at")

        if created_at_str:
            published_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        else:
            published_at = datetime.now(timezone.utc)

        raw_metadata = {
            "public_metrics": tweet.get("public_metrics"),
            "entities": tweet.get("entities"),
            "referenced_tweets": tweet.get("referenced_tweets"),
            "conversation_id": tweet.get("conversation_id"),
            "lang": tweet.get("lang"),
        }

        return {
            "guid": tweet_id,
            "title": None,
            "url": f"https://x.com/{x_username}/status/{tweet_id}",
            "author": x_username,
            "published_at": published_at,
            "raw_content": text,
            "raw_metadata": raw_metadata,
            "feed_id": feed_id,
            "is_processed": False,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_exclude_param(self, config: TwitterSourceConfig) -> str | None:
        """Build the exclude parameter from config toggles.

        Default: both retweets and replies excluded.
        - include_retweets=True, include_replies=True → None (omit param)
        - include_retweets=True, include_replies=False → "replies"
        - include_retweets=False, include_replies=True → "retweets"
        - include_retweets=False, include_replies=False → "retweets,replies"
        """
        parts: list[str] = []
        if not getattr(config, "include_retweets", False):
            parts.append("retweets")
        if not getattr(config, "include_replies", False):
            parts.append("replies")
        return ",".join(parts) if parts else None

    async def _paginate_tweets(self, x_user_id: str, params: dict) -> list[dict]:
        """Fetch tweets with automatic pagination via next_token."""
        client = await self._get_client()
        all_tweets: list[dict] = []

        while True:
            response = await client.get(f"/users/{x_user_id}/tweets", params=params)
            self._handle_error_response(response)

            body = response.json()
            tweets = body.get("data", [])
            all_tweets.extend(tweets)

            meta = body.get("meta", {})
            next_token = meta.get("next_token")
            if not next_token:
                break
            params["pagination_token"] = next_token

        logger.info("Fetched %d tweets for user %s", len(all_tweets), x_user_id)
        return all_tweets

