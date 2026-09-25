"""345 Paragraf: eski hat 8 satir pasif, yeni ithal beta kapisindan gecer

Revision ID: 0056_prg345_beta_onay
Revises: 0055_prg345_agac
Create Date: 2026-09-25

SAHIP KARARI (25 Eyl 2026)
--------------------------
"1. ... eski hatta 8 soru ... pasife alinsin  2. Yeni yuklenen 1011 soru
pasif duruyor AKTIFLESTIR". Bireysel insan denetimi yapilmadi; toplu beta
sahibi onayi (0014/0016/0018/0023/0027/0037/0039 emsali).

1. ESKI HAT PASIF
-----------------
'345 2025 Paragraf Sifir Risk Soru Bankasi' kaynakli, ithal_araci
TASIMAYAN 8 satir (eski gemini hatti). Sekizinin de bu kitabin yeni
ithalinde ayni sayfada bir ikizi var (`eski_hat_ikizi`, cevap 8/8 ayni);
eski metinler OCR hatali, biri `subject_area = SOSYAL` (paragraf sorusu).
is_active = FALSE; SILINMEZ, baska alana dokunulmaz. Guard: yalniz satir
hala aktifse.

2. BETA KAPISI -- KAPI YUKU OLCULDU (25 Eyl, yerel DB, 0055 sonrasi)
-------------------------------------------------------------------
`v_safe_for_beta` tanimi pg_get_viewdef ile okundu. 1011 yeni satirda:
    quality_review_status 'pending' ............ 1011/1011 (kilit)
    uyum sinyali (consensus_2signal_run vb.) ...    0/1011 (kilit)
    is_ai_generated=true, review 'PENDING' .....  1011/1011 (kilit)
    sik_bos bayragi ............................    0
    ogrenciye gorunen alti alanda `[??]` .......    0
    bos sik / cevap ............................    0
    gorselsiz satir ............................    0
    aktif satirlarla soru_hash cakismasi .......    0
Uc kilit acilir, is_active acilir.

HEDEF 1010 (1011 DEGIL)
-----------------------
`uq_qb_soru_hash_active` (aktif satirlarda soru_hash benzersiz) iki
kitap-ici tekrari ayni anda aktif tutamaz: T022_20 ve T038_13 ayni soruyu
basiyor (`kitap_ici_tekrar`). Ilk basildigi yer (T022_20) acilir, T038_13
(KITAP_ICI_TEKRAR_PASIF) PASIF kalir. Dislama kurali 0039 ile ayni:
servis edilemez bayrak (sik_bos / gorsel_yok_sekilli /
gosterilemez_gorsel_sik_kirpimsiz) ya da gorunen alanda `[??]`; ikisi de
bu kitapta 0 olculdu, kural yine de SQL'de durur.

ACILANLAR ARASINDA GORUNUR BIRAKILANLAR (dislanmadi)
----------------------------------------------------
- `kaynak_kusuru` 143: OKUMA belirsizligi notu (okuyucu diski altinda
  kalan satir sonu harfleri, iki adayli t~l / rn~m, sapka). Basili sayfa
  kusuru DEGIL (0027'nin kaynak_dizgi_kusuru'ndan farkli); ogrenci ayrica
  tam soru kirpimini gorur.
- `bulanik_metin_tasarim` 8 (T081 'Algisal Butunluk Testi'): parca kitapta
  BILEREK bulanik; govde '[bulanik metin]' + soru koku, parca kirpimda.
- `okuyucu_diski_ortme` 250, `numara_ortulu` 2: gorunen alanda `[??]` 0.
- `mukerrer_aday` 10, `cikmis_soru` 83: cikmis soru kutulari beklenen
  ortusme; aktif satirlarla hash cakismasi 0.

KONSENSUS SINYALLERI (bu kitaba ait, PRG_345_YONTEM.md)
-------------------------------------------------------
- anahtar_iki_bagimsiz_okuma_harf_farki_0: kitap sonu anahtar iki
  bagimsiz gorsel okuma, 1012 girdi, 0 harf farki.
- anahtar_tablo_glif_ucuncu_kanal_loo: tablo sayfalarinda glif
  en-yakin-komsu ucuncu kanal LOO 441/441.
- anahtar_girdi_sayisi_test_basina_esit: 85/85 test, 1012/1012 girdi.
- transkripsiyon_bes_kapi_yesil: harness KAPI1-5 yesil.
- metin_tam_ikinci_okuma_gozle_hukum: on kayitli orneklem ust siniri
  %3.11 > %3 -> TAM ikinci okuma; 138 kelime farki kirpimdan gozle.

DURUSTLUK
---------
- quality_review_status 'pending' -> 'auto_judged_high'; 'human_verified'
  YAZILMAZ. review_status 'PENDING' -> 'APPROVED'; metadata'ya
  onay_turu='toplu_beta_sahibi', bireysel_denetim_yapildi=false.
- is_ai_generated'a DOKUNULMAZ; is_public'e DOKUNULMAZ.
- Cevaplar dogrulanmadi (tek kaynak basili anahtar); sorular cozulmedi.

TELIF
-----
Satirlarin `pipeline_metadata.telif` notu "aktiflestirme ayri karar" der;
bu migration o ayri kararin (urun sahibi) uygulanmasidir.

GERI ALINABILIR
---------------
Degisen her satirin onceki uc degeri + islem turu GUNLUK'e yazilir;
downgrade once acilanlari kapatir, sonra eski hatti geri acar ve eklenen
metadata anahtarlarini siler. Konu sayaci ve beta gorunumu yenilenir.

Revizyon adi 21 karakter (sinir 32).
"""

