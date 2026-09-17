# Bilgi Sarmal TYT Turkce Soru Bankasi -- yontem

Veri seti: `veriseti/zkitap/cikti/bilgi_sarmal_turkce_sorular.json` (1468 soru)
Konu agaci: `veriseti/zkitap/cikti/bilgi_sarmal_turkce_konu_agaci.json` (41 dugum)
Ithal araci: `backend/scripts/kitap/bilgi_sarmal_turkce_ithal.py`
Migration  : 0029 (konu agaci), 0030 (kaynak adi)

## 0. Kaynak ve TAVANI

Kaynak, kitabi gosteren bir okuyucu uygulamasinin ekran goruntuleridir:
336 sayfa, her biri 1920x1080 PNG. PDF'te METIN KATMANI YOK -- olculdu:
her sayfa tek bir gomulu JPEG ve o JPEG de 1920x1080. Yani daha yuksek
cozunurlukte bir kaynak YOKTUR.

Sayfa karti goruntunun icinde sabit bir dikdortgen kapliyor:

    x 592-1328, y 42-1016   ->  736 x 974 piksel

Bu kirpim 2x buyutulerek okundu. Metin bu olcekte okunabiliyor; ancak
nokta/virgul ayrimi ve ince cizgiler tavanda. Bu nedenle okuyuculara
"cozunurluk kaynakli supheyi kitap kusuru diye isaretleme" kurali verildi.

## 1. Sayfa yapisi

| aralik | icerik |
|---|---|
| 1-8 | kapak, icindekiler, on soz |
| 9-331 | soru sayfalari (323 sayfa) |
| 332-336 | CEVAP ANAHTARI (5 sayfa) |

Anahtar bolumu, metni hic okumadan, piksel duzeyinde bulundu: kesintisiz
yatay cetvel (>=120 px koyu kosu) sayimi 332-336'da 29-51, 331 ve
oncesinde 0.

Basili sayfa numarasi dosya numarasiyla BIREBIR ayni (s332 -> sayfa_0332.png,
s10 -> sayfa_0010.png; ikisi de goruntuden dogrulandi).

## 2. Cevap anahtari -- CIFT OKUMA

Anahtar sayfalari iki BAGIMSIZ okumayla cikarildi:

    Okuma A: sayfa sol/sag sutunlara bolunur, 3.0x olcek
    Okuma B: sayfa BOLUNMEZ, tek parca, 2.2x olcek

Iki okuma farkli kirpim geometrisi ve farkli olcek kullanir; ayni goruntuyu
ayni sekilde iki kez okumak degildir. Okuyuculara beklenen test sayisi ya
da soru sayisi SOYLENMEDI (capa etkisi bastirildi).

    114 test blogu -- iki okumada da ayni konumlarda
    1468 cevap     -- hem numara hem harf karsilastirildi -> FARK 0
    Sayfa: degerleri                                      -> FARK 0
    test etiketleri                                       -> FARK 0

Tek fark iki konu adinin buyuk/kucuk harf yazimiydi ("OSYM TIPI" /
"OSYM Tipi") -- veri degil, yazim.

Cevap harf dagilimi: A=289 B=253 C=344 D=299 E=283 (toplam 1468).

**Sorular COZULMEDI.** Tek cevap kaynagi kitabin kendi basili anahtaridir.

## 3. Sifir serbestlik dereceli kapilar

| kapi | sonuc |
|---|---|
| her testte numaralar 1..N kesintisiz | 114 testte 0 kusur |
| anahtardaki `Sayfa:` degerleri kitap boyunca kesintisiz ARTIYOR | 0 kusur |
| 114 testin sayfa araliklari 9-331'i tam kapliyor (bosluk/cakisma yok) | 0 kusur |
| okunan soru sayisi == anahtardaki soru sayisi | 114/114 test |
| bolum numaralari 1..9 kesintisiz ve sirali | 0 kusur |
| K1-K12 yapisal dogrulayici | 1468 soruda 0 kusur |

`Sayfa:` kapisi ozellikle gucludur: tek basina hem okuma sirasini hem 114
sayfa numarasini ayni anda dogrular ve iki okuma bunu bagimsiz uretti.

## 4. Soru sayfalari -- transkripsiyon

