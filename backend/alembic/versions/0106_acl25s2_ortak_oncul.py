"""ACIL 2025 Matematigin Ilaci Sayilar-2: ortak oncul kirpimda olmayan 4 soru servis disi

Revision ID: 0106_acl25s2_ortak_oncul
Revises: 0105_akt20k0_ortak_oncul
Create Date: 2026-09-28

NEDEN (gozle; onceki kitaplarda ortak oncul taramasi)
-----------------------------------------------------
ACL25S2 isleminde okuyucular dort soruya 'ortak bilgi kutusu kirpimda yok'
notu dusmus, sorular yine de 0095 ile aktif olmustu. Sayfa gozle:
  s112 sol sutun tepesi: '5. ve 6. sorulari asagidaki bilgilere gore
  cevaplayiniz.' + olcum tablosu + m = |1.olcum - 2.olcum| bilgisi;
  s113 sol sutun tepesi: '1. ve 2. sorulari asagidaki bilgilere gore
  cevaplayiniz.' + f(t) = 30 . |18 - 2t| + 400.
Oncul numarasiz ve sutun tepesinde; hicbir kirpimda yok (ilk soru dahil).
T065_05, T065_06, T066_01, T066_02 oncul olmadan cevaplanamaz. Tum kitap_hat
kitaplarinda geometrik tarama (sutunun ilk kutusu ustunde kirpima girmemis
murekkep, tam genislik test basliklari haric) yalniz bu iki sayfayi buldu.
Kural AKT20K0 (0105) ile ayni: bayrak 'ortak_oncul_kirpimda_yok',
is_active=FALSE.

Bu migration SILMEZ; onceki is_active ve bayrak durumu GUNLUK'e yazilir,
downgrade tam geri alir. Taze/CI DB'de satir yoksa dokunulmaz.
"""

import logging
from collections.abc import Sequence
from typing import Any, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0106_acl25s2_ortak_oncul"
down_revision: Union[str, None] = "0105_akt20k0_ortak_oncul"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "acl25s2_ortak_oncul_gunlugu_0106"
KAYNAK = "ACIL 2025 Matematigin Ilaci Sayilar-2"
ITHAL_ARACI = "scripts/kitap/kitap_hat/ithal.py"
BAYRAK = "ortak_oncul_kirpimda_yok"
# (birim_kodu, birim_ici_sira): s112 5-6 ve s113 1-2.
HEDEF: tuple[tuple[str, int], ...] = (
    ("ACL25S2-T065", 5),
    ("ACL25S2-T065", 6),
    ("ACL25S2-T066", 1),
    ("ACL25S2-T066", 2),
)

_HEDEF_SQL = """
SELECT qb.id::text, qb.is_active,
       COALESCE((qm.pipeline_metadata::jsonb -> 'bayraklar') ? 'ortak_oncul_kirpimda_yok', FALSE)
  FROM question_bank qb
  JOIN question_metadata qm ON qm.id = qb.id
 WHERE qm.source_book = :kaynak
   AND qm.pipeline_metadata::jsonb ->> 'ithal_araci' = :arac
   AND qm.pipeline_metadata::jsonb ->> 'birim_kodu' = :birim
   AND (qm.pipeline_metadata::jsonb ->> 'birim_ici_sira')::int = :sira
"""

_BAYRAK_EKLE = """
UPDATE question_metadata
   SET pipeline_metadata = jsonb_set(
         pipeline_metadata::jsonb, '{bayraklar}',
         COALESCE(pipeline_metadata::jsonb -> 'bayraklar', '[]'::jsonb)
           || '["ortak_oncul_kirpimda_yok"]'::jsonb)
 WHERE id::text = :id
"""

_BAYRAK_SIL = """
UPDATE question_metadata
   SET pipeline_metadata = jsonb_set(
         pipeline_metadata::jsonb, '{bayraklar}',
         (pipeline_metadata::jsonb -> 'bayraklar') - 'ortak_oncul_kirpimda_yok')
 WHERE id::text = :id
"""

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
        _log.info("[0106] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0106] mv_safe_for_beta yenilendi")


def _tablolar_var(b) -> bool:
    denetci = sa.inspect(b)
    return all(
        denetci.has_table(t)
        for t in ("question_bank", "question_metadata", "topic_hierarchy")
    )


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0106] soru tablolari yok (taze DB?) -- atlandi")
        return
    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("onceki_is_active", sa.Boolean(), nullable=True),
        sa.Column("bayrak_vardi", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    satirlar: list[Any] = []
    for birim, sira in HEDEF:
        satirlar += b.execute(
            sa.text(_HEDEF_SQL),
            {"kaynak": KAYNAK, "arac": ITHAL_ARACI, "birim": birim, "sira": sira},
        ).fetchall()
    for sid, akt, vardi in satirlar:
        b.execute(
            sa.text(
                f"INSERT INTO {GUNLUK} (id, onceki_is_active, bayrak_vardi)"  # noqa: S608  # nosec B608 - GUNLUK sabit modul duzeyi ad
                " VALUES (:id, :akt, :vardi)"
            ),
            {"id": sid, "akt": akt, "vardi": bool(vardi)},
        )
        if not vardi:
            b.execute(sa.text(_BAYRAK_EKLE), {"id": sid})
        b.execute(
            sa.text(
                "UPDATE question_bank SET is_active = FALSE, updated_at = now()"
                " WHERE id::text = :id"
            ),
            {"id": sid},
        )
    _log.info(
        "[0106] %s hedef, %s satir servis disi (%s)", len(HEDEF), len(satirlar), BAYRAK
    )
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0106] %s yok -- downgrade atlandi", GUNLUK)
        return
    if not _tablolar_var(b):
        op.drop_table(GUNLUK)
        return
    kayitlar = b.execute(
        sa.text(f"SELECT id, onceki_is_active, bayrak_vardi FROM {GUNLUK}")  # noqa: S608  # nosec B608 - GUNLUK sabit modul duzeyi ad
    ).fetchall()
    for sid, akt, vardi in kayitlar:
        b.execute(
            sa.text(
                "UPDATE question_bank SET is_active = :akt, updated_at = now()"
                " WHERE id::text = :id"
            ),
            {"id": sid, "akt": akt},
        )
        if not vardi:
            b.execute(sa.text(_BAYRAK_SIL), {"id": sid})
    _log.info("[0106] geri alindi: %s satir", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
