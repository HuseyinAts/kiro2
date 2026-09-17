# Bilgi Sarmal AYT Edebiyat Soru Bankasi -- uretim yontemi ve olcumler

Veri: `bilgi_sarmal_edebiyat_sorular.json` (1597 soru).
Konu agaci: `bilgi_sarmal_edebiyat_konu_agaci.json` (58 dugum).
Kaynak: `veriseti/zkitap/screenshots/Bilgi Sarmal Ayt Edebiyat Soru Bankasi 2024/`
(416 PNG + PDF; ikisi de git disinda).
Ithal: `scripts/kitap/bilgi_sarmal_edebiyat_ithal.py`, migration `0031`.

Her asama bir oncekini SINAR; her iddia ayni kapsamda olculmustur.
Faz 0 kesif fisi: `EDB_KESIF.md`.

## 0. Kaynak ve TAVANI

Kaynak, kitabi gosteren bir okuyucu uygulamasinin ekran goruntuleridir:
416 sayfa, her biri 1920x1080 PNG. PDF'te METIN KATMANI YOK -- olculdu
(orneklenen sayfalar tek bir gomulu 1920x1080 gorsel tasiyor). Daha
yuksek cozunurlukte bir kaynak YOKTUR.

Sayfa karti goruntunun icinde sabit bir dikdortgen kapliyor -- BU KITAP
ICIN olculdu, kardes kitabin degeri VARSAYILMADI:

    x 596-1323, y 46-1013   ->  728 x 968 piksel

(Kardes kitap BS TYT Turkce'de 592-1328 / 42-1016 = 736x974 idi; 4 px
fark bu yuzden olcumle belirlendi.) Kirpim 2x buyutulerek okundu.

## 1. Sayfa yapisi

| dosya | icerik | tespit kanali |
|---|---|---|
| 1-3 | kapak, kunye/yazarlar, SUNU | goz |
| 4-7 | ICINDEKILER (4 sayfa) | goz |
| 8-9 | kavram semasi / GUZEL SANATLAR bilgi sayfasi | goz |
| 10, 53, 106, 257, 345 | BOLUM ayraci (1..5. BOLUM) | sari bant |
| 11, 54, 107, 258, 346, 406, 407 | SORDUK/SORDULAR (7 sayfa) | sari bant + goz |
| 12-405 | test soru sayfalari (ayrac/SORDUK haric 386) | -- |
| 408 | CEVAP ANAHTARI kapagi | goz |
| 409-416 | CEVAP ANAHTARI (8 sayfa, basili 109-116) | yatay cetvel 14-20 |

Basili sayfa numarasi govdede dosya numarasiyla BIREBIR ayni; 11 sayfada
goruntuden dogrulandi (f12, f13, f50, f100, f200, f300, f350, f390, f400,
f403, f405). Anahtar bolumunun KENDI numaralandirmasi var (f409 -> 109).

### Bagimsiz kanal: test baslangic sayfalari

Baslik bandi piksel olarak sayildi (kart y 30-100, notr gri > 8000 px) ve
**130 sayfa** bulundu. Bu olcum ANAHTAR OKUNMADAN ONCE yapildi.
Anahtardan cikan 130 `Sayfa:` degeri bu listeyle **BIREBIR ayni** cikti.
Yani test sayisi ve yerleri iki bagimsiz kanaldan ayni geldi.

## 2. Cevap anahtari -- IKI AYRI BASILI KAYNAK

Kitapta cevap iki yerde basili; ikisi de KITABIN KENDISI. Soru HICBIR
asamada cozulmedi.

### 2a. Kitap sonu anahtari (f409-416) -- CIFT OKUMA

Bicim: `Test N: <konu>   Sayfa: <s>` + 6 sutunlu izgara.

Iki bagimsiz okuma, farkli geometri ve farkli olcek, okuyuculara beklenen
sayi SOYLENMEDI:

  * okuma A: 16 sutun seridi, 3x buyutme, 4 okuyucu
  * okuma B: 8 tam sayfa, 2.5x buyutme, 4 okuyucu

Sonuc: her iki okuma da **130 blok / 1572 cevap**; blok ve cevap sayilari
grup grup ayni (32/36/36/26 blok, 362/405/410/395 cevap).

Fark **1 girdi**: f414 sol sutun "SARMAL TEST - 3" (Sayfa: 243), soru 12
-- A "C", B "D". Iki hakem, A/B'nin ne dedigi SOYLENMEDEN, farkli
kaynaklardan (A seridi / B tam sayfasi) yuksek buyutmede okudu:
**2/2 "D"**. Anahtar "D" olarak kapatildi.

