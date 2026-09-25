# 345 2025 AYT Turk Edebiyati Soru Bankasi -- uretim yontemi ve olcumler

Kaynak: `veriseti/zkitap/screenshots/345 2025 Ayt Turk Edebiyati Soru Bankasi/`
(348 PNG; git disinda). Veri dosyalari
`veriseti/zkitap/cikti/345_2025_ayt_edebiyat_*.json`. Faz 0 kesif fisi:
`EDB_345_AYT_KESIF.md`. Hat, 345 2025 AYT Kimya hattinin
(`KIM_345_AYT_YONTEM.md`) edebiyata uyarlanmis kopyasidir; farklar asagida.

| arac | is |
|---|---|
| `scripts/kitap/edb345ayt_tarama.py` | capa taramasi (simge, basili numara, ara cizgi), dosya 1-328 |
| `scripts/kitap/edb345ayt_kutu.py` | kirpim kutulari + ortak metin kutulari (kirmizi baslik) |
| `scripts/kitap/edb345ayt_kirp.py` | soru + ortak metin gorselleri, ortme / kenar olcumu |
| `scripts/kitap/edb345ayt_metin_harness.py` | transkripsiyon gruplari + kapilar (KAPI1-5) |
| `scripts/kitap/edb345ayt_ithal.py` | PASIF ithal |
| `alembic 0053_edb345ayt_agac` | konu agaci (EDB-345A25: 10 unite + 46 konu) |

Hicbir soru cozulmedi; hicbir cevap uretilmedi.

## 0. Kaynak ve tavani

Tek yakalama (baska baski yok -> ortulen metin icin kurtarma kanali yok).
Dosya 329-348, dosya 328'in piksel-ozdes kopyasi (okuyucu takili); icerik
1-328. Sayfa karti `(589, 43) - (1331, 1020)` = 742x977. Basili sayfa
numarasi = dosya numarasi.

| kalem | deger | kanal |
|---|---|---|
| icerik sayfasi | 328 | dosya sayimi + sha256 |
| on sayfalar | 1-4 (kapak, kunye, icindekiler 3-4) | goz |
| unite ayraci | 10 (5, 39, 71, 113, 147, 191, 221, 255, 275, 299) | bant okumasi + goz |
| soru sayfasi | 306 (6-320) | bant okumasi |
| cevap anahtari | 321-328 | goz |
| test | 148 (138 x 2 sayfa, 10 x 3 sayfa) | bant + anahtar |
| soru | 1384 | anahtar (x2) + transkripsiyon |

Kaynak cozunurlugu dusuk: 742 px genislikte `rn`~`m`, `t`~`l`, `f`~`l`,
`ll`~`tl` pikselde birlesiyor (bolum 4).

## 1. Cevap anahtari -- kitap sonu, iki okuma + glif kanali

Sayfa alti cevap seridi YOK; anahtar kitap sonunda (dosya 321-328), konu
basina satirlar. `345_2025_ayt_edebiyat_cevap_anahtari.json`; ham okumalar
`345_2025_ayt_edebiyat_ham_okumalar.json`.

| | okuma A | okuma B |
|---|---|---|
| olcek / montaj | 3x, sayfa basina 3 yatay dilim | 2x, tam sayfa |
| sira | sayfa sirasinda | TERS |
| girdi sayisi okuyucuya soylendi mi | hayir | hayir |

* A == B: 148/148 test satiri (unite, konu, tur, sira) ayni; 1384/1384
  girdi numarasi ayni; harf farki **1** (s323 Tanzimat Siiri OSYM 1 soru 5:
  A 'B?', B 'D').
* Ucuncu kanal: harf glifi (girdinin sag 9x16 pikseli) en-yakin-komsu,
  birini-disarida-birak. 1384 glifin tamami segmente edildi; iki okumanin
  ayni ve tereddutsuz okudugu 1325 glifte LOO **1325/1325**.
* Uyusmaz girdi: NN 5/5 'B', 12x NEAREST goz 'B' -> **B**.
* Okuyuculardan birinin '?' koydugu 59 girdi (uyusmaz dahil): 59'unda NN
  cogunlugu okunan harfle ayni; 30 satirlik 5x montajla gozle de bakildi.

| kanal | soru |
|---|---|
| `iki_okuma+piksel` | 1325 |
| `iki_okuma(biri_tereddutlu)+piksel+goz` | 58 |
| `iki_okuma(uyusmaz)+piksel+goz` | 1 |

Harf dagilimi A 265, B 284, C 307, D 273, E 255.

### 1a. Soru -> sayfa / sutun konumu

Anahtar yalniz (test, soru no, harf) verir. Konum iki bagimsiz olcumden:

