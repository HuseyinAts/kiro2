# 345 2025 Start Matematik -- uretim yontemi ve olcumler

Durum: Faz 1 (sayfa turu, capa taramasi, cevap anahtari, test -> unite)
Faz 2 (unite agaci, 0057), Faz 3 (kirpim kutulari) ve Faz 4
(transkripsiyon + tam ikinci okuma) TAMAM. Sonraki fazlar `STM_345_KESIF_VE_PLAN.md` bolum 2'de.

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

Simge (mor buyutec) sayimi 371 (Faz 3'te yanlis simge elendi, bkz. 3),
numara 371. Simge soru BASI degildir: s266 sag sutunda simge sorunun
ortasinda ('Buna gore...' satirinin solunda) duruyor; s233 solda bos alanda
bir simge var; s137 solda bir soruda simge yok. Kirpim capasi Faz 3'te basili numaradan alinir, simge
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

## 3. Kirpim kutulari (`stm345_kutu.py`, `stm345_kirp.py`)

`345_2025_start_matematik_kirpim_kutulari.json`; ortme raporu
`345_2025_start_matematik_ortme_olcumu.json`. Gorseller git'e girmez,
kutulardan yeniden uretilir.

| kural / olcu | deger |
|---|---|
| capa | basili soru numarasi, 180/180 sutun (simge yedek, kullanilmadi) |
| tavan | unite adi bandi (kirmizi) son satiri + 4; olculen bant alti 120 (52 sayfa) / 123 (38) |
| kutu ustu | capadan yukari ilk 10 satirlik bos bandin alti - 3 (mat345tyt kurali); kisa bant yedegi 0 kez gerekti |
| kutu alti | sonraki kutunun ustu - 1; sutun sonu 900 (serit murekkebi y >= 914, sutun icerigi en alt 883) |
| yatay | ara cizgi cift dosya x 372, tek x 369 (90/90, doluluk >= 0.8); sol [4, cizgi-2], sag [cizgi+3, 738]; kenar seridi yok (90/90) |
| kapi ihlali | 0 (371 kutu, kutusuz 0; kart ici, >= 30 px, serit sizintisi yok, capa kutu icinde, sira ve cakisma) |
| ust kesimi notr metne degen | 0 |
| yukseklik | min 129, medyan 368, max 755 |
| kenar kapisi (notr murekkep kirpim kenarinda) | 0 |

Gozle: 371 kirpimin tamami 13 temas sayfasinda (0.45x, kirmizi cerceve)
tek tek bakildi; baslik bandi, onceki/sonraki soru ya da cevap seridi
tasiyan kirpim goruldugu yok.

### 3a. Yanlis simge ve okuyucu maskesi

Ilk kosuda s83 sagdaki sandalye sekli (koyu mavi kenar + gri zemin)
simge sanildi; okuyucu maskesi seklin icinde bir diski beyazlatti
(T011_03, ortme halkasi 106 piksel). Duzeltme `stm345_tarama.py`: gercek
simge YUVARLAK lila disk ustundedir; merkezden 9-13 px halkanin >= 0.6'si
disk rengi olmali. Olculdu: gercek 371 simgede oran >= 0.79, sekil 0.32.
Duzeltmeden sonra T011_03 kirpimi orijinalle ayni (10x gozle); simge
371, cevap anahtari bayt bayt degismedi.

### 3b. Ortme

6 soruda okuyucu diskinin halkasinda kitap murekkebi var. 5'inde sag
sutunun simgesi, sol sutundaki satirin son harflerinin hemen sagina
oturuyor (T010_07 'igede', T016_02 'birinin', T027_05 'ayni', T037_02
'hangi', T038_05 'Akif'); halka piksellerinin bir kismi ara cizginin
kendisi. Kirpimda satir kenara kadar okunuyor; diskin altinda harf kalip
kalmadigi goruntuden bilinemez -> Faz 4'te okuyucuya soru basina
bildirilecek, bayrak `okuyucu_diski_ortme`. T030_07: disk sag sutunun
'7.' numarasinin ustunde; numara kismen beyazlatildi, govde etkilenmedi.

### 3c. Kapsam disi olcumu

Konu sayfalarinda 'ISINDIRMA KOSESI' basligi (turuncu ~(247,145,48)):
83 sayfada 83 kutu; 83'unun basligi gozle dogrulandi (alt sinir; olcu
baska renkte basilmis kutuyu kacirabilir). Acik uclu alistirmalar siksiz
oldugu icin sayilmadi.