323 sayfa, 2x buyutulmus sayfa kirpimi olarak okundu; sayfalar testlerin
sinirlarina gore 29 gruba bolundu ve her grup ayri bir okuyucuya verildi.
Okuyuculara testlerin kac soruluk oldugu SOYLENMEDI.

KURAL: kitap ne yaziyorsa o. Bu bir dil bilgisi/anlam kitabidir; sorular
kasitli yazim yanlisi icerebilir, hicbiri duzeltilmedi.

### Bagimsiz segmentasyon kanali

Kirmizi soru-numarasi imlecleri piksel duzeyinde sayildi (metin hic
okunmadan; ayirac uzerindeki yayinevi logosu x konumuyla elendi):

    1470 imlec  vs  1468 okunan soru
    646 sutun yuvasinin 614'unde sayim AYNI
    32 sapmanin tamami aciklanabilir: 22'si -1 (okuyucu simgesi soru
    numarasini ortmus; okuyucular bunu ayrica rapor etti), gerisi sag
    sutunun soru olmayan icerigi (okuma metni / bilgi kutusu).

### Soru icermeyen sayfalar

Transkripsiyon 12 sayfada soru bulamadi. Bagimsiz piksel kanali (grafik
agirlikli sayfa tespiti) bunlarin 11'ini ONCEDEN isaretlemisti; piksel
kanalinin isaretleyip soru CIKAN sayfa sayisi 0. Tek ek sayfa 96, grafik
agirlikli olmayan bir okuma metni sayfasi.

## 5. OKUYUCU SIMGESI ORTMESI -- bu kitabin en onemli kusuru

Okuyucu uygulamasi her sorunun soluna bir buyutec ve bir soru isareti
simgesi CIZER. SAG sutunun simgeleri tam olarak SOL sutunun satir
sonlarina denk gelir ve oradaki harfleri KAPATIR. Bu kitabin degil,
YAKALAMANIN kusurudur.

Simge renkleri kitabin baskisinda hic gecmez, bu yuzden kesin olarak
tespit edilebilir: disk (240,238,247), glif (69,39,160).

    1536 simge blogu
     619 tanesinin sol kenarina 0-3 px mesafede kitap murekkebi var
     451 SORU (1468'in %30.7'si) etkileniyor -- 442'sinde 1, 8'inde 2,
         1'inde 3 bolge
     112 / 114 test en az bir satirinda etkileniyor

12'lik rastgele orneklem yuksek buyutmede incelendi: 11'inde gercekten
karakter kaybi var (ornekler: "...oldugu gibi anla[tir]", "hangisinde
soru anlami bir adil[la]", "her sey yukaridan daha iyi gorebi[lir]" -- kose
parantezler ORTULEN parcayi gosterir).

Bu satirlarda okuyucu ortulen parcayi BAGLAMDAN TAMAMLADI; metnin o
bolumu OKUNMUS DEGIL, CIKARILMISTIR.

### Kurtarma denendi ve yok

`screenshots/Bilgi Sarmal Tyt Turkce Soru Bankasi 2022 2023` klasoru ayni
kitabin ikinci kopyasidir (336 sayfa). Sayfa karti icindeki piksel farki
OLCULDU: **0**. Fark yalniz tarayici sekme cubugunda (y 4-41). Yani ikinci
kopya ayni yakalamadir, kurtarma saglamaz.

### Nasil isaretlendi

Her etkilenen satirda:

    pipeline_metadata.okuyucu_simgesi_ortmesi = true
    pipeline_metadata.ortulen_bolge           = 1..3
    pipeline_metadata.bayraklar               = [... "okuyucu_simgesi_ortmesi"]

Urun sahibi karari (17 Eyl 2026): **ithal et ama isaretle**. 1468'in
tamami PASIF ithal edildi; aktiflestirme kapisi bu bayragi disarida
birakmalidir.

## 6. Konu agaci (0029)

Kitabin kendi anahtari bolum basligini, konu adini ve sayfayi birlikte
basar; agac oradan kuruldu:

    TUR
     +- TUR-BS1 .. TUR-BS9        9 bolum
         +- TUR-BS<n>-NN          32 konu dugumu

