"""Fix gamification FK types: Integer -> VARCHAR for users.id and topic_hierarchy.id

users.id is UUID (String), topic_hierarchy.id is String — all FK columns referencing
these tables must use VARCHAR, not INTEGER.

Covers: realm_progress, streaks, xp_transactions, oba_uyeler, user_badges,
        duels, parent_child, student_abilities

Revision ID: d3e4f5a6b7c8
Revises: c1d2e3f4a5b6
Create Date: 2026-03-20
"""

from alembic import op

revision = "d3e4f5a6b7c8"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # realm_progress
    op.execute(
        "ALTER TABLE realm_progress "
        "ALTER COLUMN student_id TYPE VARCHAR USING student_id::text"
    )

    # streaks
    op.execute(
        "ALTER TABLE streaks ALTER COLUMN user_id TYPE VARCHAR USING user_id::text"
    )

    # xp_transactions
    op.execute(
        "ALTER TABLE xp_transactions "
        "ALTER COLUMN student_id TYPE VARCHAR USING student_id::text, "
        "ALTER COLUMN topic_id TYPE VARCHAR USING topic_id::text"
    )

    # oba_uyeler
    op.execute(
        "ALTER TABLE oba_uyeler ALTER COLUMN user_id TYPE VARCHAR USING user_id::text"
    )

    # user_badges
    op.execute(
        "ALTER TABLE user_badges ALTER COLUMN user_id TYPE VARCHAR USING user_id::text"
    )

    # duels
    op.execute(
        "ALTER TABLE duels "
        "ALTER COLUMN player1_id TYPE VARCHAR USING player1_id::text, "
        "ALTER COLUMN player2_id TYPE VARCHAR USING player2_id::text, "
        "ALTER COLUMN topic_id TYPE VARCHAR USING topic_id::text"
    )

    # parent_child
    op.execute(
        "ALTER TABLE parent_child "
        "ALTER COLUMN parent_id TYPE VARCHAR USING parent_id::text, "
        "ALTER COLUMN child_id TYPE VARCHAR USING child_id::text"
    )

    # student_abilities
    op.execute(
        "ALTER TABLE student_abilities "
        "ALTER COLUMN student_id TYPE VARCHAR USING student_id::text"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE realm_progress "
        "ALTER COLUMN student_id TYPE INTEGER USING student_id::integer"
    )
    op.execute(
        "ALTER TABLE streaks ALTER COLUMN user_id TYPE INTEGER USING user_id::integer"
    )
    op.execute(
        "ALTER TABLE xp_transactions "
        "ALTER COLUMN student_id TYPE INTEGER USING student_id::integer, "
        "ALTER COLUMN topic_id TYPE INTEGER USING topic_id::integer"
    )
    op.execute(
        "ALTER TABLE oba_uyeler "
        "ALTER COLUMN user_id TYPE INTEGER USING user_id::integer"
    )
    op.execute(
        "ALTER TABLE user_badges "
        "ALTER COLUMN user_id TYPE INTEGER USING user_id::integer"
    )
    op.execute(
        "ALTER TABLE duels "
        "ALTER COLUMN player1_id TYPE INTEGER USING player1_id::integer, "
        "ALTER COLUMN player2_id TYPE INTEGER USING player2_id::integer, "
        "ALTER COLUMN topic_id TYPE INTEGER USING topic_id::integer"
    )
    op.execute(
        "ALTER TABLE parent_child "
        "ALTER COLUMN parent_id TYPE INTEGER USING parent_id::integer, "
        "ALTER COLUMN child_id TYPE INTEGER USING child_id::integer"
    )
    op.execute(
        "ALTER TABLE student_abilities "
        "ALTER COLUMN student_id TYPE INTEGER USING student_id::integer"
    )
