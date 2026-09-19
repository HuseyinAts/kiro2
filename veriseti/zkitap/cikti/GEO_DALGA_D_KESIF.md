# Dalga D (geometri) -- FAZ 0 ON KESIF

Plan: `ZKITAP_ISLEME_PLANI.md` bolum 1, dalga D. Bu fis SALT OKUNUR
olcumlerin sonucudur: transkripsiyon yok, DB'ye yazilmadi.
Tarih: 18 Eyl 2026.

Plan bu dalga icin iki on kosul koymustu:
  (a) #3 / #4 cifti ayni kitap mi?
  (b) #8 DB'deki `Mikro Orijinal 2025 AYT Geometri`nin ikinci cildi mi,
      yoksa ayni kitabin kopyasi mi?

Ikisi de olculdu. **Sonuc: dalga bes kitap degil DORT kitap; ve dorduncu
kitabin ikizi bir KURTARMA KANALI.**

---------------------------------------------------------------------

## Dalganin kitaplari

| # | klasor | PNG |
|---|---|---|
| 1 | 2023-2024-ACIL-TYT-AYT Geometri Soru Bankasi | 448 |
| 3 | Orijinal-2024-Geometri Soru Bankasi | 432 |
| 4 | Orijinal-Tyt Ayt Geometri Soru Bankasi | 432 |
| 5 | C1CELL-2024-TYT-AYT-Geometri Soru Bankasi | 420 |
| 8 | Mikro Orijinal-Tyt Ayt-Geometri Soru Bankasi 2 | 416 |
| 9 | Bilgi Sarmali-2022-2023-Tyt Ayt-Geometri Soru Bankasi | 402 |

## (a) #3 ve #4 AYNI KITABIN AYNI YAKALAMASI

8 ornek sayfada tam goruntu karsilastirmasi:

| sayfa | farkli piksel orani |
|---|---|
| 5 | 0,0059 |
| 20 | 0,0329 |
| 60 | 0,0168 |
| 120 | 0,0062 |
| 200 | 0,0063 |
| 280 | 0,0063 |
| 360 | 0,0073 |
| 420 | 0,0176 |

s200 gozle karsilastirildi: **sayfa icerigi birebir ayni** -- ayni 7-12
sorulari, ayni sekiller, ayni alt cevap satiri. Fark yalnizca okuyucu
uygulamasinin KROMUNDA: sekme adi (`Orijinal - 2024 - TYT - AYT -
Geometri - 5b` vs `ORIJINAL - 2025 - TYT - AYT - Geometri Soru
Bankasi`) ve yuzen arac cubugunun konumu.

**Karar: ikisinden BIRI islenir.** Digeri, Edebiyat kitabinda oldugu
gibi okuyucu simgesi ortmesi icin KURTARMA KANALI olarak kullanilir
(simge konumlari iki yakalamada ayni degil). Yani dalga bir kitap
kisaldi ve ustelik ortme borcu dusecek.

## (b) #8 DB'dekinden FARKLI BIR KITAP

`Mikro Orijinal-Tyt Ayt-Geometri Soru Bankasi 2` (416 PNG, islenmemis)
ile DB'ye giren `Mikro Orijinal-2025-Ayt-Geometri Soru Bankasi`
(416 PNG, 1211 satir) karsilastirildi:

| sayfa | farkli piksel orani |
|---|---|
| 10 | 0,0130 |
| 60 | 0,0350 |
| 120 | 0,0374 |
| 200 | 0,0530 |
| 300 | 0,0671 |
| 400 | 0,0137 |

Sayi tek basina karar verdirmez; s200 gozle karsilastirildi:

  * #8 s200: `OSYM TARZI TEST 3 / YAMUK`, 1-6 numarali alti soru
  * DB'nin kitabi s200: `PARALELKENAR / KESISEN DOGRULAR`, konu
    anlatimi ve `Ornek 1-6`

Ayni sayfa numarasinda TAMAMEN FARKLI icerik. **#8 gercekten ayri bir
kitap** (ikinci cilt); DB'dekinin kopyasi degil. Islenmeye deger.

## Diger uc kitap icin ortusme riski

DB'de yalnizca iki geometri kitabi var: `345 2025 TYT-AYT Geometri`
(2708 satir) ve `Mikro Orijinal 2025 AYT Geometri` (1211 satir).
#1 (ACIL), #5 (C1CELL) ve #9 (Bilgi Sarmali) farkli yayinevleridir;
DB'de ayni yayinevinden geometri kitabi YOK. Bu yuzden bu uclu icin
Faz 0 duzeyinde ortusme riski gorulmedi -- kesin hash ortusmesi her
kitabin kendi Faz 1'inde olculur (Biyoloji'de oldugu gibi surpriz
cikabilir).

## Dalganin guncel buyuklugu

