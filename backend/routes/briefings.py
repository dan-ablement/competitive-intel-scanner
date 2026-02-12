from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from backend.database import get_db
from backend.models.briefing import Briefing

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class CardBrief(BaseModel):
    id: str
    title: str
    event_type: str
    priority: str
    status: str


class BriefingResponse(BaseModel):
    id: str
    date: str
    content: str
    raw_llm_output: Optional[dict] = None
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    cards: list[CardBrief] = []
    created_at: str
    updated_at: str


class BriefingListItem(BaseModel):
    id: str
    date: str
    status: str
    card_count: int
    created_at: str
    updated_at: str


class BriefingUpdate(BaseModel):
    content: Optional[str] = None


class StatusUpdate(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_STATUSES = {"draft", "in_review", "approved", "archived"}


def _briefing_to_list_item(briefing: Briefing) -> dict:
    """Serialize a Briefing to a list-item dict."""
    card_count = len(briefing.cards) if briefing.cards else 0
    return {
        "id": str(briefing.id),
        "date": briefing.date.isoformat() if briefing.date else None,
        "status": briefing.status,
        "card_count": card_count,
        "created_at": briefing.created_at.isoformat() if briefing.created_at else None,
        "updated_at": briefing.updated_at.isoformat() if briefing.updated_at else None,
    }


def _briefing_to_response(briefing: Briefing) -> dict:
    """Serialize a Briefing to a full response dict with linked cards."""
    cards = []
    if briefing.cards:
        cards = [
            {
                "id": str(c.id),
                "title": c.title,
                "event_type": c.event_type,
                "priority": c.priority,
                "status": c.status,
            }
            for c in briefing.cards
        ]
    return {
        "id": str(briefing.id),
        "date": briefing.date.isoformat() if briefing.date else None,
        "content": briefing.content,
        "raw_llm_output": briefing.raw_llm_output,
        "status": briefing.status,
        "approved_by": str(briefing.approved_by) if briefing.approved_by else None,
        "approved_at": briefing.approved_at.isoformat() if briefing.approved_at else None,
        "cards": cards,
        "created_at": briefing.created_at.isoformat() if briefing.created_at else None,
        "updated_at": briefing.updated_at.isoformat() if briefing.updated_at else None,
    }


def _get_briefing_or_404(briefing_id: str, db: Session) -> Briefing:
    """Fetch a briefing by ID or raise 404."""
    briefing = (
        db.query(Briefing)
        .options(joinedload(Briefing.cards))
        .filter(Briefing.id == uuid.UUID(briefing_id))
        .first()
    )
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")
    return briefing


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("", response_model=list[BriefingListItem])
def list_briefings(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List briefings, most recent first. Optionally filter by status."""
    query = db.query(Briefing).options(joinedload(Briefing.cards))

    if status:
        if status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        query = query.filter(Briefing.status == status)

    briefings = query.order_by(Briefing.date.desc()).all()
    # Deduplicate due to joinedload
    seen = set()
    unique = []
    for b in briefings:
        if b.id not in seen:
            seen.add(b.id)
            unique.append(b)
    return [_briefing_to_list_item(b) for b in unique]


@router.get("/{briefing_id}", response_model=BriefingResponse)
def get_briefing(briefing_id: str, db: Session = Depends(get_db)):
    """Get a single briefing with linked analysis cards."""
    briefing = _get_briefing_or_404(briefing_id, db)
    return _briefing_to_response(briefing)


@router.put("/{briefing_id}", response_model=BriefingResponse)
def update_briefing(
    briefing_id: str,
    body: BriefingUpdate,
    db: Session = Depends(get_db),
):
    """Edit a briefing's content."""
    briefing = _get_briefing_or_404(briefing_id, db)

    update_data = body.model_dump(exclude_unset=True)
    if "content" in update_data:
        briefing.content = update_data["content"]

    db.commit()
    db.refresh(briefing)

    # Re-load with cards
    briefing = (
        db.query(Briefing)
        .options(joinedload(Briefing.cards))
        .filter(Briefing.id == briefing.id)
        .first()
    )
    return _briefing_to_response(briefing)


@router.post("/{briefing_id}/status", response_model=BriefingResponse)
def update_briefing_status(
    briefing_id: str,
    body: StatusUpdate,
    db: Session = Depends(get_db),
):
    """Change the status of a briefing (draft → in_review → approved → archived)."""
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {body.status}")

    briefing = _get_briefing_or_404(briefing_id, db)
    briefing.status = body.status

    # If approving, record the timestamp (no auth enforcement yet per task spec)
    if body.status == "approved":
        briefing.approved_at = datetime.utcnow()

    db.commit()
    db.refresh(briefing)

    # Re-load with cards
    briefing = (
        db.query(Briefing)
        .options(joinedload(Briefing.cards))
        .filter(Briefing.id == briefing.id)
        .first()
    )
    return _briefing_to_response(briefing)
