# Aktif Ogrenme TYT Dilbilgisi Soru Bankasi 2025 -- yontem

Bu belge, kitabin soru ve cevaplarinin nasil cikarildigini ve her iddianin
hangi olcume dayandigini yazar. Rakamlar 16 Eylul 2026 olcumudur.

## 0. Kaynak

    veriseti/zkitap/screenshots/Aktif Ogrenme Tyt Dilbilgisi Soru Bankas<U+0131> 2025/
      sayfa_0001.png .. sayfa_0224.png   (1920x1080, sayfa basina bir goruntu)
      <ayni ad>.pdf                      (34 MB)

PDF'te METIN KATMANI YOK: pymupdf ile 224 sayfanin ucu ornekleme ile
kontrol edildi, `get_text()` uzunlugu 0 ve her sayfa tek bir 1920x1080
gorsel. Yani 1920x1080 TAVAN COZUNURLUKTUR; daha net bir kaynak mevcut
degildir. Bu, asagidaki tek bir kararin (s48 q8) gerekcesidir.

Ekran goruntusu numarasi ile kitabin BASILI sayfa numarasi AYNI: s118'in
sayfa alt rozeti "118" okundu.

## 1. Sayfa siniflandirmasi -- iki bagimsiz kanal

| kanal | olcum | sonuc |
|---|---|---|
| 1. bant renk imzasi | x 620-1340, y 70-160 icinde turuncu>2000 VE mavi>2000 | 86 sayfa |
| 2. cevap seridi | sayfa altinda "Soru N/ X" metni var mi | ayni 86 sayfa |
| OSYM bandi | yesil+fistik imza | s221-224 (4 sayfa) |

UYUSMAZLIK = 0. Toplam soru sayfasi = 90.

Kitabin diger sayfa tipleri (unite ayraci, konu anlatimi, Kavrama Bolumu
"Ornek : N", Uygulama Bolumu "Soru : N") BU FAZIN KAPSAMINDA DEGIL.
Kavrama/Uygulama bolumu 115 sayfa ve yaklasik 271 soru tasiyor; orada da
basili cevap var (Ornek'lerde satir ici "Cevap: X", Uygulama'da sag alt
serit). AYRI FAZ olarak isaretlendi.

## 2. Cevap anahtari -- cift okuma

Cevaplar SORU COZULEREK degil, kitabin kendi basili cevap seridinden
okundu (urun karari; bu depo icin standart).

Okuma A: serit x 690-1280, y 942-976, 2.5x olcek, montaj basina 12 sayfa.
Okuma B: sol ve sag bant AYRI satirlar, metin siniri otomatik bulunur,
         3.2x olcek, montaj basina 14 satir.

Iki okuma FARKLI geometri ve FARKLI olcek kullanir; ayni goruntuyu ayni
sekilde iki kez okumak degildir.

    553 soru, hem numara hem harf karsilastirildi  ->  FARK = 0

### Sifir serbestlik dereceli dogrulama

Bir test, numarasi 1 olan sayfayla baslar ve sonraki 1'e kadar surer. Her
testin numaralari 1..N kesintisiz olmali; olmazsa okuma yanlistir.

    44 test  ->  sureklilik kusuru = 0
    test uzunlugu: 12 soru x24, 13 x12, 14 x5, 11 x1, 10 x1, 18 x1 (OSYM)
    sayfa/test  : 2 sayfa x43, 4 sayfa x1 (OSYM)

Cevap harf dagilimi: A=73 B=120 C=127 D=141 E=92 (toplam 553).

### Ucuncu bagimsiz kanal: DB'deki eski satirlar

DB'de bu kitaptan 17 satir zaten vardi (eski gemini hatti,
`kiro2_batch_v4.14e`). 15'i bu kanalda; kelime kumesi ortusmesi 1.00 ile
her biri tek bir soruya eslesti.

    cevap uyumu: 13 / 15
    FARK       :  2

      s107 q6  -- eski satir C  |  basili serit E
      s33  q4  -- eski satir A  |  basili serit B

Iki serit de 5x buyutmede UCUNCU kez okundu; serit E ve B diyor. Eski
satirlarin cevabi yanlis. Kullanici karari "mevcut satirlara dokunma"
oldugu icin DUZELTILMEDI -- burada kayda geciyor.

