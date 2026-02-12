from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.augment_profile import AugmentProfile

router = APIRouter()


# --- Pydantic schemas ---

class AugmentProfileResponse(BaseModel):
    id: str
    company_description: str
    key_differentiators: str
    target_customer_segments: str
    product_capabilities: str
    strategic_priorities: str
    pricing: str
    updated_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_model(cls, obj: AugmentProfile) -> "AugmentProfileResponse":
        return cls(
            id=str(obj.id),
            company_description=obj.company_description,
            key_differentiators=obj.key_differentiators,
            target_customer_segments=obj.target_customer_segments,
            product_capabilities=obj.product_capabilities,
            strategic_priorities=obj.strategic_priorities,
            pricing=obj.pricing,
            updated_by=str(obj.updated_by),
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )


class AugmentProfileUpdate(BaseModel):
    company_description: Optional[str] = None
    key_differentiators: Optional[str] = None
    target_customer_segments: Optional[str] = None
    product_capabilities: Optional[str] = None
    strategic_priorities: Optional[str] = None
    pricing: Optional[str] = None


# --- Routes ---

@router.get("", response_model=AugmentProfileResponse)
def get_augment_profile(db: Session = Depends(get_db)):
    """Get the Augment company profile (single-row table)."""
    profile = db.query(AugmentProfile).first()
    if not profile:
        # Create a default empty profile if none exists
        profile = AugmentProfile(
            company_description="",
            key_differentiators="",
            target_customer_segments="",
            product_capabilities="",
            strategic_priorities="",
            pricing="",
            updated_by=uuid.UUID("00000000-0000-0000-0000-000000000000"),
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return AugmentProfileResponse.from_orm_model(profile)


@router.put("", response_model=AugmentProfileResponse)
def update_augment_profile(
    update: AugmentProfileUpdate,
    db: Session = Depends(get_db),
):
    """Update the Augment company profile."""
    profile = db.query(AugmentProfile).first()
    if not profile:
        # Create if not exists
        profile = AugmentProfile(
            company_description="",
            key_differentiators="",
            target_customer_segments="",
            product_capabilities="",
            strategic_priorities="",
            pricing="",
            updated_by=uuid.UUID("00000000-0000-0000-0000-000000000000"),
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    # TODO: Set updated_by from authenticated user when auth is implemented
    db.commit()
    db.refresh(profile)
    return AugmentProfileResponse.from_orm_model(profile)
