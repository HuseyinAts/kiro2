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

## Adim 2 -- Kirpim kutulari (BITTI)

Cikti: `acil_2324_geometri_kirpim_kutulari.json` (**1881 kutu**).
Uretici: `backend/scripts/kitap/acil_geo_kutu.py` (kutulari uretir VE dort
kapiyi kosar; kapilardan biri patlarsa dosyayi hic yazmaz).

Kutular sabit bir izgaradan degil, **simgeden** turetiliyor. Kurallar
Faz 0'da olculmustu; burada uygulandi:

| kural | deger |
|---|---|
| kutu ustu | simge_y - 6 |
| kutu alti | ayni sutunda sonraki simge_y - 9 |
| son kutunun alti (cevap kutulu sayfa) | kutunun ustu - 4 |
| son kutunun alti (kutusuz sayfa) | 902 |
| kutu sol kenari | simge_x + 24 (disk disarida kalsin) |
| sol sutun sag kenari | gx_sag + 1 |
| sag sutun sag kenari | 706 |
| tam genislik sayfa | sag sutunda simge yok + govde 400'un sagina tasiyor |

### Dort kapi (hepsi gecti)

| kapi | olctugu sey | sonuc |
|---|---|---|
| 1 | kutu sayisi == 1881 | gecti |
| 2 | hicbir kutunun alti cevap kutusuna girmiyor | 0 ihlal |
| 3 | ayni sutunda ortusme yok, 40 px'ten kisa kutu yok | 0 / 0 |
| 4 | her kutuda murekkep var (>= 120 px) | 0 bos |

**Kapilarin gecmesi kutular DOGRU demek degil**, yalnizca bilinen dort
hata sinifinin olmadigini soyler. Bu yuzden ayrica gozle ornekleme
yapildi: s5, s47, s200, s435 sayfalarinda kutular sayfanin uzerine
cizilip bakildi.

### Gozle ornekleme iki kusuru yakaladi (kapilar yakalayamadi)

**(a) Sol sutunun sag kenari sikki kesiyordu.** Ilk turetme
`gx_sag - 8` kullaniyordu; s200'de "E) 14" ve "E) 34" siklarinin son
harfi kutunun disinda kaldi. Olcum: sol sutunun metni **tam gx_sag'da**
bitiyor (s200 sik satiri, murekkep x 84-361, gx_sag = 361). Kenar
`gx_sag + 1` yapildi.

  Yan etkisi: sag sutun simgesinin diskinden ~10 px sol kutuya siziyor.
  Disk sabit renkli oldugu icin (240,238,247 / glif 69,39,160) disa
  aktarimda beyaza boyanacak -- adim 2b.

**(b) Okuyucu simgesi kutunun icindeydi.** Ilk turetme kutuyu simgenin
x'inden baslatiyordu, yani ogrenciye gosterilecek gorsele okuyucunun
kendi arayuzu giriyordu. Sol kenar `simge_x + 24` yapildi.

**(c) Tam genislik sayfa yaridan kesiliyordu.** s47 ("Karma Test - 4")
tek sutunlu; sol kutunun sag kenari 338'de kaliyor ve soruyu ortadan
bicdi. Sag sutunda hic simge yokken govdenin ayiricinin sagina tasiyip
tasmadigi olculuyor; tasiyorsa kutu sayfanin tamamini kapliyor.

Not: (a) ve (c) dort kapinin da GECTIGI durumlardi -- kapilar "kutu bos
mu, tasiyor mu, cakisiyor mu" diye bakiyor, "dogru yeri mi kapsiyor"
diye bakmiyor. Gozle ornekleme bu yuzden zorunlu.

## Adim 2b -- Kirpim disa aktarimi (BITTI)

Uretici: `backend/scripts/kitap/acil_geo_kirp.py`
Cikti: `<CROP_IMAGE_DIR>/ACILGEO_2324/s<sayfa>_<sutun>_<sira>.png`
(**1881 gorsel**; git'e girmez, her ortamda yeniden uretilir.)

### Kaynak PDF degil PNG

Bu kitabin PDF'i zaten ayni PNG'lerden uretilmis; PNG'den kirpmak
render boyutu uyusmazligi riskini bastan kaldiriyor. Yine de her
sayfanin boyutu 1920x1080 ile karsilastiriliyor ve tutmazsa script
DURUYOR -- kaymis kirpim uretmektense hic uretmemek.

### Okuyucu simgesi beyazlatiliyor

Adim 2'de sol kutu `gx_sag + 1`'e kadar uzatilmisti (yoksa son sikkin
son harfi kesiliyordu); bunun yan etkisi sag sutun simgesinin diskinden
~10 px'in kutuya girmesiydi. Disk OPAK oldugu icin altinda kitap
icerigi zaten gorunmuyor: beyaza boyamak bilgi kaybettirmiyor.

Beyazlatma **renge gore degil, konuma gore** yapiliyor. Gerekce Faz
0'dan: s435'teki bisikletli cizimin lacivert formasi glif rengine 40
tolerans icinde dusuyordu; renk filtresi kitabin kendi cizimini de
silerdi. Konumlar kutu dosyasinin kendi `simge` alanindan geliyor --
her simgenin bir kutusu oldugu icin liste tam, ve script git disi bir
dosyaya bagimli degil.

### Dogrulama

* 1881 kutu -> **1881 gorsel**, eksik yok.
* Gozle ornekleme: s0200_sol_1 (soru 10, "E) 14" tam), s0200_sag_1
  (soru 12, bes sik tam), s0005_sol_1 ("E) 25" tam), s0047_sol_1 (tam
  genislik soru, uc vinc sekli de iceride). Hicbirinde okuyucu simgesi
  yok, hicbirinde cevap kutusu yok.
* Script'in `faz0b.json` bagimliligi kaldirildiktan sonra cikti
  degismedi: 120 rastgele dosyada md5 farki 0.

## Sirada ne var

| adim | durum |
|---|---|
| 1. cevap anahtari | **BITTI** (1881 cevap, 3 kanal + simge caprazi) |
| 2. kirpim koordinatlari (simgeden turetilir; tek/cift 18 px kaymasi) | **BITTI** (1881 kutu, dort kapi + gozle ornekleme) |
| 2b. kirpim disa aktarimi (disk beyazlatma dahil) | **BITTI** (1881 gorsel) |
| 3. sayfa transkripsiyonu (442 sayfa, ~37 grup, ~5,5M jeton) | siradaki |
| 4. konu agaci migration (6 bolum / 27 konu) | -- |
| 5. ithal araci + e2e testler | -- |

## Olcum dosyalari (git disi, `backend/_geo1_gecici/`)

`_a1_kutu_kirp.py` (138 kutu kirpimi), `_a1_montaj.py` (kanal A/B
montajlari), `anahtar/` (kutu goruntuleri), `montaj_a/`, `montaj_b/`,
`kanal_c*.png`, `okuma_a.json`, `cevap_anahtari.json`, `testler.json`.
