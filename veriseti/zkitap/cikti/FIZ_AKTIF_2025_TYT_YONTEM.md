# AKTIF 2025 TYT Fizik Soru Bankasi -- yontem (AKT25FZ)

Tarih: 29 Eyl 2026. Hat: ortak `backend/scripts/kitap/kitap_hat/` (profil
`kitap_hat/profiller/akt25fz.py`; Aktif Ogrenme serisi, kancalar AKT20K0 /
AKT20AY / AKT24BY'den). Kaynak: FERNUS 1920x1080, 352 PNG, kart
(589,43)-(1331,1022); basili sayfa = dosya.

## 1. Kitap yapisi

* Icindekiler s6: 13 unite (acilis 7, 19, 41, 69, 89, 109, 127, 147, 173,
  201, 233, 247, 327). Konu = unite.
* Test sayfasi = turuncu bant >= 1500 VE pembe >= 600 VE iki kutulu serit
  (x0 < 100): 132 test sayfasi, 13 blok, kopya sayfa yok. Sayfa turu: kapak
  4, konu 216, test 132.
* Bant adlari baskida uc yerde farkli -> `BANT_ESLER` (ISI-SICAKLIK VE
  GENLESME, NEWTON'UN kesme isareti, IS-GUC-ENERJI).

## 2. Test siniri ve cevap anahtari (iki gecis)

* Sayfa basina serit okumasi A / B (4+4 okuyucu): A == B 655/655; BAS 66 test.
* Glif ucuncu kanal: 655 hucre, LOO 655/655, uyumsuz 0 -> goz teyidi yok.
  Harf A 117, B 115, C 146, D 124, E 153. Soru cozulmedi.

## 3. Capa ve kirpim

* Numaralar pembe / kirmizi ve kucuk: profil `numara_maskesi`
  (r > 180, r - g > 50, b >= g - 10, b < 200), `NUMARA_H` (5, 12),
  `NUMARA_DX` (14, 48).
* Simge cift L 73 / R 368, tek L 63 / R 358. s57-67 ve s103-107 tek dosyalari
  cift yerlesimde -> `PARITE_TERS` (AKT24BY kancasi).
* Simgesi band kenarinda / hic olmayan 4 soru `EK_CAPA` (s68, 106, 192, 197).
* Pembe sekme kivrimi (x 62-95, y 600-712) `SUS_BOLGELERI` ile beyazlatildi;
  R sutunu 376/386'dan (simge halkasi kenar ihlali).
* Dizgi sikisik: sik satirlari arasi bosluk sorular arasi bosluktan buyuk.
  Varsayilan BOSLUK ile kutu ustu onceki sorunun D/E satirlarinin ustune
  cikiyordu -> yeni genel kanca profil `BOSLUK` (burada 5); 93 kutu degisti,
  hepsi iki okumada yeniden okundu.
* Bos bant 1-3 satir kalan 3 yer (s346 R 11, s349 R 5-6): yeni kanca
  `KUTU_UST_KESIN {(dosya, sutun, sira): y}` (KUTU_UST yalniz yukari
  cikarir; bu kesin deger koyar). Degerler `_a21_gecici/ust_artik.py`
  olcumu (numaranin ustundeki bos kosunun basi); sonrasinda kutu ustu ile
  numara arasinda >= 6 murekkep satiri olan kutu 0.
* Bu dar bantlarda onceki kutunun alt 2 satiri E sikkinin kuyruguna degiyor
  (kirp KESIK 3: T063_10, T065_04, T065_05). Kirpimlar gozle tam -> yeni
  kanca `KESIK_GOZ_ONAY` (kirp.goz_onayi_ayir): onayli kayitlar kapiyi
  tetiklemez, JSON'da `kesik_goz_onayli`; olculmeyen onay (bayat) kapiyi
  durdurur.
* 655 kutu, artik 0; kirp kenar 0, KESIK 0 (+3 goz onayli); ortme 32 soru.

## 4. Ortak oncul

* Okumalarda `komsu_not` 0 (yeniden kirpimdan sonra); 'sorulari / bilgilere
  gore' kalibi 3 soruda, ucunde de bilgi ayni kirpimda. Ortak oncul YOK.

## 5. Metin

* 14 grup, iki bagimsiz okuma; 136 fark 8 hakemle: okuma_1 36, okuma_2 26,
  ikisi 4, yok 70 (farklarin cogu sekil ici veri yazisinin alinip
  alinmamasi). Gorunen `[??]` 0. Cikmis soru etiketi 33 (TYT 2018-2023 28,
  YGS 5) -> `BEKLENEN_ETIKET = 33`.

## 6. Mukerrer, ithal, beta

* DB 6159 fizik satiri; 56 aday, GUCLU 37; kitap ici 0. 7 soru baska
  kaynaklarda (Mikro Orijinal TYT Fizik 2025, 345 2025 TYT Fizik ...) ayni
  soru_hash ile var -> ayni id, ithal yazmadi. Cevap farki icerik 5 esleme
  (T001_08, T053_04 x3, T061_09): basili anahtar degismez.
* 0110 agac (FIZ-AKT25FZ: 13 bolum, 13 konu), ithal 648 PASIF, 0111 eski
  hat (0 satir), 0112 toplu beta 648/648. Round-trip (0109 <-> 0112) temiz.
