"""Neofizik sorularini beta kapisindan gecirir (bireysel denetim atlanarak)

Revision ID: 0014_neofizik_beta_toplu_onay
Revises: 0013_neofizik_konu_agaci
Create Date: 2026-09-10

BAGLAM
------
0013 ile ithal edilen 1218 Neofizik sorusu bilerek PASIF yazildi
(is_ai_generated=true + review_status='PENDING'), cunku bireysel insan
denetimi yapilmamisti. Urun sahibi bu denetimi ATLAYIP toplu olarak beta
surumunde yapmaya karar verdi. Bu migration o karari uygular.

NE OLDUGU KONUSUNDA DURUST OLMA
-------------------------------
Kapiyi acmak icin uc alan degisiyor ve ucu de GERCEGI soyluyor:

- quality_review_status: 'pending' -> 'auto_judged_high'
  Dogru, cunku hat bu sorulari otomatik olarak yuksek guvenle yargiladi:
  1319 soru iki kez bagimsiz okundu (%89,3 bayt-bayt ayni; gercek icerik
  uyusmazligi 18 soruda kaldi ve hepsi cozuldu) ve cozum-dogrulama basili
  cevap anahtarlariyla %96,0 uyustu. 'human_verified' YAZILMIYOR -- hicbir
  insan bu sorulari tek tek dogrulamadi.

- review_status: 'PENDING' -> 'APPROVED'
  Bu bir TOPLU sahip onayidir, soru soru denetim degildir. Ayrimin kaybolmamasi
  icin pipeline_metadata'ya acikca yaziliyor:
      onay_turu = 'toplu_beta_sahibi'
      bireysel_denetim_yapildi = false
  Boylece "servis edilen kac soru hic bireysel denetimden gecmedi" sorusu
  tek sorguyla yanitlanabilir.

- pipeline_metadata += consensus_2signal_run
  Dogru: iki bagimsiz okuma + cozum-dogrulama = iki sinyalli uzlasma kosumu.

is_ai_generated ALANINA DOKUNULMUYOR -- true kalir. Bu icerik OCR/AI
kaynaklidir ve DB bunu soylemeye devam etmelidir.

KAPSAM: sik_bos OLANLAR HARIC
-----------------------------
D10'un genel kurali (`bayraklar` icinde 'sik_bos' tasiyan hicbir satir
kapidan gecemez) BOZULMUYOR. Neofizik'in 1218 satirindan 37'si bu bayragi
tasiyor -- sikki metin degil gorsel oldugu icin mevcut metin-tabanli sunum
katmaninda eksik gorunurler. Onlar PASIF kalir; gorsel-sik destegi geldiginde
ayrica ele alinir. Bu migration ~1181 satiri hedefler.

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

revision: str = "0014_neofizik_beta_toplu_onay"
down_revision: Union[str, None] = "0013_neofizik_konu_agaci"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "neofizik_beta_onay_gunlugu_0014"
KAYNAK = "Neofizik AYT Fizik Soru Bankasi 2025"

# Eklenen metadata anahtarlari -- downgrade tam olarak bunlari siler.
EK_ANAHTARLAR = ("consensus_2signal_run", "onay_turu", "bireysel_denetim_yapildi")

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
        _log.info("[0014] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0014] mv_safe_for_beta yenilendi")


def _tablolar_var(b) -> bool:
    denetci = sa.inspect(b)
    return all(
        denetci.has_table(t)
        for t in ("question_bank", "question_metadata", "question_statistics")
    )


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0014] soru tablolari yok (taze DB?) -- atlandi")
        return

    hedef = b.execute(sa.text(_HEDEF_SQL), {"kaynak": KAYNAK}).fetchall()
    if not hedef:
        _log.info("[0014] %s satiri yok -- atlandi (veri ithal edilmemis)", KAYNAK)
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
        [
            {"id": r[0], "akt": r[1], "rs": r[2], "qrs": r[3]}
            for r in hedef
        ],
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
        "[0014] beta kapisi acildi: %s satir; sik_bos nedeniyle disarida kalan: %s",
        len(idler),
        haric,
    )
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0014] %s yok -- downgrade atlandi", GUNLUK)
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

    _log.info("[0014] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
