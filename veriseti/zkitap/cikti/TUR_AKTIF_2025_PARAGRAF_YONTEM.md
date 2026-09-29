# AKTIF 2025 TYT Paragraf Soru Bankasi -- yontem (AKT25PR)

Tarih: 29 Eyl 2026. Hat: ortak `backend/scripts/kitap/kitap_hat/` (profil
`kitap_hat/profiller/akt25pr.py`; Aktif Ogrenme serisi, AKT25FZ'den). Kaynak:
FERNUS 1920x1080, 144 PNG (klasordeki PDF goruntu, metin katmani yok), kart
(589,43)-(1331,1022); basili sayfa = dosya - 5. Kapakta 'Pro AKTIF Paragraf'.

## 1. Kitap yapisi

* Icindekiler dosya 9: 5 unite (acilis dosya 10, 22, 28, 36, 46) + Deneme
  Testi. Deneme Testi 1 dosya 62'de basliyor (icindekilerdeki basili 79
  yakalamayla tutmuyor; gozle). Unite = konu; 6. bolum 'DENEME TESTI'.
* 111 test sayfasi, 5 blok (17-21, 24-27, 30-35, 39-45, 56-144). Sayfa turu:
  kapak 9, konu 24, test 111. Deneme 17 yakalamada yalniz 12 soru (sonu yok).

## 2. Test siniri ve cevap anahtari (iki gecis)

* Sayfa basina serit okumasi A / B (4+4 okuyucu): A == B 451/451, bant
  farki 0; BAS 30 test (13 konu testi + 17 deneme).
* Glif ucuncu kanal: 451 hucre, LOO 451/451 (goz teyidi yok). Harf A 64,
  B 87, C 127, D 109, E 64. Soru cozulmedi.

## 3. Capa ve kirpim

* Okuyucu simgesi numaranin ~23 px ustu / 25 px solu: cift L 28 / R 355,
  tek L 46 / R 371. Numara kirmizi; Deneme bandinin kahve bayragi
  (~190,100,80) pencerede ilk blob oluyordu (dx_disi 30) -> maske g < 90 ve
  r - g > 80 (c3_renk.py).
* ORTAK PARCA: 20 yerde '13 - 14. sorulari asagidaki parcaya gore
  cevaplayiniz.' pembe cerceve + parca sutun basinda; simge cercevenin
  basinda, ilk sorunun numarasi parcanin altinda (tarama blob_yok 20; serit
  hucresi capadan 20 fazla). Capa numaradan `EK_CAPA` (c3_oncul.py), ilk
  sorunun kutusu cercevenin 3 px ustunden `KUTU_UST` (c3_cerceve.py).
* Orta ayrac turuncu cizgi + ustunde dikey camgobegi 'aktif ogrenme
  yayinlari' yazisi cift x 356-367 / tek 373-384 (c3_ayrac.py). Tek SUS
  penceresi cift sayfanin R numarasini (x 379) da silerdi -> yeni genel
  kanca `SUS_PARITE {0: pencereler, 1: pencereler}` (kirp.sayfa_no_lekesi,
  beyaz_sayfa n'yi gecirir). Yazinin gri (doygun olmayan) kenari icin
  sutunlar ayracin disinda: cift L 20-354 / R 371-712, tek L 38-371 /
  R 388-712.
* Pembe sekme kivrimi SUS (62, 114, 600, 712).
* 451 kutu, artik 0; kirp kenar 0, KESIK 0; ortme 41 soru.

## 4. Ortak oncul

* 20 parca, hepsi 'X - (X+1)'. Okuma talimatina kural eklendi: cerceveyle
  baslayan kirpimda govde = cerceve cumlesi + parca + soru koku (komsu_not
  degil). X+1 sorusunun govdesine parca metin olarak eklenir
  (`_a21_gecici/c3_ortak_yama.py`, metin topla'dan sonra; 20/20). Sekle
  dayanan oncul yok -> `ORTAK_ONCUL_YOK` bos.

## 5. Metin

* 12 grup, iki bagimsiz okuma; 43 fark 8 hakemle: okuma_1 24, okuma_2 17,
  ikisi 2. Gorunen `[??]` 0. Kitabin dizgi hatalari basildigi gibi
  ('dger', 'gelmistir', 'Pennysyluvania' ...).

## 6. Mukerrer, ithal, beta

* DB 6182 Turkce satiri; 18 aday, GUCLU 13; ayni hash 0. Eski hat 19 satir:
  modern karsiligi olan 13'u 0114 ile pasif, 6 aktif kalir. Cevap farki
  icerik 3 esleme (T007_03, T012_05, T025_06): basili anahtar degismez.
* 0113 agac (TUR-AKT25PR: 6 bolum, 6 konu), ithal 451 PASIF, 0114 eski hat
  (13 pasif), 0115 toplu beta 451/451. Round-trip (0112 <-> 0115) temiz.
