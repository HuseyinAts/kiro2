# 2019-2020 Aktif 0'dan Baslayanlara Aktif Kimya -- yontem (AKT20K0)

Tarih: 28 Eyl 2026. Hat: ortak `backend/scripts/kitap/kitap_hat/` (profil
`kitap_hat/profiller/akt20k0.py`; Aktif Ogrenme serisinin ILK kitabi, yeni
duzen). Kaynak: FERNUS 1920x1080, 368 PNG, kart (589,43)-(1331,1022).
Kesif: `kesif` araci (120 sayfa) + `_a21_gecici/ak_*.py` olcumleri.

## 1. Kitap yapisi

* Icindekiler s6: 9 unite (Kimya Bilimi .. Kimya Her Yerde); unite acilis
  sayfalari dosya 7, 37, 113, 165, 197, 211, 279, 309, 345 (gozle).
* Konu sayfalari ('KAVRAMA / UYGULAMA BOLUMU'): cozumlu 'Ornek N' ve
  'Soru : Na' alistirmalari -- numara '6a' bicimi, kapsam DISI.
* Test sayfalari: turuncu unite bandi + pembe 'KONU TESTI (N)' sekmesi
  (turuncu >= 1500 px ve pembe >= 300 px). 122 test sayfasi, 13 blok;
  sayfa turu 122 test, 240 konu, 6 kapak.
* Soru numarasi PEMBE (220,0,130) -- yeni `numara_maskesi`.

## 2. Test siniri ve cevap anahtari (iki gecis)

* Her sayfanin altinda iki acik mavi kutu ('Soru 1/ B'); aralarinda sayfa
  numarasi dairesi. 1. gecis sayfa basina serit okumasi A / B (4+4
  okuyucu): A == B 868/868, fark 0; BAS 61 test (Konu Testi cogu iki sayfa).
* Kitapta baski hatalari (gozle): s341-342 (Asitler Konu Testi 5) sorular
  ve serit '1-6' + '6, 7, 8, 10, 11, 12' -> yeni `SERIT_NUMARA_BASKI_HATASI`
  (okunan dizi profildekiyle ayni olmali; sira 7-12). s222 4. soru ve s340
  10. soru numarasi '5.' basilmis (serit dogru) -> `BASKI_NUMARA_HATASI`.
* Glif ucuncu kanal: yeni `ANAHTAR_DISLA_X` (sayfa numarasi rakamlari harf
  sayilmaz) ve iki kutulu serit okuma sirasi (sol kutu tum satirlari, sonra
  sag kutu). 856 hucre, LOO 856 (uyumsuz 0); glif disi test 5 (s34 ince
  font) 5x gozle 'CDDBBCBDEDEC'. Harf dagilimi A 92, B 171, C 206, D 196,
  E 203. Soru cozulmedi.
* Iki satirli seritlerde (cok sorulu sayfa) serit alt siniri kutudaki son
  koyu satirdan (ilk olcum 2. satiri kesiyordu).

## 3. Capa ve kirpim

* Okuyucu simgesi konmamis 2 soru `EK_CAPA`: s108 R '13.'; s196 R '8.'
  (simge ustteki ORTAK TABLODA; capa tablo basindan, 8. sorunun kutusu
  tabloyu kapsar; 9-11 tabloya dayanir).
* Yeni kancalar: `ust_bant(a)` (testin ilk sayfasi bant 99, devam sayfasi
  85), `SUS_BOLGELERI` (pembe sekmenin koyu kivrimi ve sutun sonu mavi
  ucgenler: yalniz DOYGUN pikseller beyazlar, siyah metin kalir).
* SUTUNLAR sol (28, 370) / sag (381, 712): kart kenar golgesi x 22 / 719 ve
  orta ayrac x 371 her satirda koyu (ilk olcum 720 sag sutunun kutularini
  12-35 px'e indirmisti).
* 868 kutu, artik 0; kirp kenar 0, KESIK 0; ortme 174 soru (sag sutun
  simgesi sol sutun satir sonlarinin ustunde).

## 4. Metin

* 17 grup, iki bagimsiz okuma; kimya yazimi DB'deki kimya kitaplariyla ayni
  (`Na_2CO_3`, `SO_4^(2-)`). 753 ayni; 115 fark 8 hakemle: okuma_1 34,
  okuma_2 30, ikisi 11, yok 40.
* Gorunen `[??]` 115 soru: cogu okuyucu simgesinin altinda kalan satir sonu
  (beyaz daire); tahmin yazilmadi.

## 5. Mukerrer ve eski hat

* DB 6161 kimya satiri; 298 aday, 187 GUCLU; 31 soru eski hat satiriyla ayni
  hash.
* Eski hat 'Aktif Ogrenme 0 Baslayanlara Kimya 2019 2020': 520 satir aktif;
  187'sinin modern karsiligi var -> 0100 ile pasif; 333 aktif kaldi (konu
  sayfasi alistirmalari dahil, modern karsiligi yok).

## 6. Ithal ve beta

* 0099 agac (KIM-AKT20K0: 9 unite x 1 konu), ithal 868 yeni satir PASIF,
  0100 eski hat 187 pasif, 0101 toplu beta 753/868 (115 gorunen `[??]`
  disarida). Round-trip temiz.
* exam_type TYT, subject KIMYA.

## 7. Sonradan duzeltme: ortak oncul (AKT20AY'de bulunan sinif, 28 Eyl 2026)

* s196 sag sutun numarasiz ortak tablo + '8., 9., 10., ve 11. sorulari tabloya
  gore cevaplayiniz': tablo yalniz 8. sorunun kirpiminda (EK_CAPA ile), 9-11
  (T032_09 .. T032_11) tablo olmadan cevaplanamaz ama 0101 ile aktif olmustu.
* `ORTAK_ONCUL_YOK` + 0105: bayrak `ortak_oncul_kirpimda_yok`, is_active FALSE
  (gunluklu, geri alinabilir). Aktif 753 -> 750.
