from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db, SessionLocal
from backend.utils import utc_isoformat
from backend.models.check_run import CheckRun
from backend.services.briefing_generator import BriefingGenerator
from backend.services.feed_checker import FeedChecker
from backend.services.llm_analyzer import LLMAnalyzer
from backend.services.profile_reviewer import ProfileReviewer

router = APIRouter()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class CheckRunResponse(BaseModel):
    id: str
    scheduled_time: str
    started_at: str
    completed_at: Optional[str]
    status: str
    feeds_checked: int
    new_items_found: int
    cards_generated: int
    error_log: Optional[str]
    briefing_id: Optional[str] = None
    briefing_error: Optional[str] = None
    analysis_status: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_run_to_response(
    cr: CheckRun,
    briefing_id: str | None = None,
    briefing_error: str | None = None,
    analysis_status: str | None = None,
) -> dict:
    """Serialize a CheckRun model to a dict matching CheckRunResponse."""
    return {
        "id": str(cr.id),
        "scheduled_time": utc_isoformat(cr.scheduled_time),
        "started_at": utc_isoformat(cr.started_at),
        "completed_at": utc_isoformat(cr.completed_at),
        "status": cr.status,
        "feeds_checked": cr.feeds_checked,
        "new_items_found": cr.new_items_found,
        "cards_generated": cr.cards_generated,
        "error_log": cr.error_log,
        "briefing_id": briefing_id,
        "briefing_error": briefing_error,
        "analysis_status": analysis_status,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

def _run_background_analysis(
    check_run_id: str,
    generate_briefing: bool,
) -> None:
    """Background task: run LLM analysis and optional briefing generation.

    Uses its own DB session so it's independent of the HTTP request lifecycle.
    """
    import uuid as _uuid

    db = SessionLocal()
    try:
        # LLM analysis
        analyzer = LLMAnalyzer()
        cards_generated = analyzer.process_unprocessed_items(
            db, check_run_id=_uuid.UUID(check_run_id),
        )
        logger.info("Background LLM analysis complete: %d cards generated for check_run %s", cards_generated, check_run_id)

        # Update check_run with analysis results
        check_run = db.query(CheckRun).filter(CheckRun.id == _uuid.UUID(check_run_id)).first()
        if check_run:
            check_run.cards_generated = cards_generated

        # Briefing generation if requested
        if generate_briefing:
            try:
                generator = BriefingGenerator()
                briefing = generator.generate_briefing(db)
                if briefing:
                    logger.info("Background briefing generated: %s", briefing.id)
                else:
                    logger.info("No briefing generated (no recent cards or already exists)")
            except Exception:
                logger.exception("Background briefing generation failed")

        db.commit()
    except Exception:
        logger.exception("Background analysis failed for check_run %s", check_run_id)
    finally:
        db.close()


@router.post("/check-feeds", response_model=CheckRunResponse)
def trigger_check_feeds(
    background_tasks: BackgroundTasks,
    generate_briefing: bool = Query(False, description="Generate a morning briefing after the feed check"),
    db: Session = Depends(get_db),
):
    """Trigger a full feed check run.

    Feed fetching (RSS parsing, web scraping, Twitter polling) runs synchronously
    and the response is returned immediately. LLM analysis and briefing generation
    run as background tasks so Cloud Scheduler sees a quick 200 response.

    Pass generate_briefing=true to also generate a daily briefing from recent cards
    (intended for the 9:05 AM morning run).
    """
    try:
        checker = FeedChecker(db)
        check_run, new_items_total = checker.run_fetch_only()

        # Determine analysis status
        if new_items_total > 0:
            # Queue LLM analysis + optional briefing as a background task
            background_tasks.add_task(
                _run_background_analysis,
                check_run_id=str(check_run.id),
                generate_briefing=generate_briefing,
            )
            analysis_status = "pending"
        else:
            analysis_status = "complete"

        return _check_run_to_response(
            check_run,
            analysis_status=analysis_status,
        )
    except Exception as exc:
        logger.exception("Feed check run failed unexpectedly")
        raise HTTPException(status_code=500, detail=f"Feed check failed: {str(exc)}")


@router.get("/check-runs", response_model=list[CheckRunResponse])
def list_check_runs(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List check run history, most recent first."""
    runs = (
        db.query(CheckRun)
        .order_by(CheckRun.started_at.desc())
        .limit(limit)
        .all()
    )
    return [_check_run_to_response(cr) for cr in runs]



# ---------------------------------------------------------------------------
# Profile Review
# ---------------------------------------------------------------------------

class ProfileReviewResponse(BaseModel):
    message: str
    competitor_suggestions: int
    augment_suggestions: int
    total: int


@router.post("/maintenance/review-profiles", response_model=ProfileReviewResponse)
def trigger_profile_review(db: Session = Depends(get_db)):
    """Trigger a weekly profile review.

    Reviews all competitor profiles and the Augment profile against
    recent approved analysis cards, generating update suggestions.
    """
    try:
        reviewer = ProfileReviewer(db)
        result = reviewer.run()
        return ProfileReviewResponse(
            message=f"Profile review complete. {result['total']} suggestions generated.",
            **result,
        )
    except Exception as exc:
        logger.exception("Profile review failed")
        raise HTTPException(status_code=500, detail=f"Profile review failed: {str(exc)}")


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

# Read-only schedule configuration (matches Cloud Scheduler setup)
SCHEDULE_CONFIG = {
    "feed_checks": [
        {"time": "12:05 AM ET", "cron": "5 0 * * 1-5", "purpose": "Overnight check"},
        {"time": "9:05 AM ET", "cron": "5 9 * * 1-5", "purpose": "Morning check + briefing"},
        {"time": "12:05 PM ET", "cron": "5 12 * * 1-5", "purpose": "Midday check"},
        {"time": "5:05 PM ET", "cron": "5 17 * * 1-5", "purpose": "End of business check"},
        {"time": "8:05 PM ET", "cron": "5 20 * * 1-5", "purpose": "Evening check"},
    ],
    "maintenance": {
        "profile_review": {
            "time": "Sundays 10:00 AM ET",
            "cron": "0 10 * * 0",
            "purpose": "Weekly profile review",
        },
    },
    "content_types": [
        "new_feature",
        "product_announcement",
        "partnership",
        "acquisition",
        "acquired",
        "funding",
        "pricing_change",
        "leadership_change",
        "expansion",
        "other",
    ],
    "admins": [
        "diacono@augmentcode.com",
        "mollie@augmentcode.com",
        "mattarnold@augmentcode.com",
    ],
}


class SettingsResponse(BaseModel):
    feed_checks: list[dict]
    maintenance: dict
    content_types: list[str]
    admins: list[str]


@router.get("/settings", response_model=SettingsResponse)
def get_settings():
    """Get system settings (schedule configuration, content types, admins)."""
    return SCHEDULE_CONFIG


@router.put("/settings", response_model=SettingsResponse)
def update_settings(payload: dict):
    """Update system settings.

    Currently read-only — schedule is managed via Cloud Scheduler.
    Returns the current settings unchanged.
    """
    # Settings are read-only for now (managed via Cloud Scheduler / env vars).
    # In the future, this could persist to a settings table.
    return SCHEDULE_CONFIG