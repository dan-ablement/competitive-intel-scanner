"""Content Templates CRUD routes."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.content_template import ContentTemplate
from backend.models.user import User
from backend.routes.auth import get_current_user
from backend.utils import utc_isoformat

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class TemplateSection(BaseModel):
    title: str
    description: str = ""
    prompt_hint: str = ""


class TemplateCreate(BaseModel):
    content_type: str
    name: str
    description: Optional[str] = None
    sections: list[TemplateSection] = []
    doc_name_pattern: Optional[str] = None


class TemplateUpdate(BaseModel):
    content_type: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    sections: Optional[list[TemplateSection]] = None
    doc_name_pattern: Optional[str] = None
    is_active: Optional[bool] = None


class TemplateResponse(BaseModel):
    id: str
    content_type: str
    name: str
    description: Optional[str] = None
    sections: Optional[list[dict]] = None
    doc_name_pattern: Optional[str] = None
    is_active: bool
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _template_to_response(t: ContentTemplate) -> dict:
    return {
        "id": str(t.id),
        "content_type": t.content_type,
        "name": t.name,
        "description": t.description,
        "sections": t.sections or [],
        "doc_name_pattern": t.doc_name_pattern,
        "is_active": t.is_active,
        "created_at": utc_isoformat(t.created_at),
        "updated_at": utc_isoformat(t.updated_at),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("", response_model=list[TemplateResponse])
def list_templates(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
):
    """List content templates. By default only active templates."""
    query = db.query(ContentTemplate)
    if not include_inactive:
        query = query.filter(ContentTemplate.is_active == True)
    templates = query.order_by(ContentTemplate.name).all()
    return [_template_to_response(t) for t in templates]


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(template_id: str, db: Session = Depends(get_db)):
    """Get a single content template by ID."""
    t = db.query(ContentTemplate).filter(ContentTemplate.id == uuid.UUID(template_id)).first()
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return _template_to_response(t)


@router.post("", response_model=TemplateResponse, status_code=201)
def create_template(
    body: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new content template. Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create templates")

    # Check for duplicate content_type
    existing = db.query(ContentTemplate).filter(ContentTemplate.content_type == body.content_type).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Template with content_type '{body.content_type}' already exists")

    t = ContentTemplate(
        id=uuid.uuid4(),
        content_type=body.content_type,
        name=body.name,
        description=body.description,
        sections=[s.model_dump() for s in body.sections] if body.sections else [],
        doc_name_pattern=body.doc_name_pattern,
        is_active=True,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return _template_to_response(t)


@router.put("/{template_id}", response_model=TemplateResponse)
def update_template(
    template_id: str,
    body: TemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a content template. Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update templates")

    t = db.query(ContentTemplate).filter(ContentTemplate.id == uuid.UUID(template_id)).first()
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")

    update_data = body.model_dump(exclude_unset=True)
    if "sections" in update_data and update_data["sections"] is not None:
        update_data["sections"] = [s.model_dump() if hasattr(s, "model_dump") else s for s in body.sections]
    for field, value in update_data.items():
        setattr(t, field, value)

    db.commit()
    db.refresh(t)
    return _template_to_response(t)


@router.delete("/{template_id}", status_code=200)
def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a content template (set is_active=false). Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete templates")

    t = db.query(ContentTemplate).filter(ContentTemplate.id == uuid.UUID(template_id)).first()
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")

    t.is_active = False
    db.commit()
    return {"ok": True, "id": str(t.id)}

