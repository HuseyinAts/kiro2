# Dalga D / kitap #1 -- ACIL 2023-2024 TYT-AYT Geometri Soru Bankasi
# FAZ 0 KESIF FISI

Plan: `ZKITAP_ISLEME_PLANI.md` bolum 1 (dalga D) ve bolum 3 (K0.1-K0.8).
On kosullar `GEO_DALGA_D_KESIF.md`'de kapatilmisti; bu fis dalganin ILK
kitabinin kitap-basi Faz 0'idir.

Bu fis SALT OKUNUR olcumlerin sonucudur: DB'ye yazilmadi, soru
transkripsiyonu yapilmadi, hicbir soru cozulmedi. Tarih: 18 Eyl 2026.

Klasor: `veriseti/zkitap/screenshots/2023-2024-ACIL-TYT-AYT Geometri Soru Bankasi`
(dosya adinda Turkce karakter var; scriptler glob ile buluyor.)

---------------------------------------------------------------------

## K0.1 -- Sayfa karti ve sayfa sayisi uzlasmasi

12 ornek sayfada (5, 40, 80, 120, 160, 200, 240, 280, 320, 360, 400, 440)
kart dikdortgeni **sapmasiz** olculdu:

| olcu | deger |
|---|---|
| kart x | 593 - 1326 |
| kart y | 46 - 1013 |
| kart boyutu | **734 x 968** |
| ekran | 1920 x 1080 |
| 12 ornekte sapma | 0 px |

Kart, Mikro Fizik (728x968 @ 596,46) ve 345 Fizik (748x980 @ 584,42) ile
ayni aileden ama **ayni degil** -- plan kuralinin ("varsayma, olc") yine
karsiligini verdigi yer.

Sayfa sayisi uzlasmasi: PNG 448 (`sayfa_0001..0448`), PDF `/Count 448`.
**Uyusuyor.**

## K0.2 -- Sayfa haritasi ve basili sayfa no ofseti

| aralik | icerik | simge |
|---|---|---|
| s1 | kapak | (kapak grafiginde 4 yanlis pozitif) |
| s2 - s4 | on kisim; s3 = ICINDEKILER | 0 |
| **s5 - s446** | **soru sayfalari (442 sayfa)** | 1881 |
| s447 - s448 | arka kapak | 0 |

Basili sayfa no = dosya no (**ofset 0**), iki bagimsiz yerden dogrulandi:

  * s5 alt ortasinda "5" yaziyor, ustunde "Test - 1 / Dogruda Acilar";
    icindekiler "Dogruda Acilar ......... 5" diyor.
  * s200 alt ortasinda "200" yaziyor, ustunde "Test - 7 / Kare";
    icindekiler "Kare ......... 178" diyor (178-200 araligi).

## K0.3 -- Anahtar bicimi: TEST SONU KUTUSU

Bu kitap, simdiye kadar gorulen uc bicimden de farkli, **dorduncu** bicimi
kullaniyor: her testin SON sayfasinin altinda, iki satirlik kucuk bir
IZGARA KUTUSU, testin tum sorularinin cevabini birlikte veriyor
(ornek s200: `1.C 2.A ... 13.B`).

| olcu | deger (kart-ici koordinat) |
|---|---|
| kutulu sayfa | **138** |
| kirmizi rakamlarin y araligi | 861 - 898 |
| kutu cercevesinin ust cizgisi | 856 - 888 |
| kutu x araligi (tipik) | 394 - 665 |
| kutu x araligi (aykiri: s47) | 50 - 665 |

Test uzunlugu dagilimi: 3 sayfa (99 test), 4 sayfa (33), 2 sayfa (5).
Ilk kutu s7, son kutu s446; kutular arasi bosluk yok, son kutudan sonra
soru sayfasi kalmiyor. Yani **anahtari olmayan test YOK** (plan R5 riski
bu kitapta gerceklesmiyor).

**Sizinti kapisi (emsal: 345 Fizik `test_kirpim_cevap_satirini_icermiyor`):**
kirpim kutularinin alti kart-ici **y = 856**'nin USTUNDE kalmali.

