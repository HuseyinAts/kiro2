# 345 2025 TYT Biyoloji Soru Bankasi -- uretim yontemi ve olcumler

Veri: `biyo345tyt_sorular.json` (1024 soru).
Derleyici: `backend/scripts/kitap/biyo345tyt_derle.py`.
Ithal: `backend/scripts/kitap/biyo345tyt_ithal.py`.
Konu agaci: `backend/alembic/versions/0022_biyo345tyt_konu_agaci.py`.
Kaynak: `veriseti/zkitap/screenshots/345 2025 Tyt Biyoloji Soru Bankasi/`
(235 ekran goruntusu, 1920x1080 PDF viewer; git disinda).

## Gorsel ve OCR hatti (onceki tur)

| olcum | sonuc |
|---|---|
| kaynak ekran goruntusu | 235 |
| soru sayfasi | 219 (16 sayfa sorusuz: 5 on + 6 bolum kapagi + 5 cekim kusuru) |
| cikarilan soru | 1024 = manifest beklentisi 1024 |
| cevabi null | 0 -- 1024 cevabin tamami cevap seridinden okundu |
| dogrulayici K1-K11 | 0 kusur |

Uretim: `backend/scripts/pipeline/sayfa_kirp_zkitap.py` (sayfa + sutun
kirpimi, manifest) ve `backend/scripts/pipeline/dogrula_ocr_json.py`
(K1-K11). Ikisi de PR #270/#271/#272 ile master'da.

## F1 -- konu kanali: sayfanin KENDI baslik bandi

0017 (Mikro Geometri) ve geo345 ile ayni ilke: agac kitabin ICINDEKILER
sayfasindan DEGIL, her sayfanin KENDI BASLIK BANDINDAN uretildi. OCR
ciktisinin sayfa duzeyi `topic_title` alani tam olarak o banttir.

Olcum (birincil kaynak: `ocr_json/`, 15 Eyl 2026):

- 219 soru sayfasinin **112'sinde bant var**, 107'sinde yok.
- Bantli sayfalar 15 farkli metin veriyor. Ikisi ayni baslik:
  `ESEYLI VE ESEYSIZ UREME` ve `ESEYLI ve ESEYSIZ UREME` -- yalnizca harf
  buyuklugu farki. Kanonlastirinca **14 konu** kalir.

### Sifir serbestlik dereceli dogrulama

Bu 14 ad, sayfa sirasinda **tam 14 KOSU** olusturuyor: hicbir konu ikinci
kez acilmiyor, hicbir konu baska bir blogun icinde gorunmuyor. Bant
okumasi yanlis olsaydi bir blogun ortasinda yabanci bir kosu belirirdi.

| kosu (bantli sayfalar) | konu |
|---|---|
| 6-12 | BIYOLOJI VE CANLILARIN ORTAK OZELLIKLERI |
| 18-32 | INORGANIK BILESIKLER, KARBOHIDRATLAR, LIPITLER, PROTEINLER, VITAMINLER |
| 36-46 | ENZIMLER |
| 50-56 | NUKLEIK ASITLER |
| 60-64 | ATP VE SAGLIKLI BESLENME |
| 70-84 | HUCRENIN YAPISI |
| 88-102 | HUCRE ZARINDAN MADDE GECISLERI |
| 108-114 | CANLILARIN CESITLILIGI VE SINIFLANDIRILMASI |
| 118-136 | CANLI ALEMLERI VE VIRUSLER |
| 142-154 | HUCRE BOLUNMELERI |
| 158-168 | ESEYLI VE ESEYSIZ UREME |
| 174-188 | MENDEL GENETIGI, ES BASKINLIK, COK ALELLILIK, KAN GRUPLARI |
| 192-207 | ESEYE BAGLI KALITIM VE GENETIK VARYASYONLAR |
| 213-229 | EKOSISTEM EKOLOJISI VE GUNCEL CEVRE SORUNLARI |

### Bantsiz sayfalar TAHMIN EDILMEDI, OKUNDU

Bloklarin arasinda kalan 107 sayfa bant tasimiyor; hepsi "OSYM Tadinda
Sorular", "Orijinal Sorular", "Karma Sorular" ve "OSYM Kosesi - Cikmis
Sorular" bolumleri (sayfa ust seridi montajiyla goruldu).

Bunlarin bir ONCEKI bloga ait oldugu varsayilmadi, **olculdu**: 14 blogun
tamamini kapsayan 11 ornek sayfada sorularin metni okundu ve 11/11 onceki
blogun konusu cikti. Ornekler:

| sayfa | onceki blok | sayfadaki sorular |
|---|---|---|
| 0013 | Biyoloji ve canlilarin ortak ozellikleri | nilufer yapragi, hidatot -- morfolojik uyumlar |
| 0047 | Enzimler | arjinin sentezinde gorevli enzimler, G6PD eksikligi |
| 0103 | Hucre zarindan madde gecisleri | osmotik basinc, plazmoliz, patates deneyi |
| 0169 | Eseyli ve eseysiz ureme | bal arisinda ureme, gamet birlesmesi |
| 0208 | Eseye bagli kalitim | renk korlugu ve hemofili soyagaci |

