"""Mikro Geometri sorularini beta kapisindan gecirir (bireysel denetim atlanarak)

Revision ID: 0018_mikro_geo_beta_onay
Revises: 0017_mikro_geo_konu_agaci
Create Date: 2026-09-11

BAGLAM
------
0017 ile ithal edilen 1211 geometri sorusu bilerek PASIF yazildi
(is_ai_generated=true + review_status='PENDING'). Urun sahibi bireysel insan
denetimini ATLAYIP toplu olarak beta surumunde yapmaya karar verdi; ayni
karar fizik kitaplari icin 0014 (AYT) ve 0016 (TYT) ile uygulanmisti. Bu
migration geometri karsiligidir.

KAPI YUKU OLCULDU, TAHMIN EDILMEDI
----------------------------------
`v_safe_for_beta` tanimi pg_views'ten okundu ve her kosul 1211 geometri
satirina karsi AYRI AYRI sayildi:

    pipeline_metadata NOT NULL .................... 1211/1211 GECIYOR
    demoted_at yok ................................ 1211/1211 GECIYOR
    ai_extras.topic_match_quality <> 'fallback' ... 1211/1211 GECIYOR
    match_tier tier1 degil ........................ 1211/1211 GECIYOR
    sik_bos yok ................................... 1211/1211 GECIYOR
    quality_review_status in (hv, auto_judged_high)    0/1211 ENGEL
    (is_ai_generated=false OR review_status=APPROVED)  0/1211 ENGEL
    uyum sinyali (6 anahtardan biri) ...............    0/1211 ENGEL

Kapiyi tutan UC kilit var; bu migration ucunu de acar. Servis katmani ayrica
is_active ister, o da acilir.

FIZIK KITAPLARINDAN AYRILAN IKI NOKTA
-------------------------------------
1. KAPSAM TAM. TYT'de 891 satirin 64'u `sik_bos` bayragi tasidigi icin
   disarida kalmisti. Geometride sik_bos bayrakli soru YOK (olculdu:
   1211/1211 temiz), cunku bu kitapta sikki gorsel olan soru cikmadi --
   sikler her zaman metin. Hedef: 1211 satirin TAMAMI.

2. KONSENSUS GEREKCESI FARKLI. 0014 (AYT fizik) `auto_judged_high`i cift
   okuma VE bagimsiz cozum-dogrulamasina dayandirmisti. 0016 (TYT fizik)
   cozum dogrulamasi olmadigi icin iki sinyal kullandi. Geometride cozum
   dogrulamasi YINE YOK (urun karari), ama TYT'de olmayan IKI BAGIMSIZ
   KANAL daha var. Gerekceyi kopyalamak yanlis olurdu; geometrinin DORT
   sinyali sunlardir ve dordu de olculmustur:

   1. CIFT BAGIMSIZ OKUMA (tam kapsam, 1213/1213 soru iki kez okundu)
      - 1187 soru birebir (>= 0.995 normalize benzerlik)
      - 16 yuksek (0.95-0.995), 10 hakeme gitti, DUSUK (< 0.85) YOK
      - kirpimda BASILI soru numarasi 1213/1213 ayni okundu
      - hakem turu 46 kalem: 39 P, 6 Q, 1 hakemin kendi okumasi

   2. ANAHTAR SERIDI CIFT OKUMA (TYT'de yoktu)
      Bu kitapta cevap anahtari her sayfanin altinda DUZ basili; 237 seridin
      tamami iki bagimsiz ajan tarafindan okundu ve UYUSMAZLIK SIFIR
      (237/237 sayfa, 1213 girdi).

   3. BASILI ANAHTAR CAPRAZ KONTROLU (iki bagimsiz duzeyde)
      - soru duzeyi: anahtarin harfi transkript edilen siklarda VAR
        (1211/1211; ithal on kontrolu + R5 bekcisi)
      - sayfa duzeyi: seritteki girdi sayisi o sayfada tespit edilen soru
        sayisina esit (237/237 sayfa) -- segmentasyonun bagimsiz yer gercegi

   4. BANNER <-> ANAHTAR ZINCIRI ORTUSMESI (TYT'de yoktu)
      Sayfalarin testlere gruplanmasi iki TAMAMEN BAGIMSIZ kanaldan
      uretildi: (a) sayfa alti seritteki numara zinciri, (b) sayfa ustu
      baslik bandi (iki bagimsiz okuma, 237/237). Iki kanal da 149 test
      buldu ve SAYFA KUMELERI BIREBIR AYNI cikti.

   Bu dort sinyal TRANSKRIPSIYONU ve SEGMENTASYONU dogrular. CEVABIN KENDISI
   dogrulanmadi: cevap kitabin basili anahtarindan gelir ve urun karari
   geregi tek kaynaktir. Ayrim kaybolmasin diye metadata'ya acikca yazilir:

       konsensus_sinyalleri = ['cift_bagimsiz_okuma',
                               'anahtar_seridi_cift_okuma',
                               'basili_anahtar_capraz_kontrolu',
                               'banner_anahtar_zinciri_ortusmesi']

   Ithal sirasinda yazilan `cozum_dogrulamasi='yapilmadi_urun_karari'` alani
   yerinde kalir.

SINYAL LISTESINE GIRMEYEN BIR BULGU
-----------------------------------
Ithal sirasinda iki sorunun resmi "OSYM 2025 TYT" kaynagindan gelen
satirlarla BIREBIR carpistigi gorulmustu (ayni metin + ayni 5 sik -> ayni
md5, ayni dogru cevap, ayni yil/sinav). Bu, hattin tamaminin sifir serbestlik
dereceli bir dis kontroludur -- AMA yalnizca 1213 sorunun 2'sini kapsar.
Satir duzeyinde bir sinyal gibi yazmak diger 1209 icin FAZLA IDDIA olurdu;
bu yuzden `konsensus_sinyalleri` listesine KONULMADI, yalnizca burada ve
GEO_YONTEM.md'de kayitlidir.

NE OLDUGU KONUSUNDA DURUST OLMA
-------------------------------
- quality_review_status: 'pending' -> 'auto_judged_high'
  'human_verified' YAZILMIYOR -- hicbir insan bu sorulari tek tek
  dogrulamadi.
- review_status: 'PENDING' -> 'APPROVED'
  Bu TOPLU sahip onayidir. Metadata'ya yazilir:
      onay_turu = 'toplu_beta_sahibi'
      bireysel_denetim_yapildi = false
- is_ai_generated ALANINA DOKUNULMUYOR -- true kalir. Kapiyi acmanin kolay
  ama yanlis yolu onu false yapmakti; o yol DB'ye yanlis bir kaynak beyani
  birakirdi.

AYNI HASH'LI YABANCI SATIRLAR
-----------------------------
Hedef sorgusu `source_book` ile sinirlidir, bu yuzden ayni soru_hash'i
tasiyan 2 OSYM satiri bu migration'in kapsaminda DEGILDIR; onlar kendi
kaynaklarinda ve zaten aktiftir.

GERI ALINABILIR
---------------
Degistirilen her satirin ONCEKI degerleri GUNLUK'e yazilir; downgrade() tam
olarak o degerleri geri koyar ve eklenen metadata anahtarlarini siler.

Revizyon adi 23 karakter (sinir 32 -- bkz. 0016'nin ogrendigi ders).
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0018_mikro_geo_beta_onay"
down_revision: Union[str, None] = "0017_mikro_geo_konu_agaci"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "mikro_geo_beta_onay_gunlugu_0018"
KAYNAK = "Mikro Orijinal 2025 AYT Geometri Soru Bankasi"

# Eklenen metadata anahtarlari -- downgrade tam olarak bunlari siler.
EK_ANAHTARLAR = (
    "consensus_2signal_run",
    "konsensus_sinyalleri",
    "onay_turu",
    "bireysel_denetim_yapildi",
)

_HEDEF_SQL = """
SELECT qb.id, qb.is_active, qb.review_status, qs.quality_review_status
  FROM question_bank qb
  JOIN question_metadata qm ON qm.id = qb.id
  LEFT JOIN question_statistics qs ON qs.id = qb.id
 WHERE qm.source_book = :kaynak
   AND (qm.pipeline_metadata IS NULL
        OR NOT (qm.pipeline_metadata::jsonb ? 'bayraklar')
        OR NOT ((qm.pipeline_metadata::jsonb -> 'bayraklar') ? 'sik_bos'))
