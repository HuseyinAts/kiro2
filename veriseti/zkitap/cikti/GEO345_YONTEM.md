# 345 TYT-AYT Geometri Soru Bankasi -- uretim yontemi ve olcumler

Veri: `geo345_sorular.json` (2743 soru). Gorseller: `geo345_kirp.py`.
Kaynak: `veriseti/zkitap/screenshots/345 Tyt Ayt Geometri Soru Bankasi{,' 2'}/`
(PDF + sayfa PNG'leri; her ikisi de git disinda).

## Kitap kimligi

Iki cilt: c1 = 440 sayfa, c2 = 336 sayfa, toplam 776 sayfa.

DIKKAT: ayni klasorde ucuncu bir klasor daha var --
`345 2025 Tyt Ayt Geometri Soru Bankasi 1`. O AYRI BIR KITAP DEGIL:
c1'in ilk 336 sayfasi (318/336 sayfa alan imzasiyla birebir ayni; farkli
olan 18'in 4'u kapak/kunye/icindekiler, 6'si konu ayrac kapagi, 8'i esik
civari). KULLANILMADI.

## Kanallar ve sirasi

Her asama bir oncekini SINAR; her iddia ayni kapsamda olculmustur.

### F1 -- sayfa turu siniflandirmasi
Renk temasi hipotezi KURULDU ve OLCUMLE CURUTULDU (167/159 blok; iki
pencere yalnizca 256/440 ortusuyor; gozle bakinca 5. bir sablon cikti).
Birincil sinyal olarak ikon dedektoru secildi.

### F2 -- ikon dedektoru
`IKON_RGB=(69,39,160)`, tolerans 40, 7x7 morfolojik KAPAMA (halka + sap
parcalarini birlestirir), gercek ikon alani HER ZAMAN 86.
Dis dogrulama: c1'de ikonsuz sayfalar, icindekilerdeki 8 konu baslangicinin
tam bir oncesi -- 8/8, icindekiler bilgisi KULLANILMADAN.
Toplam alan=86 ikon: 3335.

