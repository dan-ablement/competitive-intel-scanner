"""initial_schema

Revision ID: 001
Revises:
Create Date: 2026-02-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(), unique=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("role", sa.Enum("admin", "reviewer", "viewer", name="user_role"), nullable=False, server_default="viewer"),
        sa.Column("google_id", sa.String(), unique=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # competitors
    op.create_table(
        "competitors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), unique=True, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("key_products", sa.Text(), nullable=False),
        sa.Column("target_customers", sa.Text(), nullable=False),
        sa.Column("known_strengths", sa.Text(), nullable=False),
        sa.Column("known_weaknesses", sa.Text(), nullable=False),
        sa.Column("augment_overlap", sa.Text(), nullable=False),
        sa.Column("pricing", sa.Text(), nullable=False),
        sa.Column("content_types", postgresql.JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_suggested", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("suggested_reason", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # rss_feeds
    op.create_table(
        "rss_feeds",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("url", sa.String(), unique=True, nullable=False),
        sa.Column("competitor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("competitors.id"), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_checked_at", sa.DateTime(), nullable=True),
        sa.Column("last_successful_at", sa.DateTime(), nullable=True),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # feed_items
    op.create_table(
        "feed_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("feed_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rss_feeds.id"), nullable=False),
        sa.Column("guid", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("author", sa.String(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=False),
        sa.Column("raw_content", sa.Text(), nullable=False),
        sa.Column("is_processed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_relevant", sa.Boolean(), nullable=True),
        sa.Column("irrelevance_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("feed_id", "guid", name="uq_feed_items_feed_guid"),
    )

    # augment_profile
    op.create_table(
        "augment_profile",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_description", sa.Text(), nullable=False),
        sa.Column("key_differentiators", sa.Text(), nullable=False),
        sa.Column("target_customer_segments", sa.Text(), nullable=False),
        sa.Column("product_capabilities", sa.Text(), nullable=False),
        sa.Column("strategic_priorities", sa.Text(), nullable=False),
        sa.Column("pricing", sa.Text(), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # check_runs
    op.create_table(
        "check_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scheduled_time", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.Enum("running", "completed", "failed", name="check_run_status"), nullable=False),
        sa.Column("feeds_checked", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("new_items_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cards_generated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_log", sa.Text(), nullable=True),
    )


    # analysis_cards
    op.create_table(
        "analysis_cards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("feed_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("feed_items.id"), nullable=True),
        sa.Column("event_type", sa.Enum(
            "new_feature", "product_announcement", "partnership", "acquisition",
            "acquired", "funding", "pricing_change", "leadership_change", "expansion", "other",
            name="event_type",
        ), nullable=False),
        sa.Column("priority", sa.Enum("red", "yellow", "green", name="priority_level"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("impact_assessment", sa.Text(), nullable=False),
        sa.Column("suggested_counter_moves", sa.Text(), nullable=False),
        sa.Column("raw_llm_output", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.Enum("draft", "in_review", "approved", "archived", name="card_status"), nullable=False, server_default="draft"),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("check_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("check_runs.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # analysis_card_competitors
    op.create_table(
        "analysis_card_competitors",
        sa.Column("analysis_card_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analysis_cards.id"), primary_key=True),
        sa.Column("competitor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("competitors.id"), primary_key=True),
    )

    # analysis_card_edits
    op.create_table(
        "analysis_card_edits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("analysis_card_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analysis_cards.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("field_changed", sa.String(), nullable=False),
        sa.Column("previous_value", sa.Text(), nullable=False),
        sa.Column("new_value", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # analysis_card_comments
    op.create_table(
        "analysis_card_comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("analysis_card_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analysis_cards.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("parent_comment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analysis_card_comments.id"), nullable=True),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # briefings
    op.create_table(
        "briefings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("date", sa.Date(), unique=True, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("raw_llm_output", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.Enum("draft", "in_review", "approved", "archived", name="briefing_status"), nullable=False, server_default="draft"),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # briefing_cards
    op.create_table(
        "briefing_cards",
        sa.Column("briefing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("briefings.id"), primary_key=True),
        sa.Column("analysis_card_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analysis_cards.id"), primary_key=True),
    )

    # profile_update_suggestions
    op.create_table(
        "profile_update_suggestions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("target_type", sa.Enum("competitor", "augment", name="suggestion_target_type"), nullable=False),
        sa.Column("competitor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("competitors.id"), nullable=True),
        sa.Column("field", sa.String(), nullable=False),
        sa.Column("current_value", sa.Text(), nullable=False),
        sa.Column("suggested_value", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("source_card_ids", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.Enum("pending", "approved", "rejected", name="suggestion_status"), nullable=False, server_default="pending"),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # content_outputs
    op.create_table(
        "content_outputs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("competitor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("competitors.id"), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_card_ids", postgresql.JSONB(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.Enum("draft", "approved", "published", name="content_output_status"), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("content_outputs")
    op.drop_table("profile_update_suggestions")
    op.drop_table("briefing_cards")
    op.drop_table("briefings")
    op.drop_table("analysis_card_comments")
    op.drop_table("analysis_card_edits")
    op.drop_table("analysis_card_competitors")
    op.drop_table("analysis_cards")
    op.drop_table("check_runs")
    op.drop_table("augment_profile")
    op.drop_table("feed_items")
    op.drop_table("rss_feeds")
    op.drop_table("competitors")
    op.drop_table("users")
    op.execute("DROP TYPE content_output_status")
    op.execute("DROP TYPE suggestion_status")
    op.execute("DROP TYPE suggestion_target_type")
    op.execute("DROP TYPE check_run_status")
    op.execute("DROP TYPE briefing_status")
    op.execute("DROP TYPE card_status")
    op.execute("DROP TYPE priority_level")
    op.execute("DROP TYPE event_type")
    op.execute("DROP TYPE user_role")
