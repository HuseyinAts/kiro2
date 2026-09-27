# 2020-2021 ACIL TYT Matematik Soru Bankasi -- yontem kaydi

Kaynak adi (DB): `2020-2021 ACIL TYT Matematik Soru Bankasi`, onek `ACL21T`.
Klasor: `screenshots/2020-2021-ACIL-TYT Matematik Soru Bankasi` (Turkce
harfli), 448 PNG, FERNUS okuyucu 1920x1080; sayfa karti (589,43)-(1331,1022)
= 742x979; basili sayfa = dosya no. Sahip talimati (27 Eyl 2026):
"siradaki islenebilir kitabi ayni sekilde bastan sona isle" -- tam otonom
Faz 0-8, `MAT_ACIL_1920_TYT_YONTEM.md` (ACL20T) ile ayni hat.

Hicbir soru cozulmedi. Tek cevap kaynagi kitabin basili cevap seridi.
Okunamayan yer `[??]`; tahmin yazilmadi.

## 0. Tarama (`acil2021tyt_tarama.py`)

- Sayfa turu: bandin altinda sari cizgi (y 55-90) olan **test** sayfasi 430;
  **kapak** 18 (1-5, 13 bolum kapagi, arka kapak). Acik uclu sayfa yok.
- Test = ardisik test sayfalari, son sayfada sag altta sari cevap seridi:
  150 test.
- Capa = kirmizi basili numara, okuyucu simgesinin (69,39,160) sag-alt
  penceresinde. Simge x: tek 31 / 359, cift 48 / 376 (2255 glif olculdu);
  numara x: tek 50 / 377, cift 67 / 394.
- YENI KURAL: cevap seridinin de okuyucu simgesi var (seridin 7-28 px
  ustu, sag sutun); penceresine sayfa numarasi rozetinin kirmizisi
  dusuyordu (ilk olcumde 46 testte capa = serit + 1). Seritli sayfada
  serit ustu - 40 px'ten asagidaki simge capa degil (`SERIT_SIMGE_PAY`).
- KAPI: test basina capa == serit hucresi: 150/150, toplam 2113.

## 1. Cevap anahtari (`acil2021tyt_anahtar.py`)

- Seritler (3x) iki bagimsiz okumayla: A (A1 ileri 1-75, A2 ileri 76-150),
  B (B1 geri 150-76, B2 geri 75-1). 2113/2113 hucre ayni.
- Glif LOO: 2041 bolutlenen hucrenin 2039'u ayni; 2 uyumsuz (T042#10,
  T069#10) 5x gozle -- okuma dogru (`goz_teyit`). Bolutlenemeyen 4 test
  (16, 36, 45, 140; 72 hucre) 5x gozle, hepsi ayni.
- Dagilim A 244, B 429, C 595, D 560, E 285.
- Bagimsiz teyit: onceki baskiyla (ACL20T) GUCLU eslesen 812 sorunun
  HICBIRINDE iki kitabin basili anahtari farkli degil.

## 2. Harita (`acil2021tyt_harita.py`) ve agac (0074)

- Icindekiler (dosya 3): 13 bolum, 30 konu, baslangic sayfalari.
- Her test tek konu araliginda; bant adi konu ya da acik listedeki basili
  alt baslik (BOLME / BOLUNEBILME, EBOB / EKOK / EBOB-EKOK PROBLEMLERI,
  SAYI / KESIR / YAS / ISCI / HIZ / YUZDE KAR-ZARAR / KARISIM / GRAFIK /
  SAYISAL MANTIK PROBLEMLERI, KUMELER / KARTEZYEN CARPIM, FONKSIYON alt
  basliklari). Bant adi testin `bant` alaninda saklanir.
- Kodlar `MAT-ACL21T-Bnn(-Kmm)`; 0074 (43 dugum, round trip).

## 3. Kirpim kutulari (`acil2021tyt_kutu.py`, `acil2021tyt_kirp.py`)

- Sayfa duzeni ACL20T ile ayni: sutun sinirlari tek L[45,356] R[370,700],
  cift L[62,370] R[386,716] (kirmizi dikey ayrac tek x 363, cift x 379
  olculdu). UST_BANT 81 (bant alti cizgiler y 72-79), SAYFA_ALTI 904,
  SERIT_PAY 12.
