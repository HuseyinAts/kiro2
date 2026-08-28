"""Formalize 4-Level Taxonomy for Knowledge Components and Topic Hierarchy

Revision ID: level4_kc_taxonomy_20260808
Revises: 0a9560c892c0
Create Date: 2026-08-08 16:35:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "level4_kc_taxonomy_20260808"
down_revision = "0a9560c892c0"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Ensure knowledge_components table exists with enhanced 4-level taxonomy fields
    op.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_components (
            kc_id VARCHAR PRIMARY KEY,
            kc_name VARCHAR NOT NULL,
            parent_topic_id VARCHAR REFERENCES topic_hierarchy(id) ON DELETE SET NULL,
            parent_kc_id VARCHAR REFERENCES knowledge_components(kc_id) ON DELETE SET NULL,
            level INTEGER DEFAULT 4,
            taxonomy_level INTEGER DEFAULT 4,
            code VARCHAR(100),
            meb_code VARCHAR(100),
            description TEXT,
            bkt_p_init NUMERIC DEFAULT 0.4,
            bkt_p_transit NUMERIC DEFAULT 0.12,
            bkt_p_guess NUMERIC DEFAULT 0.20,
            bkt_p_slip NUMERIC DEFAULT 0.10,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Add missing columns safely if table already existed
    op.execute(
        "ALTER TABLE knowledge_components ADD COLUMN IF NOT EXISTS parent_kc_id VARCHAR REFERENCES knowledge_components(kc_id) ON DELETE SET NULL"
    )
    op.execute(
        "ALTER TABLE knowledge_components ADD COLUMN IF NOT EXISTS level INTEGER DEFAULT 4"
    )
    op.execute(
        "ALTER TABLE knowledge_components ADD COLUMN IF NOT EXISTS taxonomy_level INTEGER DEFAULT 4"
    )
    op.execute(
        "ALTER TABLE knowledge_components ADD COLUMN IF NOT EXISTS code VARCHAR(100)"
    )
    op.execute(
        "ALTER TABLE knowledge_components ADD COLUMN IF NOT EXISTS meb_code VARCHAR(100)"
    )

    # Create indexes for fast KC traversal and taxonomy lookup
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_kc_parent_topic ON knowledge_components(parent_topic_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_kc_parent_kc ON knowledge_components(parent_kc_id)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_kc_level ON knowledge_components(level)")

    # 2. Ensure question_kc_mapping table exists with is_primary flag
    op.execute("""
        CREATE TABLE IF NOT EXISTS question_kc_mapping (
            question_id VARCHAR NOT NULL,
            kc_id VARCHAR NOT NULL REFERENCES knowledge_components(kc_id) ON DELETE CASCADE,
            weight NUMERIC DEFAULT 1.0,
            is_primary BOOLEAN DEFAULT FALSE,
            PRIMARY KEY (question_id, kc_id)
        )
    """)

    op.execute(
        "ALTER TABLE question_kc_mapping ADD COLUMN IF NOT EXISTS is_primary BOOLEAN DEFAULT FALSE"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_qkc_question ON question_kc_mapping(question_id)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_qkc_kc ON question_kc_mapping(kc_id)")


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_qkc_kc")
    op.execute("DROP INDEX IF EXISTS idx_qkc_question")
    op.execute("DROP TABLE IF EXISTS question_kc_mapping CASCADE")
    op.execute("DROP INDEX IF EXISTS idx_kc_level")
    op.execute("DROP INDEX IF EXISTS idx_kc_parent_kc")
    op.execute("DROP INDEX IF EXISTS idx_kc_parent_topic")
    op.execute("DROP TABLE IF EXISTS knowledge_components CASCADE")
