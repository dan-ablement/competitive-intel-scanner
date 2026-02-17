"""add_twitter_support

Revision ID: 003
Revises: 002
Create Date: 2026-02-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Extend feed_type ENUM with 'twitter' value
    op.execute("ALTER TYPE feed_type ADD VALUE 'twitter'")

    # 2. Drop UNIQUE constraint on rss_feeds.url (Twitter sources have null URLs)
    op.drop_constraint("rss_feeds_url_key", "rss_feeds", type_="unique")

    # 3. Make rss_feeds.url nullable
    op.alter_column("rss_feeds", "url", existing_type=sa.String(), nullable=True)

    # 4. Create twitter_source_config table
    op.create_table(
        "twitter_source_config",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("feed_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rss_feeds.id"), unique=True, nullable=False),
        sa.Column("x_username", sa.String(), nullable=False),
        sa.Column("x_user_id", sa.String(), nullable=True),
        sa.Column("last_tweet_id", sa.String(), nullable=True),
        sa.Column("initial_backfill_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("backfill_completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("include_retweets", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("include_replies", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # 5. Add raw_metadata JSONB column to feed_items
    op.add_column("feed_items", sa.Column("raw_metadata", postgresql.JSONB(), nullable=True))

    # 6. Make feed_items.title nullable
    op.alter_column("feed_items", "title", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    # Reverse order of upgrade operations

    # 6. Re-add NOT NULL on feed_items.title
    op.alter_column("feed_items", "title", existing_type=sa.String(), nullable=False)

    # 5. Drop raw_metadata column from feed_items
    op.drop_column("feed_items", "raw_metadata")

    # 4. Drop twitter_source_config table
    op.drop_table("twitter_source_config")

    # 3. Re-add NOT NULL on rss_feeds.url
    op.alter_column("rss_feeds", "url", existing_type=sa.String(), nullable=False)

    # 2. Re-add UNIQUE constraint on rss_feeds.url
    op.create_unique_constraint("rss_feeds_url_key", "rss_feeds", ["url"])

    # Note: Cannot remove 'twitter' from feed_type ENUM in PostgreSQL easily.
    # The value is harmless and left in place.

