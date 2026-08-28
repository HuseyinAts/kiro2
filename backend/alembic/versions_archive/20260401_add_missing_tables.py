"""Add missing tables: fsrs_cards, daily_quests, study_sessions

ORM'de tanim var ama DB'de eksik olan 3 tablo:
- fsrs_cards       (fsrs_models.py:FSRSCard)
- daily_quests     (gamification.py:DailyQuest)
- study_sessions   (learning_path_models.py:StudySession)

NOT: fsrs_cards op.execute() ile olusturuluyor — subjectarea enum DB'de zaten mevcut,
     sa.Enum create_type=False parametresi op.create_table() icinde etkisiz.
     study_sessions: study_room.py versiyonu atildi (study_rooms FK tablosu yok).

Revision ID: 20260401_add_missing_tables
Revises: freeze_baseline_20260401
Create Date: 2026-04-01
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "20260401_add_missing_tables"
down_revision: Union[str, None] = "freeze_baseline_20260401"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. fsrs_cards — raw SQL (subjectarea enum zaten DB'de var)
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE fsrs_cards (
            id              VARCHAR         NOT NULL PRIMARY KEY,
            student_id      VARCHAR         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            front_text      TEXT            NOT NULL,
            back_text       TEXT            NOT NULL,
            subject_area    subjectarea     NOT NULL,
            topic           VARCHAR(200)    NOT NULL,
            stability       FLOAT           NOT NULL DEFAULT 0.0,
            difficulty      FLOAT           NOT NULL DEFAULT 0.0,
            elapsed_days    INTEGER         NOT NULL DEFAULT 0,
            scheduled_days  INTEGER         NOT NULL DEFAULT 0,
            reps            INTEGER         NOT NULL DEFAULT 0,
            lapses          INTEGER         NOT NULL DEFAULT 0,
            state           VARCHAR(20)     NOT NULL DEFAULT 'new',
            due_date        TIMESTAMPTZ     NOT NULL,
            last_review     TIMESTAMPTZ,
            cultural_factors JSONB,
            created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX idx_fsrs_card_student ON fsrs_cards (student_id)")
    op.execute("CREATE INDEX idx_fsrs_card_due     ON fsrs_cards (due_date)")
    op.execute("CREATE INDEX idx_fsrs_card_subject ON fsrs_cards (subject_area)")
    op.execute("CREATE INDEX idx_fsrs_card_state   ON fsrs_cards (state)")

    # ------------------------------------------------------------------
    # 2. daily_quests  (gamification.py:DailyQuest)
    # ------------------------------------------------------------------
    op.create_table(
        "daily_quests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("quest_date", sa.Date(), nullable=False),
        sa.Column(
            "student_id",
            sa.String(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("quest_type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_value", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("current_value", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("xp_reward", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "bonus_claimed", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "quest_date", "student_id", "quest_type", name="uq_daily_quest"
        ),
    )
    op.create_index("idx_daily_quest_student", "daily_quests", ["student_id"])
    op.create_index("idx_daily_quest_date", "daily_quests", ["quest_date"])

    # ------------------------------------------------------------------
    # 3. study_sessions  (learning_path_models.py:StudySession)
    #    FK: learning_path_student_profiles.student_id  (tablo mevcut)
    # ------------------------------------------------------------------
    op.create_table(
        "study_sessions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column(
            "student_id",
            sa.String(100),
            sa.ForeignKey(
                "learning_path_student_profiles.student_id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column(
            "started_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column(
            "topics_studied",
            sa.JSON(),
            nullable=True,
            server_default=sa.text("'[]'::json"),
        ),
        sa.Column(
            "questions_answered", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("correct_count", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_session_student_started", "study_sessions", ["student_id", "started_at"]
    )


def downgrade() -> None:
    op.drop_index("idx_session_student_started", table_name="study_sessions")
    op.drop_table("study_sessions")

    op.drop_index("idx_daily_quest_date", table_name="daily_quests")
    op.drop_index("idx_daily_quest_student", table_name="daily_quests")
    op.drop_table("daily_quests")

    op.execute("DROP INDEX IF EXISTS idx_fsrs_card_state")
    op.execute("DROP INDEX IF EXISTS idx_fsrs_card_subject")
    op.execute("DROP INDEX IF EXISTS idx_fsrs_card_due")
    op.execute("DROP INDEX IF EXISTS idx_fsrs_card_student")
    op.drop_table("fsrs_cards")
