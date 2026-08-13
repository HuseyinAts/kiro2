"""KVKK Md.7 erasure backup tablosu — anonimleştirme öncesi orijinal PII (reversible)

Silme executor'ı (anonimleştirme) çalışmadan ÖNCE anonimleştirilen kolonların
orijinal değerlerini bu tabloya yazar → geri-alınabilirlik + KVKK silme-işlemi
kanıtı (audit). Talep bazında (request_id) gruplu.

Reversible.

Revision ID: kvkk_erasure_backup_20260704
Revises: kvkk_missing_tables_20260704
Create Date: 2026-07-04
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "kvkk_erasure_backup_20260704"
down_revision: Union[str, None] = "kvkk_missing_tables_20260704"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_GRANT = """
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'kiro2_app') THEN
    GRANT SELECT, INSERT, UPDATE, DELETE ON kvkk_erasure_backup TO kiro2_app;
  END IF;
END $$;
"""


def upgrade() -> None:
    op.create_table(
        "kvkk_erasure_backup",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("request_id", sa.String(), nullable=False, index=True),
        sa.Column("user_id", sa.String(), nullable=False, index=True),
        sa.Column("table_name", sa.String(100), nullable=False),
        sa.Column("original_values", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_erasure_backup_request", "kvkk_erasure_backup", ["request_id"])
    op.execute(_GRANT)


def downgrade() -> None:
    op.drop_table("kvkk_erasure_backup")
