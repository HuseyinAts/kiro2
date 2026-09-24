# 345 2025 TYT Matematik Soru Bankasi -- uretim yontemi ve olcumler

Kaynak: `veriseti/zkitap/screenshots/345 2025 Tyt Matematik Soru Bankasi/`
(416 PNG + PDF; ikisi de git disinda). Veri dosyalari
`veriseti/zkitap/cikti/345_2025_tyt_matematik_*.json`.

| arac | is |
|---|---|
| `scripts/kitap/mat345tyt_tarama.py` | capa taramasi (simge, basili numara, ara cizgi) |
| `scripts/kitap/mat345tyt_kutu.py` | kirpim kutulari |
| `scripts/kitap/mat345tyt_kirp.py` | soru gorselleri + ortme / kenar olcumu |
| `scripts/kitap/mat345tyt_metin_harness.py` | transkripsiyon gruplari + kapilar |
| `scripts/kitap/mat345tyt_ithal.py` | PASIF ithal |
| `alembic 0042_mat345tyt_agac` | konu agaci (MAT-345T25) |
| `alembic 0043_mat345tyt_kaynak_adi` | eski hat source_book yazim duzeltmesi |

Her asama bir oncekini SINAR; her iddia ayni kapsamda olculmustur. Hicbir
soru cozulmedi; hicbir cevap uretilmedi.

## 0. Kaynak ve tavani

FERNUS okuyucusunun 1920x1080 ekran goruntuleri. Sayfa karti bu kitap icin
olculdu: `(589, 43) - (1331, 1020)` = 742x977. Basili sayfa numarasi dosya
numarasiyla ayni (sayfa altindaki basili numara ile olculdu; `source_page`
= dosya no).

| kalem | deger | kanal |
|---|---|---|
| toplam sayfa | 416 | dosya sayimi |
| on sayfalar | 1-4 (kapak, kunye, icindekiler 3-4) | goz |
| bolum ayraci | 13 (5, 57, 85, 111, 127, 169, 203, 265, 295, 327, 353, 381, 401) | sag kenar doygunlugu + goz |
| soru sayfasi | 399 | cevap satiri |
| test | 202 | cevap satiri numaralandirmasi |
| soru | 2063 | cevap satiri (x2) + transkripsiyon |

## 1. Cevap anahtari -- sayfa alti satir, iki okuma + piksel kanali

Anahtar her soru sayfasinin altinda, sutun basina ayri basili satir (kart
y 892-904). `345_2025_tyt_matematik_cevap_anahtari.json`; ham okumalar
(A, B ve test baslik bandi okumasi) `345_2025_tyt_matematik_ham_okumalar.json`
-- testler anahtari ve konu haritasini bu ham dosyadan yeniden turetir.

| | okuma A | okuma B |
|---|---|---|
| olcek | 5x | 7x |
| montaj | 12 satir | 9 satir |
| sira | sayfa sirasinda | TERS |
| girdi sayisi okuyucuya soylendi mi | hayir | hayir |

* A == B: **2063/2063** girdi, harf ve numara duzeyinde fark 0.
* Ucuncu kanal (piksel): harf glifinin 8x9 penceresi, en-yakin-komsu,
  birini-disarida-birak. 1817 glif segmente edildi, LOO uyumu 1801/1817.
  Uyumsuz ya da dusuk marjli **17** girdinin hepsi 6x en-yakin-komsu
  kontrast buyutmesiyle gozle incelendi: 17'sinde de A/B okumasi dogru.
* Segmentasyonun kapsamadigi **63 yarim satir** (241 girdi) ayrica gozle
  tarandi; okumayla celiski yok.
* Okuyuculardan birinin '?' ile tereddut isaretledigi **44 girdi** tek tek
  gozle incelendi (cogu B/E); 44'unde de okunan harf dogru.
* Numara kitap boyunca ya oncekinin +1'i ya da 1: 202 test, baska kopma yok.
* Testlerin 185'i 2, 11'i 1, 6'si 3 sayfa; sayfalar hep ardisik; iki testi
  birden tasiyan sayfa yok.

Kaynak dagilimi (veri setinde `cevap_okuma_kanali`): `iki_okuma+piksel`
1762, `iki_okuma+goz(piksel_kapsam_disi)` 241, `iki_okuma(biri_tereddutlu)+goz`
44, `iki_okuma+piksel_supheli+goz` 16.

## 2. Konu agaci -- kitabin kendi icindekiler sayfasi (0042)

