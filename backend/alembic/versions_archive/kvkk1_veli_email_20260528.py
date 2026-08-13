"""KVKK Faz 1: student_profiles.veli_email (reşit olmayan öğrenci veli iletişimi)

Revision ID: kvkk1_veli_email_20260528
Revises: s179_hot_path_idx_20260521
Create Date: 2026-05-28

Nullable; sadece reşit olmayan kullanıcılar için register sırasında doldurulur.
veli_onay flag'i ile birlikte minor consent capture (Faz 1, email gönderimi yok).
"""

import sqlalchemy as sa

from alembic import op

revision = "kvkk1_veli_email_20260528"
down_revision = "s179_hot_path_idx_20260521"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "student_profiles",
        sa.Column("veli_email", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("student_profiles", "veli_email")
