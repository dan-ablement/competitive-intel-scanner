"""Content Outputs routes — CRUD, generate, status changes, stale content detection."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from backend.database import get_db, SessionLocal
from backend.models.analysis_card import AnalysisCard, AnalysisCardCompetitor
from backend.models.competitor import Competitor
from backend.models.content_output import ContentOutput
from backend.models.content_template import ContentTemplate
from backend.models.user import User
from backend.routes.auth import get_current_user
from backend.utils import utc_isoformat

router = APIRouter()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ContentOutputResponse(BaseModel):
    id: str
    competitor_id: str
    competitor_name: str
    content_type: str
    title: Optional[str] = None
    content: str
    sections: Optional[list[dict]] = None
    source_card_ids: Optional[list[str]] = None
    version: int
    status: str
    template_id: Optional[str] = None
    google_doc_id: Optional[str] = None
    google_doc_url: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    published_at: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str


class ContentOutputCreate(BaseModel):
    competitor_id: str
    template_id: str


class ContentOutputUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class StatusUpdate(BaseModel):
    status: str


class StaleContentItem(BaseModel):
    competitor_id: str
    competitor_name: str
    content_type: str
    status: str  # 'stale' or 'missing'
    days_stale: Optional[int] = None
    latest_content_id: Optional[str] = None


class GenerateResponse(BaseModel):
    id: str
    status: str
    message: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _output_to_response(co: ContentOutput) -> dict:
    """Serialize a ContentOutput to a dict matching ContentOutputResponse."""
    competitor_name = ""
    if co.competitor:
        competitor_name = co.competitor.name

    # Parse content as sections if it's JSON
    sections = None
    try:
        parsed = json.loads(co.content) if co.content else None
        if isinstance(parsed, dict):
            sections = [{"title": k, "body": v} for k, v in parsed.items()]
    except (json.JSONDecodeError, TypeError):
        pass

    return {
        "id": str(co.id),
        "competitor_id": str(co.competitor_id),
        "competitor_name": competitor_name,
        "content_type": co.content_type or "",
        "title": co.title or "",
        "content": co.content or "",
        "sections": sections or [],
        "source_card_ids": co.source_card_ids or [],
        "version": co.version,
        "status": co.status,
        "template_id": str(co.template_id) if co.template_id else None,
        "google_doc_id": co.google_doc_id,
        "google_doc_url": co.google_doc_url,
        "approved_by": str(co.approved_by) if co.approved_by else None,
        "approved_at": utc_isoformat(co.approved_at),
        "published_at": utc_isoformat(co.published_at),
        "error_message": co.error_message,
        "created_at": utc_isoformat(co.created_at),
        "updated_at": utc_isoformat(co.updated_at),
    }


VALID_STATUSES = {"draft", "in_review", "approved", "published", "failed"}


# ---------------------------------------------------------------------------
# Background task helpers
# ---------------------------------------------------------------------------

def _run_content_generation(content_output_id: str, competitor_id: str, template_id: str) -> None:
    """Background task: generate content via LLM and update the content_output record."""
    db = SessionLocal()
    try:
        from backend.services.content_generator import ContentGenerator

        generator = ContentGenerator()
        result = generator.generate_content(
            db,
            competitor_id=uuid.UUID(competitor_id),
            template_id=uuid.UUID(template_id),
        )

        co = db.query(ContentOutput).filter(ContentOutput.id == uuid.UUID(content_output_id)).first()
        if co:
            co.content = result.get("content", "")
            co.raw_llm_output = result.get("raw_llm_output")
            co.source_card_ids = result.get("source_card_ids", [])
            co.content_type = result.get("content_type", co.content_type)

            # Generate title from template + competitor
            competitor = db.query(Competitor).filter(Competitor.id == uuid.UUID(competitor_id)).first()
            template = db.query(ContentTemplate).filter(ContentTemplate.id == uuid.UUID(template_id)).first()
            if template and competitor and template.doc_name_pattern:
                co.title = template.doc_name_pattern.replace("{competitor}", competitor.name)
            elif competitor:
                co.title = f"Battle Card - {competitor.name}"

            co.status = "draft"
            db.commit()
            logger.info("Content generation complete for output %s", content_output_id)
    except Exception as e:
        logger.exception("Content generation failed for output %s", content_output_id)
        co = db.query(ContentOutput).filter(ContentOutput.id == uuid.UUID(content_output_id)).first()
        if co:
            co.status = "failed"
            co.error_message = f"Content generation failed: {str(e)}"
            db.commit()
    finally:
        db.close()


def _run_google_docs_publish(content_output_id: str, user_id: str) -> None:
    """Background task: publish content to Google Docs."""
    db = SessionLocal()
    try:
        from backend.services.google_docs_service import GoogleDocsService

        co = db.query(ContentOutput).options(
            joinedload(ContentOutput.competitor)
        ).filter(ContentOutput.id == uuid.UUID(content_output_id)).first()
        if not co:
            logger.error("Content output %s not found for Google Docs publish", content_output_id)
            return

        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user:
            logger.error("User %s not found for Google Docs publish", user_id)
            co.status = "failed"
            co.error_message = "Approving user not found"
            db.commit()
            return

        service = GoogleDocsService()
        service.create_or_update_doc(db, co, user)
        logger.info("Google Docs publish complete for output %s", content_output_id)
    except Exception as e:
        logger.exception("Google Docs publish failed for output %s", content_output_id)
        co = db.query(ContentOutput).filter(ContentOutput.id == uuid.UUID(content_output_id)).first()
        if co:
            co.status = "failed"
            co.error_message = f"Google Docs publish failed: {str(e)}"
            db.commit()
    finally:
        db.close()



# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------

@router.get("", response_model=list[ContentOutputResponse])
def list_content_outputs(
    competitor_id: Optional[str] = Query(None),
    content_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List content outputs with optional filters."""
    query = db.query(ContentOutput).options(joinedload(ContentOutput.competitor))

    if competitor_id:
        query = query.filter(ContentOutput.competitor_id == uuid.UUID(competitor_id))
    if content_type:
        query = query.filter(ContentOutput.content_type == content_type)
    if status:
        query = query.filter(ContentOutput.status == status)

    outputs = query.order_by(ContentOutput.updated_at.desc()).all()
    return [_output_to_response(co) for co in outputs]


