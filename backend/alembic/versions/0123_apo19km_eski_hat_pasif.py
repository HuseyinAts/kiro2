"""2019-2020 Apotemi TYT-AYT Kimya Soru Bankasi: modern karsiligi olan eski hat satirlari pasif

Revision ID: 0123_apo19km_eski_hat_pasif
Revises: 0122_apo19km_agac
Create Date: 2026-09-28

KARAR
-----
Sahip talimati: siradaki kitaplari ayni sekilde bastan sona isle. Emsal
0072 / 0075. Bu migration SILMEZ; yalniz is_active=FALSE yapar ve downgrade
ile tam geri alinir.

NEDEN (mukerrer olcumu, apotemi_2019_tyt_ayt_kimya_mukerrer_adaylari.json)
------------------------------------------------------------------
Ayni kitabin eski aktarimi aktif duruyor:
    Apotemi Tyt Ayt Kimya 2019-2020: 345 satir, 345 aktif, 236 modern karsilik
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

revision: str = "0123_apo19km_eski_hat_pasif"
down_revision: Union[str, None] = "0122_apo19km_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "apo19km_eski_hat_gunlugu_0123"
KAYNAK = "2019-2020 Apotemi TYT-AYT Kimya Soru Bankasi"
ITHAL_ARACI = "scripts/kitap/kitap_hat/ithal.py"
ESKI_KAYNAKLAR: tuple[str, ...] = ("Apotemi Tyt Ayt Kimya 2019-2020",)

# (eski satir id, modern kirpim adi -- APO19KM- oneksiz, modern id); kaynak:
# mukerrer_adaylari.json eski_hat, modern_karsilik=true. Yorum: eski basili sayfa.
ESKI_MODERN: tuple[tuple[str, str, str], ...] = (
    (
        "26a81fc6-8416-507a-876d-d158582eac59",
        "T001_03",
        "79e10ba5-7452-5d9b-b092-fb418a75c8ea",
    ),  # s12
    (
        "8f9a5af3-2232-5b30-88f3-5907bffe4626",
        "T001_09",
        "827e584b-981a-59f7-a19b-6e076a0121fd",
    ),  # s13
    (
        "3a9546b2-3530-5ded-b534-747523b3faa2",
        "T003_08",
        "279ba7f0-0aaf-5466-880f-eb1208cb9a9a",
    ),  # s17
    (
        "670e1170-f953-5502-9a5b-347791a39b2b",
        "T004_04",
        "8013a57d-1937-5fd6-a0ad-61cda0b9056f",
    ),  # s18
    (
        "20c0b763-9000-55a1-920a-a7881efe8ec2",
        "T004_10",
        "e8b00104-c522-5e3c-a211-05c83927abff",
    ),  # s19
    (
        "02356d6f-1d98-5586-ba14-89ca3e24df64",
        "T007_10",
        "7a96ce61-0657-5469-a965-960b6cd3e881",
    ),  # s25
    (
        "0295ef6f-1870-503c-ab97-6903c172352c",
        "T007_07",
        "8930b5d7-7a4a-51e8-97d2-ac0110fbdcac",
    ),  # s25
    (
        "1d21657f-6ac0-5417-b9c4-6fb6afae22d1",
        "T007_07",
        "8930b5d7-7a4a-51e8-97d2-ac0110fbdcac",
    ),  # s25
    (
        "748872fe-9a20-5a38-bba1-003624d4eb44",
        "T008_10",
        "65b0f97a-63a4-551e-9a0c-c999389b4dc3",
    ),  # s27
    (
        "2c2dad81-54bb-5ed4-8f1a-d05cf4cbc808",
        "T009_05",
        "16d299a6-5e08-5103-b40e-4d4e28e465ea",
    ),  # s29
    (
        "56064c0d-3b0e-5f5c-80af-acbdd4a4ad1e",
        "T009_07",
        "8e934bbf-6a03-55e3-b164-bad735c4ec0d",
    ),  # s29
    (
        "cfc9cb68-1154-5742-ae1c-986725c94de8",
        "T009_09",
        "03a7bbad-d711-5c30-af3c-a924a9ecf7ca",
    ),  # s29
    (
        "0c5da01d-2d2c-5347-9d0f-e96330e29e24",
        "T011_10",
        "f20a50b1-35ae-5793-993a-11e3aa275b03",
    ),  # s33
    (
        "5825703c-2b47-53b1-8ef4-60c2d3b9590f",
        "T011_09",
        "872c4dfa-9380-5792-9c69-774b36cddd0e",
    ),  # s33
    (
        "0ca6adc0-aa0b-520b-b77e-16fd6c733992",
        "T012_09",
        "de4d25bb-f39b-58ce-9422-d63eb63da3eb",
    ),  # s35
    (
        "4ddb7267-5416-5a0d-ac9c-2cd97e571d0d",
        "T012_08",
        "c4eeedc5-1910-5a85-b682-c511e076d521",
    ),  # s35
    (
        "78feae38-e071-57ed-b654-cba2db7adb17",
        "T012_06",
        "9453a49e-8915-50c3-a307-36c01fcb9efb",
    ),  # s35
    (
        "9bb2bc36-6bd2-5272-a6f5-c0ca5ff1202e",
        "T012_10",
        "7c5b76d3-70f6-5802-bcf4-60091962db13",
    ),  # s35
    (
        "8ced802b-b80d-56f1-9945-75719ad09759",
        "T013_08",
        "10b400b8-aa87-52af-bb8c-69e70c107570",
    ),  # s37
    (
        "9ad21ed8-82ad-5226-b467-3cd41d0b05fe",
        "T013_09",
        "aec4f230-2318-5db4-a8ae-fcadcb78c092",
    ),  # s37
    (
        "e3781710-70d2-5131-bcb0-3dcb2e49f218",
        "T013_06",
        "713c33ff-5f5d-564d-8a8b-8d7c9dbff874",
    ),  # s37
    (
        "2c2a9ab5-9f69-5dc1-b53e-8ab652980b2c",
        "T014_10",
        "983fc3bb-1f9b-5c74-982f-7b59d9825da7",
    ),  # s39
    (
        "3e45b94a-ce31-5dd0-8e89-bbd8e337ba27",
        "T014_07",
        "7d88c596-41eb-5c78-b0b2-f2f090b3088b",
    ),  # s39
    (
        "488ffdfa-fe92-54f4-9839-a2deb6c94150",
        "T014_12",
        "8e505d1c-71c2-5e04-9f2b-02f858d89bf9",
    ),  # s39
    (
        "5e7681de-e6a6-50bb-9ccf-60f92bc24526",
        "T014_11",
        "e6bdc1f1-4962-533f-849a-39c03a57f9ed",
    ),  # s39
    (
        "bd835254-5c0b-5f76-8167-446a605af54a",
        "T014_09",
        "845b826b-d074-5287-a108-83eb8f073b45",
    ),  # s39
    (
        "42ab936c-d868-5b1a-891d-4990b6aa2d6c",
        "T015_09",
        "6570b1a7-d65d-5f99-8ecf-11a2288f80c1",
    ),  # s41
    (
        "cc79bd87-cfa1-5ade-a4f7-0091ee397c1e",
        "T015_07",
        "2c39f4d0-f20a-5c42-8ee4-3a4734228383",
    ),  # s41
    (
        "f5387520-0743-5f08-93ec-686c9da71675",
        "T015_10",
        "6d1d0e48-ba7c-531f-a084-1e322200ae9b",
    ),  # s41
    (
        "5bd2fa1c-1e0a-5a5d-bc4e-a4cd161833a6",
        "T016_01",
        "f7dc59e3-ae64-536d-9050-c08a78d03445",
    ),  # s42
    (
        "9498ae05-1237-5de3-9613-1a4496b2fca2",
        "T016_12",
        "def2e508-b468-5779-bd40-725c1bb34cf8",
    ),  # s43
    (
        "03fa8e65-d1f3-5723-9378-b4e6abb77f9d",
        "T017_02",
        "a5b2bad8-406b-5974-9d69-e74edff9033c",
    ),  # s44
    (
        "1e7674c9-59e2-58e3-9a09-e11fb322ff55",
        "T017_05",
        "bcffb6cc-4d05-5da6-92ce-8ce7b0439954",
    ),  # s44
    (
        "da991893-e4f4-537d-8dd5-b5c8c958c4c0",
        "T017_01",
        "2df5dfb4-5853-5c73-bc6a-ebd3e81adf39",
    ),  # s44
    (
        "dec83645-eed0-5dbd-bf87-10eab0c73b6e",
        "T017_06",
        "a0edfd2c-298a-53dd-9539-7e60efb3c9f8",
    ),  # s45
    (
        "fb01df88-2085-515a-b07c-9b8a2928bbe3",
        "T017_09",
        "cb7a2453-b76e-580e-81d2-5138db4a6601",
    ),  # s45
    (
        "1f48f1d5-7d18-588d-9830-57ff5558eb20",
        "T018_10",
        "9debf90d-033a-5011-beda-7d30a4ace25f",
    ),  # s47
    (
        "234a5222-5d9f-5edb-a5dc-c5a889364d77",
        "T018_06",
        "0c10f5f8-ec0d-503c-8b22-b0d150f7146f",
    ),  # s47
    (
        "a7a0a0ca-ac8b-5590-b9a2-f3877eb63c26",
        "T018_09",
        "696949bb-45b0-5171-a702-44b0ce7bbe7c",
    ),  # s47
    (
        "cea58fba-cf06-5d88-ab8b-6d57b5b75a62",
        "T018_07",
        "80ad1729-cf39-51d1-b03e-bb1fefc4f47b",
    ),  # s47
    (
        "dc358ab2-2295-5c0c-98df-c50fca4d9f23",
        "T019_04",
        "a8fea7ca-f604-5741-b7b7-d728907ced58",
    ),  # s48
    (
        "7089b1e8-e29a-5bbb-94e9-72959e4777eb",
        "T019_11",
        "3b9d4059-bb56-539b-b586-4a86c79042ba",
    ),  # s49
    (
        "a5e6f866-8834-563e-b1da-e779e44186c6",
        "T019_09",
        "6cf75553-3b0a-5dca-9bde-b97fe164c00b",
    ),  # s49
    (
        "c2ebf125-67ae-5434-9c20-e03dde076c5d",
        "T019_10",
        "a40468da-16b9-5b11-9c7a-f6b7f5b9f2e3",
    ),  # s49
    (
        "fe74f3d7-c7d7-5ba8-b9fc-01f2f1ad4c66",
        "T019_08",
        "476ce821-e2b6-5314-b10f-70c90fd71bce",
    ),  # s49
    (
        "ece3bc00-fc8e-525f-b95e-fc9c4587b18a",
        "T020_04",
        "8f3783a4-080e-5e5c-a46d-21ea73d82e80",
    ),  # s50
    (
        "1ba2012e-dbd2-52c7-aed5-72ad8fe4a162",
        "T020_06",
        "56c4c3a3-da54-5ff0-a5a8-fba42bdb3bb7",
    ),  # s51
    (
        "ab64aaf1-8ba7-5c77-85da-7ff2431497d7",
        "T020_08",
        "c76ed584-6612-5abb-9fff-f2da4566edd1",
    ),  # s51
    (
        "ea326acb-9102-593c-9b6c-541db98eab10",
        "T021_10",
        "f067164e-3228-5fb5-bbb3-c1f364e5469c",
    ),  # s53
    (
        "190d1ee1-a459-5f28-a520-16424be89c17",
        "T022_01",
        "2234f200-3482-5dbb-ac4d-47b49451738b",
    ),  # s54
    (
        "63a64fda-45c6-5a6f-aa64-737973cd5370",
        "T022_04",
        "8eb5ad84-dde7-5222-8ff5-06ef058ec9e6",
    ),  # s54
    (
        "07a19dc5-2773-5512-98f9-4a7f1794d210",
        "T022_10",
        "94a3630f-f4bf-5edf-91b7-46ec16db71a1",
    ),  # s55
    (
        "302372bb-66f7-5621-b2d0-ec1b7ab8a5d2",
        "T024_12",
        "0d6923b9-8db4-5b29-9010-cff72372d1d7",
    ),  # s59
    (
        "c04304a4-2ac8-559c-94a8-9c384132510b",
        "T024_08",
        "b48ba1b0-cdf5-59ae-a809-2ce376d88524",
    ),  # s59
    (
        "cac394ab-709d-563f-9f16-4a7bb2e6c41e",
        "T025_09",
        "835450be-6275-50cd-a234-2e49e38e2e7f",
    ),  # s61
    (
        "250c37bb-409f-50a8-8d5b-db18ae09c301",
        "T026_01",
        "5ea96b48-fcbc-5e13-8284-f0ba54a48c40",
    ),  # s62
    (
        "5f977187-b542-555c-8bd6-7fddb2b24777",
        "T026_03",
        "b05b2bec-7536-5ada-b32e-0755d5099d44",
    ),  # s62
    (
        "6452398d-29fd-5c8c-a622-849666cb7afe",
        "T026_02",
        "d52b2a75-8418-5eaa-9f3d-a0738a12b80b",
    ),  # s62
    (
        "107bb58f-3496-56c8-b735-32e9ec6f1d5f",
        "T026_08",
        "4888c905-f8b3-500c-ae0e-c6e35a21701e",
    ),  # s63
    (
        "4c8c4849-7526-5e5a-803e-4aa62c831f86",
        "T027_10",
        "3c9a44b0-eed2-5bea-9bf4-b9489fd7e6c1",
    ),  # s65
    (
        "c40a1400-a6a8-58c1-b01d-6578a2a2c163",
        "T029_02",
        "f3003dab-81e2-522a-99ef-230c6f15692d",
    ),  # s68
    (
        "4521296d-6037-572c-8106-3268a531cc91",
        "T030_09",
        "9f764673-50ec-5090-b376-a12f8c3beefe",
    ),  # s71
    (
        "212fcadf-f37d-5474-b932-b29966b68cf5",
        "T031_11",
        "2afd2e66-17e0-51eb-b7b0-87eec1fd5caa",
    ),  # s73
    (
        "27a6472c-4378-5e28-87e9-2c34c02fd80b",
        "T031_08",
        "81048ee4-6fab-561c-a967-5d62c24b0626",
    ),  # s73
    (
        "96da0da1-1335-5cd7-b383-66f745d390cc",
        "T032_09",
        "f38a1559-2254-5544-8afa-5ef9c5939943",
    ),  # s75
    (
        "d38b57da-ec5c-554e-81e1-e2f0fdd6e67b",
        "T033_08",
        "b6e94d0f-53a7-5b23-a851-a8a4937388e0",
    ),  # s77
    (
        "ea72edef-d770-5ba2-8855-68d9bc3c43dd",
        "T033_11",
        "2ff76d6b-7245-5936-a413-7135884fe05e",
    ),  # s77
    (
        "cfcaf7d8-86d9-5bee-af1e-e2029eff9ded",
        "T034_11",
        "4709068d-5ef4-5ce8-a523-f82bbaa54783",
    ),  # s79
    (
        "05bb4119-140a-5c47-9efe-9e2f7e7c108e",
        "T036_07",
        "4cd265cf-3eef-54bc-887f-fa84c9a15f25",
    ),  # s83
    (
        "0cb854ae-6cc7-505e-b9a5-ddde0ae5386e",
        "T036_11",
        "a1cdeb83-c1f7-57d3-807b-963e9174469f",
    ),  # s83
    (
        "5c2cf6e1-05d4-5504-87ad-20dd321621bc",
        "T036_09",
        "00eea66e-7981-5786-8bde-cfc4dafd968d",
    ),  # s83
    (
        "d383bd44-7944-523e-b2e8-3b0007bd862d",
        "T036_12",
        "c1ac5dd2-3089-5d85-87e5-03c8f5035cab",
    ),  # s83
    (
        "5bdb2705-86fe-5c29-9f4e-4ce302efcbde",
        "T037_01",
        "73b1d734-9b35-5237-9ece-6b052dfdcd45",
    ),  # s84
    (
        "74b7f09f-6e9c-5503-8f46-8cfa054546b6",
        "T037_02",
        "69884266-1906-5248-96b1-429786260625",
    ),  # s84
    (
        "7dc49cb8-3f13-542b-ba2d-eafaff1650f5",
        "T037_05",
        "7b5a605b-a3a0-5668-a133-5f909dfe56d1",
    ),  # s84
    (
        "925465f8-8962-5dbd-b2cd-170994a98be3",
        "T037_08",
        "a894910c-642d-5bb5-9f85-a77ece078607",
    ),  # s85
    (
        "a279f845-0b8b-5e36-87a0-2a062c4de1d7",
        "T037_07",
        "22d7dbbf-105e-55cc-87f6-5f6da745565e",
    ),  # s85
    (
        "e0011d6c-77a8-5dd8-8668-ddee6ff94a62",
        "T037_07",
        "22d7dbbf-105e-55cc-87f6-5f6da745565e",
    ),  # s85
    (
        "ec33435f-f938-5bac-b639-6b036c555568",
        "T037_09",
        "14a1421c-ce51-57b1-9937-62a0bde7df10",
    ),  # s85
    (
        "ffb48833-5793-5921-8848-f96aff7ee386",
        "T037_12",
        "8f02f1b9-0567-59a1-9d8f-1ea96035939b",
    ),  # s85
    (
        "669d0db7-e919-5b29-8802-933d971a2897",
        "T038_08",
        "e7d27311-cfd1-591c-b8c2-e85b8ec27ed8",
    ),  # s87
    (
        "5dcac540-890c-5ca4-b8de-5393e70774d1",
        "T040_09",
        "8986f167-780a-5892-a7db-52e3f08e2c6d",
    ),  # s91
    (
        "4e9140f8-e9d5-5fed-85ba-74eed4ae2579",
        "T041_08",
        "9f9beb78-1773-5761-b248-37ca6f687f5c",
    ),  # s93
    (
        "0680f256-2fd9-5db7-b4c0-94c0b21cc3c1",
        "T042_07",
        "0d85ccc6-9d97-532d-9fb1-4186cefb9822",
    ),  # s95
    (
        "99610372-1087-5644-9ae1-1ca58e74a0e1",
        "T042_07",
        "0d85ccc6-9d97-532d-9fb1-4186cefb9822",
    ),  # s95
    (
        "7968f5db-c110-5e69-bace-7ae97ee16009",
        "T043_11",
        "a072f5e1-877f-5152-88bf-b21080f0a5b9",
    ),  # s97
    (
        "1232a7a6-5266-5590-a7b2-e7e56af215aa",
        "T044_09",
        "e5907a3d-bfa4-5999-9bd3-4af4b4b72fa1",
    ),  # s99
    (
        "14448a9c-d603-5bbe-8b9f-902805f67b33",
        "T044_08",
        "d29bb7d1-bf19-5914-9a65-06641258341d",
    ),  # s99
    (
        "57689105-2c5e-5df1-9a2a-f3c2eadd9c7b",
        "T044_11",
        "bf74f211-05be-5b2b-a4ae-8ea6479ac6dc",
    ),  # s99
    (
        "6e95cb0e-bc1e-55c3-ae0b-0f878702341e",
        "T044_10",
        "25883a07-c9f2-527e-963b-1106aabb6f74",
    ),  # s99
    (
        "a95c8bb4-c807-5745-9969-86ee84b1741b",
        "T046_01",
        "f3d3fb29-85ed-5519-b2df-ba84df281dc2",
    ),  # s102
    (
        "ed66314a-e3fa-58fc-8fae-5770fb5ab711",
        "T046_02",
        "d1eedb4f-8fd9-5be6-8b58-8442172d8a56",
    ),  # s102
    (
        "2fdf7ea8-9866-5757-88da-3b860d12e345",
        "T046_10",
        "313a7eeb-b95b-5c58-9582-742d289c183a",
    ),  # s103
    (
        "fe3ff450-2843-5434-8640-d2b0478b4b5d",
        "T046_07",
        "2c164d0a-2c93-5291-9b17-c26bc6d98d04",
    ),  # s103
    (
        "5d42cec4-ad42-5515-9132-d481d332e55a",
        "T047_08",
        "35671a33-7bb8-5692-a508-c99993f25062",
    ),  # s105
    (
        "44a765e1-fdf6-5890-b41f-284e47cfb8a3",
        "T048_01",
        "61df1bc8-26b0-5fb6-9eef-29e5914a256e",
    ),  # s106
    (
        "8b6ebe01-0981-5dfa-ba02-78ca7fd1c00d",
        "T048_02",
        "e5112f11-4072-5fa5-90f8-0b9b6ce6bc1b",
    ),  # s106
    (
        "cd7c2f0c-98c5-54ce-9cb6-cd6f073195d2",
        "T048_06",
        "98650065-70eb-5859-9405-2390cd418dcd",
    ),  # s106
    (
        "0a6134ba-d16f-5606-9c1c-442c36b64b34",
        "T049_06",
        "f7091289-b48a-5a15-8639-f30abc73c127",
    ),  # s109
    (
        "8a63cbf5-7a37-55c6-bc91-5f3d8a377ffb",
        "T050_11",
        "c74dda21-8043-5991-b3a9-e2f29408ee4c",
    ),  # s111
    (
        "487c58dc-c112-5464-9e0d-6d4c2543041c",
        "T052_09",
        "f6af2f6f-341a-594c-aa42-53267c407a15",
    ),  # s115
    (
        "e04f4e16-b2cd-5e34-8db4-6732d8b3e58e",
        "T052_06",
        "405b6793-04cc-56bf-9e50-55df8ef3322a",
    ),  # s115
    (
        "ae0dd3ba-fe3d-52e2-b9ce-0349519c652f",
        "T053_11",
        "3d4ffd32-553d-5638-9d66-06c16e722cc2",
    ),  # s117
    (
        "0581427b-dcd8-50b2-b137-9ddfdab843cd",
        "T054_09",
        "3c51c90a-bc88-5d3b-8a17-dc2c31de8085",
    ),  # s119
    (
        "2f85285d-841f-5485-84bb-55973f3aafc4",
        "T054_13",
        "ade6e2c5-37c2-57be-a978-0688540ae478",
    ),  # s119
    (
        "68c57c12-2540-5b6e-a0b7-ecb10d5c47e0",
        "T054_11",
        "d3897462-a05a-512c-ade4-e4dfda6e32ff",
    ),  # s119
    (
        "91d43dc6-0ef0-5083-8e2e-d04c289043b7",
        "T055_09",
        "804178d1-fc0f-53ca-a277-4936e94000d8",
    ),  # s121
    (
        "954912ab-abcf-578b-9581-5e94773ec831",
        "T055_12",
        "dc0eacbd-9e85-54a3-951f-a7a811237878",
    ),  # s121
    (
        "16ced86d-0cb5-54b7-9d30-9148a8f0f254",
        "T056_04",
        "af71395b-28d4-5082-ac05-80fb1c8cc501",
    ),  # s122
    (
        "2e303ef6-4296-5d35-9cdb-c28da33db768",
        "T056_11",
        "d8163260-b84a-5b33-a587-c5f57bfe20db",
    ),  # s123
    (
        "b500436f-d33d-5019-a324-cc5726a433fd",
        "T056_08",
        "63fd2626-1844-5e5e-9789-b803502c295b",
    ),  # s123
    (
        "dc9dce9b-b99c-5f14-bcd5-b77354193587",
        "T056_12",
        "48c5dbad-b870-54fb-8f25-79d98e95f810",
    ),  # s123
    (
        "6f0a59c9-00c9-59c6-be6b-cccd592d5f8f",
        "T058_01",
        "fb399610-d49c-594d-b05b-ae95a5dd97d4",
    ),  # s126
    (
        "872bcfd7-783a-5f6b-ae4f-c21757b4b8b7",
        "T058_09",
        "6d2ba450-7d92-53e0-8a47-e49a5b7605fa",
    ),  # s127
    (
        "9a3114a3-0b59-5c51-8c99-d4f4e396997f",
        "T058_07",
        "62eb747f-a4df-56a3-93f7-a1839957bbd5",
    ),  # s127
    (
        "2381b55b-9286-5b7b-9276-0852a32ef249",
        "T059_01",
        "d6e2d351-1cd4-5f22-abf3-c98fb2c1b0fb",
    ),  # s128
    (
        "d97555ee-34ed-5880-9608-a5ef136ffffc",
        "T059_08",
        "1a9d77b0-8a67-5304-bcc6-96b71b28864c",
    ),  # s129
    (
        "29827081-4918-5a80-aa58-d017c838e2b0",
        "T060_06",
        "557c455b-f18b-531b-aa6e-2d2990c66cce",
    ),  # s130
    (
        "2bcc201e-9ee7-5837-963c-67d71edf14a1",
        "T060_03",
        "91dc6abc-aac5-5ead-8648-f039db734299",
    ),  # s130
    (
        "45b93367-eebe-5699-b584-d47a87288b39",
        "T060_11",
        "ae40f58d-1c21-5af9-86b5-b1f7e22a4c11",
    ),  # s131
    (
        "3cf5c36e-203b-5fa0-8ec2-05e45852a373",
        "T061_06",
        "02e07736-0b6f-5fb1-8d65-a78f47c25a36",
    ),  # s132
    (
        "519fac5b-8c67-5717-a09c-b612f4028e88",
        "T061_02",
        "bc193cc7-3b29-5051-840f-e94618844a75",
    ),  # s132
    (
        "e303c30b-e900-526a-9d0b-2ae9e5dfb33a",
        "T061_03",
        "f63e334d-30e4-5cbc-9ca6-83c25a61392e",
    ),  # s132
    (
        "fa072459-31e9-54fb-ab10-995e258361a0",
        "T061_01",
        "62dc7b43-8849-5ce7-a010-0f26e2af076b",
    ),  # s132
    (
        "1ed1bf18-a526-5449-bb8c-1da75eef33eb",
        "T062_07",
        "96449cfb-873c-507d-b0ac-d7e5ae7428ef",
    ),  # s135
    (
        "2b2a1b52-bf25-57a8-9529-441dc64ca057",
        "T062_08",
        "2595d974-bb6d-59a3-8a34-cefd0f35e934",
    ),  # s135
    (
        "fe1297e5-933f-539b-b51e-f30bd859df5a",
        "T064_10",
        "92d406ac-7256-50a7-a9e2-3a3fbc1119ad",
    ),  # s139
    (
        "7b327d48-1783-5386-8fcd-17840402005d",
        "T066_03",
        "b9bb0704-a4a5-5f6a-9955-be1ba524ecfe",
    ),  # s142
    (
        "7f700e21-3b40-5185-8853-9684adc6c32c",
        "T066_04",
        "bc1c3c96-c99b-55ef-80ad-7ad250911732",
    ),  # s142
    (
        "a0060308-931b-54ea-91a3-cfa855c72d8d",
        "T066_02",
        "e213a3e5-a811-536f-8c3d-601cc78850a8",
    ),  # s142
    (
        "ce5df897-dae6-5311-bc1c-f435505d76e2",
        "T066_01",
        "1b6cb228-3a17-5afc-bbd4-96ed488c49b9",
    ),  # s142
    (
        "1edaa9a3-f597-5c5d-afca-e21d5a8d3391",
        "T066_11",
        "5d34a6c6-3a62-5916-8ebf-9276ce041fed",
    ),  # s143
    (
        "7783a50a-a118-535d-bd9e-53743bf8dc4a",
        "T066_08",
        "6c9a64f5-5d94-5883-9692-9bf1cb3a8e77",
    ),  # s143
    (
        "cb52ebc6-ec65-5900-95a1-fe58572ef74f",
        "T066_09",
        "d035bdd8-3fa5-5014-9705-64da8fb28e07",
    ),  # s143
    (
        "51736c49-0379-5427-9b20-34c72a41bc67",
        "T067_06",
        "214c2f26-c86f-5d5a-a5f7-1352dcfffa3b",
    ),  # s145
    (
        "7d2e8bf2-eaf9-540f-9a5e-cd38ff0a40a1",
        "T067_10",
        "1578eaa4-8a56-5bf2-aea4-ea28740c9714",
    ),  # s145
    (
        "55918bf9-fa73-53bb-8a59-b1e6ba1e4072",
        "T068_09",
        "66a92f2f-ee12-57ab-9abd-7b2cda652ad5",
    ),  # s147
    (
        "56e9e1a4-562f-56f0-8d73-2ddfa338aa12",
        "T068_08",
        "78cc7fb5-2314-53f5-8c27-dfe7f6d73451",
    ),  # s147
    (
        "bd6547fa-23da-5f4f-821f-909776859b89",
        "T069_08",
        "c4e26cec-2913-5bd1-8a0d-58bdc5b528c5",
    ),  # s149
    (
        "1b796da0-770f-5dd2-943e-e212361ec833",
        "T070_02",
        "0e8545ee-d2c7-501c-ac91-c99fc5a7cd54",
    ),  # s150
    (
        "aec5386f-d9ca-5c81-924b-a743aa75e2de",
        "T070_03",
        "d628d53e-f780-57a0-be40-cdfe494971c7",
    ),  # s150
    (
        "a0163b0a-0408-5437-af3f-dbf402817768",
        "T075_07",
        "ee03462c-6fa7-520b-85b8-644fa9acee32",
    ),  # s161
    (
        "4f2b4d38-7c20-5a21-bfb0-2aac6c9ac39c",
        "T077_09",
        "495763d2-4e35-5c7c-a19f-c9e2d218221a",
    ),  # s165
    (
        "56116b99-0fd7-5b6f-8f90-eb9fb93a1b5e",
        "T080_10",
        "a2034d52-5883-5cc6-a65b-54a8146560d3",
    ),  # s171
    (
        "ff72c042-e9a8-53b8-90c4-92cfe0d55c3d",
        "T085_07",
        "a53f30eb-b636-5544-8637-e95b098abeb7",
    ),  # s181
    (
        "6262d5cc-c6cd-5555-aee8-fab873d37c73",
        "T086_07",
        "1f5f30e2-b943-55d3-80cf-dc10140638a9",
    ),  # s183
    (
        "d35fdd66-24b1-5bdb-ac79-6e58911a911d",
        "T087_07",
        "c5c1d0f6-a6f5-5975-a639-b7c7e1a3a157",
    ),  # s185
    (
        "fc18a2e9-81ec-5924-b43a-5ff96bbc3865",
        "T088_09",
        "11fcb5b3-fd4a-5872-a28f-66a64ce00662",
    ),  # s187
    (
        "1848ba36-9fea-5b6c-a94d-ffd0936d8343",
        "T090_06",
        "6a9b4393-781c-526a-ba2b-7f468f93a914",
    ),  # s191
    (
        "afe719c8-927a-5d14-abde-0bcce4b63cdf",
        "T091_07",
        "76d15224-f4b2-5bd0-93cc-d06bdabee564",
    ),  # s193
    (
        "c596f595-d207-54b0-8249-bf35f94f4b3a",
        "T091_11",
        "4e2faf62-eb58-58ba-98c6-3996957438e0",
    ),  # s193
    (
        "0d6e2981-e4ef-5b56-8b93-657e788135d4",
        "T092_06",
        "75ae5123-bfdb-51e0-8b2f-3b6bee72860b",
    ),  # s194
    (
        "2aff2779-8956-5e4e-a2ac-bbf4e764e11a",
        "T092_02",
        "fd910bd5-6630-5467-9ac7-be2a071f113e",
    ),  # s194
    (
        "f5b4d9b9-9d7c-5a85-a1a0-f3f816d24521",
        "T092_07",
        "63e65af7-e1e4-52ad-9228-53f416c9ca70",
    ),  # s195
    (
        "292d61b6-a585-5883-8762-ffdd1c20f69b",
        "T095_08",
        "320dff6a-ae9a-57b6-8231-792d54918f80",
    ),  # s201
    (
        "926afdcd-b374-5bb1-a88c-5b82c59d895a",
        "T096_06",
        "659d57fb-0523-5c4e-8c91-619e4e090d20",
    ),  # s202
    (
        "92d09264-a506-5339-b053-4e03c457b104",
        "T096_03",
        "ba29244c-be8b-509a-a4b4-cb7a6e9f7418",
    ),  # s202
    (
        "2a7be00a-d6fe-524c-a810-ff55fcc48dc1",
        "T096_09",
        "4e8f3e6f-e5a4-5009-bef6-68d8278b91b6",
    ),  # s203
    (
        "bf0e2879-1cad-585b-9c27-c3a645f666ab",
        "T097_01",
        "7c2d39bd-d4bd-56db-84fc-ed8d0ed810f4",
    ),  # s204
    (
        "a4a41c84-9ec9-5bf3-81d0-a4f7dcc32733",
        "T101_03",
        "a2252725-59c5-5afe-af0b-493321baec84",
    ),  # s212
    (
        "c6f0b3f8-89b4-56fe-b988-930bb47fa1fb",
        "T103_09",
        "6cd78854-4b3d-5dd4-a007-a2f9d5602ed9",
    ),  # s217
    (
        "d781ff3f-f598-50a4-964c-62429f8e036c",
        "T108_09",
        "5a0b1695-9fe1-5780-8f09-3924e6df60cf",
    ),  # s227
    (
        "819d55d4-9486-544b-b319-e2c3ed495988",
        "T109_03",
        "befefc88-dd66-5a13-9c83-54bc87b5a849",
    ),  # s228
    (
        "1aebe827-c3e8-5198-a55c-82b48d1bc113",
        "T112_03",
        "9e26dbc9-bede-55fb-ae98-5afd5a1b562b",
    ),  # s234
    (
        "12875f36-1f9e-5bb7-ab5e-62c13cb6eb65",
        "T117_05",
        "0b425454-b81d-50d0-a854-7dd77146c60c",
    ),  # s244
    (
        "1c163aa0-b57b-54c4-9a0a-5a40eb5a17e1",
        "T117_04",
        "9473918d-ff50-5c35-a200-0991550c61ee",
    ),  # s244
    (
        "49cb28cd-7709-53f1-9903-d7baac91e21f",
        "T117_09",
        "c416c053-f2ab-5af9-8cc0-9428cab06817",
    ),  # s245
    (
        "a856686c-1aa1-5461-a226-fa684a06372e",
        "T117_08",
        "8e03a157-6fc2-5aa1-b6ef-20f983d18484",
    ),  # s245
    (
        "f0e386c8-8a70-528c-8ffd-53bb9275a025",
        "T118_10",
        "ca8c38d2-9278-58be-be97-613e821a1427",
    ),  # s247
    (
        "292f5ede-1e9b-54cc-8478-0f9ddaaa75d4",
        "T119_01",
        "5e01f483-a427-523b-b591-bb6814ad7ddb",
    ),  # s248
    (
        "51e0e52f-6e7e-521e-868e-84056a99a039",
        "T119_04",
        "b1b74d77-91d3-5ed9-a0c7-547c2fb22255",
    ),  # s248
    (
        "d6571390-e769-5cda-a335-1a4a1d8f6305",
        "T120_02",
        "e11aee2e-b299-5f1a-ab07-e54eff957117",
    ),  # s250
    (
        "b24c4217-fa5d-5e57-8dc9-80b0f16a2ce3",
        "T121_03",
        "c2fc1db2-6b9e-55c1-980a-5ac54301702f",
    ),  # s252
    (
        "ea778023-d82c-5dad-a714-3905f505a902",
        "T121_06",
        "b58dae1b-3a56-583f-92d2-9456356d4b21",
    ),  # s252
    (
        "ba150d32-0949-562e-8b09-e8f7fe4ba8b0",
        "T121_07",
        "d2eb3c7f-9473-5267-9a04-56faee692aa3",
    ),  # s253
    (
        "450da69b-c34e-5935-90e5-8c62c9069302",
        "T122_05",
        "fc20a5d7-1754-507b-9d40-35f65b9a5e30",
    ),  # s254
    (
        "451c3c21-6133-54a4-ad75-565bf4142efa",
        "T122_03",
        "f4fdf05b-2fd6-50ca-b83d-9d749cd90192",
    ),  # s254
    (
        "c024334e-a4d7-5375-a70b-60aa9c223dc0",
        "T122_02",
        "6e75d235-b582-5d09-b888-562615108968",
    ),  # s254
    (
        "488c8a76-f072-502b-97e1-84614efe5566",
        "T122_07",
        "b6311318-5d4e-5c97-98f0-6bea7cd5270d",
    ),  # s255
    (
        "8da14370-23ca-5256-9ba3-f2bcd8ad10e3",
        "T122_08",
        "1d360a15-d46f-5c50-93dc-2389c427ebc7",
    ),  # s255
    (
        "6f4cb652-96ef-5bbf-a7c8-dccaf912693f",
        "T123_01",
        "1f2bde6e-4079-548a-b6ea-c84eb1ccebd5",
    ),  # s256
    (
        "9afd102b-9e4c-55e8-8864-2a8a37153e68",
        "T123_08",
        "74f05818-176f-5dca-99d5-b84d85166d40",
    ),  # s257
    (
        "25ce4a8f-8b94-5637-ac8f-73550bb2dac7",
        "T124_07",
        "a6fe824c-1319-527d-ada2-1d541c0632e0",
    ),  # s259
    (
        "870788c6-fd48-5be0-ba91-173812c25afb",
        "T124_07",
        "a6fe824c-1319-527d-ada2-1d541c0632e0",
    ),  # s259
    (
        "c4fdfc0a-f496-51fe-9013-c393f6b66e4c",
        "T124_11",
        "6eebf875-9656-51f5-874a-925d3729b568",
    ),  # s259
    (
        "02c7815f-584c-5098-98f6-e045214b6178",
        "T125_04",
        "c69d6ee0-4119-5b7e-92b8-986cdf4280b3",
    ),  # s260
    (
        "1a5669d1-ce0e-5859-8bb1-7696ee8fd453",
        "T125_11",
        "fdbde4a0-dedb-51b2-a19d-d1db45679c92",
    ),  # s261
    (
        "5b20ee62-ffab-5eba-970f-8faa182b7886",
        "T125_12",
        "d144de94-b73b-5481-9b74-bc422abf57b1",
    ),  # s261
    (
        "24247566-c0d6-5797-acf3-2c6d8839be12",
        "T126_11",
        "f82ea784-1b59-5bbf-bd6a-d1389040c1b0",
    ),  # s263
    (
        "f391398f-d802-538c-86bb-a0819d94018c",
        "T126_09",
        "a8a1652b-8346-5717-8d2c-896b55e35a57",
    ),  # s263
    (
        "1afbf8b3-9880-5d79-a0e9-c7f857ac5754",
        "T127_05",
        "f2af09b3-171f-585e-9157-4faecfc44e2d",
    ),  # s264
    (
        "f6f5de54-fa4f-51ef-b890-80a171827ae6",
        "T128_02",
        "1da5723d-b5cc-567a-8989-b179dbb149e8",
    ),  # s266
    (
        "25a6c0a3-b667-5676-a8fc-418bf00819a0",
        "T129_06",
        "18a84dd0-45cb-5b47-8da8-27ebfda0d43d",
    ),  # s268
    (
        "cb2ff241-edcd-5dba-beba-569b53686854",
        "T129_05",
        "7b317d9e-8e1c-59fb-b3cf-e6400a669503",
    ),  # s268
    (
        "fbb172f3-6bb8-5b4d-9847-03822f3334de",
        "T129_02",
        "d8b86d1f-d538-5aaf-805a-79facaaa4072",
    ),  # s268
    (
        "b228cbc9-cc6b-5909-b639-af480577e4aa",
        "T129_10",
        "eafb370f-b65c-5b2f-9e20-03f94beda056",
    ),  # s269
    (
        "920bef02-ac60-5b9e-bd4b-8260441f2bed",
        "T130_11",
        "48f5c403-de55-5052-97e2-ccab622fe788",
    ),  # s271
    (
        "09623062-8cb6-5a2d-ac4f-4382473d7476",
        "T132_06",
        "339b878c-12f0-572e-97d9-31292a7bcf66",
    ),  # s275
    (
        "203d7b95-e687-5c40-b5d8-b7fd3251f34b",
        "T132_05",
        "29979a86-2b44-5bfe-a66d-88ad56bf5475",
    ),  # s275
    (
        "88443fc4-45ac-5625-92b7-63b4871adc10",
        "T133_05",
        "2ff23e63-00f3-5b16-98f5-d34700e4846b",
    ),  # s277
    (
        "4c71de80-8ded-53fc-bde9-244cd608f01d",
        "T135_05",
        "922d7c48-c8f9-5ddb-a332-0a0baa77fbe7",
    ),  # s281
    (
        "6ffbc737-dd02-5f2b-925b-90a19ae6db1b",
        "T136_08",
        "03b2138c-9258-5834-afe8-2ace1cfd981a",
    ),  # s283
    (
        "963ca149-f358-5e25-8abd-44c847cf952c",
        "T140_06",
        "fd222576-73aa-55d9-b7ad-dfada3fdddc3",
    ),  # s290
    (
        "bf47dde6-084d-5dd4-bb65-575b6af3d559",
        "T140_07",
        "2d1657a0-a4bc-5efb-a268-30162c78a04e",
    ),  # s291
    (
        "1a629639-84f2-56d4-9732-54c90f814231",
        "T141_07",
        "eb10b564-1178-5056-9ddb-3bf900aa988a",
    ),  # s293
    (
        "beb33b5c-ff0d-5943-884a-696b48845d24",
        "T141_09",
        "f6634589-b328-5ef2-983d-4d00429b9a13",
    ),  # s293
    (
        "30d7dcb0-db4b-51eb-a639-bae922730f6f",
        "T142_06",
        "c869b2ee-1044-56fa-96a8-9c39e8f1776a",
    ),  # s294
    (
        "9b350d96-1e18-58af-889f-7e6aa3f2f8d5",
        "T142_05",
        "b46e6db7-6c9a-5358-8413-42245678d6f7",
    ),  # s294
    (
        "07f9c551-0b3c-5018-a7af-f42ef51e4fe0",
        "T142_08",
        "c783796c-48aa-5d4e-90de-b403da4ece7a",
    ),  # s295
    (
        "f91d42a4-f167-5eca-942d-7ab221d11502",
        "T142_07",
        "602f1436-f0e8-5853-b2bd-9b03029e4dd7",
    ),  # s295
    (
        "15e6e2a7-bd4e-5c3f-83ee-1539d2bd90b8",
        "T143_08",
        "39d2f6c9-db99-559e-a1a9-04e97223f815",
    ),  # s297
    (
        "7243b4a4-98c7-58dd-9d8c-93c6e13492f4",
        "T143_10",
        "a453c7a5-a5a9-5b70-a8d5-982e720f9d35",
    ),  # s297
    (
        "7d050b5e-ac99-5cc8-bd03-e0d0c080a063",
        "T143_07",
        "f213b6b3-420a-5f8d-9302-9c17937f6612",
    ),  # s297
    (
        "624d0d76-f681-5839-928c-1671a30bfc84",
        "T149_01",
        "0e6f83af-3196-53a2-b8bf-556d99f037a4",
    ),  # s308
    (
        "0ddc810a-6a89-5fb6-8e49-755dd12e1719",
        "T153_10",
        "1ad37a49-cd47-52bf-9de9-53718046b335",
    ),  # s317
    (
        "5561a64b-8da5-5269-bcea-3e71f06cbe5f",
        "T153_10",
        "1ad37a49-cd47-52bf-9de9-53718046b335",
    ),  # s317
    (
        "721cde14-99ee-5673-a390-1f2312a44298",
        "T153_11",
        "f6d4b8e2-edde-5fca-a939-23be49c2aea4",
    ),  # s317
    (
        "ae3047e1-69dc-50fc-b22d-33b5a201205b",
        "T153_07",
        "45059271-1d73-5cf2-bb21-358720385244",
    ),  # s317
    (
        "b3b63065-fe1c-50aa-bee1-e4b6d27fe7dc",
        "T153_08",
        "6bfa9bce-03dd-5094-bc22-9593c9e8eb5d",
    ),  # s317
    (
        "ef459f66-85d3-5bda-92ee-e28977a6d84a",
        "T154_11",
        "a982bdfd-36c8-5530-8e62-95c6f812213d",
    ),  # s319
    (
        "216982a5-dea3-5846-9ea8-6982227144e0",
        "T155_09",
        "c0468cf3-a7ea-58b6-bd99-4bea081aea58",
    ),  # s321
    (
        "b708164c-4565-54ce-98ce-488530db8f47",
        "T157_11",
        "149e3f54-ef01-52b3-8f88-c9922c44bb4d",
    ),  # s325
    (
        "3673b1cc-3585-500f-a262-e0ae17b6abcf",
        "T159_06",
        "be349d3a-4e0a-53a9-a841-e4e2229e974f",
    ),  # s328
    (
        "9c0f23b9-efca-597c-9964-cd79f55fe075",
        "T159_04",
        "83dd20bf-7934-5645-b91a-dbbde78ce62f",
    ),  # s328
    (
        "db1b48e2-f4d3-57f6-83c6-ec732d38c18c",
        "T159_08",
        "1f5caba8-96af-5755-b03c-31eb9284ce70",
    ),  # s329
    (
        "514069b8-9540-5561-b93c-5c69445e6f51",
        "T160_02",
        "35b628d9-76dc-5d78-8425-670bfacb01d7",
    ),  # s330
    (
        "3cf81f3e-34c3-5747-b4b4-322bd6209b25",
        "T160_11",
        "1148a310-ef51-555d-867e-992a1ea4f3a5",
    ),  # s331
    (
        "283c2dd4-7960-5cc6-9879-0dd6e6eda313",
        "T163_01",
        "9d3601f0-5e93-5460-847f-6094b3ddee52",
    ),  # s336
    (
        "0957b983-e2c7-526d-bac7-49084329a936",
        "T163_08",
        "301c1a2e-59ea-52b2-a4af-0e872354fca3",
    ),  # s337
    (
        "c1af4e9e-2c2b-5f01-a1f7-5248ed913bc3",
        "T163_11",
        "8b76e693-9c33-5763-82c1-3caf0bf4c0e2",
    ),  # s337
    (
        "6a730569-c95b-5a9a-8e12-6cfe2455ec91",
        "T165_07",
        "4ee387c9-f53c-5e3f-bbce-51b7efce87fc",
    ),  # s341
    (
        "b8c59c0d-7b57-5644-98b1-4e1ca877338d",
        "T165_07",
        "4ee387c9-f53c-5e3f-bbce-51b7efce87fc",
    ),  # s341
    (
        "daf42d50-c04d-55a5-9abb-c7d1ea1bdf92",
        "T166_10",
        "e6aeb63c-a996-5c03-9dfe-b049a860b497",
    ),  # s343
    (
        "61f3f793-1f90-5c31-93bb-2ef8564e9f0e",
        "T167_08",
        "e28d6afe-4c32-5d89-ac5c-15cf0ad6deb3",
    ),  # s345
    (
        "8b21bd3f-c954-54cd-8185-a744c1b2ca57",
        "T169_10",
        "04c63cff-5f7d-52da-bcf3-bcce3efa8a8d",
    ),  # s349
    (
        "b99e46ba-c6f0-53ef-86f3-0ec14ba90e21",
        "T169_08",
        "d16d7036-0aee-5e21-8e2e-366cdf24c274",
    ),  # s349
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
        _log.info("[0123] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0123] mv_safe_for_beta yenilendi")


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
        _log.info("[0123] soru tablolari yok (taze DB?) -- atlandi")
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
    _log.info("[0123] eski hat: %s aday, %s satir pasife alindi", len(idler), len(eski))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0123] %s yok -- downgrade atlandi", GUNLUK)
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
    _log.info("[0123] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