import json
import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0056_prg345_beta_onay"
down_revision: Union[str, None] = "0055_prg345_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "prg345_beta_onay_gunlugu_0056"
KAYNAK = "345 2025 Paragraf Sifir Risk Soru Bankasi"
ITHAL_ARACI = "scripts/kitap/prg345_ithal.py"

# Eski gemini hatti satirlari (ithal_araci yok); sekizinin de yeni ithalde
# ayni sayfada ikizi var (eski_hat_ikizi.db_id).
ESKI_HAT_PASIF: tuple[str, ...] = (
    "58044c42-3230-558c-bd88-26d4c5eff0d3",
    "69b96e1f-692a-57b9-9305-a693282f600f",
    "6d5a7eb6-d7f1-5e65-a119-f930b4a21d5f",
    "74649484-f889-57b8-9dd5-37cdc6454da0",
    "93ce876e-f3b9-5417-80b3-906f9e3647cd",
    "c8ae4ab2-2818-5d62-bf76-64f8d4729a54",
    "ee267419-d4de-5b84-ad85-318a58e6492f",
    "eed89ee4-968f-512f-9bf9-ab5a5ad39a27",
)

# T038_13: T022_20 ile ayni soru_hash; aktif benzersizlik kisiti geregi
# ilk basildigi yer (T022_20, 0bfc9486) acilir, bu PASIF kalir.
KITAP_ICI_TEKRAR_PASIF = "4b52585c-f48e-5a69-bb06-9b4b9eb3ec91"

ORTME_ISARETI = "%[??]%"

SERVIS_DISI_BAYRAKLAR = (
    "sik_bos",
    "gorsel_yok_sekilli",
    "gosterilemez_gorsel_sik_kirpimsiz",
)

SINYALLER: tuple[str, ...] = (
    "anahtar_iki_bagimsiz_okuma_harf_farki_0",
    "anahtar_tablo_glif_ucuncu_kanal_loo",
    "anahtar_girdi_sayisi_test_basina_esit",
    "transkripsiyon_bes_kapi_yesil",
    "metin_tam_ikinci_okuma_gozle_hukum",
)

