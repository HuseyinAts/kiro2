"""Partial index for beta verified_provisional pool selection

Revision ID: beta_vp_idx_20260602
Revises: sqf_flagtype_2new_20260602
Create Date: 2026-06-02

_select_beta_questions sorgusu (is_active=true AND
pipeline_metadata->>'verified_provisional'='true') 187K satirda Seq Scan ile
~3.5s cold suruyordu (beta-start yavasligi). Partial Index Only Scan ile
~11ms (~320x). 2,734 satir eslesir, index minik.

CONCURRENTLY → tablo lock yok (prod-safe). IF NOT EXISTS → canlida elle
olusturulmus index'le cakismaz.
"""

from alembic import op

revision = "beta_vp_idx_20260602"
down_revision = "sqf_flagtype_2new_20260602"
branch_labels = None
depends_on = None

_INDEX = "idx_qbank_verified_provisional"


def upgrade() -> None:
    # CONCURRENTLY transaction icinde calismaz → autocommit block
    with op.get_context().autocommit_block():
        op.execute(
            f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {_INDEX} "
            "ON question_bank (id) "
            "WHERE is_active = true "
            "AND (pipeline_metadata->>'verified_provisional') = 'true'"
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {_INDEX}")
