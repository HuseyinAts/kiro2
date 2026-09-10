"""Neofizik TYT sorularini beta kapisindan gecirir (bireysel denetim atlanarak)

Revision ID: 0016_neofizik_tyt_beta_onay
Revises: 0015_neofizik_tyt_konu_agaci
Create Date: 2026-09-10

BAGLAM
------
0015 ile ithal edilen 891 TYT sorusu bilerek PASIF yazildi
(is_ai_generated=true + review_status='PENDING'). Urun sahibi bireysel
insan denetimini ATLAYIP toplu olarak beta surumunde yapmaya karar verdi;
AYT icin ayni karar 0014 ile uygulanmisti. Bu migration TYT karsiligidir.

KAPI YUKU OLCULDU, TAHMIN EDILMEDI
----------------------------------
`v_safe_for_beta` tanimi pg_views'ten okundu ve her kosul TYT satirlarina
karsi ayri ayri sayildi:

    demoted_at yok ................................ 891/891 GECIYOR
    pipeline_metadata NOT NULL .................... 891/891 GECIYOR
    sik_bos yok ................................... 827/891 (64'u engelli)
    quality_review_status in (hv, auto_judged_high)   0/891 ENGEL
    (is_ai_generated=false OR review_status=APPROVED) 0/891 ENGEL
    uyum sinyali (6 anahtardan biri) ...............   0/891 ENGEL

Yani kapiyi tutan UC kilit var; bu migration ucunu de acar. Servis katmani
ayrica is_active ister, o da acilir.

AYT'DEN (0014) AYRILAN NOKTA -- BURASI ONEMLI
---------------------------------------------
0014'te `auto_judged_high` gerekcesi IKI sinyale dayaniyordu: cift bagimsiz
okuma VE bagimsiz cozum-dogrulamasi (%96,0 anahtarla uyum).

TYT'de bagimsiz cozum dogrulamasi YOK -- urun karari geregi sorular tekrar
cozulmedi. Ayni gerekceyi kopyalamak YANLIS OLURDU. TYT'nin iki sinyali
sunlardir ve ikisi de olculdu:

  1. CIFT BAGIMSIZ OKUMA (tam kapsam, 891/891 soru iki kez okundu)
     - bicimsel normalizasyon sonrasi hakem disi 870/870 BIREBIR
     - kalan 21 soru hakem turunda yuksek cozunurluklu kirpimla cozuldu
     - hakem bulgusu: uyusmazliklarin hicbiri OKUMA HATASI degildi
       (konvansiyon farki ya da kitabin kendi dizgi hatasi)

  2. BASILI CEVAP ANAHTARI CAPRAZ KONTROLU (iki bagimsiz duzeyde)
     - soru duzeyi: anahtarin harfi transkript edilen siklarda VAR
       (891/891; ithal on kontrolu + bekci)
     - blok duzeyi: anahtardaki cevap sayisi o bloktaki soru sayisina esit
       (109/109 blok) -- segmentasyonun bagimsiz yer gercegi

Bu iki sinyal TRANSKRIPSIYONU dogrular. CEVABIN KENDISI dogrulanmadi:
cevap kitabin basili anahtarindan gelir ve urun karari geregi tek kaynaktir.
Bu ayrim kaybolmasin diye metadata'ya acikca yazilir:

    konsensus_sinyalleri = ['cift_bagimsiz_okuma',
                            'basili_anahtar_capraz_kontrolu']

Ayrica ithal sirasinda yazilan `cozum_dogrulamasi='yapilmadi_urun_karari'`
alani yerinde kalir; "cevaplar bagimsiz dogrulandi mi" sorusu tek sorguyla
yanitlanabilir.

NE OLDUGU KONUSUNDA DURUST OLMA
-------------------------------
- quality_review_status: 'pending' -> 'auto_judged_high'
  'human_verified' YAZILMIYOR -- hicbir insan bu sorulari tek tek
  dogrulamadi.
- review_status: 'PENDING' -> 'APPROVED'
  Bu TOPLU sahip onayidir. Metadata'ya yazilir:
      onay_turu = 'toplu_beta_sahibi'
      bireysel_denetim_yapildi = false
- is_ai_generated ALANINA DOKUNULMUYOR -- true kalir.

KAPSAM: sik_bos OLANLAR HARIC
-----------------------------
D10'un genel kurali bozulmuyor: `bayraklar` icinde 'sik_bos' tasiyan hicbir
satir kapidan gecemez. TYT'nin 891 satirindan 64'u bu bayragi tasiyor
(sikki metin degil gorsel). Onlar PASIF kalir. Hedef: 827 satir.

REVIZYON ADI NEDEN KISA
-----------------------
Ilk deneme `0016_neofizik_tyt_beta_toplu_onay` (33 karakter) idi ve alembic
kendi `alembic_version.version_num` kolonuna yazarken patladi:
`value too long for type character varying(32)`. Migration'in kendi
UPDATE'leri sorunsuz kosmustu (827 satir), islem geri alindi ve DB
dokunulmadan kaldi. Revizyon adlari 32 KARAKTERI ASMAMALI.

GERI ALINABILIR
---------------
Degistirilen her satirin ONCEKI degerleri GUNLUK'e yazilir; downgrade()
tam olarak o degerleri geri koyar ve eklenen metadata anahtarlarini siler.
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0016_neofizik_tyt_beta_onay"
down_revision: Union[str, None] = "0015_neofizik_tyt_konu_agaci"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "neofizik_tyt_beta_onay_gunlugu_0016"
KAYNAK = "Neofizik TYT Fizik Soru Bankasi"

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
                       'basili_anahtar_capraz_kontrolu'),
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
        _log.info("[0016] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0016] mv_safe_for_beta yenilendi")


def _tablolar_var(b) -> bool:
    denetci = sa.inspect(b)
    return all(
        denetci.has_table(t)
        for t in ("question_bank", "question_metadata", "question_statistics")
    )


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0016] soru tablolari yok (taze DB?) -- atlandi")
        return

    hedef = b.execute(sa.text(_HEDEF_SQL), {"kaynak": KAYNAK}).fetchall()
    if not hedef:
        _log.info("[0016] %s satiri yok -- atlandi (veri ithal edilmemis)", KAYNAK)
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
        "[0016] beta kapisi acildi: %s satir; sik_bos nedeniyle disarida kalan: %s",
        len(idler),
        haric,
    )
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0016] %s yok -- downgrade atlandi", GUNLUK)
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

    _log.info("[0016] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
