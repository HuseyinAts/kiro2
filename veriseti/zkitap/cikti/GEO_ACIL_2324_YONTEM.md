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

## Adim 2c -- Kirpim duzeltmeleri ve ORTULU sorularin disarida birakilmasi

Transkripsiyonun ilk 288 sorusu kosunca ajanlar bagimsiz olarak "son sik
kesik" diye rapor etti. Dort kapi da yesildi, yani kapilar bu hatayi
GORMUYORDU. Eklenen besinci kapi olctu: 1881 kirpimin **664'unde** murekkep
sag kenara, **32'sinde** alt kenara degiyordu.

Kok neden tek degil, **uc ayri** seymis.

### (a) Sol sutunun sag siniri: oluk, gx_sag degil

Ilk kural `gx_sag + 1` idi. Simgeler beyazlatildiktan sonra olculdu: iki
sutun arasindaki OLUK her sayfada `gx_sag + 18` ile `+47` arasinda, tam
30 px. Sol sutunun metni en fazla `gx_sag + 17`'ye geliyor. Sinir
`gx_sag + 18` yapildi.

Arada bir yanlis deneme daha belgeleniyor: "ayirici cizgiyi sayfa basina
dedektorle bul". **Cizgi her sayfada yok** (s44, s53, s57'de 340-430
arasinda en uzun dikey kolon 10 px) ve dedektor s44'te bir seklin dikey
kenarina takilip siniri 329'a cekerek E sikkini tamamen kesti. Yapisal
sabit, dedektorden guvenli cikti.

Ilk olcumlerin "metin gx_sag'da bitiyor" demesinin sebebi de anlasildi:
olcum penceresi `x < gx_sag` ile sinirliydi, yani cevabi sorunun icine
koymustu.

### (b) Cevap kutusu SAYFAYI degil SUTUNU sinirlar

Cevap kutusu x 377-393 ile 637-660 arasinda, yani SAG sutunun altinda.
Ilk surum bu limiti iki sutuna da uyguladi; s43'te sol sutunun sik satiri
(y ~892) kutunun disinda kaldi ve o soru siksiz kirpildi. Artik limit
yalniz kutuyla YATAYDA 20 px'ten fazla ortusen sutuna uygulaniyor.

### (c) ORTME: Faz 0'in K0.4 olcumu yapisal olarak yanlisti

s44'un sik satiri 4x buyutulunce goruldu: "A) V7  B) 2V2  C) 3  D) 3V2
E) 5" ve **"5"in uzerinde okuyucunun buyutec diski duruyor**.

Disk OPAK. Altindaki murekkep goruntude zaten yok. Yani "disk icinde
murekkep var mi" diye bakan olcum ortmeyi **hicbir zaman bulamaz**. Faz
0'da "soru metnini ortme olculemedi" sonucuna varmamizin sebebi buydu ve
sonuc yanlisti.

Dogru olcum: bir metin SATIRI diskin icine giriyor mu -- yani diskin
HEMEN SOLUNDA (6 px) kitap murekkebi var mi. Olculdu:

| olcu | deger |
|---|---|
| ortme olayi | **154** |
| etkilenen essiz soru | **151** |
| hepsi | sag sutun simgesi, sol sutun sorusunu ortuyor |

**SAHIP KARARI: bu 151 soru islenmeyecek.** Kutu dosyasinda
`ortulu: true` ile isaretleniyor, kirpim araci onlari atliyor.
Islenecek soru: **1730**.

Kurtarma kanali yok (bu kitabin ikinci bir yakalamasi yok). Okuyucunun
ayar panelinde "Zenginlestirme ve Aktivite Dugmelerini Goster" anahtari
var; kapali yakalanirsa bu ortme sinifi tamamen ortadan kalkar -- sonraki
kitaplar icin not.

### Besinci kapi

`KAPI5`: kutunun DISINDA ama ayni sutunun tavani icinde murekkep kaldi mi.
"Kenarda murekkep var mi" diye sormak yanlis olurdu: icerik oluga kadar
mesru sekilde gidebiliyor.

Ders: **dort kapi da yesilken uc ayri kusur vardi.** Kapilar "kutu bos mu,
tasiyor mu, cakisiyor mu" diye bakar; "dogru yeri mi kapsiyor" sorusunu
ancak gozle ornekleme ve -- bu sefer -- transkripsiyon ajanlarinin
geri bildirimi yakaladi.

## Adim 2d -- Soru numarasini beyazlatan pay (KAPI 6)

