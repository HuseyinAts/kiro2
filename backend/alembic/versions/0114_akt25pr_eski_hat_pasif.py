"""AKTIF 2025 TYT Paragraf Soru Bankasi: modern karsiligi olan eski hat satirlari pasif

Revision ID: 0114_akt25pr_eski_hat_pasif
Revises: 0113_akt25pr_agac
Create Date: 2026-09-28

KARAR
-----
Sahip talimati: siradaki kitaplari ayni sekilde bastan sona isle. Emsal
0072 / 0075. Bu migration SILMEZ; yalniz is_active=FALSE yapar ve downgrade
ile tam geri alinir.

NEDEN (mukerrer olcumu, aktif_2025_tyt_paragraf_mukerrer_adaylari.json)
------------------------------------------------------------------
Ayni kitabin eski aktarimi aktif duruyor:
    Aktif Ogrenme Tyt Paragraf Soru Bankas\u0131 2025: 19 satir, 19 aktif, 13 modern karsilik
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

revision: str = "0114_akt25pr_eski_hat_pasif"
down_revision: Union[str, None] = "0113_akt25pr_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "akt25pr_eski_hat_gunlugu_0114"
KAYNAK = "AKTIF 2025 TYT Paragraf Soru Bankasi"
ITHAL_ARACI = "scripts/kitap/kitap_hat/ithal.py"
ESKI_KAYNAKLAR: tuple[str, ...] = ("Aktif Ogrenme Tyt Paragraf Soru Bankas\u0131 2025",)

# (eski satir id, modern kirpim adi -- AKT25PR- oneksiz, modern id); kaynak:
# mukerrer_adaylari.json eski_hat, modern_karsilik=true. Yorum: eski basili sayfa.
ESKI_MODERN: tuple[tuple[str, str, str], ...] = (
    (
        "c48e9fa7-82ef-5226-89e1-831d910fdc47",
        "T007_01",
        "68fd6a11-726e-520e-be0f-2c45dda0420a",
    ),  # s34
    (
        "5464633f-6aab-5f86-8c41-ece03c5c5278",
        "T009_08",
        "e252e652-48b1-5a4f-a288-aaee9e5f9fd3",
    ),  # s42
    (
        "55353f2d-223d-573e-a7c3-e4d459fd63f9",
        "T011_06",
        "48aab33f-a869-5145-9f66-09bd910a4801",
    ),  # s56
    (
        "dc2548ee-4085-5fd8-acab-6bcd19cc2cfc",
        "T011_11",
        "c569431a-7b9b-5a1a-9133-626a9f3b7858",
    ),  # s57
    (
        "7f775f65-c656-5b31-9151-445222205101",
        "T015_05",
        "4d1bc62a-ba83-56b6-8b33-de74d371bc9a",
    ),  # s68
    (
        "843cf941-49bd-5c20-9c30-f0b9f2958bce",
        "T017_12",
        "328daab9-186f-5494-a7d6-7e28c031a215",
    ),  # s79
    (
        "b0a5c27d-a296-501b-85b7-640e5b64eacd",
        "T018_10",
        "09566266-0f3c-5560-9d6f-1817a974b51f",
    ),  # s84
    (
        "2104d19b-959e-539b-8c46-cef0914f9c9d",
        "T025_08",
        "333d2f40-56da-5732-a6f9-f027f8dcd666",
    ),  # s118
    (
        "9f9e0b93-bdd7-534f-bc3d-41f992ea585c",
        "T025_06",
        "3880850a-81d2-5e17-8ba6-7285b3f16c3e",
    ),  # s118
    (
        "a3413c62-8e9a-52b4-9c6a-26a845c11a95",
        "T025_10",
        "73ab1d42-1861-5af4-96e4-588e28bffccc",
    ),  # s119
    (
        "e82ed301-104f-509c-bc6c-9139bfb3aeae",
        "T027_18",
        "42ff7b20-f22b-5414-b15a-1768ba143327",
    ),  # s131
    (
        "0ecf0896-6a0b-578b-bf32-5505646b1a03",
        "T029_16",
        "785fdbf2-cddf-5525-8a72-6087a60f7aed",
    ),  # s140
    (
        "e9f23b0c-de7d-5e08-80d3-a65a870629f9",
        "T030_05",
        "6f1ce974-3999-5818-ae8b-ee24fa07fee9",
    ),  # s143
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
        _log.info("[0114] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0114] mv_safe_for_beta yenilendi")


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
        _log.info("[0114] soru tablolari yok (taze DB?) -- atlandi")
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
    _log.info("[0114] eski hat: %s aday, %s satir pasife alindi", len(idler), len(eski))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0114] %s yok -- downgrade atlandi", GUNLUK)
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
    _log.info("[0114] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
