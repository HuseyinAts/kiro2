"""Recreate offline_sync_packages (dropped by c555a10f4b93, never restored)

F4-S2 kok-neden fix: bu tablo raw-SQL (op.execute, migration
offline_sync_pkg_20260420) ile olusturulmustu, ORM modeli yoktu. Bu yuzden
Alembic autogenerate onu "yetim" tablo sanip migration
c555a10f4b93_sync_db_changes (2026-06-11) ile DUSURDU ve hic geri
olusturulmadi -> 2026-06-11'den beri tum offline-sync ozelligi (POST
/sync-results) sessizce 500 donuyordu (canli curl ile dogrulandi).

Bu migration tabloyu ORIJINAL semasiyla (orn. offline_sync_pkg_20260420)
birebir geri getirir. Artik models/offline_sync_models.py::OfflineSyncPackage
ORM modeli VAR ve services/offline_sync_service.py tarafindan import
ediliyor -> autogenerate onu bir daha yetim sanip dusurmez.

Revision ID: offline_sync_restore_20260725
Revises: kvkk_erasure_backup_20260704
Create Date: 2026-07-25
"""

from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "offline_sync_restore_20260725"
down_revision: Union[str, None] = "kvkk_erasure_backup_20260704"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS offline_sync_packages (
            package_id   VARCHAR PRIMARY KEY,
            student_id   VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            consumed_at  TIMESTAMPTZ NULL,
            question_ids JSONB NULL
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_offline_sync_packages_student "
        "ON offline_sync_packages (student_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_offline_sync_packages_consumed "
        "ON offline_sync_packages (consumed_at)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_offline_sync_packages_consumed")
    op.execute("DROP INDEX IF EXISTS idx_offline_sync_packages_student")
    op.execute("DROP TABLE IF EXISTS offline_sync_packages")
