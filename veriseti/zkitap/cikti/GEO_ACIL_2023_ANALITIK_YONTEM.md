# 2022-2023 ACIL Analitik Geometri -- yontem (ACL23AG)

Tarih: 28 Eyl 2026. Hat: ortak `backend/scripts/kitap/kitap_hat/` (bu kitapla
kuruldu; profil `kitap_hat/profiller/acl23ag.py`). Kaynak: FERNUS 1920x1080
ekran goruntusu, 176 PNG, kart (589,43)-(1331,1022); basili sayfa = dosya.

## 1. Kitap yapisi (kontak sayfasi + olcum)

* 'Konu Anlatimli Soru Fasikulu': 4 bolum (Nokta Analitigi, Dogru
  Analitigi, Donusum Geometrisi, Cember Analitigi). Her bolumde once konu
  anlatimi (ORNEK / COZUM kutulari -- cozumlu ornek; kapsam DISI), sonra
  testler. Icindekiler s3: test baslangiclari 22 / 72 / 119 / 155.
* Sayfa turu (profil kancasi): ust bantta sari piksel satiri > 60 -> konu
  (197 olculdu); tam genislik ince kirmizi cerceve cizgisi (724/725 px) ->
  test; diger -> kapak. Sonuc: test 81, konu 87, kapak 8. Test sayfalari
  kumesi kontak sayfasindan gozle yazilan araliklarla (22-35, 72-101,
  119-134, 155-175) birebir (kapi).
* Test = ardisik test sayfalari; son sayfada sag altta cevap tablosu. 33 test.

## 2. Cevap anahtari (test sonu tablosu)

* Tablo: 6 sutun, 1-2 satir, kirmizi numara + siyah harf; koyu yatay izgara
  cizgisi 301 px, 16 px arayla. Kisa son satir (10 / 11 hucre) icin cizgi =
  tablo x araliginda >= 90 px kesintisiz koyu kosu (ilk kirpimda 10 test
  eksik satirla kirpilmisti -- okuyucular bildirdi, kirpim duzeltildi, okuma
  bastan yapildi).
* Okuma A (ileri) ve okuma B (geri), bagimsiz: 361/361 hucre ayni, bant
  (bolum adi + test no) ayni.
* Glif ucuncu kanali: 259 hucre bolutlendi, LOO 256 uyum; 3 uyumsuz
  (T001#4 D, T017#6 D, T017#7 C) 5x gozle teyit -- okuma dogru. Bolutleme
  hucre sayisini tutturamayan 9 test (5, 7, 9, 11, 16, 20, 28, 32, 33; 102
  hucre) 5x gozle okundu, okumayla ayni.
* Hucre sayisi == capa sayisi (33/33 test). Harf dagilimi A 47, B 69, C 96,
  D 85, E 64. Hicbir soru cozulmedi.

## 3. Capa ve kirpim

* Capa = okuyucu simgesi (buyutec; dolgusuz halka, 3x3 genisletilmis
  12-17 px) + sagindaki kirmizi basili numara (ofset 20-36 px). Simge x
  sayfa paritesine gore L 13 / R 347 (tek), L 32 / R 363 (cift), tolerans 16
  (soru basina 0-15 px kayma olculdu).
* Numarasi BASILMAMIS soru: s92 sag sutun alt (T015_04). Simge var, kirmizi
  numara yok (gozle); profilde listeli, capa simgeden; metinde basili_no
  null, ithalde `numara_basilmamis` bayragi.
* Sutunlar: kirmizi dikey 'ACIL MATEMATIK' ayraci ve dikey yazisi (tek
  356-366, cift 373-383) disarida: tek L 36-352 / R 369-700, cift L 52-369 /
  R 386-716. Ust sinir test bandi alti (y 79), alt sinir 912 ya da cevap
  tablosu ustu - 8.
* Kapilar: 361 kutu, cakisma 0, artik murekkep 0, kenar 0. Okuyucu diski
  (merkez glif + (10, 8), yaricap 17) beyazlatildi; halka (19-23 px) ortme
  olcumu: 40 soru.

## 4. Metin

* 14 grup, iki bagimsiz okuma TEK dagitimda (darbogaz protokolu;
  `metin_iki_okuma.py`), okuyucu 2 okuma 1'i gormedi. 361 sorunun 345'i
  normalize ayni; 16 fark 4 hakemle kirpimdan gozle: okuma_1 4, okuma_2 8,
  ikisi 1, yok 3.
* `[??]` 10 soru (diskin ortugu satir sonlari); tahmin yazilmadi.

## 5. Mukerrer ve eski hat

* DB 19464 aday satir; 28 aday, 6 GUCLU. 1 soru ACIL 2025 KURS TYT-AYT
  Geometri'de ayni soru_hash ile var -> ayni id, ithal yazmadi.
* Eski hat '2022-2023-ACIL-Analitik Geometri' (Turkce harfli): 1 satir,
  aktif; modern karsiligi var (T016_12) -> 0078 ile pasif.

## 6. Ithal ve beta

* 0077 agac (GEO kokunun altinda GEO-ACL23AG: 4 bolum + 4 konu), ithal 360
  yeni satir PASIF, 0078 eski hat pasif, 0079 toplu beta onayi: 350/360
  (10 gorunen `[??]` disarida). Round-trip (0076 <-> 0079) temiz.
* exam_type AYT, subject GEOMETRI (kardes geometri kitaplariyla tutarli).
