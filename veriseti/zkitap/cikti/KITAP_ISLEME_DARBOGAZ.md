# Kitap isleme hatti -- dar bogaz olcumu ve cozumler (27 Eyl 2026)

Kaynak: dosya zaman damgalari (`backend/_a21_gecici`, `VeraFilm/a2_*`,
`d-dataset/output/crops/ACL21T`) ve GitHub PR zamanlari (`gh pr view`).
Saatler yerel (UTC+3). Kitap: 2020-2021 ACIL TYT Matematik (ACL21T, 2113 soru).

## 1. Kitap basina sure (uctan uca)

| PR | kitap | is (onceki merge -> PR acilis) | CI (PR acilis -> merge) |
|---|---|---|---|
| #344 | 345 TYT Sosyal | 3 sa 19 dk | 51 dk |
| #345 | 345 TYT Turkce | 4 sa 13 dk | 49 dk |
| #346 | ACL20T | 3 sa 36 dk | 49 dk |
| #347 | ACL21T | 2 sa 38 dk (19:52 -> 22:30; sarj kesintisi haric) | ~49 dk (bekleniyor) |

Ortalama: ~3.5 sa is + ~49 dk CI = ~4.3 sa / kitap. 147 dogrudan islenebilir
kitap icin ~630 saat.

## 2. ACL21T faz kirilimi (158 dk is)

| faz | aralik | dk | pay | not |
|---|---|---|---|---|
| Faz 0 tarama / yerlesim kalibrasyonu | 19:52-20:20 | 28 | %18 | 2 yineleme: NUMARA_X yanlis (capa 0), serit glifi (46 testte capa = serit+1) |
| anahtar + harita + 0074 uretimi | 20:19-20:22 | 3 | %2 | uretec script |
| kutu + kirp (2113 kirpim) | 20:22-20:31 | 9 | %6 | kirpim 3 dk |
| **metin: okuma 1** | 20:32-21:08 | 36 | %23 | 45 grup, 15'lik 3 dalga |
| **metin: okuma 2** | 21:09-21:49 | 40 | %25 | okuma 1 bittikten SONRA basladi |
| **metin: karsilastir + hakem + duzeltme** | 21:49-22:11 | 22 | %14 | 8 hakem, 249 fark |
| mukerrer + ithal + 0075/0076 + test uretimi | 22:11-22:26 | 15 | %9 | |
| commit + push + PR | 22:26-22:30 | 4 | %3 | pre-commit ~2 dk, push 75 sn |

Metin fazi toplam **98 dk = %62**. CI beklemesi uctan uca surenin **%24'u**.

### Metin fazinin ici (dalga bariyeri kaniti)

Okuma 1 grup teslim zamanlari: 1-15 -> 20:38-20:45, 16-30 -> 20:50-20:58,
31-45 -> 21:03-21:08. Her dalga en yavas okuyucuyu bekledi (grup_12 20:45:47,
digerleri 20:41-20:43; grup_19 20:58, digerleri 20:50-20:54). Okuyucu basina
5-13 dk; dalga basina 3-5 dk bariyer kaybi x 6 dalga = ~20 dk.

Okuma 2 tasarim geregi okuma 1'i GORMEZ; ama zamansal olarak ARKASINA
kondu. Bagimsizlik dizin ayrimiyla saglaniyor (parca / parca2), zamansal
siraya ihtiyac yok.

Hakem: 249 karardan 89'u (%36) "esasli hata yok" = yalniz bicim farki.
En sik: bileske halkasi U+2218 / o, carpi U+00D7 / x, ust simge, tek atomu
saran parantez, ust cizgi, kok cizgisi, tablo ayraci.

## 3. Dar bogazlar (etkiye gore) ve durum