## 4. Transkripsiyon (`stm345_metin_harness.py`)

`345_2025_start_matematik_metin.json` (371 soru). Kirpimlar 2x Lanczos;
10 grup (test sinirina hizali, ~40 soru), 10 ayri okuyucu. Talimat
`VeraFilm/s_metin_talimat.md`: 'kitap ne yaziyorsa o', soru cozme yok,
anahtar gosterilmedi; matematik yazim sozlesmesi (eksi U+2212, `a/b`,
`x^2`, kok, mutlak deger, kutu `\u25a1` ve cokgen sembolleri, `[n]` kutu
icinde sayi); ortme listesindeki sorularda satir sonu bildirimi.

Kapilar (harness `kapi`, okuyucuya soylenmeyen yapidan): KAPI1 her kirpim
bir kez; KAPI2 basili no == test ici sira; KAPI3 bes sik dolu; KAPI4
toplam 371. **TUM KAPILAR YESIL.** Ortme listesindeki 5 soruda okuyucular
satir sonlarini tam gordu (disk altinda harf yok).

### 4a. Ikinci okuma -- on kayitli TAM okuma

On kayit (`345_2025_start_matematik_ikinci_okuma.json`, karsilastirmadan
ONCE): onceki kitaplarin kurali (esasli hata CP95 ust siniri <= %3)
371 soruluk kitapta sifir hatali orneklemde bile n >= 99 ister; bu yuzden
dogrudan TAM ikinci okuma: ilk okumayi gormeyen 10 ayri okuyucu, ayni
talimat ve gruplar.

* 317 soru tam ayni; 54 soruda 95 farkli parca. Her fark kirpimdan (1x)
  piksel dokumu ya da 6x yakinlastirmayla karara baglandi (hukumler
  `ikinci_okuma.json` -> `sonuc`, `duzeltmeler`).
* Esasli ilk okuma hatasi 11 soru (%3.0): ikisi harf/imla (I noktasi,
  'olan'), biri eksik sekil yazisi, sekizi isaret (soluk '+' -> '-',
  '<=' -> '<', sapka).
* Kesme isareti ' / \u2019 karisikligi (38 parca) bicimdir: harness
  topla tum metinde ASCII "'" yapar.
* Ondalik ayirici: ikinci okuma 6 soruda nokta okudu; piksel dokumunde
  hepsinde virgul kuyrugu (taban cizgisi alti soluk iz) var -> virgul.

### 4b. Soluk '+' taramasi (iki okumanin ortak kor noktasi)

Ekran goruntusunde '+' isaretinin dikey cubugu cogu yerde 200-245 griye
soluyor; iki okuyucu ayni isareti '-' okuyabilir ve karsilastirma bunu
yakalamaz. Piksel olcusu: izole ince yatay cubuk (6-10 px, koyu < 200,
iki yani bos) + ortasindan gecen seritte ust ve altta simetrik soluk iz
(200-248). 40 aday; 40'i gozle '+'. 34'unde iki okuma da '+', 4'unde
yalniz ikinci okuma; **2'sinde iki okuma da '-' yazmisti** (T008_09 B
`2 * (3a + 4b)`, T021_07 III `c + b`) -> duzeltildi. Ayrica T024_06'nin
kalin satirinda sapka iki okumada da kacmisti (6x). Ikinci, yerel arka
plana gore tarama 63 aday daha verdi; metin icindeki adaylarin 31
sorusu son metinle karsilastirildi, celiski yok.

Sinir: tamamen kaybolmus isaretler (gri kutu icinde) bu olcuyle
bulunamaz; okuyucu bildirimi + piksel dokumuyle `[??]` yapildi.

### 4c. Okunamaz -> `[??]` (tahmin yok)

| soru | ne |
|---|---|
| T005_05 | C sikki o sutununda isaret render edilmemis |
| T011_07 | 2 numarali gri kutuda uc isaret render edilmemis |
| T012_02 | III. denklemde isaretler render edilmemis |
| T035_08 | 2. tarti ekranindaki 7-segment us (11 / 9 ayrilamaz) |
| T036_02 | Sekil 1 kutle ekranindaki us (3x3 piksel) |
| T038_04 | tablo hucresinde 3 ile 2 arasinda silinmis isaret izi |

