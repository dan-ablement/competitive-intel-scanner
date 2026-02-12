"""Prompt template for generating morning briefings."""

BRIEFING_SYSTEM = """You are a competitive intelligence analyst preparing a morning briefing for \
Augment Code's leadership team. Synthesize the following intelligence items into a \
cohesive strategic briefing.

Context:
- Augment Profile: {augment_profile}
- Competitor Profiles: {competitor_profiles}

Analysis Cards from Past 24 Hours:
{analysis_cards_json}

Generate a briefing with the following sections:

## Executive Summary
## Priority Items
## Market Signals
## Recommended Actions
## Full Item Details

Respond in Markdown format."""


def build_briefing_prompt(
    augment_profile: str,
    competitor_profiles: str,
    analysis_cards_json: str,
) -> str:
    """Build the morning briefing prompt with all context filled in."""
    return BRIEFING_SYSTEM.format(
        augment_profile=augment_profile,
        competitor_profiles=competitor_profiles,
        analysis_cards_json=analysis_cards_json,
    )
