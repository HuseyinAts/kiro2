"""ACIL 2025 Matematigin Ilaci Sayilar-2: modern karsiligi olan eski hat satirlari pasif

Revision ID: 0094_acl25s2_eski_hat_pasif
Revises: 0093_acl25s2_agac
Create Date: 2026-09-28

KARAR
-----
Sahip talimati: siradaki kitaplari ayni sekilde bastan sona isle. Emsal
0072 / 0075. Bu migration SILMEZ; yalniz is_active=FALSE yapar ve downgrade
ile tam geri alinir.

NEDEN (mukerrer olcumu, acil_2025_ilac_sayilar2_mukerrer_adaylari.json)
------------------------------------------------------------------
Ayni kitabin eski aktarimi aktif duruyor:
    AC\u0130L-2025-Matemati\u011fin \u0130lac\u0131 Say\u0131lar-2: 53 satir, 53 aktif, 43 modern karsilik
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

revision: str = "0094_acl25s2_eski_hat_pasif"
down_revision: Union[str, None] = "0093_acl25s2_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "acl25s2_eski_hat_gunlugu_0094"
KAYNAK = "ACIL 2025 Matematigin Ilaci Sayilar-2"
ITHAL_ARACI = "scripts/kitap/kitap_hat/ithal.py"
ESKI_KAYNAKLAR: tuple[str, ...] = (
    "AC\u0130L-2025-Matemati\u011fin \u0130lac\u0131 Say\u0131lar-2",
)

# (eski satir id, modern kirpim adi -- ACL25S2- oneksiz, modern id); kaynak:
# mukerrer_adaylari.json eski_hat, modern_karsilik=true. Yorum: eski basili sayfa.
ESKI_MODERN: tuple[tuple[str, str, str], ...] = (
    (
        "71538ef7-416f-5935-8d28-7a27ce8a489c",
        "T006_10",
        "b31fa814-949b-5265-8ec6-c34bc849e4ee",
    ),  # s15
    (
        "f1331c8c-2526-565c-b908-71713a511dfe",
        "T010_01",
        "8182844b-b0f5-5cc3-8ed6-141da0e89d6e",
    ),  # s21
    (
        "85295b9b-f09e-5b68-8fbd-fb88aaa76a5e",
        "T011_12",
        "f0f1bc9b-cd75-5f87-86af-bdaa76e9f466",
    ),  # s24
    (
        "6dc120b2-4219-5d32-923d-cdcbbd85d4d2",
        "T013_06",
        "ce12600c-4304-5ef5-a68e-b4097c47105c",
    ),  # s27
    (
        "6320e989-3a5d-5491-9ae9-4342e623360b",
        "T014_07",
        "a1fcb297-c83c-5dc4-8f62-94bbd940471c",
    ),  # s30
    (
        "ff33b8aa-1723-5bbf-867f-8e0c2a9310c1",
        "T027_12",
        "96f9553c-f50c-52a6-adbf-5a5b730b58c3",
    ),  # s54
    (
        "4ce9b452-f9b8-5f6a-849c-10e68e35b716",
        "T030_04",
        "2862470b-06da-5634-8097-cc8b48383c9e",
    ),  # s57
    (
        "f3db341d-f2e5-57d0-88ec-383b3bcf9753",
        "T033_02",
        "f2910bf8-c2b5-5590-8d8b-a940bb59b168",
    ),  # s61
    (
        "c239287f-be01-5a28-840f-f343a1989475",
        "T043_07",
        "b8842e1e-543a-5988-8792-3b04b4969e13",
    ),  # s78
    (
        "fd97dafb-0d2b-5881-9b24-d38e91a6c60d",
        "T045_01",
        "b8c3f042-2ae9-51ba-981e-e21b70621d3c",
    ),  # s82
    (
        "8c2ce114-1b67-51c6-900f-7843b6b7d5cd",
        "T046_01",
        "a3da9b53-c3a8-5afb-a3e4-08975b407d2b",
    ),  # s83
    (
        "4996e091-e4d2-5e64-8d7f-5186f08eb01a",
        "T047_01",
        "98dbccf2-c9e8-5975-b7b3-e8f5b2bdef13",
    ),  # s84
    (
        "5b99db06-0113-5e3b-bc92-34df7aed0e2f",
        "T047_03",
        "4b66d0fe-b991-5454-8bfc-fc546cb0ab6b",
    ),  # s84
    (
        "8421930d-a2f6-5e3d-af16-39916f6c5d3d",
        "T047_04",
        "24336cd6-bca7-553a-8020-4323e24ac52e",
    ),  # s84
    (
        "f148e143-572b-5559-94b0-757aa9cf5da4",
        "T048_01",
        "91d6b29b-1dab-5e26-bc25-a63ae80a251c",
    ),  # s85
    (
        "37c80531-db68-588d-bca7-8d3b592a85f3",
        "T049_02",
        "34c70ccb-34a8-57af-aca8-6b467b04aa22",
    ),  # s86
    (
        "d6ad3592-0393-5bb6-b3c0-bbdc99a0aa73",
        "T050_01",
        "2dac92fb-c230-544d-9b32-76d30dbcbd94",
    ),  # s87
    (
        "e40093a3-eb2f-5b4a-b093-e4ed3bf70709",
        "T050_06",
        "0728ea68-81f1-5502-bf56-f7d9c92248aa",
    ),  # s87
    (
        "5cbbf9b5-5a34-576a-9c5c-1e636c15424e",
        "T052_06",
        "fa3da73a-a167-5fbe-b59a-3886dcdf8cea",
    ),  # s89
    (
        "7c5e25d3-2d49-517f-8806-36e167fd8c54",
        "T052_05",
        "0d324312-0e1a-5395-b63a-1d50cba97d24",
    ),  # s89
    (
        "ba1992bd-6a10-59fd-8e96-0f834a019a40",
        "T052_04",
        "5ba59e38-18ce-5d99-ac0f-43a85cc0ab02",
    ),  # s89
    (
        "b4a662cc-c5a7-5a5a-8149-a7353eb85e5e",
        "T052_11",
        "5d4d6212-fef9-59b6-9981-797a37b475bd",
    ),  # s90
    (
        "7ef940bf-a7e4-5163-8e5b-032239931f3a",
        "T054_07",
        "ae8c440b-c898-5ebb-b6da-97bcacbbfef1",
    ),  # s93
    (
        "5772f481-039f-5b36-8a85-6f725e95158b",
        "T056_01",
        "4d5f22a3-8514-5f40-b83f-3bbb85628149",
    ),  # s95
    (
        "f43c8956-c447-58ed-ae69-66c7cb02c81b",
        "T059_06",
        "22a7eb4b-df76-5daa-b640-76d3f72f7193",
    ),  # s99
    (
        "a7055652-a687-589c-9c9c-b956f76912c8",
        "T059_10",
        "b98d571a-3731-500a-bf8f-1af5a44b70bf",
    ),  # s100
    (
        "f3e9d334-06aa-561e-bbdf-ebce6dd6f0fe",
        "T059_08",
        "b0d05f60-396d-5362-abcf-ab75470c3232",
    ),  # s100
    (
        "8658b774-fad8-583b-97d9-4dd9031146d0",
        "T060_11",
        "d01acf68-8918-5186-bf11-40698de33fdc",
    ),  # s102
    (
        "ce4896b8-7826-5f27-9b13-0b1a821df26c",
        "T060_10",
        "4e96c478-6431-5448-a5c9-9259d6f090cf",
    ),  # s102
    (
        "4b5c10c5-f42d-554a-b808-5680fc25cea4",
        "T062_10",
        "e7c8b70e-a402-57e1-8b94-0467e4b8815e",
    ),  # s106
    (
        "fa882ea4-5e35-587c-b2d8-d57859828753",
        "T062_08",
        "189f6cc7-bd17-501a-a6f1-0d2402a85049",
    ),  # s106
    (
        "09e1fd59-61c1-5ff8-8f00-04e25dd191e3",
        "T064_12",
        "37b50f91-9d2b-5826-83a0-2422667a3d24",
    ),  # s110
    (
        "c0d6a4d6-ce8e-5eb6-9e35-9b5b18c024d6",
        "T067_01",
        "acec874c-942d-5f40-8a55-06be759ad4cb",
    ),  # s115
    (
        "e1627195-7662-5250-908f-99e123dae30c",
        "T068_08",
        "393dbacb-494b-5239-8c7f-ea9c0995eb77",
    ),  # s118
    (
        "4bcf0041-cf9d-5f74-9d73-ff1c33ad066f",
        "T069_03",
        "ad5d97f1-50e7-5a37-956b-9ad9f35c4706",
    ),  # s120
    (
        "59b2910d-a2bf-508e-a446-98f2620fede7",
        "T075_01",
        "b8d083eb-234e-5e02-b4ea-9d425289b9ed",
    ),  # s129
    (
        "d4e340a4-fa77-59cb-a94d-55689a96ca91",
        "T077_04",
        "34764c26-1fe1-55a4-9d66-e389ee93fd8e",
    ),  # s132
    (
        "e887a3ec-c7cc-51d6-9046-3c41156ff7fb",
        "T078_01",
        "709fd458-e265-5dee-bbeb-50482bc721be",
    ),  # s133
    (
        "2634b178-75ea-5a82-a115-fcb7c6c88269",
        "T081_07",
        "792bf44e-05fb-5833-be41-5e7c5e09bc65",
    ),  # s139
    (
        "0fc91b94-f20f-5937-bd42-db30c8fba3b9",
        "T095_01",
        "3ce9c103-94d3-5788-8e7d-18f78073cd7f",
    ),  # s165
    (
        "c00a6e0d-1144-5ea4-9a65-8f56cb499340",
        "T104_07",
        "2520740b-dbbc-5e9d-af22-0e5b005bc35c",
    ),  # s179
    (
        "82a2937a-1e79-54f1-8dca-efe7bf6f7937",
        "T105_07",
        "d83817f9-56a8-5159-917a-9209d2d70205",
    ),  # s181
    (
        "11f4ebac-b6d7-5d73-895a-8fea90d06718",
        "T110_09",
        "5498a04d-83dc-5593-bc28-4b4cd469e004",
    ),  # s191
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
        _log.info("[0094] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0094] mv_safe_for_beta yenilendi")


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
        _log.info("[0094] soru tablolari yok (taze DB?) -- atlandi")
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
    _log.info("[0094] eski hat: %s aday, %s satir pasife alindi", len(idler), len(eski))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0094] %s yok -- downgrade atlandi", GUNLUK)
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
    _log.info("[0094] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