1. **Sayfa ust bandi** (her sayfa, 316 bant, iki okuyucu; `bant_okumasi`):
   test turu logosu (K/O/R/M/G) + tur ici sira. Ardisik ayni (tur, sira)
   kosulari = test sayfalari. 148 kosunun 148'i anahtarin test sirasiyla
   (tur + sira) birebir.
2. **Sutun basina basili numara sayisi** (piksel; genislik <= 12 px dar
   numaralar): testin sayfalarinda L sonra R sutunu, yukaridan asagi.
   148 testin 147'sinde toplam == anahtardaki soru sayisi; 1 sutunda (s293
   sol) numara okuyucu diski altinda -> simge sayisi.

## 2. Konu agaci -- kitabin kendi icindekiler sayfasi (0053)

10 unite + 46 konu, kitabin icindekiler sayfalarindan (dosya 3-4). Adlar
Turkce (kaynakta `\u` kacisli), kodlar `EDB-345A25-Unn(-kk)`.

| test turu | test | soru | dugum |
|---|---|---|---|
| Kazanim Odakli (K) | 46 | 496 | konu |
| OSYM Tadinda (O) | 58 | 530 | konu |
| Orijinal (R) | 8 | 34 | unite |
| Karma (M) | 26 | 247 | unite |
| Genel Bakis (G) | 10 | 77 | unite 10 |

Dogrulama: 46 konunun 46'sinda icindekiler baslangic sayfasi == konunun
ilk testinin ilk sayfasi. K ve O bantlari konu adini basar (bir istisna:
'BAGIMSIZ SAIRLER - MANZUM HIKAYE VE MENSUR SIIR' kisaltmasi, `bant_esleme`);
M / R / G bantlari unite adini serbest kisaltmayla basar -> unite dugumu.

Migration round-trip (upgrade -> downgrade -> upgrade) yerelde: 56 dugum
silindi / ayni id'lerle yeniden eklendi.

## 3. Kirpim kutulari -- capa kanali, ortak metin

`345_2025_ayt_edebiyat_kirpim_kutulari.json`. KIM kurali aynen (capa: dar
numara sayisi == sutunun soru sayisi ise numara, degilse simge / birlesik).

| olcu | deger |
|---|---|
| sutun kanali | numara 611, simge 1 |
| kutusuz soru | 0 |
| ust kurali | logo 61, logo_yakin_secenek 1, tavan_asimi 1 |
| numara diski ortulu kutu | 18 (hepsinde numara yine okundu) |
| yukseklik | min 104, medyan 288, max 786 px |
| kesim metne degen | 2 (T043_02, T145_04: OSYM KOSESI logosu; gozle tam) |

* SAYFA_ALTI 896 korundu: sayfa alti seridi olmasa da notr (siyah) metin
  612 sutunun hepsinde y <= 879'da bitiyor; alttaki yapboz / kose susu
  renkli.
* **Ortak metin**: kirmizi (~(190,43,48)) cerceveli baslik, >= 150 px yatay
  kirmizi kosu cifti (`ortak_basliklari`). **11** baslik, hepsi sutun
  basinda, ilk soru kutusunun ustunde; soru kutusu ICINDE baslik 0. Iki
  bagimsiz kanalla ayni 11 sutun: (a) kirmizi cerceve, (b) ilk kutusu
  y > 175'te baslayan sutunlar (tam olarak bu 11). Ortak kutu = baslik ustu
  - 3 .. ilk soru kutusu ustu - 1.

## 4. Transkripsiyon

Kirpimlar 2x Lanczos; 28 grup (test sinirina hizali, ~50 soru), ayri
okuyucular; talimat `VeraFilm/e_metin_talimat.md` ('kitap ne yaziyorsa o':
eski yazim, sapkali harfler, yazim hatalari aynen; soru cozme yok; anahtar
gosterilmedi). Ek kurallar gruplar ilerledikce eklendi:

* grup 1-2 sonrasi: ortak metin ayri okunur; kutu-ok semasi; alti cizili
  baslik; numara + ek sirasi; tirnak bicimi.
* grup 3-8 sonrasi (cozunurluk): `rn`~`m`, `t`~`l` gibi birlesmelerde
  yalniz biri gercek Turkce kelime veriyorsa o yazilir, not yok; iki aday da
  mumkunse (ozel ad, eser adi) piksel okumasi + `kaynak_kusuru`na iki aday.
  Grup 03 bu kuraldan once okundu: 3 soruda 'omegi' -> 'ornegi'
  (`duzeltme.json`).
* hizasiz iki sutunlu tablo eslestirilmez, iki liste yazilir.

