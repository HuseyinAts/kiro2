"""faz1 RLS — billing + organizations tenant isolation (defense-in-depth)

Billing tabloları (organization_licenses, data_processing_agreements, invoices) +
org_memberships + organizations tablolarına RLS policy. Bu tablolar RLS-migration'ından
(faz1_rls / faz1_rls2 / faz1_katmanBC) SONRA yaratıldığı için önceki 73-tablo setinde
yoktu → şu ana kadar sadece app-katman scoping (billing_service :org param +
require_org_role) ile korunuyorlardı. Bu migration DB-katman ikinci savunmayı ekler.

- 4 tablo `organization_id = GUC` (standart tenant_isolation deseni, faz1_rls ile aynı).
- `organizations` ÖZEL: tenant'ın kendisi = satır, scope kolonu `id` (organization_id yok).
- `plans` HARİÇ: global plan kataloğu (tenant-scoped DEĞİL, tüm kiracılar aynı planları okur).

Policy PERMISSIVE-when-unset: app.current_org_id set değilse tüm satırlar görünür
(bootstrap/tenant-resolution/celery/migration kırılmaz); set İSE org'a filtreler.
App non-superuser (kiro2_app) olarak bağlandığı için RLS AKTİF (cutover 4 Tem yapıldı).

Reversible.

Revision ID: faz1_billing_rls_20260704
Revises: faz1_billing_20260704
Create Date: 2026-07-04
"""

from collections.abc import Sequence
from typing import Union

from alembic import op

revision: str = "faz1_billing_rls_20260704"
down_revision: Union[str, None] = "faz1_billing_20260704"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# organization_id kolonu ile scope edilen tablolar (standart desen)
ORG_ID_TABLES = [
    "org_memberships",
    "organization_licenses",
    "data_processing_agreements",
    "invoices",
]

# organization_id (standart)
_PRED_ORGID = (
    "current_setting('app.current_org_id', true) IS NULL "
    "OR current_setting('app.current_org_id', true) = '' "
    "OR organization_id = current_setting('app.current_org_id', true)"
)

# organizations tablosu: scope kolonu = id (org'un kendisi)
_PRED_ID = (
    "current_setting('app.current_org_id', true) IS NULL "
    "OR current_setting('app.current_org_id', true) = '' "
    "OR id = current_setting('app.current_org_id', true)"
)


def upgrade() -> None:
    for t in ORG_ID_TABLES:
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {t} FOR ALL "
            f"USING ({_PRED_ORGID}) WITH CHECK ({_PRED_ORGID})"
        )
    # organizations — id-scoped
    op.execute("ALTER TABLE organizations ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE organizations FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY tenant_isolation ON organizations FOR ALL "
        f"USING ({_PRED_ID}) WITH CHECK ({_PRED_ID})"
    )


def downgrade() -> None:
    for t in [*ORG_ID_TABLES, "organizations"]:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {t}")
        op.execute(f"ALTER TABLE {t} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {t} DISABLE ROW LEVEL SECURITY")
