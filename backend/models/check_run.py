from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Integer, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class CheckRun(Base):
    __tablename__ = "check_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheduled_time: Mapped[datetime] = mapped_column(nullable=False)
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(
        SAEnum("running", "completed", "failed", name="check_run_status"),
        nullable=False,
    )
    feeds_checked: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_items_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cards_generated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_log: Mapped[str | None] = mapped_column(Text, nullable=True)