Bu 6 soru gorunen alanda `[??]` tasir; 0039/0056 dislama kurali geregi
aktiflestirmede disarida kalir. Goruntunun kendisi de ayni kaybi tasir;
sorular bu cozunurlukte cozulemeyebilir.

## 5. Mukerrer ve eski hat (`stm345_mukerrer.py`)

Cikti: `345_2025_start_matematik_mukerrer_adaylari.json` (ithal ONCESI
olcum).

| olcum | sonuc |
|---|---|
| `soru_hash` x tum question_bank | 0 carpisma |
| kitap ici ayni hash | 0 |
| kitap ici yakin cift (3-gram >= 0.9 VE >= 3 ayni sik) | 0 (en yuksek 0.78) |
| DB MATEMATIK + GEOMETRI (16235 satir), 3-gram >= 0.75 | 15 aday, GUCLU 0 (en yuksek 0.847) |
| cikmis soru etiketi (OSYM) | 0 soru |

### 5a. Olcu neden degisti

Onceki kitaplarin olcusu (govde kelime kumesi Jaccard >= 0.75 VE bes
sikkin >= 3'u birebir) burada once denendi: 369 aday, 111 'guclu'. Gozle
hepsi farkli soru: govde kelimeleri kalip cumle ('islemin sonucu
kactir?'), formul kelime kumesine girmiyor; sik normalizasyonu eksiyi
bosluga cevirdigi icin '-2' == '2' ve 1..5 gibi siklar her yerde
ortusuyor. Yeni olcu formulu korur: bosluksuz, eksi tek '-', `\frac{a}{b}`
-> `a/b`, LaTeX komutu/parantez/dolar silinmis govdenin karakter 3-gram
Jaccard'i. GUCLU = 3-gram >= 0.9 VE >= 3 sik birebir.

Pozitif kontrol (betik kapisi): kesirli ve eksili 52 govdenin LaTeX'e
cevrilmis, bosluklari bozulmus hali kendi sorusuna 3-gram 1.0 ile
baglaniyor; biri 0.9'un altina duserse betik durur. Ilk kosuda bu kapi
bir aciga yakaladi (`\frac` ile '/' kayboluyordu, T009_04 0.759); kesir
donusumu eklendi.

15 adayin hepsi (0.75-0.847) gozle incelendi: ayni kalip, farkli formul
(or. T034_02 '|x + 1| + 2 = 0' <-> '|2x + 1| + 3 = 0'). Isaret konmaz.

### 5b. Eski hat

Kaynak adini tasiyan 3 eski satir, basili sayfalari gozle incelendi:

| db_id | basili s. | eski satir | sayfada ne var |
|---|---|---|---|
| fc2fc6b8 | 194 | dortgen alani formulu | Iki Bilinmeyenli Denklemler, denklem sistemi alistirmalari |
| 0bd78e59 | 203 | 'serinin ortalamasi' formulu | Basit Esitsizlikler, sayi dogrusu araliklari |
| be4bf295 | 209 | 'a + b = 10 ve a - b = 2 ise a ve b'nin toplami' | Basit Esitsizlikler, aralik alistirmalari |

Uc soru da sayfada yok; 371 soruluk metne en yakin 3-gram 0.13-0.26.
Uc satir da aktif. Oneri: pasif (SAHIP KARARI; 0056 deseni, gunluklu geri alinabilir).

SAHIP KARARI (26 Eyl): "Bu 3 eski satir pasife alinsin" -> migration
`0058_stm345_eski_hat_pasif`: guard (kaynak adi, ithal_araci yok, hala aktif),
onceki is_active GUNLUK'te, silme yok. Yerel DB'de upgrade -> downgrade ->
upgrade temiz (3 -> 3 aktif geri -> 3 pasif).

## 6. Ithal (`stm345_ithal.py`) -- PASIF

Kaynak adi `345 2025 Start Matematik` (kaynak_sozlesmesi girdisi; onek
STM345). TYT / MATEMATIK, sinif 12; sorular unite dugumune
(MAT-345S25-Unn, `konu_eslesme_duzeyi` = 'unite'). `source_page` BASILI
sayfa (dosya - 1; eski hat satirlari da basili sayfa tasiyor).
Kirpimlar `/static/crops/STM345/<STM345-Tddd_nn>.png` (yerelde
`d-dataset/output/crops/STM345/`, 371 dosya; git'e girmez,
`stm345_kirp.py` yeniden uretir).

Kapilar: yapisal (371 soru, 45 test, 16 unite, 371 anahtar, 371 kutu,
metinde cevap alani yok, cikmis etiketi yok) + baglama (basili no == test
ici sira; kutu ile anahtar ayni dosya/sutun/serit sirasi; kutu testin
sayfasinda) + on kontrol (5 sik, A-E, dolu anahtar sikki, unite kodu,
bilinen cevap kanali, kutu, basili sayfa == dosya - 1, benzersiz id).

Yerel DB (26 Eyl): 371 yeni satir, is_active 0, beta kapisindan gecen 0;
ikinci kosu 'zaten var 371, yazilacak 0'. Bayraklar: kaynak_kusuru 23,
okunamaz_isaret 6, okuyucu_diski_ortme 6, sikler_gorsel 3 (+ sik_tekrar 3,
ayni uc soru). Cozum yok; `cozum_dogrulamasi` = 'yapilmadi_urun_karari'.

## 7. Aktiflestirme (0059, Faz 8 -- sahip karari 26 Eyl)

Kapi yuku yerel DB'de olculdu (0059 docstring): 371 satirda uc kilit
(quality 'pending', uyum sinyali yok, ai + review 'PENDING'); servis disi
bayrak 0, gorunen alanda `[??]` 6, bos sik/cevap 0, gorselsiz 0, aktif
satirlarla hash cakismasi 0. Dislama kurali 0039/0056 ile ayni -> 365
satir acilir ('auto_judged_high', 'APPROVED', bes konsensus sinyali,
onay_turu 'toplu_beta_sahibi', bireysel_denetim_yapildi false); `[??]`
tasiyan 6 soru pasif kalir. Unite sayaclari toplami 365. Yerel DB'de
upgrade -> downgrade -> upgrade temiz (365 -> 0 -> 365).

Not: `v_safe_for_beta` is_active suzmez; 0058 ile pasife alinan eski hat
satirlarindan 2'si onceki `auto_judged_high` durumlari nedeniyle gorunumde
kalir (DB genelinde 14 pasif satir ayni durumda; bu PR'in degistirdigi bir
davranis degil).

## Testler

`backend/tests/e2e/test_stm345_ithal.py` (47: butunluk, yapisal kapi,
unite baglantisi, kaynak sozlesmesi, eski hattan ayri kimlik, pasif ithal,
bayrak capalari, 8 yapisal + 10 kayit/baglama mutasyonu; kod mutasyonlari
-- etiket kapisi, okunamaz bayragi, basili sayfa, kanal kapisi -- kirmizi).

`backend/tests/e2e/test_stm345_veri.py` (54; 0059 ile +4: kimlik/zincir,
dislama kurali, 365 hedef metinden, durustluk -- isaret alani / bayrak
silme ve human_verified mutasyonlari kirmizi. Onceki 50; 0058 ile +3: kimlik/zincir/ASCII, pasif kume == kitapta yok
olculen kume, guard ve gunluk. Faz 5 ile +6: 371 farkli
soru_hash, kitap ici yeniden uretilir, LaTeX kopya yakalanir, formul
normal bicimi, guclu aday yok, eski hat kitapta yok -- eksi kaybi, kesir
donusumu ve esik mutasyonlari kirmizi. Faz 4 ile +8: metin kapilari
ve mutasyonu, kutu <-> metin birebir, kesme, on kayit, duzeltmelerin
uygulandigi, [??] listesi, soluk '+' duzeltmeleri. Faz 3 ile +8: kutu kapilari,
cevap <-> kutu birebir, capa == basili numara, serit/bant siniri, yatay
sinir, kapi mutasyonu, yanlis simge elendi, ortme raporu. Faz 2 ile +8: harita hamdan
turer, migration == harita, zincir, ASCII, ayrac adi / sayfasi mutasyonu): hamdan birebir turetme,
A/B farki / eksik sutun / bicim disi girdi mutasyonlari, sureklilik, bant,
kapsam, kanal durustlugu, ASCII. Mutasyonla dogrulandi: cevap harfi,
bant adi, test sayfasi ve kaynak alani bozulunca ilgili test kirmizi;
temiz dosyada 0 kirmizi.
