# 345 2025 AYT Fizik Soru Bankasi -- uretim yontemi ve olcumler

Veri: `345_ayt_fizik_sorular.json` (1308 soru).
Konu agaci: `345_ayt_fizik_konu_agaci.json` (60 dugum).
Kaynak: `veriseti/zkitap/screenshots/345 2025 Ayt Fizik Soru Bankasi/`
(392 PNG + PDF; ikisi de git disinda).
Ithal: `scripts/kitap/fiz345_ithal.py`, migration `0033`.
Gorsel uretimi: `scripts/kitap/fiz345_kirp.py`.

Her asama bir oncekini SINAR; her iddia ayni kapsamda olculmustur.
Faz 0 kesif fisi: `FIZ_345_AYT_KESIF.md`.

## 0. Kaynak ve TAVANI

Kaynak, kitabi gosteren bir okuyucu uygulamasinin ekran goruntuleridir:
392 sayfa, her biri 1920x1080 PNG. PDF'te METIN KATMANI YOK. PNG sayisi
= PDF sayfa sayisi = 392.

Sayfa karti BU KITAP ICIN olculdu (12 ornek sayfada kartin ince cerceve
cizgisi sutun/satir profiliyle bulundu; 12'sinde de ayni):

    x 584-1331, y 42-1021  ->  kirpim (584, 42, 1332, 1022) = 748 x 980

Kardes kitap `Mikro Orijinal TYT Fizik` 728x968 idi. Onun degeri
varsayilsaydi HER kirpim kayardi; "her kitap icin olc" kurali burada
karsiligini verdi.

Basili sayfa numarasi dosya numarasiyla BIREBIR ayni; veri setinde
`sayfa == basili_sayfa` 1308 satirin 1308'inde dogru.

## 1. Sayfa yapisi

Kitabin KENDI icindekiler sayfalari (f3, f4) 20 bolumu ve basili
baslangic sayfalarini veriyor. Kitap KONU ANLATIMLIDIR: bazi sayfalarin
bir sutunu konu anlatimi ya da cozumlu ornektir, soru degildir.

| kalem | deger | kanal |
|---|---|---|
| toplam sayfa | 392 | dosya sayimi |
| soru tasiyan sayfa | 380 | cevap satiri + transkripsiyon |
| soru | 1308 | cevap satiri (x2) + transkripsiyon |
| test | 190 | cevap satiri numaralandirmasi |
| bolum | 20 | icindekiler |
| konu dugumu | 40 | test baslik bandi |

## 2. Cevap kaynagi -- SAYFA ALTI SATIR, CIFT OKUMA

Bu kitapta anahtar kitabin sonunda ya da test sonunda DEGIL, **her soru
sayfasinin altinda, sutun basina ayri** basili (ornek s87: solda
`5.C 6.D`, sagda `7.D 8.E`). Kart koordinatinda y 892-897, kucuk gri
punto. Sorular HICBIR asamada cozulmedi.

### 2a. Satirin yeri once PIKSEL olarak bulundu

Kart ic koordinatinda alt 200 satirin murekkep profili cikarildi; her
soru sayfasinda 6 piksel yuksekliginde, x 67-673 araliginda ayni bantta
duran bir metin satiri bulundu (y 892-897). Bu bant transkripsiyondan
ONCE belirlendi.

### 2b. Iki bagimsiz okuma

| | okuma A | okuma B |
|---|---|---|
| olcek | 5x | 7x |
| montaj | 12'serli | 9'arli |
| sira | sayfa sirasinda | TERS sirada |
| okuyucu sayisi | 8 ayri alt ajan | 8 ayri alt ajan |
| okuyucuya girdi sayisi soylendi mi | hayir | hayir |
| cikan sayfa | 382 | 382 |
| cikan girdi | 1308 | 1308 |

Harf duzeyinde uyusmazlik: **5 sutun** (s10/s18/s20/s24 sol, s374 sag) --
besi de bu fonttaki B/E benzerligi. Besi de 12x buyutmede GOZLE karara
baglandi: B'nin alt kasesi kapali, E'nin uc yatay cubugu acik. Besinde
de okuma A dogru cikti; hangi satirin hakemlendigi veri setinde degil,
bu belgede ve `cevaplar.json`da izlenir.

### 2c. Yapisal kapilar

| kapi | sonuc |
|---|---|
| sayfa ici numara surekliligi (sol bitince sag devam) | 382 sayfada 0 kusur |
| sayfalar arasi gecis: "devam" ya da "yeni test 1'den" | 379 gecisin hepsi; ucuncu durum YOK |
| test basina numaralar 1..N kesintisiz | 190/190 |
| her test tam 2 sayfa | 190/190 |
| benzersiz `soru_hash` | 1308/1308 |

Test buyuklugu dagilimi: 8 soruluk 81 test, 6 soruluk 65, 7 soruluk 24,
5 soruluk 10, 4 soruluk 4, 3 soruluk 3, 9 soruluk 3.

## 3. Transkripsiyon ve UCUNCU KANAL

380 sayfa 12'serli 32 gruba bolundu; her grubu AYRI bir alt ajan 2x
buyutulmus kart kirpimindan transkribe etti. Ajanlara sayfada kac soru
oldugu SOYLENMEDI ve sayfa altindaki cevap satirini yok saymalari
istendi.

Transkripsiyon 1308 soru kaydi uretti. Sayfa/sutun bazinda cikardigi
soru NUMARALARI, cevap satiri okumasiyla karsilastirildi:

    686 sayfa/sutun kumesi -- FARK 0

Yani soru sayisi ve numaralandirma UC BAGIMSIZ kanaldan ayni cikti:
cevap satiri okumasi A, okuma B, ve 32 ayri ajanin soru transkripsiyonu.

### 3a. Normalizasyon (durustluk notu)

Ilk gruplarda talimat yeterince dar degildi ve `kaynak_kusuru` alani
dizgi kusuru olmayan bicim notlariyla da dolduruldu (sik tablosunun iki
sutunlu olmasi, virgulden onceki bosluk, dilbilgisi elestirisi). 46
kayit TEK TEK elden gecirildi: 25'i gercek basim kusuru olarak tutuldu,
21'i dusuruldu. Dusurulenlerin 5'i aslinda "siklar grafik" durumuydu ve
`sikler_gorsel` bayragina cevrildi.

## 4. Okuyucu simgesi ortmesi

Kart icinde glif rengine (69,39,160) yakin ve etrafinda lila disk
(240,238,247) bulunan bloklar sayildi; sayfa ustu susleme (y < 120) ve
olcu disi bloklar elendi. Transkripsiyon sirasinda metni gercekten
okunamaz kilan **16 satir** bulundu; ortulen parca `ortulen_metin`
alaninda `...[??]` ile saklanir, TAHMIN EDILMEDI.

Bu kitabin 2024 baskisi bir KURTARMA KANALI sunar (simgeler iki
yakalamada ayni yerde degil; bkz. bolum 7), ama bu ithalde
KULLANILMADI -- borc listesinde.

## 5. Gorseller -- TAM SORU KIRPIMI

Sorularin **1007'si (%77)** sekil/grafik/devre semasi iceriyor ve sekil
olmadan soru eksik kalir. `question_image_url` TAM SORU KIRPIMIDIR.

### 5a. Kutular LLM'e tahmin ETTIRILMEDI

Kutu, okuyucu simgesinin konumundan turetildi:
`[simge ust - 6, sonraki simge ust - 9]`; son sorunun alti cevap
satirinin ustunde sabitlendi. Sutun siniri sayfa basina sag sutun
simgesinin x konumundan hesaplandi.

Bir sutunda simge sayisi o sutunun cevap satiri girdi sayisina ESIT
DEGILSE o sutunun sorulari kirpimsiz birakildi (tahmin edilmedi):
**1295 kutu uretildi, 13 soruda uretilemedi (7 sutun)**. Gerekce her
satirda `kirpim_gerekcesi`'nde yazili.

Simge dedektoru iki kez duzeltildi ve ikisi de OLCUMLE yakalandi
(kapi: "sutundaki simge sayisi == o sutunun cevap satiri girdi sayisi"):

| dedektor | uyumlu sutun / 686 | kutusuz soru |
|---|---|---|
| sutun siniri 360 (sag sutun simgeleri x~359'da, yarisi sol sutuna dusuyordu) | 256 | 825 |
| sinir 300 | 606 | 159 |
| sinir 300 + sayfa ustu susleme (y<120) ve olcu disi bloklar elendi | **679** | **13** |

Ucuncu satirdaki 7 uyumsuz sutun veri setinde `kirpim_gerekcesi` ile
duruyor; o sutunlarin sorularina kutu URETILMEDI.

### 5b. Cevap sizintisi kapisi

Cevap satiri kart y 892'de basliyor. Uretilen 1295 kutunun y-alt siniri
**hicbirinde 888'i gecmiyor** (test: `test_kirpim_cevap_satirini_icermiyor`).
Yani ogrenciye gosterilecek gorselde cevap YOK.

### 5c. Kutu kenarlari metni kesiyor mu?

Bilesen tabanli olcum (sayfa murekkep maskesi 8-komsuluk etiketlenir;
glif boyutlu bir bilesen hem kutunun icinde hem disinda piksel
tasiyorsa "kesik" sayilir): 1295 kirpimda toplam 195 kesik bilesen,
bunlarin 160'i 20 pikselden kucuk. 30 px ve uzeri tasan 33 soru var ve
bunlarin cogu ayni desende (sag sutun 2. sorusunda sol kenar + alt).

Ornekleme ile gozle bakildi (s154 sag 2, s241 sag 8, s87 sol 5): kesilen
sey soru METNI degil, sayfanin sutun ayirici INCE MAVI CIZGISI. Orneklem
3; 33'un tamami tek tek dogrulanmadi -- borc listesinde.

## 6. Siklari GRAFIK olan 19 soru

19 soruda A-E siklari grafik/diyagramdir, metin olarak basili degildir.
Bu satirlarda sik alanlarina `(gorsel sik)` yazildi ve `sikler_gorsel`
bayragi kondu; siklar UYDURULMADI. 19'un 18'inde kirpim var, yani soru
gorselle birlikte gosterilebilir.

Kalan **1 satirda (s27 sag 5)** ne sik metni ne de kirpim var: bu satir
ogrenciye hicbir bicimde gosterilemez. SILINMEDI;
`gosterilemez_gorsel_sik_kirpimsiz` bayragiyla isaretlendi. Bu bir
ithal DURDURMA gerekcesi degil, cunku ithal zaten PASIF ve
aktiflestirme ayri bir karar.

## 7. Baski ikilemi: 2024 mu 2025 mi?

`screenshots` altinda ayni kitabin iki klasoru var: `345 2024 Ayt Fizik`
ve `345 2025 Ayt Fizik`, ikisi de 392 sayfa. 392 sayfanin TAMAMI kart
bolgesinde piksel piksel karsilastirildi:

| olcum | sonuc |
|---|---|
| farkli piksel orani medyani | %0,28 |
| oran > %1 olan sayfa | 25 |
| oran > %5 | 6 |
| en yuksek | %77 (f1 kapak) |

Medyandaki %0,28 fark okuyucu SIMGELERININ kaymasindan geliyor (fark
bloklari iki sutunun simge kolonlarinda). Ama farkli cikan sayfalar
GERCEKTEN farkli icerik: f241 gozle karsilastirildi -- 5. ve 7. soru
ayni, 6. soru komple degismis (2024: CIKMIS SORU AYT-2022; 2025: CIKMIS
SORU AYT-2025) ve alt cevap satiri da buna gore farkli. f87'de 2025
baskisi 2024'te HIC OLMAYAN bir 8. soru eklemis.

**Karar: 2025 baskisi islendi; 2024 ISLENMEDI.** 2024 baskisi ortme
kurtarma kanali olarak kullanilabilir (simgeler ayni yerde degil) ve
2024'te olup 2025'te olmayan sorular olabilir -- ikisi de borc.

## 8. Mukerrer adaylari ISARETLENDI, SILINMEDI

DB'deki 3456 FIZIK satirina karsi kelime kumesi ortusmesi >= 0.75 olan
**11 soru** bulundu: 9'u `OSYM 2025 AYT`, 2'si `Neofizik AYT Fizik Soru
Bankasi 2025`. Kitap zaten CIKMIS SORU kutulari basiyor, yani OSYM
ortusmesi beklenen bir bulgudur.

11 adayin **10'unda** DB'deki cevap bizim okumamizla AYNI. Tek catisma
(s49 soru 3, ortusme 0.765) gozle incelendi: iki soru da "konum-zaman
grafigine gore hiz-zaman grafigi" kalibinda, govdeler farkli ve iki
tarafta da siklar grafik. Ayni soru DEGIL, ayni kalip. Catisma
gizlenmedi, veri setinde `cevap_ayni: false` olarak duruyor.

Hash duzeyinde (NFC metin + siklar) DB genelinde ikinci kopya **0**.

## 9. Konu agaci (0033)

`0033_fiz345_agac`, FIZ kokunun altina `FIZ-345` onekiyle AYRI bir alt
agac kurar: **20 bolum + 40 konu**.

* Bolum adlari ve sayfa araliklari: kitabin KENDI icindekiler
  sayfalarindan (f3, f4).
* Konu adlari: her testin sayfa ustundeki BASLIK BANDINDAN; 190 testin
  190'inin bandi okundu.
* Bandin adi bolum adiyla ayniysa ya da birden cok bolumu kapsiyorsa
  (ornek "BIR ve IKI BOYUTTA HAREKET", "TORK, DENGE, KUTLE ve AGIRLIK
  MERKEZI") soru BOLUM dugumune baglanir: 1037 satir bolum, 271 satir
  konu duzeyinde.
* Agacta soru tasimayan dugum YOK: 60/60 kullanildi.

**Bagimsiz dogrulama**: testlerin sayfa sinirlari cevap satirindaki
numaralandirmadan turetildi; icindekilerden gelen bolum araliklariyla
karsilastirildiginda 190 testin 190'i tek bir bolumun icinde kaldi,
bolum sinirini asan test YOK.

Test turu bantta yazili: kazanim 422, osym_tadinda 625, gunluk_hayat
186, orijinal 75 soru.

### 9a. Yanlis alarm (kayda gecirildi)

f358'in baslik bandi "URETECE BAGLI DEVRELER" diyor ama sayfa MODERN
FIZIK bolumunde. Once kitabin dizgi kusuru sanildi; sayfadaki alti soru
okundu ve hepsinin FOTOSEL devreleri (kesme gerilimi, akim-gerilim
grafigi) hakkinda oldugu goruldu. Bant DOGRU; kusur olarak
isaretlenmedi.

## 10. Alanlar ve kaynaklari

| alan | kaynak |
|---|---|
| `question_text`, `a..e` | sayfa granulerliginde gorsel okuma (tek gecis, 32 ajan) |
| `correct_answer` | sayfa alti cevap satiri, iki bagimsiz okuma, 5 sutun gozle hakemlendi |
| `explanation` | NULL -- kitabin soru sayfalarinda cozum YOK, uydurulmadi |
| `question_image_url`, `image_width/height` | simge tabanli tam soru kirpimi |
| `source_page` | dosya numarasi (= basili numara) |
| `osym_year` | NULL -- kitap yil basiyor ama sistematik cikarilmadi |
| `osym_format_compliant` | FALSE -- iddia edilmedi |
| `bloom_level` | `metin_olcum.bloom_belirle` heuristigi |
| `readability_score` | Atesman Turkce okunabilirlik |
| `morphology_complexity` | heuristik (Zemberek YOK) |

Ithal PASIF: `is_active=FALSE, is_public=FALSE, is_ai_generated=TRUE,
review_status='PENDING'`.

## 11. Ithal sonrasi olcum (18 Eyl 2026)

`python backend/scripts/kitap/fiz345_ithal.py --yaz` ciktisi:
`YAZILDI: 1308 yeni satir`, `is_active 0`, `kapidan gecen 0`.

DB'den bagimsiz olcum:

| olcum | sonuc |
|---|---|
| question_bank / content / statistics satiri | 1308 / 1308 / 1308 |
| is_active TRUE | 0 |
| is_public TRUE | 0 |
| review_status <> PENDING | 0 |
| `v_safe_for_beta` kapisindan gecen | 0 |
| explanation NOT NULL | 0 |
| question_image_url dolu | 1295 |
| image_width + image_height dolu | 1295 |
| FIZ-345 agacina bagli satir | 1308 |
| kullanilan farkli konu dugumu | 60 |
| exam_type/subject_area AYT-FIZIK disinda | 0 |
| `ithal_araci` damgasi tasiyan | 1308 |
| `mukerrer_aday` bayrakli | 11 |
| `okuyucu_simgesi_ortmesi` bayrakli | 16 |
| `osym_year` dolu | 0 |
| DB genelinde bu hash'lerin ikinci kopyasi | 0 |
| `topic_hierarchy` FIZ-345 dugumu | 60 |
| 0033 gunlugundeki dugum | 60 |
| AYT FIZIK toplam (tum kitaplar) | 2540 |

Gorseller: `d-dataset/output/crops/FIZ345_AYT/` altinda 1295 PNG
uretildi, 13 soru kutusuz atlandi (script ciktisi ile birebir).

## 12. Bilinen borc

1. **13 soruda kirpim kutusu uretilemedi**; 11'i sekilli
   (`gorsel_yok_sekilli`).
2. **1 satir (s27 sag 5) hicbir bicimde gosterilemez**: siklari grafik
   ve kirpimi yok.
3. **16 satirda okuyucu simgesi metni ortuyor**. Bu kitapta 2024
   baskisi kurtarma kanali sunuyor ama BU ITHALDE KULLANILMADI.
4. **TAM ikinci transkripsiyon yapilmadi** (cevap satiri icin yapildi).
   Metin hata orani bu kitap icin OLCULMEDI.
5. **25 satirda kitabin KENDI basim kusuru** isaretli; duzeltilmedi.
6. **11 mukerrer aday**; birlestirme/eleme karari verilmedi.
7. Kutu kenari olcumunde 33 kirpimda 30 px+ kesik bilesen goruldu;
   ornekleme (3 vaka) hepsinde kesilenin sutun ayirici cizgi oldugunu
   gosterdi, ama 33'un tamami dogrulanmadi.
8. **2024 baskisinda olup 2025'te olmayan sorular** olabilir (f241
   ornegi); taranmadi.
9. Kitap CIKMIS SORU kutularinda sinav yilini basiyor; `osym_year`
   sistematik cikarilmadi.
