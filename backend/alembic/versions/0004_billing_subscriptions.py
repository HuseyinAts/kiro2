"""billing_subscriptions tablosunu aktif zincire geri getir

Revision ID: 0004_billing_subscriptions
Revises: f1954b057565

NOT: revision kimligi 32 karakteri asamaz -- `alembic_version.version_num`
kolonu VARCHAR(32). Ilk denemede "0004_restore_billing_subscriptions" (33
karakter) `StringDataRightTruncation` ile dustu (islem geri sarildi, sema
degismedi).

Create Date: 2026-09-09

KOK NEDEN
---------
`billing_subscriptions` tablosunu yaratan migration
(`versions_archive/20260423_billing_subscriptions_mvp.py`) baseline squash
sirasinda arsive tasindi. `0001_baseline_squash.py` bu tabloyu icermiyor,
cunku squash o anki DB durumunu dondurdu ve tablo o an zaten yoktu
(`versions_archive/c555a10f4b93_sync_db_changes.py` icindeki 145 adet
`DROP TABLE IF EXISTS ... CASCADE` ile dusurulmustu).

Sonuc: temiz bir kurulumda `alembic upgrade head` bu tabloyu HIC
olusturmuyor.

OLCUM (9 Eyl 2026)
------------------
- Tablo canli DB'de yok (`pg_tables` sorgusu).
- `backend/api/billing_api.py:62` SELECT, `:118` INSERT ile bu tabloyu
  raw SQL ile sorguluyor.
- Router kayitli: `backend/routers/loader.py:33`
  `"api.billing_api": ("security", "api.billing_api")`.
- Dolayisiyla `GET /api/v1/billing/me` `UndefinedTableError` -> 500.
- CI bunu zaten yakaliyor: PR #218 Backend Tests (job 102289449141)
  `tests/e2e/test_db_schema_parity.py::test_critical_tables_exist` dusuyor.

Ayni testin `CRITICAL_TABLES` listesindeki diger bes tablo
(`student_question_flags`, `teacher_classroom_students`,
`teacher_exam_configs`, `teacher_assignments`, `teacher_contents`) DB'de
mevcut; eksik olan yalnizca `billing_subscriptions`. Bu migration'in kapsami
bilincli olarak o tek tablo.

Tablo tanimi `20260423_billing_subscriptions_mvp.py`'den BIREBIR alindi --
bu bir restore, yeniden tasarim degil. `IF NOT EXISTS` korumasi sayesinde
tablonun zaten bulundugu ortamlarda (varsa) islemsizdir.
"""

from collections.abc import Sequence
from typing import Union

from alembic import op

revision: str = "0004_billing_subscriptions"
down_revision: Union[str, None] = "f1954b057565"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS billing_subscriptions (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL UNIQUE
                REFERENCES users(id) ON DELETE CASCADE,
            plan_code VARCHAR(32) NOT NULL DEFAULT 'free',
            status VARCHAR(24) NOT NULL DEFAULT 'inactive',
            provider VARCHAR(32),
            external_customer_id VARCHAR(255),
            current_period_end TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_billing_subscriptions_user_id
        ON billing_subscriptions (user_id);
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_billing_subscriptions_user_id")
    op.execute("DROP TABLE IF EXISTS billing_subscriptions")
