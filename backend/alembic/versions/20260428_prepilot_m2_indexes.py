"""Mini-migration M2: soru_hash NOT NULL + UNIQUE/non-unique indexes.

Revision ID: prepilot_m2_indexes_20260428
Revises: prepilot_m1_schema_20260428

Icerik Pipeline v1.2.1 on-kosulu - M2 (S1 backfill SONRASI).

M2 kapsami (saniyeler surer):
  1) soru_hash NOT NULL constraint (backfill bitti, hepsi dolu)
  2) uq_qb_soru_hash_active: partial UNIQUE INDEX WHERE is_active=TRUE
     - Tam tablo unique olamaz: 145 grup pasif duplicate var (Paket A artigi,
       toplam 196 fazla satir, distinct=77249)
     - Aktif arasinda 0 duplicate (M1 + S1 + M2-prep cleanup sonrasi:
       Esen Aps Cografya is_active=FALSE yapildi, Esen Tyt kanonik kalir)
  3) idx_qb_soru_hash: genel non-unique INDEX (hash lookup performansi)

ON-KOSUL (M1+S1+manuel cleanup tamamlanmis olmali):
  - alembic head = prepilot_m1_schema_20260428
  - SELECT COUNT(*) FROM question_bank WHERE soru_hash IS NULL = 0
  - Aktif duplicate gruplar = 0
    (m2_prep_deactivate_esen_aps.sql ile saglandi, 28.04.2026)

Production notu:
  Lokal'de standart CREATE INDEX (AccessExclusiveLock 1-2 sn). Production
  deploy'unda CREATE INDEX CONCURRENTLY tercih edilir (lock-free), ancak
  CONCURRENTLY alembic transactional DDL ile uyumsuz - ayri runner gerek.

Downgrade: Index'leri ve NOT NULL constraint'i kaldirir. Veri korunur.
"""

from alembic import op

revision = "prepilot_m2_indexes_20260428"
down_revision = "prepilot_m1_schema_20260428"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) NOT NULL constraint
    op.execute(
        """
        ALTER TABLE question_bank
        ALTER COLUMN soru_hash SET NOT NULL;
        """
    )

    # 2) Partial UNIQUE INDEX (aktif kayitlar arasi unique)
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_qb_soru_hash_active
        ON question_bank (soru_hash)
        WHERE is_active = TRUE;
        """
    )

    # 3) Genel non-unique INDEX (lookup performansi)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_qb_soru_hash
        ON question_bank (soru_hash);
        """
    )


def downgrade() -> None:
    # Reverse order
    op.execute("DROP INDEX IF EXISTS idx_qb_soru_hash;")
    op.execute("DROP INDEX IF EXISTS uq_qb_soru_hash_active;")
    op.execute(
        """
        ALTER TABLE question_bank
        ALTER COLUMN soru_hash DROP NOT NULL;
        """
    )
