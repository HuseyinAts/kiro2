"""Add error_type column to student_answers table

F8: Error Taxonomy — data collection foundation for F6 (coaching), F11 (DINA), F15 (clustering)

Revision ID: f8_error_type_001
Revises: 20260307_drop_questions_fk
Create Date: 2026-03-12
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "f8_error_type_001"
down_revision = "20260307_drop_questions_fk"
branch_labels = None
depends_on = None

VALID_ERROR_TYPES = ("concept", "procedural", "careless", "knowledge_gap")


def upgrade() -> None:
    # Add error_type column (nullable — students may not classify every answer)
    op.add_column(
        "student_answers",
        sa.Column("error_type", sa.String(20), nullable=True),
    )

    # Add check constraint for valid values
    op.create_check_constraint(
        "check_error_type",
        "student_answers",
        "error_type IS NULL OR error_type IN ('concept', 'procedural', 'careless', 'knowledge_gap')",
    )

    # Add index for error_type queries (F15 clustering aggregation)
    op.create_index(
        "idx_student_answer_error_type",
        "student_answers",
        ["error_type"],
    )


def downgrade() -> None:
    op.drop_index("idx_student_answer_error_type", table_name="student_answers")
    op.drop_constraint("check_error_type", "student_answers", type_="check")
    op.drop_column("student_answers", "error_type")
