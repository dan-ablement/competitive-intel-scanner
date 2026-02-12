from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from backend.database import get_db
from backend.models.analysis_card import AnalysisCard, AnalysisCardCompetitor

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class CompetitorBrief(BaseModel):
    id: str
    name: str


class CardResponse(BaseModel):
    id: str
    feed_item_id: Optional[str]
    event_type: str
    priority: str
    title: str
    summary: str
    impact_assessment: str
    suggested_counter_moves: str
    raw_llm_output: Optional[dict] = None
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    check_run_id: Optional[str] = None
    competitors: list[CompetitorBrief] = []
    created_at: str
    updated_at: str


class CardUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    impact_assessment: Optional[str] = None
    suggested_counter_moves: Optional[str] = None
    event_type: Optional[str] = None
    priority: Optional[str] = None


class StatusUpdate(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _card_to_response(card: AnalysisCard) -> dict:
    """Serialize an AnalysisCard to a dict matching CardResponse."""
    competitors = []
    if card.competitors:
        competitors = [{"id": str(c.id), "name": c.name} for c in card.competitors]
    return {
        "id": str(card.id),
        "feed_item_id": str(card.feed_item_id) if card.feed_item_id else None,
        "event_type": card.event_type,
        "priority": card.priority,
        "title": card.title,
        "summary": card.summary,
        "impact_assessment": card.impact_assessment,
        "suggested_counter_moves": card.suggested_counter_moves,
        "raw_llm_output": card.raw_llm_output,
        "status": card.status,
        "approved_by": str(card.approved_by) if card.approved_by else None,
        "approved_at": card.approved_at.isoformat() if card.approved_at else None,
        "check_run_id": str(card.check_run_id) if card.check_run_id else None,
        "competitors": competitors,
        "created_at": card.created_at.isoformat() if card.created_at else None,
        "updated_at": card.updated_at.isoformat() if card.updated_at else None,
    }


VALID_STATUSES = {"draft", "in_review", "approved", "archived"}
VALID_PRIORITIES = {"red", "yellow", "green"}
VALID_EVENT_TYPES = {
    "new_feature", "product_announcement", "partnership", "acquisition",
    "acquired", "funding", "pricing_change", "leadership_change", "expansion", "other",
}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("", response_model=list[CardResponse])
def list_cards(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    competitor_id: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List analysis cards with optional filtering."""
    query = db.query(AnalysisCard).options(joinedload(AnalysisCard.competitors))

    if status:
        query = query.filter(AnalysisCard.status == status)
    if priority:
        query = query.filter(AnalysisCard.priority == priority)
    if competitor_id:
        query = query.join(AnalysisCardCompetitor).filter(
            AnalysisCardCompetitor.competitor_id == uuid.UUID(competitor_id)
        )
    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from)
            query = query.filter(AnalysisCard.created_at >= dt_from)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format")
    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to)
            query = query.filter(AnalysisCard.created_at <= dt_to)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format")

    cards = query.order_by(AnalysisCard.created_at.desc()).all()
    # Deduplicate due to joinedload + join
    seen = set()
    unique_cards = []
    for card in cards:
        if card.id not in seen:
            seen.add(card.id)
            unique_cards.append(card)
    return [_card_to_response(c) for c in unique_cards]



@router.get("/{card_id}", response_model=CardResponse)
def get_card(card_id: str, db: Session = Depends(get_db)):
    """Get a single analysis card by ID."""
    card = (
        db.query(AnalysisCard)
        .options(joinedload(AnalysisCard.competitors))
        .filter(AnalysisCard.id == uuid.UUID(card_id))
        .first()
    )
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return _card_to_response(card)


@router.put("/{card_id}", response_model=CardResponse)
def update_card(card_id: str, body: CardUpdate, db: Session = Depends(get_db)):
    """Update an analysis card's editable fields."""
    card = (
        db.query(AnalysisCard)
        .options(joinedload(AnalysisCard.competitors))
        .filter(AnalysisCard.id == uuid.UUID(card_id))
        .first()
    )
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    update_data = body.model_dump(exclude_unset=True)

    if "event_type" in update_data and update_data["event_type"] not in VALID_EVENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid event_type: {update_data['event_type']}")
    if "priority" in update_data and update_data["priority"] not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail=f"Invalid priority: {update_data['priority']}")

    for field, value in update_data.items():
        setattr(card, field, value)

    db.commit()
    db.refresh(card)

    # Re-load with competitors
    card = (
        db.query(AnalysisCard)
        .options(joinedload(AnalysisCard.competitors))
        .filter(AnalysisCard.id == card.id)
        .first()
    )
    return _card_to_response(card)


@router.post("/{card_id}/status", response_model=CardResponse)
def update_card_status(card_id: str, body: StatusUpdate, db: Session = Depends(get_db)):
    """Change the status of an analysis card."""
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {body.status}")

    card = (
        db.query(AnalysisCard)
        .options(joinedload(AnalysisCard.competitors))
        .filter(AnalysisCard.id == uuid.UUID(card_id))
        .first()
    )
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    card.status = body.status

    # If approving, set approved_at timestamp
    if body.status == "approved":
        card.approved_at = datetime.utcnow()

    db.commit()
    db.refresh(card)

    # Re-load with competitors
    card = (
        db.query(AnalysisCard)
        .options(joinedload(AnalysisCard.competitors))
        .filter(AnalysisCard.id == card.id)
        .first()
    )
    return _card_to_response(card)
