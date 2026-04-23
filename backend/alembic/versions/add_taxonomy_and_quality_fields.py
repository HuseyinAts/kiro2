"""Add taxonomy and quality fields to sorular table.

Adds: solo_level, marzano_system, marzano_cognitive_level, webb_dok_level,
taxonomy_consistency_score, cognitive_load_estimate, difficulty_trend,
linked_misconceptions, turkish_readability_index

Revision ID: add_taxonomy_fields
Revises: f822e22c28c6
Create Date: 2026-02-06
"""
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers
revision = "add_taxonomy_fields"
down_revision = "f822e22c28c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name='sorular')"
        )
    )
    if not result.scalar():
        print("  SKIP add_taxonomy_fields: 'sorular' table does not exist")
        return

    # Taxonomy fields
    op.add_column("sorular", sa.Column("solo_level", sa.String(), nullable=True))
    op.add_column("sorular", sa.Column("marzano_system", sa.String(), nullable=True))
    op.add_column(
        "sorular", sa.Column("marzano_cognitive_level", sa.String(), nullable=True)
    )
    op.add_column("sorular", sa.Column("webb_dok_level", sa.String(), nullable=True))
    op.add_column(
        "sorular", sa.Column("taxonomy_consistency_score", sa.Float(), nullable=True)
    )

    # Quality fields
    op.add_column(
        "sorular", sa.Column("cognitive_load_estimate", sa.Float(), nullable=True)
    )
    op.add_column("sorular", sa.Column("difficulty_trend", sa.String(), nullable=True))
    op.add_column(
        "sorular", sa.Column("linked_misconceptions", JSONB(), nullable=True)
    )
    op.add_column(
        "sorular", sa.Column("turkish_readability_index", sa.Float(), nullable=True)
    )


def downgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name='sorular')"
        )
    )
    if not result.scalar():
        return

    op.drop_column("sorular", "turkish_readability_index")
    op.drop_column("sorular", "linked_misconceptions")
    op.drop_column("sorular", "difficulty_trend")
    op.drop_column("sorular", "cognitive_load_estimate")
    op.drop_column("sorular", "taxonomy_consistency_score")
    op.drop_column("sorular", "webb_dok_level")
    op.drop_column("sorular", "marzano_cognitive_level")
    op.drop_column("sorular", "marzano_system")
    op.drop_column("sorular", "solo_level")
