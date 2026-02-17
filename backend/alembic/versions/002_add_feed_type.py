"""add_feed_type_and_css_selector

Revision ID: 002
Revises: 001
Create Date: 2026-02-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the feed_type enum type
    feed_type_enum = sa.Enum("rss", "web_scrape", name="feed_type")
    feed_type_enum.create(op.get_bind(), checkfirst=True)

    # Add feed_type column with default 'rss' for existing rows
    op.add_column(
        "rss_feeds",
        sa.Column(
            "feed_type",
            sa.Enum("rss", "web_scrape", name="feed_type", create_type=False),
            nullable=False,
            server_default="rss",
        ),
    )

    # Add css_selector column (nullable, only used for web_scrape feeds)
    op.add_column(
        "rss_feeds",
        sa.Column("css_selector", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("rss_feeds", "css_selector")
    op.drop_column("rss_feeds", "feed_type")

    # Drop the enum type
    feed_type_enum = sa.Enum("rss", "web_scrape", name="feed_type")
    feed_type_enum.drop(op.get_bind(), checkfirst=True)