EK_ANAHTARLAR = (
    "consensus_2signal_run",
    "konsensus_sinyalleri",
    "onay_turu",
    "bireysel_denetim_yapildi",
)

# SQL DUZ YAZILIR (interpolasyon yok); SERVIS_DISI_BAYRAKLAR ile ayni uc
# bayragi tasidigini test dogrular.
_HEDEF_SQL = """
SELECT qb.id, qb.is_active, qb.review_status, qs.quality_review_status
  FROM question_bank qb
  JOIN question_metadata qm ON qm.id = qb.id
  JOIN question_content qc ON qc.id = qb.id
  LEFT JOIN question_statistics qs ON qs.id = qb.id
 WHERE qm.source_book = :kaynak
   AND qm.pipeline_metadata::jsonb ->> 'ithal_araci' = :arac
   AND qb.is_active IS NOT TRUE
   AND qb.id <> :tekrar
   AND NOT ((qm.pipeline_metadata::jsonb -> 'bayraklar') ? 'sik_bos')
   AND NOT ((qm.pipeline_metadata::jsonb -> 'bayraklar') ? 'gorsel_yok_sekilli')
   AND NOT ((qm.pipeline_metadata::jsonb -> 'bayraklar')
            ? 'gosterilemez_gorsel_sik_kirpimsiz')
   AND qc.question_text NOT LIKE :isaret
   AND qc.option_a NOT LIKE :isaret
   AND qc.option_b NOT LIKE :isaret
   AND qc.option_c NOT LIKE :isaret
   AND qc.option_d NOT LIKE :isaret
   AND qc.option_e NOT LIKE :isaret
"""

_ESKI_SQL = """
SELECT qb.id, qb.is_active, qb.review_status, qs.quality_review_status
  FROM question_bank qb
  JOIN question_metadata qm ON qm.id = qb.id
  LEFT JOIN question_statistics qs ON qs.id = qb.id
 WHERE qb.id = ANY(:idler)
   AND qm.source_book = :kaynak
   AND qb.is_active IS TRUE
"""

_META_EKLE = sa.text(
    """
    UPDATE question_metadata
       SET pipeline_metadata = (
             pipeline_metadata::jsonb
             || jsonb_build_object(
                  'consensus_2signal_run', true,
                  'konsensus_sinyalleri', CAST(:sinyaller AS jsonb),
                  'onay_turu', 'toplu_beta_sahibi',
                  'bireysel_denetim_yapildi', false)
           )::json
     WHERE id = ANY(:idler)
    """
)

_SAYAC_SQL = """
UPDATE topic_hierarchy t
   SET total_questions = COALESCE(g.adet, 0), updated_at = now()
  FROM (SELECT th.id, count(qb.id) AS adet
          FROM topic_hierarchy th
          LEFT JOIN question_bank qb
                 ON qb.primary_topic_id = th.id AND qb.is_active IS TRUE
         GROUP BY th.id) g
 WHERE g.id = t.id
   AND t.total_questions IS DISTINCT FROM COALESCE(g.adet, 0)
"""


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0056] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0056] mv_safe_for_beta yenilendi")


def _tablolar_var(b) -> bool:
    denetci = sa.inspect(b)
    return all(
        denetci.has_table(t)
        for t in (
            "question_bank",
            "question_metadata",
            "question_content",
            "question_statistics",
        )
    )