| kalem | plan | olcumden sonra |
|---|---|---|
| islenecek kitap | 5-6 | **4** (#1, #3-ya-da-#4, #5, #8, #9 -> ciftten biri dustu) |
| toplam soru sayfasi (kaba) | ~2550 | ~2118 |
| kurtarma kanali | yok | #3/#4 ikizi |

Not: bu fis GO/NO-GO kararini vermez; yalnizca plan'in iki on kosulunu
kapatir ve dalganin kapsamini bir kitap kucultur. Kitap basina Faz 0
(K0.1-K0.8) henuz yapilmadi.

## Olcum dosyalari (git disi, `backend/_geo2_gecici/`)

`_cift.py`, `_yanyana.py`, `_mikro8.py`, `cift/` (karsilastirma
goruntuleri), `_db_geo.py`.

---------------------------------------------------------------------

## EK (19 Eyl 2026) -- Dalga geneli yakalama geometrisi + ortme

Bu ek, dalganin butun geometri kitaplarina AYNI kalibre araci
(`backend/scripts/kitap/ortme_olc.py`) uygulanarak olculdu. Arac ACIL
2023-2024 uzerinde 154 olayi birebir yeniden urettigi icin kalibredir.
Her kitabin karti ve diski ayri olculdu -- varsayilmadi.

### Kart ve disk

| kitap | kart | disk (simge merkezine gore sol/ust/sag/alt) |
|---|---|---|
| ACIL 2023-2024 | 734x968 @ (593,46) | -6 / -5 / 21 / 24 |
| ACIL 2025 KURS | 734x968 @ (593,46) | -5 / -5 / 21 / 19 |
| C1CELL 2024 | 738x968 @ (591,46) | -6 / -5 / 22 / 24 |
| Orijinal 2024 | 734x968 @ (593,46) | -6 / -5 / 22 / 24 |
| Bilgi Sarmali 22-23 | 734x968 @ (593,46) | -6 / -5 / 22 / 24 |
| Mikro Orijinal 2 | 734x968 @ (593,46) | -6 / -5 / 22 / 24 |

Disk butun kitaplarda ayni FERNUS diski (dolgu 240,238,247).

### Iki olcu -- biri temiz, biri UST SINIR

| kitap | sag sutun simgesi | ortme sinyali (UST SINIR) | diskin sagindaki en kucuk bosluk |
|---|---|---|---|
| ACIL 2023-2024 | 916 | 154 (olculu, dogrulandi) | 27 px |
| ACIL 2025 KURS | 961 | 403 | 3 px |
| C1CELL 2024 | 1036 | 301 | 3 px |
| Orijinal 2024 | 1033 | 309 | 3 px |
| Bilgi Sarmali 22-23 | 868 | 167 | 14 px |
| Mikro Orijinal 2 (3 sutun) | 1559 | 861 (*) | 3 px |

**Diskin sagindaki bosluk TEMIZ olcumdur:** beyazlatma payinin tavan
siniridir. ACIL 2023-2024'te 27 px (rahat); kalan besin dordunde 3 px,
biri (Bilgi Sarmali) 14 px. 3 px'lik kitaplarda ACIL 2023-2024'teki
"8 -> 3" beyazlatma hatasi daha da kolay olur; her birinde KAPI 6 sart
(bkz. acil_geo_kirp.py).

**Ortme sinyali UST SINIRDIR, ortme sayisi DEGIL.** Bant hem gercek
soru metnini hem kitap mobilyasini (baslik bandi, ilerleme seridi,
sekil kenari) yakalar; ACIL 2025 KURS'ta 16 olayin gozle incelemesi
karisik cikti. Kesin sayi her kitabin Faz 1 adim 2'sinde "sik satirinda
bes etiket (A-E) gorunuyor mu" kapisiyla belirlenir.

(*) Mikro Orijinal 2 UC SUTUNLUDUR. 861, iki-sutun aracinin yaklasik
sayimidir; gercek degildir. Bu kitap Faz 1'de uc-sutunlu ortme
kapisina ihtiyac duyar (orta sutun simgesi sol sutunu, sag sutun
simgesi orta sutunu ortebilir).

### Stratejik sonuc

Alti geometri kitabinin hepsi ayni FERNUS diskini ve (biri haric) ayni
dar payi tasiyor. Yani FERNUS okuyucusunun "Zenginlestirme ve Aktivite
Dugmelerini Goster" ayari KAPALI yakalama, tek bir kitapta dogrulanirsa
butun dalganin yakalama stratejisini birden cozer: disk sinifini alti
kitaptan da siler, alti ayri KAPI 6 yukunu ortadan kaldirir. Bu yuzden
ayar testi ACIL 2025 KURS uzerinde once yapilir; sonucu dalga geneli
karardir.

Olcum dosyalari: `backend/_geo1_gecici/ortme_*.json` (git disi),
`_waved_ortme.py` (sarmalayici).
