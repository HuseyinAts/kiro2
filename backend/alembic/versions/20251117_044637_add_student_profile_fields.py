"""Add hedef_sinav and veli_onay to student_profiles

Revision ID: 20251117_044637
Revises: 20251117_032216
Create Date: 2025-11-17 04:46:37

TODO Fix Implementation - Add missing profile fields
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251117_044637'
down_revision = '20251117_032216'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add hedef_sinav and veli_onay columns to student_profiles table"""

    # Add hedef_sinav column (target exam: TYT, AYT, YDT, LGS)
    op.add_column(
        'student_profiles',
        sa.Column('hedef_sinav', sa.String(length=20), nullable=True)
    )

    # Add veli_onay column (parent approval for data collection)
    op.add_column(
        'student_profiles',
        sa.Column('veli_onay', sa.Boolean(), nullable=False, server_default='1')
    )


def downgrade() -> None:
    """Remove hedef_sinav and veli_onay columns from student_profiles table"""

    op.drop_column('student_profiles', 'veli_onay')
    op.drop_column('student_profiles', 'hedef_sinav')
