"""fix_rls_fail_closed_policy

Revision ID: ad6ba3bbe485
Revises: 7f8ef189da5a
Create Date: 2026-08-09 02:55:16.396511

"""

from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ad6ba3bbe485"
down_revision: Union[str, None] = "7f8ef189da5a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


RLS_TABLES_1 = [
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
RLS_TABLES_2 = [
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
ALL_RLS_TABLES = RLS_TABLES_1 + RLS_TABLES_2

FAIL_CLOSED_PRED = "organization_id = current_setting('app.current_org_id', true)"

PERMISSIVE_PRED = (
    "current_setting('app.current_org_id', true) IS NULL "
    "OR current_setting('app.current_org_id', true) = '' "
    "OR organization_id = current_setting('app.current_org_id', true)"
)


def alter_policy_sql(table: str, pred: str) -> str:
    """`tenant_isolation` policy'sini `pred` ile yeniden yazan DO blogu.

    Tablo/policy yoksa (bos ya da test DB'si) sessizce atlanir.

    `WITH CHECK` AYRICA yazilmak ZORUNDA: PostgreSQL'de `ALTER POLICY ... USING`
    yalniz okuma yolunu degistirir, yazma yolunu DOKUNULMAMIS birakir. Yalniz
    USING yazilirsa politika "oku-kapali / yaz-serbest" olur ve GUC set etmeyen
    bir istek yabanci bir organizasyona satir enjekte edebilir (13 Agu 2026'da
    canli olculdu; bkz. tests/integration/test_rls_fail_closed_with_check.py).
    """

    # FAIL_CLOSED_PRED). Kullanici girdisi degil; tablo adi ve policy ifadesi
    # zaten parametrelenemez.
    return f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = '{table}' AND policyname = 'tenant_isolation') THEN
                ALTER POLICY tenant_isolation ON {table} USING ({pred}) WITH CHECK ({pred});
            END IF;
        END
        $$;
        """  # noqa: S608


def upgrade() -> None:
    # Update all RLS policies to be Fail-Closed instead of Fail-Open.
    for table in ALL_RLS_TABLES:
        op.execute(alter_policy_sql(table, FAIL_CLOSED_PRED))


def downgrade() -> None:
    for table in ALL_RLS_TABLES:
        op.execute(alter_policy_sql(table, PERMISSIVE_PRED))
