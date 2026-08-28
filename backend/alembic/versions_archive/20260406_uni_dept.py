"""create_university_department_review_tables

Revision ID: 20260406_uni_dept
Revises: 20260406_reasoning
Create Date: 2026-04-06
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from alembic import op

revision = "20260406_uni_dept"
down_revision = "20260406_reasoning"
branch_labels = None
depends_on = None


def upgrade():
    # ==================== UNIVERSITIES (5 tables) ====================
    op.create_table(
        "universities",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("short_name", sa.String(50)),
        sa.Column("university_type", sa.String(20), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("district", sa.String(100)),
        sa.Column("address", sa.Text),
        sa.Column("postal_code", sa.String(10)),
        sa.Column("latitude", sa.Float),
        sa.Column("longitude", sa.Float),
        sa.Column("phone", sa.String(20)),
        sa.Column("email", sa.String(100)),
        sa.Column("website", sa.String(255)),
        sa.Column("established_year", sa.Integer),
        sa.Column("rector", sa.String(100)),
        sa.Column("total_students", sa.Integer),
        sa.Column("total_faculty", sa.Integer),
        sa.Column("world_ranking", sa.Integer),
        sa.Column("turkey_ranking", sa.Integer),
        sa.Column("description", sa.Text),
        sa.Column("campus_info", JSONB),
        sa.Column("facilities", ARRAY(sa.String)),
        sa.Column("social_media", JSONB),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index("idx_universities_city", "universities", ["city"])
    op.create_index("idx_universities_type", "universities", ["university_type"])

    op.create_table(
        "departments",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50)),
        sa.Column("faculty", sa.String(200)),
        sa.Column("degree_type", sa.String(50), nullable=False),
        sa.Column("education_language", sa.String(50), default="Türkçe"),
        sa.Column("education_duration", sa.Integer, default=4),
        sa.Column("description", sa.Text),
        sa.Column("overview", sa.Text),
        sa.Column("career_opportunities", ARRAY(sa.String)),
        sa.Column("job_titles", ARRAY(sa.String)),
        sa.Column("average_salary", sa.Integer),
        sa.Column("employment_rate", sa.Float),
        sa.Column("required_subjects", ARRAY(sa.String)),
        sa.Column("recommended_skills", ARRAY(sa.String)),
        sa.Column("accreditation", JSONB),
        sa.Column("international_programs", ARRAY(sa.String)),
        sa.Column("seo_keywords", ARRAY(sa.String)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "university_programs",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "university_id",
            UUID(as_uuid=True),
            sa.ForeignKey("universities.id"),
            nullable=False,
        ),
        sa.Column(
            "department_id",
            UUID(as_uuid=True),
            sa.ForeignKey("departments.id"),
            nullable=False,
        ),
        sa.Column("program_code", sa.String(50)),
        sa.Column("program_name", sa.String(255), nullable=False),
        sa.Column("program_type", sa.String(30), default="normal"),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("score_type", sa.String(10), nullable=False),
        sa.Column("base_score", sa.Float),
        sa.Column("top_score", sa.Float),
        sa.Column("median_score", sa.Float),
        sa.Column("total_quota", sa.Integer),
        sa.Column("general_quota", sa.Integer),
        sa.Column("special_quota", sa.Integer),
        sa.Column("filled_quota", sa.Integer),
        sa.Column("acceptance_rate", sa.Float),
        sa.Column("competition_ratio", sa.Float),
        sa.Column("min_rank", sa.Integer),
        sa.Column("max_rank", sa.Integer),
        sa.Column("median_rank", sa.Integer),
        sa.Column("scholarship", sa.Boolean, default=False),
        sa.Column("scholarship_percentage", sa.Float),
        sa.Column("tuition_fee", sa.Integer),
        sa.Column("has_language_prep", sa.Boolean, default=False),
        sa.Column("prep_mandatory", sa.Boolean, default=False),
        sa.Column("special_conditions", JSONB),
        sa.Column("bonus_coefficients", JSONB),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index(
        "idx_program_search",
        "university_programs",
        ["university_id", "department_id", "year", "score_type"],
    )
    op.create_index(
        "idx_base_score", "university_programs", ["year", "score_type", "base_score"]
    )

    op.create_table(
        "program_score_history",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "program_id",
            UUID(as_uuid=True),
            sa.ForeignKey("university_programs.id"),
            nullable=False,
        ),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("base_score", sa.Float),
        sa.Column("top_score", sa.Float),
        sa.Column("median_score", sa.Float),
        sa.Column("total_quota", sa.Integer),
        sa.Column("filled_quota", sa.Integer),
        sa.Column("min_rank", sa.Integer),
        sa.Column("max_rank", sa.Integer),
        sa.Column("source", sa.String(100)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "user_university_preferences",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", sa.String, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("preferred_cities", ARRAY(sa.String)),
        sa.Column("preferred_university_types", ARRAY(sa.String)),
        sa.Column("preferred_score_types", ARRAY(sa.String)),
        sa.Column("yks_score", sa.Float),
        sa.Column("score_type", sa.String(10)),
        sa.Column("career_interests", ARRAY(sa.String)),
        sa.Column("target_departments", ARRAY(sa.String)),
        sa.Column("max_tuition_fee", sa.Integer),
        sa.Column("needs_scholarship", sa.Boolean, default=False),
        sa.Column("preferences", JSONB),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    # ==================== UNIVERSITY INFO (5 tables) ====================
    op.create_table(
        "campus_info",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "university_id",
            UUID(as_uuid=True),
            sa.ForeignKey("universities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("campus_name", sa.String(255), nullable=False),
        sa.Column("campus_type", sa.String(30), default="main_campus"),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("district", sa.String(100)),
        sa.Column("address", sa.Text),
        sa.Column("total_area_sqm", sa.Integer),
        sa.Column("building_count", sa.Integer),
        sa.Column("libraries", JSONB),
        sa.Column("sports_facilities", ARRAY(sa.String)),
        sa.Column("laboratories", JSONB),
        sa.Column("dining_facilities", JSONB),
        sa.Column("health_center", sa.Boolean, default=False),
        sa.Column("counseling_center", sa.Boolean, default=False),
        sa.Column("career_center", sa.Boolean, default=False),
        sa.Column("international_office", sa.Boolean, default=False),
        sa.Column("wifi_available", sa.Boolean, default=True),
        sa.Column("computer_labs", sa.Integer, default=0),
        sa.Column("student_clubs", JSONB),
        sa.Column("total_student_clubs", sa.Integer, default=0),
        sa.Column("cultural_centers", ARRAY(sa.String)),
        sa.Column("public_transport_access", sa.Boolean, default=True),
        sa.Column("shuttle_service", sa.Boolean, default=False),
        sa.Column("wheelchair_accessible", sa.Boolean, default=True),
        sa.Column("description", sa.Text),
        sa.Column("highlights", ARRAY(sa.String)),
        sa.Column("photos", ARRAY(sa.String)),
        sa.Column("phone", sa.String(50)),
        sa.Column("email", sa.String(255)),
        sa.Column("website", sa.String(255)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "city_living_costs",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("region", sa.String(100)),
        sa.Column("rent_studio_avg", sa.Integer),
        sa.Column("rent_1br_avg", sa.Integer),
        sa.Column("shared_room_avg", sa.Integer),
        sa.Column("utilities_avg", sa.Integer),
        sa.Column("food_budget_avg", sa.Integer),
        sa.Column("public_transport_monthly", sa.Integer),
        sa.Column("total_min_budget", sa.Integer),
        sa.Column("total_avg_budget", sa.Integer),
        sa.Column("total_comfortable_budget", sa.Integer),
        sa.Column("cost_of_living_index", sa.Float),
        sa.Column("year", sa.Integer, nullable=False, default=2024),
        sa.Column("currency", sa.String(10), default="TRY"),
        sa.Column("data_source", sa.String(255)),
        sa.Column("notes", sa.Text),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "dormitory_info",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "university_id",
            UUID(as_uuid=True),
            sa.ForeignKey("universities.id", ondelete="CASCADE"),
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("accommodation_type", sa.String(30), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("district", sa.String(100)),
        sa.Column("address", sa.Text),
        sa.Column("total_capacity", sa.Integer),
        sa.Column("available_spaces", sa.Integer),
        sa.Column("gender", sa.String(20)),
        sa.Column("room_types", JSONB),
        sa.Column("price_min", sa.Integer),
        sa.Column("price_max", sa.Integer),
        sa.Column("price_avg", sa.Integer),
        sa.Column("deposit_required", sa.Integer),
        sa.Column("meals_included", sa.Boolean, default=False),
        sa.Column("wifi_included", sa.Boolean, default=True),
        sa.Column("laundry_facilities", sa.Boolean, default=True),
        sa.Column("study_rooms", sa.Boolean, default=False),
        sa.Column("security_24_7", sa.Boolean, default=True),
        sa.Column("distance_to_campus_km", sa.Float),
        sa.Column("description", sa.Text),
        sa.Column("photos", ARRAY(sa.String)),
        sa.Column("phone", sa.String(50)),
        sa.Column("email", sa.String(255)),
        sa.Column("website", sa.String(255)),
        sa.Column("overall_rating", sa.Float),
        sa.Column("verified", sa.Boolean, default=False),
        sa.Column("year", sa.Integer, default=2024),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "scholarship_programs",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "university_id",
            UUID(as_uuid=True),
            sa.ForeignKey("universities.id", ondelete="CASCADE"),
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("scholarship_type", sa.String(30), nullable=False),
        sa.Column("provider", sa.String(255)),
        sa.Column("coverage_percentage", sa.Float),
        sa.Column("covers_tuition", sa.Boolean, default=True),
        sa.Column("amount_min", sa.Integer),
        sa.Column("amount_max", sa.Integer),
        sa.Column("monthly_stipend", sa.Integer),
        sa.Column("min_exam_score", sa.Float),
        sa.Column("min_high_school_gpa", sa.Float),
        sa.Column("eligibility_criteria", ARRAY(sa.String)),
        sa.Column("required_documents", ARRAY(sa.String)),
        sa.Column("application_url", sa.String(255)),
        sa.Column("number_of_recipients", sa.Integer),
        sa.Column("renewable", sa.Boolean, default=True),
        sa.Column("max_duration_years", sa.Integer),
        sa.Column("description", sa.Text),
        sa.Column("active", sa.Boolean, default=True),
        sa.Column("year", sa.Integer, default=2024),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "university_statistics",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "university_id",
            UUID(as_uuid=True),
            sa.ForeignKey("universities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("year", sa.Integer, nullable=False, default=2024),
        sa.Column("total_campuses", sa.Integer, default=0),
        sa.Column("total_student_clubs", sa.Integer, default=0),
        sa.Column("city", sa.String(100)),
        sa.Column("avg_monthly_cost", sa.Integer),
        sa.Column("avg_rent", sa.Integer),
        sa.Column("cost_of_living_index", sa.Float),
        sa.Column("total_dormitory_capacity", sa.Integer, default=0),
        sa.Column("avg_dormitory_cost", sa.Integer),
        sa.Column("total_scholarships", sa.Integer, default=0),
        sa.Column("avg_scholarship_amount", sa.Integer),
        sa.Column("affordability_score", sa.Float),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "last_updated", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    # ==================== DEPARTMENT INFO (5 tables) ====================
    op.create_table(
        "department_curricula",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "department_id",
            UUID(as_uuid=True),
            sa.ForeignKey("departments.id"),
            nullable=False,
        ),
        sa.Column("total_credits", sa.Integer),
        sa.Column("duration_years", sa.Integer, default=4),
        sa.Column("duration_semesters", sa.Integer, default=8),
        sa.Column("core_courses", JSONB),
        sa.Column("elective_courses", JSONB),
        sa.Column("specialization_tracks", ARRAY(sa.String)),
        sa.Column("learning_outcomes", ARRAY(sa.Text)),
        sa.Column("skills_gained", ARRAY(sa.String)),
        sa.Column("internship_required", sa.Boolean, default=False),
        sa.Column("thesis_required", sa.Boolean, default=False),
        sa.Column("capstone_project", sa.Boolean, default=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "last_updated", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "career_opportunities",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "department_id",
            UUID(as_uuid=True),
            sa.ForeignKey("departments.id"),
            nullable=False,
        ),
        sa.Column("job_title", sa.String(200), nullable=False),
        sa.Column("job_description", sa.Text),
        sa.Column("industry_type", sa.String(30)),
        sa.Column("employment_rate", sa.Float),
        sa.Column("demand_level", sa.String(20)),
        sa.Column("required_skills", ARRAY(sa.String)),
        sa.Column("top_employers", ARRAY(sa.String)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "salary_expectations",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "department_id",
            UUID(as_uuid=True),
            sa.ForeignKey("departments.id"),
            nullable=False,
        ),
        sa.Column(
            "career_opportunity_id",
            UUID(as_uuid=True),
            sa.ForeignKey("career_opportunities.id"),
        ),
        sa.Column("experience_level", sa.String(20), nullable=False),
        sa.Column("min_salary", sa.Integer, nullable=False),
        sa.Column("max_salary", sa.Integer, nullable=False),
        sa.Column("average_salary", sa.Integer, nullable=False),
        sa.Column("region", sa.String(50)),
        sa.Column("city", sa.String(100)),
        sa.Column("industry_type", sa.String(30)),
        sa.Column("year", sa.Integer, nullable=False, default=2024),
        sa.Column("data_source", sa.String(100)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "sector_analyses",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("industry_type", sa.String(30), nullable=False),
        sa.Column("sector_name", sa.String(200), nullable=False),
        sa.Column("related_department_ids", ARRAY(UUID(as_uuid=True))),
        sa.Column("market_size_billion_tl", sa.Float),
        sa.Column("year", sa.Integer, nullable=False, default=2024),
        sa.Column("annual_growth_rate", sa.Float),
        sa.Column("job_growth_rate", sa.Float),
        sa.Column("growth_trend", sa.String(20)),
        sa.Column("total_job_openings", sa.Integer),
        sa.Column("in_demand_skills", ARRAY(sa.String)),
        sa.Column("emerging_technologies", ARRAY(sa.String)),
        sa.Column("future_outlook", sa.Text),
        sa.Column("future_demand_prediction", sa.String(20)),
        sa.Column("automation_risk", sa.String(20)),
        sa.Column("regional_distribution", JSONB),
        sa.Column("key_trends", ARRAY(sa.Text)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "department_statistics",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "department_id",
            UUID(as_uuid=True),
            sa.ForeignKey("departments.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("overall_employment_rate", sa.Float),
        sa.Column("entry_level_avg_salary", sa.Integer),
        sa.Column("mid_career_avg_salary", sa.Integer),
        sa.Column("senior_avg_salary", sa.Integer),
        sa.Column("top_industries", JSONB),
        sa.Column("top_job_titles", JSONB),
        sa.Column("top_cities", JSONB),
        sa.Column("job_market_demand", sa.String(20)),
        sa.Column("year", sa.Integer, nullable=False, default=2024),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "last_updated", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    # ==================== STUDENT REVIEWS (6 tables) ====================
    op.create_table(
        "student_reviews",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            sa.String,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "university_id",
            UUID(as_uuid=True),
            sa.ForeignKey("universities.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "department_id",
            UUID(as_uuid=True),
            sa.ForeignKey("departments.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "dormitory_id",
            UUID(as_uuid=True),
            sa.ForeignKey("dormitory_info.id", ondelete="CASCADE"),
        ),
        sa.Column("review_type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("overall_rating", sa.Float, nullable=False),
        sa.Column("education_quality_rating", sa.Float),
        sa.Column("campus_life_rating", sa.Float),
        sa.Column("facilities_rating", sa.Float),
        sa.Column("is_anonymous", sa.Boolean, default=False),
        sa.Column("is_verified", sa.Boolean, default=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("helpful_count", sa.Integer, default=0),
        sa.Column(
            "moderated_by", sa.String, sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "review_ratings",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "review_id",
            UUID(as_uuid=True),
            sa.ForeignKey("student_reviews.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("rating", sa.Float, nullable=False),
        sa.Column("comment", sa.Text),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "review_votes",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "review_id",
            UUID(as_uuid=True),
            sa.ForeignKey("student_reviews.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("vote_type", sa.String(10), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "review_reports",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "review_id",
            UUID(as_uuid=True),
            sa.ForeignKey("student_reviews.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "reporter_id",
            sa.String,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reason", sa.String(50), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column(
            "resolved_by", sa.String, sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "review_statistics",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column(
            "university_id",
            UUID(as_uuid=True),
            sa.ForeignKey("universities.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "department_id",
            UUID(as_uuid=True),
            sa.ForeignKey("departments.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "dormitory_id",
            UUID(as_uuid=True),
            sa.ForeignKey("dormitory_info.id", ondelete="CASCADE"),
        ),
        sa.Column("total_reviews", sa.Integer, default=0),
        sa.Column("average_rating", sa.Float, default=0.0),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "moderation_queue",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "review_id",
            UUID(as_uuid=True),
            sa.ForeignKey("student_reviews.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reason", sa.String(50), nullable=False),
        sa.Column("auto_flagged", sa.Boolean, default=False),
        sa.Column("priority", sa.String(20), default="normal"),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column(
            "moderator_id", sa.String, sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
    )


def downgrade():
    for t in [
        "moderation_queue",
        "review_statistics",
        "review_reports",
        "review_votes",
        "review_ratings",
        "student_reviews",
        "department_statistics",
        "sector_analyses",
        "salary_expectations",
        "career_opportunities",
        "department_curricula",
        "university_statistics",
        "scholarship_programs",
        "dormitory_info",
        "city_living_costs",
        "campus_info",
        "user_university_preferences",
        "program_score_history",
        "university_programs",
        "departments",
        "universities",
    ]:
        op.drop_table(t)