Transkripsiyonun ilk 8 partisi (376 soru) kosarken iki ajan ayni sikayeti
getirdi: `s0009_sag_2` ve `s0073_sag_1` kirpimlarinda basili numara **3**
gorunuyordu, oysa sayfa sirasi 8 diyordu. Kaynak goruntude olculdu: her
ikisinde de basili numara **8**. Kirpim uretirken okuyucu diskini
beyazlatan dikdortgenin sag payi `gx+27` idi; numaranin kirmizi glifi ise
`gx+26`'da basliyor. Yani beyazlatma numaranin ilk 1-2 sutununu siliyor ve
"8" gozle "3" oluyordu.

Pay OLCUMLE yeniden secildi. 41 sayfada her simgenin cevresi tarandi:

| olculen sey | deger |
|---|---|
| diskin (golge dahil) en sag sutunu | `gx+22` |
| kirmizi numaranin en sol sutunu | `gx+26` (antialias `gx+25`) |
| numaranin satir araligi | `gy+1 .. gy+15` |

Yeni pay `gx+23`: golgeyi tam kapsar, numaraya 2 px uzak kalir.

**KAPI 6** eklendi: her sayfa icin, beyazlatmadan ONCE, her simgenin
sagindaki kirmizi numaranin sol kenari olculur; `gx + DISK_SAG` bu degere
esit ya da ondan buyukse script DURUR ve hicbir dosya yazmaz (iki gecisli:
once tum sayfalar dogrulanir, sonra kirpim yazilir). Mutasyon dogrulamasi:
pay 27'ye geri cekildiginde kapi tetikleniyor, 23 ile 442 sayfanin
tamami temiz.

Kapinin olcum penceresi iki kez daraltildi, ikisi de yanlis alarmdan:

1. Dikeyde `gy-20 .. gy+34` iken sayfa kenarindaki dondurulmus kirmizi-sari
   "ACIL MATEMATIK" logosunu numara sandi (s6). `gy-2 .. gy+20` yapildi.
2. Yatayda `gx .. gx+60` iken ayni logo serit halinde olugun icinden
   geciyor ve diskin hemen alt/ust ucunda `gx+14` civarinda kirmizi
   birakiyordu (28 yanlis alarm). `gx+22 .. gx+60` yapildi; pencere
   beyazlatmadan onceki goruntude calistigi icin pay 22'yi assa bile
   numara hala gorulur, yani kapi korlesmiyor.

Ilk 8 partinin transkripsiyonu (376 soru) IPTAL edildi ve 1730 kirpimin
tamami yeniden uretildi; transkripsiyon sifirdan baslatildi.

## Adim 3 -- Transkripsiyon (1730 soru)

37 parti, her biri 47 soru (sonuncusu 38). Her partiyi ayri bir ajan
isledi; ajan yalniz kendi gorsellerini gordu, ciktisini dogrudan dosyaya
yazdi ve geriye tek satir ("yazildi: N") dondu -- boylece 1730 sorunun
metni ust baglama hic girmedi.

Ajan kurallari (`GOREV.md`): soruyu COZME, gordugunu aynen kopyala, sekli
metne cevirme (`sekil_var` + tek cumlelik aciklama), okuyamadigini uydurma
(`okunamayan`), basim kusurunu not et (`kaynak_kusuru`), soru numarasini
gorseldeki kirmizi rakamdan al.

### Yapisal kapilar (`acil_geo_metin_kapi.py`)

Hicbir ajan butunu gormedigi icin "sira kaydi / eksik soru / yanlis test"
sinifi hatalar ajan icinde yakalanamaz. Veri seti kitabin KENDI cevap
anahtarina ve kirpim kutularina karsi yedi kapidan gecirilir:

| kapi | ne dogrular |
|---|---|
| 1 | kayit sayisi == kutu - ortulu |
| 2 | veri sette hicbir ortulu kutu yok |
| 3 | gorsel adlari kutu listesiyle birebir |
| 4 | test basina kutu sayisi == cevap sayisi |
| 5 | basili soru numarasi == test ici sira |
| 6 | kaydin cevabi == anahtarin ayni test+sira cevabi |
| 7 | govde dolu, tam 5 sik |

Sonuc: **yedi kapi da gecti** (1730 soru, 138 test, 151 ortulu disarida).
Kapilarin korlugu yedi mutasyonla olculdu (kayit silme, cevap bozma,
numara bozma, govde bosaltma, sik silme, sira bozma, ortulu kutu ekleme):
yedisi de tetikledi.

### Tek numara uyusmazligi -- kitabin kendi hatasi

