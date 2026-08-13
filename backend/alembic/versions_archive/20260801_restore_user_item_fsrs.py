"""user_item_fsrs tablosunu geri getir (#461 / K1)

Revision ID: restore_uif_20260801
Revises: mv_safe_for_beta_20260727
Create Date: 2026-08-01

NEDEN
-----
`user_item_fsrs` 11 Haz 2026'da `c555a10f4b93_sync_db_changes.py:183` tarafindan
`DROP TABLE ... CASCADE` ile dusuruldu. O migration autogenerate ile uretilmisti;
tablonun ORM modeli olmadigi icin alembic onu "modelde yok, fazlalik" saydi.
27 Tem restore migration'i canli loglardan olcum yaparak 6 tablo kurtardi,
bu tablo o listede YOKTU.

ETKI (1 Agu 2026 olcumu)
-----------------------
`/api/v1/fsrs` router'i `routers/loader.py:63`'te KAYITLI ve su bes uc 500 veriyor:
  GET  /due          -> fsrs_service.py  _FETCH_DUE_SQL
  GET  /due?mercy    -> fsrs_service.py  _FETCH_DUE_MERCY_SQL
  POST /review       -> fsrs_service.py  _FETCH_ITEM_SQL
  GET  /due-count    -> fsrs_service.py  _DUE_COUNT_SQL
  GET  /stats        -> app/api/fsrs.py  (satir ici SQL)
Ayrica `app/services/cat_session.py` FSRS yazma hatasini `except Exception` ile
yutuyor -> her CAT oturumunun FSRS ciktisi SESSIZCE kayboluyor (500 bile gorunmuyor).

DDL KAYNAGI
-----------
`20260410_create_user_item_fsrs.py` (rev `user_item_fsrs_001`) ile BIREBIR ayni.
Mevcut migration'lar salt-okunur oldugu icin o dosya degistirilmedi, yenisi yazildi.

RLS
---
Bu tabloda `organization_id` kolonu YOK, dolayisiyla 79-tablo RLS deseni
uygulanamaz. Kapsam disi birakildi — politika ICAT EDILMEDI (27 Tem restore'unun
ayni karari).

VERI
----
Tablo BOS gelir. DROP oncesi ~147 satir vardi (13 May 2026 olcumu,
`_pilots/20260513_doc_claim_live_verification_L5_RESULT.md:34`); o veri icin
Mart-Haziran penceresinde yedek YOK, kurtarilamaz.

TEKRAR-DROP RISKI
-----------------
OLCULDU, KAPALI. `alembic/env.py:117-118` yapisal kapi
(`reflected and compare_to is None -> False`) TUM reflected-only tablolari koruyor.
`include_object()` dogrudan cagrilarak dogrulandi: `user_item_fsrs` -> HARIC.
Kontrol kollari: `question_bank` -> DAHIL, yeni tablo -> DAHIL. Yani exclude
listesine satir eklemek bugun +0 davranis degistirir (#451 dersi: degeri sifir
olan fix yapilmaz).
"""

from alembic import op

revision = "restore_uif_20260801"
down_revision = "mv_safe_for_beta_20260727"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_item_fsrs (
            user_id        TEXT        NOT NULL,
            question_id    UUID        NOT NULL,
            stability      FLOAT       NOT NULL DEFAULT 0.0,
            difficulty     FLOAT       NOT NULL DEFAULT 0.0,
            due_date       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_review    TIMESTAMPTZ,
            state          INTEGER     NOT NULL DEFAULT 0,
            reps           INTEGER     NOT NULL DEFAULT 0,
            lapses         INTEGER     NOT NULL DEFAULT 0,
            scheduled_days INTEGER     NOT NULL DEFAULT 0,
            elapsed_days   INTEGER     NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, question_id)
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_uif_user_due "
        "ON user_item_fsrs (user_id, due_date)"
    )
    # GRANT — uygulama `kiro2_app` non-superuser rolüyle baglaniyor. Bu satir
    # olmadan tablo VAR ama uclar yine 500 verir (UndefinedTable yerine
    # InsufficientPrivilege). Rol yoksa (test/CI) sessizce atlanir.
    op.execute("""
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'kiro2_app') THEN
            GRANT SELECT, INSERT, UPDATE, DELETE ON user_item_fsrs TO kiro2_app;
          END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_uif_user_due")
    op.execute("DROP TABLE IF EXISTS user_item_fsrs")
