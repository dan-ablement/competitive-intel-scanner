"""Profile Reviewer service — reviews competitor and Augment profiles against recent cards."""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import anthropic
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.analysis_card import AnalysisCard, AnalysisCardCompetitor
from backend.models.augment_profile import AugmentProfile
from backend.models.competitor import Competitor
from backend.models.profile_suggestion import ProfileUpdateSuggestion
from backend.prompts.profile_review import build_profile_review_messages, PROFILE_REVIEW_SYSTEM
from backend.utils import utc_isoformat

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-20250514"
MAX_RETRIES = 3
BASE_DELAY = 2  # seconds
REVIEW_WINDOW_DAYS = 7  # Look back 7 days for approved cards


class ProfileReviewer:
    """Reviews profiles against recent approved analysis cards and generates suggestions."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def run(self) -> dict[str, int]:
        """Run a full profile review cycle. Returns counts of suggestions created."""
        competitor_suggestions = self._review_competitors()
        augment_suggestions = self._review_augment_profile()
        total = competitor_suggestions + augment_suggestions
        logger.info(
            "Profile review complete: %d competitor suggestions, %d augment suggestions",
            competitor_suggestions, augment_suggestions,
        )
        return {
            "competitor_suggestions": competitor_suggestions,
            "augment_suggestions": augment_suggestions,
            "total": total,
        }

    # ------------------------------------------------------------------
    # Competitor review
    # ------------------------------------------------------------------

    def _review_competitors(self) -> int:
        """Review all active competitors. Returns number of suggestions created."""
        competitors = (
            self.db.query(Competitor)
            .filter(Competitor.is_active == True)  # noqa: E712
            .order_by(Competitor.name)
            .all()
        )
        suggestions_created = 0
        for competitor in competitors:
            try:
                count = self._review_single_competitor(competitor)
                suggestions_created += count
            except Exception:
                logger.exception("Failed to review competitor %s", competitor.name)
        return suggestions_created

    def _review_single_competitor(self, competitor: Competitor) -> int:
        """Review one competitor profile. Returns number of suggestions created."""
        # Get recent approved cards linked to this competitor
        cutoff = datetime.now(timezone.utc) - timedelta(days=REVIEW_WINDOW_DAYS)
        cards = (
            self.db.query(AnalysisCard)
            .join(AnalysisCardCompetitor)
            .filter(
                AnalysisCardCompetitor.competitor_id == competitor.id,
                AnalysisCard.status == "approved",
                AnalysisCard.created_at >= cutoff,
            )
            .order_by(AnalysisCard.created_at.desc())
            .limit(20)
            .all()
        )
        if not cards:
            logger.debug("No recent approved cards for competitor %s, skipping", competitor.name)
            return 0

        profile_text = self._format_competitor_profile(competitor)
        cards_text = self._format_cards(cards)

        messages = build_profile_review_messages(
            target_name=competitor.name,
            target_profile=profile_text,
            relevant_cards=cards_text,
        )

        raw = self._call_claude(messages)
        parsed = self._parse_json_response(raw)
        if parsed is None:
            return 0

        card_ids = [str(c.id) for c in cards]
        return self._create_suggestions(
            parsed, "competitor", competitor.id, card_ids,
        )

    # ------------------------------------------------------------------
    # Augment profile review
    # ------------------------------------------------------------------

    def _review_augment_profile(self) -> int:
        """Review the Augment profile. Returns number of suggestions created."""
        profile = self.db.query(AugmentProfile).first()
        if not profile:
            logger.info("No Augment profile configured, skipping review")
            return 0

        cutoff = datetime.now(timezone.utc) - timedelta(days=REVIEW_WINDOW_DAYS)
        cards = (
            self.db.query(AnalysisCard)
            .filter(
                AnalysisCard.status == "approved",
                AnalysisCard.created_at >= cutoff,
            )
            .order_by(AnalysisCard.created_at.desc())
            .limit(30)
            .all()
        )
        if not cards:
            logger.debug("No recent approved cards, skipping Augment profile review")
            return 0

        profile_text = self._format_augment_profile(profile)
        cards_text = self._format_cards(cards)

        messages = build_profile_review_messages(
            target_name="Augment Code",
            target_profile=profile_text,
            relevant_cards=cards_text,
        )

        raw = self._call_claude(messages)
        parsed = self._parse_json_response(raw)
        if parsed is None:
            return 0

        card_ids = [str(c.id) for c in cards]
        return self._create_suggestions(parsed, "augment", None, card_ids)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _format_competitor_profile(self, c: Competitor) -> str:
        return (
            f"Name: {c.name}\n"
            f"Description: {c.description}\n"
            f"Key Products: {c.key_products}\n"
            f"Target Customers: {c.target_customers}\n"
            f"Known Strengths: {c.known_strengths}\n"
            f"Known Weaknesses: {c.known_weaknesses}\n"
            f"Overlap with Augment: {c.augment_overlap}\n"
            f"Pricing: {c.pricing}"
        )

    def _format_augment_profile(self, p: AugmentProfile) -> str:
        return (
            f"Company Description: {p.company_description}\n"
            f"Key Differentiators: {p.key_differentiators}\n"
            f"Target Customer Segments: {p.target_customer_segments}\n"
            f"Product Capabilities: {p.product_capabilities}\n"
            f"Strategic Priorities: {p.strategic_priorities}\n"
            f"Pricing: {p.pricing}"
        )


    def _format_cards(self, cards: list[AnalysisCard]) -> str:
        parts: list[str] = []
        for card in cards:
            parts.append(
                f"--- Card {card.id} ---\n"
                f"Title: {card.title}\n"
                f"Event Type: {card.event_type}\n"
                f"Priority: {card.priority}\n"
                f"Summary: {card.summary}\n"
                f"Impact: {card.impact_assessment}\n"
                f"Created: {utc_isoformat(card.created_at) or 'Unknown'}"
            )
        return "\n\n".join(parts) if parts else "No cards available."

    def _create_suggestions(
        self,
        parsed: dict[str, Any],
        target_type: str,
        competitor_id: uuid.UUID | None,
        available_card_ids: list[str],
    ) -> int:
        """Create ProfileUpdateSuggestion records from parsed LLM output."""
        suggestions = parsed.get("suggestions", [])
        if not isinstance(suggestions, list):
            return 0

        count = 0
        for s in suggestions:
            if not isinstance(s, dict):
                continue
            field = s.get("field", "").strip()
            if not field:
                continue

            # Filter source_card_ids to only include cards we actually sent
            source_ids = s.get("source_card_ids", [])
            if isinstance(source_ids, list):
                source_ids = [sid for sid in source_ids if sid in available_card_ids]
            else:
                source_ids = []

            suggestion = ProfileUpdateSuggestion(
                id=uuid.uuid4(),
                target_type=target_type,
                competitor_id=competitor_id,
                field=field,
                current_value=s.get("current_value", ""),
                suggested_value=s.get("suggested_value", ""),
                reason=s.get("reason", ""),
                source_card_ids=source_ids,
                status="pending",
            )
            self.db.add(suggestion)
            count += 1

        if count > 0:
            self.db.commit()
        return count

    def _call_claude(self, messages: list[dict[str, str]]) -> str:
        """Call Claude API with exponential backoff retry."""
        for attempt in range(MAX_RETRIES):
            try:
                message = self.client.messages.create(
                    model=MODEL,
                    max_tokens=4096,
                    system=PROFILE_REVIEW_SYSTEM,
                    messages=messages,
                )
                response_text = message.content[0].text
                logger.info(
                    "Claude profile review: input_tokens=%d, output_tokens=%d",
                    message.usage.input_tokens,
                    message.usage.output_tokens,
                )
                return response_text
            except anthropic.RateLimitError:
                if attempt < MAX_RETRIES - 1:
                    delay = BASE_DELAY * (2 ** attempt)
                    logger.warning("Rate limited, retrying in %ds", delay)
                    time.sleep(delay)
                else:
                    raise
            except anthropic.APIError as e:
                if attempt < MAX_RETRIES - 1:
                    delay = BASE_DELAY * (2 ** attempt)
                    logger.warning("API error: %s, retrying in %ds", e, delay)
                    time.sleep(delay)
                else:
                    raise
        raise RuntimeError("Exhausted retries calling Claude API")

    def _parse_json_response(self, raw: str) -> dict[str, Any] | None:
        """Parse JSON from Claude's response, handling possible markdown fences."""
        text = raw.strip()
        if text.startswith("```"):
            first_newline = text.index("\n") if "\n" in text else len(text)
            text = text[first_newline + 1:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON from profile review response: %s", text[:500])
            return None