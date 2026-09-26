# 345 2025 TYT Fizik Soru Bankasi -- uretim yontemi ve olcumler

Kesif ve plan: `FZT_345_KESIF_VE_PLAN.md`.

## 0. Kaynak ve tavani

FERNUS okuyucusunun 1920x1080 ekran goruntuleri, 368 sayfa (+ metin
katmani olmayan PDF). Kart cercevesi 10 ornek sayfada ayni: dikey cizgi
x 586-588 / 1331-1334, yatay y 42 / 1022 -> ic kart (589, 43, 1331, 1022).
Basili sayfa = dosya.

## 1. Cevap anahtari -- sayfa alti serit, iki okuma + glif + goz

Cikti: `345_2025_tyt_fizik_cevap_anahtari.json` (176 test, 1397 cevap).
Ham: `345_2025_tyt_fizik_ham_okumalar.json`. Tarama:
`345_2025_tyt_fizik_capa_taramasi.json`.

1. **Serit yeri pikselden:** kart y 840-975 murekkep bantlari; 342
   sayfada tam y 899-904 bandi. Soru sayfasi = bu bantta gri (doygunluk
   < 40) murekkep + en az bir okuyucu simgesi: 357 sayfa.
2. **Girdi sayisinin bagimsiz kanali:** serit fontu 6 px, girdiler arasi
   bosluk 3-5 px'te vadisiz; nokta sayimi da ince kenarlarda kopuyor
   (1530 / 1440, ikisi de tutarsiz). Bu yuzden sayim okuyucu simgesinden:
   stm345 tanimi (glif + lila disk + halka orani >= 0.6). Serit bandinin
   uzerinde (cy >= 890) 17 simge soru capasi DEGIL (seride binen okuyucu
   simgesi; soru metni yok) -> 1397.
3. **Iki okuma:** A 5x sayfa sirasi (60 montaj, 12 satir), B 7x TERS sira
   (80 montaj, 9 satir); 8'er ayri okuyucu; girdi sayisi soylenmedi.
   A 1397 girdi, B 1397 girdi; 714 sutunun 713'u birebir.
4. **Tek fark:** s277 R A '6.D', B '8.D?'. 10x gozle '6'; ayni sayfanin
   sol sutunu '4.B 5.A' -> +1 surekliligi. Karar '6.D' (A).
5. **Kapilar:** girdi sayisi == simge 714/714; numara ya +1 ya 1
   (1397/1397, 176 test); her test tek unite araliginda, sayfalari ardisik.
6. **Glif kanali:** sutun seridi okumadaki N'e N-1 en genis bosluktan
   bolunur, her girdinin son 7x12 px'i; en-yakin-komsu LOO 1380/1397.
   Gri maske doygunluk filtresiz ilk denemede 1211/1397 idi (mavi sus
   cubuklari ve seride binen simge bolmeyi kaydiriyordu).
7. **Goz (10x):** '?' tasiyan, A/B farkli ya da glifi tutmayan 70
   sutunun TUM girdileri; hepsi A okumasiyla ayni. Harf ayrimi: soluk sol
   cubuklu 'D' (orta centik yok) / 'B' (orta centik var).

Kanal dagilimi: iki_okuma+piksel 1252, +goz(10x) 88, +goz+tereddut 56,
farkli+goz+sureklilik 1. Harf: A 177, B 234, C 329, D 306, E 351.

## 2. Unite agaci (0060)

