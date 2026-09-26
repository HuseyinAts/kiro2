"""345 Start Matematik: kitapta olmayan 3 eski hat satiri pasif

Revision ID: 0058_stm345_eski_hat_pasif
Revises: 0057_stm345_agac
Create Date: 2026-09-26

SAHIP KARARI (26 Eyl 2026)
--------------------------
"Bu 3 eski satir pasife alinsin".

NEDEN (Faz 5 olcumu, STM_345_YONTEM.md bolum 5b)
-----------------------------------------------
'345 2025 Start Matematik' kaynak adini tasiyan, ithal_araci TASIMAYAN 3
eski satir. Basili sayfalari (194/203/209 = dosya 195/204/210) gozle
incelendi: uc soru da sayfada YOK (sayfalar denklem sistemi / sayi
dogrusu araligi / esitsizlik alistirmalari); kitabin 371 sorusuna en yakin
govde 3-gram 0.13-0.26. Ikiz degil, kitapta karsiligi olmayan satirlar.

NE YAPAR
--------
is_active = FALSE; SILINMEZ, baska alana dokunulmaz. Guard: satir kaynak
adini tasiyor, ithal_araci yok ve hala aktif. Degisen her satirin onceki
is_active degeri GUNLUK'e yazilir; downgrade onu geri yukler. Konu sayaci
ve beta gorunumu yenilenir.

Revizyon adi 26 karakter (sinir 32).
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0058_stm345_eski_hat_pasif"
down_revision: Union[str, None] = "0057_stm345_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "stm345_eski_hat_gunlugu_0058"
KAYNAK = "345 2025 Start Matematik"

# Basili sayfa -> satir (345_2025_start_matematik_mukerrer_adaylari.json
# eski_hat alani).
ESKI_HAT_PASIF: tuple[str, ...] = (
    "fc2fc6b8-f93a-5490-93f5-8462af9c66b8",  # s194
    "0bd78e59-0201-5544-9780-0bb6682a514e",  # s203
    "be4bf295-3df4-52da-9872-5ef8770fa0d4",  # s209
)

_ESKI_SQL = """
SELECT qb.id, qb.is_active
  FROM question_bank qb
  JOIN question_metadata qm ON qm.id = qb.id
 WHERE qb.id = ANY(:idler)
   AND qm.source_book = :kaynak
   AND (qm.pipeline_metadata::jsonb ->> 'ithal_araci') IS NULL
   AND qb.is_active IS TRUE
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
        _log.info("[0058] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0058] mv_safe_for_beta yenilendi")


def _tablolar_var(b) -> bool:
    denetci = sa.inspect(b)
    return all(
        denetci.has_table(t)
        for t in ("question_bank", "question_metadata", "topic_hierarchy")
    )


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0058] soru tablolari yok (taze DB?) -- atlandi")
        return
    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("islem", sa.String(), nullable=False),
        sa.Column("onceki_is_active", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    eski = b.execute(
        sa.text(_ESKI_SQL), {"idler": list(ESKI_HAT_PASIF), "kaynak": KAYNAK}
    ).fetchall()
    if eski:
        b.execute(
            sa.text(
                f"INSERT INTO {GUNLUK} (id, islem, onceki_is_active)"  # noqa: S608  # nosec B608 - GUNLUK sabit modul duzeyi ad
                " VALUES (:id, 'eski_hat_pasif', :akt)"
            ),
            [{"id": str(r[0]), "akt": r[1]} for r in eski],
        )
        b.execute(
            sa.text(
                "UPDATE question_bank SET is_active = FALSE, updated_at = now()"
                " WHERE id = ANY(:idler)"
            ),
            {"idler": [r[0] for r in eski]},
        )
    _log.info("[0058] eski hat: %s satir pasife alindi", len(eski))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0058] %s yok -- downgrade atlandi", GUNLUK)
        return
    if not _tablolar_var(b):
        op.drop_table(GUNLUK)
        return
    kayitlar = b.execute(
        sa.text(f"SELECT id, onceki_is_active FROM {GUNLUK}")  # noqa: S608  # nosec B608 - GUNLUK sabit modul duzeyi ad
    ).fetchall()
    for sid, akt in kayitlar:
        b.execute(
            sa.text(
                "UPDATE question_bank SET is_active = :akt, updated_at = now()"
                " WHERE id = :id"
            ),
            {"id": sid, "akt": akt},
        )
    _log.info("[0058] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
