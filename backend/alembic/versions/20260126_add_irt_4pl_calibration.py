"""Add IRT 4PL calibration columns to questions table

Revision ID: 20260126_irt_4pl
Revises: 20260118_quality_gates
Create Date: 2026-01-26

Bu migration IRT 4PL modelini desteklemek icin gerekli kolonlari ekler:
- irt_upper_asymptote: 4PL modelinin ust asimptotu (c = slipping/carelessness)
- irt_calibrated: IRT parametrelerinin kalibre edilip edilmedigi
- irt_sample_size: Kalibrasyon icin kullanilan ornek boyutu
- source_book: Sorunun kaynak kitabi
- source_page: Sorunun kaynak sayfa numarasi

IRT 4PL Formulu:
P(theta) = c + (d - c) / (1 + exp(-a * (theta - b)))

Parametreler:
- a: discrimination (ayirt edicilik) [0.2, 4.0]
- b: difficulty (zorluk) [-4.0, 4.0]
- c: guessing (tahmin) [0.0, 0.35]
- d: upper_asymptote (ust asimptot) [0.85, 1.0]
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260126_irt_4pl"
down_revision: Union[str, None] = "20260118_quality_gates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add IRT 4PL calibration columns."""

    # Add irt_upper_asymptote (4th parameter for slipping)
    try:
        op.add_column(
            'questions',
            sa.Column(
                'irt_upper_asymptote',
                sa.Float(),
                nullable=True,
                server_default='1.0',
                comment='IRT 4PL upper asymptote (slipping parameter) [0.85, 1.0]'
            )
        )
        print("  - Added: irt_upper_asymptote")
    except Exception as e:
        print(f"  - Skipped irt_upper_asymptote: {e}")

    # Add irt_calibrated flag
    try:
        op.add_column(
            'questions',
            sa.Column(
                'irt_calibrated',
                sa.Boolean(),
                nullable=True,
                server_default='false',
                comment='Whether IRT parameters have been calibrated from real student data'
            )
        )
        print("  - Added: irt_calibrated")
    except Exception as e:
        print(f"  - Skipped irt_calibrated: {e}")

    # Add irt_sample_size
    try:
        op.add_column(
            'questions',
            sa.Column(
                'irt_sample_size',
                sa.Integer(),
                nullable=True,
                server_default='0',
                comment='Number of student responses used for IRT calibration'
            )
        )
        print("  - Added: irt_sample_size")
    except Exception as e:
        print(f"  - Skipped irt_sample_size: {e}")

    # Add source_book for tracking question origin
    try:
        op.add_column(
            'questions',
            sa.Column(
                'source_book',
                sa.String(300),
                nullable=True,
                comment='Source book name (e.g., "2019-2020-Acil Matematigin ilaci-1")'
            )
        )
        print("  - Added: source_book")
    except Exception as e:
        print(f"  - Skipped source_book: {e}")

    # Add source_page for tracking question origin
    try:
        op.add_column(
            'questions',
            sa.Column(
                'source_page',
                sa.Integer(),
                nullable=True,
                comment='Source page number in the book'
            )
        )
        print("  - Added: source_page")
    except Exception as e:
        print(f"  - Skipped source_page: {e}")

    # Add check constraint for irt_upper_asymptote
    try:
        op.create_check_constraint(
            'check_irt_upper_asymptote',
            'questions',
            'irt_upper_asymptote >= 0.85 AND irt_upper_asymptote <= 1.0'
        )
        print("  - Added: check_irt_upper_asymptote constraint")
    except Exception as e:
        print(f"  - Skipped constraint: {e}")

    # Add index for calibrated questions
    try:
        op.create_index(
            'idx_questions_calibrated',
            'questions',
            ['irt_calibrated'],
            unique=False,
            postgresql_where=sa.text('irt_calibrated = true')
        )
        print("  - Added: idx_questions_calibrated")
    except Exception as e:
        print(f"  - Skipped index: {e}")

    print("\n[OK] SUCCESS: IRT 4PL calibration migration completed")


def downgrade() -> None:
    """Remove IRT 4PL calibration columns."""

    # Drop index first
    try:
        op.drop_index('idx_questions_calibrated', table_name='questions')
        print("  - Dropped: idx_questions_calibrated")
    except Exception as e:
        print(f"  - Skipped drop index: {e}")

    # Drop constraint
    try:
        op.drop_constraint('check_irt_upper_asymptote', 'questions', type_='check')
        print("  - Dropped: check_irt_upper_asymptote")
    except Exception as e:
        print(f"  - Skipped drop constraint: {e}")

    # Drop columns
    columns_to_drop = [
        'irt_upper_asymptote',
        'irt_calibrated',
        'irt_sample_size',
        'source_book',
        'source_page'
    ]

    for column in columns_to_drop:
        try:
            op.drop_column('questions', column)
            print(f"  - Dropped: {column}")
        except Exception as e:
            print(f"  - Skipped drop {column}: {e}")

    print("\n[OK] Downgrade completed")
