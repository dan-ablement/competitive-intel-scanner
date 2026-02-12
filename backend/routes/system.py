from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.check_run import CheckRun
from backend.services.feed_checker import FeedChecker

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
def trigger_check_feeds(db: Session = Depends(get_db)):
    """Trigger a full feed check run.

    Creates a check_run, iterates all active feeds, fetches and parses RSS,
    inserts new feed_items (deduped by guid), and updates the check_run with
    counts and status.
    """
    try:
        checker = FeedChecker(db)
        check_run = checker.run()
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