Cikti: `345_2025_tyt_fizik_konu_haritasi.json` (`fiz345tyt_harita.py`),
migration `0060_fzt345_konu_agaci.py` (o JSON'dan uretildi).

* 19 unite: icindekiler (dosya 3-4, gozle), basili baslangic sayfasi.
* Bagimsiz dogrulama: her baslangic sayfasinin ust bandi (kart y 20-145,
  gozle): 19/19 '1. bolum' rozeti + 'KAZANIM ODAKLI SORULAR' + orta bantta
  unite adi. Bant adi icindekiler adinin kelimeleriyle sirayla ortusur;
  tek fark s316 bandi 'ISIK AKISI VE AYDINLANMA' (icindekiler 'Isik Akisi -
  Aydinlanma - Golge Olaylari'): 've' baglaci yalniz bantta atlanir.
* Unite sonu sayfalari (sinirin oncesi) 'Orijinal Sorular', 'Karma
  Sorular', 'Gunluk Hayat Uygulamalari' bolumleridir; ayni unitenin
  parcasi.
* Her test tek unitenin sayfa araliginda (176/176).
* FIZ kokunun altinda `FIZ-345T25-Unn`, kok+1, subject_area 'FIZIK'.
  Yerel DB'de upgrade -> downgrade -> upgrade temiz (19 -> 0 -> 19).

## 3. Kirpim kutulari (`fiz345tyt_kutu.py`, `fiz345tyt_kirp.py`)

Cikti: `345_2025_tyt_fizik_kirpim_kutulari.json` (1397 kutu, kapi ihlali 0),
`345_2025_tyt_fizik_ortme_olcumu.json`. Kurallar stm345_kutu deseni;
olculmus farklar:

* Kart 742x979; cevap seridi y 899 -> kutu alti en cok 893, kapi 897.
* Capa: basili numara sayisi seritle tutan 583 sutunda numara, tutmayan
  131 sutunda (cikmis soru kutusu, pembe 'Orijinal Sorular' sayfalari)
  okuyucu simgesi (Faz 1: simge == girdi 714/714). Kutusuz soru 0.
* Tavan: kirmizi unite bandi yoksa kart y 60. Kisa bant kurali 71 kez.
* Beyazlatma: soru simgeleri + sutun disi 7 + serit ustu 17 simge.
* Gorsel QA (gozle, tohum 345): simge kanalli 16, en kisa 12, en uzun 8,
  rastgele 32 kirpim -- hepsi tek soru, numara ustte, siklar icinde.
  Ust kesimi notr metne degen tek kutu T022_01: cikmis soru kutusunun
  cerceve ustu, soru metni tam.
* Ortme suphesi 161 soru (170 halka): gozle ornekte disk, numaranin sol
  kenarini ve sayfa susunu (mavi/yesil dikey cubuk) ortuyor; soru metni
  ortulmuyor. Bayrak olarak tasinir.
* Kenar kapisi ihlali 0.

## 4. Transkripsiyon (`fiz345tyt_metin_harness.py`)

`345_2025_tyt_fizik_metin.json` (1397 soru). Kirpimlar 2x Lanczos;
33 grup (test sinirina hizali, ~40 soru), 33 ayri okuyucu. Talimat
`VeraFilm/f_metin_talimat.md`: 'kitap ne yaziyorsa o', soru cozme yok,
anahtar gosterilmedi, fizik yazim sozlesmesi (alt indis `h_K`, `F_(net)`;
us `10^(-3)`; eksi U+2212; vektor U+20D7; Yunan harfleri; birimler;
tablo ` | `, bos hucre `-`; alti cizili `<u>`; sekil yazisi yalniz soru
ona dayaniyorsa).

Kapilar (harness `kapi`, okuyucuya soylenmeyen yapidan): KAPI1 her kirpim
bir kez; KAPI2 basili no == test ici sira; KAPI3 bes sik dolu; KAPI4
toplam 1397. **TUM KAPILAR YESIL.**

### 4a. Numara ortmesi (KAPI2)

Okuyucu diski cogu yerde numaranin sol yarisini kesiyor; kalan parca iki
rakama uyuyor (8 -> '3', 4 -> '1', 9 -> ')'). Okuyucu null yazabilir;
yalniz capa simgeden alinan (131 sutun) ya da ortme olcumundeki (161)
sorularda. Ilk kosu 53 KAPI2 verdi: hepsi null, hicbiri yanlis rakam
degil. 53'unun sol-ust 200x110 bolgesi izgarada gozle incelendi: disk
numarayi tamamen kesiyor, halkada murekkep kalmadigi icin ortme olcumu
kacirmis. Liste `345_2025_tyt_fizik_numara_goz.json`; KAPI2 onu da
ortulu sayar (liste bosaltilinca 53 ihlal geri gelir -- test). Null
numara toplam 134; numara test ici siradan alinir.

Okuyucularin numara kesigi notlari kaynak kusuru degildir (talimat 'bunu
YAZMA'); harness `topla` bunlari ';' parcasi bazinda ayiklar (tirnak
icindeki ';' bozulmaz). Kalan gercek kusur notu 63 soru.

### 4b. Ikinci okuma -- on kayitli TAM okuma

On kayit (`345_2025_tyt_fizik_ikinci_okuma.json`, karsilastirmadan
ONCE): STM345 ilk okumasinda esasli hata %3.0 idi; bu oranda orneklem
CP95 <= %3 kapisini gecemez -> dogrudan TAM ikinci okuma: ilk okumayi
gormeyen 33 ayri okuyucu, ayni talimat (teslim dizini `f_metin_parca2`),
ayni gruplar.

* Normalizasyon (NFC, kesme/tirnak tipi, eksi/tire tipi, carpma noktasi,
  bosluk) sonrasi 1328 soru ayni, 69 soru farkli (govde 64, sik 19,
  sekil_var 1, vurgu 1).
* 69 farkin hepsi kirpimdan gozle (3-16x) karara baglandi (3 hakem
  partisi; hukumler `ikinci_okuma.json` -> `hukumler`, nihai alanlar
  `duzeltmeler`): 35 yalniz bicim (tablo '-' hucresi, coklu alt indis
  parantezi, bilesik kesir parantezi, noktalama), 13 ilk okuma, 20 ikinci
  okuma, 1 ikisi hatali.
* **Ilk okuma esasli hata 14 / 1397 (%1.0)**; ikinci okuma 21. Ornekler:
  'montelenmesi' -> 'monte edilmesi' (ikinci), 'alpha > 0' -> 'alpha > theta'
  (ilk), sekildeki rota bilgisi eksik (ilk), tabela / ekran yazisi eksik.
  Kitabin baski hatalari ('karsilastimalarindan', 'gimistir',
  'filitreleri') korunur; duzelten okuma hatali sayildi.
* Okuyucular ayni model ailesinden; ortak kor nokta riski icin 4c.

### 4c. Soluk isaret taramasi ve yakinlastirma

STM345 4b deseni ('+' nin dikey cubugu soluk -> iki okuyucu da '-'
okuyabilir): koyu kisa yatay cubuk + ortasindan gecen simetrik soluk
dikey iz. 9 soruda 11 aday; 11'i de sekil ogesi (izgara kesisimi, olcek
cizgisi, sekil etiketi). Metinde gizli '+' yok.

Okuyucu bildirimleriyle soluk eksiler: T095_04 Bakir ussu (piksel
dokumunde 233-247 gri yatay iz: var), T078_09 sik tablosunda uc soluk
eksi (var). Cozume dogrudan giren belirsiz karakterler 8x yakinlastirildi:
T008_07 usleri (I. 5, III. yatay cubugu eksik 4), T042_06 '9,798'.

### 4d. Okunamaz -> `[??]` (tahmin yok)

| soru | ne |
|---|---|
| T118_07 | tabela rakamlari: BANDIRMA ve GOKSUN nufusunun son haneleri, GOKSUN rakiminin son hanesi |

Tek soru gorunen alanda `[??]` tasir; 0039/0056 dislama kurali geregi
aktiflestirmede disarida kalir.

## Testler

`backend/tests/e2e/test_fiz345tyt_veri.py` (39): hamdan birebir anahtar
turetme, tek farkin kaydi, A/B farki / gecersiz goz karari / bicim disi /
numara kopmasi / simge farki / goz celiskisi mutasyonlari, kapsam, unite
araliklari, kanal durustlugu, ASCII; Faz 2 ile +7: harita hamdan turer,
migration == harita, zincir, kodlar, bant adi / rozet mutasyonu, 've' kurali;
Faz 3 ile +5: kutu kapilari, kutu <-> cevap birebir, capa kanali, kapi
mutasyonu (sizinti / cakisma), ortme raporu; Faz 4 ile +13: metin
kapilari, kapi mutasyonu (KAPI1-4), null numara yalniz ortulu sorularda,
numara_goz listesi bosalinca 53 KAPI2, kutularla ayni dosyalar, kivrik
kesme / numara notu kalmadi, numara notu ayiklama, on kayitli tam ikinci
okuma sayilari, duzeltmeler son metinde, `[??]` yalniz T118_07, ornek
hukumler, etiketler, soluk '+' kaydi.
