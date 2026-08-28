"""create 58 missing tables and fix uuid to varchar types

Revision ID: 20260406_create_missing_tables
Revises: 20260406_uni_dept
Create Date: 2026-04-06

Tables created via Base.metadata.create_all(checkfirst=True).
UUID->String type fixes applied to 18 model files (218 replacements).
9 empty tables with UUID PKs were dropped and recreated as VARCHAR.
3 tables with data kept as-is (kiro2_cat_sessions, kiro2_learning_events, topic_prerequisites).
"""

from collections.abc import Sequence
from typing import Union

# revision identifiers
revision: str = "20260406_create_missing_tables"
down_revision: Union[str, None] = "20260406_uni_dept"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tables already created via create_all script
    pass


def downgrade() -> None:
    # Not reversible - too many tables
    pass
