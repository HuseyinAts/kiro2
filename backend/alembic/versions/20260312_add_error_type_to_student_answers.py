"""Add error_type column to student_answers table

F8: Error Taxonomy — data collection foundation for F6 (coaching), F11 (DINA), F15 (clustering)

Revision ID: f8_error_type_001
Revises: a1b2c3d4e5f6
Create Date: 2026-03-12
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers
revision = "f8_error_type_001"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None

VALID_ERROR_TYPES = ("concept", "procedural", "careless", "knowledge_gap")


def _column_exists(table: str, column: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
            "WHERE table_name=:table AND column_name=:column)"
        ),
        {"table": table, "column": column},
    )
    return result.scalar()


def _index_exists(name: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname=:name)"),
        {"name": name},
    )
    return result.scalar()


def _constraint_exists(name: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.table_constraints "
            "WHERE constraint_name=:name)"
        ),
        {"name": name},
    )
    return result.scalar()


def upgrade() -> None:
    # Add error_type column (nullable — students may not classify every answer)
    if not _column_exists("student_answers", "error_type"):
        op.add_column(
            "student_answers",
            sa.Column("error_type", sa.String(20), nullable=True),
        )

    # Add check constraint for valid values
    if not _constraint_exists("check_error_type"):
        op.create_check_constraint(
            "check_error_type",
            "student_answers",
            "error_type IS NULL OR error_type IN ('concept', 'procedural', 'careless', 'knowledge_gap')",
        )

    # Add index for error_type queries (F15 clustering aggregation)
    if not _index_exists("idx_student_answer_error_type"):
        op.create_index(
            "idx_student_answer_error_type",
            "student_answers",
            ["error_type"],
        )


def downgrade() -> None:
    op.drop_index("idx_student_answer_error_type", table_name="student_answers")
    op.drop_constraint("check_error_type", "student_answers", type_="check")
    op.drop_column("student_answers", "error_type")
