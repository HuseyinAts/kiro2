# 345 2024 AYT Biyoloji Soru Bankasi -- FAZ 0 KESIF FISI

Plan: `ZKITAP_ISLEME_PLANI.md` bolum 2 (K0.6 agirlikli). Dalga C.
Bu fis SALT OKUNUR olcumlerin sonucudur: DB'ye yazilmadi, migration
yok, ithal yok. Tarih: 18 Eyl 2026.

Kaynak: `veriseti/zkitap/screenshots/345 2024 Ayt Biyoloji Soru Bankasi/`
-- 376 PNG (1920x1080) + PDF.

**KARAR: ATLA (tam dalga acilmasin).** Gerekce asagida olculdu.

---------------------------------------------------------------------

## Ozet

DB'de `345 2025 AYT Biyoloji Soru Bankasi` adiyla **1315 satir** zaten
var. Bu klasor (2024 baskisi) ayni kitabin bir onceki baskisidir ve
buyuk olcude AYNI SORULARI tasir. Tam dalga (~1330 soru, ~6-8M jeton)
acmanin getirisi **kabaca 30-60 yeni soru**dur.

| olcum | sonuc |
|---|---|
| 2024 baskisinda cevap satiri tasiyan sayfa | 313 |
| 2024 baskisinda okunan cevap girdisi | 1332 |
| DB'deki 2025 baskisi satiri | 1315 (313 sayfa) |
| iki baskinin GENEL cevap dizisi hizalamasi | **%85,2** |
| hizalanan cevap | 1128 / 1332 |
| hizalanmayan (2024 tarafi) | 204 |
| bunlarin 5+ uzunlukta blok olani | 61 soru, 8 bolge |

## K0.1 -- Sayfa karti ve okuma hatti

Kart, 345 AYT Fizik ile AYNI cikti (ayni yayinevi, ayni okuyucu):

    x 584-1331, y 42-1021   ->  (584, 42, 1332, 1022) = 748 x 980

Cevap satiri da ayni yerde: kart ic koordinatinda y 892-897, x 70-669,
sayfa basina sol/sag sutun ayri. Yani B2'de kurulan tum hat bu kitapta
DEGISIKLIK OLMADAN calisti.

## K0.6 -- ORTUSME (bu dalganin asil kapisi)

### 1. adim: cevap satiri okundu (tam kitap)

313 sayfanin cevap satiri 6 ayri alt ajanla okundu (5x olcek, 12'serli
montaj): **1332 girdi, 0 adet "?"**. Okuyuculara sayfa basina kac girdi
bekledigim soylenmedi.

### 2. adim: DB'deki 2025 baskisiyla hizalama

Iki baskinin cevap dizileri kitap boyunca hizalandi
(difflib.SequenceMatcher):

  * benzerlik orani **0,852**
  * en uzun eslesen bloklar: 64, 57, 33, 31, 27, 27, 24, 23, 22, 22
  * 5+ uzunlukta fark blogu: 11

Sayfa sayfa karsilastirma YANILTICI: iki baski arasinda soru
numaralandirmasi ve sayfa sinirlari kaymis (ornek: s58'in dizisi 2025
baskisinda s60'ta cikiyor). Bu yuzden karsilastirma sayfa duzeyinde
degil, KITAP DUZEYINDE dizi hizalamasi olarak yapildi.

### 3. adim: en cok ayrisan 8 bolge TRANSKRIBE edildi

Hizalamanin 5+ uzunlukta fark verdigi 8 bolgeden 36 sayfa (24-30,
59-61, 66-71, 247-250, 332-337, 343-347, 350-354) 3 ajanla
transkribe edildi: **129 soru**. Her biri DB'deki 1315 satira karsi
once hash, sonra kelime kumesi ortusmesiyle karsilastirildi:

| durum | adet |
|---|---|
| hash BIREBIR ayni | 17 |
| kelime ortusmesi >= 0,75 (ayni soru, farkli transkripsiyon) | 78 |
| 0,50 - 0,75 (buyuk olasilikla ayni) | 5 |
| **< 0,50 -- GERCEKTEN YENI** | **28** |
| degerlendirilemeyecek kadar kisa | 1 |

Yani **en cok ayrisan bolgelerde bile sorularin %74'u zaten DB'de**.

Yeni cikan 28 sorunun bolgelere dagilimi:

| sayfa araligi | yeni soru |
|---|---|
| 24-30 | 4 |
| 59-61 | 0 |
| 66-71 | 3 |
| 247-250 | 5 |
| 332-337 | 2 |
| 343-347 | 5 |
| 350-354 | 9 |

Yeni sorularin bulundugu sayfalar: 25, 30, 67, 68, 70, 248, 249, 250,
335, 336, 343, 344, 346, 350, 351, 352, 353, 354.

### 4. adim: tum kitaba tasima

Hizalanmayan 204 cevabin en ayrisik 61'ini kapsayan bolgelerde yeni
icerik orani %22 (28/129) cikti. Ayni orani hizalanmayan tumune
uygularsak tum kitapta beklenen yeni soru sayisi **~45**tir. Bu bir
KESTIRIMDIR (olcum kapsami: 129 soru); kesin sayi ancak tam
transkripsiyonla bulunur -- ki bu zaten atlamak istedigimiz maliyettir.

## Neden ATLA

| secenek | maliyet | getiri |
|---|---|---|
| tam dalga (1332 soru) | ~6-8M jeton | ~45 yeni soru + 1287 mukerrer |
| hedefli mini-ithal (18 sayfa) | ~0,5M jeton | 28 olculmus yeni soru |
| atla | 0 | 0 |

Tam dalga, soru basina yaklasik 150 kat daha pahali. Ayrica 1287
mukerrer satir DB'ye girerse her biri `mukerrer_aday` bayragiyla
isaretlenir ve urun sahibine 1287 kalemlik bir birlestirme isi cikar.

**Oneri: tam dalga ACILMASIN.** Sahip isterse ikinci secenek
(yalnizca yukarida sayilan 18 sayfadaki 28 soru) ayri ve kucuk bir
dalga olarak yapilabilir; o sorularin metni ZATEN transkribe edildi
(`backend/_bio_gecici/hedefli_metin.json`), geriye cevap eslemesi,
kirpim ve ithal kaliyor.

## Yan bulgu: DB'deki kitabin adi

DB'deki kayit `345 2025 AYT Biyoloji Soru Bankasi` adini tasiyor ve
`sayfa_dosya_no` 8-376 araligindan geliyor. Diskteki 2025 klasoru 374
PNG tasiyor ama numaralari 3-376; yani iki klasor de 376 basili sayfa.
s120'nin soru numaralandirmasi (sol 6, sol 7, sag 8) DB ile birebir
ortustugu icin **DB'deki ithal 2025 klasorunden yapilmis**tir; 2024
klasoru gercekten islenmemis olan taraftir.

## Olcum dosyalari (git disi, `backend/_bio_gecici/`)

`_hizalama.py`, `_cift.py`, `_kart.py`, `_giris.py`/`giris.json`,
`_montaj.py`/`montaj_a/`, `_db_bio.py`, `_db_bio2.py`,
`_db_disa.py`/`db_2025.json`, `_sayfa_kirp.py`/`sj/`,
`_ortusme.py`/`ort.txt`, `hedefli_metin.json`.
