"""Prompt template for generating morning briefings."""

BRIEFING_SYSTEM_PROMPT = """You are a competitive intelligence analyst preparing a morning briefing for \
Augment Code's GTM team — Account Executives, Sales Engineers, and leadership. \
Synthesize the following intelligence items into a cohesive strategic briefing."""

BRIEFING_USER_PROMPT = """Context:
- Augment Profile: {augment_profile}
- Competitor Profiles: {competitor_profiles}

Analysis Cards from Past 24 Hours:
{analysis_cards_json}

Generate a briefing with the following sections in Markdown format:

## Executive Summary
A concise overview of the most important competitive developments from the past 24 hours.

## Priority Items
Highlight RED and YELLOW priority items with their implications for Augment.

## Market Signals
Broader market trends and patterns observed across the intelligence items.

## AE Talk Tracks
For each notable development above, provide a structured talk track that AEs can use in customer conversations.

For each talk track:
### [Brief description of the competitive development]
**Trigger:** "If a customer asks about [specific competitor announcement/development]..."
**Response:** A 2-3 sentence positioning statement AEs can use verbatim or adapt for their conversations. Should be confident, factual, and differentiation-focused.
**Proof point:** One specific Augment capability, metric, or architectural advantage that anchors the response.

## Full Item Details
A brief summary of each analysis card included in this briefing, grouped by competitor.

Respond in Markdown format only. Do not wrap in code fences."""


def build_briefing_prompt(
    augment_profile: str,
    competitor_profiles: str,
    analysis_cards_json: str,
) -> tuple[str, str]:
    """Build the morning briefing prompt with all context filled in.

    Returns (system_prompt, user_prompt) tuple for Claude API call.
    """
    user_prompt = BRIEFING_USER_PROMPT.format(
        augment_profile=augment_profile,
        competitor_profiles=competitor_profiles,
        analysis_cards_json=analysis_cards_json,
    )
    return BRIEFING_SYSTEM_PROMPT, user_prompt
