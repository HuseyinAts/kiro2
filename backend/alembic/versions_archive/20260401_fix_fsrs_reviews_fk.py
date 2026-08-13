"""Fix fsrs_reviews card_id FK

fsrs_cards tablosu olmadan yaratildiginda FK eklenemedi.
fsrs_cards artik mevcut — FK kısıtını ekliyoruz.

Revision ID: 20260401_fix_fsrs_reviews_fk
Revises: 20260401_add_missing_tables
Create Date: 2026-04-01
"""

from collections.abc import Sequence
from typing import Union

from alembic import op

revision: str = "20260401_fix_fsrs_reviews_fk"
down_revision: Union[str, None] = "20260401_add_missing_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # fsrs_reviews.card_id -> fsrs_cards.id (CASCADE)
    # fsrs_cards artik mevcut oldugu icin eklenebilir
    op.create_foreign_key(
        "fsrs_reviews_card_id_fkey",
        "fsrs_reviews",
        "fsrs_cards",
        ["card_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fsrs_reviews_card_id_fkey",
        "fsrs_reviews",
        type_="foreignkey",
    )
