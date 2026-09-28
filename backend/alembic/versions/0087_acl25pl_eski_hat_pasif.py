"""ACIL 2025 Matematigin Ilaci Polinom: modern karsiligi olan eski hat satirlari pasif

Revision ID: 0087_acl25pl_eski_hat_pasif
Revises: 0086_acl25pl_agac
Create Date: 2026-09-28

KARAR
-----
Sahip talimati: siradaki kitaplari ayni sekilde bastan sona isle. Emsal
0072 / 0075. Bu migration SILMEZ; yalniz is_active=FALSE yapar ve downgrade
ile tam geri alinir.

NEDEN (mukerrer olcumu, acil_2025_ilac_polinom_mukerrer_adaylari.json)
------------------------------------------------------------------
Ayni kitabin eski aktarimi aktif duruyor:
    AC\u0130L-2025-Matemati\u011fin \u0130lac\u0131 Polinom: 53 satir, 53 aktif, 38 modern karsilik
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

revision: str = "0087_acl25pl_eski_hat_pasif"
down_revision: Union[str, None] = "0086_acl25pl_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "acl25pl_eski_hat_gunlugu_0087"
KAYNAK = "ACIL 2025 Matematigin Ilaci Polinom"
ITHAL_ARACI = "scripts/kitap/kitap_hat/ithal.py"
ESKI_KAYNAKLAR: tuple[str, ...] = (
    "AC\u0130L-2025-Matemati\u011fin \u0130lac\u0131 Polinom",
)

# (eski satir id, modern kirpim adi -- ACL25PL- oneksiz, modern id); kaynak:
# mukerrer_adaylari.json eski_hat, modern_karsilik=true. Yorum: eski basili sayfa.
ESKI_MODERN: tuple[tuple[str, str, str], ...] = (
    (
        "c09c2a59-44de-5484-a56f-c294d72b6f46",
        "T003_04",
        "3cc61212-b3b4-543a-a95e-46c81a5ba9a1",
    ),  # s10
    (
        "4f8530af-7495-5518-ae03-b1f387c5ae34",
        "T004_11",
        "9fdc15cd-f577-5444-98df-92f53987f9de",
    ),  # s12
    (
        "e808725b-584d-5711-a198-d816930a4d1d",
        "T018_06",
        "0172dbc3-41b9-5f8d-b2e6-8d222bb20c59",
    ),  # s32
    (
        "44b615d1-6c97-5d4e-bb9b-4d0fcc262472",
        "T018_11",
        "fc1775cc-f7ed-58a0-86d1-492ef86091a0",
    ),  # s33
    (
        "f357bbbd-6e2d-503f-aa6d-62d660ec4985",
        "T018_08",
        "65f82037-b3cb-5a43-8e64-5bd12c139d7b",
    ),  # s33
    (
        "35ba9b4d-0867-5549-b4ed-d1cb7a00d3c6",
        "T019_04",
        "eebd8ec2-5e62-5b5e-a46b-f02b396a6e52",
    ),  # s34
    (
        "0c2953d9-a851-5e94-9c5e-1180d4d9f62f",
        "T020_01",
        "31d29566-5c4a-5d8a-a6e7-07d88280fb68",
    ),  # s35
    (
        "58700acf-34fe-5c4c-8e2d-1d4186249ae1",
        "T023_12",
        "8fd168a5-a6bf-5b70-9625-7962db23da69",
    ),  # s41
    (
        "37ee07e8-f10c-5a7c-b99b-3491a0dee519",
        "T028_06",
        "21a78a18-9cfc-5615-a34e-d49a29347adc",
    ),  # s50
    (
        "70dbb008-82af-5fd0-867e-cfaf821381cf",
        "T029_11",
        "73a93d50-96bc-590d-b0ea-df077848771c",
    ),  # s53
    (
        "acf59fec-528a-5b0f-bdae-ad4d80bacc2e",
        "T029_10",
        "92b64806-88e3-573c-b008-b4788d5cd329",
    ),  # s53
    (
        "efaa496b-0333-5408-9b3a-0effbbb8a178",
        "T029_07",
        "25343e20-241b-548b-a09f-219e2e75ae16",
    ),  # s53
    (
        "ea8016fd-e624-5579-b2a6-5ae66743d4f8",
        "T036_10",
        "00dfc7f3-6810-5738-8bab-4daf43e300d7",
    ),  # s67
    (
        "20388896-20ba-5e22-818a-5b8b5422b99f",
        "T041_01",
        "36bd995c-2f02-5904-aa00-0c7b8d5a731b",
    ),  # s74
    (
        "dac7c9bb-02c1-5bc6-a34f-6a417b78e919",
        "T044_12",
        "e806d607-0ae2-5635-9fe1-e76d8fd2c795",
    ),  # s79
    (
        "6ab7ac55-0f25-5778-9c8a-e7f0d96aa32f",
        "T047_02",
        "12f28cc5-5e79-594b-86dd-86e26e24c7f8",
    ),  # s83
    (
        "8fee28d7-b04e-59ad-9a38-de1a72ec1333",
        "T047_01",
        "6811613b-7033-583c-975d-8e0aeb93bea3",
    ),  # s83
    (
        "c9b0e3d0-6f48-58a2-a516-7792470e6025",
        "T050_01",
        "6c30e5e9-e691-5129-9931-2e4dd6cf0025",
    ),  # s87
    (
        "38d627d6-e84b-5acc-a056-fa643f7c4275",
        "T053_09",
        "ff281fdc-c50d-5559-a370-199f2ad4dcfb",
    ),  # s93
    (
        "2ae6b8db-5d48-596b-b220-718960e7c9f2",
        "T055_04",
        "80a6728e-9a87-5fbf-a1fe-0f4dddc04c6c",
    ),  # s96
    (
        "8f58ca60-3823-536d-8b45-e9d13d95cde8",
        "T055_06",
        "10b8d327-ac9d-5943-9236-1c5d9d680c6d",
    ),  # s96
    (
        "00b8ba63-a93f-58fc-9f38-6af61c933e59",
        "T056_08",
        "c1e946d5-f77a-5f0c-9fa7-62ca0cef5a13",
    ),  # s99
    (
        "cc19037b-6762-5150-9353-b6be0ecbf640",
        "T056_07",
        "966ba2d8-f07b-5f10-89b7-e4afd994d6c1",
    ),  # s99
    (
        "3e271c45-8496-564d-99a4-9ee8a3ee6623",
        "T060_08",
        "d6d1cd22-134a-50d8-a937-7716e626febf",
    ),  # s107
    (
        "e5addf5b-a50f-5dc4-b82b-2cdb3655f01c",
        "T060_12",
        "69afd870-8b44-5ff2-96fa-1c846d90fd1c",
    ),  # s107
    (
        "2616d184-e059-56c2-b11b-45e1ee8b2365",
        "T072_08",
        "aab45136-d47e-55f3-a07c-3d70ebca9ce9",
    ),  # s130
    (
        "1ea35e9f-8381-5405-bf46-9381c5b2d557",
        "T076_08",
        "c73d16af-30fc-54ba-b91c-2761f30be6bb",
    ),  # s136
    (
        "c1cb831a-0377-5ac5-a259-bd751f3199ca",
        "T078_10",
        "63f08d3c-a5f8-52ce-a0a7-7ea5774dc0cf",
    ),  # s139
    (
        "8ea03ff2-9f96-5217-b3ab-3a3ee6ec2b92",
        "T084_11",
        "b6015385-160b-54a5-b33f-bd40627afca2",
    ),  # s149
    (
        "3e6cb751-6ced-54ad-bb1f-f1dde200c391",
        "T086_03",
        "68bd79b0-56c4-5498-a60a-e30e0fd34d0e",
    ),  # s152
    (
        "02e6d1b1-32f4-5925-9b70-11a2516d29c7",
        "T088_05",
        "0c6424d0-5f7b-512b-8921-50e8d9253c38",
    ),  # s156
    (
        "01d20ffc-adc0-527e-be89-69dae34c2214",
        "T089_12",
        "7a23bdd5-f541-5991-ad3d-79ef7c36e06b",
    ),  # s159
    (
        "c5b7df93-b08c-58c5-8d9d-2f40757ac46f",
        "T131_01",
        "d35b2286-ea45-562d-ad0a-16e0f7eb3b9c",
    ),  # s231
    (
        "676b393c-0643-5a66-92ca-3c0e1232fabd",
        "T132_06",
        "75d97d5f-001e-5469-81fa-9c1348ea6398",
    ),  # s232
    (
        "d84c37d6-5ddd-5aba-a4d3-c2acf3fe7036",
        "T133_01",
        "57f47f6d-9d68-5072-8bac-9a6fe35a367c",
    ),  # s234
    (
        "3fc04ee8-40c2-5eb4-aa65-02e0749144de",
        "T140_08",
        "ddc59bdb-bf02-5787-86e6-887b7b13a183",
    ),  # s245
    (
        "e019ffbf-9157-528c-b1ba-f7eca50ec250",
        "T153_09",
        "15797aac-c9d7-508c-8b98-768ba4519b91",
    ),  # s267
    (
        "f34e61ea-4585-59d9-aa17-44db0e987e19",
        "T156_08",
        "b827d79f-8524-55d5-95f9-29858249bb60",
    ),  # s273
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
        _log.info("[0087] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0087] mv_safe_for_beta yenilendi")


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
        _log.info("[0087] soru tablolari yok (taze DB?) -- atlandi")
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
    _log.info("[0087] eski hat: %s aday, %s satir pasife alindi", len(idler), len(eski))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0087] %s yok -- downgrade atlandi", GUNLUK)
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
    _log.info("[0087] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