Ayrica 2 blokta konu adinda sapka farki ("Dini" / "Dini"); B okumasi esas
alindi. Cevap harflerinde baska fark yok.

### 2b. SORDUK/SORDULAR sayfalari -- sayfa ici KIRMIZI sik

7 sayfa (f11, f54, f107, f258, f346, f406, f407), her sayfada 4 kutu =
**28 soru**. Bu sorular kitap sonu anahtarinda YOK; dogru sik kutunun
icinde KIRMIZI basili.

Iki bagimsiz okuma: birincisi soruyu da yazdi, ikincisine YALNIZCA
"hangi sik kirmizi" soruldu (soru metni okutulmadi, dogru cevabi
dusunmek acikca yasaklandi). Sonuc **28/28 ayni**, fark 0.

Harf dagilimi A 14 / B 4 / C 4 / D 2 / E 4. A'nin fazlaligi kutu
sirasindan ya da kutu turunden gelmiyor (capraz sayim yapildi) ve f54
kutu 2'de GOZLE teyit edildi ("A) Kahramani ruhsal derinlikleriyle
tasvir edilmistir." kirmizi basili). Kitabin ozelligi.

Kutularin 14'u yayinevinin kendi sorusu ("AYT Edebiyat"), 14'u CIKMIS
sinav sorusu (etiket ustte basili: AYT/LYS + yil; olculen yillar
2017-2022).

### 2c. Kitabin kendi tekrari -- iki kaynak birbirini teyit etti

3 soru kitapta IKI KEZ basili: bir kez testte, bir kez SORDUK sayfasinda
(s128 q4 = s406 k1, s268 q4 = s258 k1, s351 q1 = s346 k1 -- ayni hash).
Iki BAGIMSIZ cevap kaynagi (kitap sonu anahtari / sayfa ici kirmizi sik)
bu ucunde de AYNI harfi verdi (A, A, C). `id = uuid5(hash)` benzersiz
olmak zorunda oldugu icin veri setinde TEST satiri tutuldu,
`sorduk_tekrari=true` ve `cevap_kaynagi=..._kirmizi_sik_teyitli` yazildi.

## 3. Sifir serbestlik dereceli kapilar

| kapi | sonuc |
|---|---|
| her testte numaralar 1..N kesintisiz | 130 testte 0 kusur |
| anahtardaki `Sayfa:` degerleri kesintisiz ARTIYOR | 0 kusur |
| okunan soru sayisi == anahtardaki soru sayisi | 130/130 test |
| anahtarin 130 `Sayfa:` degeri == piksel kanalinin 130 test basligi | 130/130 |
| bolum numaralari 1..5 kesintisiz ve sirali | 0 kusur |
| cevap harfleri A-E | 0 kusur |
| K1-K12 yapisal dogrulayici | 1597 satirda 0 kusur |

## 4. Soru sayfalari -- transkripsiyon

386 test sayfasi, testlerin sinirlarina gore **32 gruba** bolundu ve her
grup ayri bir okuyucuya verildi (2x buyutulmus sayfa karti). 7 SORDUK
sayfasi ayri bir okuyucuya gitti. Okuyuculara testlerin kac soruluk
oldugu SOYLENMEDI.

KURAL: kitap ne yaziyorsa o. Bu bir EDEBIYAT kitabidir; eski yazimlar ve
ozel imla kasitlidir, hicbiri duzeltilmedi. Cozunurluk kaynakli supheyi
kusur diye isaretlemek acikca yasaklandi.

Okunan: **1572** test sorusu + 28 SORDUK = 1600; kitabin kendi 3 tekrari
tekillestirilince **1597**.

### Bagimsiz segmentasyon kanali

Okuyucu simgesi GRUPLARI piksel duzeyinde sayildi (metin hic okunmadan):

    1948 simge grubu (test sayfalarinda)  vs  1572 okunan soru
    772 sutun yuvasinin 565'inde sayim AYNI
    207 sapmanin TAMAMI ayni yonde (simge >= soru); TERSI 0

Sapmanin nedeni OLCULDU, varsayilmadi: okuyucularin "soru yok" dedigi 16
sayfa (s64, s70, s91, s94, s95, s96, s99, s160, s161, s212, s290, s294,
s334, s335, s350, s368) 0 soru tasir ama sayfa basina 4-10 simge grubu
tasir. Cunku kitabin ONEMLI / UNUTMA / DIKKAT / OGREN bilgi kutulari da
okuyucudan ayni simgeleri alir. Ayni bulgu BIYO345_YONTEM'de de kayitli.
Yani bu kanal UST SINIR verir, esitlik kapisi degildir; ama "simge <
soru" vakasinin 0 olmasi UYDURULMUS soru olmadigini gosterir.

