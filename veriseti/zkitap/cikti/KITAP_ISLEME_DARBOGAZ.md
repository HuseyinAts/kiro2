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
| 3 | CI beklemesi (API Security Testing / ZAP ~42 dk) | ~49 dk | kitap/* veri PR'larinda ZAP'i beklememe ya da bu PR'lar icin kapiyi kaldirma | **COZULDU** (sahip karari 28 Eyl: kitap PR'larinda ZAP beklenmez, deterministik kontroller yesilse `--admin` merge; ZAP master'da kosmaya devam eder) |
| 4 | Hakeme giden bicim farklari | ~4-5 dk + hakem gurultusu | `norm()` genisletildi (halka, ust simge, ust cizgi, kok cizgisi, tek atom parantezi, tablo ayraci) | **COZULDU**: 249 -> 208 fark (%16); tek tarafli esasli hata gizlenmedi (gercek veriyle dogrulandi) |
| 5 | Kitap basina 4 gecici script (talimat2/karsilastir/hakem/duzeltme) yeniden yazimi | ~5 dk + kirilganlik | `backend/scripts/kitap/metin_iki_okuma.py` (kitap parametreli, 27 birim testi) | **COZULDU** |
| 6 | Faz 0 yerlesim kalibrasyonu yinelemeleri | ~10-15 dk (ayni seri); yeni seride ~1-1,5 sa | ayni seri: profil sabitlerini komsu profilden import (acl25s1 <- acl25pl, acl24am <- acl24mg). Yeni seri: `kitap_hat/kesif.py` profilsiz olcum + profil taslagi; `tarama` elenen glife NEDEN yazar; `kirp` kenar ihlalinde murekkep x araligini verir; iki gecisli test siniri `kitap_hat/bas_listesi.py` | **COZULDU** (28 Eyl; bolum 6) -- sure ilk yeni-seri kitabinda olculecek |
| 7 | Kitap basina 8 script + 3 migration + 2 test = ~4.8k satir kopya kod (14 harness kopyasi var) | ~10 dk uretim + CI/mypy/pre-push buyumesi | ortak profil gudumlu hat `scripts/kitap/kitap_hat/` (PR #349) | **COZULDU** |
| 8 | Cihaz koprusu 60 sn siniri -> her uzun adim Start-Process + log yoklama | ~1-2 dk x ~10 adim | (arac siniri) | KABUL |
| 9 | Kirpim kesigi gec yakalaniyor: yanlis SAYFA_ALTI / serit ortusmesi soruyu kesiyor, ancak metin okumasinda fark ediliyor (acl25s1: 10 soru yeniden kirpildi + okundu, ~25 dk; T042_06 D/E) | ~20-30 dk + veri hatasi riski (acl24mg'de 4 kesik soru DB'ye girmisti) | `kirp.py` dort kenar olcumu + KESIK kapisi (exit 1), `kutu.py` alt-sinir-alti taramasi, `metin hazirla` kapi zinciri | **COZULDU** (28 Eyl; bolum 7) |

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

Karar (28 Eyl 2026): kitap PR'larinda ZAP beklenmez (madde 3 COZULDU).
Olcum: #350 48 dk, #351 44 dk, #352 2 sa 23 dk (yeni seri, iki gecisli
test siniri) -- onceki merge'den merge'e; ayni seride ~5-6 kat kisalma.

## 6. Yeni seri akisi (28 Eyl 2026; madde 6)

Yeni bir yayin serisinin ilk kitabinda kalibrasyon her olcum icin elle yazilan
gecici betiklerle (`_a21_gecici/m3_*`, `p4_*`, `a_olc_glif`, `numara_ara`,
`alt_tara`, `p5_dis` ... 60+ dosya, git disi) yapiliyordu; `tarama` elenen
glifin nedenini soylemiyor, `kutu` kenar ihlalinde olculen siniri vermiyordu.

1. `python -m scripts.kitap.kitap_hat.kesif --klasor "<glob>" [--ornek 60] [--goz 3]`
   -- profil ISTEMEZ. Olcer: glif x histogrami -> SIMGE_X; dort numara
   maskesi (`ortak.NUMARA_MASKELERI`: kirmizi / mavi / camgobegi / siyah)
   isabeti -> numara_maskesi; blob dy/dx/h -> PENCERE, NUMARA_H, NUMARA_DX;
   x projeksiyonu + orta ayrac -> SUTUNLAR; yatay cizgiler / duz metin serit /
   en alt murekkep -> UST_BANT, SAYFA_ALTI, anahtar_bolgesi on ayari; sayfa
   ozeti -> TEST_SAYFALARI adayi. Konsola profil TASLAGI basar (`# GOZ:`
   isaretli satirlar gozle kesinlesir), `_kesif_<ad>.json/.txt`, `--goz` ile
   montaj PNG. Dogrulama (60 sayfa): acl25pl SIMGE_X 25/356/43/374 (profil
   27/357/42/372), maske camgobegi, ayrac 362/379; acl24mg 28/353/45/376
   (27/353/43/369), maske mavi, serit cizgileri 890/905, serit x0 376/392;
   acl23ag 16/350/35/365 (13/347/32/363), maske kirmizi, ayrac 362/379.
2. Taslak -> `profiller/<kod>.py` (ayni seri varsa komsu profilden import).
3. `tarama --profil K`: elenen her glif `neden` tasir (serit_ustu, sutun_disi
   gx=.., blob_yok maske_px=.. bloblar_hw=.., dx_disi dx=.. dy=.., gecerli_red)
   ve kapi ihlalinde ilgili testlerin glifleri nedenleriyle basilir -> hangi
   sabitin oynayacagi belli.
4. 'Ilaci' duzeni (sayfa basina serit, numara sayfalar boyunca): `bas_listesi
   --profil K gecis1 | yaz | grupla` (eski p4_gecis1 / p4_bas_yaz).
5. `kutu` -> `kirp` (kenar ihlalinde `murekkep_x` = gercek murekkep araligi ->
   SUTUNLAR tek adimda) -> `metin hazirla`.
Sure hedefi: ilk yeni-seri kitabinda Faz 0 <= 30 dk (zaman damgalariyla olculecek).

## 7. Kirpim kesik kapisi (28 Eyl 2026; madde 9)

* `kirp.py kenar_olc`: beyazlatilmis kutunun dort kenarindaki 2 px seritte koyu
  piksel (ust/alt seridinde koselerden 6 px iceri: sayfa susu sayilmaz).
  sol/sag > 3 -> `kenar`; ust/alt > 3 -> `kesik`. Ikisinden biri varsa exit 1;
  `ortme_olcumu.json`'a `kesik`, `kesik_kapisi_ihlali`. `metin hazirla` bu
  sayilara bakar (`kirpim_kapisi`), e2e test her profilde 0 ister.
* `kutu.py alt_sinir_alti`: sutun alt sinirinin altinda, serit sutunla
  ortusmuyorsa serit hizasi dahil, ilk tam genislik satira kadar koyu satir ->
  kapi (kirpimdan da once).
* Gercek veri (6 kitap): acl23ag 0 / acl23kc 0 / acl25s1 0 / acl25s2 0;
  acl25pl 7 'ust' ihlali = konu sayfasi ayrac cizgisi altindaki logo kuyrugu
  (AYRAC_PAY 7 ile 0; kirpim ustu 5 px asagi kaydi, metin degismedi);
  **acl24mg 4 GERCEK kesik** (T012_03, T048_04, T053_03 sik satiri yarim;
  T081_02 siklar hic yok, `[okunamadi]`, beta disi). SAYFA_ALTI 885 -> 898,
  yeniden kirpim, gozle okuma, 0089 duzeltme migration'i (yeni satir + beta;
  496/499). Yani kapi, DB'ye girmis bir veri hatasini buldu.
* Mutasyon kaniti (acl25s1, profil gecici degistirilip geri alindi):
  SAYFA_ALTI 922 -> 878 (ilk hatali deger) -> `kutu` 9 sayfada "alt sinir
  altinda murekkep" (s32/39/40/76/77/80/142/143/169 L; 7-126 px), exit 1.
  SERIT_ORTUSME_EN_AZ 60 -> 19 (serit s80 sol sutuna 20 px giriyor) -> `kutu`
  gecer (serit satirlari atlanir), `kirp` KESIK 1: ACL25S1-T042_06 alt 57 px,
  exit 1 -- metin okumasinda bulunan D/E kesigi artik kirpimda duruyor.
  Dogru profille 6 kitapta kenar 0 / kesik 0 (yanlis alarm yok).

## 8. Ikinci tur (29 Eyl 2026): 155 kitap oncesi olcum ve cozumler

Kaynak: APO19MT / APO19FZ oturum zaman damgalari, cProfile (APO19FZ, 448 sayfa),
`_a21_gecici/{zaman_olc,hakem_analiz,ab_tarihce,tek_okuma_sim2,regres_hat,esdeger_kirp}.py`.

### 8.1 APO19FZ (yeni seri, 2180 soru) uctan uca: ~3 sa 36 dk is + 2 CI turu

| faz | dk | not |
|---|---|---|
| kesif + profil + serit + capa | ~30 | serit okuyucu 8 ajan ~7 dk |
| **kutu + kirp yinelemeleri** | **~60** | 5 tam kosu; kutu ~4 dk + kirp ~5-7 dk / kosu |
| metin hazirla (x2) | ~6 | |
| **metin okuma (68 ajan, 20 esz.)** | **~65** | 4 dalga 14/19/15/13 dk; dalga ici en yavas ajan belirler |
| **hakem (20 ajan)** | **~21** | 455 fark |
| faz68 + beta sorunu | ~12 | |
| commit (pre-commit pytest 7 dk) + 2 CI turu | ~75 | 2. tur: CI mypy numpy tip hatasi |

### 8.2 Olculen dar bogazlar ve cozum

| # | dar bogaz | kanit | cozum | sonuc (olculdu) |
|---|---|---|---|---|
| 10 | kutu/kirp/tarama/metin-hazirla CPU suresi | cProfile: kutu 174 sn'nin 153'u, kirp 439 sn'nin 354'u `beyaz_sayfa`; okuyucu renk siniflamasi TUM sayfada, sayfa basina 2 kez; tarama her sayfayi 2 kez yukluyor; PNG kodlama tek cekirdek | renk yalniz disk penceresinde (piksel basina islem, cikti ayni); `ortak.paralel` surec havuzu (sayfa basina is, sirali birlestirme); tarama tek yukleme; PNG `compress_level=1` (kayipsiz) | tarama 108 -> ~12 sn, kutu 174 -> ~12 sn, kirp 439 -> 16 sn, metin hazirla 94 -> 22 sn. **Esdegerlik:** 14 kitap / 3590 sayfa `beyaz_sayfa` fark 0; 14 kitapta `kutulari_uret` == kayitli JSON; tarama == sirali HEAD; kirpim + okuma PNG'leri piksel piksel ayni (APO19FZ 2180, APO19MT 1382) |
| 11 | Anahtar ikinci okumasi (B) bilgi getirmiyor | 16 kitap / 15.154 hucre: A != B **0**; glif tek-hata analizi: 8 kitapta her hucre icin tek yanlis harf glif LOO'da yakalanir, yakalanmayabilecek hucreler zaten `uyumsuz` -> goz teyidi | **Tek okuma** (sahip karari): `okuma_b` None; kapi: glif LOO + `glif_etiket.png` (etiket basina 24 ornek glif; sistematik harf takasina karsi) gozle `ham --etiket-goz`; glif disi testler goz_c | serit okuyucu 8 -> 4 ajan; kalite kaniti yukarida |
| 12 | Hakeme giden sekil-etiketi farklari | APO19FZ 455 farkin 327'si sekil etiketi (221 'esasli yok'); APO19MT 247'nin 80'i | profil `SEKIL_SATIRI = True`: MEKANIK kural (rakam iceren her etiket, tek `\u015eekil: a; b` satiri) + `norm()` bu satiri sirasiz kume olarak karsilastirir | ilk kitapta olculecek; beklenen hakem yuku ~%50 az |
| 13 | CI mypy yerelde gorunmuyor -> ikinci CI turu | #364: yerel pre-commit mypy gecti, CI (py3.11, mypy 1.11.2, numpy 2.x stub) 4 hata | `gonder2.ps1` on kosulu: `C:\Users\husey\.venv_mypy_ci` (py3.11 + mypy 1.11.2, CI argumanlari) listedeki .py'lerde; hata varsa commit yok | pozitif kontrol: eski APO19FZ profilinde CI'nin 4 hatasi birebir yerelde cikti |
| 14 | Metin okuma dalga bariyeri (arac siniri 20 esz. ajan, sonuc ancak tum parti bitince donuyor) | 4 dalga, dalga basina en yavas ajan (19 dk'ya kadar) | kitap icinde cozum yok (arac); Workflow araci boru hatti (biten ajanin yerine hemen yenisi) + sonraki kitabin kalibrasyonunu okuma sirasinda yapmak ~20-30 dk/kitap kazandirir -- **sahip onayi gerekir** (cok ajanli orkestrasyon) | ACIK |
| 15 | pre-commit tam pytest (~7 dk / commit) | b15 gonder logu: 320 test 437 sn | kitap PR'i basina tek commit hedefi (on kosullar commit oncesi); kancaya dokunulmadi | KABUL |

Beklenen yeni-seri kitap is suresi: ~3,6 sa -> ~2,3 sa (kutu/kirp yinelemeleri
60 -> ~8 dk, serit 8 -> 4 ajan, hakem ~yari, ikinci CI turu yok). Ayni seride
(profil hazir) ~1,5 sa. Madde 14 onaylanirsa kitaplar arasi ortusmeyle ~1 sa'e iner.
