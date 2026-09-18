# ACIL 2023-2024 TYT-AYT Geometri -- FAZ 1 YONTEM (surmekte)

Faz 0 fisi: `GEO_ACIL_2324_KESIF.md` (karar GIT).
Sahip karari: ACIL'in her iki baskisi da islenecek; 2025 baskisinin
Faz 0'i `GEO_ACIL_2025_KURS_KESIF.md`.

Bu belge Faz 1 ilerledikce buyur. Su an **1. adim bitti**.

---------------------------------------------------------------------

## Adim 1 -- Cevap anahtari (BITTI)

Cikti: `acil_2324_geometri_cevap_anahtari.json`
(138 test, **1881 cevap**, her satir `{test, soru_no, cevap, bas_sayfa,
son_sayfa}`).

### Neden once anahtar

Faz 0'da olculdu: her testin son sayfasinda iki satirlik izgara kutusu
var ve kutu, testin TUM sorularinin cevabini birlikte veriyor. Bu,
kirpim kutularinin alt sinirini (sizinti kapisi y = 856) ve soru
numaralandirmasini birlikte belirledigi icin hattin ilk halkasi.

Sorular COZULMEDI. Tek kaynak kitabin basili anahtaridir.

### Uc bagimsiz okuma kanali

Piksel dedektoru bu is icin kullanilmadi (Dalga B2 dersi: kucuk puntoda
sayim otoritesi olamaz). Bunun yerine uc kanal:

| kanal | duzen | olcek | sira | sayfa basina test |
|---|---|---|---|---|
| A | montaj | 2x | 1 -> 138 | 10 |
| B | montaj | 1.5x | 138 -> 1 | 10 |
| C | tek tek | 4x | secili 6 test | 1 |

**Kanal A ile B arasinda fark: 0.** 138 testin 138'i, 1881 cevabin
1881'i birebir ayni okundu.

### Dorduncu capraz: simge sayimi

Faz 0'da her sayfanin buyutec simgeleri sayilmisti (1881). Test basina
"anahtar girdisi sayisi == simge sayisi" kapisi kuruldu:

    138 / 138 test tutuyor, toplam 1881 == 1881.

Yani anahtar yalnizca kendi kendisiyle degil, kitabin dizgisinden gelen
bagimsiz bir sayimla da dogrulandi.

### Kirpim penceresi ilk denemede yanlisti (belgeleniyor)

Ilk kirpim, Faz 0'da olculen `cerceve_ust` degerini kullaniyordu. O
deger bazi sayfalarda izgaranin ORTA cizgisini yakaladigi icin kutunun
UST SATIRI kirpiliyordu; ayrica kutu genisligi kirmizi piksel x'inden
turetildigi icin son hucrenin harfi disarida kaliyordu. Comert sabit
pencereye gecildi: kart-ici **y 846-908, x 24-706**. Bu pencere
138 kutunun 138'inde tam kutuyu iceriyor.

### Olculen bir ozellik: anahtar C-agirlikli

| sik | adet | oran |
|---|---|---|
| A | 235 | %12,5 |
| B | 319 | %17,0 |
| C | **570** | **%30,3** |
| D | 472 | %25,1 |
| E | 285 | %15,2 |

Bu, okuma hatasi degil: test basina C orani 0,00 ile 0,62 arasinda
geziyor (std 0,131), yani p=0,30 civarinda gercek bir rastgelelik
gorunumunde -- sistematik bir yanlis okuma olsaydi oran her testte
benzer sisecekti. Ayrica C orani ucta olan alti test (90, 6, 31, 22,
45, 113) 4x buyutmede tek tek dogrulandi; altisi da tuttu.

Pratik sonucu: bu kitapta "hep C isaretle" taban cizgisi %30 yapar.
Kalibrasyon ve zorluk kestirimi bunu hesaba katmali.

## Sirada ne var

| adim | durum |
|---|---|
| 1. cevap anahtari | **BITTI** (1881 cevap, 3 kanal + simge caprazi) |
| 2. kirpim koordinatlari (simgeden turetilir; tek/cift 18 px kaymasi) | siradaki |
| 3. sayfa transkripsiyonu (442 sayfa, ~37 grup, ~5,5M jeton) | -- |
| 4. konu agaci migration (6 bolum / 27 konu) | -- |
| 5. ithal araci + e2e testler | -- |

## Olcum dosyalari (git disi, `backend/_geo1_gecici/`)

`_a1_kutu_kirp.py` (138 kutu kirpimi), `_a1_montaj.py` (kanal A/B
montajlari), `anahtar/` (kutu goruntuleri), `montaj_a/`, `montaj_b/`,
`kanal_c*.png`, `okuma_a.json`, `cevap_anahtari.json`, `testler.json`.
