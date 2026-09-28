# 2023-2024 Aktif Ogrenme Biyoloji -- yontem (AKT24BY)

Tarih: 29 Eyl 2026. Hat: ortak `backend/scripts/kitap/kitap_hat/` (profil
`kitap_hat/profiller/akt24by.py`; Aktif Ogrenme serisi, kancalar AKT20K0 /
AKT20AY'den). Kaynak: FERNUS 1920x1080, 272 PNG, kart (589,43)-(1331,1022);
basili sayfa = dosya - 1.

## 0. Sira ve kapsam disi kitaplar

* DURUMU'daki siradaki ISLENEBILIR satirlar (Altyapi 'Kartlarla' serisi: TYT
  Kimya, TYT Tarih, AYT Kimya, AYT Roman Ozetleri; ayni serideki TYT / AYT
  Fizik) gozle acildi: hepsi konu karti kitabi, coktan secmeli soru ve cevap
  anahtari YOK -> DURUMU'da 'KAPSAM DISI'. Bu kitap siradaki ilk soru kitabi.

## 1. Yakalama kusuru (olculdu + gozle)

* Art arda kart farki < %0,05: dosya 218-250 = dosya 217'nin (basili 216),
  254-272 = dosya 253'un (basili 219) kopyasi. Yakalama basili 1-219'u
  kapsar; basili 220-266 (5. unitenin sonu, 6. unite Ekoloji) YOK.
* Kopya dosyalar `KOPYA_SAYFALAR` ile sayfa turu 'kapak'. Bosluktan sonra
  (dosya 251-253) dosya paritesi basili sayfanin tersi -> yeni genel kanca
  `ortak.parite` + profil `PARITE_TERS` (tarama SIMGE_X, kutu SUTUNLAR).
* Eksik sayfalar yeniden yakalanmadan islenemez (5. unite Konu Testi 6'nin
  yalniz ilk sayfasi var: 5 soru).

## 2. Kitap yapisi

* Icindekiler s7: 6 unite; yakalamada 5'i (acilis dosyasi 8, 64, 106, 152,
  190). Konu = unite (test bandi unite adini tasir).
* 'ETKINLIKLER & HATIRLATMALAR' / 'ESLENECEKLER' sayfalari test bandi
  renklerini tasir, cevap seridi yok; konu sayfalarinin 'Soru N' seridi yalniz
  sag kutu. Test = renk VE iki kutulu serit (x0 < 100): 83 test sayfasi, 6 blok.
* Test 35 bandi baskida 'HUCE BOLUNMELERI' -> `BANT_ESLER`.

## 3. Test siniri ve cevap anahtari (iki gecis)

* Sayfa basina serit okumasi A / B (4+4 okuyucu): A == B 528/528; BAS 42 test.
* Glif ucuncu kanal: 528 hucre, LOO 527; 1 uyumsuz (T002#17, iki satirli
  kutu) 5x gozle E. Harf A 91, B 89, C 93, D 121, E 134. Soru cozulmedi.
* Numara baski hatalari (gozle, serit ardisik): s59-60 Konu Testi 9'da '6.'
  yok (sorular 1-5, 7-13); s91 R '12.' iki kez; s182 R '3.' iki kez ->
  `BASKI_NUMARA_HATASI` (sira konumdan, basili numara bayrakta).

## 4. Capa ve kirpim

* Simge x cift L 51 / R 350, tek L 62 / R 361 (tolerans 14; s53 '11.' simgesi
  13 px solda). Numara kirmizi; iki basamak dx 46.
* Turuncu orta ayrac (min kanal koyu) ve dikey camgobegi 'aktif ogrenme
  yayinlari' yazisi (y 452-545) x 360-381 penceresinde SUS_BOLGELERI ile
  beyazlatildi; sutunlar cift L 30-361 / R 374-712, tek L 30-370 / R 384-712.
* 528 kutu, artik 0; kirp kenar 0, KESIK 0; ortme 104 soru.

## 5. Ortak oncul

* Sutun tepesinde numarasiz oncul (tarama 'blob_yok' ya da kutu artik
  kapisi): s53 R (metin + madde listesi, 12-14), s91 L (sekil, 10-12), s175 L
  (grafik, 9-10), s179 L (sekil, 8-10; 8. soru simgesiz -> `EK_CAPA`), s188 R
  (sekil, 4-5), s213 L (sekil, 8-10) -> `KUTU_UST` (ilk sorunun kutusu).
* Sutun ORTASINDA oncul: s176 L '2 ve 3. sorulari asagidaki gorsele gore' 1.
  sorunun kutusundaydi (metin okumasi `komsu_not` ile buldu) -> `KUTU_UST`
  (176, L, 1) ile 2. sorunun kutusuna; yeniden kirpim gozle, govde yamalandi.
* METIN oncul (s53 R) T005_13-14 govdesinin basina eklendi
  (`_a21_gecici/c1_ortak_yama.py`). SEKIL / GRAFIK oncule dayanan 9 soru
  `ORTAK_ONCUL_YOK` -> 'ortak_oncul_kirpimda_yok', beta disi.

## 6. Metin

* 11 grup, iki bagimsiz okuma; 68 fark 8 hakemle: okuma_1 18, okuma_2 28,
  ikisi 2, yok 20. Gorunen `[??]` 39 soru.

## 7. Mukerrer, ithal, beta

* DB 2357 biyoloji satiri; 4 aday, GUCLU 0; ayni hash 0; eski hat satiri yok.
* 0107 agac (BIO-AKT24BY: 5 bolum, 5 konu), ithal 528 PASIF, 0108 eski hat
  (0 satir), 0109 toplu beta 480/528 (39 `[??]` + 9 ortak oncul disarida).
  Round-trip (0106 <-> 0109) temiz. exam_type TYT, subject BIYOLOJI.
