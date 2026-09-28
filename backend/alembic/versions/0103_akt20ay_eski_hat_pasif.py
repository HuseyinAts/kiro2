"""2019-2020 Aktif AYT Kimya: modern karsiligi olan eski hat satirlari pasif

Revision ID: 0103_akt20ay_eski_hat_pasif
Revises: 0102_akt20ay_agac
Create Date: 2026-09-28

KARAR
-----
Sahip talimati: siradaki kitaplari ayni sekilde bastan sona isle. Emsal
0072 / 0075. Bu migration SILMEZ; yalniz is_active=FALSE yapar ve downgrade
ile tam geri alinir.

NEDEN (mukerrer olcumu, aktif_2020_ayt_kimya_mukerrer_adaylari.json)
------------------------------------------------------------------
Ayni kitabin eski aktarimi aktif duruyor:
    Aktif Ogrenme Ayt Kimya 2019 2020: 490 satir, 490 aktif, 170 modern karsilik
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

revision: str = "0103_akt20ay_eski_hat_pasif"
down_revision: Union[str, None] = "0102_akt20ay_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "akt20ay_eski_hat_gunlugu_0103"
KAYNAK = "2019-2020 Aktif AYT Kimya"
ITHAL_ARACI = "scripts/kitap/kitap_hat/ithal.py"
ESKI_KAYNAKLAR: tuple[str, ...] = ("Aktif Ogrenme Ayt Kimya 2019 2020",)

# (eski satir id, modern kirpim adi -- AKT20AY- oneksiz, modern id); kaynak:
# mukerrer_adaylari.json eski_hat, modern_karsilik=true. Yorum: eski basili sayfa.
ESKI_MODERN: tuple[tuple[str, str, str], ...] = (
    (
        "177d251f-05d3-54c3-92e8-89096c935f4b",
        "T001_08",
        "5373e2ee-2e3b-5c8d-91f4-9d3be6c13e44",
    ),  # s23
    (
        "393dfcfe-7b3f-5ddd-a717-5c78b1d07b2c",
        "T001_02",
        "c9176621-5092-51bc-a7ba-7e7daaa3c009",
    ),  # s23
    (
        "7305c758-2e06-5fe0-af6d-6a426cfd650c",
        "T001_05",
        "7f3dbcfc-53cb-5fa1-a616-0ee06d0b601f",
    ),  # s23
    (
        "b5b325c2-b8e3-57d8-8e5c-2cc8e196607e",
        "T001_06",
        "d4027029-a3a4-5369-ac39-9af663d2d744",
    ),  # s23
    (
        "dcda45a8-05f1-5a5e-894d-19c5fff06c2b",
        "T001_01",
        "19c1cd5f-7b25-52cf-ba24-6b32dae36df3",
    ),  # s23
    (
        "03db9fcd-230c-5fa2-b7d5-bd77333583c0",
        "T001_11",
        "d6a2073a-f9b5-55df-8636-0f747e9dd89c",
    ),  # s24
    (
        "0f530f20-cf32-587f-8283-e1bc834d6bb5",
        "T001_14",
        "4bb1bb98-3295-5827-9b77-bc32aa9472cd",
    ),  # s24
    (
        "37b49217-d408-5cd1-b5cd-8ab00e43f55b",
        "T001_16",
        "e10d86d5-745f-5a44-9815-d6c724f853c5",
    ),  # s24
    (
        "a16eaf15-9edb-54b6-a91a-8072bf930cf5",
        "T001_15",
        "61f2116b-d947-538a-a989-94020f76e01c",
    ),  # s24
    (
        "cba548a9-2e3c-5981-b852-25f0b1186450",
        "T001_12",
        "7958abf4-957c-5732-bb23-fc3edebcdbbb",
    ),  # s24
    (
        "5ca9d1bc-1577-5501-821d-c87e2b3dd07a",
        "T002_08",
        "d5932ea4-3f5c-53c7-a53d-e179847824d6",
    ),  # s25
    (
        "705db3a8-6f7a-5efd-b953-0b58ec067d30",
        "T002_04",
        "81326b3a-6eea-54ec-9eb4-c66b52d6f2c1",
    ),  # s25
    (
        "8a0a7d44-f4f1-5dd3-929a-7f3d5ecce943",
        "T002_03",
        "6d0e3878-0574-519a-a33f-fa9ee6b39b53",
    ),  # s25
    (
        "cc072734-5d86-5f7e-80fe-59584c367b0d",
        "T002_05",
        "90373411-5adc-5d94-abad-8e7bef5f0481",
    ),  # s25
    (
        "e4eb3742-8130-5067-8351-2b1029c24846",
        "T002_06",
        "269a0651-e5fd-50ea-ad84-4e2ec4fd2613",
    ),  # s25
    (
        "0545bea9-0318-53c4-9e1f-1e9432b1de1b",
        "T002_12",
        "6bef347f-8e89-5c2f-8fcf-d87da49f6142",
    ),  # s26
    (
        "5f2b8ae5-fc46-5828-8831-a3280144322a",
        "T002_10",
        "7e3bf818-1aaa-5280-a62b-df6bf62c09a1",
    ),  # s26
    (
        "ab99f2f9-1cfe-50a8-aeb3-eabc09feedf3",
        "T002_11",
        "cd4bc631-72d2-5d69-a07d-fc69d8bf7b04",
    ),  # s26
    (
        "f780f502-8226-5c77-a28e-34af4708403c",
        "T002_13",
        "96742eff-3cc4-5e83-915f-30ead5049573",
    ),  # s26
    (
        "f999b3f1-0dff-5448-83db-d92abbb500f4",
        "T002_14",
        "508265ad-3a4c-5462-a3cb-9b35f695dccc",
    ),  # s26
    (
        "2aa75a3f-27e2-552b-9df3-cb53396d215b",
        "T003_07",
        "d0f9665b-5611-526c-9956-52de1490f5b0",
    ),  # s27
    (
        "cd518375-7e64-5762-86ae-a13f35b27b3e",
        "T003_03",
        "7f8d2744-b1d0-5b99-b35b-6c349e6e68e5",
    ),  # s27
    (
        "0ebb1db9-2036-56a2-8a1f-3a7a6ac2b7bc",
        "T003_09",
        "e269628b-af6e-5fcf-9e7a-6039be7fe6a7",
    ),  # s28
    (
        "9a139144-37a1-5c8f-be44-f2e7383ab0d6",
        "T003_11",
        "bd53e0d9-4596-59db-a19c-ae8728c3e41f",
    ),  # s28
    (
        "ffd29a20-cc9b-53fa-adb5-05c7e138c2aa",
        "T003_10",
        "5114a66a-9b57-54a4-9684-253ae14268cd",
    ),  # s28
    (
        "248aa3f2-edd1-5404-95a4-c4aa4ea18016",
        "T004_02",
        "aab7a409-804d-54b5-9dca-a76523e8e95c",
    ),  # s29
    (
        "5f2148d5-bc3b-5e1a-abc6-ddebbbd7b615",
        "T004_07",
        "86f31a89-0005-572d-8fd4-9cab7628681a",
    ),  # s29
    (
        "78f29cbb-8ea7-5ba3-bfb5-4f25f82266fc",
        "T004_04",
        "980bf793-16d7-5956-9b68-df45e16b99d6",
    ),  # s29
    (
        "8579d979-e8dc-5f91-a4c5-06ea8e05746e",
        "T004_06",
        "039f2274-0cfd-592a-938d-df9f133bf199",
    ),  # s29
    (
        "cf0caf16-f971-5d64-bf88-e645867ce316",
        "T004_09",
        "718334c9-8cb5-5279-8553-3b3bf2526295",
    ),  # s29
    (
        "61989968-15ab-56ce-9146-5d79e9765c35",
        "T004_16",
        "fe7593fb-c16b-52d6-aefe-af187aa79f86",
    ),  # s30
    (
        "664e7f40-8d02-55af-95c1-b85946b03729",
        "T004_17",
        "d060db5e-5fd5-5fcd-baeb-9c2c93b77016",
    ),  # s30
    (
        "be41ae2e-bcea-55fa-ad70-be7a9d6f662d",
        "T004_14",
        "05450443-56b5-5d68-8454-ec1722a5a569",
    ),  # s30
    (
        "fe0486b1-074a-5a4e-9ab0-19ff21606068",
        "T004_12",
        "57b4bdea-b3ea-557b-a40f-1dffd8da3c79",
    ),  # s30
    (
        "2b0e6948-1617-5221-a669-664dee041e57",
        "T006_03",
        "d263b5ae-a38c-5f64-9afd-5d5561031bcc",
    ),  # s49
    (
        "ba6d93a6-ee18-506f-a901-57f3a063801d",
        "T006_06",
        "166daa4f-4cf6-5a16-b7f1-7cbcec02493e",
    ),  # s49
    (
        "3a636a29-d6d5-5409-a4b8-fd238554df5d",
        "T006_10",
        "b6037e33-2ec1-5c3b-a904-8e2dfc2accbd",
    ),  # s50
    (
        "4b67d9d2-0311-51e2-9adb-adc0400181e7",
        "T006_13",
        "1ff8a00b-b658-5f86-bdc6-00860a4bd97e",
    ),  # s50
    (
        "6d22f109-7654-5cbb-bf2f-255ddab179d0",
        "T006_12",
        "521dc5c5-f0f2-56af-914c-8e1a1a749736",
    ),  # s50
    (
        "7c38d265-fded-58dc-bbe3-c2b15df1086b",
        "T006_09",
        "e098293b-bf16-54b3-a91f-db4823068aec",
    ),  # s50
    (
        "a5b45138-d98c-5754-8b9e-c93f660352a3",
        "T006_11",
        "57752374-5c88-58c3-887f-8b7feb616077",
    ),  # s50
    (
        "acdd567f-f5fd-56b7-9078-fb248d1a06e7",
        "T006_07",
        "f895fa7b-6624-5efa-8eff-2726948e3b6d",
    ),  # s50
    (
        "d05549fb-7ed4-5932-a60a-c73fb37863a8",
        "T006_15",
        "848bd7fb-a357-526f-a601-0fb8dfa48e5b",
    ),  # s50
    (
        "dbafb751-4d94-5438-9a67-e20655ae94ba",
        "T006_14",
        "8d669172-aaee-58f2-a7ec-4af301d8ee10",
    ),  # s50
    (
        "991d768c-37c5-5d41-b7f2-3315b6f2368f",
        "T008_03",
        "33cc37a6-9782-5814-859d-00f7fb13eab1",
    ),  # s53
    (
        "67626ece-70dc-5c9a-a8ab-df8b92d1cbc0",
        "T008_10",
        "02ed4179-8265-5f12-a602-ea34ea0d7db4",
    ),  # s54
    (
        "43a84ba1-7fcd-59c5-b930-e01cbc1be226",
        "T009_07",
        "4854a682-4e29-59f5-a6b7-081e7b7060a2",
    ),  # s55
    (
        "9fe9e9f4-628c-5143-8db6-7f9df8b321b1",
        "T009_04",
        "be1f2ba5-f8a3-550e-a722-cb3833292c7b",
    ),  # s55
    (
        "be002757-6748-5722-b6f9-7e7faa26327a",
        "T009_02",
        "7d38c98f-adad-56ea-8230-0dd72142c67f",
    ),  # s55
    (
        "715228be-8587-5af2-a621-b710bab8d660",
        "T009_09",
        "82f78dd3-9790-5479-83ef-ad743feeef3e",
    ),  # s56
    (
        "eae722ed-48f1-5e57-acc4-d885e344b375",
        "T009_10",
        "2a7ba800-8f1d-5d5b-ba7a-85f9c753477c",
    ),  # s56
    (
        "b81d249b-3a0b-5071-b0d2-ca25d0356fc9",
        "T010_04",
        "aae5e210-0a2d-5178-8c5f-0594b6a7bd07",
    ),  # s77
    (
        "b0f08611-0c2b-5b6a-981e-2d5ca73d4238",
        "T010_09",
        "65fefa73-b88f-5683-a72b-a51aa6bad780",
    ),  # s78
    (
        "b4439720-027c-5684-b43a-dbe7837d29f9",
        "T011_04",
        "d3f52e74-ca56-5907-a44c-671afd461825",
    ),  # s79
    (
        "ebb43030-0d64-5aa2-8075-34d3293b43d0",
        "T011_01",
        "9a530f8a-9d25-562e-9540-1f096a1f78a2",
    ),  # s79
    (
        "f5076e97-169d-58dc-8389-ff2b3308aab2",
        "T011_10",
        "5affd9a8-6846-542b-877a-f6955bd61091",
    ),  # s80
    (
        "f7b18a99-fe41-565b-ac00-377be5c3c619",
        "T011_08",
        "3a00cfb1-7976-56f2-b636-220eaa288eee",
    ),  # s80
    (
        "7c5f0125-22f8-5599-8b1c-eace57d3f0f7",
        "T012_08",
        "d3515c90-1f0b-5801-acc0-405d5295d9e7",
    ),  # s81
    (
        "662b7d66-5a30-557e-aeff-7d7bc214e1f0",
        "T013_03",
        "9c0aca91-c945-5b97-8179-8c0be5285739",
    ),  # s83
    (
        "b3c8c544-7692-5ea5-aad1-8531d28ebae7",
        "T014_10",
        "3fd037aa-9cfe-5dde-8199-e23b9b17f6e1",
    ),  # s86
    (
        "8b6f7e5e-1d9b-5991-9e31-787b8768e39b",
        "T015_16",
        "cf4362fc-ee9a-5f36-9be9-ab1b8a5bee6f",
    ),  # s108
    (
        "fff55b9c-6851-544d-9386-a3cdd0a31efa",
        "T015_10",
        "6101ce50-3a04-541e-a568-9445150f4b1b",
    ),  # s108
    (
        "77752516-9b52-5a5b-bb59-17cdf172c255",
        "T016_12",
        "f32adcf0-f3f5-536d-b590-7e09b5a955d4",
    ),  # s110
    (
        "7d3407ee-487e-5f43-8830-89095ab75301",
        "T016_08",
        "1ef0324c-4f31-58e1-a5db-04fe71385ab2",
    ),  # s110
    (
        "0e96023a-77cc-5298-96e5-7ce6846f0ccb",
        "T017_04",
        "6169da94-c628-5ef4-8045-df58b63e1fd5",
    ),  # s111
    (
        "7f0202e1-4e2d-5f81-82c3-e9323c8ba6de",
        "T018_03",
        "9852c8a1-ac00-58f9-893f-c052cc63a08e",
    ),  # s113
    (
        "d6da9ace-309d-5650-a94d-f4eee56f4ebf",
        "T018_11",
        "eb268d7b-0796-5020-86e2-a0ac1e29bb99",
    ),  # s114
    (
        "540265bd-94a8-5a5e-851d-7a3c54d1b58f",
        "T019_02",
        "ff900630-12af-51c6-a2cb-0bfbd296d233",
    ),  # s115
    (
        "528cd375-9ff7-5108-a43f-f430fac8e25e",
        "T025_09",
        "814226de-c956-5985-9704-4805d31c6e7e",
    ),  # s162
    (
        "2ba81aa8-4bd6-5e25-bcb2-4466402ff149",
        "T026_11",
        "b8fff5d3-7b14-5558-81d7-3a720c9de9de",
    ),  # s164
    (
        "647c0e84-29b4-517c-869a-105232ce7a19",
        "T027_15",
        "2fbe461c-31a0-598b-b862-be8a90edd10a",
    ),  # s166
    (
        "c07bd59d-10a3-5588-991e-f7b55ae86a22",
        "T028_06",
        "b8e86e59-84f6-51c7-b981-cf3135e0c6f7",
    ),  # s167
    (
        "5a20d762-447e-50d7-91b0-6693f17f2d41",
        "T033_04",
        "209d8f74-61a5-59b3-97df-aa08c398b3f6",
    ),  # s203
    (
        "16ebfcc1-0dc7-5160-bc12-7d088b3441b9",
        "T036_06",
        "2fbb1205-8e76-5238-a40c-61a83ea1e2cf",
    ),  # s231
    (
        "c23009c8-18ca-52fd-9d0b-c99e580b680d",
        "T036_10",
        "6bfcee17-7115-57a6-baa8-ce782bb8969a",
    ),  # s232
    (
        "ffa0ed53-9606-5e95-84ce-3f699f6503e9",
        "T036_10",
        "6bfcee17-7115-57a6-baa8-ce782bb8969a",
    ),  # s232
    (
        "4af495e3-3624-5965-8ae8-f29422f9d5af",
        "T038_01",
        "f6d44657-51ac-51f1-b01e-7ad3938b3805",
    ),  # s235
    (
        "6106f7fe-d61c-58e9-aa8c-94ad0c29a596",
        "T038_06",
        "e0373d4f-90fa-5f1e-84f8-b4a196b38019",
    ),  # s235
    (
        "8b1d4d41-59fb-5e4e-9346-d60b00dd6a0c",
        "T038_04",
        "ed7fa591-a4be-5455-8915-fab479e0c6ca",
    ),  # s235
    (
        "a50f7dfb-dfcc-54ff-81fe-4f6d3bed6307",
        "T038_07",
        "5d1c434b-4f99-5c13-b35c-ae9d23248511",
    ),  # s236
    (
        "ec2abe50-ef60-5549-ba8a-7fa6351a26aa",
        "T038_09",
        "5d072129-70dd-5e8e-bb55-d81f18c1ed91",
    ),  # s236
    (
        "db0414ad-0929-50b1-ae2c-b156e60c8c5d",
        "T039_05",
        "22db7dbc-e329-56d7-bba5-e1b2b7c549d1",
    ),  # s237
    (
        "93ca28d8-5d80-5f09-b074-dc510834ffbc",
        "T040_05",
        "5c0f73a4-1dc4-559e-806b-6c8c205832e9",
    ),  # s239
    (
        "4268f705-cac8-5bd8-a1b6-7cfc3c4ac50d",
        "T040_11",
        "ad3be980-5b78-5cea-85b3-7d95f28121ee",
    ),  # s240
    (
        "cad6c5ff-c6fa-5aa2-a906-0d861645ffb3",
        "T040_10",
        "66e91ce4-2b89-5b9c-af38-f0e357b78739",
    ),  # s240
    (
        "f00f973f-f374-5f87-bf0d-34d66c7f89fb",
        "T040_07",
        "47419a79-d980-5a96-ac2b-de6cc425aac0",
    ),  # s240
    (
        "08d769c8-3ed1-59dd-996e-80f0787f9ab6",
        "T041_04",
        "91e44cb5-d7e8-52a6-893a-73ae6e3bbcc2",
    ),  # s241
    (
        "499d6246-d7f0-59c1-bff8-78d3e2bcca75",
        "T041_06",
        "81c47b2d-624d-5eec-8b61-fe267294377a",
    ),  # s241
    (
        "b7909ec4-17dc-53a8-925b-196d629ae54c",
        "T041_05",
        "78ad4f59-d494-5af5-9004-951013aa7f70",
    ),  # s241
    (
        "1fd38bec-5735-51d0-86c3-a047abc18b2d",
        "T041_12",
        "7f24748a-01c0-5606-bade-3e8521dbb980",
    ),  # s242
    (
        "d54bdbc2-2ac4-5a4a-af45-828783ba9288",
        "T041_14",
        "a06dd41c-6297-5e6e-884b-d413d6941367",
    ),  # s242
    (
        "42d7fc7e-b5f0-53c8-b73e-8f3f258b005a",
        "T043_01",
        "71fb9227-00a5-5fe8-8641-51f7df086a84",
    ),  # s277
    (
        "a571b477-ead8-5756-913f-00a4e594855c",
        "T043_07",
        "d9041c00-e4e9-5828-9b87-c7362370b292",
    ),  # s277
    (
        "ac3f5ebc-e332-5610-b8c0-9bc9b37066d4",
        "T043_02",
        "7b1fca8b-16bb-556c-8fc7-d968a46aadae",
    ),  # s277
    (
        "af40c1a6-9492-5c80-b698-ac3483865fb1",
        "T043_03",
        "7f0f987d-5805-5f6e-96f9-5f3a16118cc4",
    ),  # s277
    (
        "b8293db7-6393-5023-ac4b-0ce081fd7237",
        "T043_04",
        "a48be4ce-c192-5da5-bd1d-ab6904645658",
    ),  # s277
    (
        "3e7c5d8f-ed76-5973-89b5-9ba680f388ed",
        "T043_15",
        "002a7fa1-6840-5e29-9a8d-fbeac7d8cd88",
    ),  # s278
    (
        "b4a0b16b-9419-564b-90b7-594031931eb4",
        "T043_14",
        "6993f816-8dde-54ca-b29a-4fe99b508c72",
    ),  # s278
    (
        "eab8de72-712b-55e7-81a3-fea3eed881a8",
        "T043_10",
        "c552c18a-e57f-51c6-8f2e-18497a8ec52e",
    ),  # s278
    (
        "e46a08e0-0001-5538-b234-5e7a673a1164",
        "T044_09",
        "53c5b4db-dcd9-5c40-83d0-2f035dd5733c",
    ),  # s280
    (
        "e7068bee-553b-5491-89f4-132a525c7c7f",
        "T045_01",
        "ada036ba-0b80-5d0e-a2f1-5e4b764ea6ba",
    ),  # s281
    (
        "35581545-9b44-54d7-98e4-35c41e82b8a1",
        "T046_01",
        "2c346905-fa70-50d6-b50b-b6fc2a32b678",
    ),  # s283
    (
        "00b2d325-3839-5a85-97e6-87260b5d82ce",
        "T047_05",
        "db7ae5a5-c537-5e83-b957-616c405a1dda",
    ),  # s286
    (
        "14cf9a0a-68bd-51fe-b911-886b74ee7479",
        "T048_02",
        "29786260-3fd8-5985-976f-1ed2fea4cfe8",
    ),  # s287
    (
        "f6d582d6-9bd1-5a79-b539-e61d2f48a94b",
        "T048_01",
        "f6ac6534-16c1-53e7-80aa-e4ddd9aa3994",
    ),  # s287
    (
        "3c83e140-bfe1-587e-b67b-b1720010e866",
        "T050_01",
        "1be8673d-8b5f-5e08-9cf8-958911b9a29a",
    ),  # s291
    (
        "03ae44bc-fc4e-5f4d-8d42-89959355f99c",
        "T050_12",
        "134466f4-cc01-5425-93fa-934b8592cb3e",
    ),  # s292
    (
        "0b109095-4dc1-5d74-8055-c60582c789d6",
        "T050_10",
        "c7b9813a-f55e-5918-9a74-5470536fb2f9",
    ),  # s292
    (
        "0f6168c7-b9c5-5732-b68f-d9b66e456eac",
        "T050_11",
        "0502defd-ed4d-582f-98d4-bbc9399ea0b0",
    ),  # s292
    (
        "1d54e839-0253-5b82-a14e-133d4ff38826",
        "T051_09",
        "2dbc6644-a31c-5112-b29e-f6a17a0187e7",
    ),  # s293
    (
        "3eac76bf-d91c-573a-b0dd-ff31658f0065",
        "T051_05",
        "6b07c58f-dbf0-5347-ae43-bd203b54f2a9",
    ),  # s293
    (
        "421811ea-99fe-5c46-8560-f5661d79388b",
        "T051_04",
        "12f626af-723e-5fcb-8130-e4a9694bfb26",
    ),  # s293
    (
        "77d4757a-1eb6-574a-8107-673da96336ff",
        "T051_08",
        "fbbd9d8b-310a-5d64-8139-5e3f98ee0ac8",
    ),  # s293
    (
        "82ad3f46-a9e8-5cd9-b92e-fcf2ebd6fe8c",
        "T051_06",
        "ccb23c1d-2e27-5146-a237-af81ed9bfcf7",
    ),  # s293
    (
        "8dab8e1f-3a7d-5be6-8061-d26d54588a60",
        "T051_03",
        "174b19df-4a8c-5239-bcef-52a26721785e",
    ),  # s293
    (
        "ee3fb195-dca8-558d-926d-6ba317b08202",
        "T051_07",
        "e3c1a3cc-aa12-5e1e-8730-316e2fd77078",
    ),  # s293
    (
        "26ffa2b2-31c2-56f8-9d0c-08e89ca8b8eb",
        "T051_14",
        "27981127-bf1d-5bb5-854f-e51f7544a07c",
    ),  # s294
    (
        "3cb4fcea-f92b-53f8-9103-ee46928c8769",
        "T051_13",
        "e22d6809-7d78-5c84-b2bd-c5a3054c48a6",
    ),  # s294
    (
        "69dccd87-0c73-54c1-8f19-5c511858f3ea",
        "T051_12",
        "b4ddd856-f59e-5eef-8700-7c7b17756ecd",
    ),  # s294
    (
        "80df38d7-99fd-5003-9ac2-65aeedda0463",
        "T051_11",
        "b8198bd9-3711-59e6-8824-831db82ff3a4",
    ),  # s294
    (
        "b1e1757a-a82a-5ae1-944d-c7f21db684c7",
        "T053_05",
        "1ecc99dc-29b5-5d81-b3ac-53dcffe0b9c0",
    ),  # s313
    (
        "2247d574-2527-5a85-990f-359f8fb54ad6",
        "T053_08",
        "7e888797-feec-5dfe-9b36-66b2a4b56085",
    ),  # s314
    (
        "f2a8d35a-81de-5f41-8640-cdf7738720c4",
        "T053_09",
        "87b0bbbd-91d5-554c-8830-dcad0091afb9",
    ),  # s314
    (
        "1f1bc423-0f1d-58f2-8dcf-185f2749c86c",
        "T054_09",
        "422b2059-da56-5d78-a323-991cbfcc0e24",
    ),  # s316
    (
        "990a224c-8174-5bd2-b82e-a0ca48dcff4b",
        "T055_01",
        "9b3949df-d212-5690-87ec-dea773c76e29",
    ),  # s317
    (
        "1a641c02-d6fb-5b43-98ff-8fcba5001cee",
        "T055_11",
        "2d424f3c-0610-599f-8c4a-af17f9627a74",
    ),  # s318
    (
        "83efe97f-865b-513f-8ab1-ec622e2fbd11",
        "T055_10",
        "9f7722fe-0ef0-5ba9-91c0-d2ee63cffd92",
    ),  # s318
    (
        "8513078e-4f5b-5288-86df-25ca8f6f3ab3",
        "T055_13",
        "864d9cf2-9bf9-5cb3-bbad-a10da2ea4e75",
    ),  # s318
    (
        "ff1dba5d-be1e-5c16-9b82-710126caf390",
        "T055_08",
        "3ea4f6f6-b9e3-5978-8700-327fc91cec9f",
    ),  # s318
    (
        "5b215d43-a6f8-5a41-82e5-5a24241643f7",
        "T056_01",
        "bd4c04cc-ef31-57d4-88dc-c0ff451ffecc",
    ),  # s355
    (
        "8d251485-5924-5f0d-a8b1-20d1c4abd0ec",
        "T056_03",
        "546da993-a00e-5c3c-8464-d09f8d494342",
    ),  # s355
    (
        "bcd4790a-0ac3-5371-9a6c-331d0f811fbb",
        "T056_06",
        "f67e9c50-8020-5878-8ddb-dc47c1320e73",
    ),  # s355
    (
        "d50c7edd-2d74-5e88-93ad-96f6de8f541c",
        "T056_05",
        "56028f69-1e21-5035-80b5-d75576f2fb3b",
    ),  # s355
    (
        "1c84063a-1e22-5fec-a720-a03e7329b8b6",
        "T056_15",
        "4ad51d4c-8f22-556b-8e9e-de0a8121464e",
    ),  # s356
    (
        "3a1409f7-47fb-55f4-a505-a81735aa6932",
        "T056_16",
        "17eb55c7-d923-55a1-a5e3-721909650301",
    ),  # s356
    (
        "912f2de1-7ce0-5013-ba5c-644d1451225a",
        "T056_10",
        "e77ba844-3266-5541-bb4a-faa3c4326782",
    ),  # s356
    (
        "c2dfa226-8eaf-5b62-9160-ff6abbdeca37",
        "T056_14",
        "d5df13df-ff53-54fc-931a-84f7ce8c66f1",
    ),  # s356
    (
        "38ee4dfc-987e-5fca-a8d9-610a519b3d35",
        "T057_10",
        "b8c05ae4-926f-5bc9-a539-4fd33c62cbe3",
    ),  # s358
    (
        "567c40ff-9ea7-57ab-8078-2a3a9bafdb3b",
        "T057_13",
        "2ab34f97-360f-5616-b66e-2c5214546d99",
    ),  # s358
    (
        "fe11ae48-d802-5676-8621-db82f433862e",
        "T058_01",
        "0c265569-72bc-500d-b723-39aa82210520",
    ),  # s359
    (
        "8bc2228a-292f-575f-971c-ccd0f9c47bed",
        "T059_06",
        "e7258555-4012-5045-8b98-a1e0db910301",
    ),  # s361
    (
        "e59f2f9a-1ac0-5ed4-9c17-49512692667e",
        "T059_04",
        "069a3238-1c90-5a6f-a2ae-1223227cf723",
    ),  # s361
    (
        "a3f029c4-b979-5c5f-954d-27264447933b",
        "T059_13",
        "7c2daedb-706e-562a-90e2-4245c0ba899d",
    ),  # s362
    (
        "b88dfa6b-788c-5499-9e63-092f81e018ae",
        "T059_11",
        "360dfd56-34ec-5f49-b72a-7222013d53ab",
    ),  # s362
    (
        "ea6bde71-6586-5133-b7ff-e76c940e449d",
        "T059_14",
        "e7587f05-f85b-51ce-93a7-75173dd4ba29",
    ),  # s362
    (
        "b1414c11-301a-5ce4-bfcd-2e7a0f3f4a74",
        "T060_03",
        "914e8f52-c03e-56a8-9d4f-146b4ada548c",
    ),  # s363
    (
        "f24a7b51-1862-598b-9a0f-d4f38246e9d4",
        "T061_02",
        "6a157871-9e9f-5ab1-84ad-07601ceba9ce",
    ),  # s365
    (
        "adc10e52-6c52-5e96-823e-215ccd4f37f7",
        "T061_13",
        "b765ce2c-e778-5aa8-8339-34c30fdf7c84",
    ),  # s366
    (
        "9c090113-adf8-5cd8-9cbc-4f8741ebf740",
        "T062_05",
        "9d560867-eaea-5edf-83ea-83660fa3591f",
    ),  # s367
    (
        "c9ae1f09-8aa6-5424-ad35-46091dd0f099",
        "T062_06",
        "41b30358-161c-58dd-9d5b-1de4d1ff4739",
    ),  # s368
    (
        "0f0a2809-caee-553b-ace5-7792d4ac5e52",
        "T063_02",
        "4f51003f-fc9e-5b6c-8f62-7c29b0d3c0c9",
    ),  # s369
    (
        "6d9cd006-e34f-50c7-bca7-cd6008f8db5e",
        "T063_09",
        "b8ad19cc-fbab-5f00-88af-2d0d48fbbeff",
    ),  # s370
    (
        "e0716577-4c31-5747-bede-f58e414c6ae9",
        "T063_08",
        "5c55fcf3-8ae4-5261-8f3c-08ec4bb50a44",
    ),  # s370
    (
        "a36051e0-8d14-502d-908b-cc8e4cc1d885",
        "T064_04",
        "fc2adbe0-2bc2-53d5-b2c2-05e1502c4ae9",
    ),  # s371
    (
        "ad9053b5-c795-55b8-9099-b7e6416f7716",
        "T064_02",
        "7c9e2827-4eb8-567e-884b-45b7a9b36c46",
    ),  # s371
    (
        "de75c0aa-d09f-5b28-b0fc-bd01c5f0a77e",
        "T064_03",
        "47053049-24b8-53db-90d1-8f5f1f4d4f00",
    ),  # s371
    (
        "136e923b-ef54-5cdf-b54f-67477c60c6c5",
        "T065_02",
        "4063649f-0fe4-5ce2-8ee9-db0f129c3c1d",
    ),  # s373
    (
        "224f748a-4b05-5a71-b75a-16e835fc2f61",
        "T065_04",
        "6895a16b-dff0-5893-918e-bf89f5a3ebe3",
    ),  # s373
    (
        "248e459f-42dc-5fa4-9397-c9ea344f7d48",
        "T065_06",
        "52368fe8-45da-589d-b4fe-c07c0c440c78",
    ),  # s373
    (
        "9eebea02-2750-5c27-840a-fbb921bafb8b",
        "T067_02",
        "850eb820-b979-5bd6-90ae-8d3b1d0e530f",
    ),  # s401
    (
        "b71d9aaa-b88a-51f3-8d00-39e0dba8d768",
        "T068_06",
        "1d5c3c2e-114d-599a-a447-78e16b04b451",
    ),  # s403
    (
        "fccf981c-e620-50f7-a6e0-7dc3cfa617ac",
        "T068_05",
        "6f4257a5-7c6e-5627-b7ec-3536c38572c5",
    ),  # s403
    (
        "53bcd3fd-ea56-5b5b-a1a8-0c293b684a77",
        "T068_14",
        "72060386-291b-581d-a1cf-a98e49b06df9",
    ),  # s404
    (
        "3c9d784a-aa70-57a0-82ad-5cf262550d1d",
        "T069_04",
        "edfc16aa-87e4-5760-b317-748473da54a1",
    ),  # s405
    (
        "7469597c-3060-5c88-a34d-c3da73eb635b",
        "T069_05",
        "80838cfb-d6e6-57fb-ab1e-800af33480e2",
    ),  # s405
    (
        "c04da873-0162-55c3-944d-b4787f08df48",
        "T069_11",
        "9e71eaf4-3501-5e51-bc5a-e05bfa17911e",
    ),  # s406
    (
        "2466d5f3-9725-5ba0-934a-574604a49c89",
        "T070_04",
        "a2e09cd0-04e6-5939-8554-40a7a6c2ab02",
    ),  # s413
    (
        "fad6993f-877b-50ac-874d-f995e05f022a",
        "T070_10",
        "ba4be289-f08f-5deb-a982-b082a08fc535",
    ),  # s414
    (
        "2317a70f-d511-5487-880e-67390853aaa2",
        "T071_02",
        "71c906b1-633e-567e-ab3f-e8e5cf030337",
    ),  # s415
    (
        "5314cd50-92e3-5733-8856-5fb06139fde6",
        "T071_06",
        "7a050323-3d57-53a6-a4c2-e8500eb092f8",
    ),  # s415
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
        _log.info("[0103] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0103] mv_safe_for_beta yenilendi")


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
        _log.info("[0103] soru tablolari yok (taze DB?) -- atlandi")
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
    _log.info("[0103] eski hat: %s aday, %s satir pasife alindi", len(idler), len(eski))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0103] %s yok -- downgrade atlandi", GUNLUK)
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
    _log.info("[0103] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
