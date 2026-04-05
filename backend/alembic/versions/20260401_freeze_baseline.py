"""Freeze baseline — ORM/DB drift korumasi tamamlandi

Bu migration HICBIR SEY YAPMAZ.
Amaci: 01 Nisan 2026 itibarıyla mevcut DB state'ini Alembic'e bildirmek.

Yapilan korumalar (alembic/env.py):
- include_object: 12 DB-only tablo autogenerate'den haric tutuldu
- compare_type=False: VARCHAR/String, NUMERIC/Float tip gurultusu susturuldu
- compare_server_default=False: server default gurultusu susturuldu

ORM'e eklenen korunan kolonlar (question_bank.py):
- QuestionBankItem: irt_a, irt_b, irt_c, irt_calibrated, irt_calibrated_at,
                   irt_n_responses, irt_method, is_calib_pool  (CAT engine)
- TopicHierarchy: difficulty_level, subject_area  (legacy)

KURAL: Bundan sonra migration eklemeden once:
  1. alembic check calistir, ciktıyı MANUEL incele
  2. ASLA `alembic revision --autogenerate` calistirma
  3. Sadece `alembic revision -m "aciklama"` (bos) kullan

Revision ID: freeze_baseline_20260401
Revises: learning_events_001
Create Date: 2026-04-01
"""

from collections.abc import Sequence
from typing import Union

from alembic import op

revision: str = "freeze_baseline_20260401"
down_revision: Union[str, None] = "learning_events_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Bu migration kasıtlı olarak bostur.
    # Gelecekteki autogenerate calistirmalarına karsi temiz baseline noktasi.
    pass


def downgrade() -> None:
    pass