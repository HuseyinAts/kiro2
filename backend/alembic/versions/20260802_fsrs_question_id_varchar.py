"""user_item_fsrs.question_id UUID -> VARCHAR (JOIN tip uyumu)

Revision ID: fsrs_qid_varchar_20260802
Revises: gf25_coaching_20260802
Create Date: 2026-08-02

NEDEN
-----
`GET /api/v1/fsrs/due` canlida 500 veriyordu:

    asyncpg.exceptions.UndefinedFunctionError:
    operator does not exist: character varying = uuid

`_FETCH_DUE_SQL` (app/services/fsrs_service.py:66) ve kardesi
`_FETCH_DUE_MERCY_SQL` (:105) su JOIN'i yapiyor:

    JOIN question_bank q ON q.id = f.question_id

Olculen tipler (2 Agu 2026, information_schema):
    user_item_fsrs.question_id  ->  uuid
    question_bank.id            ->  character varying

PostgreSQL'de `varchar = uuid` icin operator YOKTUR. Yani bu iki sorgu
tablonun kuruldugu gunden (20260410_create_user_item_fsrs.py:20) beri
HIC calismadi. `20260801_restore_user_item_fsrs.py:65` (#461 restore) ayni
DDL'i birebir yeniden uyguladigi icin kaymayi da beraberinde getirdi.

NEDEN FARK EDILMEDI
-------------------
1. Bu ucu kapsayan Golden Flow testi YOK (`grep fsrs/due tests/e2e/` -> yalniz
   `/fsrs/review` icin GF12). 164 yesilin arkasinda saklanabildi.
2. `test_fsrs_schema_contract.py` bekcisi "SQL'deki tablo adlari semada var mi"
   diye soruyor ve YESILDI — cunku tablolar GERCEKTEN var. Bekci tip uyumunu
   olcmuyordu. Bu turda `test_fsrs_okuma_sorgulari_canli_semada_GERCEKTEN_
   kosuyor` eklendi: artik sorgular canliya karsi KOSTURULUYOR.

ETKI
----
`frontend/src/pages/FSRSReviewPage.tsx:46` dogrudan `/api/v1/fsrs/due?limit=20`
cagiriyor — ogrencinin tekrar sayfasi. Uc her cagrida 500.

VERI
----
`user_item_fsrs` 1 satir (2 Agu olcumu) ve o satir bir olcum artefakti:
`question_id = 00000000-0000-0000-0000-000000000000`, `question_bank`'ta
karsiligi YOK (0 eslesme). Tip donusumu bu satiri korur.

FK NEDEN `NOT VALID`
--------------------
Gecerli bir FK, yukaridaki YETIM satir yuzunden dogrulanamaz. Iki secenek
vardi: (a) satiri sil, (b) FK'yi `NOT VALID` ekle. Onaylanmamis veri silme
YAPILMADI. `NOT VALID` PostgreSQL'in tam da bu durum icin standart deseni:
kisit YENI/GUNCELLENEN satirlarda ZORLANIR, mevcut satirlar taranmaz.
Yetim temizlendikten sonra tek komutla tamamlanir:

    ALTER TABLE user_item_fsrs VALIDATE CONSTRAINT user_item_fsrs_question_id_fkey;

DOGRULAMA
---------
backend/tests/integration/test_fsrs_schema_contract.py
  - test_fsrs_okuma_sorgulari_canli_semada_gercekten_kosuyor  (asil bekci)
  - test_alet_dogrulamasi_bozuk_sorgu_yakalaniyor             (kontrol kolu)
  - test_alet_dogrulamasi_cast_parametre_sanilmaz             (kontrol kolu:
    ilk surum `::text` cast'ini parametre sandi ve YANLIS kirmizi verdi)
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "fsrs_qid_varchar_20260802"
down_revision = "gf25_coaching_20260802"
branch_labels = None
depends_on = None

_FK_ADI = "user_item_fsrs_question_id_fkey"


def upgrade() -> None:
    op.execute(
        "ALTER TABLE user_item_fsrs "
        "ALTER COLUMN question_id TYPE VARCHAR USING question_id::text"
    )
    op.execute(
        f"ALTER TABLE user_item_fsrs ADD CONSTRAINT {_FK_ADI} "
        "FOREIGN KEY (question_id) REFERENCES question_bank(id) "
        "ON DELETE CASCADE NOT VALID"
    )


def downgrade() -> None:
    op.execute(f"ALTER TABLE user_item_fsrs DROP CONSTRAINT IF EXISTS {_FK_ADI}")
    op.execute(
        "ALTER TABLE user_item_fsrs "
        "ALTER COLUMN question_id TYPE UUID USING question_id::uuid"
    )
