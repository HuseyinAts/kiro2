# ACIL 2025 Matematigin Ilaci Sayilar-2 -- yontem (ACL25S2)

Tarih: 28 Eyl 2026. Hat: ortak `backend/scripts/kitap/kitap_hat/` (profil
`kitap_hat/profiller/acl25s2.py`; serit / sayfa turu acl25pl'den, numara /
capa acl25s1'den). Kaynak: FERNUS 1920x1080, 192 PNG, kart
(589,43)-(1331,1022); basili sayfa = dosya.

## 1. Kitap yapisi

* 5 bolum (Denklemler, Esitsizlikler, Mutlak Deger, Uslu Sayilar, Koklu
  Sayilar); bolum acilisi 'BUNLARI OGREN' sayfasi.
* 'Matematigin Ilaci' duzeni: her sayfanin kendi cevap seridi (duz metin,
  acl25pl gibi); soru numarasi SIYAH kalin (acl25s1 gibi). s1 (kapak)
  `KAPAK_SAYFALARI` ile sayfa turunden disarida.
* Sayfa turu: 179 test, 9 konu, 4 kapak.

## 2. Test siniri ve cevap anahtari (iki gecis)

* 1. gecis sayfa basina serit okumasi A / B -> BAS_SAYFALARI (110 test);
  2. gecis `bas_listesi`; A == B 938/938; hucre == capa 110/110.
* Glif ucuncu kanal: 938 hucre, LOO 926; 12 uyumsuzun hepsi B / E; 12'si de
  5x gozle teyit edildi. Harf dagilimi A 151, B 176, C 253,
  D 207, E 151. Soru cozulmedi.

## 3. Capa ve kirpim

* Okuyucu simgesi konmamis 6 soru `EK_CAPA` (s49 L/R, s112 L, s113 L, s171
  L/R; numaradan, gozle).
* `SAYFA_ALTI` 922, `SERIT_ORTUSME_EN_AZ` 60 (acl25s1 dersleri);
  `AYRAC_PAY` 7 (T024_01 ustunde logo kuyrugu -> kenar ihlali).
* 938 kutu, artik 0; kirp kenar 0, KESIK 0 (#353 kapisi); ortme 12 soru.

## 4. Metin

* 17 grup, iki bagimsiz okuma. 868 ayni; 70 fark 7 hakemle: okuma_1 26,
  okuma_2 26, ikisi 3, yok 15.
* Ortak bilgi kutusuna dayanan sorular talimatta (kutu kirpimda yoksa
  kaynak_kusuru). 1 cikmis soru etiketi (T064_11 'AYT / 2023', kirpimda
  basili; `BEKLENEN_ETIKET` 1).
* Gorunen `[??]` 5 soru (T029_06 C sikki sembol, T084_04 / T102_09 / T104_12
  soluk isaret, T085_07 ekran goruntusu ussu); hakem piksel buyutmesiyle
  karar veremedi, tahmin yazilmadi.

## 5. Mukerrer ve eski hat

* DB 23000 satir; 217 aday, 43 GUCLU; ayni hash 0.
* Eski hat 'ACIL-2025-Matematigin Ilaci Sayilar-2': 53 satir aktif; 43'unun
  modern karsiligi var -> 0094 ile pasif; 10 aktif kaldi.

## 6. Ithal ve beta

* 0093 agac (MAT-ACL25S2: 5 bolum x 1 konu), ithal 938 yeni satir PASIF,
  0094 eski hat 43 pasif, 0095 toplu beta 933/938 (5 gorunen `[??]`
  disarida). Round-trip (0092 <-> 0095) temiz.
* exam_type TYT, subject MATEMATIK.
