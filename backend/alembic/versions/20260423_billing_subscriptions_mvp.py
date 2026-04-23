"""billing_subscriptions MVP table (entitlement kaydı)

Revision ID: billing_subscriptions_mvp_20260423
Revises: diary_drift_recovery_20260422

Ödeme sağlayıcı entegrasyonu öncesi: kullanıcı başına tek satır abonelik özeti.
Webhook veya iç araçlar `users.is_premium` + bu tabloyu güncelleyebilir.

"""

from collections.abc import Sequence
from typing import Union

from alembic import op

revision: str = "billing_subscriptions_mvp_20260423"
down_revision: Union[str, None] = "diary_drift_recovery_20260422"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS billing_subscriptions (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL UNIQUE
                REFERENCES users(id) ON DELETE CASCADE,
            plan_code VARCHAR(32) NOT NULL DEFAULT 'free',
            status VARCHAR(24) NOT NULL DEFAULT 'inactive',
            provider VARCHAR(32),
            external_customer_id VARCHAR(255),
            current_period_end TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_billing_subscriptions_user_id
        ON billing_subscriptions (user_id);
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_billing_subscriptions_user_id")
    op.execute("DROP TABLE IF EXISTS billing_subscriptions")