Blok siniri bu yuzden "bir sonraki blogun basindan onceki sayfa" alindi.
Sonuc: **1024 sorunun 1024'u bir konu blogunun icinde**, blok disinda 0.

## F2 -- konu agaci: neden yeni bir TYT unite seti

Canli DB olcumu (15 Eyl 2026): BIO agacinda 18 dugum vardi -- kok,
`BIO-OSYM-GENEL` ve 0021'in kurdugu `BIO-U1..BIO-U16`. Bu 16 unitenin
**hepsi AYT mufredati** (Sinir Sistemi, Hormonlar, Duyu Organlari, ...
Bitkilerde Ureme ve Gelisme). Ayni olcumde biyoloji sorularinin 1328'i AYT,
6'si TYT idi.

Bu kitap TYT: OCR ciktisinin 222 sayfasinin 222'sinde `exam_type` = "TYT",
konular 9-10. sinif mufredati. `BIO-U1..U16` ile **tek bir ortusme yok**,
yani var olan bir uniteye baglamak yanlis olurdu. 0022 migration'i 14
konuyu `BIO-T1..BIO-T14` olarak kurar; `LIKE 'BIO-T%'` deseni ne koku, ne
`BIO-OSYM-GENEL`'i, ne de `BIO-U*`'yi kapsar.

Seviye yalnizca UNITE (level 2). Kitapta unite alti konu etiketi YOK; sayfa
ustundeki "Kazanim Odakli / Karma / OSYM Tadinda / Orijinal Sorular / OSYM
Kosesi" konu degil TEST TURUDUR ve soru duzeyinde
`pipeline_metadata.test_turu` olarak tasinir. Var olmayan bir L3 katmani
uydurulmadi.

## F3 -- alel tuzagi: harf buyuklugu ONEMLI

Ilk turda `sik_tekrar` bayragi 9 soruda yandi. Kaynak sebep olculdu: ev
kalibi (geo345/biyo345) siklari `.lower()` ile kiyasliyor. Biyolojide bu
YANLIS: genetik sorularinda siklar yalnizca harf buyukluguyle ayrilir --
alel gosteriminde `A` baskin, `a` cekinik.