KAPI 5, `s0185_sag_2` icin basili numarayi 10, test ici sirayi 8 buldu.
Kaynak sayfa acilip bakildi: s185'te numaralar gercekten **5, 6, 7, 10**
gidiyor ve ayni testin bir sonraki sorusu da 10 numarali. Yani kirpim ya
da transkripsiyon hatasi degil, kitabin basim hatasi; kayit
`kaynak_kusuru` alanina yazildi. Kapi, `kaynak_kusuru` dolu olan numara
uyusmazliklarini rapor eder ama dusurmez.

### Veri seti

`acil_2324_geometri_metin.json` -- 1,26 MB, 1730 kayit. Her kayit:
gorsel, sayfa/sutun/sira, test, test_ici_sira, soru_no_basili, cevap,
govde, sikler (A-E), sekil_var, sekil_aciklama, sikler_gorsel,
kaynak_kusuru, okunamayan.

Olculen dagilimlar: sekilli soru 1513 / 1730; gorsel sikli 17;
kaynak_kusuru isaretli 36; okunamayan alani dolu 10.
Cevap dagilimi A 216 / B 300 / C 530 / D 423 / E 261.

## Adim 4 -- Konu agaci (migration 0034)

Kitabin kendi agaci GEO kokunun altina **GEO-ACL24** onekiyle ayri bir alt
agac olarak kuruldu: 6 bolum + 27 konu + 3 alt konu = 36 dugum.

Mevcut `GEO-U1..GEO-U5` agacina DOKUNULMADI. Sebep olculdu: kitapta
"Ozel Ucgenler", "Ucgende Merkezler", "Genel Dortgenler", "Cemberin
Cevresi" dugumleri var, mevcut agacta yok; mevcut agacta "Dik Ucgen",
"Egim", "Esitsizlik Grafikleri" var, kitapta yok. Sessizce "en yakin"
dugume baglamak yanlis veri olurdu (FIZ-345 / FIZ-MO / TUR-BS / EDB-BS
deseninin aynisi).

### Iki bagimsiz kanal

| kanal | ne verdi |
|---|---|
| A: icindekiler (s3) | 6 bolum, 27 konu, her konunun baslangic sayfasi |
| B: 138 testin ILK sayfasindaki ust bant | testin konu adi |

Karsilastirma: **128 test birebir ayni ad**, 10 test ayni adin UZUN hali
("OZEL UCGENLER Pisagor Bagintisi", "Analitik Geometri Karma Testler").
Celisen tek test YOK.

Bandin kendi alt basligi olan uc test (8, 9, 10) icin uc ALT KONU dugumu
acildi; adlari bandin kendisinden geliyor. "Analitik Geometri" konusunun
7 testinin TAMAMI "Karma Testler" bandini tasidigi icin ayri bir alt
dugum ACILMADI -- ebeveyniyle birebir ayni kumeyi kapsayan dugum bilgi
tasimaz.

Ucuncu kontrol: testlerin sayfa sinirlari cevap anahtarindan turetildi ve
icindekilerden gelen konu araliklariyla karsilastirildi -- **138 testin
138'i tek bir konunun icinde kaldi**, konu sinirini asan test yok.

### Dogrulama

  * Yerel Postgres'te `alembic upgrade head` -> 36 dugum eklendi
    (level 2: 6, level 3: 27, level 4: 3).
  * `alembic downgrade -1` -> 36 dugum silindi, `GEO-U*` agacindaki 36
    dugum dokunulmadan kaldi.
  * Yeniden `upgrade head` -> tekrar 36 dugum (tekrarlanabilir).
  * `test_acilgeo_konu_agaci.py`: 14 test. Iki mutasyon denendi --
    migration'da bir dugum adini degistirmek ve haritada bir testi
    yanlis konuya atamak; ikisi de yakalandi.

## Adim 5 -- Ithal araci (`acil_geo_ithal.py`)

Ithal PASIF: `is_active=FALSE`, `is_public=FALSE`, `review_status='PENDING'`.
Aktiflestirme ayri bir karardir. Kaynak adi sozlesmeye eklendi:
`ACIL 2023-2024 TYT-AYT Geometri Soru Bankasi` / onek `ACIL_GEO_2324`.

Script uc dosyayi birlestirir -- ayri bir "ithal veri seti" uretilmez:

| dosya | ne verir |
|---|---|
| `acil_2324_geometri_metin.json` | govde, siklar, cevap, sekil bilgisi |
| `acil_2324_geometri_konu_haritasi.json` | test -> konu dugumu |
| `acil_2324_geometri_kirpim_kutulari.json` | kirpim kutusu (ortulu olanlar HARIC) |

