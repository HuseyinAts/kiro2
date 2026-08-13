"""restore_rls_enforcement

RLS bu DB'de tamamen eksikti (0/241 relrowsecurity, 0 pg_policies) ama
alembic_version zaten bu migration'in atalari olan faz1_rls_20260704 /
faz1_rls2_20260704 / faz1_billing_rls_20260704 / parent_link_codes_20260726'nin
UZERINDEN gecmis (head=51b325d6ff41). Alembic transactional DDL kullandigi icin
o migration'lar hata verseydi zincir orada durur, sonraki onlarca migration
(mv_safe_for_beta matview, taxonomy, FSRS restore...) hic calismazdi -- ama
hepsi mevcut. Yani RLS buyuk ihtimalle calisti, SONRA alembic disinda (manuel
DDL veya sema resetleme) sokuldu; alembic_version head'de kaldi. Bu migration
DB'yi tarihcenin iddia ettigi duruma GERI GETIRIR (forward-fix; uygulanmis
migration'lar YERINDE degistirilmez -- ayni desen: ad6ba3bbe485).

Kapsam: 79 tablo, 4 kaynak migration'in birlesimi (kaynaklar PERMISSIVE
predicate ile CREATE POLICY yapiyordu):
  - faz1_rls_20260704            : 13 tablo
  - faz1_rls2_20260704           : 60 tablo
  - faz1_billing_rls_20260704    : 4 org_id-tablo + organizations (id-scoped) = 5
  - parent_link_codes_20260726   : 1 tablo (parent_link_codes)

ad6ba3bbe485 (68f0783a1, bu oturumun P0 fix'i) zincirde SONRA gelip SADECE
ALL_RLS_TABLES (faz1_rls + faz1_rls2 = 73 tablo) icin USING+WITH CHECK'i
FAIL_CLOSED'a ceviriyordu; billing/organizations (5) ve parent_link_codes (1)
bu kapsamin DISINDAYDI. Tarihceyi harfiyen tekrar oynatmak icin bu migration
da ayni ayrimi yapiyor: 73 tablo fail-closed, 6 tablo permissive-when-unset.

Idempotent: DROP POLICY IF EXISTS + yeniden CREATE (kismi/bozuk durumdan da
guvenle calisir, iki kez calistirilirsa hata vermez).

Revision ID: 041a9181271c
Revises: 51b325d6ff41
Create Date: 2026-08-13
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "041a9181271c"
down_revision: Union[str, None] = "51b325d6ff41"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# faz1_rls_20260704 (13) + faz1_rls2_20260704 (60) -- ad6ba3bbe485'in
# ALL_RLS_TABLES kapsamiyla BIREBIR ayni (programatik olarak o iki dosyadan
# cikarildi, elle kopyalanmadi).
FAIL_CLOSED_TABLES = [
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
    "api_keys",
    "audit_logs",
    "chat_analytics",
    "chat_sessions",
    "classrooms",
    "coaching_events",
    "daily_plans",
    "daily_quests",
    "duel_ratings",
    "dungeon_progress",
    "eba_video_recommendations",
    "eba_video_usage",
    "eba_video_watches",
    "forum_questions",
    "fsrs_student_profiles",
    "fsrs_study_sessions",
    "fsrs_subject_stats",
    "image_uploads",
    "khan_oauth_tokens",
    "kiro2_cat_sessions",
    "kvkk_data_export_requests",
    "league_history",
    "league_memberships",
    "learning_analytics",
    "learning_path_student_profiles",
    "learning_progress_daily",
    "manipulative_activities",
    "manipulative_progress",
    "notifications",
    "oba_challenge_progress",
    "oba_uyeler",
    "osb_settings",
    "parent_child",
    "parent_notifications",
    "parent_social_settings",
    "point_transactions",
    "pomodoro_participants",
    "quiz_submissions",
    "realm_progress",
    "refresh_tokens",
    "sessions",
    "solution_duel_submissions",
    "streak_daily_log",
    "streak_tracking",
    "streaks",
    "student_engagement_signals",
    "student_goals",
    "student_learning_profiles",
    "student_nano_skill_mastery",
    "study_plans",
    "study_rooms",
    "study_sessions",
    "teacher_pool_profiles",
    "topic_completions",
    "user_achievements",
    "user_badges",
    "weekly_progress",
    "xp_transactions",
    "yks_exam_goals",
    "zpd_history",
]
assert len(FAIL_CLOSED_TABLES) == 73

# faz1_billing_rls_20260704 (4) + parent_link_codes_20260726 (1) -- ad6ba3bbe485
# kapsaminin DISINDA kaldi, permissive-when-unset olarak kalir. `organizations`
# ayri (id-scoped) cunku scope kolonu organization_id degil id.
PERMISSIVE_ORG_ID_TABLES = [
    "org_memberships",
    "organization_licenses",
    "data_processing_agreements",
    "invoices",
    "parent_link_codes",
]

PERMISSIVE_PRED = (
    "current_setting('app.current_org_id', true) IS NULL "
    "OR current_setting('app.current_org_id', true) = '' "
    "OR organization_id = current_setting('app.current_org_id', true)"
)
PERMISSIVE_PRED_ID = (
    "current_setting('app.current_org_id', true) IS NULL "
    "OR current_setting('app.current_org_id', true) = '' "
    "OR id = current_setting('app.current_org_id', true)"
)
FAIL_CLOSED_PRED = "organization_id = current_setting('app.current_org_id', true)"


def _ready_tables(names: list[str], scope_column: str) -> set[str]:
    """Bu ortamda RLS kurulabilecek (tablo VE scope kolonu var olan) adlari dondurur.

    13 Agu 2026'da bu DB'de bulunan iki ayri drift, bu migration'in KONUSU
    DEGIL (once-var-olan eksiklikler, muhtemelen c555a10f4b93'un dusurdugu ve
    restore dalgalarinin kapsamadigi kalintilar):
      - 3 tablo hic YOK: daily_plans, learning_progress_daily, yks_exam_goals
      - 1 tablo var ama scope kolonu YOK: data_processing_agreements.organization_id

    Sabit listeleri degistirmek yerine calisma-zamaninda introspect edip
    eksikleri ATLA + acikca yazdir -- baska bir ortamda hepsi mevcutsa hicbir
    sey atlanmaz.
    """
    bind = op.get_bind()
    tablo_var = {
        row[0]
        for row in bind.execute(
            sa.text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename = ANY(:names)"
            ),
            {"names": names},
        )
    }
    kolon_var = {
        row[0]
        for row in bind.execute(
            sa.text(
                "SELECT table_name FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = ANY(:names) "
                "AND column_name = :col"
            ),
            {"names": list(tablo_var), "col": scope_column},
        )
    }
    ready = tablo_var & kolon_var
    eksik_tablo = sorted(set(names) - tablo_var)
    eksik_kolon = sorted(tablo_var - kolon_var)
    if eksik_tablo:
        print(  # noqa: T201 -- alembic upgrade ciktisinda gorunmesi ISTENIYOR
            f"[041a9181271c] UYARI: {len(eksik_tablo)} tablo bu ortamda yok, RLS "
            f"atlaniyor (ayri bir eksiklik, bu migration'in kapsami DEGIL): "
            f"{eksik_tablo}"
        )
    if eksik_kolon:
        print(  # noqa: T201
            f"[041a9181271c] UYARI: {len(eksik_kolon)} tabloda '{scope_column}' "
            f"kolonu yok, RLS atlaniyor (ayri bir eksiklik): {eksik_kolon}"
        )
    return ready


def _apply_policy(table: str, pred: str) -> None:
    """RLS+FORCE'u acar, tenant_isolation policy'sini `pred` ile (yeniden) kurar.

    DROP POLICY IF EXISTS + CREATE POLICY: idempotent, kismi durumdan da guvenle
    calisir. Tablo adlari modul sabiti (kullanici girdisi DEGIL).
    """
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
    op.execute(
        f"CREATE POLICY tenant_isolation ON {table} FOR ALL "
        f"USING ({pred}) WITH CHECK ({pred})"
    )


def upgrade() -> None:
    org_id_names = [*FAIL_CLOSED_TABLES, *PERMISSIVE_ORG_ID_TABLES]
    ready = _ready_tables(org_id_names, "organization_id")
    ready_orgs = _ready_tables(["organizations"], "id")

    for t in FAIL_CLOSED_TABLES:
        if t in ready:
            _apply_policy(t, FAIL_CLOSED_PRED)
    for t in PERMISSIVE_ORG_ID_TABLES:
        if t in ready:
            _apply_policy(t, PERMISSIVE_PRED)
    if "organizations" in ready_orgs:
        _apply_policy("organizations", PERMISSIVE_PRED_ID)


def downgrade() -> None:
    org_id_names = [*FAIL_CLOSED_TABLES, *PERMISSIVE_ORG_ID_TABLES]
    ready = _ready_tables(org_id_names, "organization_id") | _ready_tables(
        ["organizations"], "id"
    )
    for t in [*org_id_names, "organizations"]:
        if t not in ready:
            continue
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {t}")
        op.execute(f"ALTER TABLE {t} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {t} DISABLE ROW LEVEL SECURITY")
