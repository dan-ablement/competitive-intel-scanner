"""LLM Analyzer service — evaluates feed items using Claude API and creates analysis cards."""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any

import anthropic
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.analysis_card import AnalysisCard, AnalysisCardCompetitor
from backend.models.augment_profile import AugmentProfile
from backend.models.competitor import Competitor
from backend.models.feed_item import FeedItem
from backend.models.feed import RSSFeed
from backend.utils import utc_isoformat
from backend.prompts.feed_evaluation import build_feed_evaluation_prompt

logger = logging.getLogger(__name__)

# Valid enum values for validation
VALID_EVENT_TYPES = {
    "new_feature", "product_announcement", "partnership", "acquisition",
    "acquired", "funding", "pricing_change", "leadership_change", "expansion", "other",
}
VALID_PRIORITIES = {"red", "yellow", "green"}

MODEL = "claude-sonnet-4-20250514"
MAX_RETRIES = 3
BASE_DELAY = 2  # seconds


class LLMAnalyzer:
    """Evaluates feed items via Claude and creates analysis cards."""

    def __init__(self) -> None:
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_unprocessed_items(
        self,
        db: Session,
        check_run_id: uuid.UUID | None = None,
    ) -> int:
        """Process all unprocessed feed items. Returns number of cards created."""
        items = (
            db.query(FeedItem)
            .filter(FeedItem.is_processed == False)  # noqa: E712
            .all()
        )
        if not items:
            logger.info("No unprocessed feed items found.")
            return 0

        # Load context once
        augment_profile_text = self._load_augment_profile(db)
        competitor_profiles_text = self._load_competitor_profiles(db)

        cards_created = 0
        for item in items:
            try:
                created = self._process_single_item(
                    db, item, augment_profile_text, competitor_profiles_text, check_run_id,
                )
                if created:
                    cards_created += 1
            except Exception:
                logger.exception("Failed to process feed item %s", item.id)
                # Mark as processed to avoid infinite retry loops; mark irrelevant
                item.is_processed = True
                item.is_relevant = False
                item.irrelevance_reason = "Processing error"
                db.commit()

        return cards_created

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_augment_profile(self, db: Session) -> str:
        profile = db.query(AugmentProfile).first()
        if not profile:
            return "No Augment profile configured yet."
        return (
            f"Company: {profile.company_description}\n"
            f"Differentiators: {profile.key_differentiators}\n"
            f"Target Customers: {profile.target_customer_segments}\n"
            f"Capabilities: {profile.product_capabilities}\n"
            f"Strategic Priorities: {profile.strategic_priorities}\n"
            f"Pricing: {profile.pricing}"
        )

    def _load_competitor_profiles(self, db: Session) -> str:
        competitors = (
            db.query(Competitor)
            .filter(Competitor.is_active == True)  # noqa: E712
            .order_by(Competitor.name)
            .all()
        )
        if not competitors:
            return "No competitors configured yet."
        parts: list[str] = []
        for c in competitors:
            parts.append(
                f"--- {c.name} ---\n"
                f"Description: {c.description}\n"
                f"Key Products: {c.key_products}\n"
                f"Target Customers: {c.target_customers}\n"
                f"Strengths: {c.known_strengths}\n"
                f"Weaknesses: {c.known_weaknesses}\n"
                f"Overlap with Augment: {c.augment_overlap}\n"
                f"Pricing: {c.pricing}"
            )
        return "\n\n".join(parts)

    def _process_single_item(
        self,
        db: Session,
        item: FeedItem,
        augment_profile_text: str,
        competitor_profiles_text: str,
        check_run_id: uuid.UUID | None,
    ) -> bool:
        """Process one feed item. Returns True if an analysis card was created."""
        feed: RSSFeed = item.feed
        feed_name = feed.name if feed else "Unknown Feed"

        # Twitter items have no title — synthesise one from the tweet text
        is_twitter = feed and feed.feed_type == "twitter"
        if is_twitter:
            item_title = f"Tweet by @{item.author}" if item.author else "Tweet"
            item_content = item.raw_content[:8000]
            # Append engagement metrics when available
            if item.raw_metadata and item.raw_metadata.get("public_metrics"):
                metrics = item.raw_metadata["public_metrics"]
                item_content += (
                    f"\n\n[Engagement: {metrics.get('like_count', 0)} likes, "
                    f"{metrics.get('retweet_count', 0)} retweets, "
                    f"{metrics.get('reply_count', 0)} replies]"
                )
        else:
            item_title = item.title
            item_content = item.raw_content[:8000]  # Truncate very long content

        prompt = build_feed_evaluation_prompt(
            augment_profile=augment_profile_text,
            competitor_list_with_profiles=competitor_profiles_text,
            feed_name=feed_name,
            item_title=item_title,
            item_content=item_content,
            item_url=item.url,
            item_published_at=utc_isoformat(item.published_at) or "Unknown",
        )

        raw_response = self._call_claude(prompt)
        parsed = self._parse_json_response(raw_response)

        if parsed is None:
            logger.warning("Could not parse LLM response for item %s", item.id)
            item.is_processed = True
            item.is_relevant = False
            item.irrelevance_reason = "LLM response parse error"
            db.commit()
            return False

        is_relevant = parsed.get("is_relevant", False)

        # Mark feed item
        item.is_processed = True
        item.is_relevant = is_relevant
        if not is_relevant:
            item.irrelevance_reason = parsed.get("irrelevance_reason", "Not relevant")
            db.commit()
            return False

        # Create analysis card
        card = self._create_analysis_card(db, item, parsed, check_run_id)

        # Link competitors
        self._link_competitors(db, card, parsed)

        # Handle suggested new competitor
        self._handle_suggested_competitor(db, card, parsed)

        db.commit()
        logger.info("Created analysis card %s for feed item %s", card.id, item.id)
        return True

    def _call_claude(self, prompt: str) -> str:
        """Call Claude API with exponential backoff retry."""
        for attempt in range(MAX_RETRIES):
            try:
                message = self.client.messages.create(
                    model=MODEL,
                    max_tokens=2048,
                    messages=[{"role": "user", "content": prompt}],
                )
                response_text = message.content[0].text
                logger.info(
                    "Claude API call: input_tokens=%d, output_tokens=%d",
                    message.usage.input_tokens,
                    message.usage.output_tokens,
                )
                return response_text
            except anthropic.RateLimitError:
                if attempt < MAX_RETRIES - 1:
                    delay = BASE_DELAY * (2 ** attempt)
                    logger.warning("Rate limited, retrying in %ds (attempt %d/%d)", delay, attempt + 1, MAX_RETRIES)
                    time.sleep(delay)
                else:
                    raise
            except anthropic.APIError as e:
                if attempt < MAX_RETRIES - 1:
                    delay = BASE_DELAY * (2 ** attempt)
                    logger.warning("API error: %s, retrying in %ds (attempt %d/%d)", e, delay, attempt + 1, MAX_RETRIES)
                    time.sleep(delay)
                else:
                    raise
        # Should not reach here, but just in case
        raise RuntimeError("Exhausted retries calling Claude API")


    def _parse_json_response(self, raw: str) -> dict[str, Any] | None:
        """Parse JSON from Claude's response, handling possible markdown fences."""
        text = raw.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            # Remove opening fence (possibly ```json)
            first_newline = text.index("\n") if "\n" in text else len(text)
            text = text[first_newline + 1:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON from LLM response: %s", text[:500])
            return None

    def _create_analysis_card(
        self,
        db: Session,
        item: FeedItem,
        parsed: dict[str, Any],
        check_run_id: uuid.UUID | None,
    ) -> AnalysisCard:
        """Create an AnalysisCard from parsed LLM output."""
        event_type = parsed.get("event_type", "other")
        if event_type not in VALID_EVENT_TYPES:
            event_type = "other"

        priority = parsed.get("priority", "green")
        if priority not in VALID_PRIORITIES:
            priority = "green"

        card = AnalysisCard(
            id=uuid.uuid4(),
            feed_item_id=item.id,
            event_type=event_type,
            priority=priority,
            title=parsed.get("title", item.title),
            summary=parsed.get("summary", ""),
            impact_assessment=parsed.get("impact_assessment", ""),
            suggested_counter_moves=parsed.get("suggested_counter_moves", ""),
            raw_llm_output=parsed,
            status="draft",
            check_run_id=check_run_id,
        )
        db.add(card)
        db.flush()  # Get the card ID for linking
        return card

    def _link_competitors(
        self,
        db: Session,
        card: AnalysisCard,
        parsed: dict[str, Any],
    ) -> None:
        """Link analysis card to mentioned competitors by name matching."""
        competitor_names = parsed.get("competitor_names", [])
        if not competitor_names:
            return

        for name in competitor_names:
            # Case-insensitive match
            competitor = (
                db.query(Competitor)
                .filter(
                    Competitor.is_active == True,  # noqa: E712
                    Competitor.name.ilike(name),
                )
                .first()
            )
            if competitor:
                link = AnalysisCardCompetitor(
                    analysis_card_id=card.id,
                    competitor_id=competitor.id,
                )
                db.add(link)

    def _handle_suggested_competitor(
        self,
        db: Session,
        card: AnalysisCard,
        parsed: dict[str, Any],
    ) -> None:
        """If the LLM suggests a new competitor, create it with is_suggested=True."""
        suggestion = parsed.get("suggested_new_competitor")
        if not suggestion or not isinstance(suggestion, dict):
            return

        name = suggestion.get("name", "").strip()
        if not name:
            return

        # Check if competitor already exists (case-insensitive)
        existing = (
            db.query(Competitor)
            .filter(Competitor.name.ilike(name))
            .first()
        )
        if existing:
            # Link existing competitor to card if active
            if existing.is_active:
                link = AnalysisCardCompetitor(
                    analysis_card_id=card.id,
                    competitor_id=existing.id,
                )
                db.add(link)
            return

        # Create new suggested competitor
        new_competitor = Competitor(
            id=uuid.uuid4(),
            name=name,
            description=suggestion.get("description", ""),
            key_products="",
            target_customers="",
            known_strengths="",
            known_weaknesses="",
            augment_overlap="",
            pricing="",
            is_active=True,
            is_suggested=True,
            suggested_reason=suggestion.get("reason", "Suggested by LLM analysis"),
        )
        db.add(new_competitor)
        db.flush()

        # Link to card
        link = AnalysisCardCompetitor(
            analysis_card_id=card.id,
            competitor_id=new_competitor.id,
        )
        db.add(link)
        logger.info("Created suggested competitor: %s", name)