## 3. Soru segmentasyonu -- sifir serbestlik dereceli kapi

Her soru, sutun basinda koyu kirmizi bir numara imleciyle ("7.") baslar.
Imlecler sutun icinde tespit edildi:

  * bant alt siniri SAYFA BASINA olculur (tek sayfalarda buyuk bant
    y~155'e, cift sayfalarda kucuk bant y~133'e kadar iner),
  * sayfa ortasindaki dikey yayinevi seridi (x=968) maskelenir -- bu
    serit s168 ve s180'de imlec sanilmisti, olcumle ayiklandi,
  * imlec yuksekligi <= 20 px (rakam yuksekligi ~9 px).

KAPI: bir sayfada bulunan imlec sayisi, o sayfanin cevap seridindeki soru
sayisina ESIT olmali.

    90 sayfanin 90'inda esit  ->  KUSUR = 0

## 4. Metin transkripsiyonu

90 sayfa 1062x1200 cozunurlukte render edilip goruntuden okundu (5 sayfa
dogrudan, 85 sayfa yedi paralel okuyucu ile; hepsi ayni gorev tanimini
kullandi). Roma rakamlarinin hangi sozcuge ait oldugu supheli her yerde
ilgili bolge 3x-22x buyutulerek teyit edildi.

KURAL: kitap ne yaziyorsa o yazildi. Bu bir yazim/dil bilgisi soru
bankasidir; sorularin cogu KASITLI yazim yanlisi icerir ("olsada",
"yemekde", "sekizyuz", "yada", "sokakdan"...). Duzeltmek soruyu
cozulemez hale getirirdi.

### Yapisal dogrulayici (K1-K11)

dosya tamligi, sayfa alani, numara kumesi = anahtar kumesi, numara
tekrari, tam 5 sik (A-E), bos sik, kisa metin, literal \uXXXX sizintisi,
mojibake izi, sik tekrari, kitap ici yinelenen soru.

    90 dosya / 553 soru  ->  1 bulgu

Bulgu: **s48 q8** -- A ve E secenekleri BIREBIR AYNI basili
(`(,) (.) (,) (.)`). Tavan cozunurlukte ayirt edilemiyor (bkz. bolum 0).
KARAR: bu soru ITHAL DISI birakildi.

## 5. Kitabin kendi dizgi kusurlari (13 soruda isaretli)

Hicbiri duzeltilmedi; her biri `pipeline_metadata.kaynak_kusuru` ile
tasinir ve `bayraklar` icinde `kaynak_dizgi_kusuru` gorunur.

| soru | kusur |
|---|---|
| s16 q9 | hem "diyen" hem "sizliyor" altinda "V" basili; okuma sirasina gore IV/V atandi |
| s30 q11 | koku "cumlelerin" diyor, numaralanan ogeler sozcuk |
| s48 q8 | A ve E secenekleri ayni (ithal disi) |
| s110 q10 | koku "hangisi" (tekil), secenekler ikili |
| s130 q13 | E secenegindeki alt cizgiler basilmamis |
| s143 q6 | "D )IV" -- ayrac yanlis konumda |
| s146 q6 | dorduncu secenek "D)" yerine "C)" basili |
| s184 q9 | A secenegindeki konusma cizgisi basilmamis |
| s217 q4 | "C II ve III" -- kapanis ayraci yok |
| s218 q9 | B secenegindeki alt cizgi basilmamis |
| s219 q3 | "C II ve III" -- kapanis ayraci yok |
| s222 q6 | "verilenlerdenhangisi" bitisik basili |
| s224 q15 | "sigina gi" -- araya bosluk girmis |

Ayrica AGAC DUZEYINDE bir kusur: SOZCUK TURLERI - ZARF (BELIRTEC)
unitesinde iki teste de "Konu Testi 1" basili (s117 ve s119). Diger 15
unitede rozet sirasi 1..N duzgun. Cevap seridi numaralandirmasi iki testi
kesin ayiriyor (s117+s118 = 1-12, s119+s120 = 1-12); ikinci test KT2
olarak etiketlendi, basili rozet `basili_test_rozeti` alaninda durur.

## 6. Konu agaci

