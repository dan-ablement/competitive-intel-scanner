from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Competitor(Base):
    __tablename__ = "competitors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    key_products: Mapped[str] = mapped_column(Text, nullable=False)
    target_customers: Mapped[str] = mapped_column(Text, nullable=False)
    known_strengths: Mapped[str] = mapped_column(Text, nullable=False)
    known_weaknesses: Mapped[str] = mapped_column(Text, nullable=False)
    augment_overlap: Mapped[str] = mapped_column(Text, nullable=False)
    pricing: Mapped[str] = mapped_column(Text, nullable=False)
    content_types: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_suggested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    suggested_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now(), nullable=False)

    creator = relationship("User")
    feeds = relationship("RSSFeed", back_populates="competitor")

