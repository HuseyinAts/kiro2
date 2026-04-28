"""Mini-migration: soru_hash + manual_review_queue + question_bank_staging.

Revision ID: prepilot_pipeline_v12_20260428
Revises: billing_subscriptions_mvp_20260423

Icerik Pipeline v1.2.1 on-kosulu. Uc schema objesi ekler:
  1) question_bank.soru_hash VARCHAR(32) - MD5 hash, content-based deduplication
     - Backfill: 77.445 satir icin MD5(qtext + options) hesaplanir
     - Partial UNIQUE INDEX uq_qb_soru_hash_active (WHERE is_active=TRUE)
       * Tam tablo unique olamaz: 96 grup pasif duplicate var (Paket A artigi)
       * Aktif arasinda 0 duplicate (Paket A + on-kosul cleanup sonrasi)
     - Genel non-unique INDEX idx_qb_soru_hash (lookup performansi icin)
  2) manual_review_queue tablosu - Pipeline conflict policy Katman 3 cikti yeri
     - Yeni okuma kalibre/havuz/yanitlanmis bir kayitla cakistiginda buraya yazilir
     - Huseyin manuel review eder, decision = keep_old | replace | merge
  3) question_bank_staging tablosu - Pipeline batch staging
     - LIKE question_bank INCLUDING DEFAULTS (ayni 73 kolon + soru_hash)
     - + staging_id, staging_status, staging_batch_id, staging_created_at

On-kosul cleanup (upgrade icinde 1 satir UPDATE):
  - id=10e2304d-a613-50c7-847d-d2d304571220 (Esen Aps Cografya, sayfa 98)
  - is_calib_pool: TRUE -> FALSE
  - Sebep: id=0d6e5dbe-57a7-51e0-a4f6-0b6d1b792e2c (Esen Tyt Cografya, sayfa 90) ile
    ayni hash; ikisi de havuzda; ikisi de hic kullanilmamis (calib_sample=0, times_asked=0).
    UNIQUE INDEX engelini kaldirmak icin Aps versiyonunu havuzdan cikariyoruz.
    Esen Tyt versiyonu daha kanonik (sinav turu explicit). Havuz dengesi etkilenmez.

Downgrade: Tum schema objelerini kaldirir. Cleanup geri alinmaz (1 satir UPDATE,
manuel ihtiyac olursa Huseyin: UPDATE question_bank SET is_calib_pool=TRUE WHERE id=...).
"""

from alembic import op

revision = "prepilot_pipeline_v12_20260428"
down_revision = "billing_subscriptions_mvp_20260423"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1) On-kosul cleanup: 1 satirlik dedup
    # ------------------------------------------------------------------
    # UNIQUE INDEX (partial) WHERE is_active=TRUE icin engel olan tek aktif
    # duplicate grubu temizleniyor. Paket A'nin koruma kurali bu 2 kaydi
    # (ikisi de is_calib_pool=TRUE) korumustu; simdi birini havuzdan cikariyoruz.
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

    # ------------------------------------------------------------------
    # 2) question_bank.soru_hash kolonu + backfill + indexes
    # ------------------------------------------------------------------
    op.execute(
        """
        ALTER TABLE question_bank
        ADD COLUMN IF NOT EXISTS soru_hash VARCHAR(32);
        """
    )

    # Backfill: MD5 hash hesapla (77.445 satir, tahmini ~2-3 saniye)
    op.execute(
        """
        UPDATE question_bank
        SET soru_hash = MD5(
            LOWER(TRIM(question_text)) || '|' ||
            option_a || '|' || option_b || '|' || option_c || '|' || option_d || '|' ||
            COALESCE(option_e, '')
        )
        WHERE soru_hash IS NULL;
        """
    )

    # NOT NULL constraint (backfill sonrasi)
    op.execute(
        """
        ALTER TABLE question_bank
        ALTER COLUMN soru_hash SET NOT NULL;
        """
    )

    # Partial UNIQUE INDEX: aktif kayitlar arasinda hash unique olmali
    # (pasif kayitlar arasinda 96 grup duplicate var, onlara dokunulmuyor)
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_qb_soru_hash_active
        ON question_bank (soru_hash)
        WHERE is_active = TRUE;
        """
    )

    # Genel non-unique index (hash lookup performansi)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_qb_soru_hash
        ON question_bank (soru_hash);
        """
    )

    # ------------------------------------------------------------------
    # 3) manual_review_queue tablosu
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # 4) question_bank_staging tablosu
    # ------------------------------------------------------------------
    # LIKE INCLUDING DEFAULTS: question_bank ile ayni 73 kolon + default'lar.
    # Yeni soru_hash kolonu da otomatik gelir (yukarida eklendi).
    # Constraint'ler INCLUDING'a dahil degil — staging tablo gevsek calisir
    # (validation pipeline tarafinda yapilir).
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

    # PRIMARY KEY ayri eklenir (LIKE INCLUDING DEFAULTS PK kopyalamaz, kopyalasaydi
    # iki PK olurdu cunku LIKE base table'in PK'sini de tasimaya calisirdi).
    # Aslinda LIKE PK'yi kopyalamiyor — bu yuzden staging_id'yi PK yapiyoruz.
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
    # Reverse order (en son olusturulan ilk kaldirilir)

    # 4) question_bank_staging
    op.execute("DROP TABLE IF EXISTS question_bank_staging CASCADE;")

    # 3) manual_review_queue
    op.execute("DROP TABLE IF EXISTS manual_review_queue CASCADE;")

    # 2) question_bank.soru_hash + indexes
    op.execute("DROP INDEX IF EXISTS uq_qb_soru_hash_active;")
    op.execute("DROP INDEX IF EXISTS idx_qb_soru_hash;")
    op.execute("ALTER TABLE question_bank DROP COLUMN IF EXISTS soru_hash;")

    # 1) On-kosul cleanup geri alinmaz (1 satir UPDATE, manuel ihtiyac olursa).
    # Note: Eger downgrade gerekirse Huseyin manuel:
    #   UPDATE question_bank SET is_calib_pool = TRUE
    #   WHERE id = '10e2304d-a613-50c7-847d-d2d304571220';
