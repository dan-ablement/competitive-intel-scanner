from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.check_run import CheckRun
from backend.services.briefing_generator import BriefingGenerator
from backend.services.feed_checker import FeedChecker
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_run_to_response(cr: CheckRun) -> dict:
    """Serialize a CheckRun model to a dict matching CheckRunResponse."""
    return {
        "id": str(cr.id),
        "scheduled_time": cr.scheduled_time.isoformat() if cr.scheduled_time else None,
        "started_at": cr.started_at.isoformat() if cr.started_at else None,
        "completed_at": cr.completed_at.isoformat() if cr.completed_at else None,
        "status": cr.status,
        "feeds_checked": cr.feeds_checked,
        "new_items_found": cr.new_items_found,
        "cards_generated": cr.cards_generated,
        "error_log": cr.error_log,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/check-feeds", response_model=CheckRunResponse)
def trigger_check_feeds(
    generate_briefing: bool = Query(False, description="Generate a morning briefing after the feed check"),
    db: Session = Depends(get_db),
):
    """Trigger a full feed check run.

    Creates a check_run, iterates all active feeds, fetches and parses RSS,
    inserts new feed_items (deduped by guid), and updates the check_run with
    counts and status.

    Pass generate_briefing=true to also generate a daily briefing from recent cards
    (intended for the 9:05 AM morning run).
    """
    try:
        checker = FeedChecker(db)
        check_run = checker.run()

        # Generate briefing if requested (e.g., morning 9:05 AM run)
        if generate_briefing:
            try:
                generator = BriefingGenerator()
                briefing = generator.generate_briefing(db)
                if briefing:
                    logger.info("Morning briefing generated: %s", briefing.id)
                else:
                    logger.info("No briefing generated (no recent cards or already exists)")
            except Exception as briefing_exc:
                logger.exception("Briefing generation failed (feed check still succeeded)")
                # Don't fail the whole check-feeds response; briefing is supplementary

        return _check_run_to_response(check_run)
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
        {"time": "12:05 AM ET", "cron": "5 0 * * *", "purpose": "Overnight check"},
        {"time": "9:05 AM ET", "cron": "5 9 * * *", "purpose": "Morning check + briefing"},
        {"time": "12:05 PM ET", "cron": "5 12 * * *", "purpose": "Midday check"},
        {"time": "5:05 PM ET", "cron": "5 17 * * *", "purpose": "End of business check"},
        {"time": "8:05 PM ET", "cron": "5 20 * * *", "purpose": "Evening check"},
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