@router.get("/stale", response_model=list[StaleContentItem])
def get_stale_content(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get stale and missing content items.

    Stale: a competitor has approved analysis cards newer than the latest
    published/approved content_output for that content_type.
    Missing: a competitor has content_types configured but no content_output at all.
    """
    competitors = db.query(Competitor).filter(Competitor.is_active == True).all()
    results: list[dict] = []

    for comp in competitors:
        configured_types = comp.content_types or []
        if not isinstance(configured_types, list):
            continue

        for ct in configured_types:
            # Find latest content output for this competitor + content_type
            latest_co = (
                db.query(ContentOutput)
                .filter(
                    ContentOutput.competitor_id == comp.id,
                    ContentOutput.content_type == ct,
                    ContentOutput.status.in_(["approved", "published"]),
                )
                .order_by(ContentOutput.updated_at.desc())
                .first()
            )

            if not latest_co:
                # Missing: no content output exists
                results.append({
                    "competitor_id": str(comp.id),
                    "competitor_name": comp.name,
                    "content_type": ct,
                    "status": "missing",
                    "days_stale": None,
                    "latest_content_id": None,
                })
                continue

            # Check if there are approved analysis cards newer than the content output
            latest_card = (
                db.query(AnalysisCard)
                .join(AnalysisCardCompetitor)
                .filter(
                    AnalysisCardCompetitor.competitor_id == comp.id,
                    AnalysisCard.status == "approved",
                    AnalysisCard.approved_at > latest_co.updated_at,
                )
                .order_by(AnalysisCard.approved_at.desc())
                .first()
            )

            if latest_card:
                days_stale = (datetime.now(timezone.utc) - latest_co.updated_at.replace(tzinfo=timezone.utc)).days
                results.append({
                    "competitor_id": str(comp.id),
                    "competitor_name": comp.name,
                    "content_type": ct,
                    "status": "stale",
                    "days_stale": days_stale,
                    "latest_content_id": str(latest_co.id),
                })

    return results


@router.get("/{output_id}", response_model=ContentOutputResponse)
def get_content_output(
    output_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single content output by ID."""
    co = (
        db.query(ContentOutput)
        .options(joinedload(ContentOutput.competitor))
        .filter(ContentOutput.id == uuid.UUID(output_id))
        .first()
    )
    if not co:
        raise HTTPException(status_code=404, detail="Content output not found")
    return _output_to_response(co)


@router.post("/generate", response_model=GenerateResponse, status_code=202)
def generate_content(
    body: ContentOutputCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Kick off content generation for a competitor + template.

    Creates a ContentOutput in 'generating' status and runs LLM generation
    as a background task. Returns 202 immediately.
    """
    # Validate competitor exists
    competitor = db.query(Competitor).filter(Competitor.id == uuid.UUID(body.competitor_id)).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    # Validate template exists and is active
    template = db.query(ContentTemplate).filter(
        ContentTemplate.id == uuid.UUID(body.template_id),
        ContentTemplate.is_active == True,
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found or inactive")

    # Create content output record
    co = ContentOutput(
        competitor_id=uuid.UUID(body.competitor_id),
        content_type=template.content_type,
        title="",
        content="",
        version=1,
        status="generating",
        template_id=uuid.UUID(body.template_id),
    )
    db.add(co)
    db.commit()
    db.refresh(co)

    # Run generation in background
    background_tasks.add_task(
        _run_content_generation,
        str(co.id),
        body.competitor_id,
        body.template_id,
    )

    return {
        "id": str(co.id),
        "status": "generating",
        "message": "Content generation started. Poll GET /{id} for status.",
    }


@router.put("/{output_id}", response_model=ContentOutputResponse)
def update_content_output(
    output_id: str,
    body: ContentOutputUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update editable fields of a content output (title, content)."""
    co = (
        db.query(ContentOutput)
        .options(joinedload(ContentOutput.competitor))
        .filter(ContentOutput.id == uuid.UUID(output_id))
        .first()
    )
    if not co:
        raise HTTPException(status_code=404, detail="Content output not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(co, field, value)

    db.commit()
    db.refresh(co)
    return _output_to_response(co)


@router.patch("/{output_id}/status", response_model=ContentOutputResponse)
def update_content_output_status(
    output_id: str,
    body: StatusUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change the status of a content output.

    Approval requires admin role and triggers Google Docs publish as a background task.
    """
    if body.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(sorted(VALID_STATUSES))}",
        )

    co = (
        db.query(ContentOutput)
        .options(joinedload(ContentOutput.competitor))
        .filter(ContentOutput.id == uuid.UUID(output_id))
        .first()
    )
    if not co:
        raise HTTPException(status_code=404, detail="Content output not found")

    # Approval requires admin
    if body.status == "approved":
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Only admins can approve content")
        co.approved_by = current_user.id
        co.approved_at = datetime.now(timezone.utc)

    co.status = body.status
    db.commit()
    db.refresh(co)

    # Trigger Google Docs publish on approval
    if body.status == "approved":
        background_tasks.add_task(
            _run_google_docs_publish,
            str(co.id),
            str(current_user.id),
        )

    return _output_to_response(co)