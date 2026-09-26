"""345 2025 TYT Kimya: modern karsiligi olan eski hat satirlari pasif

Revision ID: 0063_kmt345_eski_hat_pasif
Revises: 0062_kmt345_agac
Create Date: 2026-09-26

KARAR
-----
Sahip talimati (26 Eyl 2026): "345 2025 TYT Kimya, Sosyal Bilgiler ve
Turkce; ucunu de sirayla onay istemeden kesintisiz tam otonom isle".
Emsal 0058 (STM345 eski hat pasif, sahip karari). Bu migration SILMEZ;
yalniz is_active=FALSE yapar ve downgrade ile tam geri alinir.

NEDEN (Faz 5 olcumu, KMT_345_YONTEM.md bolum 5a)
-----------------------------------------------
Ayni kitabin iki eski aktarimi aktif duruyor:
    '345 2025 Tyt Kimya Soru Bankasi' (Turkce i)   294 satir, 294 aktif
    '345 Tyt Kimya Soru Bankasi' (2024 baskisi)     213 satir, 213 aktif
Yeni ithal (kim345tyt_ithal.py, 1306 satir) ayni sorulari basili anahtar,
iki bagimsiz okuma ve gozle hakemli metinle tasir. Eski satirlardan 330'u
modern bir soruya GUCLU baglanir (formulu koruyan govde 3-gram >= 0.9 VE
bes sikkin >= 3'u birebir): 211 + 119. Bunlarin 35'i modern soruyla AYNI
soru_hash'i tasir; tekil aktif hash kurali geregi eski satir acikken
modern satir aktiflestirilemez. 330 eslesmenin 19'unda eski cevap basili
anahtardan farkli.

NE YAPAR
--------
Asagidaki (eski id, modern kirpim) ciftlerinde eski satir is_active=FALSE.
Guard: eski satir iki eski kaynak adindan birini tasiyor, ithal_araci yok,
hala aktif, VE modern karsiligi bu kitabin ithal satiri olarak DB'de var
(yoksa -- taze/CI DB, ya da modern soru baska kaynakta tutuldugu icin
yazilmadiysa (T025_01) -- eski satira dokunulmaz). GUCLU eslesmeyen 177
eski satir AKTIF kalir (2024 baskisinin farkli sorulari dahil).
Degisen her satirin onceki is_active degeri GUNLUK'e yazilir; downgrade
onu geri yukler. Konu sayaci ve beta gorunumu yenilenir.

Revizyon adi 26 karakter (sinir 32).
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0063_kmt345_eski_hat_pasif"
down_revision: Union[str, None] = "0062_kmt345_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "kmt345_eski_hat_gunlugu_0063"
KAYNAK = "345 2025 TYT Kimya Soru Bankasi"
ITHAL_ARACI = "scripts/kitap/kim345tyt_ithal.py"
ESKI_KAYNAKLAR: tuple[str, ...] = (
    "345 2025 Tyt Kimya Soru Bankas\u0131",
    "345 Tyt Kimya Soru Bankas\u0131",
)

# (eski satir id, modern kirpim adi -- KMT345- oneksiz); kaynak:
# 345_2025_tyt_kimya_mukerrer_adaylari.json eski_hat, modern_karsilik=true.
# Yorum: baski (25 = 2025, 24 = 2024) ve eski satirin basili sayfasi.
ESKI_MODERN: tuple[tuple[str, str], ...] = (
    ("9ff0a777-1d44-5bd8-892f-652fb32062e8", "T001_01"),  # 25 s6
    ("03f252f2-9271-5064-9ce0-1ebd622918ff", "T003_04"),  # 25 s10
    ("a57a4e72-9bd4-5edf-b9e8-fffb1991e5b0", "T003_05"),  # 25 s10
    ("2cc9649e-6912-52d0-85a4-fc71b227944f", "T004_01"),  # 25 s12
    ("7b8474d4-474c-539f-a10d-142b5dff6d2b", "T004_03"),  # 25 s12
    ("0619010c-acfd-5e7e-9838-847f9f09803d", "T004_08"),  # 25 s13
    ("4db1624e-2106-5014-8503-cb3d0ae8a815", "T004_07"),  # 25 s13
    ("dd36e5cc-8158-5d8a-b6d4-fb973a16f639", "T005_01"),  # 25 s14
    ("9f7cfed9-a827-570c-8bb2-b4239e54f91b", "T005_10"),  # 25 s15
    ("fe83de00-de0f-5ac4-bbc7-ee1f27c007fd", "T005_11"),  # 25 s15
    ("c5668f36-25b6-5311-a1f9-a810b76ac5b6", "T006_04"),  # 25 s16
    ("83e52448-6e4e-54ad-b4b1-daf25e84bc3c", "T006_08"),  # 25 s17
    ("41def78a-7059-56e3-bd46-10acb0fa7a2c", "T007_07"),  # 25 s19
    ("2be7bda0-1496-5f74-8876-e794e7f29358", "T008_01"),  # 25 s20
    ("0c10ee52-5ba2-55c0-b500-d1e59fc858bd", "T010_06"),  # 25 s25
    ("4dbb3639-a4d7-585f-bb55-2039177c26a5", "T010_05"),  # 25 s25
    ("874ad7a8-adcb-54cf-80f1-fecc5d22601b", "T010_10"),  # 25 s25
    ("8973825b-8774-5ab4-a0ed-2585c10918c1", "T010_08"),  # 25 s25
    ("bdfad4f6-bea9-5d0c-9906-c9970eddc101", "T010_07"),  # 25 s25
    ("0dc8c66c-5386-56b3-b3a7-883aa45aa513", "T011_10"),  # 25 s27
    ("88a717e3-28f3-5d2b-a2a1-a1131b47facb", "T012_02"),  # 25 s28
    ("a66c1602-90b0-553f-ab5d-5323260cc423", "T012_03"),  # 25 s28
    ("4e5d414b-b88c-5bc9-8863-c99c85627440", "T012_09"),  # 25 s29
    ("66a8ef7b-7323-5eff-b9ca-63a275e8d87b", "T012_06"),  # 25 s29
    ("e0735ee4-ccf3-53ee-9375-6bf3f5b87686", "T013_04"),  # 25 s30
    ("033e23f5-09dd-5479-920a-3936049e9bc9", "T014_03"),  # 25 s32
    ("9ed27332-53b9-55a1-b563-75c05e207e43", "T014_01"),  # 25 s32
    ("5c2609ec-933a-51bd-91db-c58cefc156c9", "T016_02"),  # 25 s36
    ("6c20c24d-7c9a-545e-b448-864d80081e01", "T016_05"),  # 25 s36
    ("d6f7f0da-006b-5001-806e-164b76cbf675", "T016_01"),  # 25 s36
    ("61ff634e-36eb-5b39-91ee-5e2fdf1f7cd6", "T016_06"),  # 25 s37
    ("976def29-f816-5f89-84dc-fe06509e7da8", "T016_08"),  # 25 s37
    ("0ab8c226-be5e-59e0-b475-e16116c14473", "T017_04"),  # 25 s38
    ("473626ab-dc7e-5519-95f9-cdcd7a070552", "T017_03"),  # 25 s38
    ("0286b133-684f-5811-bf53-b17e0750673f", "T017_06"),  # 25 s39
    ("5a9b045a-1727-5126-b90e-c3c74d93d3da", "T017_05"),  # 25 s39
    ("7a636618-61d4-51c5-b636-73da26ee02d1", "T017_09"),  # 25 s39
    ("064cbb9d-9e53-5d39-aa12-35b6a51e18a5", "T018_12"),  # 25 s41
    ("285eda55-cf46-5c2a-8493-b97c9c9acf26", "T019_01"),  # 25 s42
    ("c9bbf022-56d6-560b-a948-c787defe11d9", "T019_02"),  # 25 s42
    ("f7e106c1-4adb-53c6-b29d-f5d1c2e7b34b", "T019_04"),  # 25 s42
    ("0619f608-15e6-5d63-8f36-836603b3f791", "T021_05"),  # 25 s46
    ("091721c9-3cc3-5d6a-bb8d-7d5e10e46f3c", "T021_04"),  # 25 s46
    ("311717fa-de81-5393-afb2-e5976b54d261", "T021_01"),  # 25 s46
    ("70e00ef1-901f-5d51-ba14-30e9ca92bcda", "T021_02"),  # 25 s46
    ("18c60df3-c253-5d0c-bfb8-afb415255dc0", "T022_05"),  # 25 s48
    ("683e4ed4-a11a-564e-bc16-04163b60f2f1", "T022_04"),  # 25 s48
    ("9867b60a-e254-589a-90f9-6baa90335c77", "T022_03"),  # 25 s48
    ("03a2e367-34ec-5781-8d5f-fa1c9d1091fc", "T022_06"),  # 25 s49
    ("8d6c12ef-718c-5999-aabb-7f04f74be36c", "T023_02"),  # 25 s50
    ("b63fbffc-016d-5f9b-85b4-51036a12dac5", "T023_01"),  # 25 s50
    ("448ce5b9-b814-5721-bf93-a192d1f645eb", "T023_08"),  # 25 s51
    ("e68b544f-90e7-5a78-aff3-85436d355f98", "T023_09"),  # 25 s51
    ("e4807fe4-2d3f-5efc-b22e-59952a070f5b", "T024_07"),  # 25 s53
    ("752f04cb-d7a4-50d0-9a3f-da1ee0960798", "T025_09"),  # 25 s55
    ("82b6e7a1-1db4-5c2c-9ca5-c79681e3d8ea", "T026_07"),  # 25 s57
    ("0e5ba6e5-d4a4-5638-b7b6-cb259c12cd2c", "T027_06"),  # 25 s58
    ("73488d3b-8765-5882-a9aa-67f5a2bbbcfd", "T027_05"),  # 25 s58
    ("814d4240-2524-506c-894c-64758c59d285", "T027_07"),  # 25 s59
    ("abfb7c78-2eec-55b2-b1dc-d3336f8fab06", "T027_08"),  # 25 s59
    ("b06d6175-129f-5336-baa1-f479bcb913d0", "T027_09"),  # 25 s59
    ("27d70916-e1c3-5deb-9e94-3cb249b59077", "T028_01"),  # 25 s60
    ("aff30400-6b55-5281-bdbf-169b239a1ca7", "T028_06"),  # 25 s60
    ("e3d7178d-4249-5f98-9f98-c21858e622af", "T028_05"),  # 25 s60
    ("6ac6ab7f-6778-5b53-a5f3-1682502b9ece", "T028_08"),  # 25 s61
    ("821b0525-b32d-51b7-9d30-ce9c9aa22b22", "T028_07"),  # 25 s61
    ("f68d7a36-10da-5bfa-8f98-8f2c46b3daff", "T029_04"),  # 25 s62
    ("109bf6fe-8155-552f-b5f6-a085627deaf3", "T029_07"),  # 25 s63
    ("e2131a08-078d-5fdb-b2ae-d73cd2b65564", "T030_03"),  # 25 s64
    ("839ea434-e8cf-5faf-994c-03f350d057ca", "T035_04"),  # 25 s74
    ("9eca1914-5a4b-51c5-988b-8f8e040a0482", "T035_03"),  # 25 s74
    ("8af25ed0-3553-5189-bca9-f27e0e736705", "T037_01"),  # 25 s78
    ("fbc3e5a9-982c-5264-a52d-f4b11876e224", "T040_09"),  # 25 s85
    ("542d6f15-e63e-59ed-bacb-9f48b3a7ed09", "T044_11"),  # 25 s93
    ("21a5a8b4-36db-5a3f-aaf5-52ba70862db0", "T045_02"),  # 25 s94
    ("2f3f0f8f-0e46-533d-999e-388b3f535394", "T045_03"),  # 25 s94
    ("9638bcbb-3eae-5ed8-9918-678cfca3e31a", "T045_10"),  # 25 s95
    ("dfb3b651-2ae0-54f8-931f-4f0108f2a9b7", "T046_03"),  # 25 s96
    ("4f731beb-2324-548c-8e9e-fe9734cea374", "T047_04"),  # 25 s98
    ("7ea7dcf9-068f-5011-b24b-03379b9099be", "T047_06"),  # 25 s99
    ("a8da2f0c-fd36-56cb-a205-04dd0caf5f7c", "T048_05"),  # 25 s100
    ("0a77b21d-4c20-5a64-961d-5428635fcd17", "T049_07"),  # 25 s103
    ("96d4d002-c6d2-5a9d-bba3-8dfecfb25e87", "T050_03"),  # 25 s104
    ("b632da8e-f4e5-51f4-8a8b-a9c648804502", "T053_07"),  # 25 s111
    ("215a7850-f623-5c83-b432-0b0d0fe1e7e7", "T054_01"),  # 25 s112
    ("87a9048c-363b-5428-84d7-62bab58baeac", "T054_05"),  # 25 s112
    ("f0e212d7-4868-53e5-9c45-fba9709b8374", "T054_07"),  # 25 s113
    ("31b2da45-2b28-5a17-ae91-679218d5c9a5", "T058_01"),  # 25 s120
    ("bc74fd99-7156-549c-b44e-d659380512bc", "T058_01"),  # 25 s120
    ("87569ccb-d587-574d-b851-746079c5176d", "T058_10"),  # 25 s121
    ("a28f6670-4f99-5fce-8b2f-c804f53aee7d", "T059_05"),  # 25 s122
    ("cd6459ad-f20f-5458-a341-0823a85c0a33", "T063_03"),  # 25 s130
    ("c465af37-d951-574c-9b2d-70e519fb7483", "T065_07"),  # 25 s135
    ("a3627cdf-e406-5ec1-99f1-3aff7b8df159", "T069_01"),  # 25 s142
    ("a480c3e9-b20d-508c-9cfb-85008749be47", "T069_04"),  # 25 s142
    ("a0d439b4-5bbf-5129-89cf-0c16fd4cbac7", "T070_04"),  # 25 s144
    ("fb394942-f0e7-56d7-b882-76e4130c125c", "T070_10"),  # 25 s145
    ("193df639-6e2c-5891-959b-102f5ffd5d7b", "T071_03"),  # 25 s146
    ("88089281-1d58-5dbc-84f5-1713a3ca090d", "T072_04"),  # 25 s148
    ("e4006689-87a6-55b9-ac6c-58aef489a343", "T072_03"),  # 25 s148
    ("b7321591-5cea-5824-af81-743b7bb28938", "T072_08"),  # 25 s149
    ("2957ddeb-e418-519e-895c-eb3e3131a3d4", "T073_09"),  # 25 s151
    ("6339da1d-d994-5309-880c-267e363b4188", "T073_06"),  # 25 s151
    ("d6ae9ad9-1de0-5c42-a1dc-88eac9a79ffe", "T073_08"),  # 25 s151
    ("e69b53fb-3a0c-5d35-95e2-eeccaa0b6fca", "T073_05"),  # 25 s151
    ("9d72bbd5-adf2-516e-826c-167b67512384", "T074_03"),  # 25 s152
    ("e0f753ed-76a1-5143-a01c-b87e2de757d0", "T074_06"),  # 25 s153
    ("0de6b892-444e-56ce-8f86-0bb79a0cb5f9", "T077_07"),  # 25 s159
    ("251d01bb-4aeb-59b7-a2b0-7a05e6a7de58", "T077_07"),  # 25 s159
    ("270691c1-2ba1-5e7a-98a2-cbbdfb39a90e", "T079_11"),  # 25 s163
    ("99dcfdfb-855a-5b7e-ac29-c10869f2bcd7", "T080_01"),  # 25 s164
    ("9dc0a976-0d22-57e5-820a-d5c8a3f4e0ee", "T080_03"),  # 25 s164
    ("d985fe35-53ef-511c-9313-033d9ff082fd", "T080_02"),  # 25 s164
    ("e29098ba-7586-54bd-9745-2ad046be3631", "T081_01"),  # 25 s166
    ("e2b8c7a3-98d3-566d-8a70-6c0a2466558b", "T081_05"),  # 25 s166
    ("784df849-82dc-5cd2-851a-e09132e0aa16", "T081_06"),  # 25 s167
    ("ff76d563-c9e4-5008-a833-ca91f4531751", "T081_06"),  # 25 s167
    ("cc84de52-4033-52b3-b975-310dcf70bfe3", "T082_01"),  # 25 s168
    ("f35dce55-a3c0-5b22-8fee-f775a79aa55c", "T083_10"),  # 25 s171
    ("0da340f6-5950-5501-a745-b30181b4b4ef", "T084_03"),  # 25 s172
    ("2846f6cd-0e6f-5e50-9849-2034d788a5cb", "T085_05"),  # 25 s174
    ("8146187e-faa4-5c68-b365-1fb29421fb13", "T085_01"),  # 25 s174
    ("9f017ef3-0feb-530b-a229-276acf4cdc16", "T085_03"),  # 25 s174
    ("db8f9153-497d-5079-b7cb-22ddb5ffbb34", "T085_04"),  # 25 s174
    ("e463ebbc-83c5-5beb-8e25-b7fb750b2bbb", "T085_06"),  # 25 s174
    ("07cfb530-aa2d-5b9b-b8a7-b95114a031e5", "T086_02"),  # 25 s176
    ("6f5b0ad0-f857-5b4b-b87b-ab7723e0c616", "T086_01"),  # 25 s176
    ("a6af622c-3f04-5430-9e38-723dfc09a630", "T086_04"),  # 25 s176
    ("4c62c63d-72c5-5fc3-a953-0e6fc61508c2", "T087_03"),  # 25 s178
    ("ad001655-4909-599a-8d6d-5d1795fb8a7f", "T087_05"),  # 25 s178
    ("75e6b56a-083d-53ec-b2fe-95cca46b56a1", "T087_10"),  # 25 s179
    ("b0c86a5a-f4fb-5091-88fb-13c4d8150aff", "T087_09"),  # 25 s179
    ("4d86f210-6e0b-5cda-9394-618cdccc65e5", "T088_06"),  # 25 s180
    ("c72441fc-b3fd-599b-ac46-c986cbddc3e2", "T088_02"),  # 25 s180
    ("2ad6fa29-52fe-5c01-8db9-bfb6c82e9f67", "T089_03"),  # 25 s182
    ("61782ba2-e716-518a-99f6-8ead1140d0e8", "T089_08"),  # 25 s183
    ("334b9fb7-b3d6-503c-9e32-7b343b8160c7", "T090_06"),  # 25 s185
    ("392eab67-c0bb-5adc-9516-88927a818bad", "T092_02"),  # 25 s188
    ("96f1fd42-dceb-578e-84d2-d563a27bb29a", "T092_06"),  # 25 s189
    ("993c424b-1dfd-5927-8e00-afe5f3421267", "T092_08"),  # 25 s189
    ("de9e1e70-d239-5936-a2f2-bef517ef5bed", "T093_10"),  # 25 s191
    ("ed2894c3-09ec-55aa-b16e-a815700f2dd0", "T093_06"),  # 25 s191
    ("de046578-c31b-5ca1-9d40-0417a812ea0e", "T094_05"),  # 25 s192
    ("60ef2405-7beb-52c7-996a-521c5553f692", "T094_06"),  # 25 s193
    ("299aae9b-3f98-593e-b4c6-b652233c4480", "T098_07"),  # 25 s201
    ("8b37c8bf-a308-5a9a-8198-b4e54030befd", "T099_01"),  # 25 s202
    ("ad47c42a-e6d7-5f41-916c-b8291a63bc10", "T100_06"),  # 25 s204
    ("67cccee8-af13-5f5e-950a-d41e69bdb7af", "T101_05"),  # 25 s206
    ("26cc50f0-5a3a-5ff2-8def-ca924199b1ec", "T104_04"),  # 25 s212
    ("a7b3c529-f501-52c3-8a82-055e8f971998", "T106_03"),  # 25 s216
    ("bdca8684-9cef-51ec-be7d-46fa7ab44981", "T107_05"),  # 25 s218
    ("f38a5385-8317-5fa7-9b5a-19f2594c8986", "T107_03"),  # 25 s218
    ("340955f7-67bf-5939-aa72-e2947c86232f", "T108_01"),  # 25 s220
    ("599e4c43-4877-5d5a-b65b-9394713dbabd", "T109_09"),  # 25 s223
    ("bdb1d8b2-bf39-5d94-8b27-9472a6131bd7", "T109_08"),  # 25 s223
    ("3ce7c917-030a-5745-be93-89f407cea8f5", "T110_08"),  # 25 s225
    ("1612a0b7-7c3d-5a4e-bd64-e24adf4dfbcf", "T114_09"),  # 25 s233
    ("0f674a8c-0544-5f8b-a1fb-e7fa5d87723c", "T115_02"),  # 25 s234
    ("1b15f9a9-be2d-5bb0-9e5a-895b0331c008", "T115_05"),  # 25 s234
    ("c9f10d60-c5d0-5442-98b4-53b72acc917a", "T116_03"),  # 25 s236
    ("288e79f0-6fd2-5b73-a777-b7f824b8ae45", "T116_09"),  # 25 s237
    ("c20f399c-6760-5de9-b97e-f9e90d31a1f9", "T116_07"),  # 25 s237
    ("cbe314b7-fac7-574e-852f-032ec6c6d065", "T116_08"),  # 25 s237
    ("1fae4d3e-3878-5be0-a23e-cc63f883888d", "T117_01"),  # 25 s238
    ("b601d7b2-9280-5260-ab24-7536746c6943", "T117_04"),  # 25 s238
    ("c70a9002-fedc-530d-b13d-8c9974e338b5", "T117_05"),  # 25 s238
    ("34ad3db7-8195-5ab0-a4d4-521d85d056c4", "T117_07"),  # 25 s239
    ("b873f945-7c26-524a-afa2-2205101dc8ce", "T117_08"),  # 25 s239
    ("f41c75ba-a840-5d2e-9bc8-9e9b3390c2f8", "T117_10"),  # 25 s239
    ("c7ec4e32-34b4-5318-a685-b1dd3038873e", "T118_05"),  # 25 s240
    ("6b7993a8-c6fc-504c-a16e-67d27c43a32e", "T118_08"),  # 25 s241
    ("c83babab-fb38-577d-8f6c-a2228c9d06b9", "T119_09"),  # 25 s243
    ("8d2461e0-efd8-5b5d-9c01-634f9ca229ae", "T120_04"),  # 25 s244
    ("4008420d-466a-561a-9c5b-6c84988e5fef", "T120_10"),  # 25 s245
    ("6879c8f6-92ff-5d60-b26b-6eb63f70737c", "T120_09"),  # 25 s245
    ("11763db7-44e2-5732-b1e8-6c6db361b6f0", "T121_04"),  # 25 s246
    ("3f3ee57b-60a5-5238-8ab8-ea82ec2c8248", "T121_06"),  # 25 s246
    ("88e4202c-2487-53d2-94a5-eb8139648ce7", "T121_03"),  # 25 s246
    ("64ece9d8-e04e-5a1e-99eb-9bd3933dc5a0", "T122_02"),  # 25 s248
    ("709bc92c-cc98-5c8a-bce8-95645b32458c", "T122_01"),  # 25 s248
    ("a0d5e02e-eb57-5e4e-9852-0872cca25cd4", "T122_05"),  # 25 s248
    ("068058e2-2a4d-5820-aa14-129ead129167", "T123_05"),  # 25 s250
    ("4880c39f-3cf8-534f-a89e-0aec534f04ff", "T123_06"),  # 25 s250
    ("5b46468a-1237-5915-ac32-a47f0dbc8eb1", "T123_03"),  # 25 s250
    ("1cce4b9a-5973-56c3-97f0-5330ce4c5717", "T123_10"),  # 25 s251
    ("438283f5-15da-5375-ba3f-20d82d404c25", "T123_07"),  # 25 s251
    ("a4a3102c-e540-58ea-adb9-c0ca7f0450ec", "T123_08"),  # 25 s251
    ("5dfc956e-a40b-55e9-a73f-9697f8cba6e6", "T124_02"),  # 25 s252
    ("a0961020-cc7b-5960-b13f-4661f7a2f3f5", "T124_04"),  # 25 s252
    ("17615d4c-9a5a-55f2-b30f-48b85783bdbc", "T124_06"),  # 25 s253
    ("96c579bf-8d84-5c36-b1bd-f8ae4f55b8da", "T125_01"),  # 25 s254
    ("87ec9b22-e39b-5875-9325-18e76b383df6", "T125_08"),  # 25 s255
    ("632ced05-4133-541f-af38-1f4a372e0b62", "T126_04"),  # 25 s256
    ("499785c0-a661-5f36-8ac9-8137f2b31428", "T127_02"),  # 25 s258
    ("922fe412-def8-5acd-a8ab-9571b609d55a", "T128_05"),  # 25 s260
    ("7036b43c-9f8d-5070-88c0-ca72f84f0ee9", "T129_03"),  # 25 s262
    ("91422cea-1e3d-5ceb-9a5e-80ccf4b9b241", "T131_11"),  # 25 s267
    ("a2d6834a-e347-5b98-9dab-b920fb4f560d", "T131_10"),  # 25 s267
    ("a0a9ff45-c40b-57e5-836f-330c8c68f05c", "T132_04"),  # 25 s268
    ("d5e8abcd-ba57-5725-8b63-85d6e1c0510c", "T133_02"),  # 25 s270
    ("1b352c29-b60d-5602-876d-3be1313f9819", "T133_09"),  # 25 s271
    ("a99c1e2f-1f86-5d91-b57b-50780ab66652", "T135_10"),  # 25 s275
    ("cea5b383-2066-5fb8-a77e-5d9064c4603a", "T135_08"),  # 25 s275
    ("ec260d69-8c63-55b7-9cd7-9a0565405440", "T135_11"),  # 25 s275
    ("3c5510aa-6bb2-598e-b032-f1cac292ec4c", "T136_07"),  # 25 s277
    ("5e28810e-3c29-5b0d-8400-37c0503148dd", "T137_02"),  # 25 s278
    ("a1c5ebc9-039e-5f1e-b534-1c9dac5f3d22", "T137_03"),  # 25 s278
    ("f279e6b7-784d-5604-97a8-3631b5168d21", "T137_03"),  # 25 s278
    ("17a3c8b1-1cc4-5cfd-9b84-fdb1947985b5", "T137_10"),  # 25 s279
    ("5782e682-eee8-5b39-b2f0-a26baec15dfa", "T137_09"),  # 25 s279
    ("15df9456-21e1-5f63-a580-a9c07c6c763f", "T138_01"),  # 25 s280
    ("0d46ff01-1e4c-5ad4-8d30-da6ca42a6c76", "T002_05"),  # 24 s9
    ("2721c048-5d49-5fda-89a4-4eedec2cd880", "T002_08"),  # 24 s9
    ("8dbf345b-974d-5312-ad37-87cc2769e177", "T003_04"),  # 24 s10
    ("c2f06cf4-9751-515f-82a9-e4d657634216", "T004_01"),  # 24 s12
    ("c841feff-3aa5-5300-8cce-b0c3be4bd5e0", "T004_03"),  # 24 s12
    ("2e3b4b45-6141-5e51-a526-a09bba2f0021", "T004_09"),  # 24 s13
    ("bbbdf2e3-ceec-5c67-a627-114f6f38f956", "T010_06"),  # 24 s25
    ("ac279d5a-a4ca-5e47-8530-ee5a8604959d", "T011_03"),  # 24 s26
    ("94261b17-a55e-50f6-9e97-cad4bbbc3a89", "T013_04"),  # 24 s30
    ("d9cfcd5b-a88a-50e2-a981-0dde95c4e95f", "T014_01"),  # 24 s32
    ("b8a9bc25-1990-5291-8d84-7121f7405812", "T015_01"),  # 24 s34
    ("55103c81-5a92-53d1-a1db-3394ab57accc", "T016_01"),  # 24 s36
    ("59e34ac9-990b-5372-9216-723c5e3db51c", "T016_02"),  # 24 s36
    ("478787f8-e32a-57b9-80b5-ccc999192bfe", "T016_07"),  # 24 s37
    ("4794c9ab-4708-51a8-b109-537dc41bd2db", "T016_06"),  # 24 s37
    ("a0488e24-2a8f-5ffe-8ecc-f81092dbf81a", "T016_09"),  # 24 s37
    ("d996b509-c239-5265-8581-ff54b7d03125", "T016_10"),  # 24 s37
    ("e1f3e474-b411-51bf-8fb3-0c8af85f1a14", "T017_04"),  # 24 s38
    ("8a3531c0-b6b1-5db1-b1d5-57024b0f8dea", "T017_09"),  # 24 s39
    ("18eb2371-f769-5501-95ef-2214f86207b0", "T018_02"),  # 24 s40
    ("7e0c321d-760d-55eb-bdf3-21401db2daa8", "T018_01"),  # 24 s40
    ("24f0168b-e36e-5e8f-bb50-680e3ac62963", "T019_02"),  # 24 s42
    ("de7e6741-61e1-5c3a-87ef-259ade8af973", "T019_04"),  # 24 s42
    ("0224b46d-0d83-54f6-a754-a1330e935a56", "T019_07"),  # 24 s43
    ("2329e653-7133-51f2-ba38-91281d823571", "T020_05"),  # 24 s44
    ("9dd2b6f9-0fa2-5c0b-9814-769b2f8aba26", "T021_02"),  # 24 s46
    ("2601d9c5-51da-59f9-bab6-e032eb34e4e8", "T022_04"),  # 24 s48
    ("6d271f5b-5efe-50eb-91e9-d37d8f41cd1c", "T022_02"),  # 24 s48
    ("f3654aea-4c0b-54b2-b0f6-bd357523889b", "T022_01"),  # 24 s48
    ("f88cf931-5b79-5dd8-8aac-d5db3c850fdb", "T022_03"),  # 24 s48
    ("bc85d691-4eb1-59c8-9f7f-a4737e853b6d", "T022_06"),  # 24 s49
    ("986a02a0-14f9-545a-a388-2fc157302e0c", "T023_01"),  # 24 s50
    ("b02cb08e-8763-53ec-9a7a-3b3725245606", "T023_05"),  # 24 s50
    ("0addbba5-f154-593e-96cb-e390834d9217", "T023_08"),  # 24 s51
    ("64de0932-9e1d-524a-89dd-2aad8e0660ed", "T025_01"),  # 24 s54
    ("97a447fc-3d73-574b-84b8-03b9d59438ee", "T026_01"),  # 24 s56
    ("a5ca5c41-f144-57fe-b419-8dafb1bd29b1", "T026_07"),  # 24 s57
    ("b93ca6d8-1b81-5433-9d73-0ee97e91cefd", "T027_07"),  # 24 s59
    ("d80cb683-19ed-59df-b5b1-6474bbbe9fc0", "T027_07"),  # 24 s59
    ("e57cf9e2-324f-5504-8cb0-8a8e7cd566b2", "T027_09"),  # 24 s59
    ("d3828f20-c7ef-53cf-b2ac-228cf7c1ef2b", "T028_05"),  # 24 s60
    ("905f8f3e-3e41-5700-8b08-e450f60b5bd9", "T028_07"),  # 24 s61
    ("3368adc0-17e0-582b-8b06-bde72d6bc19b", "T029_04"),  # 24 s62
    ("8b003c47-8680-5f80-a73a-27cd8f50ec71", "T030_01"),  # 24 s64
    ("bae4367a-907a-5e80-81d8-25d0b20801aa", "T031_01"),  # 24 s66
    ("c196cd0d-5edf-577f-b9d9-f016d40dfb67", "T034_06"),  # 24 s73
    ("13539204-ce4f-50c8-afe2-619ab82c3b49", "T037_01"),  # 24 s78
    ("cbfc6f95-4c42-5a52-b6a2-805b91366e99", "T039_08"),  # 24 s83
    ("d030b81b-a830-5936-a250-bbe37bcb1971", "T040_08"),  # 24 s85
    ("4e07991d-62e6-5532-b86a-0194658a2672", "T046_08"),  # 24 s97
    ("a40b377b-1ea5-51e4-bd33-e56bc0db68a2", "T047_04"),  # 24 s98
    ("7f7a0634-51ff-5555-b376-dd546d2d7a6f", "T050_05"),  # 24 s104
    ("f7a95960-4008-53ae-a786-0e662def7b50", "T050_08"),  # 24 s105
    ("3cabadf6-0120-5a67-a422-039dee3dc4d8", "T054_03"),  # 24 s112
    ("9ce01b33-a20f-535b-b606-d51155dcda08", "T062_02"),  # 24 s128
    ("72ab50d1-625c-5a92-a194-1d046a0e2109", "T068_03"),  # 24 s140
    ("5a67e3c7-f614-5571-a9be-6267f492811b", "T069_09"),  # 24 s143
    ("dc4562db-ac2b-5fe1-9bc3-2a5d4e2a0895", "T076_04"),  # 24 s156
    ("678436b0-a66c-5ea8-a0c1-00b5da177301", "T077_08"),  # 24 s159
    ("8865544a-df21-5b32-95cc-917975462543", "T077_07"),  # 24 s159
    ("a2aa8416-fd04-5b23-9ce7-2c23136356a6", "T079_02"),  # 24 s162
    ("e38c746e-057e-549e-abef-25702679b462", "T080_01"),  # 24 s164
    ("e3e131ff-ecd6-5108-80eb-eca66d4bec34", "T080_02"),  # 24 s164
    ("06d2071b-a497-5434-8658-af4e77d7a942", "T081_06"),  # 24 s167
    ("65bb69a2-3213-5943-a0c4-f44806ca9f80", "T082_01"),  # 24 s168
    ("f71a8502-77bd-5ff5-9887-80980d45734b", "T082_07"),  # 24 s169
    ("fa55ac5c-dafb-5095-bbcf-270596183a41", "T084_03"),  # 24 s172
    ("abfcc0d1-e979-53a2-b679-6eeb84eb111f", "T085_01"),  # 24 s174
    ("b1e3bfb5-7295-5a1b-9669-52c74f2b5b09", "T085_03"),  # 24 s174
    ("b6d789d4-fa66-564c-82e6-4a26c0abf9bc", "T085_04"),  # 24 s174
    ("ee4ba64d-b1b5-55d4-b348-6e00ab104b85", "T085_05"),  # 24 s174
    ("1235ce0c-8987-581a-a7e7-c5ea49293a9f", "T085_12"),  # 24 s175
    ("c1375e44-175a-5c97-b54f-df358b1ed36d", "T085_11"),  # 24 s175
    ("2870aa33-e2c1-5981-946a-bb3280824acf", "T086_02"),  # 24 s176
    ("6b0cded0-0642-54dc-9724-f78b66e5de8d", "T086_04"),  # 24 s176
    ("4dc68d8e-a34f-570f-bcac-f8a06178ffc6", "T088_03"),  # 24 s180
    ("6baa4e53-2a06-5e9b-a40a-f464c92324d9", "T088_06"),  # 24 s180
    ("6f31f8ed-ad1e-5211-922f-fe203a78e2cf", "T088_02"),  # 24 s180
    ("e4b40eaa-e263-52ce-8ecd-df2b4d5b240b", "T089_08"),  # 24 s183
    ("106b58e6-aba5-5999-8362-d69743e79b39", "T090_07"),  # 24 s185
    ("7d16d1a0-764e-51c0-a450-fd2e443ce17e", "T090_05"),  # 24 s185
    ("14849971-7904-5716-9e9a-4caed63fcbd2", "T093_08"),  # 24 s191
    ("d7da1055-941e-59e9-9a1a-5ac438fbf8ae", "T094_09"),  # 24 s193
    ("a457d001-3899-5247-b7bb-24c7b13653a0", "T098_09"),  # 24 s201
    ("0e765b6c-9241-5631-9896-617e1570ced5", "T099_11"),  # 24 s203
    ("068e288b-1be9-5c96-a641-7ad226b56336", "T107_10"),  # 24 s219
    ("b0d9a872-027d-5dac-aa4b-6f4df9ca90f1", "T107_11"),  # 24 s219
    ("529ad8d9-e586-57dc-8424-318362ec518a", "T114_09"),  # 24 s233
    ("9f76c899-20cb-52a0-8a07-2416b7b0de1f", "T116_04"),  # 24 s236
    ("1fd91e3a-38cb-5c02-b48b-031444959b44", "T116_10"),  # 24 s237
    ("b45fd450-25fd-5b08-a70d-830a70f3c468", "T116_08"),  # 24 s237
    ("0fea7671-6469-5190-bb9e-40e96c837bd0", "T117_07"),  # 24 s239
    ("4ee0a177-3304-59b0-93e8-651a7f576b5f", "T118_02"),  # 24 s240
    ("88027f7a-441d-5b4c-a198-3fb346311e9e", "T118_03"),  # 24 s240
    ("56a666f6-6000-5113-b7a5-f304b281baed", "T119_09"),  # 24 s243
    ("896e836b-3062-5a98-b4e0-d375e7bbebd8", "T119_07"),  # 24 s243
    ("77610fc0-41ba-5976-b07d-e0a5c03dee9c", "T120_04"),  # 24 s244
    ("7b22a3a3-6040-5239-b82d-f3b294f23117", "T120_10"),  # 24 s245
    ("bf136b7c-68dd-578b-a32d-40d719f0b2a8", "T120_09"),  # 24 s245
    ("e1bb2449-30a3-595e-8ea6-cf60004511ff", "T120_09"),  # 24 s245
    ("419fd26a-b01a-5661-828d-ff7db690342b", "T121_03"),  # 24 s246
    ("85b472ee-b1ed-5bde-884c-1ed6122c8db6", "T121_06"),  # 24 s246
    ("b943881c-a785-5771-aa82-a88723d88dd3", "T121_08"),  # 24 s247
    ("934dfd83-56b5-538e-9938-8b5cbefe0021", "T123_01"),  # 24 s250
    ("ee735ffd-c5a9-5739-973c-6620bd2e3ed4", "T123_08"),  # 24 s251
    ("5d6d92be-daa8-5113-a81d-5396040967e9", "T124_04"),  # 24 s252
    ("d0aaabf0-caa4-53ab-be5c-d43d6473843c", "T125_01"),  # 24 s254
    ("0467ea6f-a907-5dac-a40c-c0e560d89a69", "T126_03"),  # 24 s256
    ("8df8dd7c-a54d-5333-9874-782f46d5f9f0", "T131_10"),  # 24 s267
    ("5bdcc9be-5a28-5532-8609-3335d7e1f62b", "T132_09"),  # 24 s269
    ("a3ce9004-9dd5-5af6-8df0-32122c2bfe6f", "T134_10"),  # 24 s273
    ("d47d905d-89ee-56e0-9c69-4e8efd29fce9", "T134_07"),  # 24 s273
    ("b782c6a3-dd01-5699-a47b-496d882c1569", "T135_02"),  # 24 s274
    ("5b17609e-8304-52fa-82a0-5ca14239206a", "T135_08"),  # 24 s275
    ("40e9afc6-93aa-5be8-9442-d12929b8af0a", "T137_02"),  # 24 s278
    ("a420ec7d-ce84-5e85-b98e-5f1d62d0340b", "T137_03"),  # 24 s278
    ("f2254d1e-300b-5134-b755-fd813f956e31", "T137_10"),  # 24 s279
    ("6e484080-6023-505d-b358-8ca7af6f460a", "T138_01"),  # 24 s280
    ("e5bdc395-4663-56dd-84ec-45d1dab8c171", "T138_01"),  # 24 s280
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
SELECT qm.pipeline_metadata::jsonb ->> 'kaynak_gorseli'
  FROM question_metadata qm
 WHERE qm.source_book = :kaynak
   AND qm.pipeline_metadata::jsonb ->> 'ithal_araci' = :arac
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
        _log.info("[0063] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0063] mv_safe_for_beta yenilendi")


def _tablolar_var(b) -> bool:
    denetci = sa.inspect(b)
    return all(
        denetci.has_table(t)
        for t in ("question_bank", "question_metadata", "topic_hierarchy")
    )


def hedef_idler(modern_var: set[str]) -> list[str]:
    """Modern karsiligi DB'de bulunan eski satir id'leri (saf fonksiyon, test edilir)."""
    return [e for e, m in ESKI_MODERN if f"KMT345-{m}.png" in modern_var]


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0063] soru tablolari yok (taze DB?) -- atlandi")
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
            sa.text(_MODERN_SQL), {"kaynak": KAYNAK, "arac": ITHAL_ARACI}
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
    _log.info("[0063] eski hat: %s aday, %s satir pasife alindi", len(idler), len(eski))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0063] %s yok -- downgrade atlandi", GUNLUK)
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
    _log.info("[0063] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
