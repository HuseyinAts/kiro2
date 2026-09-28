"""2024 ACIL TYT Matematik Geometri Kitap-1: modern karsiligi olan eski hat satirlari pasif

Revision ID: 0084_acl24mg_eski_hat_pasif
Revises: 0083_acl24mg_agac
Create Date: 2026-09-28

KARAR
-----
Sahip talimati: siradaki kitaplari ayni sekilde bastan sona isle. Emsal
0072 / 0075. Bu migration SILMEZ; yalniz is_active=FALSE yapar ve downgrade
ile tam geri alinir.

NEDEN (mukerrer olcumu, acil_2024_tyt_matematik_kitap1_mukerrer_adaylari.json)
------------------------------------------------------------------
Ayni kitabin eski aktarimi aktif duruyor:
    2024-AC\u0130L TYT Matematik Geometri Kitap-1: 12 satir, 12 aktif, 7 modern karsilik
GUCLU esleme = govde 3-gram >= 0.9 VE bes sikkin >= 3'u birebir.

MODERN KARSILIK = MODERN ID
---------------------------
Guard kirpim adina degil MODERN ID'ye bakar: (eski id, modern kirpim, modern
id) ciftinde modern id question_bank'ta varsa eski satir is_active=FALSE.
Modern id = uuid5(NAMESPACE_OID, soru_hash(govde, sikler)) -- ithalin formulu.
Taze/CI DB'de modern id yoksa eski satira dokunulmaz.
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0084_acl24mg_eski_hat_pasif"
down_revision: Union[str, None] = "0083_acl24mg_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "acl24mg_eski_hat_gunlugu_0084"
KAYNAK = "2024 ACIL TYT Matematik Geometri Kitap-1"
ITHAL_ARACI = "scripts/kitap/kitap_hat/ithal.py"
ESKI_KAYNAKLAR: tuple[str, ...] = ("2024-AC\u0130L TYT Matematik Geometri Kitap-1",)

# (eski satir id, modern kirpim adi -- ACL24MG- oneksiz, modern id); kaynak:
# mukerrer_adaylari.json eski_hat, modern_karsilik=true. Yorum: eski basili sayfa.
ESKI_MODERN: tuple[tuple[str, str, str], ...] = (
    (
        "22ad7000-562f-5b67-95c2-714804a83f59",
        "T032_03",
        "75b13f0d-fa90-55e9-aa43-ea899232c928",
    ),  # s66
    (
        "d4c7b6df-fd3a-5f9d-835e-662d667c565c",
        "T062_01",
        "0a3f2f4d-16a3-5ef4-be2f-60a27252214a",
    ),  # s131
    (
        "449e4b23-686d-5779-85bf-e99283096ce6",
        "T063_02",
        "dac067e1-fa22-522c-9769-aedf7eb92342",
    ),  # s132
    (
        "c336b806-421e-5ba3-b12e-8c348b99fbec",
        "T063_05",
        "7d7dd15f-72bf-5898-b646-7fa45a062782",
    ),  # s132
    (
        "4a2eb895-80f4-5a56-8883-b6e538385b67",
        "T064_06",
        "5c1393c7-a383-57a4-abcb-917211ae2385",
    ),  # s133
    (
        "5c5f2539-fa37-5eab-8b3b-ef1fa801301b",
        "T079_01",
        "d1e0279e-84b7-5f58-8133-a01767d5143e",
    ),  # s181
    (
        "0f8930bc-fa34-5d94-95f7-bcbb94249e19",
        "T084_02",
        "e26e7575-fab9-56e0-bd14-9c1885e99e3b",
    ),  # s186
)

_ESKI_SQL = """
SELECT qb.id::text, qb.is_active
  FROM question_bank qb
  JOIN question_metadata qm ON qm.id = qb.id
 WHERE qb.id::text = ANY(:idler)
   AND qm.source_book = ANY(:kaynaklar)
   AND (qm.pipeline_metadata::jsonb ->> 'ithal_araci') IS NULL
   AND qb.is_active IS TRUE
"""

_MODERN_SQL = """
SELECT qb.id::text
  FROM question_bank qb
 WHERE qb.id::text = ANY(:idler)
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
        _log.info("[0084] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0084] mv_safe_for_beta yenilendi")


def _tablolar_var(b) -> bool:
    denetci = sa.inspect(b)
    return all(
        denetci.has_table(t)
        for t in ("question_bank", "question_metadata", "topic_hierarchy")
    )


def hedef_idler(modern_var: set[str]) -> list[str]:
    """Modern id'si DB'de bulunan eski satir id'leri (saf fonksiyon, test edilir)."""
    return [e for e, _, mid in ESKI_MODERN if mid in modern_var]


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0084] soru tablolari yok (taze DB?) -- atlandi")
        return
    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("islem", sa.String(), nullable=False),
        sa.Column("onceki_is_active", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    modern = {
        r[0]
        for r in b.execute(
            sa.text(_MODERN_SQL), {"idler": [mid for _, _, mid in ESKI_MODERN]}
        ).fetchall()
    }
    idler = hedef_idler(modern)
    eski = (
        b.execute(
            sa.text(_ESKI_SQL),
            {"idler": idler, "kaynaklar": list(ESKI_KAYNAKLAR)},
        ).fetchall()
        if idler
        else []
    )
    if eski:
        b.execute(
            sa.text(
                f"INSERT INTO {GUNLUK} (id, islem, onceki_is_active)"  # noqa: S608  # nosec B608 - GUNLUK sabit modul duzeyi ad
                " VALUES (:id, 'eski_hat_pasif', :akt)"
            ),
            [{"id": r[0], "akt": r[1]} for r in eski],
        )
        b.execute(
            sa.text(
                "UPDATE question_bank SET is_active = FALSE, updated_at = now()"
                " WHERE id::text = ANY(:idler)"
            ),
            {"idler": [r[0] for r in eski]},
        )
    _log.info("[0084] eski hat: %s aday, %s satir pasife alindi", len(idler), len(eski))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0084] %s yok -- downgrade atlandi", GUNLUK)
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
                " WHERE id::text = :id"
            ),
            {"id": sid, "akt": akt},
        )
    _log.info("[0084] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
