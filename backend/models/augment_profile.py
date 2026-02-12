from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class AugmentProfile(Base):
    __tablename__ = "augment_profile"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_description: Mapped[str] = mapped_column(Text, nullable=False)
    key_differentiators: Mapped[str] = mapped_column(Text, nullable=False)
    target_customer_segments: Mapped[str] = mapped_column(Text, nullable=False)
    product_capabilities: Mapped[str] = mapped_column(Text, nullable=False)
    strategic_priorities: Mapped[str] = mapped_column(Text, nullable=False)
    pricing: Mapped[str] = mapped_column(Text, nullable=False)
    updated_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now(), nullable=False)

    updater = relationship("User")

