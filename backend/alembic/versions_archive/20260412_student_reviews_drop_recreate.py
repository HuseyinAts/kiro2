"""drop and recreate student_reviews + 5 sibling tables to match ORM

Revision ID: student_review_drift_001
Revises: osb_access_001
Create Date: 2026-04-12

GF106 Task C (Session 154) — Wave 12 (Session 148) flagged massive schema
drift between the `models/student_review.py` ORM and the live DB:

- `student_reviews` ORM declared ~33 columns but live table only had 19.
  Missing: `professor_id`, `course_id`, `pros`, `cons`, `tags`,
  `student_year`, `enrollment_year`, `is_current_student`, `is_alumni`,
  `moderation_notes`, `moderated_at`, `spam_score`, `quality_score`,
  `contains_profanity`, `contains_contact_info`, `is_too_short`,
  `verification_method`, `verified_at`, `not_helpful_count`, `report_count`,
  `view_count`, `language`, `ip_address`, `user_agent`, `published_at`,
  `social_life_rating`. Plus `id` was `uuid` in DB but ORM declared
  `String(UUID-as-str)` → asyncpg inverse-rule-of-seven crash.
- `review_votes` DB had `vote_type varchar`, ORM expects `is_helpful bool`.
- `review_statistics` DB had `entity_type`, ORM expects `review_type` +
  11 missing columns (verified_reviews, rating_1..5_count,
  category_averages, total_helpful_votes, total_views,
  positive_percentage, negative_percentage, top_tags, last_updated).
- `moderation_queue` DB had `reason`/`auto_flagged`/`moderator_id`/
  `resolved_at`, ORM expects `flag_reasons`/`assigned_to`/`assigned_at`/
  `completed_at` + `priority` type mismatch (varchar vs Integer).

Session 148 installed a 503 degradation shim at the handler boundary in
`api/student_review_routes.py:create_review` to keep the Golden Flow
suite green. Session 154 removes that shim.

All 6 tables had **0 rows** at migration time, so the safest path is
`DROP TABLE ... CASCADE` + recreate to match the fixed ORM exactly.
The drop is not reversible but the tables were empty and no production
data is at risk.

Additional ORM fixes applied in `models/student_review.py`:
- All 6 `id` columns: `UUID(as_uuid=True)` + `default=uuid4` (was
  `String` + `default=lambda: str(uuid4())`). Matches the DB's native
  `uuid` type. Session 153 GF115 inverse-rule-of-seven precedent.
- `university_id` / `department_id` / `dormitory_id` on StudentReview
  and ReviewStatistics: `UUID(as_uuid=True)` to match target PK types.
- All `SQLEnum(...)` columns replaced with `String(n)` to avoid
  creating native PG enum types. Python enum validation still happens
  at the API layer. Matches canonical KIRO2 enum-as-string pattern.
- `user_id` / `moderated_by` / `reporter_id` / `resolved_by` /
  `assigned_to` remain `String` because `users.id` is `varchar`.
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision = "student_review_drift_001"
down_revision = "osb_access_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop existing tables (all empty — see Session 148 audit).
    # CASCADE handles FK dependencies between the 6 tables.
    op.execute("DROP TABLE IF EXISTS moderation_queue CASCADE")
    op.execute("DROP TABLE IF EXISTS review_statistics CASCADE")
    op.execute("DROP TABLE IF EXISTS review_reports CASCADE")
    op.execute("DROP TABLE IF EXISTS review_votes CASCADE")
    op.execute("DROP TABLE IF EXISTS review_ratings CASCADE")
    op.execute("DROP TABLE IF EXISTS student_reviews CASCADE")

    # student_reviews — parent table
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
            sa.String(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("review_type", sa.String(50), nullable=False),
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
        sa.Column("professor_id", sa.String()),
        sa.Column("course_id", sa.String()),
        sa.Column(
            "dormitory_id",
            UUID(as_uuid=True),
            sa.ForeignKey("dormitory_info.id", ondelete="CASCADE"),
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("overall_rating", sa.Float(), nullable=False),
        sa.Column("pros", JSONB(), server_default=sa.text("'[]'::jsonb")),
        sa.Column("cons", JSONB(), server_default=sa.text("'[]'::jsonb")),
        sa.Column("tags", JSONB(), server_default=sa.text("'[]'::jsonb")),
        sa.Column("student_year", sa.Integer()),
        sa.Column("enrollment_year", sa.Integer()),
        sa.Column("is_current_student", sa.Boolean(), server_default=sa.true()),
        sa.Column("is_alumni", sa.Boolean(), server_default=sa.false()),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("moderation_notes", sa.Text()),
        sa.Column(
            "moderated_by",
            sa.String(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("moderated_at", sa.DateTime(timezone=True)),
        sa.Column("spam_score", sa.Float(), server_default="0.0"),
        sa.Column("quality_score", sa.Float(), server_default="0.5"),
        sa.Column("contains_profanity", sa.Boolean(), server_default=sa.false()),
        sa.Column("contains_contact_info", sa.Boolean(), server_default=sa.false()),
        sa.Column("is_too_short", sa.Boolean(), server_default=sa.false()),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.false()),
        sa.Column("verification_method", sa.String(100)),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("helpful_count", sa.Integer(), server_default="0"),
        sa.Column("not_helpful_count", sa.Integer(), server_default="0"),
        sa.Column("report_count", sa.Integer(), server_default="0"),
        sa.Column("view_count", sa.Integer(), server_default="0"),
        sa.Column("language", sa.String(10), server_default="tr"),
        sa.Column("ip_address", sa.String(50)),
        sa.Column("user_agent", sa.String(255)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("published_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_student_reviews_user", "student_reviews", ["user_id"])
    op.create_index("idx_student_reviews_type", "student_reviews", ["review_type"])
    op.create_index(
        "idx_student_reviews_university", "student_reviews", ["university_id"]
    )
    op.create_index(
        "idx_student_reviews_department", "student_reviews", ["department_id"]
    )
    op.create_index("idx_student_reviews_status", "student_reviews", ["status"])
    op.create_index("idx_student_reviews_rating", "student_reviews", ["overall_rating"])
    op.create_index("idx_student_reviews_created", "student_reviews", ["created_at"])
    op.create_index("idx_student_reviews_verified", "student_reviews", ["is_verified"])

    # review_ratings
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
        sa.Column("rating", sa.Float(), nullable=False),
        sa.Column("comment", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_review_ratings_review", "review_ratings", ["review_id"])
    op.create_index("idx_review_ratings_category", "review_ratings", ["category"])
    op.create_index("idx_review_ratings_rating", "review_ratings", ["rating"])
    op.create_index(
        "idx_review_ratings_unique",
        "review_ratings",
        ["review_id", "category"],
        unique=True,
    )

    # review_votes
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
            sa.String(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("is_helpful", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_review_votes_review", "review_votes", ["review_id"])
    op.create_index("idx_review_votes_user", "review_votes", ["user_id"])
    op.create_index(
        "idx_review_votes_unique",
        "review_votes",
        ["review_id", "user_id"],
        unique=True,
    )

    # review_reports
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
            sa.String(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reason", sa.String(50), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column(
            "resolved_by",
            sa.String(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("resolution_notes", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_review_reports_review", "review_reports", ["review_id"])
    op.create_index("idx_review_reports_reporter", "review_reports", ["reporter_id"])
    op.create_index("idx_review_reports_status", "review_reports", ["status"])
    op.create_index("idx_review_reports_reason", "review_reports", ["reason"])

    # review_statistics
    op.create_table(
        "review_statistics",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("review_type", sa.String(50), nullable=False),
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
        sa.Column("total_reviews", sa.Integer(), server_default="0"),
        sa.Column("verified_reviews", sa.Integer(), server_default="0"),
        sa.Column("average_rating", sa.Float()),
        sa.Column("rating_1_count", sa.Integer(), server_default="0"),
        sa.Column("rating_2_count", sa.Integer(), server_default="0"),
        sa.Column("rating_3_count", sa.Integer(), server_default="0"),
        sa.Column("rating_4_count", sa.Integer(), server_default="0"),
        sa.Column("rating_5_count", sa.Integer(), server_default="0"),
        sa.Column("category_averages", JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column("total_helpful_votes", sa.Integer(), server_default="0"),
        sa.Column("total_views", sa.Integer(), server_default="0"),
        sa.Column("positive_percentage", sa.Float()),
        sa.Column("negative_percentage", sa.Float()),
        sa.Column("top_tags", JSONB(), server_default=sa.text("'[]'::jsonb")),
        sa.Column(
            "last_updated",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_review_statistics_type", "review_statistics", ["review_type"])
    op.create_index(
        "idx_review_statistics_university", "review_statistics", ["university_id"]
    )
    op.create_index(
        "idx_review_statistics_department", "review_statistics", ["department_id"]
    )
    op.create_index(
        "idx_review_statistics_rating", "review_statistics", ["average_rating"]
    )

    # moderation_queue
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
        sa.Column("priority", sa.Integer(), server_default="0"),
        sa.Column("flag_reasons", JSONB(), server_default=sa.text("'[]'::jsonb")),
        sa.Column(
            "assigned_to",
            sa.String(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("assigned_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_moderation_queue_review", "moderation_queue", ["review_id"])
    op.create_index("idx_moderation_queue_status", "moderation_queue", ["status"])
    op.create_index("idx_moderation_queue_priority", "moderation_queue", ["priority"])
    op.create_index(
        "idx_moderation_queue_assigned", "moderation_queue", ["assigned_to"]
    )


def downgrade() -> None:
    # Drop the recreated tables. Downgrade cannot restore the original
    # drifted schema — it was incomplete anyway and all 6 tables were
    # empty at migration time, so there is nothing meaningful to
    # restore. The downgrade simply tears down what upgrade() built.
    op.drop_table("moderation_queue")
    op.drop_table("review_statistics")
    op.drop_table("review_reports")
    op.drop_table("review_votes")
    op.drop_table("review_ratings")
    op.drop_table("student_reviews")