Anahtar <-> soru sayisi caprazi, 6 testte simge sayimi ile karsilastirildi:

| test (sayfa) | simge | kutudaki son numara |
|---|---|---|
| 5-7 | 12 | 12 |
| 35-37 | 12 | 12 |
| 126-128 | 14 | 14 |
| 204-206 | 12 | 12 |
| 319-321 | 16 | 16 |
| 444-446 | 12 | 12 |

6/6 tam tutuyor (78 soru). Kalan 132 testin caprazi Faz 1'e birakildi.

## K0.4 -- Simge ortmesi: YOK denecek kadar az

Okuyucu ayni FERNUS: disk (240,238,247), glif (69,39,160), disk boyutu
1678 blogun 1604'unde tam **30 x 32**.

Olculen: 1881 simge. Disk DAIRESI icinde kitap murekkebi olan simge
**168 (%8,9)** -- ve bunlarin **tamami** sag sutun simgeleri
(gx 344/346/359/361). Ortulen sey soru degil, sayfa mobilyasi: sutun
ayirici cizgi ve dikey "ACIL MATEMATIK" filigrani. Sol sutun
simgelerinde (gx 14/32, 959 adet) **tek bir olay bile yok**.

Emsal Edebiyat'ta %30,7 ile "ithal et ama isaretle" karari verilmisti;
bu kitapta soru metnini/seklini ortme **olculemedi**.

### Iki olcum tuzagi (ikisi de yakalandi)

  * **Kare ayak izi yanlisti.** Disk daire; 30x32 kare maskenin koseleri
    sayfayi gosteriyor, bu yuzden "diskin ALTINDA murekkep %12,4" gibi
    fiziken imkansiz bir sonuc cikti (disk opak). Dairesel maske (r<=15
    ic, 15<r<=18 halka) dogruyu verdi.
  * **Cizim, glif rengine dusebiliyor.** s435'teki bisikletli cizimin
    lacivert formasi (69,39,160)'a 40 tolerans icinde kaliyordu ve 6
    sahte "temas" uretiyordu. Cozum: glif blogunun cevresinde DISK
    halkasi sarti. Sahte simge sayisi 1890 -> **1881**.

## K0.5 -- Sekil yogunlugu: SEKIL hatti

442 soru sayfasinin **tamaminda** grafik/renkli icerik var
(renkli piksel ortalamasi 14.189 / 710.112 = %2,0; renkli < 2000 olan
sayfa sayisi 0). Geometri kitabi oldugu icin sorularin cogunda sekil
var (s5: 4/4, s200: 3/4, s435: 2/5 gozle sayildi).

**Karar: METIN degil SEKIL hatti.** Kirpim isi zorunlu, 345 Fizik'teki
hat aynen kullanilabilir.

### Faz 1 icin iki dizgi kurali (olculdu)

  * **Simge sutunlari TEK/CIFT sayfada 18 px kayiyor.** Tek sayfa:
    gx 14 ve 346. Cift sayfa: gx 32 ve 361. (Tek: 480 + 455; cift:
    479 + 458.) Tek bir kirpim koordinati varsayilsa cift sayfalarin
    tamami kayardi.
  * **Tam genislik (tek sutun) sayfa var ama tek tane: s47.** "Karma
    Test - 4" icinde, sayfanin tamamini kaplayan tek soru ve tam
    genislikte cevap kutusu (kutu x0 = 50). Sutun bolme mantigi bu
    sayfayi ozel ele almali.

## K0.6 -- Surum / kopya

DB'de ACIL yayinevinden **geometri kitabi yok** (havuzdaki iki geometri
kitabi: `345 2025 TYT-AYT Geometri` 2708 satir, `Mikro Orijinal 2025 AYT
Geometri` 1211 satir). Bu kitap icin DB tarafinda ortusme riski yok.