"""

_META_EKLE = sa.text(
    """
    UPDATE question_metadata
       SET pipeline_metadata = (
             pipeline_metadata::jsonb
             || jsonb_build_object(
                  'consensus_2signal_run', true,
                  'konsensus_sinyalleri', jsonb_build_array(
                       'cift_bagimsiz_okuma',
                       'anahtar_seridi_cift_okuma',
                       'basili_anahtar_capraz_kontrolu',
                       'banner_anahtar_zinciri_ortusmesi'),
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
        _log.info("[0018] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0018] mv_safe_for_beta yenilendi")


def _tablolar_var(b) -> bool:
    denetci = sa.inspect(b)
    return all(
        denetci.has_table(t)
        for t in ("question_bank", "question_metadata", "question_statistics")
    )


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0018] soru tablolari yok (taze DB?) -- atlandi")
        return

    hedef = b.execute(sa.text(_HEDEF_SQL), {"kaynak": KAYNAK}).fetchall()
    if not hedef:
        _log.info("[0018] %s satiri yok -- atlandi (veri ithal edilmemis)", KAYNAK)
        return

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("onceki_is_active", sa.Boolean(), nullable=True),
        sa.Column("onceki_review_status", sa.String(), nullable=True),
        sa.Column("onceki_quality_review_status", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    idler = [r[0] for r in hedef]
    b.execute(
        sa.text(
            f"INSERT INTO {GUNLUK} (id, onceki_is_active, onceki_review_status,"  # noqa: S608  # nosec B608
            " onceki_quality_review_status)"
            " VALUES (:id, :akt, :rs, :qrs)"
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
    b.execute(_META_EKLE, {"idler": idler})

    haric = b.execute(
        sa.text(
            "SELECT count(*) FROM question_metadata"
            " WHERE source_book = :kaynak AND id <> ALL(:idler)"
        ),
        {"kaynak": KAYNAK, "idler": idler},
    ).scalar_one()
    _log.info(
        "[0018] beta kapisi acildi: %s satir; sik_bos nedeniyle disarida kalan: %s",
        len(idler),
        haric,
    )
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0018] %s yok -- downgrade atlandi", GUNLUK)
        return
    if not _tablolar_var(b):
        op.drop_table(GUNLUK)
        return

    kayitlar = b.execute(
        sa.text(
            "SELECT id, onceki_is_active, onceki_review_status,"  # noqa: S608  # nosec B608
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

    _log.info("[0018] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