44 testin ilk sayfasindaki turuncu bant okundu; 17 ad cikti ve bu 17 ad
sayfa sirasinda tam 17 KOSU olusturuyor (hicbir unite ikinci kez
acilmiyor). `0025_dilbilgisi_konu_agaci` bunlari TUR kokunun altina
kurar:

| kod | ad | ithal edilen soru |
|---|---|---|
| TUR-D1 | Ses Bilgisi | 23 |
| TUR-D2 | Yazim Kurallari | 34 |
| TUR-D3 | Noktalama Isaretleri | 36 |
| TUR-D4 | Ekler ve Sozcuk Yapisi | 46 |
| TUR-D5 | Sozcuk Turleri - Isim (Ad) | 26 |
| TUR-D6 | Sozcuk Turleri - Sifat (On Ad) | 25 |
| TUR-D7 | Tamlamalar | 23 |
| TUR-D8 | Sozcuk Turleri - Zamir (Adil) | 25 |
| TUR-D9 | Sozcuk Turleri - Zarf (Belirtec) | 23 |
| TUR-D10 | Sozcuk Turleri - Edat (Ilgec) / Baglac / Unlem | 25 |
| TUR-D11 | Sozcuk Turleri - Fiiller (Eylemler) | 33 |
| TUR-D12 | Fiilimsiler (Eylemsiler) | 24 |
| TUR-D13 | Fiilde (Eylemde) Cati | 40 |
| TUR-D14 | Cumlenin Ogeleri | 35 |
| TUR-D15 | Cumle Turleri | 51 |
| TUR-D16 | Anlatim Bozukluklari | 52 |
| TUR-OSYM-GENEL | OSYM Kitapcik (siniflandirilmamis) | 16 |

NEDEN YENI SET: TURKCE agacinda 7 dugum vardi ve hepsi kaba -- TUR.ANL,
TUR.DIL, TUR.PAR, TUR.YAZ, TYT-TR-01/02/03. "Dil Bilgisi" adi IKI KEZ
gecmekte (TUR.DIL ve TYT-TR-02). Bir dilbilgisi soru bankasinin 16 ayri
unitesini tek bir "Dil Bilgisi" dugumune baglamak konu duzeyinde adaptif
secimi imkansiz kilardi.

Desen `code LIKE 'TUR-D%' OR code = 'TUR-OSYM-GENEL'` mevcut yedi dugumun
HICBIRINI kapsamaz (olculdu: migration oncesi 0 satir). Naif bir `TUR%`
deseni TUR.ANL/TUR.DIL/TUR.PAR/TUR.YAZ'i da yakalardi -- test bu mutasyonu
ayrica olcer.

SEVIYE: yalniz UNITE (level 2). Kitapta unite alti konu etiketi YOK;
"Konu Testi N" / "OSYM Sorulari" konu degil TEST TURUDUR ve soru duzeyinde
tasinir. Var olmayan bir L3 katmani uydurulmadi.

## 7. Ithal

    veriseti/zkitap/cikti/aktif_dilbilgisi_sorular.json     537 soru
    veriseti/zkitap/cikti/aktif_dilbilgisi_dislanan.json     16 soru
    553 = 537 + 16

Dislananlar:
  * 15 -- DB'de zaten olan satirlar (kullanici karari: dokunma, atla)
  *  1 -- s48 q8 (secenekler ayirt edilemiyor)

Ithal PASIF:

    is_active = FALSE, is_public = FALSE,
    is_ai_generated = TRUE, review_status = 'PENDING'

Kosum sonrasi olcum (16 Eyl 2026):

    toplam 537, is_active 0, is_public 0, konusuz 0,
    v_safe_for_beta kapisindan gecen 0

Aktiflestirme AYRI bir karardir ve bu PR'in konusu degildir.

### Adlandirma

Mevcut 17 satirin `source_book` yazimi U+0131 (noktasiz i) tasiyordu ve
`kaynak_sozlesmesi.py`'nin ASCII sartina takiliyordu. Iki yazim yan yana
kalsaydi `normalize_anahtar` ikisini de ayni anahtara cozer, yani ayni
kitabin iki yazimi olusurdu -- 0019'un kapattigi delik. Dogru yazim tahmin
edilmedi, diskteki klasor adinin ASCII katlanmasiyla OLCULDU.
`0026_dilbilgisi_kaynak_adi` yalnizca bu kolonu degistirir; icerik,
cevap, konu baglantisi ve aktiflik durumu degismez ve downgrade ile tam
olarak eski degerine doner.