def _gunluge_yaz(b, satirlar, islem: str) -> None:
    b.execute(
        sa.text(
            f"INSERT INTO {GUNLUK} (id, islem, onceki_is_active,"  # noqa: S608  # nosec B608 - GUNLUK sabit modul duzeyi ad
            " onceki_review_status, onceki_quality_review_status)"
            " VALUES (:id, :islem, :akt, :rs, :qrs)"
        ),
        [
            {"id": r[0], "islem": islem, "akt": r[1], "rs": r[2], "qrs": r[3]}
            for r in satirlar
        ],
    )


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0056] soru tablolari yok (taze DB?) -- atlandi")
        return
    var_mi = b.execute(
        sa.text("SELECT 1 FROM question_metadata WHERE source_book = :k LIMIT 1"),
        {"k": KAYNAK},
    ).first()
    if not var_mi:
        _log.info("[0056] %s satiri yok -- atlandi", KAYNAK)
        return

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("islem", sa.String(), nullable=False),
        sa.Column("onceki_is_active", sa.Boolean(), nullable=True),
        sa.Column("onceki_review_status", sa.String(), nullable=True),
        sa.Column("onceki_quality_review_status", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 1. ESKI HAT PASIF (once: acilacak satirlarla hash cakismasi olmasin)
    eski = b.execute(
        sa.text(_ESKI_SQL), {"idler": list(ESKI_HAT_PASIF), "kaynak": KAYNAK}
    ).fetchall()
    if eski:
        _gunluge_yaz(b, eski, "eski_hat_pasif")
        b.execute(
            sa.text(
                "UPDATE question_bank SET is_active = FALSE, updated_at = now()"
                " WHERE id = ANY(:idler)"
            ),
            {"idler": [r[0] for r in eski]},
        )
    _log.info("[0056] eski hat: %s satir pasife alindi", len(eski))

    # 2. BETA KAPISI
    hedef = b.execute(
        sa.text(_HEDEF_SQL),
        {
            "kaynak": KAYNAK,
            "arac": ITHAL_ARACI,
            "tekrar": KITAP_ICI_TEKRAR_PASIF,
            "isaret": ORTME_ISARETI,
        },
    ).fetchall()
    idler = [r[0] for r in hedef]
    if idler:
        _gunluge_yaz(b, hedef, "beta_ac")
        b.execute(
            sa.text(
                "UPDATE question_bank SET is_active = TRUE, review_status = 'APPROVED',"
                " updated_at = now() WHERE id = ANY(:idler)"
            ),
            {"idler": idler},
        )
        b.execute(
            sa.text(
                "UPDATE question_statistics SET quality_review_status = 'auto_judged_high'"
                " WHERE id = ANY(:idler)"
            ),
            {"idler": idler},
        )
        b.execute(
            _META_EKLE, {"idler": idler, "sinyaller": json.dumps(list(SINYALLER))}
        )
    _log.info("[0056] beta kapisi: %s satir acildi", len(idler))

    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0056] %s yok -- downgrade atlandi", GUNLUK)
        return
    if not _tablolar_var(b):
        op.drop_table(GUNLUK)
        return

    kayitlar = b.execute(
        sa.text(
            "SELECT id, islem, onceki_is_active, onceki_review_status,"  # noqa: S608  # nosec B608 - GUNLUK sabit modul duzeyi ad
            f" onceki_quality_review_status FROM {GUNLUK}"
        )
    ).fetchall()
    # Once acilanlar kapanir, sonra eski hat geri acilir (hash kisiti sirasi).
    for sira in ("beta_ac", "eski_hat_pasif"):
        for sid, islem, akt, rs, qrs in kayitlar:
            if islem != sira:
                continue
            b.execute(
                sa.text(
                    "UPDATE question_bank SET is_active = :akt, review_status = :rs,"
                    " updated_at = now() WHERE id = :id"
                ),
                {"id": sid, "akt": akt, "rs": rs},
            )
            b.execute(
                sa.text(
                    "UPDATE question_statistics SET quality_review_status = :qrs"
                    " WHERE id = :id"
                ),
                {"id": sid, "qrs": qrs},
            )

    acilan = [r[0] for r in kayitlar if r[1] == "beta_ac"]
    for anahtar in EK_ANAHTARLAR:
        b.execute(
            sa.text(
                "UPDATE question_metadata"
                " SET pipeline_metadata = (pipeline_metadata::jsonb - :a)::json"
                " WHERE id = ANY(:idler)"
            ),
            {"a": anahtar, "idler": acilan},
        )

    _log.info("[0056] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
