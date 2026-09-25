# 345 2025 Start Matematik -- uretim yontemi ve olcumler

Durum: Faz 1 (sayfa turu, capa taramasi, cevap anahtari, test -> unite)
ve Faz 2 (unite agaci, 0057) TAMAM. Sonraki fazlar `STM_345_KESIF_VE_PLAN.md` bolum 2'de.

## 0. Kaynak ve tavani

FERNUS okuyucusunun 1920x1080 ekran goruntuleri, 320 sayfa
(`sayfa_0001..0320`, bosluk yok; 3 `_enhanced_*` dosyasi 1024x576,
kullanilmaz). Kart `(589, 43) - (1331, 1020)` = 742x977. Basili sayfa =
dosya - 1 (icindekiler 'Sayfa (3)' = dosya 4 ayraci; dosya 11 altinda
basili '10'); `source_page` icin hangisinin yazilacagi Faz 6'da.

| kalem | deger | kanal |
|---|---|---|
| unite | 16 (icindekiler dosya 3, 'KITAP BITIRME PLANI') | goz |
| test sayfasi ('SINAVA GECIS') | 90 | baslik izgara rengi (`stm345_tarama.py`) |
| test | 45, hepsi tam 2 ardisik sayfa | cevap seridi numaralandirmasi + bant |
| soru (kapsam) | 371 | cevap seridi (x2) |
| kapsam disi | konu sayfalarindaki acik uclu alistirmalar ve 'Isindirma Kosesi' (anahtar basili degil; sahip karari 25 Eyl) | - |

## 1. Cevap anahtari -- sayfa alti serit, iki okuma + glif kanali

Anahtar her test sayfasinin altinda, sutun basina ayri basili satir (kart
y 905-930; '1.C 2.B 3.E'). `345_2025_start_matematik_cevap_anahtari.json`,
ham okumalar `345_2025_start_matematik_ham_okumalar.json`; anahtar
`stm345_anahtar.py` ile hamdan yeniden turer (testle kilitli).

| | okuma A | okuma B |
|---|---|---|
| olcek / montaj | 5x, 12 satir | 7x, 9 satir |
| sira | sayfa sirasinda | TERS |
| girdi sayisi okuyucuya soylendi mi | hayir | hayir |

* A == B: **180/180** sutun, **371/371** girdi, harf ve numara farki **0**.
* B okuyucusu 12 girdide rakamda (6 / 8) tereddut isaretledi; harf
  tereddudu yok. 12'sinde de numara surekliligi rakami tek anlamli yapar
  (A kesin okudu).
* Ucuncu kanal (piksel): harf glifi 9x8 gri pencere, en-yakin-komsu,
  birini-disarida-birak. 359 glif; LOO uyumu **358/359**. Tek uyumsuz
  (33L 3.C, glif E dedi) ve pikselin girdi sayisini tutturamadigi 6 sutun
  (34L iki girdi bitisik basili; 139L/141L/173L/197L/215L '2' rakaminin
  soluk kenari ayri girdi sayildi) 10x en-yakin-komsu buyutmeyle gozle
  incelendi: hepsinde okuma dogru (`goz_kararlari`).
* Kanal dagilimi: iki okuma + piksel 358, iki okuma + goz 13.
* Harf dagilimi A 71, B 82, C 74, D 78, E 66.

Kapilar (hepsi sert):

| kapi | sonuc |
|---|---|
| sutun girdi sayisi == basili soru numarasi sayisi (camgobegi numara kanali) | 180/180 |
| numara ya oncekinin +1'i ya da 1 | 0 kopma, 45 test |
| her test iki ardisik sayfa, tek unite | 45/45 |
| bant 'SINAVA GECIS n' == unite ici test sirasi | 90/90 sayfa |
| bant unite adi == icindekiler araligindaki unite | 90/90 sayfa |

