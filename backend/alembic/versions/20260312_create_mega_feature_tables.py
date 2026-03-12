"""Create all mega feature tables (F1-F20)

18 new tables for leagues, duels, study planner, coaching,
error clusters, DINA model, and knowledge graph.

Revision ID: mega_feature_001
Revises: f8_error_type_001
Create Date: 2026-03-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = "mega_feature_001"
down_revision = "f8_error_type_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ─────────────────────────────────────────
    # F2: League System
    # ─────────────────────────────────────────
    op.create_table(
        "league_memberships",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("student_id", sa.String(), nullable=False),
        sa.Column("league_tier", sa.String(20), nullable=False, server_default="BRONZE"),
        sa.Column("weekly_xp", sa.Integer(), server_default="0"),
        sa.Column("week_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_league_membership_student", "league_memberships", ["student_id"])
    op.create_index("idx_league_membership_tier_week", "league_memberships", ["league_tier", "week_start"])
    op.create_index("idx_league_membership_xp_rank", "league_memberships", ["league_tier", "week_start", "weekly_xp"])
    op.create_unique_constraint("uq_league_membership_student_week", "league_memberships", ["student_id", "week_start"])

    op.create_table(
        "league_history",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("student_id", sa.String(), nullable=False),
        sa.Column("week_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("from_tier", sa.String(20), nullable=True),
        sa.Column("to_tier", sa.String(20), nullable=True),
        sa.Column("final_rank", sa.Integer(), nullable=True),
        sa.Column("final_xp", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_league_history_student", "league_history", ["student_id"])
    op.create_index("idx_league_history_week", "league_history", ["week_start"])

    # ─────────────────────────────────────────
    # F1: Duel System
    # ─────────────────────────────────────────
    op.create_table(
        "duel_sessions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("player1_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("player2_id", sa.String(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("subject", sa.String(50), nullable=False),
        sa.Column("question_count", sa.Integer(), server_default="5"),
        sa.Column("time_per_question_sec", sa.Integer(), server_default="15"),
        sa.Column("status", sa.String(20), server_default="'waiting'"),
        sa.Column("player1_score", sa.Integer(), server_default="0"),
        sa.Column("player2_score", sa.Integer(), server_default="0"),
        sa.Column("winner_id", sa.String(), nullable=True),
        sa.Column("player1_elo_change", sa.Float(), server_default="0.0"),
        sa.Column("player2_elo_change", sa.Float(), server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_duel_player1", "duel_sessions", ["player1_id"])
    op.create_index("idx_duel_player2", "duel_sessions", ["player2_id"])
    op.create_index("idx_duel_status", "duel_sessions", ["status"])
    op.create_index("idx_duel_created", "duel_sessions", ["created_at"])

    op.create_table(
        "duel_matches",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("session_id", sa.String(), sa.ForeignKey("duel_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.String(), nullable=False),
        sa.Column("question_order", sa.Integer(), nullable=False),
        sa.Column("player1_answer", sa.String(1), nullable=True),
        sa.Column("player1_time_ms", sa.Integer(), nullable=True),
        sa.Column("player1_correct", sa.Boolean(), nullable=True),
        sa.Column("player2_answer", sa.String(1), nullable=True),
        sa.Column("player2_time_ms", sa.Integer(), nullable=True),
        sa.Column("player2_correct", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_duel_match_session", "duel_matches", ["session_id"])
    op.create_index("idx_duel_match_order", "duel_matches", ["session_id", "question_order"])

    op.create_table(
        "duel_ratings",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("student_id", sa.String(), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("elo_rating", sa.Float(), server_default="1200.0"),
        sa.Column("wins", sa.Integer(), server_default="0"),
        sa.Column("losses", sa.Integer(), server_default="0"),
        sa.Column("draws", sa.Integer(), server_default="0"),
        sa.Column("peak_rating", sa.Float(), server_default="1200.0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_duel_rating_student", "duel_ratings", ["student_id"], unique=True)
    op.create_index("idx_duel_rating_elo", "duel_ratings", ["elo_rating"])

    # ─────────────────────────────────────────
    # F7: Study Planner
    # ─────────────────────────────────────────
    op.create_table(
        "study_plans",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("student_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("yks_date", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("total_weeks", sa.Integer(), server_default="0"),
        sa.Column("target_net", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_study_plans_student", "study_plans", ["student_id"])
    op.create_index("idx_study_plans_active", "study_plans", ["student_id", "is_active"])

    op.create_table(
        "weekly_goals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("study_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("topics", sa.JSON(), nullable=True),
        sa.Column("target_questions", sa.Integer(), server_default="0"),
        sa.Column("target_reviews", sa.Integer(), server_default="0"),
        sa.Column("completed_questions", sa.Integer(), server_default="0"),
        sa.Column("completed_reviews", sa.Integer(), server_default="0"),
        sa.Column("accuracy_rate", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_weekly_goals_plan", "weekly_goals", ["plan_id"])
    op.create_index("idx_weekly_goals_week", "weekly_goals", ["plan_id", "week_number"])

    # ─────────────────────────────────────────
    # F6: Proactive Coaching
    # ─────────────────────────────────────────
    op.create_table(
        "coaching_events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("student_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("trigger_data", sa.JSON(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("priority", sa.Integer(), server_default="0"),
        sa.Column("action_url", sa.String(500), nullable=True),
        sa.Column("shown_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("clicked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_coaching_student", "coaching_events", ["student_id"])
    op.create_index("idx_coaching_event_type", "coaching_events", ["event_type"])
    op.create_index("idx_coaching_shown", "coaching_events", ["student_id", "shown_at"])
    op.create_index("idx_coaching_created", "coaching_events", ["created_at"])

    op.create_table(
        "student_engagement_signals",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("student_id", sa.String(), nullable=False),
        sa.Column("signal_type", sa.String(50), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_engagement_student", "student_engagement_signals", ["student_id"])
    op.create_index("idx_engagement_type_recorded", "student_engagement_signals", ["student_id", "signal_type", "recorded_at"])

    # ─────────────────────────────────────────
    # F15: Error Clustering
    # ─────────────────────────────────────────
    op.create_table(
        "error_clusters",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("subject", sa.String(50), nullable=False),
        sa.Column("topic_ids", JSONB(), server_default="'[]'"),
        sa.Column("error_pattern", sa.String(100), nullable=False),
        sa.Column("student_count", sa.Integer(), server_default="0"),
        sa.Column("recommended_remediation", JSONB(), server_default="'{}'"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_error_cluster_subject", "error_clusters", ["subject"])
    op.create_index("idx_error_cluster_updated", "error_clusters", ["updated_at"])

    op.create_table(
        "peer_recommendations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("cluster_id", sa.String(), nullable=False),
        sa.Column("source_topic", sa.String(200), nullable=False),
        sa.Column("target_topic", sa.String(200), nullable=False),
        sa.Column("improvement_rate", sa.Float(), server_default="0.0"),
        sa.Column("sample_size", sa.Integer(), server_default="0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_peer_rec_cluster", "peer_recommendations", ["cluster_id"])
    op.create_index("idx_peer_rec_source", "peer_recommendations", ["source_topic"])

    # ─────────────────────────────────────────
    # F11: DINA Model
    # ─────────────────────────────────────────
    op.create_table(
        "nano_skills",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("knowledge_point_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("subject", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_nano_skill_kp", "nano_skills", ["knowledge_point_id"])

    op.create_table(
        "q_matrix",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("question_id", sa.String(), nullable=False),
        sa.Column("nano_skill_id", sa.String(), sa.ForeignKey("nano_skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_required", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_qmatrix_question", "q_matrix", ["question_id"])
    op.create_index("idx_qmatrix_skill", "q_matrix", ["nano_skill_id"])
    op.create_unique_constraint("uq_qmatrix_pair", "q_matrix", ["question_id", "nano_skill_id"])

    op.create_table(
        "dina_parameters",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("question_id", sa.String(), nullable=False, unique=True),
        sa.Column("slip", sa.Float(), server_default="0.1"),
        sa.Column("guess", sa.Float(), server_default="0.2"),
        sa.Column("calibrated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_dina_question", "dina_parameters", ["question_id"], unique=True)

    op.create_table(
        "student_nano_skill_mastery",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("student_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("nano_skill_id", sa.String(), sa.ForeignKey("nano_skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mastery", sa.Float(), server_default="0.5"),
        sa.Column("confidence", sa.Float(), server_default="0.0"),
        sa.Column("response_count", sa.Integer(), server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_snsm_student", "student_nano_skill_mastery", ["student_id"])
    op.create_index("idx_snsm_skill", "student_nano_skill_mastery", ["nano_skill_id"])
    op.create_unique_constraint("uq_snsm_pair", "student_nano_skill_mastery", ["student_id", "nano_skill_id"])

    # ─────────────────────────────────────────
    # F4: Knowledge Graph
    # ─────────────────────────────────────────
    op.create_table(
        "knowledge_points",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("topic_id", sa.String(), nullable=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("name_tr", sa.String(200), nullable=False),
        sa.Column("subject", sa.String(50), nullable=False),
        sa.Column("prerequisite_ids", sa.JSON(), nullable=True),
        sa.Column("difficulty_range", sa.JSON(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_kp_topic", "knowledge_points", ["topic_id"])
    op.create_index("idx_kp_subject", "knowledge_points", ["subject"])
    op.create_index("idx_kp_code", "knowledge_points", ["code"], unique=True)

    op.create_table(
        "question_knowledge_mappings",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("question_id", sa.String(), nullable=False),
        sa.Column("knowledge_point_id", sa.String(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_qkm_question", "question_knowledge_mappings", ["question_id"])
    op.create_index("idx_qkm_knowledge_point", "question_knowledge_mappings", ["knowledge_point_id"])
    op.create_unique_constraint("uq_question_knowledge_mapping", "question_knowledge_mappings", ["question_id", "knowledge_point_id"])

    op.create_table(
        "student_knowledge_states",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("student_id", sa.String(), nullable=False),
        sa.Column("knowledge_point_id", sa.String(), nullable=False),
        sa.Column("mastery_level", sa.Float(), server_default="0.0"),
        sa.Column("confidence", sa.Float(), server_default="0.0"),
        sa.Column("response_count", sa.Integer(), server_default="0"),
        sa.Column("last_assessed", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_sks_student", "student_knowledge_states", ["student_id"])
    op.create_index("idx_sks_knowledge_point", "student_knowledge_states", ["knowledge_point_id"])
    op.create_unique_constraint("uq_student_knowledge_state", "student_knowledge_states", ["student_id", "knowledge_point_id"])


def downgrade() -> None:
    # Drop in reverse order (dependencies first)
    op.drop_table("student_knowledge_states")
    op.drop_table("question_knowledge_mappings")
    op.drop_table("knowledge_points")

    op.drop_table("student_nano_skill_mastery")
    op.drop_table("dina_parameters")
    op.drop_table("q_matrix")
    op.drop_table("nano_skills")

    op.drop_table("peer_recommendations")
    op.drop_table("error_clusters")

    op.drop_table("student_engagement_signals")
    op.drop_table("coaching_events")

    op.drop_table("weekly_goals")
    op.drop_table("study_plans")

    op.drop_table("duel_ratings")
    op.drop_table("duel_matches")
    op.drop_table("duel_sessions")

    op.drop_table("league_history")
    op.drop_table("league_memberships")
