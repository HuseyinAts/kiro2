# 2019-2020 Aktif AYT Kimya -- yontem (AKT20AY)

Tarih: 28 Eyl 2026. Hat: ortak `backend/scripts/kitap/kitap_hat/` (profil
`kitap_hat/profiller/akt20ay.py`; Aktif Ogrenme serisi, kancalar AKT20K0'dan).
Kaynak: FERNUS 1920x1080, 416 PNG, kart (589,43)-(1331,1022); basili sayfa =
dosya.

## 1. Kitap yapisi

* Icindekiler s6: 12 unite; 1. unite iki kisim (1-A Modern Atom Teorisi s7,
  1-B Periyodik Sistem s33). Test bandi 10. unitede 'ORGANIK BILESIKLER'
  (icindekiler 'Hidrokarbonlar') -> `BANT_ESLER`.
* 142 test sayfasi, 13 blok; sayfa turu 142 test, 269 konu, 5 kapak.
* AKT20K0'dan farklar (olculdu): soru numarasi KIRMIZI; yerlesim pariteye
  gore kayar (simge cift L 60 / R 356, tek L 52 / R 344; ayrac cift 376, tek
  366; kart kenari 29 / 712); serit kutulari y 912-970 (arama y 900'den:
  y 860 civarinda acik mavi tablolar); sayfa numarasi penceresi (335, 405)
  (322 cift sayfada sol kutunun son harfini siliyordu: her testte 1 glif eksik).
* Bant alti: bandin egik alt kenari 131-160 doygun piksel; `ust_bant` bant
  ustunden > 100 surdukce iner (AKT20K0 olcumu artik kapisina takildi).

## 2. Test siniri ve cevap anahtari (iki gecis)

* Sayfa basina serit okumasi A / B (4+4 okuyucu): A == B 937/937; BAS 71 test.
* Kitapta baski hatalari (gozle): s161-162 Tepkimelerde Hiz Konu Testi 1'de 13.
  soru yok (sorular ve serit 1-12, 14-19) -> `SERIT_NUMARA_BASKI_HATASI`
  (sira 13-18) + `BASKI_NUMARA_HATASI`; T047_03 ve T060_14 numarasi onceki
  sorunun numarasiyla ayni basilmis.
* Glif ucuncu kanal: 937 hucre, LOO 936; 1 uyumsuz (T069#14) 5x gozle E.
  Harf dagilimi A 101, B 164, C 223, D 210, E 239. Soru cozulmedi.

## 3. Capa ve kirpim

* Simgesiz 1 soru `EK_CAPA` (s134 R '13.').
* Yeni genel kanca `KUTU_UST`: sutun basindaki numarasiz ORTAK oncul (grafik,
  tepkime, tablo) sutunun ilk sorusunun kutusuna katilir (kutu artik kapisi
  6 yeri buldu: s117 R, s118 L, s162 R, s165 L/R, s170 L).
* 937 kutu, artik 0; kirp kenar 0, KESIK 0; ortme 181 soru.

## 4. Ortak oncul (yeni hata sinifi)

* Oncul yalniz grubun ilk sorusunun kirpiminda; bagimli sorular onculsuz
  anlamsiz, ikisi birebir ayni ('Tepkimenin derecesi kactir?' T027_02 = T027_07,
  cevaplari C / D) -> ithal on kontrolu 'ayni hash iki kez' ile durdu.
* METIN oncul (s165 L tepkime 1-5, s165 R mekanizma 6-10, s199-200 denge
  tepkimesi 9-12): oncul satirlari bagimli sorunun govdesinin basina eklendi
  (`_a21_gecici/b9_ortak_yama.py`; 12 soru).
* GRAFIK / TABLO oncul (s117 R 5-9, s118 L 10-14, s162 R 14-19, s170 L 7-10):
  16 bagimli soru `ORTAK_ONCUL_YOK` -> bayrak `ortak_oncul_kirpimda_yok`;
  beta sablonu ve beta_olc bu bayragi servis disi sayar (yeni kural).
* Ayni sinif AKT20K0'da: s196 tablo 8-11, T032_09..11 0101 ile aktif olmustu
  -> 0105 ile bayrak + pasif (geri alinabilir).

## 5. Metin

* 18 grup, iki bagimsiz okuma; 185 fark 8 hakemle: okuma_1 55, okuma_2 35,
  ikisi 15, yok 80.
* Gorunen `[??]` 134 soru (cogu okuyucu simgesi altinda kalan satir sonu).

## 6. Mukerrer, eski hat, ithal, beta

* DB 7029 kimya satiri; 293 aday, 170 GUCLU; 23 soru eski hat satiriyla ayni
  hash.
* Eski hat 'Aktif Ogrenme Ayt Kimya 2019 2020': 490 satir aktif; 170'inin
  modern karsiligi -> 0103 ile pasif; 320 aktif kaldi.
* 0102 agac (KIM-AKT20AY: 12 bolum, 13 konu), ithal 937 PASIF, 0104 toplu beta
  788/937 (134 `[??]` + 16 ortak oncul disarida). Round-trip temiz.
* exam_type AYT, subject KIMYA.
