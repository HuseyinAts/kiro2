"""Change quiz_questions.question_id FK from questions to question_bank

quiz_questions table is empty (0 rows) so this migration is safe.
The model was already updated in Session 89 (commit 3bda7a6).

Revision ID: qz_fk_qbank_001
Revises: 5e00e4fca928
Create Date: 2026-03-14
"""

from alembic import op

# revision identifiers
revision = "qz_fk_qbank_001"
down_revision = "5e00e4fca928"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old FK pointing to empty 'questions' table
    op.drop_constraint(
        "quiz_questions_question_id_fkey", "quiz_questions", type_="foreignkey"
    )
    # Create new FK pointing to production 'question_bank' table (77,336 questions)
    op.create_foreign_key(
        "quiz_questions_question_id_fkey",
        "quiz_questions",
        "question_bank",
        ["question_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "quiz_questions_question_id_fkey", "quiz_questions", type_="foreignkey"
    )
    op.create_foreign_key(
        "quiz_questions_question_id_fkey",
        "quiz_questions",
        "questions",
        ["question_id"],
        ["id"],
    )
