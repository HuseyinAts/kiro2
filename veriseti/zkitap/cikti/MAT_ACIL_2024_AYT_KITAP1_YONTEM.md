# Acil 2024 AYT Matematik Kitap-1 -- yontem (ACL24AM)

Tarih: 28 Eyl 2026. Hat: ortak `backend/scripts/kitap/kitap_hat/` (profil
`kitap_hat/profiller/acl24am.py`; MOZ Akademi duzeni, kancalar acl24mg'den).
Kaynak: FERNUS 1920x1080, 224 PNG, kart (589,43)-(1331,1022); basili sayfa =
dosya.

## 1. Kitap yapisi

* 7 bolum (Polinom, Ikinci Dereceden Denklem, Karmasik Sayilar, Parabol,
  Fonksiyon Uygulamalari, Esitsizlikler, Trigonometri); Trigonometri testleri
  bantta 'I. BOLUM' .. 'VII. BOLUM' -> 'Trigonometri N. Bolum'.
* Konu anlatim sayfalarindaki halkali ornekler kapsam DISI. Sayfa turu
  ('KONU TESTLERI' sekmesi): 67 test, 147 konu, 10 kapak.

## 2. Cevap anahtari

* Her test tek sayfa, sayfa alti tek satir serit; iki bagimsiz okuma A == B
  340/340; hucre == capa 67/67.
* Glif ucuncu kanal: 329 hucre, LOO 329 (uyumsuz 0); glif disi 3 test (26,
  29, 55) 5x gozle. Harf dagilimi A 55, B 78, C 71, D 75, E 61. Soru
  cozulmedi.

## 3. Capa ve kirpim

* s90 R ust soru numarasi okuyucu diskinin altinda -> `NUMARASIZ_CAPA`
  (basili_no null); s133 R numara simgeden 36 px sagda -> `EK_CAPA`.
* `anahtar_bolgesi`: acl24mg olcumu serit alt cizgisi satirindaki TUM koyu
  pikselin x min/max'ini aliyordu; s33 / s114 / s133'te sol sutunun serit
  hizasindaki sik satiri seridin x0'ini 300'e cekti, sol sutun alt siniri
  serit ustune indi. Okuyucu T029_02'de D/E siklarini kesik bildirdi. Duzeltme:
  alt cizgi satirindaki EN UZUN kosu (acl25s1 `_en_uzun_kosu`).
* Kutu kapisi (`alt_sinir_alti`) genisletildi: serit sutunun ICINDE
  basliyorsa sutunun seritten onceki kismi da taranir (seride 40 px pay:
  acl23kc cevap tablosu cercevesi; sol kenardan 12 px pay: acl25pl sag sutun
  capraz sayfa susu). Mutasyon: eski serit olcumuyle (x0 300) kapi s33, s114,
  s133'u yakaliyor; yedi profilin hepsinde guncel ihlal 0.
* `SAYFA_ALTI` 914 (s33 E) y 893-901, s114 D/E y 899-908; kapi 898 ve
  904'u yakaladi). 340 kutu, artik 0; kirp kenar 0, KESIK 0.
* Yeniden kirpimda 67 kirpim degisti; 66'sinda fark yalniz bos satir
  (`b_kirpim_icerik.py`), icerik farki yalniz T029_02: D) II ve III,
  E) I, II ve III gozle yazildi, kesik notu kalkti.

## 4. Metin

* 8 grup, iki bagimsiz okuma; 35 fark 4 hakemle: yok 21, okuma_2 9,
  okuma_1 3, ikisi 2.
* Gorunen `[??]` 6 soru (T006_03, T010_01 E, T042_02, T066_01 / 02 / 04);
  tahmin yazilmadi.

## 5. Mukerrer ve eski hat

* DB 23938 satir; 12 aday, 3 GUCLU; ayni hash 0.
* Eski hat 'Acil-2024-AYT Matematik Kitap-1': 7 satir aktif; 3'unun modern
  karsiligi var -> 0097 ile pasif; 4 aktif kaldi.

## 6. Ithal ve beta

* 0096 agac (MAT-ACL24AM: 7 bolum, 13 konu), ithal 340 yeni satir PASIF,
  0097 eski hat 3 pasif, 0098 toplu beta 334/340 (6 gorunen `[??]`
  disarida). Round-trip temiz.
* exam_type AYT, subject MATEMATIK.
