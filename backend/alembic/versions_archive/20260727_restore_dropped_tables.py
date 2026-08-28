"""c555a10f4b93'ün düşürdüğü canlı-kod tablolarını geri getir

Kök neden: `c555a10f4b93_sync_db_changes.py` bir `alembic revision --autogenerate`
çıktısıdır ve `upgrade()` gövdesinde 145 adet `DROP TABLE IF EXISTS ... CASCADE`
taşır (satır 47/85/89/108/193/209/285 buradaki tablolar). `env.py` target_metadata'sı
yalnızca `models.database.Base` olduğu için başka model modüllerindeki tablolar
(teacher_classroom.py) ve raw-SQL ile yaratılmış tablolar (billing_subscriptions)
autogenerate'e "modelde yok, fazlalık" göründü. `alembic_version` head'de kaldığı
için kayıp SESSİZ oldu.

Ölçüm (27 Tem 2026, `docker logs kiro2-backend --since 168h`): son 72 saatte
student_question_flags 160, teacher_classroom_students 84, billing_subscriptions 17,
teacher_exam_configs 14 kez `UndefinedTableError` fırlattı.

Tablo tanımları ORİJİNAL migration'lardan BİREBİR alındı — bu bir restore, yeniden
tasarım değil:
  - billing_subscriptions      <- 20260423_billing_subscriptions_mvp.py
  - student_question_flags     <- 20260517_student_question_flags.py
  - teacher_classroom_students,
    teacher_exam_configs,
    teacher_assignments,
    teacher_contents           <- 20260410_teacher_classroom_tables.py
`teacher_classrooms` canlıda MEVCUT (c555 onu da düşürmüş ama geri gelmiş) —
dokunulmuyor. `coppa_parental_consents` kapsam dışı (FERPA/COPPA router'ının
kaderi ayrı bir karar).

RLS: bu 6 tablonun hiçbirinde `organization_id` kolonu YOK, dolayısıyla 79-tablo
tenant_isolation deseni buraya uygulanamaz — politika icat etmek yerine kapsam dışı
bırakıldı. Kiracı izolasyonu iş emrinde (GUC beslemesi → kapsam → predicate) bu
tablolar organization_id ile birlikte ele alınacak. GRANT verilir: uygulama
`kiro2_app` non-superuser rolüyle bağlanıyor.

Idempotent: tablo zaten varsa atlanır (kısmi uygulanmış ortamlar için).

Revision ID: restore_dropped_tables_20260727
Revises: parent_link_codes_20260726
Create Date: 2026-07-27
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "restore_dropped_tables_20260727"
down_revision: Union[str, None] = "parent_link_codes_20260726"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

RESTORED_TABLES = (
    "billing_subscriptions",
    "student_question_flags",
    "teacher_classroom_students",
    "teacher_exam_configs",
    "teacher_assignments",
    "teacher_contents",
)

# 20260517_student_question_flags.py ile birebir aynı
VALID_FLAG_TYPES = (
    "wrong_answer",
    "wrong_topic",
    "solution_visible",
    "incomplete_text",
    "other",
)
VALID_RESOLUTIONS = (
    "confirmed",
    "rejected",
    "duplicate",
)


def _existing_tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    have = _existing_tables()

    if "billing_subscriptions" not in have:
        op.create_table(
            "billing_subscriptions",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "user_id",
                sa.String(36),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
                unique=True,
            ),
            sa.Column(
                "plan_code", sa.String(32), nullable=False, server_default="free"
            ),
            sa.Column(
                "status", sa.String(24), nullable=False, server_default="inactive"
            ),
            sa.Column("provider", sa.String(32), nullable=True),
            sa.Column("external_customer_id", sa.String(255), nullable=True),
            sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
        op.create_index(
            "ix_billing_subscriptions_user_id", "billing_subscriptions", ["user_id"]
        )

    if "student_question_flags" not in have:
        op.create_table(
            "student_question_flags",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("question_id", sa.String(), nullable=False),
            sa.Column("flag_type", sa.String(length=32), nullable=False),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("resolution", sa.String(length=32), nullable=True),
            sa.Column("resolved_by", sa.String(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(
                ["question_id"], ["question_bank.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.CheckConstraint(
                "flag_type IN " + str(VALID_FLAG_TYPES),
                name="student_question_flags_flag_type_check",
            ),
            sa.CheckConstraint(
                "(resolution IS NULL) OR (resolution IN "
                + str(VALID_RESOLUTIONS)
                + ")",
                name="student_question_flags_resolution_check",
            ),
        )
        op.create_index(
            "ix_student_question_flags_question_id",
            "student_question_flags",
            ["question_id"],
        )
        op.create_index(
            "ix_student_question_flags_user_created",
            "student_question_flags",
            ["user_id", "created_at"],
        )
        op.create_index(
            "ix_student_question_flags_unresolved",
            "student_question_flags",
            ["flag_type", "created_at"],
            postgresql_where=sa.text("resolved_at IS NULL"),
        )

    if "teacher_classroom_students" not in have:
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

    if "teacher_exam_configs" not in have:
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

    if "teacher_assignments" not in have:
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

    if "teacher_contents" not in have:
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
            "ix_teacher_contents_teacher_user_id",
            "teacher_contents",
            ["teacher_user_id"],
        )

    # GRANT — uygulama kiro2_app non-superuser rolüyle bağlanıyor.
    # ALTER DEFAULT PRIVILEGES zaten kapsıyor; bu belt-and-suspenders
    # (migration başka bir rolle koşarsa). Rol yoksa (test/CI) sessizce atlanır.
    grants = "\n".join(
        f"            GRANT SELECT, INSERT, UPDATE, DELETE ON {t} TO kiro2_app;"
        for t in RESTORED_TABLES
    )
    op.execute(
        f"""
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'kiro2_app') THEN
{grants}
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    have = _existing_tables()
    for table in reversed(RESTORED_TABLES):
        if table in have:
            op.drop_table(table)
