# Mikro Orijinal TYT Fizik Soru Bankasi 2025 -- uretim yontemi ve olcumler

Veri: `mikro_fizik_tyt_sorular.json` (1326 soru).
Konu agaci: `mikro_fizik_tyt_konu_agaci.json` (60 dugum).
Kaynak: `veriseti/zkitap/screenshots/Mikro Orijinal Tyt Fizik Soru Bankasi 2025/`
(400 PNG + PDF; ikisi de git disinda).
Ithal: `scripts/kitap/mikro_fizik_ithal.py`, migration `0032`.
Gorsel uretimi: `scripts/kitap/mikro_fizik_kirp.py`.

Her asama bir oncekini SINAR; her iddia ayni kapsamda olculmustur.
Faz 0 kesif fisi: `FIZ_MIKRO_TYT_KESIF.md`.

## 0. Kaynak ve TAVANI

Kaynak, kitabi gosteren bir okuyucu uygulamasinin ekran goruntuleridir:
400 sayfa, her biri 1920x1080 PNG. PDF'te METIN KATMANI YOK -- olculdu
(orneklenen sayfalar tek bir gomulu 1920x1080 gorsel tasiyor). Daha
yuksek cozunurlukte bir kaynak YOKTUR.

Sayfa karti goruntunun icinde sabit bir dikdortgen kapliyor -- BU KITAP
ICIN olculdu (12 ornek sayfanin murekkep birlesimi, uygulama kromu
maskelenerek):

    x 596-1323, y 51-1008  ->  kirpim (596, 46, 1324, 1014) = 728 x 968 px

Okuma 2x buyutulmus kirpimla yapildi. PNG sayisi (400) = PDF sayfa sayisi
(400); uyusmazlik yok.

## 1. Sayfa yapisi

Kitabin KENDI icindekiler sayfasi (f4) tam yapiyi veriyor: 11 bolum, her
bolumde Kazanim Testleri + OSYM Tarzi + OSYM Tarzi Orijinal testleri ve
her testin sayfa araligi. Her test TAM 2 sayfa.

| kalem | deger | kanal |
|---|---|---|
| toplam sayfa | 400 | dosya sayimi |
| soru sayfasi | 372 | icindekiler sayfa araliklari |
| test | 186 | icindekiler (sayfa araligi / 2) |
| bolum | 11 | icindekiler |
| soru sayfasi disi | 28 | kapak/kunye/sunu, icindekiler, 11 bolum ayraci, iki cevap kagidi izgarasi (f399-400), bos sayfalar |

Basili sayfa numarasi dosya numarasiyla BIREBIR ayni; veri setinde
`sayfa` ve `basili_sayfa` 1326 satirin 1326'sinda esit (test kapisi:
`test_dosya_sayfasi_basili_sayfayla_ayni`).

KITABIN KENDI DIZGI KUSURU: icindekilerde bolum 07 ORIJINAL satiri
"30 - 33 - 34 - 35 - 36" (bes numara) diyor ama sayfa araligi 235-242 =
8 sayfa = 4 test. "30" yanlis basilmis; isaretlendi.

## 2. Cevap anahtari -- SAYFA ALTI SERIT, CIFT OKUMA

Bu kitapta anahtar kitabin sonunda degil, HER TESTIN IKINCI (son)
sayfasinin altinda duz basili; serit o testin tum cevaplarini tasir
(ornek: `1.E 2.C 3.E 4.E 5.B 6.D 7.D 8.C`). Sorular HICBIR asamada
cozulmedi.

### 2a. Seritler once PIKSEL olarak bulundu (metin okunmadan)

Serit kutusunun alt cercevesi kart y=896'da, x 50-730 araliginda
kesintisiz koyu kosu olarak olculur. Ust cercevesi y=883'te acik gri
(170,170,170) bir cizgi; cevap metni ikisinin arasinda (y 886-893).

| olcum | sonuc |
|---|---|
| serit bulunan sayfa | 186 |
| icindekilerden turetilen test sayisi | 186 |
| beklenen serit sayfasinda serit BULUNMAYAN | 0 |
| beklenmeyen sayfada serit BULUNAN | 0 |
| seritlerdeki magenta numara kumesi (girdi sayisi) | 1326 |

Yani beklenen soru sayisi (1326) anahtardan degil, anahtarin PIKSEL
yapisindan gelir; transkripsiyon bu sayiyi TUTMAK zorundaydi.

### 2b. TESSERACT DENENDI VE ELENDI