`question_image_url` kirpim script'inin KENDI urettigi adi kullanir
(`ACILGEO_2324/sNNNN_sutun_sira.png`). fiz345'te ad kayit id'siydi, cunku
orada veri seti id'yi zaten tasiyordu; burada kirpim script'i metin
hattindan bagimsiz calisiyor ve hash'i bilmiyor. Ikinci bir adlandirma
semasi uydurmak yerine kirpimin deterministik adi kullanildi.

### Bos sik avi -- 8 kayit

On kontrol iki kayitta "anahtar sikki bos" diye DURDU. Sebep arandi ve
sekiz kayitta bos sik bulundu. Sekizi de kaynakta tek tek acildi:

  * ALTISI okunabiliyordu, transkripsiyon ajani fazla temkinliydi
    (sik goruntunun sag kenarina 3-4 px kala bitiyor). Degerler kaynaktan
    okunup yazildi: s0134 E=2, s0158 E=5/2, s0189 E=4/5,
    s0194 C=(karekok2 - 1), s0197 C="I ve II", s0406 E=9/2.
  * IKISI gercekten bulanik: s0328'de B sikkindeki islem isareti,
    s0380'de E sikkindeki us degeri (5 mi 6 mi ayirt edilemedi).
    UYDURULMADI; `okunamayan` alaninda belgelendi.

s0380'de bulanik sik ANAHTAR sikki. Satir silinmedi: tam soru kirpimi
gercek sikki tasiyor, ogrenci gorselde goruyor. On kontrolun "anahtar
sikki bos" kapisi bu tek durum icin daraltildi -- bos anahtar sikki
yalniz `okunamayan` dolu VE kirpim varsa affedilir; belgelenmemis bos
anahtar hala DURDURUR. Satir `anahtar_sikki_okunamadi` bayragi tasir.

### Yerel olcum (Postgres 5434)

```
veri setinde 1730 soru (ortme yuzunden disarida: 151)
on kontrol: ... TEMIZ
YAZILDI: 1730 yeni satir
DB'de bu ithalin satirlari: toplam 1730, is_active 0, kapidan gecen 0
gorselli: 1730 / 1730     konu kodu: 30
bayraklar: kaynak_dizgi_kusuru 36, konu_alt_konu_duzeyinde 39,
           sik_tekrar 21, sikler_gorsel 17, okunamayan_parca 4,
           sik_bos 2, anahtar_sikki_okunamadi 1
bloom: application 1372, comprehension 358   okunabilirlik ort 90,4
```

### Koruma testleri

`tests/e2e/test_acilgeo_ithal.py` -- 21 test, canli DB istemez. Kapsam:
veri seti butunlugu, **ortulu 151 sorunun ithale girmemesi**, konu
baglantisi (kok dugume dusen kayit yok), kaynak adi sozlesmesi, ithalin
PASIF olmasi, cozumun uydurulmamasi, kirpim/gorsel tutarliligi, kirpim
kutularinin kart icinde kalmasi ve bayrak sayilari.

Bes mutasyon denendi, besi de yakalandi: anahtar sikkini belgesiz
bosaltmak, bir sikki silmek, govdeyi bosaltmak, konu kodunu agac disina
tasimak, ayni soruyu iki kez koymak.

## Sirada ne var

| adim | durum |
|---|---|
| 1. cevap anahtari | **BITTI** (1881 cevap, 3 kanal + simge caprazi) |
| 2. kirpim koordinatlari (simgeden turetilir; tek/cift 18 px kaymasi) | **BITTI** (1881 kutu, dort kapi + gozle ornekleme) |
| 2b. kirpim disa aktarimi (disk beyazlatma dahil) | **BITTI** (1881 gorsel) |
| 2c. kirpim duzeltmeleri + 151 ortulu sorunun disarida birakilmasi | **BITTI** |
| 2d. soru numarasini beyazlatan pay (KAPI 6) | **BITTI** |
| 3. transkripsiyon (1730 soru, 37 parti) | **BITTI** (yedi kapi gecti) |
| 4. konu agaci migration (0034; 6 bolum / 27 konu / 3 alt konu) | **BITTI** |
| 5. ithal araci + e2e testler | **BITTI** (1730 satir PASIF) |

## Olcum dosyalari (git disi, `backend/_geo1_gecici/`)

`_a1_kutu_kirp.py` (138 kutu kirpimi), `_a1_montaj.py` (kanal A/B
montajlari), `anahtar/` (kutu goruntuleri), `montaj_a/`, `montaj_b/`,
`kanal_c*.png`, `okuma_a.json`, `cevap_anahtari.json`, `testler.json`.
