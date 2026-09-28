"""2019-2020 Aktif 0'dan Baslayanlara Aktif Kimya: modern karsiligi olan eski hat satirlari pasif

Revision ID: 0100_akt20k0_eski_hat_pasif
Revises: 0099_akt20k0_agac
Create Date: 2026-09-28

KARAR
-----
Sahip talimati: siradaki kitaplari ayni sekilde bastan sona isle. Emsal
0072 / 0075. Bu migration SILMEZ; yalniz is_active=FALSE yapar ve downgrade
ile tam geri alinir.

NEDEN (mukerrer olcumu, aktif_2020_0dan_kimya_mukerrer_adaylari.json)
------------------------------------------------------------------
Ayni kitabin eski aktarimi aktif duruyor:
    Aktif Ogrenme 0 Baslayanlara Kimya 2019 2020: 520 satir, 520 aktif, 187 modern karsilik
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

revision: str = "0100_akt20k0_eski_hat_pasif"
down_revision: Union[str, None] = "0099_akt20k0_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "akt20k0_eski_hat_gunlugu_0100"
KAYNAK = "2019-2020 Aktif 0'dan Baslayanlara Aktif Kimya"
ITHAL_ARACI = "scripts/kitap/kitap_hat/ithal.py"
ESKI_KAYNAKLAR: tuple[str, ...] = ("Aktif Ogrenme 0 Baslayanlara Kimya 2019 2020",)

# (eski satir id, modern kirpim adi -- AKT20K0- oneksiz, modern id); kaynak:
# mukerrer_adaylari.json eski_hat, modern_karsilik=true. Yorum: eski basili sayfa.
ESKI_MODERN: tuple[tuple[str, str, str], ...] = (
    (
        "b02f8e07-fb44-5c8d-9f84-b727cda92e4c",
        "T001_02",
        "fd770958-eaca-58ac-881d-20859e4c4e93",
    ),  # s25
    (
        "bcea5819-21ed-5227-846a-59c195f60aa4",
        "T001_07",
        "344eea6e-0650-5d9d-994a-388df8d2a02d",
    ),  # s25
    (
        "cf795cf8-43d6-548e-b4f3-5de333eadc1f",
        "T001_01",
        "4977ba9f-fa13-5e0b-b5fd-7fd40aa718fe",
    ),  # s25
    (
        "2e870cc9-c1d1-51ad-9e0b-b07f34196aaf",
        "T002_01",
        "c268f1fe-aa5f-509d-b0e9-de32c3963ea5",
    ),  # s27
    (
        "5990c6d1-553b-58ef-b6b7-fdf4dc6ad207",
        "T002_05",
        "afa971df-9d68-5b12-9e95-1baefb2acc0e",
    ),  # s27
    (
        "8d24698d-d30c-5ab3-9784-04e37f668b74",
        "T002_07",
        "508adcb4-fdcf-5d71-9a5e-48a2aee10912",
    ),  # s27
    (
        "9554b051-a5f1-52a2-a440-ceca3e365b98",
        "T002_04",
        "689375aa-4678-52c3-a17e-1a94f5839b00",
    ),  # s27
    (
        "c0e448e5-a3ce-5bb2-aa48-a9514fc2047b",
        "T002_06",
        "a69a837e-e411-56b0-ae99-93258c750db2",
    ),  # s27
    (
        "e277c99b-7e4c-5c46-ac46-0fa2fd066cff",
        "T002_02",
        "cdb6728d-9441-535a-80e8-046e8f51d312",
    ),  # s27
    (
        "16c6b84d-111e-5029-afc7-2beee9ad810f",
        "T002_09",
        "cbedb365-72a1-574d-8065-deaa256012c3",
    ),  # s28
    (
        "bee7fd97-2250-5017-9b05-f413bd480593",
        "T003_04",
        "0315b97d-a3f9-5887-af9d-f194f7e0aaa8",
    ),  # s29
    (
        "d8e0950b-c469-50dd-a458-8a02d0bd4396",
        "T003_03",
        "df22f667-063d-5d48-b777-afcf00471c7f",
    ),  # s29
    (
        "e57cb73e-6761-5a65-aea0-b9745f81f2eb",
        "T003_07",
        "eade62e1-1848-599e-9bce-0fdc7dbcd2b7",
    ),  # s29
    (
        "9eb264a2-91d8-54cf-8b2a-8fabbec44d39",
        "T003_08",
        "d5f4353f-90ef-5c3c-a7bc-f513c28dbf5f",
    ),  # s30
    (
        "6e8b0861-b55e-5232-9e74-c588b409628a",
        "T004_04",
        "c18089d9-e35f-5d8c-bedb-28379207c777",
    ),  # s31
    (
        "8064e4c6-90e3-5f87-990e-447d4f6f82cb",
        "T004_07",
        "e8643fcd-fe39-5d04-9360-54b1163dd93e",
    ),  # s31
    (
        "a62bec16-d76f-5a7b-a890-5299332f4add",
        "T004_06",
        "ada85475-a74d-507d-ab0f-18293fecfdf9",
    ),  # s31
    (
        "0027a5e0-e01f-542c-849e-22e9a8c93966",
        "T004_10",
        "b3ab847c-452a-558b-89ad-6a699272f328",
    ),  # s32
    (
        "0a39386b-37c5-5ed4-9117-10449b30e78e",
        "T004_12",
        "ae1d48a2-ec65-5601-a7cd-80369ee5d4e4",
    ),  # s32
    (
        "2cbe479e-6104-5ccc-ac19-0b8ff85193c9",
        "T004_11",
        "178c40af-30eb-5fc6-8e0a-6e6f27588c41",
    ),  # s32
    (
        "3ecf07b6-092d-5e1a-98d4-e9d08b042222",
        "T004_09",
        "616a27e5-7605-52ce-b354-8e75a77d9a30",
    ),  # s32
    (
        "68020f98-6e70-54e7-a9de-ce6b228b97d1",
        "T004_14",
        "f7cc4655-0e05-5f32-a492-d5d2815a5ea4",
    ),  # s32
    (
        "ad425a23-e555-5228-adde-289e0ada1fce",
        "T004_13",
        "5386d96f-6c11-58b5-87c6-ffeb1776aea0",
    ),  # s32
    (
        "b43ef7ae-e713-5018-9f5c-7a52c26b9957",
        "T004_08",
        "189be2be-fdbb-5002-bea4-c9e71b32d448",
    ),  # s32
    (
        "8f80fd94-8cb4-54dd-8480-4953db26b922",
        "T005_04",
        "9266bbd2-c640-5d43-91db-d5a5175fe1eb",
    ),  # s33
    (
        "d05ca837-3ae1-5e1e-ad9e-1b49549a7f99",
        "T005_02",
        "662e30b3-475b-5618-908c-038cd61f9604",
    ),  # s33
    (
        "d1ebecc4-fd71-5ecc-94ed-0bb39d2682cb",
        "T005_12",
        "19ddefc1-0a6c-5a6c-94bc-0854c8c38345",
    ),  # s34
    (
        "52563627-ca71-5fb4-a323-a1968ac968ad",
        "T006_01",
        "2d458974-3bee-5aec-8ec8-f1f1cdaa207f",
    ),  # s35
    (
        "0f29969d-e88e-574f-a67f-315f8316d3a3",
        "T007_08",
        "0ac347d6-a7cf-5b23-af2f-5e23d0ef7a26",
    ),  # s64
    (
        "125a0cf7-9979-52b7-bbac-ba31822f2bd2",
        "T007_02",
        "6b4c9ab4-3b97-5e84-a465-f1a7ed1d3c1a",
    ),  # s64
    (
        "6a47e9fd-719a-5a08-8399-e89bc1ecfb9c",
        "T007_09",
        "b9bd81aa-50b2-5ada-8e8f-83be08742f89",
    ),  # s64
    (
        "a8a713a4-7691-576d-85ee-ed1207dc7118",
        "T007_11",
        "feb8670b-b043-5ff5-b294-6016b3b4d326",
    ),  # s64
    (
        "b801f245-2d5f-59b8-a240-af09f9544845",
        "T007_04",
        "d5bdb718-8c81-51b6-90da-ee8de348e019",
    ),  # s64
    (
        "c9874082-f26d-5ba9-8254-0fc7c8ba770d",
        "T007_03",
        "ec9b9ea6-62ff-59ac-b428-846a7e21f90c",
    ),  # s64
    (
        "f45fad74-255a-557d-85ef-46f71340a5be",
        "T007_10",
        "e7661e34-7bba-50e1-acb6-aafaeea1d4b8",
    ),  # s64
    (
        "fd8df7f0-273d-5892-a60a-1bbcc6dee58a",
        "T007_07",
        "aa29e4bd-0d36-5a78-a3e6-6a3885eb67b9",
    ),  # s64
    (
        "2a787c71-3b26-5701-bb35-4efcee0dc2de",
        "T007_14",
        "4818a014-f79a-514e-9c0f-c92e5ab27730",
    ),  # s65
    (
        "3dd1652b-256d-5aad-a0bb-b23d45c22266",
        "T007_16",
        "f3b0b00d-88b6-5931-9433-0d03b6a28407",
    ),  # s65
    (
        "cd97aec6-8518-56ae-828d-c80825f36144",
        "T007_17",
        "b37338e0-9690-5305-b079-2442b37ababa",
    ),  # s65
    (
        "d7ce4d99-2479-5cdd-a444-a798b1b1cd8d",
        "T007_15",
        "d05b6db1-855f-5aaa-bfe2-6ade981b186b",
    ),  # s65
    (
        "e520bc69-0d56-531e-a5a5-7cc815f9d0ad",
        "T007_13",
        "e051300e-42c9-5688-b3ae-eed30d84814e",
    ),  # s65
    (
        "0cf19375-8926-5331-8a97-be74c06a49a1",
        "T008_02",
        "1a7899bc-1a77-5144-a61b-c35447a0d390",
    ),  # s66
    (
        "75c9c1e3-d9cf-5ef4-b3ea-ec7b617ad5d8",
        "T008_08",
        "8decbb93-d007-5d08-adf6-cecdc402830c",
    ),  # s66
    (
        "fc2d148d-aee2-5de2-ab73-81277d83fe21",
        "T008_05",
        "4f6b3efb-c026-510e-885c-04fe9766703a",
    ),  # s66
    (
        "04bbfd4c-69c7-5d29-9e35-fad2206fa768",
        "T008_16",
        "62002ed2-1112-5d23-adb8-9d2883928959",
    ),  # s67
    (
        "27f1d847-edbf-5738-bc45-581b0f33547d",
        "T008_12",
        "6ca75fcf-655e-5b5d-a6ab-bd121039328f",
    ),  # s67
    (
        "34969bf1-2f12-54af-9485-2aea93951c13",
        "T008_13",
        "b8a089fc-828e-52bd-894e-eb892df2f869",
    ),  # s67
    (
        "3a3955f3-94f9-505f-aa84-0b1bc8629455",
        "T008_18",
        "554faab1-63bb-57e7-9b75-876dda549167",
    ),  # s67
    (
        "bb0b14da-1526-5f63-a587-f221c9b0f54e",
        "T008_11",
        "5bd09a6c-a756-51fb-bd59-99c283664fca",
    ),  # s67
    (
        "bf30f27d-1ec7-5ba5-ba74-1fb6c76e81a3",
        "T008_15",
        "02a3f444-91fb-5f69-b347-976a55535b3c",
    ),  # s67
    (
        "8a2a828e-950e-597f-8a08-6fae6cabc8f4",
        "T009_07",
        "513e07af-5b71-5e0e-9266-2531463e33ee",
    ),  # s68
    (
        "97882ec1-695a-59ef-bf5b-93b280a73bb3",
        "T009_14",
        "f4217280-c3d9-5a32-aa3d-980bbaa14c7d",
    ),  # s69
    (
        "b26d4a7c-010d-5657-b467-a2fe1b791dda",
        "T010_06",
        "a9d76276-2035-5d35-92c4-fb286f7ed4ef",
    ),  # s70
    (
        "66535dd6-dc58-5244-9e6b-fcd9ef671b86",
        "T010_15",
        "3419116b-834c-5f5f-8aec-7cbb38ffe07d",
    ),  # s71
    (
        "a70d5e87-0ed3-5034-82d1-c24026df0b57",
        "T010_18",
        "409996c6-8fd8-5653-bc9c-c451de4d071a",
    ),  # s71
    (
        "cc1cae4c-e207-51f7-8045-c497907b6dcb",
        "T010_16",
        "2ecb5941-abee-57ac-b769-dbfa11eec96a",
    ),  # s71
    (
        "1881f959-46ec-5396-9e52-ade4c81126c3",
        "T011_06",
        "8d74d6f9-88b5-5a81-be0b-c0b373913121",
    ),  # s72
    (
        "3105f27e-0db8-5931-83ed-fd61ad7e44f3",
        "T011_08",
        "734bd93a-e413-5126-923e-198508cb9072",
    ),  # s72
    (
        "5f81900c-6044-59c6-a93b-ef08f2cc4f3c",
        "T011_09",
        "366aee6d-e340-5d37-955b-6b69111893a8",
    ),  # s72
    (
        "609aefa4-68f0-5750-8013-fd0ab11470c0",
        "T011_04",
        "0b2df435-4d61-53e1-a4eb-987bf39de26f",
    ),  # s72
    (
        "7979af5a-0acc-5c30-886a-0d913af429a9",
        "T012_01",
        "515ade0a-a0da-5813-b0d8-2c9975b47e81",
    ),  # s74
    (
        "b5285fa1-a055-52e5-8de5-cde4e69633ab",
        "T012_04",
        "fec0ed8e-959d-5c29-93ae-7dba79635b96",
    ),  # s74
    (
        "ce279133-51f1-51c2-8f3a-09dc630ec303",
        "T012_02",
        "c1848ecf-db94-55e8-bcd4-734c31b1b714",
    ),  # s74
    (
        "2811c487-ac1c-5d72-999d-a7a45201236e",
        "T012_15",
        "fe7532d4-63fb-54c5-8abb-b6b970dda8f6",
    ),  # s75
    (
        "327b65cf-201c-54bd-82ec-b4dc48c4c218",
        "T012_13",
        "4cb00386-d1c9-5aa7-8a63-b89b391e780b",
    ),  # s75
    (
        "4a6593ab-bf1e-5682-a9ad-11490eb9e4d1",
        "T012_12",
        "a5b59799-1159-514d-91b2-0b52a29be02e",
    ),  # s75
    (
        "2d2c7aef-bb52-54c5-8353-8b4282b7df33",
        "T013_07",
        "923f4728-a817-5548-bf4e-01d342a6190b",
    ),  # s76
    (
        "9e68e4dc-2eab-5295-9c30-5afd1aab3849",
        "T013_06",
        "052ce41f-284b-5af7-b503-1140972ef08c",
    ),  # s76
    (
        "2f2db50c-2151-57ee-ab9d-5ad42eeea727",
        "T015_05",
        "23c147ec-c101-559f-b9cb-2080d68be4d3",
    ),  # s105
    (
        "587e1a82-f97c-558a-8305-c090a817b89d",
        "T015_01",
        "27d96f2f-efde-5e25-b5d6-bb3e58781964",
    ),  # s105
    (
        "1ddb9d55-f940-5510-af64-34bf9e01d45f",
        "T016_04",
        "d9dcb8fd-c51b-5f29-a143-2c6cfecf402a",
    ),  # s107
    (
        "39f256eb-38ab-5cab-81b2-3bc560363c56",
        "T016_03",
        "62d8d76e-9bf5-588b-a38b-6aed734f5a1f",
    ),  # s107
    (
        "75f1a768-1148-560f-a7fd-1fe2d26a0765",
        "T016_02",
        "3eff6612-d744-556c-92f5-d549fc669769",
    ),  # s107
    (
        "baf867bf-a2a2-5e67-8165-fb733f7db95f",
        "T016_09",
        "11a8574f-c0c0-5126-949a-1f4be6c3287b",
    ),  # s108
    (
        "f0f65abf-ba58-5316-9194-419db27a71a3",
        "T017_06",
        "7f48d300-46de-5d4a-930a-9008d5012ba1",
    ),  # s109
    (
        "919a9c41-8b3c-5c44-b878-8cf241282800",
        "T017_11",
        "6ddfb8a3-49d1-5159-a355-7e568ec8ca4e",
    ),  # s110
    (
        "cf6c4c9e-52f7-50cb-ba87-d2b97579a75c",
        "T017_12",
        "857bf9a2-4348-5618-83bd-de9afe18384f",
    ),  # s110
    (
        "f45997b5-6a37-59cc-8d12-6fec1e083a55",
        "T017_08",
        "329f75e8-9972-59c3-91e3-b4964889650b",
    ),  # s110
    (
        "cd5be9ee-14de-5ab2-9bf7-3cf5181c1bfc",
        "T018_11",
        "316bd741-c1ed-5837-9796-40e28871852b",
    ),  # s112
    (
        "31d68c59-d796-5fc6-b80d-c28fd63ea3be",
        "T019_05",
        "e44eabf1-6454-5620-87bd-c2dd6afbb258",
    ),  # s149
    (
        "6b624f17-689b-5175-b922-3eef80af2825",
        "T019_02",
        "70ce4e2a-e975-5a7f-83d6-3136e59397a1",
    ),  # s149
    (
        "7efffc1e-43a3-5d52-a613-aa43ee68a3b6",
        "T019_03",
        "79a22a7e-90aa-5a36-ab5f-e21127688436",
    ),  # s149
    (
        "41e99f94-4372-5b31-8732-0638c409e349",
        "T019_13",
        "b060425b-26ae-5ce2-b6aa-e2dd4075d4e5",
    ),  # s150
    (
        "9dfabb9d-945a-5255-a55a-83f75fa84484",
        "T021_01",
        "5f6f8cb0-1810-5643-b733-a4ff60a5b602",
    ),  # s153
    (
        "638b606d-49c3-5ba8-846a-9b16ffc7cb9e",
        "T022_08",
        "1e3a47d4-2172-57aa-9c48-881ffefdf0bb",
    ),  # s155
    (
        "84573bf7-4c11-5c32-99e5-4bef91fe22da",
        "T022_03",
        "bd8bfdd8-960b-5c51-9f14-67650310711d",
    ),  # s155
    (
        "e011c3cc-e666-5a39-9252-e1126333ab84",
        "T022_07",
        "0ae3c020-b408-5808-be6b-c34e4811dc1e",
    ),  # s155
    (
        "be32c38f-8e64-5e41-b71a-02d5e300b250",
        "T025_07",
        "cd7e7012-2256-5304-af14-3c3c5b5fae7e",
    ),  # s161
    (
        "63ba038e-5d88-5cb6-a321-f326de27ee3d",
        "T026_02",
        "556e1f36-df3b-505c-8e8f-690e6ad4896d",
    ),  # s163
    (
        "817be286-47c9-50d3-a18e-c812c5ea1b01",
        "T026_13",
        "d0c54861-0519-5c1d-8423-1e6147e9814f",
    ),  # s164
    (
        "1d2820b1-d34e-52f5-8d1d-3e1071c337dc",
        "T027_01",
        "42a8fac9-dcfd-5507-85fc-85f1c27b7f0c",
    ),  # s185
    (
        "403b0cb0-8c15-58ee-b990-8a2b9272bc7e",
        "T028_15",
        "bb1cfd4b-da1c-58e2-9573-fb828ab80bfa",
    ),  # s188
    (
        "cfce1482-478c-57b6-a621-fb7dd625f3e7",
        "T028_09",
        "6475a6aa-107c-57d2-b5a2-8c90d3e7fce5",
    ),  # s188
    (
        "df8b293b-77b3-55bc-9188-f602afbb71a9",
        "T028_11",
        "ad394f1b-b32e-5efd-9b7e-82aaa4d483a6",
    ),  # s188
    (
        "2a825882-63aa-58f0-a7bd-c0bf4a47c7fa",
        "T029_01",
        "7cd7fae7-2cee-5d01-9b2e-b35e77de3b1d",
    ),  # s189
    (
        "ea8c10bc-2cc6-57d8-b556-0dd02ef290a0",
        "T029_05",
        "b9ae3e11-ca3c-58c5-87aa-7c127f12ca90",
    ),  # s189
    (
        "0b4a3663-3dd3-56cd-919e-1217905fa2a4",
        "T029_14",
        "bc32138b-8a0c-5945-b3eb-7e0367a90c40",
    ),  # s190
    (
        "7f38b6b3-4606-5a11-a814-fa95e797af1d",
        "T029_12",
        "dc67c44e-974a-5320-aa45-0a1ad61210cd",
    ),  # s190
    (
        "a8adf4bf-20d5-5d7b-952a-7bf301f4b45c",
        "T031_02",
        "cde906d7-f896-5b86-94d2-5419de383214",
    ),  # s193
    (
        "38f5b522-f4f7-5aa2-86b9-39b5fabb7cb2",
        "T033_03",
        "7392bbf1-8dc3-5942-85d7-9d91b6e94cd8",
    ),  # s206
    (
        "88d03140-0678-54ea-a9b0-7d8038137626",
        "T033_04",
        "37ab9ec3-8847-55f0-bcac-b67305d0ee1b",
    ),  # s206
    (
        "31ba3375-23f3-5d1f-99f4-5899724e9389",
        "T033_14",
        "16c18aa6-b148-57ab-879c-c1c20fb49a3d",
    ),  # s207
    (
        "679b73c4-80b9-5e19-bab4-45bf20274c41",
        "T033_13",
        "d03d824d-d9b6-5b9f-85af-1a30daee7238",
    ),  # s207
    (
        "8e94fbd3-3f63-55c9-816d-20dddcb8b7b4",
        "T033_12",
        "cf8c74b4-956c-5ae6-9e0c-8364cc99daa6",
    ),  # s207
    (
        "d4e677af-f667-5abf-b469-cbad10208d6b",
        "T033_11",
        "273a25fe-598a-53cf-9367-225c6d890548",
    ),  # s207
    (
        "ef4aebaf-e467-55a7-b090-c068a16de82f",
        "T033_09",
        "e3200bea-b89e-5a5c-97e3-ad561222dceb",
    ),  # s207
    (
        "86ffcf17-3339-56a5-a974-54a900a97380",
        "T034_03",
        "dc583170-4863-5884-80c6-c86e2a3b4df3",
    ),  # s208
    (
        "cb750f18-0f7f-57b2-98e0-6ac8561388c8",
        "T034_06",
        "d1765436-1d10-55c8-b9be-2d86405246da",
    ),  # s208
    (
        "221246b9-1ffe-5552-9c4a-1be822f042d2",
        "T034_12",
        "03b32426-69f0-5c72-a6f1-ccec4d00af0e",
    ),  # s209
    (
        "2622dec8-9163-53ab-9765-dbc4d8b496b0",
        "T034_11",
        "83cc80f0-ed15-549c-b12c-20adc089364d",
    ),  # s209
    (
        "398eb50f-244a-5f21-91b3-9e8d7d5037f4",
        "T034_07",
        "cadf5731-eeca-55d7-996b-b8c00607b676",
    ),  # s209
    (
        "8cd25fe2-4b2d-5b59-9454-e92a41299c8c",
        "T034_13",
        "f3611eda-6137-5a23-bfd8-523d26eb81b8",
    ),  # s209
    (
        "f8f7d762-29e3-5f65-bdb7-4d8b36b3ea69",
        "T034_08",
        "c28978ee-4e0c-5357-996a-87f6dc9c4c02",
    ),  # s209
    (
        "cf27d48a-db5a-5d0d-ad7f-c4fbc7939473",
        "T035_03",
        "85341da7-f848-5bec-a65c-7e00417ce4e5",
    ),  # s222
    (
        "f4978caf-a13f-5753-896f-99ad29016045",
        "T035_01",
        "8a164e60-aeed-5413-a521-123846ee75c6",
    ),  # s222
    (
        "29417b4f-7ab2-5f61-a0fa-438253f29fb0",
        "T038_09",
        "f4d83d54-29b8-5aed-802a-24870db39f40",
    ),  # s239
    (
        "31e76c36-cbb0-57d7-b5e3-0c4b6f79f441",
        "T038_02",
        "a317c889-474b-5779-bb21-7427db89d6b1",
    ),  # s239
    (
        "6fa5e72a-17a6-59ac-b855-41270c971638",
        "T038_07",
        "0f13ace4-05e5-5d6f-94a8-71e1e0cfbe2e",
    ),  # s239
    (
        "7bf3ecaf-bc66-5711-8923-6c790087674f",
        "T038_08",
        "a9cc80e7-9249-5e7e-9b87-9264780f2fda",
    ),  # s239
    (
        "913156b0-c16f-5974-9f8c-9ba5b43b20cc",
        "T038_05",
        "a32205f9-e12b-50b5-b4c2-778c6537d7a5",
    ),  # s239
    (
        "9ac0d8e3-bc71-5e50-bf83-0cd1c8bcb8d1",
        "T038_04",
        "a16ba3dc-b0ba-598d-9777-1eaa79462a8d",
    ),  # s239
    (
        "a8b8c8de-675d-5336-902f-990e3d16b066",
        "T038_03",
        "b49d9198-1ba2-5ec2-91b9-bad167318262",
    ),  # s239
    (
        "04fc270a-ae77-5e77-a085-ed76459e03b6",
        "T038_19",
        "897d0f7b-dfeb-519e-ac65-d76f3b031465",
    ),  # s240
    (
        "dab8002f-6d30-550d-aa88-a4024cbbd9e2",
        "T038_16",
        "ec2d9724-9ce3-5320-8e1b-a98af685ebad",
    ),  # s240
    (
        "4c10e0e4-5754-50ef-ad47-5401644b2f27",
        "T039_09",
        "1f409979-14f4-549b-81fb-edf3856c40ff",
    ),  # s242
    (
        "5f8f46e8-591d-5aa4-bec5-8df17e32314e",
        "T040_03",
        "16c8fd03-dd88-5752-8bff-bd91b53e2abf",
    ),  # s243
    (
        "b9b89b8b-94ea-5581-97e2-21e6d9fc7743",
        "T040_08",
        "e7417f69-f8bc-5cfb-9764-32ced1ac82ec",
    ),  # s243
    (
        "7b12a64a-cb8a-5b9b-b65c-f750a46613d3",
        "T040_14",
        "9a21c1a8-5cd2-5547-80cf-d8db3ce5c0d2",
    ),  # s244
    (
        "c0344c9e-e7ca-519c-b855-c6c779949aab",
        "T040_15",
        "a2ba91de-eb9e-5039-bd80-5942fef90e6d",
    ),  # s244
    (
        "844ebcb9-7e2f-5cdd-85d1-c12982fd3f8e",
        "T042_12",
        "877f4777-a367-53ba-8552-1aaa89bf5ec3",
    ),  # s256
    (
        "20d1cfcd-1569-50da-9411-642f71f36685",
        "T043_11",
        "0cd18fa3-c831-55d7-a9a2-934e18f38f8d",
    ),  # s258
    (
        "2f7ce72f-c925-5cfd-b3fb-43b4fd6c9a9b",
        "T043_10",
        "5f418890-3e81-5d50-bb20-4664f025640e",
    ),  # s258
    (
        "4a544fba-5a28-5faf-8672-0a8a992762be",
        "T044_16",
        "b174bb99-8b1c-5a83-b290-4936e57b643e",
    ),  # s272
    (
        "90b650c7-4f9c-5d55-b6ab-438b5748f8d7",
        "T044_09",
        "833231d1-67d3-5487-a556-8c98921ebe5c",
    ),  # s272
    (
        "6b58505e-b4fb-5e5f-8a23-91c5376c694a",
        "T045_04",
        "01aa5909-e4a6-5696-8dbd-e3bb73aa1d53",
    ),  # s273
    (
        "c52860db-12fc-5763-8156-058ff7e739e0",
        "T045_07",
        "3d5dbe24-877f-5d83-b10b-9c934ddbf84a",
    ),  # s273
    (
        "a214b7b8-9933-5f5f-8dbe-b13a4eeb64e9",
        "T046_06",
        "110b06a4-64cf-5bc7-9a86-5cae694b7344",
    ),  # s275
    (
        "245b9800-1579-5d05-b048-372d38a01fb5",
        "T046_12",
        "b1ddfea8-52c9-5f2b-b844-5164184b0676",
    ),  # s276
    (
        "44195d00-e964-52fc-a040-d65b8a3d581c",
        "T048_05",
        "1450b729-f611-5bdc-bc6e-63256e11a204",
    ),  # s299
    (
        "5d7c68f7-1742-572f-b184-0850d92ef2d7",
        "T048_02",
        "9aeb91b5-1fcc-5228-896e-d906fec744cc",
    ),  # s299
    (
        "8ea6348c-0c5b-5d66-8369-76b92920fe5f",
        "T048_12",
        "ce56e773-d664-59ac-a30c-cc55f70f52da",
    ),  # s300
    (
        "92428466-3d22-58bb-994d-2c9e12edb831",
        "T048_09",
        "6b11d987-afbd-53fb-bb8d-8226b698d8a3",
    ),  # s300
    (
        "9e5e1560-b9fc-512a-9b29-b6d1019119a3",
        "T049_09",
        "3faef080-1932-5332-8611-4876be8ce642",
    ),  # s302
    (
        "8ccfa4a5-cb1c-5ef9-96b5-316725ee7ad6",
        "T050_06",
        "d0623455-3b76-56e8-944d-28222e46c391",
    ),  # s303
    (
        "d62b2637-0b49-5866-bb58-9f3e92034453",
        "T050_02",
        "4c06b5eb-3ce9-520a-9cde-8a8fa577da6d",
    ),  # s303
    (
        "f05d5f73-9892-5754-831a-9279974020bb",
        "T050_07",
        "2715f343-d457-5f47-a607-1cbbde4edc1c",
    ),  # s303
    (
        "05dde39d-6d22-5588-a7e6-8fec79110487",
        "T052_03",
        "bdd6b800-8a31-5c29-a07a-7479b113cf9f",
    ),  # s307
    (
        "3bd9619a-6828-57ce-a71f-b07f59681c9c",
        "T052_04",
        "53822fef-615e-5b58-a4f3-fe04d6b2b03c",
    ),  # s307
    (
        "44908565-a375-5ea4-be66-845987891d43",
        "T052_09",
        "e4d70f37-4057-5774-a3da-bc271b9dfd82",
    ),  # s308
    (
        "9d6c413c-58e4-51d8-bbc9-7360b0d527b3",
        "T053_03",
        "fa06395d-48e2-5d6b-b5e7-ca1d298ddbd0",
    ),  # s333
    (
        "c00ae239-d677-50ab-a462-1e252dead99e",
        "T053_02",
        "06ca1a82-b4fa-5ce7-9fea-5b6bf2d2627c",
    ),  # s333
    (
        "f2184323-73f3-5880-aff2-9c91d8f796aa",
        "T053_07",
        "f72b6bbc-22c9-571b-8d41-261564a7e52b",
    ),  # s333
    (
        "18228dd2-7ffb-5f34-b2b1-2c9171a6b2a3",
        "T053_09",
        "a761407e-44e0-525a-b2ca-022fa7a10b1e",
    ),  # s334
    (
        "49b812a6-d665-5219-8afa-0d8761922bf9",
        "T053_10",
        "557df21a-d348-5749-8740-85ee2fced4fd",
    ),  # s334
    (
        "705c94d1-863e-5b4c-8565-f9ca3b046594",
        "T053_11",
        "09430213-d3cc-5ac4-be6b-9fa27c99ea45",
    ),  # s334
    (
        "f1a5d636-27e0-56da-a9c9-14330b7efd88",
        "T053_12",
        "11fc0533-8542-5bff-b0c2-a1d16204cdea",
    ),  # s334
    (
        "05f023e2-ac1e-57df-90e7-4e12516721ee",
        "T054_05",
        "d8c49217-8af1-56f0-97f3-d9ff66dffbcb",
    ),  # s335
    (
        "9d33b753-87d1-537d-b534-eded947ccad0",
        "T054_03",
        "17a7b5a7-d64a-5227-9ad5-c73db9613d96",
    ),  # s335
    (
        "c4910b29-9d5c-56c8-8dc7-4be930945816",
        "T054_02",
        "2f16dd6b-1db3-5ecd-a850-c42ab4c85b1d",
    ),  # s335
    (
        "10301214-d170-5e84-8f81-ae63dd6d4488",
        "T054_07",
        "900633b2-a1ef-543b-92e3-078fbb1b1b0b",
    ),  # s336
    (
        "83d9e838-ca8c-5f2f-a417-a27f3e81d0c0",
        "T054_14",
        "531b9eb5-033c-510e-8ffd-c528e3640763",
    ),  # s336
    (
        "a603a012-649f-5a6e-8bbd-d51067914275",
        "T054_12",
        "132cffaf-cd80-5cbd-a3fe-f90bf094d889",
    ),  # s336
    (
        "ddef9c78-1240-5839-809b-3678f1d06ce3",
        "T054_09",
        "6a70fa9d-207d-5007-b926-26e8613cb31b",
    ),  # s336
    (
        "e123c367-714e-5f1b-bb11-50390da84887",
        "T054_10",
        "f66affcc-822e-5396-aa2d-4c3d5643342d",
    ),  # s336
    (
        "17c70233-dae6-5702-bfeb-945fe38c642a",
        "T055_03",
        "3e390d6c-6cec-5699-80f8-16d0919d4143",
    ),  # s337
    (
        "74dd39fa-c2b2-5f3b-85b7-2a0ac30e9551",
        "T055_04",
        "d640d963-b801-5987-8217-15411d0dc43b",
    ),  # s337
    (
        "5db7e5a6-3790-51ce-a2c3-eb586d9995d9",
        "T055_09",
        "a8b8e4a8-8397-5fe7-a96d-b99d1f9bea75",
    ),  # s338
    (
        "61d2de93-7d38-50b9-ae1f-60bf11700758",
        "T055_10",
        "0caa06a4-7bfe-5504-9ebf-ed790f2af81d",
    ),  # s338
    (
        "ce92d7c1-5b4d-5049-9daa-0f4538a861a1",
        "T055_12",
        "0616416b-5599-5a3a-b2ce-e8a4f62827a7",
    ),  # s338
    (
        "f4cc144b-aeff-5aca-a8a2-faf5756431b8",
        "T056_01",
        "6e038be4-3f1d-57a0-96b7-f3ca51452c11",
    ),  # s339
    (
        "8106cacf-6e50-5f4c-8e31-fdaaf82aeca4",
        "T056_08",
        "6d9b2179-cdbf-5132-95c9-5a3421121732",
    ),  # s340
    (
        "e4ff4da6-e780-55bc-8146-df3511de5313",
        "T056_09",
        "576154e1-cc86-5144-adb7-03ef38f3d1b9",
    ),  # s340
    (
        "f23a8a27-9766-5fd8-9027-ea783a72ffb4",
        "T057_09",
        "de261aac-8a28-51da-9d46-7c757c1778af",
    ),  # s342
    (
        "fcdcfbe7-a28d-5098-9875-ad9c1c895a08",
        "T057_12",
        "d0ae4361-01f0-5b92-8f42-1a99fd42ed85",
    ),  # s342
    (
        "57b77f17-221a-511a-937e-99c8f78fd062",
        "T058_01",
        "6597b7f9-a8f6-5d07-a864-d7265683d561",
    ),  # s343
    (
        "8f8a1b24-d7a1-5890-bc54-6360883ddcef",
        "T058_02",
        "7a8a2850-d188-52d8-a983-b13fd7656ba0",
    ),  # s343
    (
        "21dbde28-8042-5f9c-8a29-7ff73a429998",
        "T058_08",
        "4d93f1eb-8cd5-58ee-a49a-b094ac3fbdff",
    ),  # s344
    (
        "042e4952-59b5-514c-92b4-9beaa63cfb91",
        "T059_03",
        "b2589662-a565-584d-b162-432aa1d0e78e",
    ),  # s363
    (
        "5125cc3a-d138-5a86-adb8-069f329980b5",
        "T059_07",
        "546a4177-66ff-5077-b9d1-c69ea29d7906",
    ),  # s363
    (
        "73ac9e85-f2f6-55f6-8042-c5f2404ab33b",
        "T059_08",
        "90ec6d8a-b0e5-5ea7-be52-e8789d07239a",
    ),  # s363
    (
        "fd5e8446-d3f9-5808-a4fc-c13a1e6b346d",
        "T059_01",
        "81caa12a-8daf-5160-8e29-020142450b15",
    ),  # s363
    (
        "0697a9ad-ff5e-5a36-90c2-5175aaab4dd9",
        "T060_15",
        "c76a1276-5952-56eb-a128-910ac0bbceff",
    ),  # s366
    (
        "f23ba1ba-3dc3-5752-bf95-00af31099db8",
        "T060_16",
        "88c29a51-6a7c-5e45-bcda-bba783dd16b6",
    ),  # s366
    (
        "62653443-68bd-57cb-b58b-e669be4a3e30",
        "T061_08",
        "3463fb1d-ac25-57be-8cd4-ed2e91991514",
    ),  # s367
    (
        "ef3ca295-3605-57ab-8211-1b11ada460ce",
        "T061_04",
        "be8877cf-0d95-5fe7-94ce-0dda2fa94b83",
    ),  # s367
    (
        "a1f0f2e0-669c-5668-866d-fd980c09a555",
        "T061_09",
        "07b05237-247f-5d82-a65d-60bbae92c031",
    ),  # s368
    (
        "da1ed2af-6b72-540c-9798-ed418e679df6",
        "T061_13",
        "dda2345e-9aa8-5677-b0f5-53b9797f1a78",
    ),  # s368
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
        _log.info("[0100] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0100] mv_safe_for_beta yenilendi")


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
        _log.info("[0100] soru tablolari yok (taze DB?) -- atlandi")
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
    _log.info("[0100] eski hat: %s aday, %s satir pasife alindi", len(idler), len(eski))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0100] %s yok -- downgrade atlandi", GUNLUK)
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
    _log.info("[0100] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
