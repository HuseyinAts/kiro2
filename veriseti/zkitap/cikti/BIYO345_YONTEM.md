# 345 2025 AYT Biyoloji Soru Bankasi -- cikarim yontemi ve olcumler

Kaynak klasor:
`veriseti/zkitap/screenshots/345 2025 Ayt Biyoloji Soru Bankasi/temiz .../`
374 PNG, 1504x1936, `sayfa_0003` - `sayfa_0376`.
Cikti: `veriseti/zkitap/cikti/biyo345_sorular.json` (1317 soru).

Bu dosya, sayilarin NEREDEN geldigini yazar. Iddia edilen her sey
olculmustur; olculemeyen her sey "olculmedi" diye yazilmistir.

## 0. Kaynak bicimi

Kitap bir zkitap goruntuleyici EKRAN GORUNTUSU dizisidir. PDF yok, metin
katmani yok. Sayfalar 1920x1080 ekran goruntusunden (584,46,1336,1014)
kirpilip 2x LANCZOS ile 1504x1936'ya buyutulmus. Yani 2x buyutme SENTETIK;
gercek bilgi 752x968'de. Buna ragmen okuma her yerde 1504x1936 uzerinden
yapildi: buyutme yeni bilgi eklemese de gorme modelinin OCR dogrulugunu
olculebilir sekilde artiriyor.

## 1. Sayfa tipi: anahtar seridi olan sayfa = soru sayfasi

Ilk denemede sayfa tipini BUYTEC IKONU sayarak ayirmaya calistim. YANLIS
CIKTI: ikon dedektoru (RGB 69,39,160, alan 129) hem soru buyteclerini hem
de konu ozet kutularindaki madde isaretlerini yakaliyor. s0011 "ikonlu"
gorundu ama sayfa bastan sona konu anlatimi.

Dogru olcut anahtarin kendi imzasi oldu:

- arama penceresi y 1780-1816 (gercek anahtar 344 sayfada y 1792-1803),
- 30 px'ten uzun yatay koslar atilir (kutu kenari/golgesi),
- satir mureekkebi 4..200 arasinda (glif seyrekligi),
- kos yuksekligi >= 5 satir,
- kos, y 1792-1804 cekirdek bandiyla KESISMELI,
- koyuluk esigi 200 (150 SOLUK basili anahtarlari eliyordu -- bkz. asagisi).

Sonuc: **374 sayfanin 317'sinde anahtar var, 57'sinde yok.**
Anahtarsiz 57 sayfanin TAMAMI kucuk resim izgarasiyla tek tek goruldu:
icindekiler, bolum ayraci ve konu anlatimi sayfalari. Soru sayfasi yok.
s0003 (kunye/telif) yanlis pozitifti, elle cikarildi -> **316 sayfa**,
sonrasinda sutun bazinda 600 sutun.

### Soluk baskili anahtarlar (nasil yakalandi)

Ilk tespit esigi (mean<150) dort sayfada anahtari kacirdi. Bunu ben degil
NUMARA SUREKLILIGI DENETIMI buldu: birlestirilmis anahtarda tam dort
kirilma cikti (s0054->s0056, s0169->s0171, s0262->s0264, s0286->s0288) ve
dordunde de aradaki sayfa "anahtarsiz" sayilmisti. Ham kirpima bakinca
dordunde de anahtar vardi, sadece SOLUK basilmisti. Esik 200'e cikarilinca
9 sayfa daha geldi (0051, 0055, 0102, 0132, 0170, 0214, 0263, 0287, 0366);
bunlarin 8'i gercek, 0051 mavi bant yanlis pozitifi.

## 2. F3 -- cevap anahtari

52 montaj, her biri 6 sayfa, sutun basina ayri kirpim, **4x olcek**
(glif yuksekligi 12 -> 48 px), 1.06 MP (API ~1.15 MP butcesi icinde).

Onceki surum 2x idi ve s0010 sag'da "4.E" hanesini "1.E" diye okudum.
Bu, kampanyada dusuk cozunurlukten kaynaklanan UCUNCU hane karismasiydi;
kural artik acik: **hane okumasi 4x altinda yapilmaz.**

- **Iki bagimsiz okuma** (farkli ifadelerle yazilmis iki ayri gorev),
  beklenen girdi sayisi HIC SOYLENMEDEN (capa bastirma).
- Iki okuma da 307 sayfa / 1303 girdi buldu; **13 uyusmazlik**, hepsi
  B/E ya da C/D karismasi.
- 13 uyusmazlik icin 10x NEAREST hakem kirpimi; **13/13 ikinci okuma
  lehine** cozuldu.
- Soluk anahtarli 8 sayfa 8x kirpimla ayrica okundu -> **1317 girdi**.