## 8. Alanlar ve kaynaklari

| alan | deger | kaynak |
|---|---|---|
| correct_answer | A-E | basili cevap seridi, cift okuma |
| primary_topic_id | TUR-D<n> / TUR-OSYM-GENEL | sayfa baslik bandi |
| source_page | 13..224 | dosya no = basili sayfa no (dogrulandi) |
| sutun / pozisyon / soru_no | - | imlec segmentasyonu |
| test_turu / test_no | Konu Testi / OSYM Sorulari | bant + numara surekliligi |
| question_image_url | NULL | kitapta sekilli soru YOK (537/537 sekil_var=false) |
| explanation | NULL | soru cozulmedi (urun karari) |
| osym_year | NULL | kitap "(OSYM'den)" diyor, YIL yazmiyor -- uydurulmadi |
| grade_level | 12 | olculdu: exam_type='TYT' satirlarinin 6396'si 12, 1021'i 11 |
| readability_score | Atesman | services/turkish_readability_service |
| morphology_complexity | heuristik | Zemberek yok; core/turkish_nlp_service yolu |
| bloom_level | 2 / 3 | dar kural: besi de sayisal sik + nicelik sorusu -> 3 (6 soru) |
| zorluk_tahmini | yok | uydurulmadi |

## 9. FAZ 2 -- Kavrama Bolumu "Ornek" + Uygulama Bolumu "Soru"

Kitabin ikinci soru kanali. Konu anlatimi bittigi yerde su bant basilir:

    KAVRAMA BOLUMU  <--  <unite adi>  -->  UYGULAMA BOLUMU

  * SOL sutun  "Ornek : N" -- soru + 5 sik + ADIM ADIM COZUM + satir ici
    "Cevap: X". Cozum kitabin kendi metnidir ve `explanation` alanina
    yazilir; URETILMIS aciklama DEGILDIR.
  * SAG sutun  "Soru : N" -- ayni soru tipinin cozumsuz uygulamasi.
    Cevabi sayfa altindaki basili seritte.

### Sayfa tespiti -- bir kusur ve onarimi

Ilk tarama bandi yalnizca sayfanin UST bandinda (y 70-160) aradi ve 31
sayfa buldu. OLCUM bunun EKSIK oldugunu gosterdi: s11'in cevap seridi
"Soru 2/ C" ile basliyordu, yani "Soru 1" baska bir sayfadaydi. s10'a
bakilinca bant sayfanin ORTASINDA (y~556) cikti -- konu anlatimi bittigi
yerde basliyor.

Tarama tum sayfa yuksekligine (y 70-1000) genisletildi: 42 aday. Bunlarin
3'u yanlis pozitif (s4 icindekiler sayfasi, s134 ve s139 -- ucunde de
cevap seridi YOK). Gercek sayfa sayisi: **39**.

Bu, "bulduk, gecti" denip birakilsaydi 8 sorunun (her unitenin ilk
Uygulama sorusu) sessizce kaybolacagi bir kusurdu.

### Cevap anahtari -- cift okuma

Okuma A: sag alt serit, x 1040-1340, 3.0x, 11 satir/montaj
Okuma B: otomatik metin siniri, 4.2x, 13 satir/montaj

    73 soru, hem numara hem harf  ->  FARK = 0

SIFIR SERBESTLIK DERECELI DOGRULAMA: her unitede Soru numaralari 1..N
kesintisiz (alt harfli "2a"/"2b" ayni numaranin iki parcasi).

    16 unite  ->  sureklilik kusuru = 0

Cevap harf dagilimi (Uygulama): A=9 B=16 C=15 D=16 E=17.

### Ornek <-> Soru eslesmesi

Kitap "Ornek : N" ile "Soru : N"yi AYNI numarayla esler. Ama esleme
BIREBIR DEGIL: uc sayfada (s61, s105, s141) tek bir Ornek'e karsilik
alt harfli IKI Uygulama sorusu var ("Soru : 2a", "Soru : 2b"). Bu kitabin
gercek yapisidir, transkripsiyon hatasi degildir -- s105 orijinal
goruntuden ayrica dogrulandi.

