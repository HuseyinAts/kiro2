"""faz1 RLS — Row-Level Security (ikinci savunma, tenant izolasyonu)

13 data tablosuna RLS policy: tenant izolasyonu (organization_id = GUC).
Policy PERMISSIVE-when-unset: app.current_org_id set DEĞİLSE tüm satırlar
görünür (mevcut app için no-op, kırmaz); set İSE org'a filtreler.

ÖNEMLİ — CANLI AKTİVASYON ÖN KOŞULU:
App şu an `postgres` (superuser+bypassrls) olarak bağlanıyor → RLS BYPASS edilir
(FORCE dahil). RLS etkin olması için app NON-SUPERUSER rolle bağlanmalı (ayrı
infra: rol oluştur + GRANT + DATABASE_URL değiştir + re-test). Bu migration
policy'leri kurar + FORCE eder; mekanizma geçici-rol testiyle doğrulanmıştır
(faz1_rls_verify). App-katman _scope_tenant (Faz 0) AKTIF savunma; RLS defense-in-depth.

Reversible.

Revision ID: faz1_rls_20260704
Revises: faz1_katmanA2_20260704
Create Date: 2026-07-04

"""

from collections.abc import Sequence
from typing import Union

from alembic import op

revision: str = "faz1_rls_20260704"
down_revision: Union[str, None] = "faz1_katmanA2_20260704"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Data tabloları (identity/org_memberships HARİÇ — özel auth akışları)
RLS_TABLES = [
    "exam_sessions",
    "fsrs_cards",
    "fsrs_reviews",
    "fsrs_schedules",
    "student_abilities",
    "bkt_states",
    "student_knowledge_states",
    "performance_history",
    "kvkk_consents",
    "learning_paths",
    "topic_progress",
    "user_theta",
    "kiro2_learning_events",
]

_PRED = (
    "current_setting('app.current_org_id', true) IS NULL "
    "OR current_setting('app.current_org_id', true) = '' "
    "OR organization_id = current_setting('app.current_org_id', true)"
)


def upgrade() -> None:
    for t in RLS_TABLES:
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {t} FOR ALL "
            f"USING ({_PRED}) WITH CHECK ({_PRED})"
        )


def downgrade() -> None:
    for t in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {t}")
        op.execute(f"ALTER TABLE {t} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {t} DISABLE ROW LEVEL SECURITY")
