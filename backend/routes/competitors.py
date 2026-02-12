from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.competitor import Competitor

router = APIRouter()


# --- Pydantic schemas ---

class CompetitorResponse(BaseModel):
    id: str
    name: str
    description: str
    key_products: str
    target_customers: str
    known_strengths: str
    known_weaknesses: str
    augment_overlap: str
    pricing: str
    content_types: list[str] | None
    is_active: bool
    is_suggested: bool
    suggested_reason: str | None
    created_by: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_model(cls, obj: Competitor) -> "CompetitorResponse":
        return cls(
            id=str(obj.id),
            name=obj.name,
            description=obj.description,
            key_products=obj.key_products,
            target_customers=obj.target_customers,
            known_strengths=obj.known_strengths,
            known_weaknesses=obj.known_weaknesses,
            augment_overlap=obj.augment_overlap,
            pricing=obj.pricing,
            content_types=obj.content_types,
            is_active=obj.is_active,
            is_suggested=obj.is_suggested,
            suggested_reason=obj.suggested_reason,
            created_by=str(obj.created_by) if obj.created_by else None,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )


class CompetitorCreate(BaseModel):
    name: str
    description: str = ""
    key_products: str = ""
    target_customers: str = ""
    known_strengths: str = ""
    known_weaknesses: str = ""
    augment_overlap: str = ""
    pricing: str = ""
    content_types: list[str] | None = None
    is_suggested: bool = False
    suggested_reason: str | None = None


class CompetitorUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    key_products: Optional[str] = None
    target_customers: Optional[str] = None
    known_strengths: Optional[str] = None
    known_weaknesses: Optional[str] = None
    augment_overlap: Optional[str] = None
    pricing: Optional[str] = None
    content_types: Optional[list[str]] = None


# --- Routes ---

@router.get("", response_model=list[CompetitorResponse])
def list_competitors(
    is_suggested: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """List competitors, optionally filtered by is_suggested."""
    query = db.query(Competitor).filter(Competitor.is_active == True)
    if is_suggested is not None:
        query = query.filter(Competitor.is_suggested == is_suggested)
    query = query.order_by(Competitor.name)
    competitors = query.all()
    return [CompetitorResponse.from_orm_model(c) for c in competitors]


@router.post("", response_model=CompetitorResponse, status_code=201)
def create_competitor(
    data: CompetitorCreate,
    db: Session = Depends(get_db),
):
    """Create a new competitor."""
    existing = db.query(Competitor).filter(Competitor.name == data.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Competitor with this name already exists")

    competitor = Competitor(
        name=data.name,
        description=data.description,
        key_products=data.key_products,
        target_customers=data.target_customers,
        known_strengths=data.known_strengths,
        known_weaknesses=data.known_weaknesses,
        augment_overlap=data.augment_overlap,
        pricing=data.pricing,
        content_types=data.content_types,
        is_suggested=data.is_suggested,
        suggested_reason=data.suggested_reason,
    )
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    return CompetitorResponse.from_orm_model(competitor)


@router.get("/{competitor_id}", response_model=CompetitorResponse)
def get_competitor(competitor_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a single competitor by ID."""
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return CompetitorResponse.from_orm_model(competitor)



@router.put("/{competitor_id}", response_model=CompetitorResponse)
def update_competitor(
    competitor_id: uuid.UUID,
    update: CompetitorUpdate,
    db: Session = Depends(get_db),
):
    """Update a competitor."""
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    update_data = update.model_dump(exclude_unset=True)

    # Check name uniqueness if name is being changed
    if "name" in update_data and update_data["name"] != competitor.name:
        existing = db.query(Competitor).filter(
            Competitor.name == update_data["name"],
            Competitor.id != competitor_id,
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Competitor with this name already exists")

    for field, value in update_data.items():
        setattr(competitor, field, value)

    db.commit()
    db.refresh(competitor)
    return CompetitorResponse.from_orm_model(competitor)


@router.delete("/{competitor_id}", status_code=204)
def delete_competitor(competitor_id: uuid.UUID, db: Session = Depends(get_db)):
    """Soft delete a competitor (set is_active=False)."""
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    competitor.is_active = False
    db.commit()
    return None


@router.post("/{competitor_id}/approve", response_model=CompetitorResponse)
def approve_competitor(competitor_id: uuid.UUID, db: Session = Depends(get_db)):
    """Approve a suggested competitor (set is_suggested=False)."""
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    if not competitor.is_suggested:
        raise HTTPException(status_code=400, detail="Competitor is not a suggestion")
    competitor.is_suggested = False
    db.commit()
    db.refresh(competitor)
    return CompetitorResponse.from_orm_model(competitor)


@router.post("/{competitor_id}/reject", status_code=204)
def reject_competitor(competitor_id: uuid.UUID, db: Session = Depends(get_db)):
    """Reject a suggested competitor (soft delete)."""
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    if not competitor.is_suggested:
        raise HTTPException(status_code=400, detail="Competitor is not a suggestion")
    competitor.is_active = False
    db.commit()
    return None