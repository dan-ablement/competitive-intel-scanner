from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.profile_suggestion import ProfileUpdateSuggestion
from backend.utils import utc_isoformat
from backend.models.competitor import Competitor
from backend.models.augment_profile import AugmentProfile

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class SuggestionResponse(BaseModel):
    id: str
    target_type: str
    competitor_id: str | None
    competitor_name: str | None = None
    field: str
    current_value: str
    suggested_value: str
    reason: str
    source_card_ids: list[str]
    status: str
    reviewed_by: str | None
    reviewed_at: str | None
    created_at: str

    @classmethod
    def from_orm_model(cls, obj: ProfileUpdateSuggestion, competitor_name: str | None = None) -> "SuggestionResponse":
        return cls(
            id=str(obj.id),
            target_type=obj.target_type,
            competitor_id=str(obj.competitor_id) if obj.competitor_id else None,
            competitor_name=competitor_name,
            field=obj.field,
            current_value=obj.current_value,
            suggested_value=obj.suggested_value,
            reason=obj.reason,
            source_card_ids=obj.source_card_ids or [],
            status=obj.status,
            reviewed_by=str(obj.reviewed_by) if obj.reviewed_by else None,
            reviewed_at=utc_isoformat(obj.reviewed_at),
            created_at=utc_isoformat(obj.created_at) or "",
        )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("", response_model=list[SuggestionResponse])
def list_suggestions(
    status: Optional[str] = Query("pending"),
    db: Session = Depends(get_db),
):
    """List profile update suggestions, filtered by status."""
    query = db.query(ProfileUpdateSuggestion)
    if status:
        query = query.filter(ProfileUpdateSuggestion.status == status)
    query = query.order_by(ProfileUpdateSuggestion.created_at.desc())
    suggestions = query.all()

    # Build competitor name lookup
    competitor_ids = {s.competitor_id for s in suggestions if s.competitor_id}
    competitor_names: dict[uuid.UUID, str] = {}
    if competitor_ids:
        competitors = db.query(Competitor).filter(Competitor.id.in_(competitor_ids)).all()
        competitor_names = {c.id: c.name for c in competitors}

    return [
        SuggestionResponse.from_orm_model(s, competitor_names.get(s.competitor_id))
        for s in suggestions
    ]


@router.post("/{suggestion_id}/approve", response_model=SuggestionResponse)
def approve_suggestion(
    suggestion_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Approve a suggestion and apply the change to the target profile."""
    suggestion = db.query(ProfileUpdateSuggestion).filter(
        ProfileUpdateSuggestion.id == suggestion_id,
    ).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    if suggestion.status != "pending":
        raise HTTPException(status_code=400, detail="Suggestion is not pending")

    # Apply the change to the target profile
    _apply_suggestion(db, suggestion)

    # Mark as approved
    suggestion.status = "approved"
    suggestion.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(suggestion)

    competitor_name = None
    if suggestion.competitor_id:
        comp = db.query(Competitor).filter(Competitor.id == suggestion.competitor_id).first()
        competitor_name = comp.name if comp else None

    return SuggestionResponse.from_orm_model(suggestion, competitor_name)


@router.post("/{suggestion_id}/reject", response_model=SuggestionResponse)
def reject_suggestion(
    suggestion_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Reject a suggestion."""
    suggestion = db.query(ProfileUpdateSuggestion).filter(
        ProfileUpdateSuggestion.id == suggestion_id,
    ).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    if suggestion.status != "pending":
        raise HTTPException(status_code=400, detail="Suggestion is not pending")

    suggestion.status = "rejected"
    suggestion.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(suggestion)

    competitor_name = None
    if suggestion.competitor_id:
        comp = db.query(Competitor).filter(Competitor.id == suggestion.competitor_id).first()
        competitor_name = comp.name if comp else None

    return SuggestionResponse.from_orm_model(suggestion, competitor_name)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Valid fields for each target type
COMPETITOR_FIELDS = {
    "description", "key_products", "target_customers",
    "known_strengths", "known_weaknesses", "augment_overlap", "pricing",
}
AUGMENT_FIELDS = {
    "company_description", "key_differentiators", "target_customer_segments",
    "product_capabilities", "strategic_priorities", "pricing",
}


def _apply_suggestion(db: Session, suggestion: ProfileUpdateSuggestion) -> None:
    """Apply a suggestion's change to the actual profile."""
    if suggestion.target_type == "competitor":
        if suggestion.field not in COMPETITOR_FIELDS:
            raise HTTPException(status_code=400, detail=f"Invalid competitor field: {suggestion.field}")
        competitor = db.query(Competitor).filter(Competitor.id == suggestion.competitor_id).first()
        if not competitor:
            raise HTTPException(status_code=404, detail="Target competitor not found")
        setattr(competitor, suggestion.field, suggestion.suggested_value)

    elif suggestion.target_type == "augment":
        if suggestion.field not in AUGMENT_FIELDS:
            raise HTTPException(status_code=400, detail=f"Invalid augment field: {suggestion.field}")
        profile = db.query(AugmentProfile).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Augment profile not found")
        setattr(profile, suggestion.field, suggestion.suggested_value)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown target type: {suggestion.target_type}")
