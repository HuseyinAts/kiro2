# C1CELL 2024 TYT-AYT Geometri Soru Bankasi -- FAZ 0 KESIF FISI

Sahip karari: Wave D (dalga D) kitabi #5. ACIL 2023-2024 Faz 1 bitince
(PR #301-304) sirada bu kitap secildi. Bu fis kitap-basi Faz 0'dir
(K0.1-K0.8).

Salt okunur olcum: DB'ye yazilmadi, transkripsiyon yapilmadi, hicbir soru
cozulmedi. Tarih: 19 Eyl 2026.

Klasor: `veriseti/zkitap/screenshots/C1CELL-2024-TYT-AYT-Geometri Soru
Bankasi` (dosya adinda Turkce karakter var; scriptler glob ile buluyor.)

Yayinevi: **C1CELL Yayinlari** (on sozu Gokhan KECECI imzali). ACIL,
345, Mikro, Bilgi Sarmali'dan farkli yayinevi -- ayni sorunun tekrari
riski dusuk (yine de ithal aninda soru_hash kapisi var).

---------------------------------------------------------------------

## K0.1 -- Sayfa karti ve sayfa sayisi

| olcu | deger |
|---|---|
| kart x | 591 - 1328 |
| kart y | 46 - 1013 |
| kart boyutu | **738 x 968** |
| 5 ornekte sapma | 0 px |
| PNG | **416** |

Kart, ACIL geometri kartindan (734x968 @ 593,46) 4 px genis ve 2 px
sola kaymis -- ayni aileden AMA ayni degil; olculdu, varsayilmadi.
Wave D kesif fisinde bu kitap "420 PNG" yaziyordu; gercek sayi **416**
(K0.1 olcumu). Disk butun geometri kitaplariyla ayni FERNUS diski
(dolgu 240,238,247; simge merkezine gore -6/-5/22/24).

## K0.2 -- Sayfa haritasi ve basili sayfa no ofseti

| aralik | icerik |
|---|---|
| s1 - s2 | kapak / ic kapak |
| s3 | ON SOZ (Gokhan KECECI) |
| s4 | bos |
| **s5 - s6** | **ICINDEKILER (2 sayfa)** |
| **s7 - s414** | **konu icerigi (asagida)** |
| s415 - s416 | arka kisim |

Basili sayfa no = dosya no (**ofset 0**), UC bagimsiz yerden dogrulandi:
  * icindekiler "Dogruda Aci ... 7" diyor; dosya 7 = "DOGRUDA ACI" konu
    anlatim sayfasi.
  * dosya 9'un alt seridinde sayfa numarasi "9" yaziyor.
  * dosya 8 (sol/cift sayfa) altta solda "8", dosya 10 altta solda "10".

## K0.3 -- Anahtar bicimi: TEST SONU SAYFA-ALTI SERIDI

ACIL 2023-2024'ten (test sonu 2 satirli izgara kutusu) ve ACIL 2025
KURS'tan (her sayfada serit) FARKLI. Burada her testin SON (sag) sayfasinin
altinda tek satirlik yatay bir SERIT, testin tum sorularinin cevabini
birlikte veriyor.

Ornek s9 (TEST 1, sag sayfa): `1 E 2 E 3 D 4 A 5 E 6 C 7 A 8 C 9 B
10 A 11 D 12 C` -- 12 cevap; TEST 1 = s8 (soru 1-6) + s9 (soru 7-12).

| olcu | deger (tam goruntu koordinati) |
|---|---|
| serit y | 940 - 954 |
| serit x | ~620 - 1160 (iki sutunu birden kapsar) |
| kutu zemini | acik mavi kutucuklar, icinde koyu harf |

Sol (cift) sayfalarda serit YOK; altta solda sayfa no, sagda kosan
bolum adi ("DOGRUDA ACI") var. Serit yalniz testin bittigi sag sayfada.

**Sizinti kapisi: kirpim kutularinin alti bu seridin (y~938) ustunde
kalmali.**

## K0.4 -- Simge ortmesi (kalibre arac; PR #305/#307)

`ortme_olc.py` (ACIL 2023-2024 uzerinde 154 olayi birebir ureten
kalibre arac), C1CELL karti + FERNUS diskiyle:

| olcum | deger |
|---|---|
| sag sutun simgesi | 1036 |
| ortme sinyali (UST SINIR) | 301 |
| etkilenen sayfa | 239 |
| diskin sagindaki en kucuk bosluk | **3 px** |
| eski (yanlis) metrik | 145 -- ortme olcusu DEGIL |

**301 UST SINIRDIR, ortme sayisi degil**: bant hem gercek soru metnini
hem kitap mobilyasini yakalar (bkz. GEO_DALGA_D_KESIF ek + PR #307).
Kesin sayi Faz 1 adim 2'de "sik satirinda bes etiket gorunuyor mu"
kapisiyla belirlenir.

**Diskin sagindaki bosluk 3 px** (ACIL 2023-2024'te 27 px'ti). Yani
beyazlatma payi en fazla gx+24 olabilir; daha genis pay soru numarasini
siler. Bu kitapta KAPI 6 (bkz. acil_geo_kirp.py) SART ve payi dar.

## K0.5 -- YENI YAPISAL ZORLUK: IC ICE SAYFA TIPLERI

ACIL 2023-2024 saf test kitabiydi (her sayfa soru). C1CELL DEGIL --
her konu su dort tipi IC ICE tasiyor (icindekilerden ve gozle):

| tip | ornek | soru/cevap var mi |
|---|---|---|
| Konu anlatimi (Konu Ogren) | s7 "DOGRUDA ACI" | HAYIR |
| Ciz Ogren (cozumlu ornek) | s12 | HAYIR (cozum var) |
| Beceri Temelli Sorular | s13 | EVET |
| Numarali TEST | s8-9 "TEST 1" | EVET |

Sonuc: ACIL 2023-2024'te ise yarayan "sutun basina simge sayisi ==
cevap sayisi" kapisi burada DOGRUDAN uygulanamaz -- konu anlatimi ve
Ciz Ogren sayfalarinda buyutec simgesi VAR ama cevap seridi girdisi YOK.
Faz 1 once sayfalari {anlatim, cozumlu, soru} diye SINIFLANDIRMALI,
sonra yalniz soru sayfalarindan kutu turetip cevaba baglamali.

Bu Faz 0'da hizli otomatik siniflandirma denendi (mavi zemin orani +
serit tespiti) ama kaba kaldi (mavi %15 esigi 3 sayfa buldu, serit
tespiti sayfa numarasini da sayip 326 yaniladi). Duzgun siniflandirici
-- kosan bolum adi + ust baslik + numarali soru varligi + cevap seridi
birlikte -- Faz 1'in ILK adimidir. Bu, ACIL 2023-2024'e gore ek is ve
ek risktir; fise acik yazildi.

Sekil hatti: geometri, kirpim zorunlu. Iki sutun (sol simge gx~0-50,
sag simge gx~350). Tek/cift sayfada simge kaymasi Faz 1'de olculur.

## K0.6 -- Mukerrer / baska kitapla ortusme

Yayinevi C1CELL, digerlerinden farkli; DB'de C1CELL kitabi yok. Wave D
kesfinde #3/#4 (Orijinal) ikizi vardi; C1CELL o ikizin parcasi DEGIL
(farkli kart 738x968, farkli yayinevi). Ayni sorunun baska kitapta
tekrari ithal aninda soru_hash kapisiyla yakalanir.

## K0.7 -- Konu agaci: ICINDEKILER TAM ve OKUNAKLI (s5-s6)

Iki sayfalik icindekiler her konuyu UC alt tiple veriyor: ana konu,
"(Ciz Ogren)", "Beceri Temelli Sorular" -- her birinin baslangic
sayfasiyla. Ana konular (baslangic sayfasi):

Dogruda Aci 7; Ucgende Acilar 15; Dik Ucgen 49; Ikizkenar Ucgen 78;
Eskenar Ucgen 89; Aciortay-Kenarortay ve Ucgenin Merkezleri 103;
Ucgende Benzerlik 124; Ucgenin Alani 145; Aci-Kenar Bagintilari 168;
Cokgenler 183; Dortgenler 200; Yamuk 213; Paralelkenar 228; Eskenar
Dortgen ve Deltoid 241; Dikdortgen 249; Kare 262; Cember ve Daire 277;
Kati Cisimler 322; Nokta ve Dogrunun Analitik Incelenmesi 353; Donusum
Geometrisi 385; Cemberin Analitik Incelenmesi 401 (Beceri Temelli
Sorular 414'e kadar).

**21 ana konu.** Mevcut `topic_hierarchy`de bu agacin birebir karsiligi
yok (GEO-U* agaci farkli granuler) -> Faz 1'de C1CELL-2024 onekiyle ayri
alt agac + migration gerekir (ACIL 2025 KURS'un 0034 deseninin aynisi).

## K0.8 -- GO / NO-GO ve maliyet

| kalem | deger |
|---|---|
| PNG | 416 |
| soru sayfasi | Faz 1 siniflandirmasi belirleyecek (< 408) |
| beklenen soru | siniflandirma sonrasi olculur (kaba: 1500-2000) |
| kirpim | zorunlu |
| ortme borcu | UST SINIR 301; kesin sayi Faz 1 adim 2 |
| beyazlatma payi | dar (3 px) -- KAPI 6 sart |
| anahtar | her testin sag sayfasinda serit, eksiksiz |
| DB ortusmesi | yok |

**Karar: GIT.** ACIL 2023-2024 boru hatti buyuk olcude yeniden
kullanilir, AMA iki yeni is var: (1) sayfa-tipi siniflandirici (Faz 1
adim 1), (2) beyazlatma payinin ACIL 2025 KURS gibi dar olmasi -- KAPI 6
payi bu kitaba gore yeniden olculecek.

**Ayrica (sahip karari bekliyor):** Wave D geneli bulgu (GEO_DALGA_D
eki), FERNUS "Zenginlestirme ve Aktivite Dugmelerini Goster" kapali
yeniden yakalamanin disk sinifini butun dalgadan silecegini soyluyor.
C1CELL de 3 px'lik dar-pay kitaplarindan; o test ACIL 2025 KURS'ta
dogrulanirsa C1CELL yeniden yakalamadan da kazanir.

## Olcum dosyalari (git disi, `backend/_geo1_gecici/`)

`faz0_c1.json` (simge/murekkep taramasi), `ortme_c1.json` (kalibre ortme),
`_waved_ortme.py`, `c1_*.png` (ornek sayfa/serit/icindekiler goruntuleri).
