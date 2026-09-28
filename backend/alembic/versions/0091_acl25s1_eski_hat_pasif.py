"""ACIL 2025 Matematigin Ilaci Sayilar-1: modern karsiligi olan eski hat satirlari pasif

Revision ID: 0091_acl25s1_eski_hat_pasif
Revises: 0090_acl25s1_agac
Create Date: 2026-09-28

KARAR
-----
Sahip talimati: siradaki kitaplari ayni sekilde bastan sona isle. Emsal
0072 / 0075. Bu migration SILMEZ; yalniz is_active=FALSE yapar ve downgrade
ile tam geri alinir.

NEDEN (mukerrer olcumu, acil_2025_ilac_sayilar1_mukerrer_adaylari.json)
------------------------------------------------------------------
Ayni kitabin eski aktarimi aktif duruyor:
    AC\u0130L-2025-Matemati\u011fin \u0130lac\u0131 Say\u0131lar-1: 23 satir, 23 aktif, 19 modern karsilik
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

revision: str = "0091_acl25s1_eski_hat_pasif"
down_revision: Union[str, None] = "0090_acl25s1_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "acl25s1_eski_hat_gunlugu_0091"
KAYNAK = "ACIL 2025 Matematigin Ilaci Sayilar-1"
ITHAL_ARACI = "scripts/kitap/kitap_hat/ithal.py"
ESKI_KAYNAKLAR: tuple[str, ...] = (
    "AC\u0130L-2025-Matemati\u011fin \u0130lac\u0131 Say\u0131lar-1",
)

# (eski satir id, modern kirpim adi -- ACL25S1- oneksiz, modern id); kaynak:
# mukerrer_adaylari.json eski_hat, modern_karsilik=true. Yorum: eski basili sayfa.
ESKI_MODERN: tuple[tuple[str, str, str], ...] = (
    (
        "40135a19-790f-56c5-84b0-c22069875baa",
        "T008_11",
        "4b04b790-e407-5ae0-83a8-281e16fdcbdf",
    ),  # s18
    (
        "54b9c32f-3c60-5e63-8c53-91ccce3e6061",
        "T011_09",
        "765e4308-4526-523b-846b-96d3accf4aa2",
    ),  # s24
    (
        "1f711651-822d-5467-a980-7fe7d523485d",
        "T012_15",
        "e98aa372-8ac7-5227-ae7d-2f84b004f856",
    ),  # s26
    (
        "a5a678fd-c9b7-592a-9162-ceb6e191ff31",
        "T016_01",
        "bb7631e4-09af-5447-a643-4e23a95c66a5",
    ),  # s33
    (
        "0306267a-3aa9-5a61-a8cf-1bfe9aedb800",
        "T017_06",
        "14ec0596-4561-5e89-a6f6-96c5463c485b",
    ),  # s36
    (
        "12b8e256-d699-50a6-9458-0145c363e94b",
        "T021_10",
        "32bcf25c-2db6-5906-8bda-4d9f57b1b0d4",
    ),  # s45
    (
        "e64d8969-387d-5255-85b5-f84ba6b764bb",
        "T021_07",
        "1b5b0aa2-0d74-5a4f-b198-a5c234c599cb",
    ),  # s45
    (
        "f960ba08-dbf8-5f84-b4a8-2c9f9a065f32",
        "T025_07",
        "2aae82a2-12e2-51fd-8923-d5359d9905c1",
    ),  # s51
    (
        "df1e2757-d428-5990-b59f-0664491a23a3",
        "T027_12",
        "d12d0000-d493-5100-a11e-b2441843320d",
    ),  # s54
    (
        "d1e1da6d-94b0-5650-91dc-c8db24fa96ab",
        "T029_07",
        "1efcf8f8-6f4c-5924-ada1-5ef18d870bd7",
    ),  # s57
    (
        "14674050-a06f-5ece-a3ee-b07a1b7d4237",
        "T039_06",
        "5c9bbd17-f300-599e-85e4-62e63c4c7c2f",
    ),  # s73
    (
        "e7f3a673-fbf2-549a-bf3e-bb2a4d570f01",
        "T050_01",
        "30d9644c-c235-5894-8f19-1632640ac5ab",
    ),  # s93
    (
        "94add494-244a-5b34-977d-c1faf23f36f1",
        "T050_08",
        "4ade2c65-6e5c-5288-848d-e4aab80364df",
    ),  # s94
    (
        "c5d824ee-7e4f-5ba6-81a7-db97bdd1d42c",
        "T056_07",
        "c2c76606-ac29-579a-8f8e-a699a7e71bfc",
    ),  # s106
    (
        "c36e217b-ae03-5abf-af7e-9cf0b11bb784",
        "T070_12",
        "f4a0ce1a-6c1d-5603-b956-79f76eecd495",
    ),  # s130
    (
        "eb46c4c3-0330-5fda-97f0-b07b0412a01f",
        "T070_07",
        "8007152b-060a-59ad-b02e-09dbebbef97e",
    ),  # s130
    (
        "e48c3d45-d08a-5159-bed9-92674ad8a4ea",
        "T088_01",
        "23158977-1355-5c72-a3c1-758db7001f07",
    ),  # s158
    (
        "872c4b6b-19fc-5f3f-bd52-774a73c9dd34",
        "T092_09",
        "9711af29-c96f-5ac3-ab09-08d1736fcf62",
    ),  # s166
    (
        "6c17a7db-3ac8-5688-a8c1-ff735c90c141",
        "T097_06",
        "90150620-8071-5b84-a885-4d89fb784ac2",
    ),  # s176
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
        _log.info("[0091] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0091] mv_safe_for_beta yenilendi")


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
        _log.info("[0091] soru tablolari yok (taze DB?) -- atlandi")
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
    _log.info("[0091] eski hat: %s aday, %s satir pasife alindi", len(idler), len(eski))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0091] %s yok -- downgrade atlandi", GUNLUK)
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
    _log.info("[0091] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
