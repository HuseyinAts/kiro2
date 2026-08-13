"""student_question_flags — Faz 7.2 student feedback flag mechanism

Trigger: 17 May 2026 Quality Pool Plan v1 Faz 7.2 — beta'da öğrencilerin
hatalı/tuhaf soruları raporlaması için tablo + endpoint altyapısı.

Beta launch (Faz 7.1) sonrası gerçek student feedback ile LLM-circular
risk mitigasyonu. Faz 4.1 vision findings'den türetilen flag_type'lar:
- wrong_answer: matematik hesap hatası (Faz 4.1 vision %50 fail)
- wrong_topic: Aromat sistemic subject_area bug (%33)
- solution_visible: image içinde "ÇÖZÜM:" görünür (1/77)
- incomplete_text: OCR kesim bugu (false positive)
- other: serbest metin

Revision ID: student_flags_20260517
Revises: qrs_v3_20260514
Create Date: 2026-05-17
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers
revision = "student_flags_20260517"
down_revision = "qrs_v3_20260514"
branch_labels = None
depends_on = None


VALID_FLAG_TYPES = (
    "wrong_answer",
    "wrong_topic",
    "solution_visible",
    "incomplete_text",
    "other",
)

VALID_RESOLUTIONS = (
    "confirmed",
    "rejected",
    "duplicate",
)


from core.alembic_utils import safe_create_index, safe_create_table


def upgrade() -> None:
    """student_question_flags tablosu oluştur."""
    safe_create_table(
        "student_question_flags",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("question_id", sa.String(), nullable=False),
        sa.Column("flag_type", sa.String(length=32), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution", sa.String(length=32), nullable=True),
        sa.Column("resolved_by", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["question_id"], ["question_bank.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "flag_type IN " + str(VALID_FLAG_TYPES),
            name="student_question_flags_flag_type_check",
        ),
        sa.CheckConstraint(
            "(resolution IS NULL) OR (resolution IN " + str(VALID_RESOLUTIONS) + ")",
            name="student_question_flags_resolution_check",
        ),
    )

    safe_create_index(
        "ix_student_question_flags_question_id",
        "student_question_flags",
        ["question_id"],
    )
    safe_create_index(
        "ix_student_question_flags_user_created",
        "student_question_flags",
        ["user_id", "created_at"],
    )
    safe_create_index(
        "ix_student_question_flags_unresolved",
        "student_question_flags",
        ["flag_type", "created_at"],
        postgresql_where=sa.text("resolved_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_student_question_flags_unresolved",
        table_name="student_question_flags",
    )
    op.drop_index(
        "ix_student_question_flags_user_created",
        table_name="student_question_flags",
    )
    op.drop_index(
        "ix_student_question_flags_question_id",
        table_name="student_question_flags",
    )
    op.drop_table("student_question_flags")