### F3 -- cevap anahtari (iki bagimsiz okuma + hakem)
Serit: y 933-980, sol x 625-800, sag x 1140-1310, 4x buyutme.
Iki bagimsiz okuma (7'ser ajan, beklenen sayi SOYLENMEDI -- capa etkisi):
sayfa duzeyinde 767/776 (%98.84), girdi duzeyinde 2735/2745 (%99.636).
9 uyusmazlikta hakem turu (8x buyutme, A/B'nin ne dedigi soylenmeden):
iki hakem 9/9 birbiriyle uyustu.

BAGIMSIZ DOGRULAMA -- numara surekliligi: okuma sirasinda her adim ya +1
ya da yeni testte 1'e donus olmali. Okuyuculara bu kural SOYLENMEDI.
2743 girdinin 2742'sinde akis kusursuz.

Tek kirilma = KITABIN DIZGI HATASI: c2 s285 sag'da "11.A" basili, oysa
c2 s284 sag'da 11 zaten "11.D" olarak kullanilmis ve dizi 12,13 | ?,15.
20x dogrudan okumayla teyit edildi. Harf (A) tartismasiz; onarilan
yalnizca INDEKS ve o da konum sirasindan turetildi -- soru COZULMEDI.

Harf dagilimi (F8 girdisi): A 503 / B 526 / C 656 / D 521 / E 537;
ki-kare(4) = 27.38, C icin z = +5.13 -- C anlamli sekilde fazla.

### F4 -- soru metni (sutun granulu)
Kutu granulu DENENMEDI, cunku F2c kutu seti F3 ile kiyaslaninca bozuktu.
"Fazla ikon = konu kutusu" hipotezi c1 s146 sag'da CURUTULDU (fazlalik
ikon, ikiye bolunmus bir sorunun devamiydi). Soruyu tanimlayan sey konum
degil 5 SIKKIN varligi.

Sutun kirpimi (612-962 / 954-1300, y 60-962), olcek 1x (2x ile kiyaslanip
bakilarak secildi; jeton maliyeti 1/4). Kirpima BEKLENEN NUMARALAR basildi
-- F3'un tersi: orada sayi gizlenmisti, burada hizalamayi dogrulamak icin
gosterildi. 1300 sutun, 325 montaj, 13 bagimsiz ajan.

| denetim | sonuc |
|---|---|
| cikarilan soru | 2743 / 2743 |
| numara listesi F3 ile ayni | 1300 / 1300 sutun |
| siklar A-E tam | 2743 / 2743 |
| R5 (anahtarin gosterdigi sik dolu) ihlali | 0 |
| kesik soru | 0 |
| Turkce karakter korunmus | 2743 / 2743 (46.967 TR karakteri) |
| kitap ici hash cakismasi | 0 |

BEDAVA DOGRULAMA: 2743 hash `question_bank`'e soruldu -> 35 eslesme,
hepsi `Mikro Orijinal 2025 AYT Geometri Soru Bankasi`. Hash
`md5(lower(nfc(metin))|A|B|C|D|E)` oldugu icin metnin VE bes sikkin
bayt-bayt ayni olmasi gerekir. Okuyucular o sutunlari kendiliginden
"CIKMIS SORU / OSYM kosesi" diye etiketlemisti -- iki kitap ayni resmi
OSYM sorularini basmis. Hem hash formulunun dogru uygulandigini hem de
metin cikariminin dogrulugunu kanitlar.

ITHALAT SONUCU: ayni soru => ayni id; bu 35 satir icin `ayristir()`
`yabanci` dondurecek ve UZERINE YAZILMAYACAK (PR #254/#256).

### F5 -- soru gorsel kutulari
F3 anahtari her sutunda kac kutu olmasi gerektigini soyledigi icin bolucu
SINAV EDILEBILIR hale geldi. Dort hata, dort olcum:

| # | belirti | kok neden | kesik orani |
|---|---|---|---|
| 0 | -- | sabit dolgu | %30.44 |
| 1 | agir vakalar CIFT geliyor (135/135, 108/108) | sinir icerigin ortasindan geciyor | %9.83 |
| 2 | 1042 kutu supheli, cogu murekkep=0 | arama penceresi ikondan basliyor, ikon-icerik arasindaki bosluk "en genis kosu" saniliyor | -- |
| 3 | onlarca sayfada AYNI imza (w=70 h=82 murekkep=281) | "en genis bosluk" olcutu soru ile rozet arasini seciyor | -- |
| 4 | GOZLE: sik satiri kirpiliyor | son kutunun dibi sabit 928; F3'un (933,980) seridi PAYLI pencereydi | %8.79 |

Son durum: 238/2707 kutuda kesik; **ust 0, alt 0** (dikey kesik yok);
sol 46 ve sag 197 vaka <=16 px ve gozle bakildi -- SAYFANIN CERCEVE SUSU,
icerik degil. Dagilim: kutu yuksekligi min 111, murekkep min 1014,
supheli (h<120 veya murekkep<1500) 38 ve hepsi normal boyutlu kisa metinli
sorular.

Belirsiz 28 sutun (ikon > soru) ve 1 sutun (c2 s205 sag, ikon dedektoru
kacirmis) okuyucuya soruldu; atama iki sinavdan gecti: yapisal 28/28 hata
yok, capraz olarak okuyucunun andigi sik degerleri F4'un BAGIMSIZ
cikarimiyla celismedi.

TOPLAM: 2743 kutu / 1300 sutun -- F3 anahtar girdisi ve F4 soru sayisiyla
birebir.

### Gorsel uretimi
PDF sayfa boyutu OLCULDU: 1920x1080 pt; sayfa PNG'si de 1920x1080 -->
scale=1.0'da birebir, koordinat donusumu yok. Bu VARSAYIM DEGIL:
`geo345_kirp.py` her sayfada render boyutunu dogrular ve tutmazsa DURUR.

2743 gorsel uretildi; dosya boyutlari veri setindeki
`image_width`/`image_height` ile 2743/2743 ayni. Rastgele 9 kirpim gozle
dogrulandi (seed sabit): 9/9 tam.

`image_width`/`image_height` BU KITAPTA DOLDURULUYOR. Mevcut durumda
`question_content`'te gorsel URL'si dolu 7104 satirin 6029'unda bu alanlar
NULL.

### F9 -- konu bandi (sayfanin kendi basligindan)

Veri seti konu alani TASIMIYORDU. Konu, 0017'deki (Mikro Geometri) ilkeyle
uretildi: agac kitabin ICINDEKILER sayfasindan DEGIL, her sayfanin KENDI
BASLIK BANDINDAN.

#### Bandi bulmak

Ilk deneme dar bir y penceresiydi (150-172) ve 708 soru sayfasinin yalnizca
202'sinde bant buldu. Gozle bakinca kitabin en az uc sayfa sablonu oldugu
goruldu; bant kimi sablonda y 157-163, kiminde y 119-129'da. Pencere
y 90-200 / x 800-1340'a genisletildi; kirmizi maskeyle
`(r>130) & (r-g>70) & (r-b>70) & (g<110)` 655/708 sayfada bant bulundu.

Bant, satir bantlari icinde MUREKKEBI >=100 VE GENISLIGI >=60 olandir.
Olcum (7 sayfa): baslik bantlari murekkep 154..440, genislik 75..280;
sekil kalintilari murekkep 4..30. Iki satirli basliklar
("PARALELKENAR / ESKENAR DORTGEN - DELTOID") bu kuralla birlikte yakalanir.

#### Karisan sinyal: zorluk gostergesi

Ilk kumelemeler sasirtici sekilde kirilgandi (246 kume, 162 tek sayfa).
Tanilama montaji nedeni gosterdi: bandin sagindaki ZORLUK GOSTERGESININ
dolu kirmizi ibresi ayni y satirlarinda duruyor ve maskeye giriyor. Ibre
zorluga gore dondugu icin bant genisligi sayfadan sayfaya 280 -> 301 arasi
kayiyor.

Ayrim olculdu, varsayilmadi. Bant icindeki yatay bosluklarin histogrami
(7743 bosluk):

| bosluk | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 11 | 13 | 14 | 22 | 24 | 27 | 52 | ... |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| adet | 197 | 892 | 5583 | 331 | 17 | 219 | 272 | 95 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | ... |

Metin ici en genis bosluk 14, sonraki deger 22. BOSLUK_ESIK = 18 ile bant
x-gruplara bolunur ve EN SOLDAKI yeterince genis grup (>=30 px) alinir.
Grup olcumu (13 sayfa): baslik grubu w 49..203, dolluk 0.17-0.32; ibre
grubu w 6..17, dolluk 0.34-0.76. 17 ile 49 arasinda net bosluk var.

("Murekkebi en cok grubu al" kurali DENENDI ve YANLIS cikti: dolu ibre,
ince harf govdelerinden daha cok murekkep tasiyor ve ACILAR blogunda
konu adinin yerine gecti.)

#### Kumeleme ve okuma

Ikili maskeyi md5'lemek ise yaramadi: baslik kaynakta yalnizca 7-12 piksel
yuksekliginde; 24 piksele buyutup esiklemek alt-piksel farklarini buyuk bit
farklarina ceviriyor (AYNI baslikta bile IoU 0.65). Esikleme birakildi;
kirmizilik GRI YOGUNLUK olarak tutuldu, 192x24'e olceklendi ve Pearson
korelasyonuyla kiyaslandi.

626 sayfa icin baglanti-bileseni kumelemesi (esik 0.80) -> 74 kume,
20 tek sayfalik. Her kumeden en fazla 3 uye (kume ici yayilmis) 8 montaja
dokuldu ve okundu; kume ici tutarsizlik YOK.

Okuma 17 konu adi verdi; 12 kume konu bandi degil (bolum kapagi,
"MADE BY UcDortBes" damgasi, "AYT TARZINDA" ayraci, sekil kalintisi).

#### Sifir serbestlik dereceli dogrulama

Okuyucuya beklenen konu ya da kosu sayisi SOYLENMEDI. 17 ad, sayfa
sirasinda tam 17 KOSU olusturdu -- her konu kitapta BIR KEZ acilip
kapaniyor, hicbir konu baska bir blogun icinde gorunmuyor. Yanlis okunan
tek bir kume, bir blogun ortasinda yabanci bir kosu yaratirdi; olmadi.

| cilt | blok | konu |
|---|---|---|
| c1 | 6-43 | ACILAR |
| c1 | 44-93 | OZEL UCGENLER |
| c1 | 94-141 | BENZERLIK |
| c1 | 142-195 | UCGENDE YARDIMCI ELEMANLAR |
| c1 | 196-233 | UCGENDE ALAN |
| c1 | 234-287 | GENEL DORTGENLER - YAMUK |
| c1 | 288-352 | PARALELKENAR ESKENAR DORTGEN - DELTOID |
| c1 | 353-414 | DIKDORTGEN - KARE |
| c1 | 415-440 | COKGENLER |
| c2 | 5-45 | CEMBERDE ACI |
| c2 | 46-97 | CEMBERDE UZUNLUK |
| c2 | 98-131 | DAIREDE ALAN |
| c2 | 132-161 | NOKTA ANALITIGI |
| c2 | 162-213 | DOGRU ANALITIGI |
| c2 | 214-247 | DONUSUMLER |
| c2 | 248-279 | CEMBER ANALITIGI |
| c2 | 280-336 | KATI CISIMLER |

#### Bandsiz sayfalar tahmin EDILMEDI, OKUNDU

Blok siniri "bir sonraki blogun basindan onceki sayfa" diye alindi. Bu
kural sinanmadan kabul edilmedi: bloklarin arasinda kalan ve soru tasiyan
37 sayfanin UST SERIDI tek tek okundu. Hepsi ara sayfa cikti -- "ORIJINAL
SORULAR" (+ MADE BY damgasi), "TYT/AYT TARZINDA", "Klasiklesmis Sorular",
"OSYM TADINDA SORULAR" -- ve hepsi bir ONCEKI bloga ait.

ACILAR blogu ozel durum: c1/6-17 ve c1/35-41 sayfalarinda ACILAR bandi VAR
ama band soluk basildigi icin murekkep esigini gecmiyor. O 12 sayfa da tek
tek okundu: 10'unda ACILAR bandi goruldu, 2'sinde ("TYT TARZINDA") konu
bandi yok. Gizli 18. konu YOK.

Sonuc: 2743 sorunun 2743'u bir konu blogunun icinde.

#### Agaca baglama: 10 yaprak + 7 unite

Mevcut GEO agaci 0020'den beri yayinevinden bagimsiz (5 unite, 31 yaprak).
Kitabin 17 bandinin 10'u bir yapraga birebir karsilik geliyor. Kalan 7'si
birden fazla yapragin BIRLESIMI:

| band | karsilik | baglanti |
|---|---|---|
| ACILAR | GEO-U1-DOGRUDA-ACI + GEO-U1-UCGENDE-ACI | GEO-U1 (unite) |
| OZEL UCGENLER | DIK/IKIZKENAR/ESKENAR-UCGEN | GEO-U1 (unite) |
| UCGENDE YARDIMCI ELEMANLAR | ACIORTAY + KENARORTAY | GEO-U1 (unite) |
| GENEL DORTGENLER - YAMUK | GEO-U2-DORTGENLER + GEO-U2-YAMUK | GEO-U2 (unite) |
| PARALELKENAR ESKENAR DORTGEN - DELTOID | PARALELKENAR + ESKENAR-DORTGEN + DELTOID | GEO-U2 (unite) |
| DIKDORTGEN - KARE | GEO-U2-DIKDORTGEN + GEO-U2-KARE | GEO-U2 (unite) |
| DONUSUMLER | DONME + OTELEME + SIMETRI-DONUSUMU | GEO-U4 (unite) |

Bunlar icin yeni yaprak UYDURULMADI -- var olan yapraklarla ortusen sahte
bir yaprak agacin anlamini bozardi. Bu 7 konu UNITE dugumune baglanir ve
`pipeline_metadata.konu_eslesme_duzeyi='unite'` ile isaretlenir; bandin ham
metni her soruda `konu_bandi` olarak durur, yani ileride daha ince bir tur
bu satirlari `--meta-guncelle` ile inceltebilir. Ithal HICBIR migration
gerektirmedi.

Ithal sonucu (canli DB, olculdu): 2708 satir (35'i Mikro Orijinal'de zaten
duran resmi OSYM sorusu, dokunulmadi), 4 tabloda da 2708; is_active 0,
is_public 0, `v_safe_for_beta` 0; koke dusen 0; gorselsiz 0; boyutsuz 0.
Dagilim: GEO-U2 688, GEO-U1 505, GEO-U4 123 (unite) + 10 yaprakta 1392.

#### Bilinen sinir: sinav turu olculmedi

Kitap TYT ve AYT sorularini KARISIK basiyor; `exam_type` ise tek degerli
bir kolon (DB'de yalnizca 'TYT' ve 'AYT' var). Soru duzeyinde sinav turu
OLCULMEDI: "TYT TARZINDA"/"AYT TARZINDA" bantlari yalnizca birkac ara
sayfada var, kitabin govdesi ("KAZANIM ODAKLI SORULAR") hic isaret
tasimiyor. Kardes geometri kitabiyla tutarli olsun diye 'AYT' yazildi ve
durum `pipeline_metadata.sinav_turu_kaynagi` ile isaretlendi. Satirlar
zaten PASIF; duzeltme `--meta-guncelle` ile geriye donuk yapilabilir.

## Bilinen sinirlar (durustce)

- Kirpim bilerek COMERT: kesmek geri donulmez, tasmak degil. Rastgele
  ornekte 9 kirpimin 1'inde onceki sorunun sik satiri ustte gorunuyor.
- 6 soru ozel ele alinmali:
  c1 s30 sag#6 (A ve E sikki ayni "65" -- yeniden okunmali),
  c1 s132 sol#1 (bes sik da okunamadi -> sik_bos),
  c1 s42 sag#2, c1 s381 sag#9, c1 s385 sag#8, c1 s397 sag#6
  (SIKLAR GORSEL -- metin olarak ithal edilemez).
- 11 soruda `[okunamadi]` isareti var (uydurma yerine durust isaretleme).
- F3'un %99.64'u DOGRULUK DEGIL gozlemciler arasi uyumdur; dogruluk
  iddiasi numara surekliligi ve DB hash eslesmesi kanallarina dayanir.

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
`konu_bandi_sifir_serbestlik`. 0018'in `cift_bagimsiz_okuma` sinyali
METNIN iki kez okunmasiydi; bu kitapta F4 metni TEK turda okundu, bu
yuzden o sinyal listeye KONULMADI.

Ithal sirasinda Mikro Orijinal ile carpisan 35 hash sifir serbestlik
dereceli bir dis kontroldur ama 2743'un yalnizca 35'ini kapsar; satir
duzeyinde sinyal gibi yazmak fazla iddia olurdu, listeye girmedi.
