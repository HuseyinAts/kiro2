"""Create topic_prerequisites table

Revision ID: topic_prereqs_001
Revises: cat_sessions_001
Create Date: 2026-03-29

"""

from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "topic_prereqs_001"
down_revision: Union[str, None] = "cat_sessions_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS topic_prerequisites (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            topic_id TEXT NOT NULL,
            prereq_id TEXT NOT NULL,
            prereq_type TEXT NOT NULL DEFAULT 'hard',
            strength NUMERIC NOT NULL DEFAULT 1.0,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            FOREIGN KEY (topic_id) REFERENCES topic_hierarchy(id),
            FOREIGN KEY (prereq_id) REFERENCES topic_hierarchy(id)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_topic_prereqs_topic
        ON topic_prerequisites(topic_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_topic_prereqs_active
        ON topic_prerequisites(is_active) WHERE is_active = TRUE
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_topic_prereqs_active")
    op.execute("DROP INDEX IF EXISTS idx_topic_prereqs_topic")
    op.execute("DROP TABLE IF EXISTS topic_prerequisites")
