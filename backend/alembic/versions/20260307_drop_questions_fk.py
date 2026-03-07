"""Drop FK constraints from exam_questions and student_answers pointing to questions table.

Engine now queries question_bank (77K questions) instead of questions (empty).

Revision ID: a1b2c3d4e5f6
Revises: 63ca2329af07
Create Date: 2026-03-07
"""

from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = "63ca2329af07"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop FK from exam_questions.question_id -> questions.id
    op.drop_constraint(
        "exam_questions_question_id_fkey", "exam_questions", type_="foreignkey"
    )
    # Drop FK from student_answers.question_id -> questions.id
    op.drop_constraint(
        "student_answers_question_id_fkey", "student_answers", type_="foreignkey"
    )


def downgrade() -> None:
    # Restore FK constraints (pointing back to questions table)
    op.create_foreign_key(
        "exam_questions_question_id_fkey",
        "exam_questions",
        "questions",
        ["question_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "student_answers_question_id_fkey",
        "student_answers",
        "questions",
        ["question_id"],
        ["id"],
        ondelete="CASCADE",
    )
