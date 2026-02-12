from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from backend.database import get_db
from backend.models.analysis_card import (
    AnalysisCard,
    AnalysisCardComment,
    AnalysisCardCompetitor,
    AnalysisCardEdit,
)
from backend.models.user import User
from backend.routes.auth import get_current_user

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


class CommentCreate(BaseModel):
    content: str
    parent_comment_id: Optional[str] = None


class CommentUpdate(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: str
    analysis_card_id: str
    user_id: str
    user_name: str
    content: str
    parent_comment_id: Optional[str] = None
    resolved: bool
    created_at: str
    updated_at: str
    replies: list["CommentResponse"] = []


class EditResponse(BaseModel):
    id: str
    analysis_card_id: str
    user_id: str
    user_name: str
    field_changed: str
    previous_value: str
    new_value: str
    created_at: str


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

# Fields that are tracked for edit history
TRACKED_FIELDS = {"title", "summary", "impact_assessment", "suggested_counter_moves", "event_type", "priority"}


def _comment_to_response(comment: AnalysisCardComment) -> dict:
    """Serialize a comment to a dict matching CommentResponse."""
    user_name = comment.user.name if comment.user else "Unknown"
    replies = []
    if comment.replies:
        replies = [_comment_to_response(r) for r in comment.replies]
    return {
        "id": str(comment.id),
        "analysis_card_id": str(comment.analysis_card_id),
        "user_id": str(comment.user_id),
        "user_name": user_name,
        "content": comment.content,
        "parent_comment_id": str(comment.parent_comment_id) if comment.parent_comment_id else None,
        "resolved": comment.resolved,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
        "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
        "replies": replies,
    }


def _edit_to_response(edit: AnalysisCardEdit) -> dict:
    """Serialize an edit to a dict matching EditResponse."""
    user_name = edit.user.name if edit.user else "Unknown"
    return {
        "id": str(edit.id),
        "analysis_card_id": str(edit.analysis_card_id),
        "user_id": str(edit.user_id),
        "user_name": user_name,
        "field_changed": edit.field_changed,
        "previous_value": edit.previous_value,
        "new_value": edit.new_value,
        "created_at": edit.created_at.isoformat() if edit.created_at else None,
    }


def _get_card_or_404(card_id: str, db: Session) -> AnalysisCard:
    """Fetch a card by ID or raise 404."""
    card = (
        db.query(AnalysisCard)
        .options(joinedload(AnalysisCard.competitors))
        .filter(AnalysisCard.id == uuid.UUID(card_id))
        .first()
    )
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


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
def update_card(
    card_id: str,
    body: CardUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an analysis card's editable fields and track changes."""
    card = _get_card_or_404(card_id, db)

    update_data = body.model_dump(exclude_unset=True)

    if "event_type" in update_data and update_data["event_type"] not in VALID_EVENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid event_type: {update_data['event_type']}")
    if "priority" in update_data and update_data["priority"] not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail=f"Invalid priority: {update_data['priority']}")

    # Track edits for each changed field
    for field, new_value in update_data.items():
        if field in TRACKED_FIELDS:
            previous_value = getattr(card, field, "") or ""
            if str(previous_value) != str(new_value):
                edit = AnalysisCardEdit(
                    id=uuid.uuid4(),
                    analysis_card_id=card.id,
                    user_id=current_user.id,
                    field_changed=field,
                    previous_value=str(previous_value),
                    new_value=str(new_value),
                )
                db.add(edit)

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
def update_card_status(
    card_id: str,
    body: StatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change the status of an analysis card. Only admins can approve."""
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {body.status}")

    # Enforce admin-only approval
    if body.status == "approved" and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin users can approve cards")

    card = _get_card_or_404(card_id, db)

    card.status = body.status

    # If approving, set approved_by and approved_at
    if body.status == "approved":
        card.approved_by = current_user.id
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



# ---------------------------------------------------------------------------
# Edit History
# ---------------------------------------------------------------------------

@router.get("/{card_id}/history", response_model=list[EditResponse])
def get_card_history(
    card_id: str,
    db: Session = Depends(get_db),
):
    """Get the edit history for a card."""
    # Verify card exists
    _get_card_or_404(card_id, db)

    edits = (
        db.query(AnalysisCardEdit)
        .options(joinedload(AnalysisCardEdit.user))
        .filter(AnalysisCardEdit.analysis_card_id == uuid.UUID(card_id))
        .order_by(AnalysisCardEdit.created_at.desc())
        .all()
    )
    return [_edit_to_response(e) for e in edits]


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

@router.get("/{card_id}/comments", response_model=list[CommentResponse])
def list_card_comments(
    card_id: str,
    db: Session = Depends(get_db),
):
    """List comments for a card (top-level only, with threaded replies)."""
    # Verify card exists
    _get_card_or_404(card_id, db)

    # Fetch top-level comments (no parent) with their replies
    comments = (
        db.query(AnalysisCardComment)
        .options(joinedload(AnalysisCardComment.user))
        .filter(
            AnalysisCardComment.analysis_card_id == uuid.UUID(card_id),
            AnalysisCardComment.parent_comment_id.is_(None),
        )
        .order_by(AnalysisCardComment.created_at.desc())
        .all()
    )

    # Eagerly load replies for each comment
    for comment in comments:
        _load_replies(comment, db)

    return [_comment_to_response(c) for c in comments]


def _load_replies(comment: AnalysisCardComment, db: Session) -> None:
    """Recursively load replies for a comment."""
    replies = (
        db.query(AnalysisCardComment)
        .options(joinedload(AnalysisCardComment.user))
        .filter(AnalysisCardComment.parent_comment_id == comment.id)
        .order_by(AnalysisCardComment.created_at.asc())
        .all()
    )
    comment.replies = replies
    for reply in replies:
        _load_replies(reply, db)


@router.post("/{card_id}/comments", response_model=CommentResponse, status_code=201)
def add_comment(
    card_id: str,
    body: CommentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a comment to a card."""
    # Verify card exists
    _get_card_or_404(card_id, db)

    # Validate parent comment if provided
    parent_comment_id = None
    if body.parent_comment_id:
        parent = (
            db.query(AnalysisCardComment)
            .filter(
                AnalysisCardComment.id == uuid.UUID(body.parent_comment_id),
                AnalysisCardComment.analysis_card_id == uuid.UUID(card_id),
            )
            .first()
        )
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")
        parent_comment_id = parent.id

    comment = AnalysisCardComment(
        id=uuid.uuid4(),
        analysis_card_id=uuid.UUID(card_id),
        user_id=current_user.id,
        content=body.content,
        parent_comment_id=parent_comment_id,
        resolved=False,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    # Reload with user relationship
    comment = (
        db.query(AnalysisCardComment)
        .options(joinedload(AnalysisCardComment.user))
        .filter(AnalysisCardComment.id == comment.id)
        .first()
    )
    return _comment_to_response(comment)


@router.put("/{card_id}/comments/{comment_id}", response_model=CommentResponse)
def update_comment(
    card_id: str,
    comment_id: str,
    body: CommentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Edit a comment. Only the comment author can edit."""
    comment = (
        db.query(AnalysisCardComment)
        .options(joinedload(AnalysisCardComment.user))
        .filter(
            AnalysisCardComment.id == uuid.UUID(comment_id),
            AnalysisCardComment.analysis_card_id == uuid.UUID(card_id),
        )
        .first()
    )
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own comments")

    comment.content = body.content
    db.commit()
    db.refresh(comment)

    # Reload with user
    comment = (
        db.query(AnalysisCardComment)
        .options(joinedload(AnalysisCardComment.user))
        .filter(AnalysisCardComment.id == comment.id)
        .first()
    )
    return _comment_to_response(comment)


@router.post("/{card_id}/comments/{comment_id}/resolve", response_model=CommentResponse)
def resolve_comment(
    card_id: str,
    comment_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Toggle resolve/unresolve a comment."""
    comment = (
        db.query(AnalysisCardComment)
        .options(joinedload(AnalysisCardComment.user))
        .filter(
            AnalysisCardComment.id == uuid.UUID(comment_id),
            AnalysisCardComment.analysis_card_id == uuid.UUID(card_id),
        )
        .first()
    )
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    comment.resolved = not comment.resolved
    db.commit()
    db.refresh(comment)

    # Reload with user
    comment = (
        db.query(AnalysisCardComment)
        .options(joinedload(AnalysisCardComment.user))
        .filter(AnalysisCardComment.id == comment.id)
        .first()
    )
    return _comment_to_response(comment)