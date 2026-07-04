"""KVKK schema drift fix — eksik kvkk_audit_logs + kvkk_data_deletion_requests

Bu iki tablo modeli (models/kvkk_models.py) vardı ama canlı DB'de HİÇ yaratılmamıştı
(pre-existing drift). Sonuç: /kvkk/privacy/export (audit-log INSERT) ve
/kvkk/privacy/delete (deletion-request INSERT) endpoint'leri 500 veriyordu.

Tablolar model tanımından yaratılır (create_type=False enum → mevcut
`data_processing_purpose` tipi yeniden yaratılmaz). kiro2_app (non-superuser RLS
rolü) için GRANT eklenir — yeni tablolar eski toplu-GRANT kapsamı dışında kalır.

Reversible.

Revision ID: kvkk_missing_tables_20260704
Revises: faz1_billing_rls_20260704
Create Date: 2026-07-04
"""

from collections.abc import Sequence
from typing import Union

from alembic import op

revision: str = "kvkk_missing_tables_20260704"
down_revision: Union[str, None] = "faz1_billing_rls_20260704"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_GRANT = """
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'kiro2_app') THEN
    GRANT SELECT, INSERT, UPDATE, DELETE ON kvkk_audit_logs TO kiro2_app;
    GRANT SELECT, INSERT, UPDATE, DELETE ON kvkk_data_deletion_requests TO kiro2_app;
  END IF;
END $$;
"""


def upgrade() -> None:
    from models.kvkk_models import KVKKAuditLog, KVKKDataDeletionRequest

    bind = op.get_bind()
    KVKKAuditLog.__table__.create(bind, checkfirst=True)
    KVKKDataDeletionRequest.__table__.create(bind, checkfirst=True)
    op.execute(_GRANT)


def downgrade() -> None:
    from models.kvkk_models import KVKKAuditLog, KVKKDataDeletionRequest

    bind = op.get_bind()
    KVKKDataDeletionRequest.__table__.drop(bind, checkfirst=True)
    KVKKAuditLog.__table__.drop(bind, checkfirst=True)
