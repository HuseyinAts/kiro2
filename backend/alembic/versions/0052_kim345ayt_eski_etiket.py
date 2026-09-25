"""345 AYT Kimya eski hat: TYT etiketi -> AYT, TYT konu dugumu -> kitabin dugumu, ikiz pasif

Revision ID: 0052_kim345ayt_eski_etiket
Revises: 0051_kim345ayt_eski_cevap
Create Date: 2026-09-25

SAHIP KARARI (25 Eyl 2026)
--------------------------
"1. bu ikizi pasife al  2. 118 satirin exam_type degeri ... COZ"

1. EXAM_TYPE
------------
Eski hattin (kiro2_batch_v4.14e) 345 AYT Kimya kitabindan gelen satirlarinin
268'i `exam_type='TYT'` etiketli: '345 2025 AYT Kimya Soru Bankasi' 118,
'345 2024 Ayt Kimya Soru Bankas<U+0131>' 150 (ayni kitabin onceki baskisi,
ayni kusur). Kanit (olculdu, 25 Eyl): kitap AYT Kimya (kunye + icindekiler:
12 unite, hepsi 11-12. sinif AYT konusu); bu satirlarin sayfalari kitabin
7-336 araliginda, 12 unitenin 12'sine dagiliyor; 268'in 244'u bu kitabin
modern ithalindeki bir soruyla govde Jaccard >= 0.75 eslesiyor (263'u >= 0.5);
grade_level hepsinde 12. Duzeltme: exam_type = 'AYT' (0009 deseni).

2. KONU DUGUMU
--------------
Bu kitabin eski hat satirlarindan 117'si TYT agacindaki bir dugume
(TYT-KIM-*) bagli; AYT etiketiyle celisir. Yeni dugum kitabin kendi agaci
(KIM-345A25, 0049), YALNIZ guvenli kanitla:
  * 104 satir: bu kitaptaki en iyi soru (Jaccard >= 0.75) AYNI basili
    sayfada -> o sorunun testinin dugumu;
  * 13 satir: sayfadaki tum testler ayni dugumde -> o dugum.
Diger konulu satirlara (KIM, KIM.ASI/DEN/ORG/TER) dokunulmaz.

3. IKIZ PASIF
-------------
0344bdd2 (2024 etiketi, s129 sag 6), 2e60703b'nin (0051 ile basili cevaba
cekildi) ikizi: ayni soru, sik D/E yanlis okunmus, dogru cevap ('I, II ve
III') siklarinda YOK. is_active = FALSE (silinmez).

GUARD VE GERI ALMA
------------------
exam_type yalniz hala 'TYT' ise; konu yalniz mevcut dugum kodu beklenen eski
kodsa; pasif yalniz satir aktifse degisir. Her degisiklik GUNLUK'e (id, alan,
eski_deger) yazilir; downgrade tam olarak onlari geri koyar. Konu sayaci ve
beta gorunumu yenilenir.
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0052_kim345ayt_eski_etiket"
down_revision: Union[str, None] = "0051_kim345ayt_eski_cevap"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "kim345ayt_eski_etiket_gunlugu_0052"
IKIZ_PASIF = "0344bdd2-b463-5b43-9dd9-8cf1190e48c4"

# exam_type 'TYT' -> 'AYT'
TYT_SATIRLARI: tuple[str, ...] = (
    "00f6711c-92ca-5784-b85b-a83b87e2d50b",
    "026dd722-3af6-58b8-84e1-a0432cf4f94d",
    "0271cfdc-5ef4-54a1-9ef4-8f06b780bed1",
    "0344bdd2-b463-5b43-9dd9-8cf1190e48c4",
    "05b7a417-9fbe-59c3-910f-733ddc083f24",
    "05c88626-8e89-514e-8ced-0d2d03e93716",
    "06b8a84f-a112-5fad-bb86-a984e9935e9f",
    "076f3caa-d8ac-5405-8b1c-f0d95bdc3d34",
    "096bab8a-dc45-57c6-84f6-8f8f4289f5ab",
    "09e7c691-8698-5bdc-98d7-1249777b5e3e",
    "0bf99906-211a-5991-b6fa-8d708c6eb3c3",
    "0daed2ae-3536-593f-afe9-cb8459e3169c",
    "0eef7922-37a2-5aad-a752-ff2df4bfe807",
    "0fc27aa3-ecfb-5051-b18e-f2c4f588bfbc",
    "1083c273-f019-5e04-8919-6ece5d001572",
    "118a2a68-432a-524b-90f5-ccbe4fbc2c82",
    "12b06ad5-8fa8-57dc-afeb-ba1f82dd8d8d",
    "12c0a22c-0c8f-5b52-94bf-d02b876b9bc5",
    "1351e889-a29a-5fc1-bc22-5cf7a19996a1",
    "1444e6b4-54c7-5cd7-81c4-2b339b3a25ed",
    "1446f71d-b92f-56a1-addc-d922cfa76e18",
    "14ba129d-7e93-5e17-b074-de194ae4b72e",
    "1522c319-d43b-525d-9d29-03d84fddca5a",
    "155771f6-ebbb-56b9-b756-ba26cb872111",
    "194025aa-d3a9-58a4-8c0f-dd21210c4c3f",
    "198fdd49-c6d3-5f8c-907f-c6d5bf8989d4",
    "1bd75049-04cd-5f79-8191-f3e8ce073522",
    "1c6bee78-ae55-50a0-87aa-595979f7cdce",
    "1cd47207-a0f2-5ba4-a203-d125a51d7b4a",
    "1e22d799-a225-5328-95a9-7ae8567d0ccb",
    "1f5062e0-76e3-55d1-b0f6-b7e3d6e94928",
    "1fe143e8-8833-5752-8c35-2800f7b3f115",
    "20838468-58a5-55b4-bb91-821637ef8954",
    "20c5e10b-cbb2-524b-a45c-a322683a2a22",
    "2267606d-b539-5983-8a25-c6911f26358c",
    "228e98b5-1dcc-5af1-93c0-2a4e5b351686",
    "22c2e992-7933-5330-9169-99848b00050a",
    "2367c084-f0f4-51af-a411-9574d1766285",
    "2546e81d-525f-51d4-869e-cea43c02008a",
    "26343e8d-2021-5a31-b095-3f2efddbe188",
    "26a1db42-03e7-5f4f-817e-8ec9f59ecdf4",
    "27fec0a8-2a93-5b3e-acc3-318ee6602384",
    "2855ce9a-7521-531b-981c-28ff088f9c2d",
    "298ec8e3-0376-5711-9636-301899e86932",
    "29bcaa0e-c5c2-565c-b21b-6f4b8c1cf5ad",
    "2b02aecd-8217-5e66-a526-12b151b5af95",
    "2b372c45-689f-5ebf-a6d8-bfc9fe9a37fc",
    "2cc6a251-48cb-5d28-854d-823e88deb7c8",
    "2de0ba37-30f7-5c3d-8d39-bd07b813c14d",
    "2dea63fa-4c2b-567a-b1be-63577d79c9bd",
    "2e0599bb-2024-5050-9858-0d7322f13532",
    "2e59d973-45c7-5392-b346-21db4591fc90",
    "2e60703b-ae1d-586c-817f-5c14cc4ad451",
    "2e92bb57-7353-5092-abeb-13bdd8bf4655",
    "30768661-fba5-5e43-bbe1-dc3f1a06173f",
    "30ab7521-e067-5381-990e-7460ea61966c",
    "311ec78c-9fc1-5e8f-b0c1-e82424c9ef80",
    "31526d49-6068-50a4-8184-bfc228bbdabb",
    "32d6d652-1d54-50ae-8f28-2b091367b261",
    "32e498b6-1a61-5704-a37f-e1e4a6134698",
    "32feec7d-6d43-5468-8128-67c80d99cd4d",
    "334d0f2b-c3e9-560b-bd6f-3bd6dc07992a",
    "33945cb9-3652-55ca-8903-177dfb40f088",
    "35219c9c-a1ac-589b-8cd9-8f4610732862",
    "3af9e838-0ac3-56a7-aff5-4b3a7d7267db",
    "3ceb4a65-ab42-50f6-8ea9-79182cabc2b9",
    "3cf6d874-77e0-5aac-8497-8f84f70f3baa",
    "3d25dfb6-7741-5738-9df2-d161ccfa1802",
    "3de682a9-ffe3-5c9e-bdc4-eb33a6bdad9e",
    "3facd187-99ab-5697-beca-4c9819017f6f",
    "3fd80502-baa5-5723-ae2f-1d08ba4c8c38",
    "3fe8aef1-1c15-5627-b577-bfe2d88e1764",
    "41f5ba11-ff74-514d-8f1e-728f637a9598",
    "4221d108-3187-54b3-ad20-b6298eab960f",
    "42a0af24-af2a-5d1d-9388-4efb1b5037b2",
    "42c653c3-27be-5dbd-a4bf-9cf9accd0344",
    "43a10f93-7ccd-5958-8ad4-6cb9415ba4db",
    "43de7e49-1d7f-550a-a1e3-8b031cf59e38",
    "449875f6-2313-51c6-801d-e50a373bfa7c",
    "44d7326f-ca4c-547b-9d91-0a8ecc13f9d1",
    "45990c64-f759-5777-8e33-c4ae4c77e4be",
    "45b9a0b2-4339-5aa5-8a13-d37cb66ec383",
    "45fe1ee9-bb1b-5dc2-9778-b0650c2a6a58",
    "4704595b-0292-5fc8-a4af-40c09ad11751",
    "47da24ea-e410-54df-8d21-a353891cdd53",
    "48d7ade0-cb3b-5c19-9df7-7785a5855854",
    "48f39015-c78a-5f60-bf18-b247158ab2dd",
    "4934ac5f-fda6-5b32-8fa7-68930acf55fc",
    "4a865065-484b-51e5-a2fa-e44fd5b71011",
    "4bc64d08-8efa-51bb-ad86-4ba2ac9b4c7f",
    "4e4e5d3f-2094-55a0-9c83-cd9a5f32dd41",
    "4f521899-9b94-5f09-a5d3-74f6eff0e86a",
    "510d6242-d013-593a-96b8-610f91f750e5",
    "5118ad62-bf5b-5097-a295-dce177e1fc6c",
    "543b3c12-49b1-56ad-be88-39fb5e81178c",
    "54dd0c9b-501e-552b-b973-798b0a5bb4ad",
    "54e0211a-1a88-5543-97ad-708e81ea11d2",
    "567144b1-9ac0-56da-b3d9-4ee7711b8e23",
    "573c571d-e02e-5206-a1f9-e707db390207",
    "582f1d3f-e5c2-5734-b74b-2abe214718b8",
    "58de7d53-ec5c-5e1c-9939-e8e37994c8b9",
    "5df2978f-205e-5074-a186-bf033bcb55ef",
    "5fe7bb0a-7710-50f9-9f48-0cecd1f9d62e",
    "6141057b-5e6c-5656-a009-07ad00c3a025",
    "61ace549-0c8e-5b9e-8b69-4b7f4a7b2b3f",
    "631db568-d5b9-51c0-94a8-49889f56e290",
    "63f58489-bf84-5f88-9d69-e29d85f0ef7b",
    "64203eb7-f54e-563f-b0c0-3f5639b51952",
    "6453cd45-1c4d-5b75-ae68-e6794bf56ef8",
    "64aa20c3-8d68-545c-9660-5b86a2a09840",
    "656054c9-c5c8-50b5-8061-c7e593147e2d",
    "65a28eb2-e2db-58cd-b74e-1880cbd8ec42",
    "669802bf-cbc4-5354-b37b-abb56b883065",
    "679fadc6-1a46-5141-885d-0d73cfdd4dfe",
    "697b176d-07ca-52fa-a0b0-9c142216ea1c",
    "69c7b35a-eed1-5563-8286-e954152b057a",
    "6a1f69fc-1a24-58a0-bc87-47f28eccfe3d",
    "6acc2cb6-3417-5a24-ac47-51ce9c976e06",
    "6bc055e4-c5c1-5a21-9250-d2a00f177c17",
    "6f5e772c-d67b-5242-94bc-1ec12d4c10db",
    "70f9b985-04ad-5a9f-836d-ce64bc52db14",
    "72b98dd6-5901-5c4b-97ba-7ca36574820c",
    "72f8551d-7535-54d7-a470-f9bfa4d08dc0",
    "73b034ab-f6fb-5ce1-94ee-12a600dcbc62",
    "75ac2fb8-31e4-555f-97a6-67b08c90fe43",
    "75c61b89-dc79-5393-a1db-779444db5760",
    "7645e06d-7d2e-5267-bec5-cbe8d99ad8d6",
    "7849efe2-db0a-5bb6-998c-e5f9b7db1fb1",
    "7937e6ef-9f1b-5807-bd9b-f00d59d97560",
    "7c224562-34d3-5496-9c31-65647f59e0a5",
    "7ceda6b6-9202-5ccd-8312-45a2e96dc370",
    "7ea278a3-5594-57f0-96cf-59e6991e4248",
    "7ff2b9d3-baa3-54b8-87bf-6f1836bbb219",
    "815c8cd4-56c6-50ca-a2f2-d88e4f08253d",
    "82c702e5-ca7f-5fb3-b9c0-73b260651d0c",
    "84bb774d-6dc4-54b9-bae0-8b4d73d6edda",
    "8501b633-3d34-5c16-aa93-b2d93b8353c3",
    "857c8690-2e85-5cea-bd62-71153ff18acd",
    "867eaeaf-6118-55bf-a1c3-07f77164d85b",
    "87473893-bb1c-59b1-97f2-538c3dced956",
    "8b6463e1-176e-5167-8547-180260db7efe",
    "8bb3884b-86d1-57c1-af7b-91070f9c44aa",
    "8f3445b4-1d9c-5b56-98cb-4356057b524f",
    "8ffc937f-5d65-59c2-9a2d-ec5fb6d1eb5a",
    "918c6823-bc2e-5826-9d31-51dac378f7bb",
    "922a02fe-6909-5667-a73a-269867629f8f",
    "92ab4dfd-ddca-592e-83d4-c4067767cf7a",
    "960e2fef-ca43-5234-a1f7-628c86558823",
    "96e9478b-399e-529e-a747-a488a02e8ab3",
    "97bac089-f3c0-5f90-add5-d3171de032fa",
    "98b94b3b-901e-5324-84a0-1d46c8a45417",
    "98f32942-3175-5401-a412-1d397aebbf48",
    "99c2c095-78d9-55f9-8cd9-88b5ba1db3d2",
    "9a265d7a-d3ea-5af9-ad03-3d55ecdfea02",
    "9d5ea4c6-3f0d-5ebd-88e5-890e5e6f858d",
    "9dbcbe58-91e1-5f61-89b3-ec5eb9ec30de",
    "9ea6c8dc-2c0b-5854-94af-5458945f8b3f",
    "9ec2b0a7-3e3d-5aca-9112-7b3b93b6222a",
    "9ee3eb4b-b959-5e77-b2f4-3c000d97ae81",
    "a09197bd-2aa4-57e3-a99f-6d20c13a57d1",
    "a0ee5afc-2697-5e46-ab8c-5cf3cf187dc1",
    "a3655f7b-0083-5af8-b586-edafcbe943a8",
    "a37d070c-6f1b-558b-9a15-dffe6b75534f",
    "a4df0cd1-acbd-53ca-a02f-0a3735e2aa00",
    "a5fa2347-fab6-5173-ab84-1071696560a5",
    "a65bf58f-d4d7-59dd-9249-f256e50e7bdc",
    "a6c77a3b-090f-5312-9139-d88637a3ce3d",
    "a723bb82-8de1-5bff-bdec-52c02243692b",
    "aa77719e-c665-5a33-8a0c-162740c96880",
    "aab40f0b-84ea-5401-8669-484f642d060e",
    "aba4c332-9518-5245-bc6a-39d9907380e3",
    "ad16e2cf-8007-59d5-aa49-8f1cc1cff2d1",
    "aeefe231-6641-583f-a9f7-c3d92e5f578d",
    "af8a1ca1-6083-5fac-b015-6ad4b5c44d63",
    "b0cc5880-f78e-5247-a236-d01a62a64b9b",
    "b1d6292c-66be-5631-bcb3-a8546a886131",
    "b29b2001-ae54-5d6b-8b48-3ae73210f82d",
    "b324d844-8525-5e86-9345-60886dc1ff84",
    "b4586be3-1163-505d-8fb8-2edc8f70f7a8",
    "b488648b-716d-5951-81b8-906e939a0c82",
    "b4aa8e72-ef3e-565f-af13-54094736316c",
    "b4d9f3e7-1f75-5f3d-8c5d-54a2f5e49b42",
    "b5596707-046b-5826-9991-66dd0529b3c0",
    "b567d806-cd8b-527c-ada3-850e9d4dd2a3",
    "b6869ac8-047f-578d-a6d8-327a23b4cd02",
    "b6b39e1f-367e-5ce9-be2a-3597bf89c859",
    "b8c63574-59f6-5549-9d2b-8ca3545a9738",
    "b8e94267-1398-510a-adfa-dd3f47baceae",
    "b98ba733-9a3c-5116-9dfb-7ceb17d4a8b3",
    "bb47dcda-2e94-59f0-81ee-7118ab932371",
    "bb89b184-fc9a-5b72-bbbd-0c87411bfed5",
    "bc5f24bf-ad64-550b-891f-36abb42250a1",
    "bd853fc5-496a-50cb-ae5c-9819bd219007",
    "c0a069c2-157a-54d8-a9b6-5c6c068269a1",
    "c32ac1e1-f9bc-5b54-b457-5817122cce16",
    "c345da0c-3791-57fc-814e-b43080854471",
    "c3b3d9e6-9267-58b1-a065-cd627df16310",
    "c6281d8b-f80a-56bb-b3bc-24184b1d6a63",
    "c81fb0cf-a12b-5b78-a862-9a8017035a09",
    "c8ce65c2-4e18-5afb-876f-beb13d25eb95",
    "c958787d-c3ca-5c42-98ef-3c44d5d3a315",
    "c9861032-56d0-5fdc-b78b-6047d904fb81",
    "ca9a7a9a-219b-53f2-9137-308fb3a6bf50",
    "cb2d4c88-292e-57e5-9b7d-febb9dd462cb",
    "cb525976-c3ce-56e0-823a-6ebc5cfec00d",
    "cbef7da5-bf53-5237-8839-bcafd21f9e6e",
    "ccfc94de-ea69-584b-b761-e31b1971297a",
    "cd226069-64a0-5c12-a860-37343733b714",
    "cde6b4cd-b0bd-51c8-be39-99c5140a5665",
    "ce7f53cf-df97-5e20-875c-fa65bfca3c31",
    "cf4788fc-3351-52f7-aca7-76da21b8a8b3",
    "cfefccec-78b9-5f3d-bbd7-cf5423819a99",
    "d00792d0-f3d2-5cff-854e-73a04534bf0e",
    "d0ad3b15-ea15-5c8e-9e9c-dda92f24da08",
    "d2f776f5-3aa1-57f6-878c-a3cabdc0c259",
    "d37d3b6d-4729-5401-baf5-e54e0284b35f",
    "d6e719d0-6fc6-51ae-b084-87ebe7e137a6",
    "d7b6b100-0258-57ea-b742-f8ef85634ceb",
    "d7e9d662-5cab-504e-bf12-eda54e8bd47b",
    "d9f74ba2-35c6-5801-9e92-2ff9c49706e9",
    "da340792-ca64-5da8-9a83-65892476b680",
    "db172e12-5157-5b68-8450-77ed1b466956",
    "dcdc4e24-f195-5225-8245-dcd67235e2a3",
    "dd818f20-9882-5464-ad39-9dad555cfdf2",
    "dd88b92f-91df-5ac8-a37b-e97b0bee8cab",
    "ddca17c9-5021-58ae-bcf8-d431c29716ad",
    "df755eeb-e8fd-54c7-a627-f2dc16629d5f",
    "df8dbe0a-988a-5591-880e-85f4d92a9dcf",
    "dff0462d-d77b-5006-a482-c4412fd8a5c6",
    "e00432bc-b008-56d8-9099-3f39311be225",
    "e0981318-1015-5464-bc9e-196a0f823255",
    "e0d73595-ee3f-5d5f-9c4e-9a28adf3bfe1",
    "e2078945-afa4-538e-963a-40cd87d881e6",
    "e2393425-91c0-5510-963a-b894d2ac506f",
    "e27b6ddf-5b25-5d3b-8cfa-fd8803bdde81",
    "e4dd1d25-6e2f-5d1d-8da5-755d0bfbb230",
    "e524a856-90a3-59a1-a8d7-2a1ea6331974",
    "e7b7d3d2-49ac-57b1-8740-f23478650409",
    "e80c64a9-28de-5c32-b5f5-de5bcca26cd4",
    "e8b2f6c0-c1ca-5867-8c72-0cc6b798b1bc",
    "e993a615-40dd-5d10-8fc7-74f780acc7cf",
    "ea4985a2-e381-539a-9ac7-fd9f142638ab",
    "eaf5c5ab-a398-5905-8ac6-66cdf34e80f5",
    "ed09ff89-a4c5-5db2-b4b2-34843e1534f3",
    "ee2e4158-5095-539f-bb65-9c7c366b74f7",
    "ee87c531-a5b3-59bc-b56c-d429cfbbb1d4",
    "ee8b9541-51d1-5a46-b512-f05a11aed484",
    "eed94d2b-48e8-5d70-9756-9ceb80eb24c5",
    "ef19b7f1-cab2-500a-93fe-cec644cf8419",
    "f065197e-9c5a-53e1-89b2-5d2ce88798d6",
    "f0a782b4-079c-5bc9-acf9-d890d4daa643",
    "f1473e9a-948b-5b38-9959-8ac32316c238",
    "f20a1655-8be3-5de9-8de8-24c1f2cd5f12",
    "f2fad265-5024-54ec-bf0f-0c16c3f23115",
    "f4bb0d59-b2de-5d7e-afa0-7c2ec8cd1b2e",
    "f9424b30-b4c9-5117-82d3-9d974fbd0f64",
    "fb243b2c-b0e6-5bce-814d-edb3980143a8",
    "fb683e33-9fae-54f9-83f0-8c584794cd91",
    "fc390f2e-6d87-5a45-b28c-776d7d56e0f0",
    "fcadc184-bfe2-5d65-8cd7-2cf43db86ec6",
    "fd2cc713-d87a-50f9-8b1c-7f91d62fb931",
    "fd91fae7-6e41-57b1-9f8a-406226b10097",
    "fddb9814-f2b6-5c48-877e-82b662826f5d",
    "fe0e7bc7-6296-5543-b963-11c7e9a75de4",
    "fe16c7ae-bc8f-58c5-9d64-38318baad541",
    "ff506061-317b-53ff-a9b5-48ae928d49f1",
    "ff9edbbc-304e-541c-bbdd-e5eeeae3367f",
    "ffe89404-14a0-5dbf-b1eb-6b6db1944af5",
)

# (id, eski dugum kodu, yeni dugum kodu)
KONU_TASIMA: tuple[tuple[str, str, str], ...] = (
    ("00f6711c-92ca-5784-b85b-a83b87e2d50b", "TYT-KIM-01", "KIM-345A25-U01-01"),
    ("026dd722-3af6-58b8-84e1-a0432cf4f94d", "TYT-KIM-03", "KIM-345A25-U03-01"),
    ("0271cfdc-5ef4-54a1-9ef4-8f06b780bed1", "TYT-KIM-04", "KIM-345A25-U02-02"),
    ("028ab719-3432-5ba4-8c82-48622c664417", "TYT-KIM-04", "KIM-345A25-U08"),
    ("03ada2b2-65ba-5af4-a88e-5f5cb3621d49", "TYT-KIM-01", "KIM-345A25-U01"),
    ("05b7a417-9fbe-59c3-910f-733ddc083f24", "TYT-KIM-01", "KIM-345A25-U01"),
    ("05c88626-8e89-514e-8ced-0d2d03e93716", "TYT-KIM-04", "KIM-345A25-U05-03"),
    ("06b8a84f-a112-5fad-bb86-a984e9935e9f", "TYT-KIM-04", "KIM-345A25-U03-03"),
    ("076f3caa-d8ac-5405-8b1c-f0d95bdc3d34", "TYT-KIM-04", "KIM-345A25-U08-01"),
    ("1083c273-f019-5e04-8919-6ece5d001572", "TYT-KIM-04", "KIM-345A25-U05-03"),
    ("118a2a68-432a-524b-90f5-ccbe4fbc2c82", "TYT-KIM-01", "KIM-345A25-U01"),
    ("12255307-3d54-59a5-b496-ddc945dc8746", "TYT-KIM-04", "KIM-345A25-U08-04"),
    ("12c0a22c-0c8f-5b52-94bf-d02b876b9bc5", "TYT-KIM-09", "KIM-345A25-U03-02"),
    ("1446f71d-b92f-56a1-addc-d922cfa76e18", "TYT-KIM-04", "KIM-345A25-U03-02"),
    ("1b321ec0-2aa2-5e62-9135-b2380f89a262", "TYT-KIM-01", "KIM-345A25-U01"),
    ("1cd47207-a0f2-5ba4-a203-d125a51d7b4a", "TYT-KIM-01", "KIM-345A25-U01-01"),
    ("1e22d799-a225-5328-95a9-7ae8567d0ccb", "TYT-KIM-01", "KIM-345A25-U01"),
    ("2112374d-5f2e-5aff-9675-cb40331b1d02", "TYT-KIM-03", "KIM-345A25-U09-05"),
    ("22a6b7c8-f580-5fda-9b45-cb90e7c1a934", "TYT-KIM-03", "KIM-345A25-U09"),
    ("2367c084-f0f4-51af-a411-9574d1766285", "TYT-KIM-04", "KIM-345A25-U12-01"),
    ("26a1db42-03e7-5f4f-817e-8ec9f59ecdf4", "TYT-KIM-02", "KIM-345A25-U01-02"),
    ("2937751b-dcd2-59b5-ad8f-ce347e20ff63", "TYT-KIM-01", "KIM-345A25-U01-01"),
    ("29bcaa0e-c5c2-565c-b21b-6f4b8c1cf5ad", "TYT-KIM-04", "KIM-345A25-U03-04"),
    ("2cc6a251-48cb-5d28-854d-823e88deb7c8", "TYT-KIM-04", "KIM-345A25-U10-03"),
    ("2de0ba37-30f7-5c3d-8d39-bd07b813c14d", "TYT-KIM-04", "KIM-345A25-U03-03"),
    ("2e0599bb-2024-5050-9858-0d7322f13532", "TYT-KIM-01", "KIM-345A25-U01-02"),
    ("2e59d973-45c7-5392-b346-21db4591fc90", "TYT-KIM-04", "KIM-345A25-U05-03"),
    ("2e92bb57-7353-5092-abeb-13bdd8bf4655", "TYT-KIM-09", "KIM-345A25-U03"),
    ("30768661-fba5-5e43-bbe1-dc3f1a06173f", "TYT-KIM-04", "KIM-345A25-U02"),
    ("311ec78c-9fc1-5e8f-b0c1-e82424c9ef80", "TYT-KIM-02", "KIM-345A25-U01-03"),
    ("31526d49-6068-50a4-8184-bfc228bbdabb", "TYT-KIM-03", "KIM-345A25-U09-05"),
    ("32feec7d-6d43-5468-8128-67c80d99cd4d", "TYT-KIM-04", "KIM-345A25-U03-01"),
    ("35219c9c-a1ac-589b-8cd9-8f4610732862", "TYT-KIM-04", "KIM-345A25-U08-01"),
    ("3af9e838-0ac3-56a7-aff5-4b3a7d7267db", "TYT-KIM-04", "KIM-345A25-U08-03"),
    ("3fbf19ff-3edc-59e7-b706-27f8b3699849", "TYT-KIM-01", "KIM-345A25-U01"),
    ("3fd80502-baa5-5723-ae2f-1d08ba4c8c38", "TYT-KIM-04", "KIM-345A25-U03"),
    ("3fe8aef1-1c15-5627-b577-bfe2d88e1764", "TYT-KIM-04", "KIM-345A25-U05-03"),
    ("42c653c3-27be-5dbd-a4bf-9cf9accd0344", "TYT-KIM-02", "KIM-345A25-U01-04"),
    ("43a10f93-7ccd-5958-8ad4-6cb9415ba4db", "TYT-KIM-09", "KIM-345A25-U03-05"),
    ("43be5863-d1a5-5c44-94bc-abeb74b744bb", "TYT-KIM-01", "KIM-345A25-U01"),
    ("44d7326f-ca4c-547b-9d91-0a8ecc13f9d1", "TYT-KIM-02", "KIM-345A25-U01-03"),
    ("45990c64-f759-5777-8e33-c4ae4c77e4be", "TYT-KIM-04", "KIM-345A25-U02"),
    ("4a750fa4-9951-57e9-8134-4fb331382c82", "TYT-KIM-04", "KIM-345A25-U08-01"),
    ("4f521899-9b94-5f09-a5d3-74f6eff0e86a", "TYT-KIM-04", "KIM-345A25-U03-03"),
    ("543b3c12-49b1-56ad-be88-39fb5e81178c", "TYT-KIM-04", "KIM-345A25-U02"),
    ("5cd23f09-bea5-5d64-991f-05ef1a662f11", "TYT-KIM-01", "KIM-345A25-U01-01"),
    ("61ace549-0c8e-5b9e-8b69-4b7f4a7b2b3f", "TYT-KIM-02", "KIM-345A25-U01"),
    ("65a28eb2-e2db-58cd-b74e-1880cbd8ec42", "TYT-KIM-01", "KIM-345A25-U12-04"),
    ("669802bf-cbc4-5354-b37b-abb56b883065", "TYT-KIM-01", "KIM-345A25-U02-03"),
    ("69c7b35a-eed1-5563-8286-e954152b057a", "TYT-KIM-03", "KIM-345A25-U11-04"),
    ("6acc2cb6-3417-5a24-ac47-51ce9c976e06", "TYT-KIM-11", "KIM-345A25-U12"),
    ("6bc055e4-c5c1-5a21-9250-d2a00f177c17", "TYT-KIM-09", "KIM-345A25-U03-02"),
    ("70f9b985-04ad-5a9f-836d-ce64bc52db14", "TYT-KIM-04", "KIM-345A25-U01-05"),
    ("715e8e11-a83a-5080-8a21-4b3a07eb21d0", "TYT-KIM-04", "KIM-345A25-U08-04"),
    ("72b98dd6-5901-5c4b-97ba-7ca36574820c", "TYT-KIM-02", "KIM-345A25-U01"),
    ("72f8551d-7535-54d7-a470-f9bfa4d08dc0", "TYT-KIM-02", "KIM-345A25-U01"),
    ("74af652c-f77f-5816-8368-08a53544a585", "TYT-KIM-04", "KIM-345A25-U08-01"),
    ("7849efe2-db0a-5bb6-998c-e5f9b7db1fb1", "TYT-KIM-01", "KIM-345A25-U01"),
    ("794e1e33-ed90-52b9-922b-5f758554febd", "TYT-KIM-04", "KIM-345A25-U08-01"),
    ("7c224562-34d3-5496-9c31-65647f59e0a5", "TYT-KIM-01", "KIM-345A25-U01-05"),
    ("815c8cd4-56c6-50ca-a2f2-d88e4f08253d", "TYT-KIM-04", "KIM-345A25-U03-02"),
    ("82c702e5-ca7f-5fb3-b9c0-73b260651d0c", "TYT-KIM-02", "KIM-345A25-U01-03"),
    ("8501b633-3d34-5c16-aa93-b2d93b8353c3", "TYT-KIM-04", "KIM-345A25-U08-01"),
    ("87473893-bb1c-59b1-97f2-538c3dced956", "TYT-KIM-03", "KIM-345A25-U01-05"),
    ("8b6463e1-176e-5167-8547-180260db7efe", "TYT-KIM-03", "KIM-345A25-U03-01"),
    ("8ffc937f-5d65-59c2-9a2d-ec5fb6d1eb5a", "TYT-KIM-04", "KIM-345A25-U08-03"),
    ("922a02fe-6909-5667-a73a-269867629f8f", "TYT-KIM-04", "KIM-345A25-U03-02"),
    ("944b2df5-68aa-5757-ab40-89c6b0f616d4", "TYT-KIM-04", "KIM-345A25-U08-02"),
    ("960e2fef-ca43-5234-a1f7-628c86558823", "TYT-KIM-03", "KIM-345A25-U03-01"),
    ("98b94b3b-901e-5324-84a0-1d46c8a45417", "TYT-KIM-04", "KIM-345A25-U05-03"),
    ("98f32942-3175-5401-a412-1d397aebbf48", "TYT-KIM-02", "KIM-345A25-U01"),
    ("9a265d7a-d3ea-5af9-ad03-3d55ecdfea02", "TYT-KIM-03", "KIM-345A25-U09-04"),
    ("9c695c02-87b0-5465-8571-6bec1b361d1a", "TYT-KIM-01", "KIM-345A25-U01-01"),
    ("a0ee5afc-2697-5e46-ab8c-5cf3cf187dc1", "TYT-KIM-01", "KIM-345A25-U01"),
    ("a2163253-086f-5f35-bca2-1e68a41c157c", "TYT-KIM-04", "KIM-345A25-U08-01"),
    ("a3655f7b-0083-5af8-b586-edafcbe943a8", "TYT-KIM-01", "KIM-345A25-U01-01"),
    ("a5fa2347-fab6-5173-ab84-1071696560a5", "TYT-KIM-04", "KIM-345A25-U08-03"),
    ("a6c77a3b-090f-5312-9139-d88637a3ce3d", "TYT-KIM-04", "KIM-345A25-U03"),
    ("aba4c332-9518-5245-bc6a-39d9907380e3", "TYT-KIM-10", "KIM-345A25-U02-06"),
    ("afa232f5-3dcc-5b06-807e-f4b1e60634a9", "TYT-KIM-01", "KIM-345A25-U01"),
    ("b1d6292c-66be-5631-bcb3-a8546a886131", "TYT-KIM-04", "KIM-345A25-U08-03"),
    ("b4586be3-1163-505d-8fb8-2edc8f70f7a8", "TYT-KIM-01", "KIM-345A25-U01"),
    ("b488648b-716d-5951-81b8-906e939a0c82", "TYT-KIM-04", "KIM-345A25-U05-02"),
    ("b567d806-cd8b-527c-ada3-850e9d4dd2a3", "TYT-KIM-01", "KIM-345A25-U01"),
    ("b8e94267-1398-510a-adfa-dd3f47baceae", "TYT-KIM-02", "KIM-345A25-U01-03"),
    ("bb47dcda-2e94-59f0-81ee-7118ab932371", "TYT-KIM-04", "KIM-345A25-U05-03"),
    ("bb89b184-fc9a-5b72-bbbd-0c87411bfed5", "TYT-KIM-02", "KIM-345A25-U01"),
    ("c0a069c2-157a-54d8-a9b6-5c6c068269a1", "TYT-KIM-04", "KIM-345A25-U03-02"),
    ("c32ac1e1-f9bc-5b54-b457-5817122cce16", "TYT-KIM-04", "KIM-345A25-U03-02"),
    ("c7ada458-3420-5d21-8bda-9cb3dd9f6d7e", "TYT-KIM-04", "KIM-345A25-U08-04"),
    ("c87972e5-fb62-5686-8cfd-08bb9cfcc838", "TYT-KIM-04", "KIM-345A25-U08-01"),
    ("c8ce65c2-4e18-5afb-876f-beb13d25eb95", "TYT-KIM-04", "KIM-345A25-U03"),
    ("c958787d-c3ca-5c42-98ef-3c44d5d3a315", "TYT-KIM-04", "KIM-345A25-U03-03"),
    ("cde6b4cd-b0bd-51c8-be39-99c5140a5665", "TYT-KIM-11", "KIM-345A25-U12-03"),
    ("cf4788fc-3351-52f7-aca7-76da21b8a8b3", "TYT-KIM-04", "KIM-345A25-U12-03"),
    ("cfefccec-78b9-5f3d-bbd7-cf5423819a99", "TYT-KIM-04", "KIM-345A25-U08-01"),
    ("d37d3b6d-4729-5401-baf5-e54e0284b35f", "TYT-KIM-01", "KIM-345A25-U01-02"),
    ("d7e9d662-5cab-504e-bf12-eda54e8bd47b", "TYT-KIM-01", "KIM-345A25-U01-01"),
    ("da340792-ca64-5da8-9a83-65892476b680", "TYT-KIM-02", "KIM-345A25-U01-04"),
    ("db172e12-5157-5b68-8450-77ed1b466956", "TYT-KIM-02", "KIM-345A25-U01"),
    ("e2393425-91c0-5510-963a-b894d2ac506f", "TYT-KIM-02", "KIM-345A25-U01"),
    ("e4158a98-cbeb-57c7-aaa7-4015fdc5812c", "TYT-KIM-03", "KIM-345A25-U09-05"),
    ("e4dd1d25-6e2f-5d1d-8da5-755d0bfbb230", "TYT-KIM-04", "KIM-345A25-U08"),
    ("e524a856-90a3-59a1-a8d7-2a1ea6331974", "TYT-KIM-04", "KIM-345A25-U03-03"),
    ("e90916a5-5f1f-5e45-946b-c30eecb24c80", "TYT-KIM-01", "KIM-345A25-U01"),
    ("eaf5c5ab-a398-5905-8ac6-66cdf34e80f5", "TYT-KIM-02", "KIM-345A25-U01-03"),
    ("ed09ff89-a4c5-5db2-b4b2-34843e1534f3", "TYT-KIM-04", "KIM-345A25-U05-03"),
    ("f0a782b4-079c-5bc9-acf9-d890d4daa643", "TYT-KIM-09", "KIM-345A25-U03-03"),
    ("f1473e9a-948b-5b38-9959-8ac32316c238", "TYT-KIM-01", "KIM-345A25-U01"),
    ("f20a1655-8be3-5de9-8de8-24c1f2cd5f12", "TYT-KIM-02", "KIM-345A25-U09"),
    ("f4bb0d59-b2de-5d7e-afa0-7c2ec8cd1b2e", "TYT-KIM-01", "KIM-345A25-U01-01"),
    ("f9424b30-b4c9-5117-82d3-9d974fbd0f64", "TYT-KIM-03", "KIM-345A25-U09-04"),
    ("fac2b601-2640-5636-8bf2-ba39004d4440", "TYT-KIM-02", "KIM-345A25-U01-05"),
    ("fcadc184-bfe2-5d65-8cd7-2cf43db86ec6", "TYT-KIM-04", "KIM-345A25-U08-03"),
    ("fcb576c2-ad22-558c-a83e-0d437ad947d5", "TYT-KIM-01", "KIM-345A25-U01-01"),
    ("fd91fae7-6e41-57b1-9f8a-406226b10097", "TYT-KIM-04", "KIM-345A25-U08-01"),
    ("ff9edbbc-304e-541c-bbdd-e5eeeae3367f", "TYT-KIM-01", "KIM-345A25-U02-03"),
)

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
        _log.info("[0052] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))


def _gunlukle(b, satirlar: list[tuple[str, str, Union[str, None]]]) -> None:
    if satirlar:
        b.execute(
            sa.text(
                f"INSERT INTO {GUNLUK} (id, alan, eski_deger) "  # noqa: S608  # nosec B608
                "VALUES (:id, :alan, :eski)"
            ),
            [{"id": s[0], "alan": s[1], "eski": s[2]} for s in satirlar],
        )


def upgrade() -> None:
    b = op.get_bind()
    denetci = sa.inspect(b)
    if not all(
        denetci.has_table(t)
        for t in ("question_bank", "question_metadata", "topic_hierarchy")
    ):
        _log.info("[0052] soru tablolari yok (taze DB?) -- atlandi")
        return
    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("alan", sa.String(), nullable=False),
        sa.Column("eski_deger", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", "alan"),
    )

    # 1) exam_type
    ayt = [
        str(x)
        for x in b.execute(
            sa.text(
                "SELECT id FROM question_metadata "
                "WHERE id = ANY(:ids) AND exam_type = 'TYT'"
            ),
            {"ids": list(TYT_SATIRLARI)},
        ).scalars()
    ]
    _gunlukle(b, [(sid, "exam_type", "TYT") for sid in ayt])
    if ayt:
        b.execute(
            sa.text(
                "UPDATE question_metadata SET exam_type = 'AYT' WHERE id = ANY(:ids)"
            ),
            {"ids": ayt},
        )

    # 2) konu dugumu
    kodlar = sorted({k for _, e, y in KONU_TASIMA for k in (e, y)})
    dugum: dict[str, str] = {
        str(kod): str(did)
        for kod, did in b.execute(
            sa.text("SELECT code, id FROM topic_hierarchy WHERE code = ANY(:k)"),
            {"k": kodlar},
        ).fetchall()
    }
    mevcut: dict[str, str] = {
        str(qid): str(kod)
        for qid, kod in b.execute(
            sa.text(
                "SELECT q.id, t.code FROM question_bank q "
                "JOIN topic_hierarchy t ON t.id = q.primary_topic_id "
                "WHERE q.id = ANY(:ids)"
            ),
            {"ids": [x[0] for x in KONU_TASIMA]},
        ).fetchall()
    }
    tasinan = 0
    for sid, eski, yeni in KONU_TASIMA:
        if mevcut.get(sid) != eski or yeni not in dugum or eski not in dugum:
            _log.info("[0052] %s konu beklenen durumda degil -- ATLANDI", sid[:8])
            continue
        _gunlukle(b, [(sid, "primary_topic_id", str(dugum[eski]))])
        b.execute(
            sa.text(
                "UPDATE question_bank SET primary_topic_id = :y, updated_at = now() "
                "WHERE id = :id"
            ),
            {"y": dugum[yeni], "id": sid},
        )
        tasinan += 1

    # 3) ikiz pasif
    aktif = b.execute(
        sa.text("SELECT is_active FROM question_bank WHERE id = :id"),
        {"id": IKIZ_PASIF},
    ).scalar()
    pasif = 0
    if aktif is True:
        _gunlukle(b, [(IKIZ_PASIF, "is_active", "true")])
        b.execute(
            sa.text(
                "UPDATE question_bank SET is_active = FALSE, updated_at = now() "
                "WHERE id = :id"
            ),
            {"id": IKIZ_PASIF},
        )
        pasif = 1

    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    _log.info(
        "[0052] exam_type AYT: %s / %s, konu tasindi: %s / %s, ikiz pasif: %s",
        len(ayt),
        len(TYT_SATIRLARI),
        tasinan,
        len(KONU_TASIMA),
        pasif,
    )


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0052] %s yok -- downgrade atlandi", GUNLUK)
        return
    kayitlar = b.execute(
        sa.text(f"SELECT id, alan, eski_deger FROM {GUNLUK}")  # noqa: S608  # nosec B608
    ).all()
    for sid, alan, eski in kayitlar:
        if alan == "exam_type":
            b.execute(
                sa.text("UPDATE question_metadata SET exam_type = :e WHERE id = :id"),
                {"e": eski, "id": sid},
            )
        elif alan == "primary_topic_id":
            b.execute(
                sa.text(
                    "UPDATE question_bank SET primary_topic_id = :e, updated_at = now() "
                    "WHERE id = :id"
                ),
                {"e": eski, "id": sid},
            )
        elif alan == "is_active":
            b.execute(
                sa.text(
                    "UPDATE question_bank SET is_active = TRUE, updated_at = now() "
                    "WHERE id = :id"
                ),
                {"id": sid},
            )
    b.execute(sa.text(_SAYAC_SQL))
    op.drop_table(GUNLUK)
    _refresh_safe_for_beta(b)
    _log.info("[0052] geri alindi: %s kayit", len(kayitlar))
