"""Briefing Generator service — creates daily morning briefings from recent analysis cards."""

from __future__ import annotations

import json
import logging
import random
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

import anthropic
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.analysis_card import AnalysisCard
from backend.models.augment_profile import AugmentProfile
from backend.models.briefing import Briefing, BriefingCard
from backend.models.competitor import Competitor
from backend.prompts.briefing import build_briefing_prompt
from backend.utils import utc_isoformat

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-20250514"
MAX_RETRIES = 5
BASE_DELAY = 15  # seconds
RATE_LIMIT_MIN_DELAY = 60  # minimum seconds to wait on rate limit (per-minute quota)


class BriefingGenerator:
    """Generates daily morning briefings from recent analysis cards."""

    def __init__(self) -> None:
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_briefing(self, db: Session) -> Briefing | None:
        """Generate a daily briefing from analysis cards created in the past 24 hours.

        Returns the created Briefing, or None if no cards were found.
        """
        today = datetime.now(timezone.utc).date()

        # Check if a briefing already exists for today
        existing = db.query(Briefing).filter(Briefing.date == today).first()
        if existing:
            logger.info("Briefing already exists for %s (id=%s), skipping.", today, existing.id)
            return existing

        # Gather analysis cards from the past 24 hours
        cards = self._gather_recent_cards(db)
        if not cards:
            logger.info("No analysis cards from the past 24 hours. Skipping briefing generation.")
            return None

        # Load context
        augment_profile_text = self._load_augment_profile(db)
        competitor_profiles_text = self._load_competitor_profiles(db)

        # Build card summaries for the prompt
        cards_json = self._cards_to_json(cards)

        # Call Claude to generate the briefing
        system_prompt, user_prompt = build_briefing_prompt(
            augment_profile=augment_profile_text,
            competitor_profiles=competitor_profiles_text,
            analysis_cards_json=cards_json,
        )

        briefing_content = self._call_claude(system_prompt, user_prompt)

        # Create the briefing record
        briefing = Briefing(
            id=uuid.uuid4(),
            date=today,
            content=briefing_content,
            raw_llm_output={"content": briefing_content, "model": MODEL},
            status="draft",
        )
        db.add(briefing)
        db.flush()

        # Link constituent analysis cards
        for card in cards:
            link = BriefingCard(
                briefing_id=briefing.id,
                analysis_card_id=card.id,
            )
            db.add(link)

        db.commit()
        db.refresh(briefing)
        logger.info(
            "Generated briefing %s for %s with %d cards.",
            briefing.id, today, len(cards),
        )
        return briefing

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _gather_recent_cards(self, db: Session) -> list[AnalysisCard]:
        """Get all analysis cards from the past 24 hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        cards = (
            db.query(AnalysisCard)
            .filter(AnalysisCard.created_at >= cutoff)
            .order_by(AnalysisCard.created_at.desc())
            .all()
        )
        return cards

    def _load_augment_profile(self, db: Session) -> str:
        """Load the Augment company profile as text."""
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
        """Load all active competitor profiles as text."""
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


    def _cards_to_json(self, cards: list[AnalysisCard]) -> str:
        """Serialize analysis cards to a JSON string for the LLM prompt."""
        card_dicts: list[dict[str, Any]] = []
        for card in cards:
            competitor_names = []
            if card.competitors:
                competitor_names = [c.name for c in card.competitors]
            card_dicts.append({
                "id": str(card.id),
                "title": card.title,
                "event_type": card.event_type,
                "priority": card.priority,
                "summary": card.summary,
                "impact_assessment": card.impact_assessment,
                "suggested_counter_moves": card.suggested_counter_moves,
                "status": card.status,
                "competitors": competitor_names,
                "created_at": utc_isoformat(card.created_at),
            })
        return json.dumps(card_dicts, indent=2)

    def _call_claude(self, system_prompt: str, user_prompt: str) -> str:
        """Call Claude API with rate-limit-aware retry.

        For RateLimitError (429): waits at least 60s (per-minute quota) plus jitter.
        For other APIErrors: uses exponential backoff with BASE_DELAY.
        """
        for attempt in range(MAX_RETRIES):
            try:
                message = self.client.messages.create(
                    model=MODEL,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                response_text = message.content[0].text
                logger.info(
                    "Briefing Claude API call: input_tokens=%d, output_tokens=%d",
                    message.usage.input_tokens,
                    message.usage.output_tokens,
                )
                return response_text
            except anthropic.RateLimitError:
                if attempt < MAX_RETRIES - 1:
                    # Per-minute rate limit — wait at least 60s plus jitter
                    delay = RATE_LIMIT_MIN_DELAY + random.uniform(0, 5)
                    logger.warning(
                        "Rate limited (429), waiting %.1fs (attempt %d/%d)",
                        delay, attempt + 1, MAX_RETRIES,
                    )
                    time.sleep(delay)
                else:
                    raise
            except anthropic.APIError as e:
                if attempt < MAX_RETRIES - 1:
                    delay = BASE_DELAY * (2 ** attempt)
                    logger.warning(
                        "API error: %s, retrying in %ds (attempt %d/%d)",
                        e, delay, attempt + 1, MAX_RETRIES,
                    )
                    time.sleep(delay)
                else:
                    raise
        raise RuntimeError("Exhausted retries calling Claude API for briefing")