## 5. Okuyucu simgesi ortmesi -- KURTARILDI

Kardes kitapta (BS TYT Turkce) bu okuyucunun buyutec simgesi sol sutunun
satir sonlarini ortuyor ve 1468 sorunun 451'inde (%30.7) metnin bir
bolumu baglamdan tamamlanmak zorunda kalmisti; ikinci kopya piksel piksel
ayni oldugu icin kurtarma yolu YOKTU.

Bu kitapta durum farkli:

### Olcum duzeltildi

Ilk olcum murekkebi `min(RGB)<130` sayiyordu; bu turuncu sutun ayracini,
cyan bilgi kutusu kenarini ve sari susleme ucgenlerini de "metin" sayar.
8 orneklik goz kontrolunde GORULDU ve duzeltildi: metin = `max(RGB)<150`
ve `(max-min)<60` (koyu VE notr).

    1984 simge blogu
     277 blok -- KIRLENMIS olcum (temas >= 6 px)
     133 blok -- DUZELTILMIS olcum: gercek metin temasi (%6.7 ust sinir)
     145 blok -- yalnizca renkli ogeye temas ediyordu

Yigilma testi: simge bandindaki metin satirlarinda "disk sol kenari -
metnin en sag x" mesafesi 1 px olanlarin orani %4.15; ayni sayfalardaki
simgesiz kontrol satirlarinda %1.15 (3.6 kat). Kirpilma sinyali gercek
ama 133 blokla sinirli.

### Kurtarma kanali (BS Turkce'de yoktu)

Ayni kitabin ikinci bir yakalamasi var: `screenshots/Bilgi Sarmal Ayt
Edebiyat Soru Bankasi` (2023-2024 baskisi). Simgeleri ~7 px KAYIK: ayni
sayfada simge maskelerinin yalnizca ~%35'i ortusuyor (olculdu). Govdede
303 sayfa iki baskida ayni icerikte oldugu icin B'de ortulen bolge A'da
ACIKTADIR.

Ortme temasi olan 121 sayfanin 92'si bu kosulu sagliyor; okuyuculara o
sayfalarin "_alt" dosyasi verildi ve kurali soylendi: satir sonu simgenin
altinda kaliyorsa _alt'tan oku, yoksa TAHMIN ETME, bayrakla.

Sonuc: **1597 satirda kalan ortme bayragi 2**, ikisi de yalnizca SORU
NUMARASININ ortulmesi (s26 q6, s27 q10); metin degil. Numaralar zaten
numara surekliligi kapisiyla dogrulandi.

## 6. Bu kitap AYRI BIR BASKI -- kopya degil

