"""quality_review_status v2 convention — drop approved, add legacy_v3_unaudited + human_verified

Trigger: 14 May 2026 audit bulgusu — 'approved' literal hardcoded'du,
manuel onay yoktu, %87 hata oranı. Convention v2'de 'approved' yasaklanır.
Bkz: docs/quality_review_status_convention.md

Revision ID: qrs_v2_20260515
Revises: prepilot_m2_indexes_20260428
Create Date: 2026-05-15

NOT: Bu migration sadece CHECK constraint kuralını günceller. Data
migration ayrı bir adımda yapılır (backend/migrations/D2_legacy_approved_downgrade.sql).
Bu Alembic migration ÇALIŞTIRILMADAN ÖNCE D2 SQL'i Hüseyin tarafından
psql ile koşturulmalı (yoksa CHECK violation tetiklenir).
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers
revision = "qrs_v2_20260515"
down_revision = "prepilot_m2_indexes_20260428"
branch_labels = None
depends_on = None


VALID_STATUSES = (
    "pending",
    "unverified",
    "legacy_v3_unaudited",
    "human_verified",
    "auto_judged_high",
    "rejected",
    "archived",  # Soft delete marker (is_active=False ile birlikte kullanılır)
)


def upgrade() -> None:
    """Drop old constraint (if any) + add new CHECK with v2 values."""
    conn = op.get_bind()

    # Pre-flight: hâlâ 'approved' satırı var mı?
    res = conn.execute(
        sa.text(
            "SELECT COUNT(*) FROM question_bank "
            "WHERE quality_review_status = 'approved'"
        )
    )
    approved_remaining = res.scalar() or 0
    if approved_remaining > 0:
        raise RuntimeError(
            f"qrs_v2_20260515 upgrade aborted: {approved_remaining} satır "
            "hâlâ quality_review_status='approved'. Önce D2 migration'ını "
            "(backend/migrations/D2_legacy_approved_downgrade.sql) "
            "psql ile çalıştır."
        )

    # Mevcut constraint isimleri PostgreSQL'de tahmin edilemez (autogenerate
    # değil, raw SQL ile eklenmiş olabilir). Mevcut olanı drop et.
    conn.execute(
        sa.text(
            """
            DO $$
            DECLARE
                con_name TEXT;
            BEGIN
                SELECT conname INTO con_name
                FROM pg_constraint
                WHERE conrelid = 'public.question_bank'::regclass
                  AND contype = 'c'
                  AND pg_get_constraintdef(oid) ILIKE '%quality_review_status%';
                IF con_name IS NOT NULL THEN
                    EXECUTE format(
                        'ALTER TABLE public.question_bank DROP CONSTRAINT %I',
                        con_name
                    );
                END IF;
            END$$;
            """
        )
    )

    # Yeni CHECK constraint
    valid_list = ", ".join(f"'{s}'" for s in VALID_STATUSES)
    conn.execute(
        sa.text(
            f"""
            ALTER TABLE public.question_bank
            ADD CONSTRAINT quality_review_status_v2_check
            CHECK (quality_review_status IN ({valid_list}))
            """
        )
    )


def downgrade() -> None:
    """Revert to permissive constraint (allow 'approved' again).

    Bu downgrade SADECE acil rollback için. Convention v2'yi kaldırmak
    'approved' yalanını geri getirir — kullanılmaması tavsiye edilir.
    """
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "ALTER TABLE public.question_bank "
            "DROP CONSTRAINT IF EXISTS quality_review_status_v2_check"
        )
    )
    # Eski 'approved'u geri yaz (D2 rollback'i)
    conn.execute(
        sa.text(
            "UPDATE question_bank "
            "SET quality_review_status = 'approved' "
            "WHERE quality_review_status = 'legacy_v3_unaudited'"
        )
    )