- Okuyucu diski beyazlatma ve sayfa no lekesi beyazlatma ACL20T ile ayni;
  kirpimlar gozle kontrol edildi. Kenar kapisi 0; ortme 327 halka / 316 soru.
- Kapilar yesil: 2113 kutu == anahtar, cakisma yok, artik murekkep yok.
  Yukseklik min 101 / medyan 301 / max 823.

## 4. Transkripsiyon (`acil2021tyt_metin_harness.py`)

- 45 grup (~40-55 kirpim), her grup ayri okuyucu; ACL20T talimati.
- On kayitli TAM ikinci okuma (45 bagimsiz okuyucu). Karsilastirma
  normalizasyonu ACL20T + kombinasyon yazimi `C(n, r)` = `(n r)`.
  249 farkli soru; 8 hakem gozle: okuma_1 63, okuma_2 81, ikisi 16, yok 89.
  Ilk okuma esasli hata 79/2113 (%3.7), ikinci 97/2113.
- `[??]`: 221 soru (212'si ortme olcumunde; 9'u soluk isaret ya da kirpim
  kenarinda kesik rakam). T076_09'un D sikki kitapta basilmamis:
  `[okunamadi]` + `sik_okunamadi`.
- SINIR (ACL20T ile ayni): iki okumanin ayni bicimde atladigi sekil verisi
  karsilastirmada gorunmez; ogrenci her zaman tam soru kirpimini gorur.

## 5. Mukerrer olcumu (`acil2021tyt_mukerrer.py`)

- DB: MATEMATIK/GEOMETRI + bu kaynak ve eski hat adi (17809 satir).
- ONEMLI BULGU: bu kitap onceki baskinin (2019-2020, ACL20T) buyuk olcude
  tekrari. 812 soru ACL20T'de GUCLU eslesir; 458'i AYNI soru_hash (ayni id).
  Hicbirinde cevap farki yok. Durum tablosundaki "ortaklik -" bu olcumden
  once yazilmisti.
- Tam hash carpismasi 461 soru (458 ACL20T, 3 eski hat).
- Kitap ici yakin: T140_01/02/04 (ayni govde ve siklar, farkli soru).
- Eski hat '2020-2021-ACIL-TYT Matematik Soru Bankasi': 27 satir, 16'si
  modern karsilikli; cevaplari basili anahtarla ayni.

## 6. Ithal (`acil2021tyt_ithal.py`)

- PASIF. 2113 kayit uretildi; 458'i ACL20T ile ayni id (zaten var), 1655
  yeni satir yazildi. Crops `d-dataset/output/crops/ACL21T/`.
- Yeni bayrak `modern_kitap_ikizi`: ACL20T'deki GUCLU eslesme id'leri
  (`pipeline_metadata.modern_kitap_ikizi`).

## 7. Eski hat pasif (0075_acl21t_eski_hat_pasif)

- 16 eski satir pasif. Guard kirpim adina degil MODERN ID'ye bakar (modern
  karsiligin bir kismi ayni hash ile ACL20T satiri oldugu icin): modern id
  = uuid5(soru_hash), ithalin kendi formulu (testle dogrulanir).

## 8. Beta onayi (0076_acl21t_beta_onay)

- 1655 yeni satirdan 1271 acildi. Dislanan: 213 gorunen `[??]`, 1
  `sik_okunamadi`, ve ikizi ACL20T'de AKTIF olan 226 soru (170'i yalniz bu
  kural yuzunden; ayni soru iki kez servis edilmez). Ikizi pasif olan 128
  soru (ACL20T'de `[??]` ya da hash ikizi yuzunden kapali) diger kurallari
  gecerse bu kitabin okumasiyla acildi.
- human_verified yazilmaz; round trip yerel DB'de denendi.

## Testler

- `backend/tests/e2e/test_acil2021tyt_veri.py` (50) ve
  `test_acil2021tyt_ithal.py` (59): anahtar + mutasyonlar, harita, 0074,
  capa (serit simgesi kurali dahil), kutu, metin, ikinci okuma, mukerrer
  (onceki baski cevap uyumu), 0075 modern id formulu, 0076 dislama.
