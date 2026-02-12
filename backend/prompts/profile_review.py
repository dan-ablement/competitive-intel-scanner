"""Prompt template for weekly profile review."""

PROFILE_REVIEW_SYSTEM = """You are reviewing competitive intelligence profiles for accuracy and completeness.

Current {target_name} Profile: {target_profile}
Recent Approved Analysis Cards: {relevant_cards}

Respond with JSON:
{{
  "suggestions": [
    {{
      "field": string,
      "current_value": string,
      "suggested_value": string,
      "reason": string,
      "source_card_ids": [string]
    }}
  ]
}}

IMPORTANT: Respond ONLY with valid JSON. No markdown, no code fences, no explanation outside the JSON."""


def build_profile_review_prompt(
    target_name: str,
    target_profile: str,
    relevant_cards: str,
) -> str:
    """Build the profile review prompt with all context filled in."""
    return PROFILE_REVIEW_SYSTEM.format(
        target_name=target_name,
        target_profile=target_profile,
        relevant_cards=relevant_cards,
    )