11 ortak metin ayri okundu (`VeraFilm/e_ortak_talimat.md`): baslik aynen,
kapsam (ilk-son soru no), metin.

Kapilar (`edb345ayt_metin_harness.py kapi`, okuyucuya soylenmeyen yapidan):
KAPI1 her kirpim bir kez; KAPI2 basili no == test ici sira (1384/1384,
numarasi okunamayan yok); KAPI3 bes sik dolu; KAPI4 toplam 1384; KAPI5
ortak metin 11, kapsam basi == kutudaki ilk soru, kapsam testte, metin dolu.
Bilerek bozulan kopyada (numara 99, bos sik, kapsam kaymasi, kapsam 6-30,
eksik kayit) her kapi duruyor.

| olcu | deger |
|---|---|
| sekil_var | 96 |
| gorsel sik | 1 (T115_01) |
| kaynak_kusuru | 59 |
| cikmis etiketi | 61 (AYT 51, 'OSYM - yil' 10) |
| duzeltme okumasi | 5 |

Basili kitap hatasi olarak kalan: T059_06 A ve C sikki ayni basili (gozle;
`sik_tekrar` bayragi).

### 4a. Ikinci okuma -- orneklemle karar

On kayit (olcumden ONCE, `345_2025_ayt_edebiyat_ikinci_okuma.json`): 28
grubun her birinden 8 soru (random.Random(20260925)) = 224; ilk okumayi
gormeyen 7 okuyucu x 32. Karsilastirma bicim normalize (bosluk, satir
sonu, tire/tirnak turu, sapka); her fark kirpima bakilarak gozle hukum.

| sonuc | adet |
|---|---|
| ayni | 210 |
| yalniz noktalama | 2 |
| farkli | 12 |
| - ikinci okuma hatasi | 4 (hos/bos, alti cizgi kapsami, sayfalarini/sayilarini, Harname) |
| - esdeger yazim | 5 |
| - belgelenmis belirsizlik | 1 (T142_04 'Mermerleri', ilk okumada not) |
| - ilk okuma hatasi | 2 (T047_02 'yapitin'->'yapitinin', T085_01 'konularini'->'konulari') |

Iki ilk okuma hatasi yalniz Turkce ek farki, anlam ayni -> esasli degil;
esasli hata **0/224**, CP95 ust sinir **%1.63** <= %3 -> TAM IKINCI OKUMA
YOK. Duyarlilik: ek hatalari esasli sayilsaydi 2/224, ust sinir %3.19 (> %3)
olurdu. Iki hata ithal oncesi duzeltildi (`duzeltme.json`).

## 5. Ortme

`345_2025_ayt_edebiyat_ortme_olcumu.json`: diskin halkasinda kitap
murekkebi olan **94** soru `okuyucu_diski_ortme` bayragi tasir (kurtarma
kanali yok). Kenar kapisi 8 kutu: T068_11 dikey 'CIKMIS SORU' yazisi,
digerleri Genel Bakis sag sutununun turuncu kose susu; metin kesilmiyor
(gozle).

## 6. Mukerrer adaylari -- isaretlendi, silinmedi

DB EDEBIYAT (1621 satir) x bu kitap; govde (ortak metinli soruda ortak
metin + govde) kelime kumesi Jaccard >= 0.75: 20 aday; GUCLU (>= 3 sik
birebir) **6** (BS 2024 AYT Edebiyat 4, OSYM 2025 AYT 2). Cevap harfi farkli
2 GUCLU aday (T029_04, T031_08) OSYM 2025 AYT cikmislari: kitap sik
sirasini degistirmis, dogru sikkin METNI iki tarafta ayni -> celiski yok.

## 7. Alanlar ve kaynaklari

KIM ile ayni; farklar: `cevap_kaynagi = kitap_sonu_cevap_anahtari`,
`ortak_metin` / `ortak_metin_kapsami` (+ `ortak_metin_govdede` bayragi,
23 soru: soru metni = ortak metin + bos satir + govde), `sinav` 'OSYM'
(yalniz 'OSYM - yil' etiketli 10 soru; oturum basili degil, tahmin yok).
`subject_area = EDEBIYAT`, `exam_type = AYT`, `grade_level = 12`.

## 8. Bilinen borc

* Cozumler kitapta soru sayfasinda yok; `explanation` bos.
* Ortak metinli sorularin gorseli yalniz soru kirpimi (parca gorselde yok).
* Cozunurluk: iki adayli ozel ad / eser adi `kaynak_kusuru` notunda;
  tam ikinci okuma yapilmadi (orneklem karari).
* Ithal PASIF; aktiflestirme ayri (sahip) karari.
