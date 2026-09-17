# Bilgi Sarmal AYT Edebiyat Soru Bankasi -- FAZ 0 KESIF FISI

Plan: `ZKITAP_ISLEME_PLANI.md` bolum 2 (K0.1-K0.8). Bu fis SALT OKUNUR
olcumlerin sonucudur: hicbir sayfa transkribe edilmedi, hicbir anahtar
okunmadi, DB'ye yazilmadi. Tarih: 17 Eyl 2026.

Kaynak klasorler (`veriseti/zkitap/screenshots/`):
  A = `Bilgi Sarmal Ayt Edebiyat Soru Bankasi`        (416 PNG)
  B = `Bilgi Sarmal Ayt Edebiyat Soru Bankasi 2024`   (416 PNG)

---------------------------------------------------------------------

## K0.6a -- IKI SURUM AYNI KITAP MI? (once bu, cunku gerisini belirler)

Sekme cubugundaki basliklar (goruntuden okundu):
  A: "2023 - 2024 - BS - TYT - Turkce Soru Bankasi" sekmesi + AKTIF
     "2023 - 2024 - BS - AYT - Edebiyat Soru Bankasi"
  B: "BS - 2024 - AYT - Edebiyat - Sb"

Sayfa karti icinde TAM SAYFA piksel farki (416/416 sayfa, esik 24):
  fark 0 olan sayfa: **0**   (BS Turkce'deki ikinci klasor fark 0 idi)
Yani bu iki klasor AYNI YAKALAMA DEGIL.

Icerik ayni mi? Murekkep maskesi +-2 px hizalanip Jaccard olculdu
(416 sayfa):

| olcut | sayfa |
|---|---|
| J >= 0.85 (ayni icerik, yalniz render gurultusu) | 318 |
| J <  0.85 (GERCEKTEN farkli) | 98 |

Govde araliginda (12-405): 303 sayfa ayni, 91 sayfa farkli.

Iki uc ornek 1.5x/5x buyutmede GOZLE dogrulandi:
  * s50: soru 6,7,8,10 ayni; **soru 9 metni revize** -- A "Tanpinar,
    siirlerinde...", B "Ahmet Hamdi Tanpinar, siirlerinde..." (yazar adi
    tam yazilmis, satir sarmasi degismis).
  * s48: **soru 11 ve 14 TAMAMEN FARKLI SORU** (A: guzel sanatlar
    olcutleri / kavram listesi; B: Tristan Tzara-Dadaizm / Surrealizm).
    Soru 12 ve 13 ayni.

SONUC: ayni kitabin iki baskisi; ~%76 ortak, ~%24 revize. Kopya DEGIL,
bu yuzden "birini atla" karari icerik kaybi demektir.