Serit metni 1x olcekte ~8 px yuksek ve numaralar magenta. Tesseract
(psm 7 + whitelist) dort ornek seritte de bozuk okudu. Reddedildi ve
kayda gecirildi; yerine LLM montaj okumasi kullanildi.

### 2c. Iki bagimsiz okuma, FARK 0

| | okuma A | okuma B |
|---|---|---|
| olcek | 4x | 5x |
| montaj | 8'erli | 6'sarli |
| sira | sayfa sirasinda | TERS sirada |
| okuyucuya girdi sayisi soylendi mi | hayir | hayir |
| cikan serit | 186 | 186 |
| cikan cevap | 1326 | 1326 |

Harf duzeyinde FARK 0. Okunan cevap sayisi piksel kanalinin girdi
sayisiyla da birebir ayni. Her serit kirpimi sayfanin BASILI NUMARASINI
da tasidigi icin sayfa numarasi denetimi ayni okumadan bedava geldi.

## 3. Sifir serbestlik dereceli kapilar

| kapi | sonuc |
|---|---|
| her seritte numaralar 1..N kesintisiz | 186 seritte 0 kusur |
| cevap harfleri A-E disinda | 0 |
| okunan soru sayisi == serit girdi sayisi | 186/186 test |
| serit testin IKINCI sayfasinda (`serit_sayfa == test_bas_sayfa + 1`) | 1326/1326 |
| soru sayfasi testin iki sayfasindan biri | 1326/1326 |
| K1-K12 yapisal dogrulayici | 1326 satirda 0 kusur |
| benzersiz `soru_hash` / `id` | 1326 / 1326 |
| NFC disi metin | 0 |

Harf dagilimi: D 294, C 283, E 273, B 268, A 208 (hicbiri %10-%35
bandinin disinda degil).

## 4. Soru sayfalari -- transkripsiyon

Okuma sayfa granulerliginde, 2x buyutulmus kart kirpimiyla yapildi
(gruplar `_grup` alaninda izlenir, 31 grup). Her sayfada sol/sag sutun
ayri okundu; sutun ve soru numarasi kayda gecirildi.

TAM ikinci transkripsiyon YAPILMADI -- bu bilinen borctur (bkz. 9).
Cevap seridi icin iki bagimsiz okuma yapildi, soru METNI icin
yapilmadi.

## 5. Okuyucu simgesi ortmesi -- KURTARMA KANALI YOK

Okuyucu uygulamasi her sorunun soluna bir buyutec simgesi ciziyor.
Soru sayfalarinda toplam 1381 simge blogu olculdu. Duzeltilmis metin
maskesiyle (koyu VE notr: `max(RGB)<150 ve (max-min)<60`) metne temas
eden blok sayisi 121 (%8.8 ust sinir).

Edebiyat kitabindan FARKLI olarak bu kitabin IKINCI BIR YAKALAMASI YOK
(`screenshots` altinda tek klasor). Yani ortulen parca baska bir
kaynaktan kurtarilamaz. Emsal uygulandi: okunabilen kismi yaz, TAHMIN
ETME, `...[??]` isaretini birak, `okuyucu_simgesi_ortmesi` bayragini koy.

Transkripsiyon sirasinda metni gercekten okunamaz kilan 16 satir
bulundu; ortulen parca `ortulen_metin` alaninda saklanir. (121 "temas
eden blok" bir UST SINIRDIR: cogu simge satir arasina ya da bosluga
denk geliyor ve metni okunamaz kilmiyor.)

## 6. Gorseller -- TAM SORU KIRPIMI

Sorularin 1022'si (%77) sekil/grafik/tablo iceriyor ve sekil olmadan
soru eksik kalir. `question_image_url` TAM SORU KIRPIMIDIR (metin +
sekil birlikte).

### 6a. Kutular LLM'e tahmin ETTIRILMEDI

Okuyucu uygulamasinin her sorunun soluna cizdigi simge piksel duzeyinde
bulundu (disk 240,238,247 / glif 69,39,160) ve kutu
`[simge ust - 6, sonraki simge ust - 9]` olarak turetildi. Sutun
sinirlari SAYFA BASINA sag sutun simgesinin x konumundan hesaplandi:
sol = `(6, sinir+2)`, sag = `(sinir-2, 712)`.

Iki hata olculdu ve duzeltildi:

* Turetme once her sutunun ILK simgesini kaciriyordu (`y0 >= 100` esigi,
  simgeler y~94'te): esik 80'e cekildi, 39 kirpim -> 1247 kirpim.
* SABIT sutun siniri (326) hem sol sutun metnini kirpiyor hem sol sutun
  harflerini sag kirpima sizdiriyordu (goz kontrolunde goruldu);
  sayfa basina turetilen sinirla degistirildi ve yeniden goz kontrolu
  yapildi.

Bir sutunda simge sayisi o sutunda okunan soru sayisina ESIT DEGILSE o
sutunun sorulari kirpimsiz birakildi (tahmin edilmedi): 1247 soruda kutu
uretildi, 79'unda uretilemedi (46 sutun yuvasi). Gerekce her satirda
`kirpim_gerekcesi`'nde yazili (ornek: "simge 1 != soru 2"). Bu 79
sorunun 66'si sekilli; onlar `gorsel_yok_sekilli` ile isaretlidir --
aktiflestirmede once bunlar konusulmalidir.

### 6b. Kirpimlar CEVAP SERIDINI icermiyor (sizinti kapisi)

Serit ust cercevesi kart y=883. Serit sayfasindaki 583 kirpimin
y-alt siniri en fazla **872** (328'inde tam 872); 883'u gecen kirpim
**0**. Uretilen 583 PNG'nin alt 20 satirinda serit magentasi arandi:
5 pikselden fazla tasiyan 1 kirpim var, o da 7 px (sekil rengi, rakam
degil). Yani ogrenciye gosterilecek gorselde cevap yok.

### 6c. Kutu kenarlari metni kesiyor mu?

Bilesen tabanli olcum (sayfa murekkep maskesi 8-komsulukla etiketlenir;
glif boyutlu bir bilesen hem kutunun icinde hem disinda piksel
tasiyorsa "kesik" sayilir): 1247 kirpimin 345'inde en az bir kesik
bilesen var, toplam 505 bilesen. Bunlarin 378'i 20 pikselden kucuk
(kil payi temas).

En buyuk dort tasmaya GOZLE bakildi (s26, s32, s60, s82): dordunde de
kesilen sey soru METNI degil, sorunun etrafindaki YUVARLAK KOSELI
CERCEVE. Kutunun 45 px genisletilmis hali ile tight kirpim
karsilastirildi; metin ve siklar tight kirpimda eksiksiz. Yani bu
olcumun sayisi cerceve/susleme kaynaklidir, metin kaybi degil --
ama tamami tek tek dogrulanmadi, orneklem 4.

## 7. Mukerrer adaylari ISARETLENDI, SILINMEDI

DB'deki mevcut FIZIK satirlarina karsi kelime kumesi ortusmesi >= 0.75
olan 34 soru bulundu (30'u `Neofizik TYT Fizik Soru Bankasi`, 4'u
`OSYM 2025 TYT`). Iki ornek gozle karsilastirildi: metin kelimesi
kelimesine ayni; yani bu sorular iki farkli yayinevinin kitabinda ayni
sekilde basili.

SILINMEDI. `pipeline_metadata.mukerrer_aday` alanina hedef satirin
id'si, kitabi, sayfasi, iki taraftaki cevap ve ortusme degeri yazildi;
birlestirme/eleme URUN SAHIBININ karari.

YAN BULGU: 34 adayin 34'unde de DB'deki satirin cevabi bizim serit
okumamizla AYNI cikti. Bagimsiz uretilmis iki kitap (ve 4 soruda
OSYM'nin kendi kitapcigi) anahtari dogruladi.

Not: hash duzeyinde (NFC metin + siklar) DB genelinde ikinci kopya 0 --
ayni soru farkli dizgiyle basildigi icin hash'ler tutmuyor; bu yuzden
kelime kumesi kanali kullanildi.

## 8. Konu agaci (0032)

`0032_mikro_fizik_agac`, FIZ kokunun altina `FIZ-MO` onekiyle AYRI bir
alt agac kurar (BS Turkce'deki `TUR-BS`, Edebiyat'taki `EDB-BS`
deseninin aynisi). Mevcut FIZ agacina sessizce "en yakin dugume"
baglamak yanlis veri olurdu.

* 11 bolum (`FIZ-MO1..FIZ-MO11`) ve sayfa araliklari: kitabin KENDI
  icindekiler sayfasindan.
* 49 konu dugumu: her testin sayfa ustundeki BASLIK BANDINDAN
  (ornek "KAZANIM TESTI (Duzgun Dogrusal Hareket) - 3"); 186 testin
  186'sinin bandi okundu, hicbiri eksik/okunamaz degildi.
* OSYM TARZI / OSYM TARZI ORIJINAL testleri (476 soru) ve baslik bandi
  "KARMA TEST" olan kazanim testleri (46 soru) bir konuyu degil bolumun
  tamamini tarar; onlar BOLUM dugumune baglanir ve
  `konu_bolum_duzeyinde` bayragini alir. Toplam 522 satir.
* Agacta soru tasimayan dugum YOK: 60 dugumun 60'i kullanildi.

Downgrade yalnizca bu kosumda olusturulan dugumleri siler
(`mikro_fizik_konu_gunlugu_0032`) ve soru tasiyan ya da cocugu olan
dugume DOKUNMAZ.

## 9. Alanlar ve kaynaklari

| alan | kaynak |
|---|---|
| `question_text`, `a..e` | sayfa granulerliginde gorsel okuma (tek gecis) |
| `correct_answer` | sayfa alti cevap seridi, iki bagimsiz okuma, fark 0 |
| `explanation` | NULL -- kitabin soru sayfalarinda cozum YOK, uydurulmadi |
| `question_image_url`, `image_width/height` | simge tabanli tam soru kirpimi |
| `source_page` | dosya numarasi (= basili numara) |
| `osym_year` | NULL -- kitap cikmis soru yili basmiyor |
| `osym_format_compliant` | FALSE -- iddia edilmedi |
| `bloom_level` | `metin_olcum.bloom_belirle` heuristigi (kaynagi metadatada) |
| `readability_score` | Atesman Turkce okunabilirlik |
| `morphology_complexity` | heuristik (Zemberek YOK, metadatada yazili) |

Ithal PASIF: `is_active=FALSE, is_public=FALSE, is_ai_generated=TRUE,
review_status='PENDING'`.

## 10. Ithal sonrasi olcum (18 Eyl 2026)

`python backend/scripts/kitap/mikro_fizik_ithal.py --yaz` ciktisi:
`YAZILDI: 1326 yeni satir`, `is_active 0`, `kapidan gecen 0`.

DB'den bagimsiz olcum (`_ithal_sonrasi.py`):

| olcum | sonuc |
|---|---|
| question_bank / content / statistics satiri | 1326 / 1326 / 1326 |
| is_active TRUE | 0 |
| is_public TRUE | 0 |
| review_status <> PENDING | 0 |
| `v_safe_for_beta` kapisindan gecen | 0 |
| explanation NOT NULL | 0 |
| question_image_url dolu | 1247 |
| image_width + image_height dolu | 1247 |
| FIZ-MO agacina bagli satir | 1326 |
| kullanilan farkli konu dugumu | 60 |
| exam_type/subject_area TYT-FIZIK disinda | 0 |
| `ithal_araci` damgasi tasiyan | 1326 |
| `mukerrer_aday` bayrakli | 34 |
| `okuyucu_simgesi_ortmesi` bayrakli | 16 |
| `osym_year` dolu | 0 |
| DB genelinde bu hash'lerin ikinci kopyasi | 0 |
| `topic_hierarchy` FIZ-MO dugumu | 60 |
| 0032 gunlugundeki dugum | 60 |
| TYT FIZIK toplam (tum kitaplar) | 2224 |

Gorseller: `d-dataset/output/crops/MIKRO_FIZIK_TYT/` altinda 1247 PNG
uretildi, 79 soru kutusuz atlandi (script ciktisi ile birebir).

## 11. Bilinen borc

1. **79 soruda kirpim kutusu uretilemedi** (`kirpim_gerekcesi` dolu);
   bunlarin 66'si sekilli (`gorsel_yok_sekilli`). Sekilli olanlar
   sekilsiz gosterilemez -- aktiflestirme karari urun sahibinin.
2. **16 satirda okuyucu simgesi metni ortuyor**; bu kitabin ikinci bir
   yakalamasi yok, kurtarma kanali YOK. Ortulen parca `ortulen_metin`'de.
3. **16 satirda kitabin KENDI dizgi kusuru** isaretli
   (`kaynak_dizgi_kusuru`): bozuk sik harfi, artik metin, alt simge
   hatasi. Duzeltilmedi, kayda gecirildi.
4. **TAM ikinci transkripsiyon yapilmadi** (yalnizca cevap seridi cift
   okundu). Metin hata orani bu kitap icin OLCULMEDI.
5. **34 mukerrer aday** baska yayinevinin kitabiyla ortusuyor;
   birlestirme/eleme karari verilmedi.
6. Kutu kenari olcumunde 345 kirpimda kesik bilesen goruldu; orneklenen
   4 buyuk vakada kesilen sey cerceve cikti, ama 345'in tamami tek tek
   dogrulanmadi.
