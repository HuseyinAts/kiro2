"""add_performance_indexes

Revision ID: f1954b057565
Revises: 0003_restore_user_item_fsrs
Create Date: 2026-09-08 15:24:35.440075

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1954b057565'
down_revision: Union[str, None] = '0003_restore_user_item_fsrs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # question_metadata: AI soru secimi ve filtreleme icin kompozit indeks
    op.create_index('idx_qmeta_exam_subject', 'question_metadata', ['exam_type', 'subject_area'])

    # question_statistics: IRT algoritmasi zorluk analizleri icin indeks
    op.create_index('idx_qstats_irt_diff', 'question_statistics', ['irt_difficulty'])


def downgrade() -> None:
    op.drop_index('idx_qstats_irt_diff', table_name='question_statistics')
    op.drop_index('idx_qmeta_exam_subject', table_name='question_metadata')