Icindekiler (dosya 3-4): 13 bolum, 30 konu ve her konunun basili baslangic
sayfasi. Bolum ayraci sayfalari yalniz 'BOLUM NN' ve konu listesini basiyor;
bolumlerin ayri bir adi YOK -- dugum adi 'Bolum NN' (uydurulmadi).

Bagimsiz ikinci kanal: her testin ilk sayfasindaki baslik bandi (202 bant,
goz ile okundu, `konu_haritasi.json` > `testler`):

* test turu: Klasiklesmis Sorular 95 test / 1337 soru, OSYM Tadinda Sorular
  90 / 653, Orijinal Sorular 17 / 73;
* 202 testin 202'si tek bir icindekiler araligina dusuyor;
* bantta konu adi basili 184 testin 184'unde bant adi == aralik konusu
  (bosluklar yok sayilarak; iki acik esleme: bant 'FAKTORIYEL' =
  'Faktoriyel Kavrami', bant 'SAYISAL VE SOZEL MANTIK' = 'Sayisal - Sozel
  Mantik'). Orijinal Sorular bantlari ve bir OSYM bandi konu adi basmiyor (18);
* Klasiklesmis ve OSYM Tadinda sira numaralari her konuda 1'den kesintisiz.

Sorular KONU dugumune baglanir (30 dugumun 30'u soru tasiyor); bolum
dugumleri yalniz gruplama.

## 3. Kirpim kutulari -- iki capa kanali, kitabin anahtari secer

`mat345tyt_tarama.py` iki bagimsiz piksel kanali olcer:

| kanal | yontem | olcum |
|---|---|---|
| okuyucu simgesi | glif halkasi (69,39,160) + lila disk penceresi | 2213 simge |
| basili numara | camgobegi (0,160,224), numara seridi | 2076 numara |

Bir sutunun capasi, sayisi o sutunun cevap satiri girdi sayisina ESIT olan
kanaldir (once numara). 798 sutunun 782'sinde iki kanal da, 14'unde yalniz
numara, 2'sinde yalniz simge tutuyor; ikisinin de tutmadigi sutun **0**.
Kullanilan: numara 796 sutun, simge 2 sutun.

Simge dedektoru bir kez duzeltildi ve olcumle yakalandi: ilk surum disk+glif
birlesik bilesenini boyutla suzuyordu; 'UcDortBes' filigrani disk rengine
yakin oldugu icin filigranla ortusen simgeler kaciyordu (s15 sag 8).
Kapi uyumu 769 -> 784 / 798.

Kutu kurallari ve DUZELTMELER (hepsi transkripsiyon ya da olcum yakaladi):

| surum | kusur | nasil yakalandi | duzeltme |
|---|---|---|---|
| v1 | OSYM Tadinda sayfalarinin acik mavi dikey cercevesi kirpim kenarinda (324 kenar ihlali) | kenar kapisi | cerceve beyazlatma (`cerceve_maskesi`) |
| v1 | OSYM sayfalarinda ust bant kutuya giriyor (T005_01) | goz | `bant_tavani` |
| v2 | Orijinal Sorular bandinin alt parcasi 7 kirpimda | okuyucu kaynak_kusuru | bant tavani + Orijinal zemini; bant aramasi numara seridinden saga |
| v2 | onceki sorunun secenekleri sonraki kutuda (s210, s288) | okuyucu kaynak_kusuru | 'OSYM KOSESI' logosu kurali |
| v2 | bir sorunun govdesi sonraki kutuda (s359, s403: T175_13/14, T196_11/12) | okuyucu kaynak_kusuru | bant capadan > 70 px uzaksa 25 px'lik kisa bant aramasi |
| v2 | cercevenin kisa cikintilari 87 kirpimin sol kenarinda 4 px | kenar kapisi | cerceve varsa banttaki tum cerceve pikselleri |

Kenar kapisinda kalan TEK kutu: T193_01 (s396 sol), cercevenin 6 piksellik
cikintisi, rengi esigin 1 birim disinda (L1 46 > 45); gozle bakildi, metin
degil.

Son durum: 2063 kutu, kutusuz soru 0; kutu alti hic bir kutuda cevap
satirina (y 889) ulasmiyor (<= 886). Ust kesimi +-3 satirda notr koyu metne
degen 3 kutu (T102_06, T141_06, T196_12) gozle incelendi: uc kesim de metnin
disinda (onceki secenek satirinin alt kenari ya da ust simge 1-2 px).
Etkilenen 18 soru yeni kirpimdan AYRI bir okuyucuyla yeniden okundu
(`duzeltme`).

## 4. Transkripsiyon

2063 kirpim 2x Lanczos, test sinirina hizali 33 grup; her grubu ayri okuyucu
okudu. Okuyuculara anahtar ve sorudaki numara SOYLENMEDI; matematik yazimi
sozlesmesi (kesir a/b, us ^, kok √(...), eksi U+2212) talimatta sabit.
Kapilar (`mat345tyt_metin_harness.py kapi`) ilk birlesimde YESIL:

| kapi | sonuc |
|---|---|
| her kirpim tam bir kez | 2063/2063 |
| basili numara == test ici sira | 2062/2063; tek istisna T192_07 (numara okuyucu diski altinda, capasi simgeden) |
| bes sik dolu | 2063/2063 |

Olculen capalar: sekilli 695, siklari gorsel 22, 'CIKMIS SORU' etiketli 149
(TYT 81, MSU 61, AYT 7; yil 2018-2025), kaynak kusuru notu 101. Rastgele 5
soruluk orneklem gozle kirpimla karsilastirildi: 5/5 birebir. TAM ikinci
transkripsiyon YAPILMADI (borc).

## 5. Ortme

Okuyucu diski beyazlatildi; diskin kenar halkasinda kitap murekkebi olculen
**167 soru** `okuyucu_diski_ortme` bayragi tasir (disk opak, alti goruntude
YOK; tahmin edilmedi). 2024 baskisi (`345 2024 Tyt Matematik`) kurtarma
kanali olabilir -- bu ithalde KULLANILMADI (borc).

## 6. Mukerrer adaylari -- isaretlendi, silinmedi

DB'deki 12230 MATEMATIK+GEOMETRI satirina karsi govde kelime kumesi Jaccard
>= 0.75: 62 aday. Matematikte govde kalip cumledir ('islemin sonucu
kactir?'); bu yuzden GUCLU aday = ayrica bes sikkin >= 3'u birebir: **27**.
27'nin 23'unde DB cevabi bizim okumamizla ayni. 4 catismanin (T055_09,
T055_13, T084_01 -- '345 2024 Tyt Matematik' eski hat; T169_02 -- bu kitabin
eski hat satiri) hepsinde kitabin kendi cevap satiri 6x buyutmede gozle
yeniden okundu: bizim okumamiz dogru. Eski hat satirlarina DOKUNULMADI.

Hash duzeyinde (metin + sikler) bu kitabin 2063 sorusu birbirinden farkli;
sekil ikizi yok.

## 7. Eski hat satirlari ve kaynak adi (0043)

DB'de bu kitaptan eski hattan gelen 12 satir var (`345 2025 Tyt Matematik
Soru Bankas<U+0131>`, 12'si aktif). Yazim yeni ASCII adla ayni anahtara
cozuluyor; 0043 yalniz `source_book` yazimini duzeltir (metin, cevap,
aktiflik degismez; geri alinabilir). Bu 12 satirdan biri (T169_02 karsiligi)
kitabin anahtariyla CELISIYOR ve AKTIF -- karar sahipte.

## 8. Alanlar ve kaynaklari

| alan | kaynak |
|---|---|
| `question_text`, `a..e` | kirpimdan gorsel okuma (33 grup + 18 duzeltme) |
| `correct_answer` | sayfa alti cevap satiri, iki okuma + piksel + goz |
| `explanation` | NULL -- kitapta cozum yok, uydurulmadi |
| `question_image_url` | tam soru kirpimi `/static/crops/MAT345_TYT/` |
| `source_page` | dosya no (= basili no) |
| `osym_year`, `osym_format_compliant` | yalniz 'CIKMIS SORU' etiketli 149 soruda |
| `bloom_level` | `metin_olcum.bloom_belirle` heuristigi |

Ithal PASIF: `is_active=FALSE, is_public=FALSE, is_ai_generated=TRUE,
review_status='PENDING'`.

## 9. Bilinen borc

1. TAM ikinci transkripsiyon yapilmadi (orneklem 5/5).
2. 167 soruda okuyucu diski ortme suphesi; 2024 baskisi kurtarma kanali
   kullanilmadi.
3. 101 soruda okuyucu kaynak kusuru notu (soluk isaret, belirsiz rakam,
   metin ici ikon); duzeltilmedi, bayrakli.
4. 27 guclu mukerrer aday; birlestirme/eleme karari verilmedi. Bir eski hat
   satiri (aktif) kitabin anahtariyla celisiyor.
5. 22 soruda siklar gorsel; soru gorselle birlikte gosterilmeli.
