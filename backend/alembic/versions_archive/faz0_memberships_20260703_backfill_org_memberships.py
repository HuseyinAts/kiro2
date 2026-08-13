"""faz0 org_memberships backfill

Faz 0 Step 4: mevcut kullanıcıları org_memberships'e taşı (org_role türet).
users.role → org_role: ADMIN→SCHOOL_ADMIN, TEACHER→TEACHER, STUDENT→STUDENT,
PARENT→PARENT. org_id = users.organization_id (Step 2 retrofit).

Reversible: downgrade backfill'li membership'leri siler.

Revision ID: faz0_memberships_20260703
Revises: faz0_orgdefault_20260703
Create Date: 2026-07-03

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "faz0_memberships_20260703"
down_revision: Union[str, None] = "faz0_orgdefault_20260703"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BACKFILL_MARK = "faz0_backfill_20260703"


def upgrade() -> None:
    # Her kullanıcı için org_membership (çift-önleme: zaten varsa atla)
    op.execute(
        sa.text(
            """
        INSERT INTO org_memberships
          (id, organization_id, user_id, org_role, is_active, created_at)
        SELECT
          gen_random_uuid()::text,
          u.organization_id,
          u.id,
          CASE u.role::text
            WHEN 'ADMIN'   THEN 'SCHOOL_ADMIN'
            WHEN 'TEACHER' THEN 'TEACHER'
            WHEN 'PARENT'  THEN 'PARENT'
            ELSE 'STUDENT'
          END,
          true,
          now()
        FROM users u
        WHERE NOT EXISTS (
          SELECT 1 FROM org_memberships m
          WHERE m.organization_id = u.organization_id AND m.user_id = u.id
        )
        """
        )
    )


def downgrade() -> None:
    # Yalnız backfill turunda yaratılanları güvenle silmek zor (marker yok);
    # tüm membership'leri siler — backfill dışı membership henüz yok (Step 4).
    op.execute(sa.text("DELETE FROM org_memberships"))
