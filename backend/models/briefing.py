from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, Text, ForeignKey, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Briefing(Base):
    __tablename__ = "briefings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    raw_llm_output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(
        SAEnum("draft", "in_review", "approved", "archived", name="briefing_status"),
        default="draft",
        nullable=False,
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now(), nullable=False)

    approver = relationship("User")
    cards = relationship("AnalysisCard", secondary="briefing_cards", backref="briefings")


class BriefingCard(Base):
    __tablename__ = "briefing_cards"

    briefing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("briefings.id"), primary_key=True
    )
    analysis_card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analysis_cards.id"), primary_key=True
    )

