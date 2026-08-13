"""add FK student_answers.question_id -> question_bank.id

Bağlam: 2026-06-10 DB audit — student_answers.question_id FK'siz idi; load-test
161K orphan satır birikmişti (temizlendi, R1). Bu FK gelecekteki orphan/junk
insert'i DB seviyesinde engeller. Tablo boş olduğundan anında valid.
Idempotent (pg_constraint guard) — ad-hoc eklendiyse no-op.

Revision ID: c3d2e1f0a9b8
Revises: b2f1a9c7d3e4
Create Date: 2026-06-10
"""

from alembic import op

revision = "c3d2e1f0a9b8"
down_revision = "b2f1a9c7d3e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='student_answers_question_id_fkey') THEN
            ALTER TABLE student_answers
              ADD CONSTRAINT student_answers_question_id_fkey
              FOREIGN KEY (question_id) REFERENCES question_bank(id);
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE student_answers DROP CONSTRAINT IF EXISTS student_answers_question_id_fkey"
    )