Anahtardaki 63 farkli test adinin bir bolumu bir KONUYU degil bolumun
tamamini tarayan KARMA testtir ("Sarmal Test - N", "OSYM Tipi ...",
"SIMULASYON-N", "... (Karma)", "Tarama Testi"). Bunlara ayri konu dugumu
acmak agaci yalancilastirirdi; bu sorular dogrudan BOLUM dugumune baglanir
ve satirda `konu_eslesme_duzeyi='bolum_karma_test'` yazar.

    konu dugumune baglanan : 956 soru
    bolum dugumune baglanan: 512 soru

## 7. Kaynak adi (0030)

DB'de bu kitaptan eski hattan gelen 13 satir vardi; yazimi iki bosluklu ve
Turkce karakterliydi. Ev sozlesmesi (kaynak_sozlesmesi.py) yeni ithaller
icin yalniz ASCII ve ardisik cift bosluk yasagi getiriyor. 0030 eski yazimi
ASCII'ye cevirir:

    "Bilgi Sarmal  Tyt Turkce Soru Bankasi"  ->  "Bilgi Sarmal Tyt Turkce Soru Bankasi"
                 (iki bosluk, u-umlaut, noktasiz i)

OLCULDU: `normalize_anahtar` ile ayni anahtara cozulen TEK deger eski
yazimdir; bu bir AD DUZELTMESIDIR, birlestirme degil. Ayni yayinevinin
diger Turkce kitaplari yil sonekleri yuzunden farkli anahtara cozuluyor,
onlara dokunulmadi.

## 8. Ucuncu bagimsiz kanal: DB'deki 13 eski satir

Eski satirlarin her biri yeni ithalde en cok ortusen soruyla eslestirildi
(kelime kumesi ortusmesi):

    ortusme >= 0.75 olan 10 eslesmede cevap uyumu: 7 AYNI, 3 FARKLI
    ortusme 0.63-0.71 olan 3 eslesmede: 3'u de FARKLI (eslesme zaten zayif)

7 uyum, basili anahtar okumasinin tamamen bagimsiz bir hattan gelen
teyididir. 3 farkin tarafi belirlenMEDI: eski satirlarin METNI gozle
gorulur bicimde bozuk ("sevdimiyorum", "Calal kazik, yere balmaz",
"toksilin"), yani eslesme dogru soruya olmayabilir. Eski satirlara
DOKUNULMADI.

DIKKAT: bu 13 satirin 12'si `is_active=1` ve 13'u `is_public=1`; yani
bozuk metinli sorular su anda ogrenciye gosteriliyor. Bu bir URUN
KARARIDIR, bu ithalin kapsaminda degildir.

## 9. Alanlar ve kaynaklari

| alan | kaynak |
|---|---|
| question_text, a-e | sayfa goruntusunden okuma (2x kirpim) |
| correct_answer | kitabin kendi cevap anahtari, cift okuma |
| explanation | **NULL** -- kitabin soru sayfalarinda cozum yok, uydurulmadi |
| primary_topic_id | anahtarin bolum/konu basliklari (0029 agaci) |
| source_page | basili sayfa numarasi (= dosya numarasi) |
| word_count, readability, morphology, bloom | `scripts/kitap/metin_olcum.py` |
| is_active / is_public / review_status | FALSE / FALSE / PENDING |

## 10. Ithal sonrasi olcum (17 Eyl 2026)

    veri setinde 1468 soru
    on kontrol: 5 sik + dolu anahtar + dolu metin + TUR-BS konu kodu
                + benzersiz hash -- TEMIZ
    zaten var: 0, yazilacak: 1468
    YAZILDI: 1468 yeni satir
    DB'de bu ithalin satirlari: toplam 1468, is_active 0, kapidan gecen 0

    bayraklar: okuyucu_simgesi_ortmesi 451, konu_bolum_duzeyinde 512,
               kaynak_dizgi_kusuru 126, gorsel_yok_sekilli 14

## 11. Bilinen borc

  * 451 satirda metnin bir bolumu baglamdan tamamlandi (bolum 5).
    Aktiflestirme bu bayragi disarida birakmali.
  * 14 soru sekil/tablo iceriyor ama soru kirpimi URETILMEDI
    (`gorsel_yok_sekilli`); bunlar ogrenciye sekilsiz gosterilirse
    cozulemez.
  * 126 satirda kitabin kendi dizgi kusuru isaretli; metni
    `kaynak_kusuru` alaninda tam olarak duruyor.
  * Eski 13 satirin metni bozuk ve 12'si aktif (bolum 8).
