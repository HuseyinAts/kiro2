"""345 AYT Fizik + Mikro TYT Fizik kitaplarini beta kapisindan gecirir

Revision ID: 0039_fizik_beta_onay
Revises: 0038_fizik_gorsel_url
Create Date: 2026-09-22

BAGLAM
------
Iki fizik kitabi bilerek PASIF ithal edilmisti:

    345 2025 AYT Fizik Soru Bankasi ........... 1308 satir (PR #291)
    Mikro Orijinal TYT Fizik Soru Bankasi 2025  1326 satir (PR #290)

Urun sahibi bireysel insan denetimini ATLAYIP toplu beta onayi verdi;
0014/0016/0018/0023/0037 emsali.

ON KOSUL: 0038
--------------
Iki kitabin gorsel URL'leri de dosya sistemi yoluydu; 0038 onardi ve
sonrasinda DB genelinde `/static/crops` disi gorsel URL sayisi 0 olctu.

KAPI YUKU OLCULDU
-----------------
`v_safe_for_beta` tanimi pg_views'ten okundu, her kosul iki kitap icin
AYRI sayildi (backend/_geo1_gecici/_fizik_kapi_olc.py):

    kosul                              FIZ345       MIKRO_TYT
    pipeline_metadata NOT NULL ...... 1308/1308     1326/1326
    demoted_at yok .................. 1308/1308     1326/1326
    topic_match_quality <> fallback . 1308/1308     1326/1326
    match_tier tier1 degil .......... 1308/1308     1326/1326
    sik_bos bayragi yok .............    0 satir       0 satir
    primary_topic_id dolu ........... 1308/1308     1326/1326
    quality_review_status uygun .....    0/1308        0/1326
    uyum sinyali ....................    0/1308        0/1326
    (is_ai_generated=false OR APPROVED)  0/1308        0/1326
    is_active .......................    0/1308        0/1326

Kapiyi tutan UC kilit var; bu migration ucunu de acar, is_active da
acilir.

HEDEF 2634 DEGIL 2549 -- VE DISLAMA KURALI BAYRAK DEGIL OLCUM
--------------------------------------------------------------
Nominal kapsam 1308 + 1326 = 2634. Gercek hedef 2549.

Ilk tasarimda `okuyucu_simgesi_ortmesi` bayrakli 32 satirin tamami
dislanacakti. OLCUM bunun YANLIS oldugunu gosterdi: bayrak iki kitapta
FARKLI seyi isaretliyor.

  * FIZ345'te ortme basili SORU NUMARASINI vuruyor. `ortulen_metin`
    alani bunu acikca yaziyor: "soru numarasi mor buyutec simgesinin
    altinda kaldigi icin okunamiyor". Govde ve sikler saglam; ogrenciye
    gorunen 6 alanin hicbirinde `[??]` YOK (0/1308 olculdu). Bu 16
    satir servis edilebilir -- dislanmalari veri kaybi olurdu.
  * MIKRO'da ortme GOVDEYI vuruyor: "satin almak istedig[??] cep
    telefonu", "veriler ye[??] almaktadir". 8 satirda isaret ogrenciye
    GORUNUYOR.

Bu yuzden dislama kurali bayraga degil OLCUME baglandi:

    (a) servis edilemez bayrak: sik_bos / gorsel_yok_sekilli /
        gosterilemez_gorsel_sik_kirpimsiz
    (b) ogrenciye gorunen alti alandan birinde `[??]` gecmesi

    kitap        toplam   (a)    (b)   birlesim   hedef
    FIZ345         1308    11      0         11    1297
    MIKRO_TYT      1326    66      8         74    1252
                                                   ----
                                                   2549

`gorsel_yok_sekilli`: sekil iceren ama kirpimi uretilemeyen soru --
sekilsiz cozulemez (0023'un TYT biyolojide verdigi karar).
`gosterilemez_gorsel_sik_kirpimsiz` (FIZ345 s27 sag 5): siklari grafik
VE kirpimi yok; hicbir bicimde gosterilemez. Bu satir zaten 11'in
icinde.

KONSENSUS GEREKCESI HER KITAP ICIN AYRI YAZILDI
-----------------------------------------------
0023'un dersi: baska kitabin sinyallerini kopyalamak yanlistir.

1. 345 AYT FIZIK (FIZ_345_AYT_YONTEM.md)
   - cevap_satiri_cift_okuma: sayfa alti cevap satiri iki kez okundu;
     harf duzeyinde uyusmazlik 5 sutunda (bu fonttaki B/E benzerligi),
     besi de 12x buyutmede gozle karara baglandi.
   - sayfa_ici_numara_surekliligi: 382 sayfada 0 kusur (sol bitince sag
     devam eder).
   - sayfalar_arasi_gecis_iki_durumlu: 379 gecisin hepsi ya "devam" ya
     "yeni test 1'den"; UCUNCU DURUM YOK.
   - test_basina_numaralar_kesintisiz: 190/190.

2. MIKRO TYT FIZIK (MIKRO_FIZIK_TYT_YONTEM.md)
   - serit_cift_okuma: cevap seridi icin iki bagimsiz okuma.
   - serit_numara_surekliligi: 186 seritte 0 kusur.
   - okunan_soru_sayisi_esittir_serit_girdisi: 186/186 test.
   - basili_sayfa_dosya_sayfasiyla_ayni: 1326/1326.
   - kirpim_cevap_seridini_icermiyor: sizinti kapisi -- serit ust
     cercevesi kart y=883; 583 kirpimin y-alt siniri en fazla 872,
     883'u gecen kirpim 0.

NE OLDUGU KONUSUNDA DURUST OLMA
-------------------------------
- quality_review_status: 'pending' -> 'auto_judged_high'.
  'human_verified' YAZILMIYOR -- hicbir insan tek tek dogrulamadi.
- review_status: 'PENDING' -> 'APPROVED'; metadata'ya
  onay_turu='toplu_beta_sahibi', bireysel_denetim_yapildi=false.
- is_ai_generated ALANINA DOKUNULMUYOR (true kalir).
- CEVAPLAR DOGRULANMADI: tek kaynak kitabin BASILI anahtaridir;
  sorular tekrar cozulmedi.
- SORU METNI iki kitapta da TAM olarak ikinci kez OKUNMADI. Cift okuma
  yalnizca cevap satiri/seridi icindir. Iki YONTEM belgesi de bunu borc
  olarak yaziyor.
- `mukerrer_aday` bayrakli satirlar HEDEFIN ICINDEDIR (FIZ345 11,
  MIKRO 31). Bunlar DB'deki fizik satirlariyla kelime kumesi ortusmesi
  >= 0.75 olan sorulardir; FIZ345'te 9'u OSYM 2025 AYT, 2'si Neofizik.
  Kitap CIKMIS SORU kutulari bastigi icin bu ortusme BEKLENIR ve
  meshru icerigi temsil eder. Ancak aktiflestirilince ayni soru iki
  kaynaktan da havuza girer; sinav uretiminde tekrar riski vardir.
  Dislanmadilar, GORUNUR birakildilar -- karar geri alinabilir.
- FIZ345'te 16 satirda basili soru NUMARASI okunamiyor (ustte).
  `soru_no_basili` o satirlarda guvenilmezdir; ogrenciye gorunen icerik
  etkilenmez.
- Sinav turu: FIZ345 AYT, MIKRO TYT olarak isaretli (kitaplar tek
  turlu), geometri kitaplarindaki karisiklik burada YOK.

TELIF
-----
Iki kitap da ticari soru bankasidir; satirlarin
`pipeline_metadata.telif` alani "hak sahibinin izni olmadan servis
edilemez; aktiflestirme ayri karar" der. Bu migration o AYRI KARARIN
uygulanmasidir; karar urun sahibinindir.

GERI ALINABILIR
---------------
Degistirilen her satirin ONCEKI degerleri GUNLUK'e yazilir; downgrade
tam olarak o degerleri geri koyar ve eklenen metadata anahtarlarini
siler.

Revizyon adi 20 karakter (sinir 32).
"""

