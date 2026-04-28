"""Mini-migration M1: schema only (soru_hash nullable + MRQ + staging + Esen cleanup).

Revision ID: prepilot_m1_schema_20260428
Revises: billing_subscriptions_mvp_20260423

Icerik Pipeline v1.2.1 on-kosulu - M1 (M2 backfill script'inden sonra).

M1 kapsami (saniyeler surer, backfill YOK):
  1) Esen Aps Cografya cleanup (1 satir UPDATE)
  2) question_bank.soru_hash VARCHAR(32) NULL (backfill yok, NOT NULL yok)
  3) manual_review_queue tablosu
  4) question_bank_staging tablosu

Backfill (S1 - ayri Python script):
  backend/scripts/backfill_soru_hash.py
  10K batch, her batch kendi tx, idempotent (WHERE soru_hash IS NULL)

M2 (ayri migration, S1 sonrasi):
  - soru_hash NOT NULL constraint
  - uq_qb_soru_hash_active partial UNIQUE INDEX (WHERE is_active=TRUE)
  - idx_qb_soru_hash non-unique INDEX

Sebep: 77K satir MD5 backfill migration icinde tek transaction olarak 5+ dk
AccessExclusiveLock on question_bank tutuyor (kullanici timeout). Onceki versiyon
(SUPERSEDED) bu yuzden iki kez asili kaldi. Backfill mutlaka tx-disinda batched olmali.

Downgrade: Tum schema objelerini kaldirir. Esen cleanup geri alinmaz.
"""

from alembic import op

revision = "prepilot_m1_schema_20260428"
down_revision = "billing_subscriptions_mvp_20260423"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Esen Aps Cografya cleanup
    # M2'deki UNIQUE INDEX (partial WHERE is_active=TRUE) icin tek aktif duplicate
    # bu grup. Aps versiyonu havuzdan cikariliyor; Esen Tyt versiyonu kanonik kalir.
    op.execute(
        """
        UPDATE question_bank
        SET is_calib_pool = FALSE,
            updated_at = NOW(),
            pipeline_metadata = (
                COALESCE(pipeline_metadata::jsonb, '{}'::jsonb) ||
                '{"prepilot_dedup_at":"2026-04-28","reason":"unique_index_conflict_with_id_0d6e5dbe"}'::jsonb
            )::json
        WHERE id = '10e2304d-a613-50c7-847d-d2d304571220';
        """
    )

    # 2) soru_hash kolonu (nullable, backfill S1 scriptinde yapilacak)
    op.execute(
        """
        ALTER TABLE question_bank
        ADD COLUMN IF NOT EXISTS soru_hash VARCHAR(32);
        """
    )

    # 3) manual_review_queue (Pipeline conflict policy Katman 3 cikti yeri)
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS manual_review_queue (
            id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            old_question_id   VARCHAR NOT NULL REFERENCES question_bank(id) ON DELETE CASCADE,
            new_payload_json  JSONB NOT NULL,
            reason            TEXT NOT NULL,
            source_book       VARCHAR,
            source_page       INT,
            created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            reviewed_at       TIMESTAMPTZ,
            reviewed_by       VARCHAR REFERENCES users(id),
            decision          VARCHAR
                              CHECK (decision IS NULL OR decision IN ('keep_old', 'replace', 'merge', 'pending'))
        );
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_mrq_old_qid
        ON manual_review_queue (old_question_id);
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_mrq_pending
        ON manual_review_queue (created_at)
        WHERE decision IS NULL OR decision = 'pending';
        """
    )

    # 4) question_bank_staging (Pipeline batch staging)
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS question_bank_staging (
            LIKE question_bank INCLUDING DEFAULTS,
            staging_id          UUID DEFAULT gen_random_uuid(),
            staging_status      VARCHAR NOT NULL DEFAULT 'pending'
                                CHECK (staging_status IN (
                                    'pending', 'validated',
                                    'conflict_kept_old', 'conflict_replaced', 'failed'
                                )),
            staging_batch_id    VARCHAR NOT NULL,
            staging_created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )

    op.execute(
        """
        DO $check_pk$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conrelid = 'public.question_bank_staging'::regclass
                  AND contype = 'p'
            ) THEN
                ALTER TABLE question_bank_staging
                ADD PRIMARY KEY (staging_id);
            END IF;
        END $check_pk$;
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_qbs_status
        ON question_bank_staging (staging_status);
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_qbs_batch
        ON question_bank_staging (staging_batch_id);
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_qbs_hash
        ON question_bank_staging (soru_hash)
        WHERE soru_hash IS NOT NULL;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS question_bank_staging CASCADE;")
    op.execute("DROP TABLE IF EXISTS manual_review_queue CASCADE;")
    op.execute("ALTER TABLE question_bank DROP COLUMN IF EXISTS soru_hash;")
    # Esen cleanup geri alinmaz (manuel: UPDATE ... SET is_calib_pool=TRUE WHERE id=...)
