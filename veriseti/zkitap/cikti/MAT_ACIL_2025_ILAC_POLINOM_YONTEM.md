# ACIL 2025 Matematigin Ilaci Polinom -- yontem (ACL25PL)

Tarih: 28 Eyl 2026. Hat: ortak `backend/scripts/kitap/kitap_hat/` (dorduncu
kitap, ilk 'Matematigin Ilaci' duzeni; profil `kitap_hat/profiller/acl25pl.py`).
Kaynak: FERNUS 1920x1080, 288 PNG, kart (589,43)-(1331,1022); basili sayfa =
dosya.

## 1. Kitap yapisi

* 5 bolum (Polinomlar, Carpanlara Ayirma, Ikinci Dereceden Denklemler,
  Parabol, Esitsizlikler); bolum acilisi 'BUNLARI OGREN' sayfasi, bolumler
  arasi bos kapak (s64, 124, 172, 230).
* Konu sayfasi: 'N. SORU TIPI' + ORNEK / COZUM kutulari (kapsam DISI) +
  ayrac cizgisi altinda numarali coktan secmeli sorular (kapsam ICI).
  'PEKISTIRME TESTI' ve 'KARMA TEST - N': numara iki sayfa boyunca surer
  (1-6, 7-12).
* HER sayfanin kendi cevap seridi var (sag altta duz metin '1.C 2.B ...').
  Sayfa turu = serit var mi: 276 test sayfasi, 10 konu (serit yok), 2 kapak.

## 2. Test siniri ve cevap anahtari (iki gecis)

* 1. gecis: her sayfa ayri birim (276), serit okuma A (ileri, 2 okuyucu) ve
  B (geri, 2 okuyucu): 1424/1424 hucre ayni. Seridi '1.' ile baslayan sayfa =
  test baslangici (BAS_SAYFALARI, 163 test); numaralar tum testlerde 1..N
  ardisik (kopukluk 0). Numara blob genisligi ('1' dar) denendi, guvenilmez
  cikti (ayni '1.' 6-12 px) -- terk edildi.
* 2. gecis: tarama `TEST_SINIRI = bas_listesi`; okumalar sayfa sirasiyla
  birlestirildi (p4_bas_yaz.py); A == B, hucre == capa 163/163.
* Glif ucuncu kanal (numara ve harf ayni renk: harf = noktadan sonraki blob,
  `HARF_NOKTA_SONRASI`): 1412 hucre, LOO 1410; 2 uyumsuz (T073#4 B, T077#2 B;
  bolutleme yalniz harf govdesini almis) 5x gozle teyit. T138 (7. B aralikli)
  goz_c. Harf dagilimi A 234, B 294, C 337, D 307, E 252. Soru cozulmedi.

## 3. Capa ve kirpim

* Numara CAMGOBEGI (0,160,224) -> `numara_maskesi`. Okuyucu simgesi 'N. SORU
  TIPI' basligina da konuyor (baslik da camgobegi): `capa_gecerli` numaranin
  saginda ayni satirda camgobegi metin (> 100 px / > 30 kolon) varsa reddeder
  (baslik 208-216 px; soru yanindaki cerceve/sekil <= 28 px; olculdu).
* Numara uzun kesirli sorularda simgenin 38 px altinda: pencere y 64.
* s86 sag sutun 3. soru: okuyucu simgesi YOK -> `EK_CAPA` (numaradan).
* Kutu: konu sayfasinda ilk sorunun tavani ayrac cizgisi (`AYRAC_TAVAN`,
  sutun genisliginin %60'i, <= 3 px kalin; dolu resim alanlari cizgi
  sayilmaz); artik murekkep kapisi sutunun ilk kutusundan
  (`ARTIK_ILK_KUTUDAN`; eksik soruyu serit hucre sayisi kapisi yakalar).
* 1424 kutu, artik 0, kenar 0 (ilk denemede 2 kenar: sol sutun sinirlari
  genisletildi, ayrac tavani eklendi); ortme 13 soru.

## 4. Metin

* 25 grup, iki bagimsiz okuma (3 dalga, <= 20 ajan). 1334 ayni; 90 fark 8
  hakemle: okuma_1 36, okuma_2 24, ikisi 4, yok 26.
* Baski hatasi: s36 sag sutun ortadaki soru '8.' basilmis (konumu 11, serit
  '11.A') -> `BASKI_NUMARA_HATASI`, bayrak `numara_baski_hatasi`.
* T033_08: bolunen ifadede us 6 / 8 ayirt edilemiyor (hakem 16x + goz) ->
  `[??]`. Gorunen `[??]` 5 soru.

## 5. Mukerrer ve eski hat

* DB 20660 satir; 101 aday, 38 GUCLU; ayni hash 0.
* Eski hat 'ACIL-2025-Matematigin Ilaci Polinom': 53 satir aktif; 38'inin
  modern karsiligi var -> 0087 ile pasif; 15 aktif kaldi.

## 6. Ithal ve beta

* 0086 agac (MAT-ACL25PL: 5 bolum x 1 konu), ithal 1424 yeni satir PASIF,
  0087 eski hat 38 pasif, 0088 toplu beta 1419/1424 (5 gorunen `[??]`
  disarida). Round-trip (0085 <-> 0088) temiz.
* exam_type AYT, subject MATEMATIK.