### Dogrulama: numara surekliligi (sifir serbestlik dereceli)

1317 girdinin tamami sirayla tarandi: her girdi bir oncekinden +1 ya da
yeni testin basi olarak 1. **0 kirilma.** Okuyuculara beklenen sayilar
verilmediginden bu denetimin serbestlik derecesi yok; uydurulmus tek bir
numara zinciri kirardi.

Turetilen yapi: **193 test**, uzunluk dagilimi 1-12 (yigilma 7-10).
Harf dagilimi A 234 / B 253 / C 242 / D 286 / E 302.

## 3. F4 -- soru metni

Metin **sutun granulerliginde** okundu (kutu bolucuden bagimsiz, boylece
bolucu hatasi metni bozmaz). 600 sutun kirpimi:
sol x 92-740, sag x 737-1422, y 124-1782, 1x olcek (~1.07 MP).

- Sol sutunun sag ust kosesine sag sutunun buyteci giriyordu (x ~753);
  sol pencere 740'ta kesildi.
- Ust sinir 124: test basligi ("KARMA SORULAR 3" vb.) kirpima tam girsin.
- 600 kirpim ham PNG 252 MB idi; 64 renkli palet 76 MB'a indirdi
  (JPEG degil -- glif kenarinda halka birakmasin diye).

Okuma tek turda yapildi (anahtar gibi cift tur degil), cunku metnin
BAGIMSIZ bir dogrulayicisi var:

**Sutun basina soru numarasi dizisi, anahtardaki numaralarla 600 sutunun
599'unda BIREBIR ayni cikti.** Tek sapma s0183 sag: sayfada "67." basili,
anahtar ve test sirasi "2" diyor (onceki sutun 1'de bitiyor). Yuksek
buyutmeyle bakildi: kitapta gercekten 67 yaziyor. **Yayinevi dizgi
hatasi**; konumsal esleme etkilenmiyor, `anahtar_numara_sapmasi` ile
isaretlendi. (Ayni sinif hata jeometri kitabinda da bir kez cikmisti.)

Yapisal denetimler: bos sik 0, cok kisa metin 0, `[OKUNAMADI]` 0,
tekrar eden hash 0, **tekrar eden sik 1** (s0362 sag #6).

### Bilinen sinir: siklari GORSEL olan sorular

Bazi sorularin siklari metin degil grafik/tablo/resimdir. Bu sorularda
a..e alanlari okuyucunun TARIFIDIR, kitabin bastigi metin degil.
s0362 sag #6'da iki tarif ayni cikti ve `sik_tekrar` bayragi aldi.
Bu sorularin dogru gosterimi KIRPIM GORSELIDIR; metin alanlari arama ve
hash icindir. Bu, gizlenen degil ISARETLENEN bir sinirdir.

## 4. F5 -- kirpim kutulari

Tohum: buytec ikonlari (x 60-180 / 700-820, alan 100-170). 600 sutunun
583'unde ikon sayisi soru sayisini tutturdu. Tutmayan 17 sutun gozle
incelendi, iki neden bulundu:

- **Sutun basindaki konu ozet kutusunun kendi ikonu var** (14 vaka):
  fazlalik her seferinde EN USTTE; bastan atiliyor.
- **Bazi "OSYM kosesi" kutularinda buytec yok** (3 vaka): kirmizi cerceve
  bagli bilesen olarak olculuyor ve tohum olarak ekleniyor.

Kutu sinirlari icin ilk kural jeometriden devralindi ("bir sonraki
ikondan onceki SON bos koridor") ama bu kitapta **calismadi**: gorsel
dogrulamada 0320_sag E sikkini, 0339_sag sik satirini, 0197_sag bir
tabloyu ortadan kesti. Sebep olculdu -- sik satirlari arasindaki bosluk
(~8 satir) ile sorular arasindaki bosluk ayirt edilemiyor.

Yeni kural: **bir sonraki ikonun hemen ustundeki EN AZ MUREKKEPLI satir.**
Kutuda fazladan beyazlik kalabilir, ama metin kesilmez.

Ust sinirda ayni yontem: sayfa basligi ile ilk soru arasindaki bosluk
GERCEKTE BOS DEGIL (filigran/dekor, 14-36 px mureekkep), o yuzden
"bos koridor" olcutu calismiyordu; en az mureekkepli satir kullanildi.

### Kesik olcumu (sonuc)

Sinirin hem ustunde hem altinda AYNI sutunda mureekkep varsa o sinir bir
metin satirini kesmis demektir. Olcum, dikey ayrac ve uzun yatay
dekoratif cizgiler elenerek yapildi:

| ortusme esigi | sinir sayisi | oran |
|---|---|---|
| >= 6 px  | 275 | %10.44 |
| >= 20 px |  18 | %0.68 |
| >= 40 px |  11 | %0.42 |
| >= 80 px |   0 | %0.00 |

Bos kutu 0; en kisa kutu 169 px. (Jeometri kitabinda ayni metrik >=6 px
esiginde %9.83 idi.)

## 5. OSYM cikmis sorulari

Kirmizi cerceveli "OSYM kosesi / CIKMIS SORU" kutulari bagli bilesen
olarak sayildi: **71 kutu**. Yil-sinav etiketleri ayri bir turda 3x
kirpimla okundu; **71/71 dolu** (70 AYT 2018-2025, 1 YGS 2015).
Bir kutu (0120_sag) olagandisi uzun oldugu icin sabit "alt kenardan 70 px"
bandi etiketin altina dustu; o kutu ham goruntuden tek tek okundu.

`osym_year` / `osym_format_compliant` YALNIZCA bu 71 soruda doldurulur.
Yayinevinin kendi yazdigi sorulara OSYM damgasi vurulmaz.

## 6. Bagimsiz capraz dogrulama (bedava geldi)

1317 hash canli DB ile karsilastirildi: **2'si zaten vardi**, ikisi de
`source_book = 'OSYM 2025 AYT'`. Ikisi de bu hattin OSYM-kutusu
dedektorunun bagimsiz olarak isaretledigi sorular (s0202 sag #8,
s0375 sol #3).

Yani uc ayri kanal birbirini dogruluyor:
hash formulu + metin cikarimi + OSYM kutusu tespiti.

Bu iki satira DOKUNULMADI (`kaynak_sozlesmesi.ayristir` yabanci satir
korumasi); bu kitaptan **1315 satir** yazildi.

## 7. Konu agaci

16 bolum ayrac sayfasindan okundu (`0021_biyo345_konu_agaci`).
Seviye yalnizca UNITE. Kitapta unite alti konu etiketi YOK; test
basliklari konu degil TEST TURUDUR ve soru duzeyinde tasinir.
Var olmayan bir L3 katmani uydurulmadi.

11. ayracta IKI baslik basili ("Genden Proteine ve Biyoteknoloji" ve
"Canlilar ve Cevre"); sayfa ust bilgisi bolum boyunca neredeyse hep
birincisini diyor, ikiye bolmek icin yeterli sinyal yok. Dugum kitabin
bastigi gibi tek ve iki basligi birden tasiyor.

Bolum basina soru: 78, 82, 78, 95, 89, 93, 66, 68, 72, 71, 100, 96, 85,
99, 98, 47 (toplam 1317; DB'ye giren 1315).

## 8. Yol boyunca bulunan ve duzeltilen hatalar

Bunlar liste olsun diye degil, ayni tuzaga tekrar dusulmesin diye yazili.

1. **Ikon sayisi sayfa tipi icin guvenilir degil** -- ozet kutularindaki
   madde isaretleri ayni renkte. Sayfa tipi anahtarin kendisinden
   belirlendi.
2. **"Son koyu kos" olcutu sayfa numarasini yakaliyordu** -- numara
   ORTALI ve anahtarin ALTINDA. Arama pencereleri merkezi disliyor.
3. **Kutu golgesi anahtar sanildi** (s0013) -- uzun yatay koslar elendi.
4. **Koyuluk esigi 150 soluk anahtarlari eliyordu** -- numara surekliligi
   denetimi yakaladi, esik 200 yapildi.
5. **2x olcekte hane karismasi** ("4" -> "1") -- 4x'e cikarildi.
6. **Kutu siniri onceki sorunun kuyruguna dusuyordu** -- "son bos
   koridor" yerine "en az mureekkepli satir".
7. **OSYM tohumu her sutuna eklenince** dogru ikonu disari itip 40 px'lik
   sahte kutular uretti -- yalniz tohum EKSIKSE ekleniyor.
8. **Eksik tohum "en genis koridor"a konunca** ilk sorunun ustune dustu
   (0299_sag, 61 px'lik sahte kutu) -- once en buyuk tohum araligi
   secilip tohum onun icine konuyor.
9. **`SAYISAL_SIK` regex'i katastrofik geri izlemeye giriyor** --
   `mikro_geo_ithal.py`'den devralinan desen, "2, karbondioksit
   olabilir." gibi RAKAMLA BASLAYIP metinle suren 26 karakterlik bir
   sikta ithali KILITLEDI (olculdu: 294 ms; nokta olmadan 0.001 ms).
   Desen ic ice nicelemeyecek sekilde yeniden yazildi ve **onarim
   jeometri ithaline de tasindi** -- orada tetiklenmemis olmasi hatanin
   olmadigi anlamina gelmiyor.

## 9. Kasten YAPILMAYANLAR

- **Sorular tekrar cozulmedi.** Tek cevap kaynagi kitabin basili
  anahtaridir (urun karari). `explanation` NULL.
- **Varlik duzeyinde sekil ayristirmasi yapilmadi.** Gorsel = tam soru
  kirpimi; `gorsel_kaynagi='tam_soru_kirpimi'` ile isaretli.
- **Morfoloji karmasikligi bilgi tasimiyor.** Zemberek yok; repo'nun
  heuristik yolu kelime basina en fazla bir ek soyuyor ve deger
  {0.0, 0.35} ikilisine cokuyor (olculdu: 1315 satirin hepsi 0.35).
  Uydurulmadi, `morfoloji_kaynagi` ile isaretlendi.
- **Bloom seviyesi dar kuralla atandi.** Sadece "sayisal sonuc isteyen +
  besi de sayisal sik" deseni 3/application; bu kitapta o desen 3 soruda
  var ve hicbiri nicelik kalibina uymadi, yani 1315 satirin tamami
  2/comprehension. Bu bir OLCUM degil VARSAYILAN; oyle isaretli.
- **`source_page` DOSYA numarasidir**, kitabin basili sayfa numarasi
  degil (sayfa_0020 -> basili 19).

## 10. Uretim zinciri

```
0021_biyo345_konu_agaci        (alembic)  16 unite dugumu
scripts/kitap/biyo345_kirp.py             1317 kirpim -> d-dataset/output/crops/BIYO345
scripts/kitap/biyo345_ithal.py            PASIF ithal (--yaz olmadan yalniz plan)
tests/e2e/test_biyo345_ithal.py           23 koruma testi (mutasyon karsiligi dahil)
```

Ithal sonrasi dogrulama (14 Eyl 2026, canli DB):
4 tabloda 1315'er satir; is_active 0, is_public 0, `v_safe_for_beta`dan
gecen 0; 1315 satirin tamami unite dugumune bagli, koke dusen 0;
bos metin/bos sik/gecersiz cevap/gorsel yok/boyut yok: hepsi 0.

## Beta aktiflestirme (0023_345_beta_onay)

Urun sahibi bireysel insan denetimini ATLAYIP toplu beta onayi verdi
(0014/0016/0018 ile ayni karar). Kapsam karari onundur: "hepsi, ama
TYT'nin sekilli sorulari HARIC".

Kapi yuku olculdu, tahmin edilmedi: `v_safe_for_beta` tanimi pg_views'ten
okundu ve her kosul uc kitap icin AYRI sayildi. Ustteki alti kosul zaten
geciyordu; dordu (quality_review_status, uyum sinyali, APPROVED,
is_active) tum satirlarda ENGEL idi ve migration dordunu de acti.

Nominal kapsam 4712 idi, gercek sayi 4706: geometrinin 6 satiri `sik_bos`
tasiyor ve o bayrak kapinin KENDI kosulu.

| kitap | toplam | acilan | disarida |
|---|---|---|---|
| geometri | 2708 | 2702 | 6 (sik_bos) |
| ayt biyoloji | 1315 | 1315 | 0 |
| tyt biyoloji | 1023 | 689 | 334 (gorsel_yok_sekilli) |

Olcum: `v_safe_for_beta` 8441 -> 13147 (+4706); GEOMETRI 1223 -> 3925,
BIYOLOJI 19 -> 2023. Geri alinabilirlik KANITLANDI: downgrade calistirildi,
havuz tam olarak 8441'e dondu, eklenen dort metadata anahtarindan kalan 0,
ithal metadata'si korundu; sonra tekrar uygulandi, ayni 4706 cikti.

Durustluk: `quality_review_status` `auto_judged_high` yazildi,
`human_verified` DEGIL -- hicbir insan bu sorulari tek tek dogrulamadi.
`is_ai_generated` alanina dokunulmadi, `true` kaldi. Cevaplar
dogrulanmadi; tek cevap kaynagi kitabin basili anahtaridir.

Bu kitabin `konsensus_sinyalleri` degeri (kopyalanmadi, bu belgeden
turetildi): `anahtar_seridi_cift_okuma`, `anahtar_numara_surekliligi`,
`metin_anahtar_numara_ortusmesi`. Sonuncusu METIN kanalinin bagimsiz
dogrulayicisidir (600 sutunun 599'u). Metin TEK turda okundu, bu yuzden
0018'in `cift_bagimsiz_okuma` sinyali listeye KONULMADI.

OSYM 2025 AYT ile carpisan 2 hash dis kontroldur ama 1317'nin 2'sini
kapsar; listeye girmedi.
