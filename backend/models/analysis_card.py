from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, Text, Boolean, ForeignKey, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class AnalysisCard(Base):
    __tablename__ = "analysis_cards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feed_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("feed_items.id"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(
        SAEnum(
            "new_feature", "product_announcement", "partnership", "acquisition",
            "acquired", "funding", "pricing_change", "leadership_change", "expansion", "other",
            name="event_type",
        ),
        nullable=False,
    )
    priority: Mapped[str] = mapped_column(
        SAEnum("red", "yellow", "green", name="priority_level"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    impact_assessment: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_counter_moves: Mapped[str] = mapped_column(Text, nullable=False)
    raw_llm_output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(
        SAEnum("draft", "in_review", "approved", "archived", name="card_status"),
        default="draft",
        nullable=False,
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(nullable=True)
    check_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("check_runs.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now(), nullable=False)

    feed_item = relationship("FeedItem")
    approver = relationship("User")
    check_run = relationship("CheckRun")
    competitors = relationship("Competitor", secondary="analysis_card_competitors", backref="analysis_cards")
    edits = relationship("AnalysisCardEdit", back_populates="analysis_card")
    comments = relationship("AnalysisCardComment", back_populates="analysis_card")


class AnalysisCardCompetitor(Base):
    __tablename__ = "analysis_card_competitors"

    analysis_card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analysis_cards.id"), primary_key=True
    )
    competitor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("competitors.id"), primary_key=True
    )


class AnalysisCardEdit(Base):
    __tablename__ = "analysis_card_edits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analysis_cards.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    field_changed: Mapped[str] = mapped_column(String, nullable=False)
    previous_value: Mapped[str] = mapped_column(Text, nullable=False)
    new_value: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    analysis_card = relationship("AnalysisCard", back_populates="edits")
    user = relationship("User")


class AnalysisCardComment(Base):
    __tablename__ = "analysis_card_comments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analysis_cards.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    parent_comment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analysis_card_comments.id"), nullable=True
    )
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now(), nullable=False)

    analysis_card = relationship("AnalysisCard", back_populates="comments")
    user = relationship("User")
    replies = relationship("AnalysisCardComment", backref="parent", remote_side=[id])

