"""content_generation

Revision ID: 004
Revises: 003
Create Date: 2026-02-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add new values to content_output_status ENUM
    # PostgreSQL ALTER TYPE ... ADD VALUE cannot run inside a transaction block.
    op.execute("COMMIT")
    op.execute("ALTER TYPE content_output_status ADD VALUE 'in_review'")
    op.execute("ALTER TYPE content_output_status ADD VALUE 'failed'")

    # 2. Create content_templates table
    op.create_table(
        "content_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("content_type", sa.String(), unique=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sections", postgresql.JSONB(), nullable=True),
        sa.Column("doc_name_pattern", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # 3. Add new columns to content_outputs
    op.add_column("content_outputs", sa.Column("title", sa.String(), nullable=True))
    op.add_column(
        "content_outputs",
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("content_templates.id"),
            nullable=True,
        ),
    )
    op.add_column("content_outputs", sa.Column("google_doc_id", sa.String(), nullable=True))
    op.add_column("content_outputs", sa.Column("google_doc_url", sa.String(), nullable=True))
    op.add_column(
        "content_outputs",
        sa.Column(
            "approved_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
    )
    op.add_column("content_outputs", sa.Column("approved_at", sa.DateTime(), nullable=True))
    op.add_column("content_outputs", sa.Column("published_at", sa.DateTime(), nullable=True))
    op.add_column("content_outputs", sa.Column("raw_llm_output", postgresql.JSONB(), nullable=True))
    op.add_column("content_outputs", sa.Column("error_message", sa.Text(), nullable=True))

    # 4. Add Google OAuth token columns to users
    op.add_column("users", sa.Column("google_refresh_token", sa.String(), nullable=True))
    op.add_column("users", sa.Column("google_access_token", sa.String(), nullable=True))

    # 5. Seed default "Competitive Battle Card" template
    op.execute("""
        INSERT INTO content_templates (id, content_type, name, description, sections, doc_name_pattern, is_active, created_at, updated_at)
        VALUES (
            gen_random_uuid(),
            'battle_card',
            'Competitive Battle Card',
            'A comprehensive competitive battle card for sales and GTM teams',
            '[
                {"title": "Company Overview", "description": "Brief overview of the competitor company", "prompt_hint": "Summarize the competitor''s mission, size, funding, and market position"},
                {"title": "Key Products & Services", "description": "Main products and services offered", "prompt_hint": "List and describe the competitor''s key products, features, and target use cases"},
                {"title": "Strengths & Weaknesses", "description": "Competitive strengths and weaknesses", "prompt_hint": "Analyze the competitor''s key strengths and weaknesses relative to the market"},
                {"title": "How They Compare to Augment", "description": "Direct comparison with Augment Code", "prompt_hint": "Compare the competitor''s offerings directly against Augment Code''s capabilities"},
                {"title": "Recent Competitive Developments", "description": "Latest news and developments", "prompt_hint": "Summarize recent product launches, partnerships, funding rounds, or strategic moves"},
                {"title": "Recommended Talking Points", "description": "Sales talking points and objection handling", "prompt_hint": "Provide specific talking points for sales conversations and common objection responses"},
                {"title": "Pricing Comparison", "description": "Pricing model comparison", "prompt_hint": "Compare pricing tiers, models, and value propositions"}
            ]'::jsonb,
            'Battle Card - {competitor}',
            true,
            NOW(),
            NOW()
        )
    """)


def downgrade() -> None:
    # Reverse order of upgrade operations

    # 5. Delete seeded template (no-op if already deleted)
    op.execute("DELETE FROM content_templates WHERE content_type = 'battle_card'")

    # 4. Drop Google OAuth token columns from users
    op.drop_column("users", "google_access_token")
    op.drop_column("users", "google_refresh_token")

    # 3. Drop new columns from content_outputs
    op.drop_column("content_outputs", "error_message")
    op.drop_column("content_outputs", "raw_llm_output")
    op.drop_column("content_outputs", "published_at")
    op.drop_column("content_outputs", "approved_at")
    op.drop_column("content_outputs", "approved_by")
    op.drop_column("content_outputs", "google_doc_url")
    op.drop_column("content_outputs", "google_doc_id")
    op.drop_column("content_outputs", "template_id")
    op.drop_column("content_outputs", "title")

    # 2. Drop content_templates table
    op.drop_table("content_templates")

    # 1. Remove 'in_review' and 'failed' from content_output_status ENUM
    # PostgreSQL cannot simply remove values from an ENUM. We must:
    # a) Create a new enum type with only the original values
    # b) Migrate the column to use the new type
    # c) Drop the old type and rename the new one
    op.execute("UPDATE content_outputs SET status = 'draft' WHERE status IN ('in_review', 'failed')")
    op.execute("ALTER TYPE content_output_status RENAME TO content_output_status_old")
    op.execute("CREATE TYPE content_output_status AS ENUM ('draft', 'approved', 'published')")
    op.execute(
        "ALTER TABLE content_outputs ALTER COLUMN status TYPE content_output_status "
        "USING status::text::content_output_status"
    )
    op.execute("DROP TYPE content_output_status_old")
