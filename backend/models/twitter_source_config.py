from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class TwitterSourceConfig(Base):
    __tablename__ = "twitter_source_config"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feed_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rss_feeds.id"), unique=True, nullable=False
    )
    x_username: Mapped[str] = mapped_column(String, nullable=False)
    x_user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    last_tweet_id: Mapped[str | None] = mapped_column(String, nullable=True)
    initial_backfill_days: Mapped[int] = mapped_column(Integer, default=30, server_default="30", nullable=False)
    backfill_completed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    include_retweets: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    include_replies: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now(), nullable=False)

    feed: Mapped[RSSFeed] = relationship("RSSFeed", back_populates="twitter_config")

