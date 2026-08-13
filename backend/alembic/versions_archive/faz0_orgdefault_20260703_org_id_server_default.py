"""faz0 org_id server_default — geçiş güvenliği

Faz 0 Step 2c: organization_id'ye server_default='org_legacy_default'.
Neden: NOT NULL flip sonrası henüz-tenant-farkında-olmayan eski kod (register)
org_id set etmiyor → NotNullViolation (canlı 500 doğrulandı). Default ile eski
INSERT'ler otomatik legacy-org alır; tenant-farkında kod (Step 3) override eder.

Reversible: downgrade default'u kaldırır.

Revision ID: faz0_orgdefault_20260703
Revises: faz0_notnull_20260703
Create Date: 2026-07-03

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "faz0_orgdefault_20260703"
down_revision: Union[str, None] = "faz0_notnull_20260703"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

IDENTITY_TABLES = ["users", "student_profiles", "teacher_profiles", "parent_profiles"]
LEGACY_ORG = "org_legacy_default"


def upgrade() -> None:
    for t in IDENTITY_TABLES:
        op.alter_column(
            t,
            "organization_id",
            existing_type=sa.String(),
            existing_nullable=False,
            server_default=LEGACY_ORG,
        )


def downgrade() -> None:
    for t in IDENTITY_TABLES:
        op.alter_column(
            t,
            "organization_id",
            existing_type=sa.String(),
            existing_nullable=False,
            server_default=None,
        )
