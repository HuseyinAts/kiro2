"""Fix BKTState column types: student_id and topic_id Integer -> VARCHAR

users.id is UUID (String), primary_topic_id is String — BKTState PK columns
must match.

Revision ID: c1d2e3f4a5b6
Revises: 7c540cf490c2
Create Date: 2026-03-20
"""

from alembic import op

revision = "c1d2e3f4a5b6"
down_revision = "7c540cf490c2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE bkt_states
          ALTER COLUMN student_id TYPE VARCHAR USING student_id::text,
          ALTER COLUMN topic_id   TYPE VARCHAR USING topic_id::text
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE bkt_states
          ALTER COLUMN student_id TYPE INTEGER USING student_id::integer,
          ALTER COLUMN topic_id   TYPE INTEGER USING topic_id::integer
        """
    )
