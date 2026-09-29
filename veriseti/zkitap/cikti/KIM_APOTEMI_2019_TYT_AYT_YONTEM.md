# 2019-2020 Apotemi TYT-AYT Kimya Soru Bankasi -- yontem (APO19KM)

Tarih: 29 Eyl 2026. Hat: ortak `backend/scripts/kitap/kitap_hat/` (profil
`kitap_hat/profiller/apo19km.py`; APO19FZ ile ayni Apotemi serisi; kesif
`kesif.py --cikti apo19km`). Kaynak: FERNUS 1920x1080, 352 PNG, kart
(589,43)-(1331,1022); basili sayfa = dosya - 1.

## 1. Kitap yapisi

* Icindekiler dosya 7-9: 19 unite, 116 konu basligi. Test bandi (mavi serit)
  konu degil UNITE adini tasir: konu icindekiler sayfa araligindan, bant adi
  yeni genel kanca `BANT_BOLUM_KAPISI` ile unite adina karsi denetlenir
  (harita.bolum_bant_adi). Bantta farkli basilan uc ad `BANT_ESLER` ile
  (test 26 alt konu adi, 'TEPKIME HIZLARI', 15. unitenin uzun adi).
* 10. unitede icindekiler sayfa numaralari 4 sayfa kaymis ('Sivilar 168'
  cift sayfa; icindekilerde olmayan bir plazma testi): baslangiclar test
  iceriginden gozle (profil yorumu). Sayfa araligi kapisi (her test tek konu
  araliginda) 169 testte temiz.
* Test sayfalari 12-349; her test iki sayfa, 169 test, 1838 soru.
* Sinav etiketi basili DEGIL: `SINAV_KONU` konu duzeyinde MEB 2018 unite
  sinifi (9-10 TYT, 11-12 AYT; karisik unitelerde konu bazinda).

## 2. Cevap anahtari

* APO19FZ ile ayni soluk sari serit (testin son sayfasi altligi). Tek okuma
  (4 okuyucu, 1839 hucre) + glif ikinci kanal: 1838/1839 uyum; 1 uyumsuz
  hucre (T005 #4) 3x gozle 'C' (okuma dogru). `glif_etiket.png` satirlari
  tek harf sekli (A satiri tepe ortasi seridi; takas yok).
* Seritte yanlis basilmis hucre numarasi: test 122 '9-D 9-E' -> yeni genel
  kanca `ANAHTAR_NUMARA_BASKI` {(test, sira): basili} (okuma basildigi
  gibi, numara sira no'ya cevrilir; bayat kayitta durur).
* Test 121 (dosya 252-253): anahtar 11 hucre, sayfada 8. soru BASILMAMIS
  (7 -> 9) -> `YAKALANMAYAN_SORU`. s122 L '4.' okuyucu simgesi yok -> EK_CAPA.
* Harf A 343, B 329, C 344, D 388, E 434. Soru cozulmedi.

## 3. Capa ve kirpim

* Simge L 74 / R 363, numara SIYAH (NUMARA_MASKELERI['siyah']). 3 capa olmayan
  glif: s13 fotograf ici, s91 / s92 ayni sorunun govde satirina ikinci simge.
* Kart kenarinda her satirda gri dikey cizgi x 30 / 710: SUTUNLAR bunlarin
  icinde (yoksa ust sinir bos bandi bulunamiyor, 'cok kisa' 836). Dikey
  APOTEMI sekmesi x 361-380.
* 1838 kutu, artik 0; kirp kenar 0 (s219 'TK' eksen yazisi KENAR_GOZ_ONAY),
  KESIK 0; ust artik 41 kutu gozle: hepsi sorunun kendi yapi formulu ust
  atomlari (onceki soru kalintisi yok).

## 4. Metin

* Kimya kurali (yeni, talimat): iki boyutlu yapi formulu metne aktarilmaz,
  `[yapi]` yazilir (sekil_var); tek satir formul / denklem metin. Sekil satiri
  (`SEKIL_SATIRI`) acik; yapi atomlari `Sekil:` satirina girmez. 178 soruda
  `[yapi]`.
* 29 grup, iki bagimsiz okuma, GRUP HATTI (yeni `metin_iki_okuma grup-fark`):
  bir grubun iki okumasi biter bitmez o grubun hakemi baslar (is akisi,
  bariyersiz). 290 fark (%15.8; APO19FZ %20.9): okuma_1 83, okuma_2 85, ikisi
  21, yok 101. `duzeltme-yaz --hakem 0` kararlari global `karsilastir`
  kapsamiyla denetler.
* Gorunen `[??]` 35 soru -> beta disi. Ortak oncul yok.

## 5. Mukerrer, ithal, beta

* Eski hat 345 satir; 236'sinin modern karsiligi var (0123 pasif). DB tam hash
  carpismasi 17 -- hepsi ayni kitabin eski hat satirlari (0123 sonrasi 0).
  Diger kaynakla cevap farki 15 (bayrak; anahtar basili seritten).
* 0122 agac (KIM-APO19KM: 19 bolum, 116 konu), ithal 1838 PASIF, 0123 eski hat,
  0124 toplu beta 1803/1838. Round-trip (0121 <-> 0124) temiz.
