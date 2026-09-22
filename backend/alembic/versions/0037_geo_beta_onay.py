"""ACIL + C1CELL geometri kitaplarini beta kapisindan gecirir (toplu sahip onayi)

Revision ID: 0037_geo_beta_onay
Revises: 0036_geo_gorsel_url
Create Date: 2026-09-21

BAGLAM
------
Iki geometri kitabi bilerek PASIF ithal edilmisti:

    ACIL 2023-2024 TYT-AYT Geometri Soru Bankasi ... 1730 satir (PR #304)
    C1CELL 2024 TYT-AYT Geometri Soru Bankasi ...... 1770 satir (PR #311-314)

Urun sahibi bireysel insan denetimini ATLAYIP toplu olarak beta surumunde
yapmaya karar verdi; ayni karar daha once 0014, 0016, 0018 ve 0023 ile
uygulandi. Bu migration onlarin karsiligidir.

ON KOSUL: 0036
--------------
Bu iki kitabin `question_image_url` degerleri dosya sistemi yoluydu
(tarayici cozemez). Aktiflestirme oncesi olculdu ve 0036 onardi. Onarim
olmadan ACIL'in 1513, C1CELL'in 1519 sekilli sorusu -- toplam 3032 --
cozulemez halde servis edilecekti. 0036 sonrasi olcum: iki kitapta da
1730/1730 ve 1770/1770 URL `/static/crops/` ile basliyor; 50 rastgele
ornek calisan backend'den 200 + gercek PNG dondu.

KAPI YUKU OLCULDU, TAHMIN EDILMEDI
----------------------------------
`v_safe_for_beta` tanimi pg_views'ten okundu ve her kosul iki kitap icin
AYRI sayildi (backend/_geo1_gecici/_kapi_olc_geo.py):

    kosul                                   ACIL         C1CELL
    pipeline_metadata NOT NULL ........ 1730/1730     1770/1770
    demoted_at yok .................... 1730/1730     1770/1770
    topic_match_quality <> fallback ... 1730/1730     1770/1770
    match_tier tier1 degil ............ 1730/1730     1770/1770
    sik_bos bayragi yok ............... 1728/1730     1770/1770
    quality_review_status uygun .......    0/1730        0/1770
    uyum sinyali (6 anahtardan biri) ..    0/1730        0/1770
    (is_ai_generated=false OR APPROVED)    0/1730        0/1770
    is_active .........................    0/1730        0/1770
    primary_topic_id dolu ............. 1730/1730     1770/1770
    question_image_url dolu ........... 1730/1730     1770/1770

Kapiyi tutan UC kilit var; bu migration ucunu de acar, is_active da
acilir. Ustteki kosullarin geri kalani zaten geciyor.

HEDEF 3500 DEGIL 3498
---------------------
Nominal kapsam 1730 + 1770 = 3500 idi. Gercek sayi 3498: ACIL'in iki
satiri `sik_bos` bayragi tasiyor ve bu bayrak kapinin KENDI kosulu; o
satirlar bu migration ne yaparsa yapsin kapidan gecemez. Ikisi de tek tek
bakildi (olcum, tahmin degil):

    s0328_sag_1 -- B sikki bos (kaynak dizgi kusuru + okunamayan parca)
    s0380_sag_2 -- E sikki bos VE dogru cevap E (anahtar sikki okunamadi)

Ikincisi zaten servis edilmemeli: dogru sikkin metni yok.
`gorsel_yok_sekilli` bayragi iki kitapta da 0 olctu, bu yuzden 0023'teki
gibi bir urun istisnasi GEREKMEDI.

KONSENSUS GEREKCESI HER KITAP ICIN AYRI YAZILDI
-----------------------------------------------
0023'un dersi: baska bir kitabin sinyallerini kopyalamak yanlistir. Her
kitabin sinyalleri kendi belgesinden okundu.

1. ACIL 2023-2024 (GEO_ACIL_2324_YONTEM.md)
   - anahtar_dort_kanal_sifir_uyusmazlik: cevap anahtari uc okuma
     kanalindan (A: 2x montaj ileri, B: 1.5x montaj ters, C: 4x tek tek
     secili testler) okundu; A ile B arasinda fark 0, 138 testin 138'i ve
     1881 cevabin 1881'i birebir ayni.
   - test_basina_simge_sayisi_esittir_cevap_sayisi: kitabin dizgisinden
     gelen BAGIMSIZ sayim. 138/138 test tutuyor, 1881 == 1881.
   - yedi_yapisal_kapi_mutasyonla_dogrulandi: veri seti kitabin kendi
     anahtarina ve kirpim kutularina karsi yedi kapidan gecti; kapilarin
     korlugu yedi mutasyonla olculdu ve yedisi de tetikledi.

2. C1CELL 2024 (GEO_C1CELL_2024_KESIF.md)
   - anahtar_uc_kanal_hakemle_uzlasti: anahtar uc bagimsiz kanaldan
     okundu; uyusmayan hucreler yuksek buyutmede hakem okumasiyla karara
     baglandi (hakem 5 hatayi ilk okumada buldu, ilk gecis %99,72). Son
     durumda 1770 cevabin tamaminda uyusmazlik yok.
   - birim_simge_sayisi_esittir_cevap_sayisi: birim sinirlari basili
     degildi; "N'e geri topla" ile cizildi ve 163 birimin 163'unde simge
     sayisi cevap sayisina esit cikti (1770 == 1770).
   - basili_numara_esittir_birim_ici_sira: 1770/1770.
   - ithal_kapilari_mutasyonla_dogrulandi: 13 mutasyon uygulandi; ilk
     gecis 12'sini yakaladi, kacan delik kapatildi, ikinci gecis 13/13.

NE OLDUGU KONUSUNDA DURUST OLMA
-------------------------------
- quality_review_status: 'pending' -> 'auto_judged_high'
  'human_verified' YAZILMIYOR -- hicbir insan bu sorulari tek tek
  dogrulamadi.
- review_status: 'PENDING' -> 'APPROVED'. Bu TOPLU sahip onayidir;
  metadata'ya `onay_turu='toplu_beta_sahibi'` ve
  `bireysel_denetim_yapildi=false` yazilir.
- is_ai_generated ALANINA DOKUNULMUYOR -- true kalir.
- CEVAPLAR DOGRULANMADI. Iki kitapta da tek cevap kaynagi kitabin BASILI
  ANAHTARIDIR (urun karari); sorular tekrar cozulmedi. Ustteki sinyaller
  TRANSKRIPSIYONU ve SEGMENTASYONU dogrular, cevabin kendisini degil.
- METIN iki kitapta da TAM olarak ikinci kez okunmadi (cift okuma yalniz
  cevap anahtari icin yapildi). Sinyal listesi bu eksigi gizlemez.
- ACIL'de 151 soru okuyucu diski ortmesi yuzunden ithale HIC girmedi;
  ayrica 36 satirda kitabin kendi dizgi kusuru, 10 satirda okunamayan
  parca isaretli.
- C1CELL'de 1 soruda siklar GRAFIKTIR; sik alanlarinda "(gorsel sik)"
  yazar ve gercek sikler tam soru kirpiminda gorunur.
- Sinav turu soru duzeyinde OLCULMEDI: iki kitap da TYT ve AYT sorularini
  karisik basiyor; satirlara 'AYT' yazildi ve durum
  `pipeline_metadata.sinav_turu_kaynagi` ile isaretli.

TELIF
-----
Iki kitap da ticari soru bankasidir ve satirlarin `pipeline_metadata.telif`
alani "hak sahibinin izni olmadan servis edilemez; aktiflestirme ayri
karar" der. Bu migration o AYRI KARARIN uygulanmasidir; karar urun
sahibinindir.

AYNI HASH'LI YABANCI SATIRLAR
-----------------------------
Hedef sorgusu `source_book` ile sinirlidir; ayni soru_hash'ini tasiyan
baska kaynaklarin satirlari bu migration'in kapsaminda DEGILDIR.

GERI ALINABILIR
---------------
Degistirilen her satirin ONCEKI degerleri GUNLUK'e yazilir; downgrade tam
olarak o degerleri geri koyar ve eklenen metadata anahtarlarini siler.

Revizyon adi 18 karakter (sinir 32).
"""

