"""create_missing_learning_path_tables

Kok neden (041a9181271c'nin uyardigi drift): `daily_plans`, `yks_exam_goals`,
`learning_progress_daily` bu ortamda hic yoktu. Alembic gecmisinde hicbir
migration bunlari yaratmiyor -- sadece faz1_rls2_20260704 / faz1_katmanBC_20260704
listelerinde (org_id + RLS toplu-islem) uye olarak geciyorlar. Gercek CREATE
TABLE tanimlari `backend/migrations/005_learning_path.sql` (2026-03-24) ve
`016_...daily_plans.sql` (2026-04-01) altinda -- alembic'e HIC entegre
edilmemis, izlenmeyen ham-SQL migration klasoru.

Bu ozellikler OLU DEGIL: canli kod bunlara bagimli ve su an KIRIK:
  - tasks/daily_plan_tasks.py: gecelik 02:00 Celery beat, yks_exam_goals'tan
    SELECT ile basliyor -> tablo yok -> her gece kalici fail (retry 2x sonra).
  - app/api/learning_path_daily.py: POST /learning-path/goal + gunluk plan
    varsayilan hedef okuma -> 500.
  - api/pwa_sync_api.py + api/enhanced_user_management_api.py:
    learning_progress_daily upsert/okuma -> 500.

Sema kaynagi: 005'in VARCHAR(users.id) tasarimi (016'nin UUID+FK tasarimi
users.id VARCHAR ile TYPE MISMATCH, hic calismamis olmali) + 016'nin
`yks_exam_goals` tablo adi (canli kod bunu sorguluyor, 005'in `student_goals`
adi FARKLI bir tablo -- zaten var, alakasiz "hedef takibi" ozelligi).

`learning_progress_daily`'nin UNIQUE(user_id, log_date, subject, activity_type)
kisitlamasi BILEREK isimsiz birakildi: api/pwa_sync_api.py
`ON CONFLICT ON CONSTRAINT
learning_progress_daily_user_id_log_date_subject_activity_t_key`
literal adiyla cagiriyor -- Postgres'in ayni tablo/kolon sirasiyla
otomatik uretecegi (63 karaktere kesilmis) ad ile birebir eslesmesi icin
elle isim VERILMEDI.

`organization_id` + RLS: bu 3 tablo zaten FAIL_CLOSED_TABLES (041a9181271c)
kapsaminda taniniyordu (73'luk fail-closed set), `data_processing_agreements`
PERMISSIVE_ORG_ID_TABLES kapsaminda -- ayni migration'da tablolar
yaratildigi/kolon eklendigi icin varlik kontrolu gerekmiyor (ayni transaction).

Revision ID: cdea871deea9
Revises: 041a9181271c
Create Date: 2026-08-13
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "cdea871deea9"
down_revision: Union[str, None] = "041a9181271c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LEGACY_ORG = "org_legacy_default"

FAIL_CLOSED_PRED = "organization_id = current_setting('app.current_org_id', true)"
PERMISSIVE_PRED = (
    "current_setting('app.current_org_id', true) IS NULL "
    "OR current_setting('app.current_org_id', true) = '' "
    "OR organization_id = current_setting('app.current_org_id', true)"
)


def _rls_fail_closed(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY tenant_isolation ON {table} FOR ALL "
        f"USING ({FAIL_CLOSED_PRED}) WITH CHECK ({FAIL_CLOSED_PRED})"
    )


def upgrade() -> None:
    # ── yks_exam_goals — bkz. app/api/learning_path_daily.py, daily_plan_tasks.py ──
    op.execute(f"""
        CREATE TABLE yks_exam_goals (
            user_id            VARCHAR NOT NULL PRIMARY KEY
                                REFERENCES users(id) ON DELETE CASCADE,
            organization_id    VARCHAR NOT NULL DEFAULT '{LEGACY_ORG}'
                                REFERENCES organizations(id) ON DELETE RESTRICT,
            exam_type          VARCHAR(20) NOT NULL DEFAULT 'TYT'
                                CHECK (exam_type IN
                                    ('TYT','AYT_SAY','AYT_EA','AYT_SOZ')),
            exam_date          DATE NOT NULL,
            daily_minutes      INTEGER NOT NULL DEFAULT 120
                                CHECK (daily_minutes BETWEEN 30 AND 480),
            target_university  VARCHAR(200),
            target_department  VARCHAR(200),
            created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute(
        "CREATE INDEX idx_yks_exam_goals_organization_id "
        "ON yks_exam_goals(organization_id)"
    )

    # ── daily_plans — bkz. tasks/daily_plan_tasks.py ──────────────────────────
    op.execute(f"""
        CREATE TABLE daily_plans (
            id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id            VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            organization_id    VARCHAR NOT NULL DEFAULT '{LEGACY_ORG}'
                                REFERENCES organizations(id) ON DELETE RESTRICT,
            plan_date          DATE NOT NULL,
            exam_date          DATE NOT NULL,
            days_remaining     INTEGER NOT NULL,
            total_minutes      INTEGER NOT NULL DEFAULT 0,
            plan_json          JSONB NOT NULL DEFAULT '{{}}',
            weak_subject       VARCHAR(50),
            strong_subject     VARCHAR(50),
            motivational_note  TEXT,
            generated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (user_id, plan_date)
        )
    """)
    op.execute(
        "CREATE INDEX idx_daily_plans_user_date ON daily_plans(user_id, plan_date DESC)"
    )
    op.execute(
        "CREATE INDEX idx_daily_plans_organization_id ON daily_plans(organization_id)"
    )

    # ── learning_progress_daily — bkz. api/pwa_sync_api.py,
    # enhanced_user_management_api.py
    op.execute(f"""
        CREATE TABLE learning_progress_daily (
            id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id            VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            organization_id    VARCHAR NOT NULL DEFAULT '{LEGACY_ORG}'
                                REFERENCES organizations(id) ON DELETE RESTRICT,
            log_date           DATE NOT NULL DEFAULT CURRENT_DATE,
            subject            VARCHAR(50) NOT NULL,
            minutes_spent      INTEGER NOT NULL DEFAULT 0,
            questions_done     INTEGER NOT NULL DEFAULT 0,
            correct_count      INTEGER NOT NULL DEFAULT 0,
            activity_type      VARCHAR(30) NOT NULL DEFAULT 'cat'
                                CHECK (activity_type IN
                                    ('cat','fsrs_review','practice','placement')),
            theta_before       FLOAT,
            theta_after        FLOAT,
            created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (user_id, log_date, subject, activity_type)
        )
    """)
    op.execute(
        "CREATE INDEX idx_progress_user_date "
        "ON learning_progress_daily(user_id, log_date DESC)"
    )
    op.execute(
        "CREATE INDEX idx_progress_organization_id "
        "ON learning_progress_daily(organization_id)"
    )

    for t in ("yks_exam_goals", "daily_plans", "learning_progress_daily"):
        _rls_fail_closed(t)

    # ── data_processing_agreements.organization_id — 041a9181271c'nin atladigi ──
    op.execute(
        "ALTER TABLE data_processing_agreements ADD COLUMN organization_id VARCHAR"
    )
    op.execute(
        sa.text(
            "UPDATE data_processing_agreements SET organization_id = :l "
            "WHERE organization_id IS NULL"
        ).bindparams(l=LEGACY_ORG)
    )
    op.execute(
        "ALTER TABLE data_processing_agreements "
        "ALTER COLUMN organization_id SET NOT NULL"
    )
    op.execute(
        f"ALTER TABLE data_processing_agreements "
        f"ALTER COLUMN organization_id SET DEFAULT '{LEGACY_ORG}'"
    )
    op.execute(
        "ALTER TABLE data_processing_agreements "
        "ADD CONSTRAINT fk_data_processing_agreements_organization "
        "FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT"
    )
    op.execute(
        "CREATE INDEX idx_data_processing_agreements_organization_id "
        "ON data_processing_agreements(organization_id)"
    )
    op.execute("ALTER TABLE data_processing_agreements ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE data_processing_agreements FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON data_processing_agreements FOR ALL "
        f"USING ({PERMISSIVE_PRED}) WITH CHECK ({PERMISSIVE_PRED})"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON data_processing_agreements")
    op.execute("ALTER TABLE data_processing_agreements NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE data_processing_agreements DISABLE ROW LEVEL SECURITY")
    op.execute(
        "ALTER TABLE data_processing_agreements "
        "DROP CONSTRAINT IF EXISTS fk_data_processing_agreements_organization"
    )
    op.execute("DROP INDEX IF EXISTS idx_data_processing_agreements_organization_id")
    op.execute(
        "ALTER TABLE data_processing_agreements DROP COLUMN IF EXISTS organization_id"
    )

    for t in ("yks_exam_goals", "daily_plans", "learning_progress_daily"):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {t}")

    op.execute("DROP TABLE IF EXISTS learning_progress_daily")
    op.execute("DROP TABLE IF EXISTS daily_plans")
    op.execute("DROP TABLE IF EXISTS yks_exam_goals")
