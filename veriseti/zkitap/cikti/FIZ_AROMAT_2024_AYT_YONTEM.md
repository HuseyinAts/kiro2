# 2023-2024 AROMAT AYT Fizik Soru Bankasi -- yontem (ARO23AF)

Tarih: 29 Eyl 2026. Hat: ortak `backend/scripts/kitap/kitap_hat/` (profil
`kitap_hat/profiller/aro23af.py`; yeni seri 'Aromat Gercek OSYM Deneyimi';
kesif `kesif.py --cikti aro23af`). Kaynak: FERNUS 1920x1080, 320 PNG, kart
(589,43)-(1331,1022); basili sayfa = dosya.

## 1. Kitap yapisi

* Icindekiler dosya 6: 12 bolum, 22 konu. Bolum acilis sayfalari glifsiz
  (7, 43, 75, 109, 141, 167, 201, 231, 247, 267, 289, 309) -> kapak.
* Test sayfalari: sayfa basina 2 sutun x 2 soru; lacivert bantta BUYUK HARFLI
  konu adi + bordo 'TEST NN' rozeti (testin her sayfasinda). Bolum 5-7 ve 10'da
  bant ust basligi tasir ('ELEKTRIK', 'MANYETIZMA', 'CEMBERSEL HAREKET', 'ATOM
  FIZIGINE GIRIS'): `BANT_ESLER` demet degeri (yeni: bir bant birden cok konu);
  konu sayfa araligindan.
* Test siniri iki gecisli (`bas_listesi`): 145 test (bolum sonu testleri uc
  sayfa / 12 soru, digerleri iki sayfa / 8 soru), 1167 soru.
* Sinav AYT; sinif basili DEGIL: MEB 2018 unite sinifi (11 / 12), `SINAV_KONU`.

## 2. Cevap anahtari

* HER test sayfasinin sag altinda ince soluk kirmizi cerceveli kutu, gri
  '1-D 2-B ...' (6 satir yuksek yazi), sagda bordo ok sekmesi. `anahtar_bolgesi`:
  sekme (>= 10 sutunluk kosu; kutunun koyu sol kenari tekil sutun olarak maskeye
  girebiliyor) + alt kenar cizgisi kosusu; 302/302 test sayfasi.
* Glif harf bolutu (yeni, profil `harf_bloblari`, seri ortak): harf = hucrenin
  SON sutun kosusu (esik 200). APO19MT'nin 'ust ucte birde murekkep' kurali bu
  yazida B / E'yi tek sutuna indiriyordu (vektorler ayni, uzaklik 0). Ara surum
  (ilk tire kosusu) 1161/1167 uyum verdi; 6 uyumsuz hucre 6x NEAREST gozle
  okumayla ayni cikti. Son surum 1167/1167 bolut, LOO 1167/1167 uyum (ARO23TF'de
  1137/1137).
* Ek kanal olarak ikinci bagimsiz okuma (B, ters sira): A == B 1167 hucre +
  bant. `bas_listesi` tek okumada B yerine A kullanir (yeni; bu kitapta B var).
* Harf A 188, B 250, C 268, D 224, E 237. Soru cozulmedi.

## 3. Capa ve kirpim

* Simge L 34 / R 360, numara siyah. 2 capa olmayan glif (sekil ici / numarasiz),
  sayfa capa == hucre (gecis1 kapisi temiz).
* Ust bant (lacivert serit + rozet) y 110'da biter: UST_BANT 112. Altlik (sayfa
  no dairesi y ~911, renkli cizgi y 917-921): SAYFA_ALTLIGI_Y 905.
* 1167 kutu, artik 0; kirp kenar 0, KESIK 0; ust artik 0.

## 4. Metin

* 19 grup, iki bagimsiz okuma, grup hatti (is akisi; APO19KM ile ayni anda
  kosuldu). 152 fark (%13.0): okuma_1 62, okuma_2 51, ikisi 9, yok 30.
* Sekil satirinda sekil BASLIKLARI ('Sekil 1', 'Sekil 2') gruplar arasi farkli
  hakem kararina ugradi (g03/g15 'girer', g05 'girmez'): 48 soruda basliklar
  mekanik olarak cikarildi (`_c7_ak/ek_duzeltme.json`, `c7_sekil_baslik.py`);
  kural metin.SEKIL_SATIRI_KURALI'na eklendi (sonraki kitaplar).
* Gorunen `[??]` 26 soru. Ortak oncul yok.

## 5. Mukerrer, ithal, beta

* DB 8987 satir; tam hash 0, kitap ici 0, aday 0. Eski hat yok.
* 0125 agac (FIZ-ARO23AF: 12 bolum, 22 konu), ithal 1167 PASIF, 0126 eski hat (0),
  0127 toplu beta 1141/1167 (26 gorunen `[??]`). Round-trip (0124 <-> 0127) temiz.
