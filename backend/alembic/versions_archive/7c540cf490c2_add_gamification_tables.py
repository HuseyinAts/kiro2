"""add_gamification_tables

FAZ-2 Gorev 2.1 — Master Plan v2.0
Tablolar: bkt_states, realms, realm_progress, streaks, xp_transactions,
          obalar, oba_uyeler, badges, user_badges, duels, parent_child,
          student_abilities
User tablosuna: elo_rating, is_parent kolonlari
question_bank tablosuna: irt_a, irt_b, irt_c, irt_calibrated kolonlari

NOT: users.id ve topic_hierarchy.id = VARCHAR (Integer degil!)

Revision ID: 7c540cf490c2
Revises: qz_fk_qbank_001
Create Date: 2026-03-20
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "7c540cf490c2"
down_revision: Union[str, None] = "qz_fk_qbank_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# users.id ve topic_hierarchy.id VARCHAR oldugundan FK'lar da VARCHAR
UID = sa.String(36)  # UUID veya UUID benzeri VARCHAR user ID
TID = sa.String(36)  # topic_hierarchy.id VARCHAR


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # 1. question_bank: IRT parametreleri (idempotent kontrol)
    # ------------------------------------------------------------------
    existing_cols = {
        row[0]
        for row in conn.execute(
            sa.text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='question_bank'"
            )
        )
    }
    for col_name, col_type in [
        ("irt_a", "NUMERIC(6,4)"),
        ("irt_b", "NUMERIC(6,4)"),
        ("irt_c", "NUMERIC(5,4)"),
        ("irt_calibrated", "BOOLEAN DEFAULT false"),
    ]:
        if col_name not in existing_cols:
            conn.execute(
                sa.text(f"ALTER TABLE question_bank ADD COLUMN {col_name} {col_type}")
            )

    # ------------------------------------------------------------------
    # 2. users: Gamification ek kolonlar (idempotent)
    # ------------------------------------------------------------------
    user_cols = {
        row[0]
        for row in conn.execute(
            sa.text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='users'"
            )
        )
    }
    if "elo_rating" not in user_cols:
        conn.execute(
            sa.text(
                "ALTER TABLE users ADD COLUMN elo_rating INTEGER DEFAULT 1000 NOT NULL"
            )
        )
    if "is_parent" not in user_cols:
        conn.execute(
            sa.text(
                "ALTER TABLE users ADD COLUMN is_parent BOOLEAN DEFAULT false NOT NULL"
            )
        )

    # ------------------------------------------------------------------
    # 3. student_abilities
    # ------------------------------------------------------------------
    conn.execute(
        sa.text("""
        CREATE TABLE IF NOT EXISTS student_abilities (
            student_id  VARCHAR(36) NOT NULL REFERENCES users(id),
            subject_id  INTEGER NOT NULL,
            theta       NUMERIC(6,4) NOT NULL DEFAULT 0.0,
            theta_se    NUMERIC(6,4) NOT NULL DEFAULT 1.0,
            updated_at  TIMESTAMPTZ DEFAULT now(),
            PRIMARY KEY (student_id, subject_id)
        )
    """)
    )

    # ------------------------------------------------------------------
    # 4. bkt_states
    # ------------------------------------------------------------------
    conn.execute(
        sa.text("""
        CREATE TABLE IF NOT EXISTS bkt_states (
            student_id      VARCHAR(36) NOT NULL REFERENCES users(id),
            topic_id        VARCHAR(36) NOT NULL,
            p_learn         NUMERIC(5,4) NOT NULL DEFAULT 0.05,
            p_transit       NUMERIC(5,4) NOT NULL DEFAULT 0.10,
            p_guess         NUMERIC(5,4) NOT NULL DEFAULT 0.20,
            p_slip          NUMERIC(5,4) NOT NULL DEFAULT 0.10,
            attempt_count   INTEGER NOT NULL DEFAULT 0,
            mastery_status  VARCHAR(20) NOT NULL DEFAULT 'learning',
            last_attempt    TIMESTAMPTZ,
            created_at      TIMESTAMPTZ DEFAULT now(),
            PRIMARY KEY (student_id, topic_id)
        )
    """)
    )

    # ------------------------------------------------------------------
    # 5. realms
    # ------------------------------------------------------------------
    conn.execute(
        sa.text("""
        CREATE TABLE IF NOT EXISTS realms (
            id              SERIAL PRIMARY KEY,
            slug            VARCHAR(50) UNIQUE NOT NULL,
            name            VARCHAR(100) NOT NULL,
            era             VARCHAR(150),
            npc_name        VARCHAR(100),
            npc_title       VARCHAR(100),
            tech_stack      JSONB,
            color_primary   VARCHAR(7),
            color_secondary VARCHAR(7),
            order_index     INTEGER,
            is_active       BOOLEAN NOT NULL DEFAULT true
        )
    """)
    )

    # ------------------------------------------------------------------
    # 6. realm_progress
    # ------------------------------------------------------------------
    conn.execute(
        sa.text("""
        CREATE TABLE IF NOT EXISTS realm_progress (
            id          SERIAL PRIMARY KEY,
            student_id  VARCHAR(36) NOT NULL REFERENCES users(id),
            realm_id    INTEGER NOT NULL REFERENCES realms(id),
            bkt_score   NUMERIC(5,4) NOT NULL DEFAULT 0.0,
            quest_stop  INTEGER NOT NULL DEFAULT 0,
            xp_earned   INTEGER NOT NULL DEFAULT 0,
            completed_at TIMESTAMPTZ,
            unlocked_at TIMESTAMPTZ DEFAULT now(),
            UNIQUE(student_id, realm_id)
        )
    """)
    )

    # ------------------------------------------------------------------
    # 7. streaks
    # ------------------------------------------------------------------
    conn.execute(
        sa.text("""
        CREATE TABLE IF NOT EXISTS streaks (
            user_id          VARCHAR(36) NOT NULL REFERENCES users(id),
            current_streak   INTEGER NOT NULL DEFAULT 0,
            largest_streak   INTEGER NOT NULL DEFAULT 0,
            freeze_count     INTEGER NOT NULL DEFAULT 2,
            last_activity    DATE,
            total_days_active INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id)
        )
    """)
    )

    # ------------------------------------------------------------------
    # 8. xp_transactions
    # ------------------------------------------------------------------
    conn.execute(
        sa.text("""
        CREATE TABLE IF NOT EXISTS xp_transactions (
            id          SERIAL PRIMARY KEY,
            student_id  VARCHAR(36) NOT NULL REFERENCES users(id),
            amount      INTEGER NOT NULL,
            source      VARCHAR(20) NOT NULL,
            topic_id    VARCHAR(36),
            created_at  TIMESTAMPTZ DEFAULT now()
        )
    """)
    )

    # ------------------------------------------------------------------
    # 9. obalar
    # ------------------------------------------------------------------
    conn.execute(
        sa.text("""
        CREATE TABLE IF NOT EXISTS obalar (
            id          SERIAL PRIMARY KEY,
            name        VARCHAR(100) NOT NULL,
            description TEXT,
            xp_pool     INTEGER NOT NULL DEFAULT 0,
            max_members INTEGER NOT NULL DEFAULT 20,
            created_at  TIMESTAMPTZ DEFAULT now()
        )
    """)
    )

    # ------------------------------------------------------------------
    # 10. oba_uyeler
    # ------------------------------------------------------------------
    conn.execute(
        sa.text("""
        CREATE TABLE IF NOT EXISTS oba_uyeler (
            id          SERIAL PRIMARY KEY,
            oba_id      INTEGER NOT NULL REFERENCES obalar(id),
            user_id     VARCHAR(36) NOT NULL REFERENCES users(id),
            role        VARCHAR(10) NOT NULL DEFAULT 'toycu',
            joined_at   TIMESTAMPTZ DEFAULT now(),
            UNIQUE(user_id)
        )
    """)
    )

    # ------------------------------------------------------------------
    # 11. badges
    # ------------------------------------------------------------------
    conn.execute(
        sa.text("""
        CREATE TABLE IF NOT EXISTS badges (
            id          SERIAL PRIMARY KEY,
            slug        VARCHAR(50) UNIQUE NOT NULL,
            name        VARCHAR(100) NOT NULL,
            description TEXT,
            icon        VARCHAR(10),
            category    VARCHAR(20),
            condition   JSONB
        )
    """)
    )

    # ------------------------------------------------------------------
    # 12. user_badges (DROP ve yeniden olustur eski yapidan temizle)
    # ------------------------------------------------------------------
    existing_tables = {
        row[0]
        for row in conn.execute(
            sa.text("SELECT tablename FROM pg_tables WHERE schemaname='public'")
        )
    }
    if "user_badges" in existing_tables:
        # Eski yapida badge_id yoksa dropp edip yeniden olustur
        ub_cols = {
            row[0]
            for row in conn.execute(
                sa.text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name='user_badges'"
                )
            )
        }
        if "badge_id" not in ub_cols:
            conn.execute(sa.text("DROP TABLE user_badges CASCADE"))
            existing_tables.discard("user_badges")

    if "user_badges" not in existing_tables:
        conn.execute(
            sa.text("""
            CREATE TABLE user_badges (
                id          SERIAL PRIMARY KEY,
                user_id     VARCHAR(36) NOT NULL REFERENCES users(id),
                badge_id    INTEGER NOT NULL REFERENCES badges(id),
                earned_at   TIMESTAMPTZ DEFAULT now(),
                UNIQUE(user_id, badge_id)
            )
        """)
        )

    # ------------------------------------------------------------------
    # 13. duels
    # ------------------------------------------------------------------
    conn.execute(
        sa.text("""
        CREATE TABLE IF NOT EXISTS duels (
            id              SERIAL PRIMARY KEY,
            player1_id      VARCHAR(36) NOT NULL REFERENCES users(id),
            player2_id      VARCHAR(36) NOT NULL REFERENCES users(id),
            topic_id        VARCHAR(36) NOT NULL,
            status          VARCHAR(20) NOT NULL DEFAULT 'pending',
            winner_id       VARCHAR(36),
            player1_score   INTEGER NOT NULL DEFAULT 0,
            player2_score   INTEGER NOT NULL DEFAULT 0,
            elo_delta       INTEGER NOT NULL DEFAULT 0,
            created_at      TIMESTAMPTZ DEFAULT now(),
            completed_at    TIMESTAMPTZ
        )
    """)
    )

    # ------------------------------------------------------------------
    # 14. parent_child
    # ------------------------------------------------------------------
    conn.execute(
        sa.text("""
        CREATE TABLE IF NOT EXISTS parent_child (
            id          SERIAL PRIMARY KEY,
            parent_id   VARCHAR(36) NOT NULL REFERENCES users(id),
            child_id    VARCHAR(36) NOT NULL REFERENCES users(id),
            created_at  TIMESTAMPTZ DEFAULT now(),
            UNIQUE(parent_id, child_id)
        )
    """)
    )

    # ------------------------------------------------------------------
    # Indexes
    # ------------------------------------------------------------------
    for idx_sql in [
        "CREATE INDEX IF NOT EXISTS idx_bkt_states_student ON bkt_states(student_id)",
        "CREATE INDEX IF NOT EXISTS idx_realm_progress_student ON realm_progress(student_id)",
        "CREATE INDEX IF NOT EXISTS idx_xp_transactions_student ON xp_transactions(student_id)",
        "CREATE INDEX IF NOT EXISTS idx_xp_transactions_created ON xp_transactions(created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_duels_player1 ON duels(player1_id)",
        "CREATE INDEX IF NOT EXISTS idx_duels_player2 ON duels(player2_id)",
    ]:
        conn.execute(sa.text(idx_sql))


def downgrade() -> None:
    conn = op.get_bind()
    for tbl in [
        "parent_child",
        "duels",
        "user_badges",
        "badges",
        "oba_uyeler",
        "obalar",
        "xp_transactions",
        "streaks",
        "realm_progress",
        "realms",
        "bkt_states",
        "student_abilities",
    ]:
        conn.execute(sa.text(f"DROP TABLE IF EXISTS {tbl} CASCADE"))
    for col in ["is_parent", "elo_rating"]:
        conn.execute(sa.text(f"ALTER TABLE users DROP COLUMN IF EXISTS {col}"))
    for col in ["irt_calibrated", "irt_c", "irt_b", "irt_a"]:
        conn.execute(sa.text(f"ALTER TABLE question_bank DROP COLUMN IF EXISTS {col}"))
