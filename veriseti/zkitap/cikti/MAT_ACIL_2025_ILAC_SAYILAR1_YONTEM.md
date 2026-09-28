# ACIL 2025 Matematigin Ilaci Sayilar-1 -- yontem (ACL25S1)

Tarih: 28 Eyl 2026. Hat: ortak `backend/scripts/kitap/kitap_hat/` (profil
`kitap_hat/profiller/acl25s1.py`; seri sabitleri acl25pl'den import).
Kaynak: FERNUS 1920x1080, 176 PNG, kart (589,43)-(1331,1022); basili sayfa =
dosya.

## 1. Kitap yapisi

* 5 bolum (Sayilar, Asal Sayilar, Sayi Basamaklari, Bolme Islemi, Rasyonel
  Sayilar); bolum acilisi 'BUNLARI OGREN' sayfasi, bolumler arasi kapak
  sayfalari (s41-42, 81-82, 107-108, 139-140).
* 'Matematigin Ilaci' duzeni (acl25pl ile ayni): her sayfanin kendi cevap
  seridi; 'PEKISTIRME TESTI' / 'KARMA TEST - N' numarasi iki sayfa boyunca
  surer. Bu ciltte fark: soru numarasi SIYAH kalin ('1.'), serit sag altta
  CERCEVELI tablo (ust cizgi y 884, alt y 902).
* Sayfa turu: 162 test, 9 konu, 5 kapak.

## 2. Test siniri ve cevap anahtari (iki gecis)

* 1. gecis: her sayfa ayri birim, serit okuma A (ileri) ve B (geri) -> seridi
  '1.' ile baslayan sayfa = test baslangici (BAS_SAYFALARI, 97 test).
* 2. gecis: `TEST_SINIRI = bas_listesi`; A == B 915/915; hucre == capa 97/97.
* Glif ucuncu kanal (`HARF_NOKTA_SONRASI`, `HARF_NOKTA_ARALIK` 10): 911 hucre,
  LOO 911/911 uyum; bolutlenemeyen T3 5x gozle (goz_c). Harf dagilimi A 149,
  B 171, C 175, D 236, E 184. Soru cozulmedi.

## 3. Capa ve kirpim

* Siyah numara -> `numara_maskesi` (koyu + notr); ORNEK / COZUM kutusundaki
  simge capa degil (`capa_gecerli`: numara zemini renkli ise red).
* `PENCERE` y 64 (uzun kesirli sorularda numara simgenin altinda), x0 +14
  (orta ayracin dikey harfleri alinmasin); `NUMARA_H` 9-16 ('N. Soru Tipi'
  kelime blobu h 7 disarida).
* s146 konu sayfasi 1. ve 2. soru: okuyucu simgesi YOK -> `EK_CAPA`.
* Serit x araligi = satirdaki en uzun kesintisiz kosu (s76: sekil pikselleri
  serit satirina iniyor).
* `SAYFA_ALTI` 922 (ilk deger 878, 10 sayfada sol sutun son sorusu kesildi;
  metin okumasinda bulundu, yeniden kirpildi ve yeniden okundu).
  `SERIT_ORTUSME_EN_AZ` 60 (s80: serit sol sutuna 20 px giriyor, T040_06 D/E
  kesikti). Bu iki hata `KITAP_ISLEME_DARBOGAZ.md` madde 9'u dogurdu; yeni
  `kirp.py` KESIK kapisi ile mutasyonla yeniden uretildi ve yakalandi.
* 915 kutu, artik 0, kenar 0, kesik 0; ortme 23 soru.

## 4. Metin

* 17 grup, iki bagimsiz okuma tek dagitimda. 865 ayni; 50 fark 6 hakemle:
  okuma_2 22, okuma_1 16, yok 12.
* Yeniden kirpim sonrasi goz yamasi: T040_06 D) 25 m, E) 30 m (onceki `[??]`);
  T076_04 kesik notu kalkti (siklar tam). Gorunen `[??]` 0.

## 5. Mukerrer ve eski hat

* DB 22085 satir; 34 aday, 20 GUCLU; 1 hash carpismasi (baska kaynakta ayni
  soru; ithal ayni id).
* Eski hat 'ACIL-2025-Matematigin Ilaci Sayilar-1': 23 satir aktif; 19'unun
  modern karsiligi var -> 0091 ile pasif; 4 aktif kaldi.

## 6. Ithal ve beta

* 0090 agac (MAT-ACL25S1: 5 bolum x 1 konu), ithal 915 yeni satir PASIF,
  0091 eski hat 19 pasif, 0092 toplu beta 915/915. Round-trip (0089 <-> 0092)
  temiz.
* exam_type TYT, subject MATEMATIK.