Ancak ekran goruntusu havuzunda ayni yayinevinden ikinci bir klasor var:
`ACIL-TYT-AYT-Geometri Soru Bankasi` (400 PNG). Okuyucu sekme adi
**"ACIL - 2025 - TYT - AYT - Geometri Soru Bankasi"**: yani DAHA YENI bir
baski ve ustelik **farkli dizgi** -- s7'de "Konu Ogrenme" bantlari, sari
konu basliklari ve sutun ALTINDA serit anahtar var (bu kitapta test sonu
kutusu var). Ayni kitabin ayni yakalamasi degil.

Bu klasor dalga D listesinde degil. Iki soru SAHIBE birakiliyor:

  1. Hangi baski isteniyor -- 2023-2024 (448 sayfa, bu fis) mi, 2025
     (400 sayfa) mi, yoksa ikisi de mi?
  2. Ikisi de islenirse ortusme, Biyoloji'de ogrenildigi gibi sayfa
     sayfa degil **kitap duzeyinde dizi hizalamasi** ile olculmeli.

## K0.7 -- Konu agaci

s3 (ICINDEKILER) tam ve okunakli: **6 bolum / 27 konu**, her konunun
baslangic sayfasi ile birlikte.

| bolum | konular (baslangic sayfasi) |
|---|---|
| 1 UCGENLER | Dogruda Acilar 5; Ucgende Acilar 11; Ozel Ucgenler 26; Aciortay 48; Kenarortay 57; Eslik ve Benzerlik 66; Ucgende Alan 87; Aci Kenar Bagintilari 109; Ucgende Merkezler 116 |
| 2 DORTGENLER | Genel Dortgenler 123; Paralelkenar 129; Eskenar Dortgen 147; Dikdortgen 156; Kare 178; Deltoid 201; Yamuk 207; Cokgenler 224 |
| 3 CEMBERLER | Cemberde Acilar 240; Cemberde Uzunluk 253; Cemberin Cevresi 274; Dairenin Alani 280 |
| 4 ANALITIK GEOMETRI | Noktanin Analitigi 303; Dogrunun Analitigi 316; Donusum Geometrisi 334; Analitik Geometri 344 |
| 5 KATI CISIMLER | Kati Cisimler 369 |
| 6 CEMBER ANALITIGI | Cemberin Analitik Incelenmesi 423 |

Mevcut `topic_hierarchy`de bu agacin karsiligi yok -> **migration
gerekiyor** (sirada 0034; 0033 = FIZ345).

## K0.8 -- GO / NO-GO ve maliyet

| kalem | deger |
|---|---|
| soru sayfasi | 442 |
| beklenen soru | **1881** (simge sayimi; 6 testte anahtarla capraz dogrulandi) |
| test | 138 |
| grup (12 sayfa) | ~37 |
| transkripsiyon kaba maliyet | ~37 x 150k = **~5,5M jeton** |
| kirpim | zorunlu (sekil hatti), 345 Fizik hatti yeniden kullanilabilir |
| ortme borcu | yok |
| anahtarsiz test | yok |
| DB ortusmesi | yok |

**Karar: GIT.** Bu kitap simdiye kadar islenen kitaplarin en temizi:
kart sapmasiz, sayfa sayilari uzlasiyor, her testin anahtari var, ortme
yok. Tek yapisal ozel durum s47 (tam genislik sayfa) ve tek/cift 18 px
kaymasi; ikisi de olculdu ve Faz 1 kurallarina yazildi.

Faz 1'e baslamadan once SAHIBIN cevaplamasi gereken tek soru K0.6'daki
baski secimidir (2023-2024 mu, 2025 mi, ikisi de mi).

## Olcum dosyalari (git disi, `backend/_geo1_gecici/`)

`_k01.py`, `_k01b.py` (kart), `_k04a.py` (simge imzasi),
`_faz0_tara.py` / `_faz0_tara2.py` (tam kitap taramasi; v2 disk halkasi
kapisini ekler), `_k04_dogrula.py`, `_k04_disk.py`, `_k04_disk2.py`,
`_k04_daire.py` (ortme olcumunun dort kademesi),
`_k03_kutu.py` / `_k03b.py` (cevap kutusu geometrisi),
`faz0.json`, `faz0b.json`, `k03b.json`, `k04daire.json`,
`simge_zoom.png`, `anahtar_ornek.png`.
