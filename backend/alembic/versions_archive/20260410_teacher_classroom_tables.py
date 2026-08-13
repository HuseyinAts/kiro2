"""add teacher classroom tables

Revision ID: teacher_classroom_001
Revises: dungeon_progress_001
Create Date: 2026-04-10

Creates 5 new tables for teacher classroom management:
  - teacher_classrooms
  - teacher_classroom_students
  - teacher_exam_configs
  - teacher_assignments
  - teacher_contents
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision = "teacher_classroom_001"
down_revision = "dungeon_progress_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "teacher_classrooms",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("teacher_user_id", sa.String(), nullable=False),
        sa.Column("sinif_adi", sa.String(100), nullable=False),
        sa.Column("seviye", sa.String(10), nullable=False),
        sa.Column("ders", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_teacher_classrooms_teacher_user_id",
        "teacher_classrooms",
        ["teacher_user_id"],
    )

    op.create_table(
        "teacher_classroom_students",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "classroom_id",
            UUID(as_uuid=True),
            sa.ForeignKey("teacher_classrooms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("student_user_id", sa.String(), nullable=False),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_teacher_classroom_students_classroom_id",
        "teacher_classroom_students",
        ["classroom_id"],
    )

    op.create_table(
        "teacher_exam_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("teacher_user_id", sa.String(), nullable=False),
        sa.Column("baslik", sa.String(200), nullable=False),
        sa.Column("aciklama", sa.Text(), nullable=True),
        sa.Column("sinav_tipi", sa.String(10), nullable=False),
        sa.Column("soru_sayisi", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("sure_dakika", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("durum", sa.String(20), nullable=False, server_default="taslak"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_teacher_exam_configs_teacher_user_id",
        "teacher_exam_configs",
        ["teacher_user_id"],
    )

    op.create_table(
        "teacher_assignments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("teacher_user_id", sa.String(), nullable=False),
        sa.Column("baslik", sa.String(200), nullable=False),
        sa.Column("aciklama", sa.Text(), nullable=True),
        sa.Column("sinif", sa.String(50), nullable=True),
        sa.Column("teslim_tarihi", sa.DateTime(), nullable=True),
        sa.Column("durum", sa.String(20), nullable=False, server_default="aktif"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_teacher_assignments_teacher_user_id",
        "teacher_assignments",
        ["teacher_user_id"],
    )

    op.create_table(
        "teacher_contents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("teacher_user_id", sa.String(), nullable=False),
        sa.Column("baslik", sa.String(200), nullable=False),
        sa.Column("aciklama", sa.Text(), nullable=True),
        sa.Column("tip", sa.String(20), nullable=False, server_default="diger"),
        sa.Column("konu", sa.String(100), nullable=True),
        sa.Column("sinif", sa.String(50), nullable=True),
        sa.Column("goruntulenme", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_teacher_contents_teacher_user_id", "teacher_contents", ["teacher_user_id"]
    )


def downgrade() -> None:
    op.drop_table("teacher_contents")
    op.drop_table("teacher_assignments")
    op.drop_table("teacher_exam_configs")
    op.drop_table("teacher_classroom_students")
    op.drop_table("teacher_classrooms")