| # | dar bogaz | kayip / kitap | cozum | durum |
|---|---|---|---|---|
| 1 | Okuma 2'nin okuma 1'den sonra baslamasi | ~36-40 dk | iki okumayi TEK dagitimda baslat | **COZULDU** (protokol + `metin_iki_okuma.py hazirla`) |
| 2 | 15'lik dalga bariyeri (6 dalga) | ~20 dk | tum gruplari tek partide dagit; arac siniri varsa en buyuk parti, bariyer yok | **COZULDU** (protokol) |
| 3 | CI beklemesi (API Security Testing / ZAP ~42 dk) | ~49 dk | kitap/* veri PR'larinda ZAP'i beklememe ya da bu PR'lar icin kapiyi kaldirma | **SAHIP KARARI** (asagida) |
| 4 | Hakeme giden bicim farklari | ~4-5 dk + hakem gurultusu | `norm()` genisletildi (halka, ust simge, ust cizgi, kok cizgisi, tek atom parantezi, tablo ayraci) | **COZULDU**: 249 -> 208 fark (%16); tek tarafli esasli hata gizlenmedi (gercek veriyle dogrulandi) |
| 5 | Kitap basina 4 gecici script (talimat2/karsilastir/hakem/duzeltme) yeniden yazimi | ~5 dk + kirilganlik | `backend/scripts/kitap/metin_iki_okuma.py` (kitap parametreli, 27 birim testi) | **COZULDU** |
| 6 | Faz 0 yerlesim kalibrasyonu yinelemeleri | ~10-15 dk | ayni seri/yayinevi icin yerlesim profili (SIMGE_X, NUMARA_X, bant) yeniden kullanimi | ACIK (sonraki ayni-seri kitapta olculecek) |
| 7 | Kitap basina 8 script + 3 migration + 2 test = ~4.8k satir kopya kod (14 harness kopyasi var) | ~10 dk uretim + CI/mypy/pre-push buyumesi | tek parametreli hat (kitap profili JSON) | ACIK -- buyuk yeniden yapilandirma, ayri is |
| 8 | Cihaz koprusu 60 sn siniri -> her uzun adim Start-Process + log yoklama | ~1-2 dk x ~10 adim | (arac siniri) | KABUL |

Beklenen kazanc (1+2+4+5): metin fazi 98 dk -> ~40-45 dk; is suresi
~158 -> ~100 dk; CI dahil uctan uca ~207 -> ~150 dk (**%27**). 3 ile
birlikte ~100 dk (**%50**).

## 4. Yeni metin protokolu (sonraki kitaptan itibaren)

1. `<kitap>_metin_harness.py hazirla` (okuma 1 dizini + gruplar).
2. `metin_iki_okuma.py ... hazirla --ornek <onceki_cikti> --tarih <gun>`
   (parca2 + talimat2 + on kayit) -- okuyucular baslamadan ONCE.
3. Okuma 1 (N grup) ve okuma 2 (N grup) okuyucularini TEK dagitimda baslat;
   dalga yok. Okuyucu 2 talimati `<veraf>_metin_talimat2.md`.
4. Iki okuma da tamamlaninca `metin_iki_okuma.py ... karsilastir`.
5. `hakem-hazirla --hakem 8`; 8 hakem tek dagitimda.
6. `duzeltme-yaz`; sonra `<kitap>_metin_harness.py topla` / `kapi`.

Sinir (degismedi): iki okumanin AYNI bicimde atladigi veri karsilastirmada
gorunmez. ACL21T'de hakem, yalniz halka farki yuzunden bakip 2 boyle ortak
hata bulmustu (T132_08 nokta/virgul, T134_15 kesisim/bileske); halka
normalize edilince bu tesadufi yakalama kalkar. Carpi U+00D7 / x bilerek
normalize EDILMEDI: T011_06 ve T015_07'de hakem bunu esasli buldu.

## 5. Sahip karari gereken madde: CI beklemesi

`API Security Testing` (ZAP) her PR'da ~42 dk suruyor ve kitap veri
PR'lari (script + JSON + migration + test) API yuzeyini degistirmiyor.
Secenekler:

a. Kitap PR'larinda deterministik kontroller (Backend Tests miras kumesi,
   ruff/mypy, golden flows) yesilse ZAP'i beklemeden merge; ZAP master'da
   kosmaya devam eder.
b. Workflow'da `kitap/**` dallari / yalniz `scripts/kitap`, `alembic`,
   `veriseti`, `tests/e2e/test_*_veri.py` dokunan PR'lar icin ZAP'i atla
   (paths-ignore). GitHub guvenlik ayari degil, workflow YAML'i; yine de
   guvenlik kapisi oldugu icin karar sahibin.
c. Oldugu gibi birak (~49 dk / kitap).

Karar verilene kadar mevcut kural (bekle) uygulanir.
