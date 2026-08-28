"""Create user_item_fsrs table

Revision ID: user_item_fsrs_001
Revises: 20260406_create_missing_tables
Create Date: 2026-04-10
"""

from alembic import op

revision = "user_item_fsrs_001"
down_revision = "20260406_create_missing_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_item_fsrs (
            user_id        TEXT        NOT NULL,
            question_id    UUID        NOT NULL,
            stability      FLOAT       NOT NULL DEFAULT 0.0,
            difficulty     FLOAT       NOT NULL DEFAULT 0.0,
            due_date       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_review    TIMESTAMPTZ,
            state          INTEGER     NOT NULL DEFAULT 0,
            reps           INTEGER     NOT NULL DEFAULT 0,
            lapses         INTEGER     NOT NULL DEFAULT 0,
            scheduled_days INTEGER     NOT NULL DEFAULT 0,
            elapsed_days   INTEGER     NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, question_id)
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_uif_user_due "
        "ON user_item_fsrs (user_id, due_date)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_uif_user_due")
    op.execute("DROP TABLE IF EXISTS user_item_fsrs")