Dogrulayici bunu K4 kapisi olarak kilitler: `ornekler[].no` listesi,
`sorular[].no` listesinin ALT HARFSIZ KOKLERI kumesine esit olmali.

### Yapisal dogrulayici (K1-K12)

    39 dosya / 70 Ornek + 73 Soru = 143 soru  ->  KUSUR = 0

Ek kapilar: Ornek satirlarinda satir ici cevap ve cozum ZORUNLU; Soru
satirlarinda ikisi de YASAK; kitap ici yinelenen soru yok.

22 soruda kaynak dizgi kusuru isaretlendi (bos ayrac, basilmamis alt
cizgi, cozumle soru metni arasinda sozcuk uyusmazligi, eksik virgul...).
Hicbiri duzeltilmedi.

### Ithal

    veriseti/zkitap/cikti/aktif_dilbilgisi_kavrama_sorular.json   141
    veriseti/zkitap/cikti/aktif_dilbilgisi_kavrama_dislanan.json    2

Dislanan 2 kayit, DB'de zaten olan 17 satirin bu kanaldaki ikisidir
(s128 Uygulama #4, s178 Uygulama #5). Kelime kumesi ortusmesi 1.00 ile
eslestiler ve CEVAPLARI DA UYUYOR. Boylece eski 17 satirin tamami
hesaplandi: 15 uyum, 2 fark (s107 q6, s33 q4 -- bolum 2).

FAZ 1 veri setiyle soru_hash cakismasi: 0.

Kosum sonrasi olcum (16 Eyl 2026):

    Konu Testi              521
    Uygulama Bolumu - Soru   71
    Kavrama Bolumu - Ornek   70   (70'inin explanation'i dolu)
    OSYM Sorulari            16
    TOPLAM                  678   is_active 0, konusuz 0, kapidan gecen 0

### Iki kanalin dogrulama gecmisi AYRI tutulur

`pipeline_metadata` alanlari:

    cevap_kaynagi         cevap_seridi        | satir_ici_cevap
    anahtar_cift_okuma    true                | false
    anahtar_dogrulamasi   ..._cift_okuma_...  | satir_ici_cevap_tek_okuma_...

Ornek satirlarinin cevabi CIFT OKUNMADI; "okundu" diye yazilmadi. Test
bu ayrimin metadata'da kaybolmadigini kilitler.

## 10. Bilinen borc

  * Kitabin UCUNCU kanali (unite ayraci sayfalarindaki kucuk alistirmalar,
    konu anlatimi icindeki tablo/sema ornekleri) ITHAL EDILMEDI: bunlarin
    5 sikki ve basili cevabi YOK, dolayisiyla bu semaya girmiyorlar.
  * `scripts/kitap/metin_olcum.py` yeni ithaller icin tek kaynaktir; var
    olan alti ithal script'i hala kendi satir ici kopyasini tasiyor. O
    tasima MEKANIK ve AYRI bir istir. Yeni modulun eski kopyayla birebir
    ayni sonucu urettigi 537 soru x 5 olcumde dogrulandi (fark = 0) ve
    teste baglandi.
  * Mevcut 17 satirin 2'sindeki yanlis cevap duzeltilmedi (bolum 2).

## 11. Beta aktiflestirme -- migration 0027

Kitap PASIF ithal edildi; aktiflestirme AYRI bir karardir ve bu depoda
`v_safe_for_beta` kapisindan gecirilerek yapilir. Kapinin yuku olculdu:

    kosul                                        sonuc
    pipeline_metadata NOT NULL ................. 678/678  geciyor
    demoted_at yok ............................. 678/678  geciyor
    topic_match_quality <> fallback ............ 678/678  geciyor
    match_tier tier1 degil ..................... 678/678  geciyor
    bayraklar.sik_bos yok ...................... 678/678  geciyor
    quality_review_status uygun ................   0/678  TUTUYORDU
    uyum sinyali (6 anahtardan biri) ...........   0/678  TUTUYORDU
    (is_ai_generated=false OR APPROVED) ........   0/678  TUTUYORDU

0027 bu uc kilidi acar. `is_public`e DOKUNULMAZ: bu depodaki dokuz kitap
ithalinin dokuzunda da is_public=0 (olculdu).

### Kapsam 644, 678 degil

`bayraklar.kaynak_dizgi_kusuru` tasiyan 34 satir PASIF birakildi. Bu,
0023'un `sik_bos` / `gorsel_yok_sekilli` disarida birakmasiyla ayni
siniftadir: basili sayfanin KENDISI eksik ya da celiskili. Ornekler:

    s130 q13 -- "alti cizili sozcukler" soruluyor, E'de alt cizgi YOK
    s142 q4  -- "alti cizili eylem" soruluyor, D'de alt cizgi YOK
    s105 q1  -- "alti cizili sozcuk" soruluyor, E'de alt cizgi YOK
    s43  q4  -- noktalama sorusu, C'de iki ayracin ici BOS basilmis
    s146 q6  -- dorduncu secenek "D)" yerine "C) IV" basilmis
    s16  q9  -- hem "diyen" hem "sizliyor" altinda "V" basili

Bolum dagilimi (toplam -> acilan):

    Konu Testi .............. 521 -> 511
    Uygulama Bolumu - Soru ... 71 ->  62
    Kavrama Bolumu - Ornek ... 70 ->  57
    OSYM Sorulari ............ 16 ->  14
                               ---    ---
                               678    644

34 satirin her birinin kusuru `pipeline_metadata.kaynak_kusuru` alaninda
TAM METIN olarak duruyor; tek tek incelenip acilmalari urun sahibinin
kararidir.

### Sinyal listeleri UC KANAL icin AYRI yazildi

Satirlar `anahtar_dogrulamasi` degerine gore ayrilir. Tek liste yazip
hepsine yapistirmak FAZLA IDDIA olurdu.

| kanal | sinyaller |
|---|---|
| Konu Testi + OSYM | sayfa siniflandirmasi iki kanal 0 uyusmazlik; anahtar seridi cift okuma 553 soru fark 0; test ici numara surekliligi 44 test 0 kusur; imlec/anahtar sayisi esitligi 90/90; K1-K11 tek bulgu ithal disi |
| Uygulama - Soru | anahtar seridi cift okuma 73 soru fark 0; unite ici numara surekliligi 16 unite 0 kusur; K1-K12 143 soruda 0 kusur; Ornek-Soru numara eslesmesi K4 kapisi |
| Kavrama - Ornek | K1-K12 143 soruda 0 kusur; Ornek-Soru numara eslesmesi K4 kapisi; satir ici cevap ve cozum zorunlulugu K12 kapisi |

**Ornek kanalinda anahtar CIFT OKUNMADI.** Cevap satir ici "Cevap: X"
ibaresinden BIR KEZ okundu; `anahtar_cift_okuma=false` ve
`anahtar_dogrulamasi` alanlari yerinde kalir ve sinyal listesine olmayan
bir cift okuma YAZILMAZ. Ayni durum 0023'te TYT biyolojinin 689 satirinda
da vardi. Bu ayrimi test kilitler
(`test_ornek_grubu_anahtar_cift_okumasi_iddia_etmiyor`).

### Ne oldugu konusunda durust olma

  * `quality_review_status`: pending -> auto_judged_high. `human_verified`
    YAZILMIYOR; hicbir insan sorulari tek tek dogrulamadi.
  * `review_status`: PENDING -> APPROVED. Bu TOPLU sahip onayidir ve
    metadata'ya `onay_turu='toplu_beta_sahibi'`,
    `bireysel_denetim_yapildi=false` olarak yazilir.
  * `is_ai_generated` true KALIR.
  * CEVAPLAR DOGRULANMADI. Tek cevap kaynagi kitabin basili anahtaridir;
    sinyaller transkripsiyonu ve segmentasyonu dogrular, cevabin kendisini
    degil.

### Eski 17 satir kapsam disi

Hedef sorgusu `source_book` ile DEGIL `pipeline_metadata.ithal_araci` ile
daraltilir. Eski gemini hattindan gelen 17 satir bu alani tasimaz; boylece
onlara dokunulmaz. Bu, testle kilitlidir
(`test_hedef_source_book_ile_degil_ithal_araci_ile_daraltilir`).
