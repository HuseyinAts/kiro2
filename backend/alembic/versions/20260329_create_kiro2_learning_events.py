"""Create kiro2_learning_events table

Revision ID: learning_events_001
Revises: topic_prereqs_001
Create Date: 2026-03-29

"""

from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "learning_events_001"
down_revision: Union[str, None] = "topic_prereqs_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS kiro2_learning_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL,
            question_id TEXT NOT NULL,
            session_id UUID,
            event_type TEXT NOT NULL DEFAULT 'cat_answer',
            is_correct BOOLEAN,
            theta_after NUMERIC,
            response_ms INTEGER,
            occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_learning_events_user
        ON kiro2_learning_events(user_id, occurred_at DESC)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_learning_events_session
        ON kiro2_learning_events(session_id)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_learning_events_session")
    op.execute("DROP INDEX IF EXISTS idx_learning_events_user")
    op.execute("DROP TABLE IF EXISTS kiro2_learning_events")