import json
import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0039_fizik_beta_onay"
down_revision: Union[str, None] = "0038_fizik_gorsel_url"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "fizik_beta_onay_gunlugu_0039"

# Ogrenciye GORUNEN alanlarda ortme isareti; olculdu, varsayilmadi.
ORTME_ISARETI = "%[??]%"

# Servis edilemez bayraklar (kapi kosulu + urun karari).
SERVIS_DISI_BAYRAKLAR = (
    "sik_bos",
    "gorsel_yok_sekilli",
    "gosterilemez_gorsel_sik_kirpimsiz",
)

KAYNAKLAR: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "345 2025 AYT Fizik Soru Bankasi",
        (
            "cevap_satiri_cift_okuma",
            "sayfa_ici_numara_surekliligi",
            "sayfalar_arasi_gecis_iki_durumlu",
            "test_basina_numaralar_kesintisiz",
        ),
    ),
    (
        "Mikro Orijinal TYT Fizik Soru Bankasi 2025",
        (
            "serit_cift_okuma",
            "serit_numara_surekliligi",
            "okunan_soru_sayisi_esittir_serit_girdisi",
            "basili_sayfa_dosya_sayfasiyla_ayni",
            "kirpim_cevap_seridini_icermiyor",
        ),
    ),
)

EK_ANAHTARLAR = (
    "consensus_2signal_run",
    "konsensus_sinyalleri",
    "onay_turu",
    "bireysel_denetim_yapildi",
)

