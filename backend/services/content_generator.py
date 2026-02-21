"""Content Generator service — produces battle card content from competitor profiles and analysis cards using Claude API."""

from __future__ import annotations

import json
import logging
import random
import time
import uuid
from typing import Any

import anthropic
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.analysis_card import AnalysisCard, AnalysisCardCompetitor
from backend.models.augment_profile import AugmentProfile
from backend.models.competitor import Competitor
from backend.utils import utc_isoformat

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-20250514"
MAX_RETRIES = 5
BASE_DELAY = 15  # seconds
RATE_LIMIT_MIN_DELAY = 60  # minimum seconds to wait on rate limit (per-minute quota)
INTER_ITEM_DELAY = 3  # seconds between consecutive LLM calls


class ContentGenerator:
    """Generates battle card content from competitor profiles and approved analysis cards."""

    def __init__(self) -> None:
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_content(
        self,
        db: Session,
        competitor_id: uuid.UUID,
        template_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Generate content for a competitor using a content template.

        Returns a dict with:
            - content: JSON string of per-section generated content
            - raw_llm_output: full LLM response metadata
            - source_card_ids: list of analysis card UUIDs used as context
            - competitor_id: the competitor UUID
            - content_type: the template name/type
        """
        # Load competitor
        competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
        if not competitor:
            raise ValueError(f"Competitor not found: {competitor_id}")

        # Load template (imported inside method to avoid circular/timing issues)
        from backend.models.content_template import ContentTemplate
        template = db.query(ContentTemplate).filter(ContentTemplate.id == template_id).first()
        if not template:
            raise ValueError(f"Content template not found: {template_id}")

        # Load Augment profile
        augment_profile_text = self._load_augment_profile(db)

        # Load approved analysis cards for this competitor
        cards = self._load_approved_cards(db, competitor_id)
        cards_text = self._format_cards(cards)
        source_card_ids = [str(card.id) for card in cards]

        # Build prompt
        competitor_text = self._format_competitor(competitor)
        sections = template.sections or []
        prompt = self._build_prompt(
            competitor_name=competitor.name,
            competitor_text=competitor_text,
            augment_profile_text=augment_profile_text,
            cards_text=cards_text,
            sections=sections,
        )

        # Call Claude
        raw_response = self._call_claude(prompt)
        parsed = self._parse_json_response(raw_response)

        # Build result dict (route layer creates the ContentOutput record)
        return {
            "content": json.dumps(parsed) if parsed else raw_response,
            "raw_llm_output": {
                "model": MODEL,
                "raw_text": raw_response,
                "parsed": parsed,
            },
            "source_card_ids": source_card_ids,
            "competitor_id": str(competitor_id),
            "content_type": template.name if hasattr(template, "name") else str(template_id),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

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

    def _load_approved_cards(self, db: Session, competitor_id: uuid.UUID) -> list[AnalysisCard]:
        """Load all approved analysis cards linked to a competitor, newest first."""
        cards = (
            db.query(AnalysisCard)
            .join(AnalysisCardCompetitor, AnalysisCard.id == AnalysisCardCompetitor.analysis_card_id)
            .filter(
                AnalysisCardCompetitor.competitor_id == competitor_id,
                AnalysisCard.status == "approved",
            )
            .order_by(AnalysisCard.created_at.desc())
            .all()
        )
        return cards

    def _format_competitor(self, competitor: Competitor) -> str:
        """Format a competitor profile as text for the prompt."""
        return (
            f"Name: {competitor.name}\n"
            f"Description: {competitor.description}\n"
            f"Key Products: {competitor.key_products}\n"
            f"Target Customers: {competitor.target_customers}\n"
            f"Strengths: {competitor.known_strengths}\n"
            f"Weaknesses: {competitor.known_weaknesses}\n"
            f"Overlap with Augment: {competitor.augment_overlap}\n"
            f"Pricing: {competitor.pricing}"
        )

    def _format_cards(self, cards: list[AnalysisCard]) -> str:
        """Format approved analysis cards as text for the prompt."""
        if not cards:
            return "No approved analysis cards available for this competitor."
        parts: list[str] = []
        for card in cards:
            parts.append(
                f"--- Card: {card.title} ---\n"
                f"Event Type: {card.event_type}\n"
                f"Priority: {card.priority}\n"
                f"Summary: {card.summary}\n"
                f"Impact Assessment: {card.impact_assessment}\n"
                f"Suggested Counter-Moves: {card.suggested_counter_moves}\n"
                f"Date: {utc_isoformat(card.created_at) or 'Unknown'}"
            )
        return "\n\n".join(parts)

    def _build_prompt(
        self,
        competitor_name: str,
        competitor_text: str,
        augment_profile_text: str,
        cards_text: str,
        sections: list[dict[str, str]],
    ) -> str:
        """Build the Claude prompt for content generation."""
        sections_instruction = ""
        for i, section in enumerate(sections, 1):
            title = section.get("title", f"Section {i}")
            description = section.get("description", "")
            prompt_hint = section.get("prompt_hint", "")
            sections_instruction += f"\n{i}. \"{title}\""
            if description:
                sections_instruction += f" — {description}"
            if prompt_hint:
                sections_instruction += f"\n   Guidance: {prompt_hint}"
            sections_instruction += "\n"

        return f"""You are a competitive intelligence analyst creating a battle card for **{competitor_name}** specifically. This battle card is exclusively about {competitor_name} vs Augment Code. Do not mention, reference, or compare any other competitors.

Your goal is to produce actionable, sales-team-friendly content that helps reps understand and compete against {competitor_name}.

## Our Company (Augment)
{augment_profile_text}

## Competitor Profile
{competitor_text}

## Recent Intelligence (Approved Analysis Cards)
{cards_text}

## Required Sections
Generate content for each of the following sections. Return your response as a JSON object where each key is the section title and the value is the content for that section.
{sections_instruction}

## Instructions
- This battle card is exclusively about {competitor_name} vs Augment Code. Do not mention, reference, or compare any other competitors.
- When analysis cards reference other competitors, ignore those references entirely. Extract only information directly relevant to {competitor_name} vs Augment Code.
- Write in clear, actionable language suitable for sales representatives
- Include specific talking points and objection handlers where relevant
- Reference recent intelligence from the analysis cards when applicable
- Focus on how Augment differentiates from {competitor_name}
- Be factual and avoid speculation — base claims on the provided intelligence
- Each section should be 2-5 paragraphs of substantive content

Return ONLY a valid JSON object with section titles as keys and generated content as string values. No markdown fences, no extra text."""

    def _call_claude(self, prompt: str) -> str:
        """Call Claude API with rate-limit-aware retry.

        For RateLimitError (429): waits at least 60s (per-minute quota) plus jitter.
        For other APIErrors: uses exponential backoff with BASE_DELAY.
        """
        for attempt in range(MAX_RETRIES):
            try:
                message = self.client.messages.create(
                    model=MODEL,
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}],
                )
                response_text = message.content[0].text
                logger.info(
                    "Content generation Claude API call: input_tokens=%d, output_tokens=%d",
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
        # Should not reach here, but just in case
        raise RuntimeError("Exhausted retries calling Claude API for content generation")

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
            logger.error("Failed to parse JSON from content generation LLM response: %s", text[:500])
            return None

