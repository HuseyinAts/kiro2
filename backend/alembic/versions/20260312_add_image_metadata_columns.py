"""Add image metadata columns to question_bank.

- image_ocr_text: OCR text from crop images (accessibility alt-text)
- image_width: crop image width in pixels
- image_height: crop image height in pixels

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-03-12
"""

from alembic import op

revision = "b3c4d5e6f7a8"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # IF NOT EXISTS: columns may already exist (added via direct SQL in dev)
    op.execute(
        "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS image_ocr_text TEXT"
    )
    op.execute(
        "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS image_width INTEGER"
    )
    op.execute(
        "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS image_height INTEGER"
    )


def downgrade() -> None:
    op.drop_column("question_bank", "image_height")
    op.drop_column("question_bank", "image_width")
    op.drop_column("question_bank", "image_ocr_text")
