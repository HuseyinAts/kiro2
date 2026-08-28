"""quality_review_status v3 convention — add bronze_clean status

Trigger: 14 May 2026 Quality Pool Plan v1 Faz 1.6 — Bronze tier sistemi.
Convention v2'den (qrs_v2_20260515) tek fark: 'bronze_clean' status eklenir.
Pipeline-fix uygulanmış ama judge'a girmemiş satırlar için tier marker.

Bkz: docs/quality_review_status_convention_v3.md

Revision ID: qrs_v3_20260514
Revises: qrs_v2_20260515
Create Date: 2026-05-14

NOT: Bu migration data migration YAPMAZ — sadece CHECK constraint'i günceller.
Faz 1.6 (Bronze tier promotion) data migration'ını ayrı bir adımda yapar.
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers
revision = "qrs_v3_20260514"
down_revision = "qrs_v2_20260515"
branch_labels = None
depends_on = None


VALID_STATUSES_V3 = (
    "pending",
    "unverified",
    "legacy_v3_unaudited",
    "bronze_clean",  # YENİ — pipeline-fix passed, judge için hazır
    "human_verified",
    "auto_judged_high",
    "rejected",
    "archived",
)


def upgrade() -> None:
    """v2 constraint'i drop, v3 ile değiştir (bronze_clean dahil)."""
    conn = op.get_bind()

    # Pre-flight: v2 constraint mevcut mu?
    res = conn.execute(
        sa.text(
            "SELECT conname FROM pg_constraint "
            "WHERE conrelid = 'public.question_bank'::regclass "
            "AND contype = 'c' "
            "AND pg_get_constraintdef(oid) ILIKE '%quality_review_status%'"
        )
    )
    existing_constraint = res.scalar()

    if existing_constraint:
        conn.execute(
            sa.text(
                f"ALTER TABLE public.question_bank "
                f"DROP CONSTRAINT {existing_constraint}"
            )
        )

    # v3 CHECK constraint
    valid_list = ", ".join(f"'{s}'" for s in VALID_STATUSES_V3)
    conn.execute(
        sa.text(
            f"""
            ALTER TABLE public.question_bank
            ADD CONSTRAINT quality_review_status_v3_check
            CHECK (quality_review_status IN ({valid_list}))
            """
        )
    )


def downgrade() -> None:
    """v2'ye geri dön (bronze_clean status'unu kaldır).

    Önce bronze_clean satırlarını unverified'a çevir (CHECK violation onleme).
    Sonra v2 constraint'i geri yükle.
    """
    conn = op.get_bind()

    # bronze_clean satırlarını unverified'a geri çevir
    conn.execute(
        sa.text(
            "UPDATE question_bank "
            "SET quality_review_status = 'unverified', updated_at = NOW() "
            "WHERE quality_review_status = 'bronze_clean'"
        )
    )

    # v3 constraint'i drop
    conn.execute(
        sa.text(
            "ALTER TABLE public.question_bank "
            "DROP CONSTRAINT IF EXISTS quality_review_status_v3_check"
        )
    )

    # v2 constraint'i geri yükle (bronze_clean YOK)
    valid_v2 = (
        "pending",
        "unverified",
        "legacy_v3_unaudited",
        "human_verified",
        "auto_judged_high",
        "rejected",
        "archived",
    )
    valid_list = ", ".join(f"'{s}'" for s in valid_v2)
    conn.execute(
        sa.text(
            f"""
            ALTER TABLE public.question_bank
            ADD CONSTRAINT quality_review_status_v2_check
            CHECK (quality_review_status IN ({valid_list}))
            """
        )
    )