Iki klasorun sayfa karti icindeki tam sayfa piksel farki 416/416 sayfada
sifirdan buyuk (BS Turkce'de ikinci kopyada fark 0 idi). Hizalanmis
murekkep maskesi Jaccard'i:

    318 sayfa  J >= 0.85  -> ayni icerik, render gurultusu
     98 sayfa  J <  0.85  -> GERCEKTEN farkli
    (govde 12-405: 303 ayni, 91 farkli)

Goz kontrolu: s50'de soru 9 revize edilmis (B'de "Ahmet Hamdi Tanpinar",
A'da yalnizca "Tanpinar"); s48'de soru 11 ve 14 TAMAMEN BASKA SORULAR.

Bu ithal **2024 baskisini** kapsar (daha yeni; orneklerde metin daha
tam). 2023-2024 baskisinin farkli 91 govde sayfasi AYRI bir is olarak
durur ve veri setine GIRMEDI -- urun sahibi karari (plan D2).

## 7. DB ortusmesi olculdu

  * `id` (= uuid5(soru_hash)) carpismasi: **0 / 1597**
  * Edebiyat/Turkce alanindaki 3130 mevcut satira karsi kelime kumesi
    ortusmesi >= 0.75 olan **tek** aday: s76 q12 (j = 0.80). GOZLE
    incelendi: ortusme yalnizca kalip soru kokunden geliyor
    ("Asagidakilerden hangisinde verilen ... ayrac icindeki belirleme
    uyumlu degildir?"); biri mesnevi-yazar eslestirmesi, oteki cumle
    kipleri. Icerik tamamen baska. **Gercek kopya YOK.**

## 8. Konu agaci (0031)

EDB kokunun altinda bu isten once YALNIZCA `EDB-OSYM-GENEL` vardi;
Edebiyat agaci pratikte yoktu. 0031 ile **5 bolum + 53 konu** dugumu
eklendi (58 dugum, hepsi bu kosumda olusturuldu).

Dugum adlari UYDURULMADI: kitabin kendi cevap anahtarindaki bolum
basliklari ve test konu adlaridir. SARMAL TEST / OSYM TIPI / Roman Karma
gibi KARMA testler ve SORDUK/SORDULAR sorulari bir konuyu degil bolumun
tamamini tarar; bunlar konu dugumune DEGIL bolum dugumune baglanir
(270 satir, `konu_bolum_duzeyinde` bayragi).

Downgrade yalnizca kendi GUNLUK'undeki dugumleri siler ve soru tasiyan /
cocugu olan dugume dokunmaz.

## 9. Alanlar ve kaynaklari

| alan | kaynak |
|---|---|
| question_text, a-e | sayfa goruntusunden okuma (2x kirpim, gerekirse _alt) |
| correct_answer | kitap sonu anahtari (cift okuma) ya da sayfa ici kirmizi sik (cift okuma) |
| explanation | **NULL** -- kitabin soru sayfalarinda cozum yok, uydurulmadi |
| primary_topic_id | anahtarin bolum/konu basliklari (0031 agaci) |
| source_page | basili sayfa numarasi (= dosya numarasi) |
| osym_year | yalnizca SORDUK cikmis sorularinda, kutu etiketinden |
| word_count, readability, morphology, bloom | `scripts/kitap/metin_olcum.py` |
| is_active / is_public / review_status | FALSE / FALSE / PENDING |

## 10. Ithal sonrasi olcum (17 Eyl 2026)

    veri setinde 1597 soru
    on kontrol: 5 sik + dolu anahtar + dolu metin + EDB-BS konu kodu
                + tanidik cevap kaynagi + benzersiz hash -- TEMIZ
    zaten var: 0, yazilacak: 1597
    YAZILDI: 1597 yeni satir

    DB: toplam 1597 | is_active 0 | is_public 0 | is_ai_generated 1597
        review_status PENDING 1597 | v_safe_for_beta kapidan gecen 0
        explanation dolu 0 | question_image_url dolu 0

    bayraklar: gorsel_yok_sekilli 64, konu_bolum_duzeyinde 270,
               sorduk_sordular_sayfasi 25, cikmis_soru 14,
               kaynak_dizgi_kusuru 8, okuyucu_simgesi_ortmesi 2,
               sik_bos 0

    cevap kaynaklari: kitap_sonu_anahtari 1569,
                      ..._kirmizi_sik_teyitli 3, sayfa_ici_kirmizi_sik 25

    EDB-BS agaci: 58 dugum | alembic head: 0031_bs_edebiyat_agac
    modern ithal ders toplami EDEBIYAT: 24 -> 1621

Testler: `tests/e2e/test_bilgi_sarmal_edebiyat_ithal.py` -- 44 test gecti.

## 11. Bilinen borc

  * **64 soru sekil/tablo iceriyor ama soru kirpimi URETILMEDI**
    (`gorsel_yok_sekilli`); bunlar ogrenciye sekilsiz gosterilirse
    cozulemez. Aktiflestirme bu bayragi disarida birakmalidir.
  * 8 satirda kitabin KENDI dizgi kusuru isaretli
    (`kaynak_dizgi_kusuru`); metni `kaynak_kusuru` alaninda duruyor.
  * **TAM ikinci okuma YAPILMADI.** 3 sayfalik bagimsiz teyit okumasi
    (s200, s320, s380; 11 soru) yapildi: farklarin tamami tirnak/tire
    glif varyantiydi, TEK icerik farki s380 q22'de cikti ve goruntuden
    4x buyutmede karara baglandi (kitap "evlilik" yaziyor; ilk okuma
    "evilik", teyit okumasi ise ayni soruda "romandir" demisti -- her iki
    okuyucu birer karakter hata yapti). Duzeltme veri setinde ACIK olarak
    listelidir (`teyit_duzeltmesi`). Olculen tek-okuma hata mertebesi
    ~1 karakter / ~3000 karakter.
  * 2 satirda soru NUMARASI okuyucu simgesiyle ortulu (metin degil).
  * 2023-2024 baskisinin farkli 91 govde sayfasi islenmedi.
