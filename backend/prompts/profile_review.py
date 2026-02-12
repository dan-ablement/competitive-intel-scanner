"""Prompt templates for weekly profile review."""

PROFILE_REVIEW_SYSTEM = """\
You are a competitive intelligence analyst reviewing profiles for accuracy and completeness.
Based on recent approved analysis cards, identify any profile fields that should be updated.

Only suggest changes that are clearly supported by the analysis cards provided.
Do NOT suggest changes for fields where the current value is already accurate.
If no updates are needed, return an empty suggestions array.

For competitor profiles, valid fields are: description, key_products, target_customers, \
known_strengths, known_weaknesses, augment_overlap, pricing.

For the Augment profile, valid fields are: company_description, key_differentiators, \
target_customer_segments, product_capabilities, strategic_priorities, pricing.

Respond ONLY with valid JSON. No markdown, no code fences, no explanation outside the JSON."""

PROFILE_REVIEW_USER = """\
Review the following profile and suggest updates based on recent intelligence.

Target: {target_name}

Current Profile:
{target_profile}

Recent Approved Analysis Cards:
{relevant_cards}

Respond with JSON:
{{
  "suggestions": [
    {{
      "field": "<field_name>",
      "current_value": "<current text for that field>",
      "suggested_value": "<proposed replacement text>",
      "reason": "<why this change is warranted>",
      "source_card_ids": ["<card_id_1>", "<card_id_2>"]
    }}
  ]
}}"""


def build_profile_review_messages(
    target_name: str,
    target_profile: str,
    relevant_cards: str,
) -> list[dict[str, str]]:
    """Build the profile review messages for Claude API (system + user)."""
    user_content = PROFILE_REVIEW_USER.format(
        target_name=target_name,
        target_profile=target_profile,
        relevant_cards=relevant_cards,
    )
    return [{"role": "user", "content": user_content}]