Gercek ornek (s0174 sag #5, Mendel genetigi):

```
A: aBCD    B: ABDd    C: ABCD    D: aBcd    E: ABcd
```

`.lower()` ile bunlarin dordu ayni dizgiye cokuyor. Olcum:

| kiyas | "sik tekrar" sayilan soru |
|---|---|
| `.lower()` ile | 9 |
| harf buyukluguna DUYARLI | **0** |

`biyo345tyt_ithal.py` duyarli kiyas kullanir. Testte hem dogru davranis hem
MUTASYON karsiligi civili: eski kural ayni girdide yanlis pozitif uretir ve
test bunu ayrica olcer.

Not: `soru_hash` formulu zaten siklari KUCULTMEZ (yalniz soru metnini
kucultur), yani hash tarafinda bu tuzak yoktu.

## Ithal sonucu (canli DB, olculdu)

```
zaten var: 1, yazilacak: 1023
YAZILDI: 1023 yeni satir
DB'de 345 2025 TYT Biyoloji Soru Bankasi: toplam 1023,
      is_active 0, kapidan gecen 0
```

| denetim | sonuc |
|---|---|
| question_bank / content / metadata / statistics | 1023 / 1023 / 1023 / 1023 |
| is_active, is_public, v_safe_for_beta | 0, 0, 0 |
| koke dusen soru | 0 |
| **AYT unitesine (BIO-U*) dusen soru** | **0** |
| bos metin / gecersiz cevap | 0 / 0 |
| AYT kitabi (345 2025 AYT Biyoloji) | 1315 -- dokunulmadi |

Biyoloji sorularinin sinav turu dagilimi 6 TYT / 1328 AYT iken **1029 TYT /
1328 AYT** oldu.

### Bedava capraz dogrulama

1024 hash'in 1'i canli DB'de zaten vardi ve `OSYM 2025 TYT` etiketliydi --
kitabin bastigi resmi bir OSYM sorusu. Hash `md5(lower(nfc(metin))|A|B|C|D|E)`
oldugu icin metnin VE bes sikkin bayt-bayt ayni olmasi gerekir. `ayristir()`
o satiri `yabanci` dondurdu ve UZERINE YAZMADI.

## Bilinen sinirlar (durustce)

- **SORU GORSELI YOK.** Bu kitabin gorsel hatti sayfa ve SUTUN kirpimi
  uretti, soru kutusu uretmedi; veri setinde kirpim kutusu yoktur. Bu
  yuzden `question_image_url` NULL yazildi (semada zaten 2303 satir boyle).
  **Sekil iceren 334 soru** `bayraklar` icinde `gorsel_yok_sekilli` ile
  isaretlendi -- bu sorular metin olarak eksiktir ve AKTIFLESTIRMEDEN ONCE
  bir kutu tespit turu gerektirir. Sutun kirpiminin dosya adi her satirda
  `pipeline_metadata.sutun_gorseli` olarak durur, yani kutu turu
  calistirildiginda esleme hazirdir.
- **481 sorunun konusu komsu sayfadan geldi** (bantsiz sayfalar);
  `bayraklar` icinde `konu_komsudan` ile isaretli. Blok sinirlari 11 ornek
  sayfayla dogrulandi ama her bantsiz sayfa tek tek okunmadi.
- **Dosya no != basili sayfa.** `0006-0195` kayma 0; `0196/0197/0198` ucu de
  basili 195 (viewer dondu); `0199-0233` kayma +3; `0234/0235` = `0233`
  kopyasi. Korpus basili 1-230; 231-232 hic cekilmemis. `source_page` DOSYA
  numarasidir, basili numara `pipeline_metadata.basili_sayfa`'da ayrica
  durur.
- **Bloom neredeyse tamamen `comprehension`** (1015/1023). Dar kural
  "sayisal sonuc istenen + besi de sayisal sik" biyolojide hemen hic
  tetiklenmiyor; bu bir olcum degil, ev varsayilanidir ve
  `bloom_kaynagi='varsayilan:ev_sozlesmesi'` ile isaretlidir.
- **Cozum dogrulamasi yapilmadi** (urun karari): tek cevap kaynagi kitabin
  basili cevap seridi.

## Beta aktiflestirme (0023_345_beta_onay)

Urun sahibi bireysel insan denetimini ATLAYIP toplu beta onayi verdi
(0014/0016/0018 ile ayni karar). Kapsam karari onundur: "hepsi, ama
TYT'nin sekilli sorulari HARIC".

Kapi yuku olculdu, tahmin edilmedi: `v_safe_for_beta` tanimi pg_views'ten
okundu ve her kosul uc kitap icin AYRI sayildi. Ustteki alti kosul zaten
geciyordu; dordu (quality_review_status, uyum sinyali, APPROVED,
is_active) tum satirlarda ENGEL idi ve migration dordunu de acti.

Nominal kapsam 4712 idi, gercek sayi 4706: geometrinin 6 satiri `sik_bos`
tasiyor ve o bayrak kapinin KENDI kosulu.

| kitap | toplam | acilan | disarida |
|---|---|---|---|
| geometri | 2708 | 2702 | 6 (sik_bos) |
| ayt biyoloji | 1315 | 1315 | 0 |
| tyt biyoloji | 1023 | 689 | 334 (gorsel_yok_sekilli) |

Olcum: `v_safe_for_beta` 8441 -> 13147 (+4706); GEOMETRI 1223 -> 3925,
BIYOLOJI 19 -> 2023. Geri alinabilirlik KANITLANDI: downgrade calistirildi,
havuz tam olarak 8441'e dondu, eklenen dort metadata anahtarindan kalan 0,
ithal metadata'si korundu; sonra tekrar uygulandi, ayni 4706 cikti.

Durustluk: `quality_review_status` `auto_judged_high` yazildi,
`human_verified` DEGIL -- hicbir insan bu sorulari tek tek dogrulamadi.
`is_ai_generated` alanina dokunulmadi, `true` kaldi. Cevaplar
dogrulanmadi; tek cevap kaynagi kitabin basili anahtaridir.

Bu kitabin `konsensus_sinyalleri` degeri (kopyalanmadi, bu belgeden
turetildi): `konu_bandi_sifir_serbestlik`,
`dogrulayici_k1_k11_sifir_kusur`, `manifest_soru_sayisi_ortusmesi`.
Bu kitapta cevap anahtari CIFT OKUNMADI; digerlerinin
`anahtar_seridi_cift_okuma` sinyali burada YOK ve listeye konulmadi.
Metnin guvencesi K1-K11 denetimidir (K3 ureticinin kendi beyanini
yeniden hesaplar, K11 numara surekliligini sayfalar arasi denetler).

Acilan 689 satirin 303'u `konu_komsudan` tasiyor: konusu bantsiz bir
sayfadan devralindi; varsayim 11 ornek sayfada olculdu (11/11 dogru) ama
her bantsiz sayfa tek tek okunmadi. Kapiyi tutan bir kosul degil,
kayit altina alindi.

Disarida kalan 334 sekilli soru bir kutu tespit turunden sonra AYRI bir
migration ile acilacak; `pipeline_metadata.sutun_gorseli` esleme icin
hazir duruyor.