import json
import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0037_geo_beta_onay"
down_revision: Union[str, None] = "0036_geo_gorsel_url"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "geo_beta_onay_gunlugu_0037"

KAYNAKLAR: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "ACIL 2023-2024 TYT-AYT Geometri Soru Bankasi",
        (
            "anahtar_dort_kanal_sifir_uyusmazlik",
            "test_basina_simge_sayisi_esittir_cevap_sayisi",
            "yedi_yapisal_kapi_mutasyonla_dogrulandi",
        ),
    ),
    (
        "C1CELL 2024 TYT-AYT Geometri Soru Bankasi",
        (
            "anahtar_uc_kanal_hakemle_uzlasti",
            "birim_simge_sayisi_esittir_cevap_sayisi",
            "basili_numara_esittir_birim_ici_sira",
            "ithal_kapilari_mutasyonla_dogrulandi",
        ),
    ),
)

EK_ANAHTARLAR = (
    "consensus_2signal_run",
    "konsensus_sinyalleri",
    "onay_turu",
    "bireysel_denetim_yapildi",
)

# `sik_bos` kapinin KENDI kosulu; o satirlar disarida birakilir.
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
        _log.info("[0037] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0037] mv_safe_for_beta yenilendi")


def _tablolar_var(b) -> bool:
    denetci = sa.inspect(b)
    return all(
        denetci.has_table(t)
        for t in ("question_bank", "question_metadata", "question_statistics")
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
    hedef = b.execute(sa.text(_HEDEF_SQL), {"kaynak": kaynak}).fetchall()
    if not hedef:
        _log.info("[0037] %s satiri yok -- atlandi", kaynak)
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
        "[0037] %s: %s satir acildi, sik_bos nedeniyle disarida: %s",
        kaynak,
        len(idler),
        haric,
    )
    return len(idler)


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0037] soru tablolari yok (taze DB?) -- atlandi")
        return

    var_mi = any(
        b.execute(
            sa.text("SELECT 1 FROM question_metadata WHERE source_book = :k LIMIT 1"),
            {"k": kaynak},
        ).first()
        for kaynak, _ in KAYNAKLAR
    )
    if not var_mi:
        _log.info("[0037] geometri satiri yok -- atlandi (veri ithal edilmemis)")
        return

    _gunlugu_kur()
    toplam = sum(_kitabi_ac(b, kaynak, sinyaller) for kaynak, sinyaller in KAYNAKLAR)
    _log.info("[0037] beta kapisi acildi: toplam %s satir", toplam)
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0037] %s yok -- downgrade atlandi", GUNLUK)
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

    _log.info("[0037] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
