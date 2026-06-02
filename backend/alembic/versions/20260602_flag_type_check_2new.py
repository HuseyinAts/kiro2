"""Extend student_question_flags flag_type CHECK with 'circular' + 'figure_needed'

Revision ID: sqf_flagtype_2new_20260602
Revises: kvkk2_veli_consent_20260529
Create Date: 2026-06-02

Commit c4d801884 added two new flag reasons ('circular', 'figure_needed') to
the frontend + backend Literal enum but the DB CHECK constraint
(student_question_flags_flag_type_check) still only allowed the original five
types. Beta students reporting "figür gerekiyor" / "dairesel soru" hit a
CheckViolationError surfaced as a generic 400. This migration rebuilds the
constraint to include all seven types.
"""

from alembic import op

revision = "sqf_flagtype_2new_20260602"
down_revision = "kvkk2_veli_consent_20260529"
branch_labels = None
depends_on = None

_OLD = ("wrong_answer", "wrong_topic", "solution_visible", "incomplete_text", "other")
_NEW = (
    "wrong_answer",
    "wrong_topic",
    "solution_visible",
    "incomplete_text",
    "circular",
    "figure_needed",
    "other",
)


def _check(values: tuple[str, ...]) -> str:
    joined = ", ".join(f"'{v}'" for v in values)
    return f"flag_type IN ({joined})"


def upgrade() -> None:
    op.execute(
        "ALTER TABLE student_question_flags "
        "DROP CONSTRAINT IF EXISTS student_question_flags_flag_type_check"
    )
    op.create_check_constraint(
        "student_question_flags_flag_type_check",
        "student_question_flags",
        _check(_NEW),
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE student_question_flags "
        "DROP CONSTRAINT IF EXISTS student_question_flags_flag_type_check"
    )
    op.create_check_constraint(
        "student_question_flags_flag_type_check",
        "student_question_flags",
        _check(_OLD),
    )