Piksel girdi sayimi (bosluk >= 4 px, murekkep < 225) 174/180 sutunda
okumayla esit; esik secimi bosluk dagilimindaki vadiden (3 px) olculdu.

### 1a. Okuyucu simgesi ne DEGILDIR

Simge (mor buyutec) sayimi 372, numara 371. Simge soru BASI degildir:
s266 sag sutunda simge sorunun ortasinda ('Buna gore...' satirinin
solunda) duruyor; s83 sagda sekil icinde bir yanlis simge, s137 solda bir
soruda simge yok. Kirpim capasi Faz 3'te basili numaradan alinir, simge
yalniz yardimci kanal.

Unite -> test (dosya no):

| unite | ad | test | sayfalar |
|---|---|---|---|
| 01 | Toplama ve Cikarma Islemi | 3 | 11-16 |
| 02 | Carpma ve Bolme Islemi | 2 | 33-36 |
| 03 | Islem Onceligi | 2 | 47-50 |
| 04 | Harfli Ifadeler | 2 | 65-68 |
| 05 | Basit Denklem Cozumu | 4 | 81-88 |
| 06 | Rasyonel Sayilar | 4 | 113-120 |
| 07 | Ondalik Gosterim | 3 | 137-142 |
| 08 | Sayi Kumeleri | 2 | 157-160 |
| 09 | Oran ve Oranti | 2 | 171-174 |
| 10 | Rasyonel Denklemlerin Cozumu | 2 | 185-188 |
| 11 | Iki Bilinmeyenli Denklemler | 2 | 197-200 |
| 12 | Basit Esitsizlikler | 3 | 213-218 |
| 13 | Mutlak Deger | 3 | 233-238 |
| 14 | Uslu Ifadeler | 4 | 261-268 |
| 15 | Koklu Ifadeler | 4 | 291-298 |
| 16 | Carpanlara Ayirma | 3 | 315-320 |

## 2. Unite agaci (0057)

16 unite dugumu MAT kokunun altinda (kok+1), kodlar `MAT-345S25-U01..U16`,
adlar Turkce (kaynakta `\u` kacisli), `subject_area = MATEMATIK`.
`345_2025_start_matematik_konu_haritasi.json` `stm345_harita.py` ile ham
okumalardan turer; migration dosyasi o JSON'dan URETILDI.

| kaynak / kapi | sonuc |
|---|---|
| unite adi | ayrac sayfalari (dosya 4, 18, 38, 52, 70, 90, 122, 144, 162, 176, 190, 202, 220, 240, 270, 300), gozle; kesik gorunen U10/U12/U16 tam kirpimla |
| ayrac adi ASCII-buyuk katlamasi == icindekiler (dosya 3) | 16/16 |
| ayrac dosyasi == icindekiler basili sayfasi + 1 | 16/16 |
| test bandindaki unite adi == unite | 90/90 sayfa |

Kitap uniteyi alt konuya bolmuyor: test bandi yalniz unite adini basar
('0'dan Basla' alt basliklari konu sayfalarinda, kapsam disi). Sorular
unite dugumune baglanir (`konu_eslesme_duzeyi` = 'unite').

Yerel DB: upgrade 16 dugum (hepsi level 2, tek ebeveyn = MAT koku, aktif);
downgrade 16 dugum + gunluk silindi; tekrar upgrade ayni. `alembic heads`
tek bas: 0057_stm345_agac.

## Testler

`backend/tests/e2e/test_stm345_veri.py` (25; Faz 2 ile +8: harita hamdan
turer, migration == harita, zincir, ASCII, ayrac adi / sayfasi mutasyonu): hamdan birebir turetme,
A/B farki / eksik sutun / bicim disi girdi mutasyonlari, sureklilik, bant,
kapsam, kanal durustlugu, ASCII. Mutasyonla dogrulandi: cevap harfi,
bant adi, test sayfasi ve kaynak alani bozulunca ilgili test kirmizi;
temiz dosyada 0 kirmizi.