# SQL DUZ YAZILIR (interpolasyon yok): uc bayrak sabit ve sayili oldugu icin
# f-string'e gerek yok; sorgu metni boylece goz ile denetlenebilir kalir.
# SERVIS_DISI_BAYRAKLAR ile bu metnin ayni uc bayragi tasidigini test dogrular
# (test_servis_disi_bayraklar_sql_ile_ayni).
_HEDEF_SQL = """
SELECT qb.id, qb.is_active, qb.review_status, qs.quality_review_status
  FROM question_bank qb
  JOIN question_metadata qm ON qm.id = qb.id
  JOIN question_content qc ON qc.id = qb.id
  LEFT JOIN question_statistics qs ON qs.id = qb.id
 WHERE qm.source_book = :kaynak
   AND (qm.pipeline_metadata IS NULL
        OR NOT (qm.pipeline_metadata::jsonb ? 'bayraklar')
        OR (NOT ((qm.pipeline_metadata::jsonb -> 'bayraklar') ? 'sik_bos')
            AND NOT ((qm.pipeline_metadata::jsonb -> 'bayraklar')
                     ? 'gorsel_yok_sekilli')
            AND NOT ((qm.pipeline_metadata::jsonb -> 'bayraklar')
                     ? 'gosterilemez_gorsel_sik_kirpimsiz')))
   AND qc.question_text NOT LIKE :isaret
   AND qc.option_a NOT LIKE :isaret
   AND qc.option_b NOT LIKE :isaret
   AND qc.option_c NOT LIKE :isaret
   AND qc.option_d NOT LIKE :isaret
   AND qc.option_e NOT LIKE :isaret
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
        _log.info("[0039] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0039] mv_safe_for_beta yenilendi")


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


def _gunlugu_kur() -> None:
    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("onceki_is_active", sa.Boolean(), nullable=True),
        sa.Column("onceki_review_status", sa.String(), nullable=True),
        sa.Column("onceki_quality_review_status", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def _kitabi_ac(b, kaynak: str, sinyaller: tuple[str, ...]) -> int:
    hedef = b.execute(
        sa.text(_HEDEF_SQL), {"kaynak": kaynak, "isaret": ORTME_ISARETI}
    ).fetchall()
    if not hedef:
        _log.info("[0039] %s satiri yok -- atlandi", kaynak)
        return 0

    idler = [r[0] for r in hedef]
    b.execute(
        sa.text(
            f"INSERT INTO {GUNLUK} (id, onceki_is_active, onceki_review_status,"  # noqa: S608  # nosec B608 - GUNLUK sabit modul duzeyi ad
            " onceki_quality_review_status) VALUES (:id, :akt, :rs, :qrs)"
        ),
        [{"id": r[0], "akt": r[1], "rs": r[2], "qrs": r[3]} for r in hedef],
    )
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
    b.execute(_META_EKLE, {"idler": idler, "sinyaller": json.dumps(list(sinyaller))})

    haric = b.execute(
        sa.text(
            "SELECT count(*) FROM question_metadata"
            " WHERE source_book = :kaynak AND id <> ALL(:idler)"
        ),
        {"kaynak": kaynak, "idler": idler},
    ).scalar_one()
    _log.info(
        "[0039] %s: %s satir acildi, servis edilemez oldugu icin disarida: %s",
        kaynak,
        len(idler),
        haric,
    )
    return len(idler)


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0039] soru tablolari yok (taze DB?) -- atlandi")
        return

    var_mi = any(
        b.execute(
            sa.text("SELECT 1 FROM question_metadata WHERE source_book = :k LIMIT 1"),
            {"k": kaynak},
        ).first()
        for kaynak, _ in KAYNAKLAR
    )
    if not var_mi:
        _log.info("[0039] fizik satiri yok -- atlandi (veri ithal edilmemis)")
        return

    _gunlugu_kur()
    toplam = sum(_kitabi_ac(b, kaynak, sinyaller) for kaynak, sinyaller in KAYNAKLAR)
    _log.info("[0039] beta kapisi acildi: toplam %s satir", toplam)
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0039] %s yok -- downgrade atlandi", GUNLUK)
        return
    if not _tablolar_var(b):
        op.drop_table(GUNLUK)
        return

    kayitlar = b.execute(
        sa.text(
            "SELECT id, onceki_is_active, onceki_review_status,"  # noqa: S608  # nosec B608 - GUNLUK sabit modul duzeyi ad
            f" onceki_quality_review_status FROM {GUNLUK}"
        )
    ).fetchall()
    for sid, akt, rs, qrs in kayitlar:
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

    idler = [r[0] for r in kayitlar]
    for anahtar in EK_ANAHTARLAR:
        b.execute(
            sa.text(
                "UPDATE question_metadata"
                " SET pipeline_metadata = (pipeline_metadata::jsonb - :a)::json"
                " WHERE id = ANY(:idler)"
            ),
            {"a": anahtar, "idler": idler},
        )

    _log.info("[0039] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