ONERI (D2): **B (2024)** islenir -- daha yeni baski ve orneklerde metni
daha tam. A'nin yalniz FARKLI 91 govde sayfasi, sonradan ek bir kucuk
tur olarak islenebilir (tam ikinci tur maliyetinin ~1/4'u); ortak sorular
`soru_hash` ayni id'yi urettigi icin cakismaz.

---------------------------------------------------------------------

## K0.1 -- SAYFA KARTI (varsayilmadi, olculdu)

12 ornek sayfanin murekkep birlesimi, uygulama kromu maskelenerek:

    A: x 596-1323, y 46-1013      B: x 596-1323, y 46-1013

Kirpim kutusu olarak `(596, 46, 1324, 1014)` = **728 x 968 px** alindi.
(BS Turkce'de 592-1328 / 42-1016 idi; ayni yayinevi, ayni okuyucu, 4 px
fark -- varsayim yerine olcum bu yuzden gerekli.)

PNG ve PDF sayfa sayisi: 416 = 416, uyusmazlik YOK.
PDF'te metin katmani YOK; gomulu gorsel 1920x1080 -- cozunurluk tavani
BS Turkce ile ayni.

Basili sayfa numarasi <-> dosya numarasi: f12->12, f13->13, f50->50,
f100->100, f200->200, f300->300, f350->350, f390->390, f400->400,
f403->403, f405->405 (11 sayfada goruntuden okundu).
**Govde icin ofset 0.** Anahtar bolumunun kendi numaralandirmasi var
(f409 -> basili 109, f416 -> basili 116).

---------------------------------------------------------------------

## K0.2 -- SAYFA HARITASI (piksel kanallariyla, metin okunmadan)

| dosya | icerik | tespit |
|---|---|---|
| 1-3 | kapak, kunye/yazarlar, SUNU | goz |
| 4-7 | ICINDEKILER (4 sayfa) | goz |
| 8-9 | kavram semasi / GUZEL SANATLAR bilgi sayfasi | goz |
| 10, 53, 106, 257, 345 | BOLUM ayraci (1..5. BOLUM) | sari bant |
| 11, 54, 107, 258, 346, 406, 407 | SORDUK/SORDULAR (7 sayfa) | sari bant + goz |
| 12-405 | test soru sayfalari (yukaridaki ayrac/SORDUK sayfalari haric 386 sayfa) | -- |
| 408 | CEVAP ANAHTARI kapagi | goz |
| 409-416 | CEVAP ANAHTARI (8 sayfa, basili 109-116) | yatay cetvel 14-20 |

**Bagimsiz kanal -- test baslangic sayfalari:** basliktaki gri bant
(kart y 30-100, notr gri > 8000 px) ile **130 sayfa** bulundu:
12, 14, 16, 18, 20, 22, 25, 28, 30, 33, ... , 375, 392.
Anahtarin ilk sayfasindaki `Sayfa:` degerleri (12, 14, 16, 18, 20, 22,
25, 28, 30, 33, 35, 37, 40, 42, 44, 46, 49) bu listenin ilk 17 ogesiyle
BIREBIR ayni -- yani anahtar okunmadan once test sayisi ve yerleri
bagimsiz olarak biliniyor. Faz 1'de tam kapi olarak kullanilacak:
**anahtardaki test sayisi 130 ve her `Sayfa:` bu listede olmali.**

---------------------------------------------------------------------

## K0.3 -- CEVAP ANAHTARI: IKI AYRI KAYNAK

1. **Kitap sonu anahtari** (f409-416). Bicim BS Turkce ile ayni:
   `Test N: <konu>   Sayfa: <s>` + 6 sutunlu izgara (`1. B  2. D ...`).
   Bolum basliklari da burada (ornek: "1. BOLUM / EDEBI AKIMLAR
   EDEBIYATA GIRIS EDEBIYATIN GUZEL SANATLARLA VE BILIMLE ILISKISI").
   Bu, konu agacinin da kaynagidir (K0.7).

2. **SORDUK/SORDULAR sayfalari** (7 sayfa): dogru sik sayfanin ICINDE
   **KIRMIZI** basili (ornek f11: "A) Ekspresyonizm" kirmizi). Bu sorular
   kitap sonu anahtarinda YOK. Kirmizi metin piksel olarak tespit
   edilebilir -> ikinci, bagimsiz ve yine BASILI bir cevap kaynagi.
   Kutular iki tur: "AYT Edebiyat" (yayinevinin sorusu) ve "OSYM
   AYT-2021" gibi CIKMIS soru -- yil etiketi kutunun ustunde basili.

Her iki durumda da cevap KITAPTAN okunur; soru cozulmez.

---------------------------------------------------------------------

## K0.4 -- OKUYUCU SIMGESI ORTMESI (bu kitabin kritik riski)

Yontem BS emsali (`_bs_gecici/simge.py`, `ortme.py`): disk (240,238,247)
ve glif (69,39,160) maskesi -> blok; blogun solundaki 4 px seritte kitap
murekkebi araniyor.

**Ilk olcum yanlisti ve duzeltildi.** Ilk surum murekkebi `min(RGB)<130`
sayiyordu; bu, turuncu sutun ayracini, cyan bilgi kutusu kenarini ve sari
susleme ucgenlerini de "metin" sayar. 8 orneklik goz kontrolunde goruldu.
Duzeltilmis metin maskesi: `max(RGB)<150 ve (max-min)<60` (koyu + notr).

| olcum | deger |
|---|---|
| simge blogu (f12-405) | 1984 |
| **kirlenmis** olcum: temas >= 6 px | 277 blok / 229 sayfa |
| **duzeltilmis**: metin temasi >= 6 px | **133 blok / 121 sayfa** |
| bunlarin kirlenmis olcumdeki payi | 277'nin 145'i SADECE renkli oge idi |

Simge blogu ~= soru basina bir simge grubu (buyutec + "?" birlesik):
1984 blok / 394 sayfa = sayfa basina ~5, s50'deki 5 soru ile tutarli.
Buna gore ortme ust siniri **133 / ~1984 = %6.7** -- BS Turkce'deki
%30.7'nin yaklasik dortte biri.

**Yigilma testi** (kirpilma gercek mi?): simge bandindaki metin
satirlarinda "disk sol kenari - metnin en sag x" mesafesi, ayni
sayfadaki simgesiz satirlarla karsilastirildi:

    mesafe = 1 px:  simge bandi %4.15   kontrol %1.15   (3.6 kat)
    mesafe >= 21:   simge bandi %56.6   kontrol %68.2

Yani kirpilma sinyali GERCEK ama zayif ve 133 blokla sinirli.

**Goz kontrolu (8 rastgele, 5x):** sekiz ornegin sekizinde de satir
sonundaki kelime ve tire TAM okunuyor (ornek "...kitap bulun-",
"...asagidakilerin han-"). Yani 133 blogun onemli bolumu "metin diske
degiyor" olup "karakter kayboluyor" degil. Kesin sayim ancak
transkripsiyon sirasinda satir satir yapilabilir.

### KURTARMA KANALI VAR (BS Turkce'de YOKTU)

Iki surumun simge KONUMLARI farkli: ayni sayfada simge maskelerinin
yalniz ~%35'i ortusuyor (A x 22-29'dan, B x 31-36'dan basliyor, ~7 px
kayma). Ayni icerikli 303 govde sayfasinda **B'de ortulen bolge A'da
aciktadir**. Yani bu kitapta ortulen metin BELGELENEBILIR SEKILDE
KURTARILABILIR; BS Turkce'de ikinci kopya fark 0 oldugu icin bu mumkun
degildi.

Faz 1 kurali: ortme bayragi konan her satir icin once A'ya bakilir;
kurtarilirsa `okuyucu_simgesi_ortmesi=false` ve
`ortme_kurtarildi='diger_baski_2023_2024'` yazilir.

---------------------------------------------------------------------

## K0.5 -- SEKIL YOGUNLUGU: METIN HATTI

Uzun yatay cetvel (>=120 px kesintisiz koyu kosu) sayimi, govdede
sayfa basina neredeyse sifir; >=10 olan yalniz 4 sayfa (11, 292, 335,
356). Sayfalarda sekil/grafik degil, cyan bilgi kutulari ve renkli
cerceveler var. Goz kontrolu (s48, s50, s126, s232, s268, s300, s323,
s336, s382, f11) hicbirinde soru gorseli gerektiren sekil gostermedi.

**Karar: METIN hatti** (BS Turkce / Dilbilgisi deseni). `*_kirp.py`,
`question_image_url` ve ikon-tabanli sutun kirpimi GEREKMEZ. Sekil/tablo
cikarsa `gorsel_yok_sekilli` bayragi ile isaretlenir (BS Turkce'de 14
satirda oldugu gibi).

---------------------------------------------------------------------

## K0.7 -- KONU AGACI

DB'de `topic_hierarchy` altinda EDB kokunun tek bir seviye-2 dugumu var;
Edebiyat icin agac pratikte YOK. Modern ithal satiri da 0 (ders bazinda
en buyuk bosluk -- plan bolum 1'deki oncelik gerekcesi dogrulandi).

Kaynak: anahtarin bolum basliklari + ICINDEKILER (f4-f7) + 130 test
basligi. 5 bolum olculdu (ayrac sayfalari 10, 53, 106, 257, 345):
  1. EDEBI AKIMLAR / EDEBIYATA GIRIS / EDEBIYATIN GUZEL SANATLARLA VE
     BILIMLE ILISKISI
  2. MASAL - FABL - DESTAN - EFSANE - HIKAYE (OYKU)
  3. DUYGU VE HEYECANI DILE GETIREN METINLER (SIIR)
  4. ROMAN
  5. TIYATRO (GOSTERMEYE DAYALI METINLER)
(+ "OSYM Tipi Yeni Nesil Sorular" f392 ile baslayan kapanis testi.)

Faz 1'de 0029 deseninde iki seviyeli migration yazilacak: EDB koku
altina 5 bolum + test basliklarindan turetilen konular.

---------------------------------------------------------------------

## K0.8 -- GO / NO-GO ve MALIYET

| kalem | deger |
|---|---|
| transkribe edilecek sayfa | 386 test sayfasi + 7 SORDUK = **393** |
| 12'lik grup | ~33 |
| grup basina (BS olcumu) | ~140-160k jeton |
| transkripsiyon toplami | ~5M jeton (TAHMIN) |
| anahtar (cift okuma) + kapilar + kod + test | ~0.5-1M (TAHMIN) |
| beklenen soru sayisi | ~1984 (simge kanali) + ~28 SORDUK |
| ek tur (A'nin farkli 91 sayfasi) | ~8 grup, ~1.2M (opsiyonel, D2) |

Sekil hatti yuku YOK (K0.5). Kurtarma kanali ortme borcunu BS
Turkce'deki gibi kalici yapmiyor.

**KARAR: GIT.** Engelleyici bulgu yok; ortme orani emsalin dortte biri
ve kurtarilabilir; anahtar iki kaynakta da BASILI; test sinirlari
anahtardan bagimsiz bir piksel kanaliyla zaten belirlenmis.

---------------------------------------------------------------------

## Sahibe birakilan (Faz 1 ilerlerken cevaplanabilir)

  * **D2** -- A'nin farkli 91 sayfasi da islensin mi? (plan varsayilani:
    once B tek basina biter, sonra ayri bir tur olarak degerlendirilir)
  * **D4** -- ortme politikasi: kurtarilamayan satirlar icin BS emsali
    ("ithal et ama isaretle") uygulanacak; farkli isteniyorsa soylenmeli.

## Olcum dosyalari (git disi, `backend/_edb_gecici/`)

`_cift.py`/`cift_fark.json`, `_cift_kart.py`/`cift_kart.json`,
`_hizala.py`/`hizala.json`, `_hizala_tam.py`/`hizala_tam.json`,
`_kart.py`, `_harita.py`/`harita_2024.json`, `_simge.py`/`simge.json`,
`_simge2.py`/`simge2.json`, `_margin.py`/`margin.json`,
`_kirpik.py`/`kirpik.json`, `_kirmizi.py`/`kirmizi.json`,
`_sorduk.py`/`sorduk.json`, `sayfa_turu.json`, `_kurtarma.py`.
