# Orijinal 2024 TYT-AYT Geometri Soru Bankasi -- FAZ 1 (test haritasi)

Tarih: 22 Eyl 2026
Onceki adim: `GEO_ORIJINAL_2024_KESIF.md` (Faz 0 fisi, karar GIT)

Faz 0 fisinin Faz 1 icin yazdigi talimat aynen suydu:

> Faz 1'in ILK isi, test haritasini piksel dedektoruyle degil icindekiler
> tablosundan kurmak ve iki bagimsiz okuma ile dogrulamak olmali.
> ... sayim otoritesi piksel degil, iki bagimsiz okuma olmali.

Bu belge o isin olcum tutanagidir. Her baslik bir OLCUMdur; hicbiri Faz 0
fisinden kopyalanmadi.

**Fisin talimati kismen yanlis cikti** ve bu belge nedenini olcumle gosteriyor
(bkz. 6. bolum): icindekiler tablosu kitabin kendi OZETIDIR, olcum degildir.
Iki bagimsiz okuma ayni ozeti iki kez dogru okur; ozetin kendisi hataliysa iki
okuma da ayni hatayi tasir.

## 1. Kitap kimligi (kunye sayfasindan okundu, s2)

    ORIJINAL TYT - AYT GEOMETRI SORU BANKASI
    ISBN 978-605-06571-8-0
    30. BASKI -- Ozyurt Matbaacilik, ANKARA
    Orijinal Yayinlari

Sozlesme adi (kaynak_sozlesmesi.py'ye Faz 3'te eklenecek):

    kaynak   : Orijinal 2024 TYT-AYT Geometri Soru Bankasi
    onek     : ORIJINAL_GEO_2024
    kod oneki: GEO-ORJ24

Ad, ACIL/C1CELL kalibiyla ayni bicimde kuruldu; normalize anahtari mevcut
hicbir kaynakla cakismiyor.

## 2. Test turleri -- kitabin kendi tanimi (s1 semasi + s2 onsozu)

| renk    | test adi                     | onsozdeki tanim                     |
|---------|------------------------------|-------------------------------------|
| sari    | Kazanimlari Ogreten Sorular  | klasik kurallarla cozulen sorular   |
| mavi    | OSYM Tarzi Sorular           | 2018 sonrasi yeni nesil sorular     |
| kirmizi | OSYM Tarzi Orijinal Sorular  | maviden biraz daha zorlayici        |
| turuncu | OSYM'de Cikmis Sorular       | gercek cikmis sorular (yil etiketi) |

Renk yalniz baslik bandinda degil, SAYFA NUMARASI ROZETINDE de tasiniyor
(s175 sari, s177 mavi, s178 kirmizi, s428/s432 turuncu). 425 sayfanin tamami
tarandi ve rozet renginde tam 4 kume cikti; yani test turu icin birbirinden
bagimsiz iki piksel kanali var.

DIKKAT (Faz 2'ye tasinan risk): turuncu bolumler GERCEK OSYM sorulari tasiyor.
Canli DB'de zaten `OSYM 2025 TYT` / `OSYM 2025 AYT` kaynaklari var; 0039'da
fizik kitaplarinda goruldugu gibi mukerrer aday cikabilir. Bu bolumler ithal
edilmeden once soru_hash carpismasi olculmeli.

## 3. Icindekiler -- iki bagimsiz okuma

Okuma 1: s3 kart kirpimi (734x968 @ (593,46)), tek gorsel, 2x buyutme.
Okuma 2: ayni sayfanin SOL ve SAG sutunlari ayri ayri kirpildi, 3x buyutme.

Iki okuma da JSON'a yazildi ve makineyle karsilastirildi (elle degil):

    okuma1 satir: 35  okuma2 satir: 35
    IKI OKUMA BIREBIR AYNI
    bolum: 5  adli konu: 30  OSYM bolumu: 5  adli test: 226
    sayfa monoton artan: True   ilk sayfa: 8   son sayfa: 428

Iki okuma da cikti olarak saklandi
(`orijinal_2024_geometri_icindekiler_okuma{1,2}.json`), boylece "iki okuma"
iddiasi dosyaya bagli ve denetlenebilir.

## 4. Basili sayfa <-> dosya sayfasi hizalamasi

Kart ici alt seritteki basili numara 7 bagimsiz noktada okundu:
s8, s14, s116, s262, s390, s428, s432 -- hepsinde basili numara dosya
numarasina esit. **OFSET = 0.**

Mikro TYT Fizik'teki `basili_sayfa_dosya_sayfasiyla_ayni` kapisi bu kitapta da
gecerli; Faz 2'de tam tarama ile kapi olarak kodlanacak.

## 5. Haritanin ucuncu kanalla dogrulanmasi (sayfa basliklari)

Icindekilerin verdigi 35 baslangic sayfasinin her birinin baslik bandi
kirpilip okundu:

- 30 adli konu sayfasinin HEPSI "TEST 1" rozeti tasiyor ve baslik metni
  icindekilerdeki konuyu adliyor.
- 5 OSYM sayfasinin HEPSI "OSYM'DE CIKMIS SORULAR" basligi ve turuncu tema
  tasiyor; TEST rozeti tasimiyor.

"Icindekilerin verdigi sayfa, o konunun Test 1'inin ilk sayfasidir" iddiasi
**35/35** dogrulandi.

Basliklardaki yazim icindekilerden bazen kisadir (icindekiler "Temel Kavramlar
ve Dogruda Acilar" <-> sayfa "DOGRUDA ACI"; "Dairede Cevre ve Alan" <->
"DAIREDE ALAN"). Harita icindekiler yazimini otorite alir.

## 6. ICINDEKILER IKI YERDE YANLIS -- rozet taramasi (asil bulgu)

Kart ici (575,45)-(700,120) kutusundaki ACIK GRI DISK pikselleri 425 sayfada
sayildi. Kalibrasyon: bilinen rozetli 8 sayfada 1554-1571, bilinen rozetsiz 6
sayfada 269-375. Esik 1000; sonuc 1000-1300 araliginda hic degismiyor (226).
Yani dedektor esige hassas degil -- Faz 0'in uyardigi tuzaga dusmuyor.

Sonuc: **226 rozet**, icindekilerin verdigi 226 ile ayni. Ama konu bazinda
DAGILIM ayni degil:

| konu                            | rozet | icindekiler |
|---------------------------------|-------|-------------|
| B01-02 Ucgende Acilar           | 8     | 9           |
| B01-11 Ucgende Aci-Kenar Bag.   | 5     | 4           |
| (diger 28 konu)                 | ayni  | ayni        |

Iki sapma ZIT YONLU. Toplam iki kanalda da 226 cikiyor; **toplamin tutmasi
dagilimin dogru oldugunu gostermiyor.** Toplama bakip gecseydik iki yanlis
konu atamasi sessizce ithal edilecekti.

Hangisi dogru? Sayfa. Uc kanit:

1. Sapan iki konunun son rozetleri elle okundu: s27'de "TEST 8" yaziyor
   (icindekiler 9 diyor), s144'te "TEST 5" yaziyor (icindekiler 4 diyor).
2. Ayni kontrol 30 adli konunun HEPSINDE yapildi: her konuda
   **rozet sayisi == son rozetin uzerindeki numara**. Yani rozet dizisi
   1..N kesintisiz; eksik ya da fazla rozet yok.
3. Icindekiler satirlari 5x buyutmeyle yeniden okundu; yazim gercekten
   "(Test 1-2-3-4-5-6-7-8-9)" ve "(Test 1-2-3-4)". Okuma hatasi degil,
   kitabin dizgi hatasi.

**Haritada otorite bu yuzden rozet:** `test_sayisi` rozetten gelir,
`test_sayisi_icindekiler` denetim icin yaninda durur.

Genel ders (ZKITAP_ISLEME_PLANI 8.2 madde 22): basili bir icindekiler tablosu
bir OZETTIR, olcum degildir. Iki bagimsiz okuma okuma hatasini eler, kaynagin
kendi hatasini elemez. Sayim otoritesi her zaman birimin uzerindeki kendi
kimligidir.

## 7. Birim yapisi -- olculdu (s175-s179 vitrin kesiti)

| sayfa | rozet  | cevap seridi    | sonuc                            |
|-------|--------|-----------------|----------------------------------|
| s175  | TEST 1 | yok             | test basliyor (sari)             |
| s176  | yok    | 12 girdi (1-12) | test bitiyor -> 12 soru, 2 sayfa |
| s177  | TEST 2 | 4 girdi (1-4)   | mavi, 4 soru, 1 sayfa            |
| s178  | TEST 3 | 4 girdi (1-4)   | kirmizi, 4 soru, 1 sayfa         |
| s179  | TEST 1 | yok             | sonraki konu (Paralelkenar)      |

Uc kural:

1. TEST rozeti YALNIZCA testin ILK sayfasinda var.
2. Cevap seridi YALNIZCA testin SON sayfasinda var; kart ici y ~870-930
   bandinda, x konumu sabit DEGIL (bazen sola, bazen saga yaslaniyor).
3. Test uzunlugu sabit DEGIL: 12 soru/2 sayfa da var, 4 soru/1 sayfa da.
   "Her test 2 sayfadir" varsayimi bu kitapta YANLIS olurdu.

Ek olarak s432'de serit IKI SATIR (1-20). Kirpim sizinti kapisi tek satirlik
serit varsayamaz.

Ham murekkep sayimiyla serit aramak ISE YARAMADI: y 855-945 bandinda 425
sayfanin 424'u esigi asiyor, cunku soru metni de o banda giriyor. Serit
dedektoru Faz 2'de YAPISAL olmali (kisa jeton dizisi + genis bosluk deseni),
esik tabanli degil. Bu, olumsuz bir olcum olarak buraya yazildi.

## 8. Uretilen cikti

| dosya | ne |
|-------|----|
| `orijinal_2024_geometri_konu_haritasi.json` | 5 bolum, 35 dugum, s8-s432 bosluksuz |
| `orijinal_2024_geometri_icindekiler_okuma1.json` | okuma 1 (tam sayfa kirpim) |
| `orijinal_2024_geometri_icindekiler_okuma2.json` | okuma 2 (sutun kirpimi) |
| `orijinal_2024_geometri_rozet_taramasi.json` | 425 sayfanin rozet olcumu + esik gerekcesi |
| `orijinal_2024_geometri_serit_taramasi.json` | cevap seridi yapisal taramasi (231 sayfa) |
| `orijinal_2024_geometri_birim_haritasi.json` | 231 birim: bas, son, tur, soru ve simge sayisi |
| `orijinal_2024_geometri_simge_taramasi.json` | 2099 okuyucu simgesinin kart ici konumu |
| `orijinal_2024_geometri_kirpim_kutulari.json` | 2072 soru kutusu (kart ici) |
| `orijinal_2024_geometri_ortme_olcumu.json` | 2099 simgenin altinda icerik var mi |
| `orijinal_2024_geometri_sayfa_numarasi.json` | 425 sayfanin basili numara basamak sayisi |

Harita dugumlerinde: `test_sayisi` (rozetten), `test_sayisi_icindekiler`
(denetim), `test_bas_sayfalari` (her testin ilk sayfasi). Sonuncusu Faz 3'te
birim -> sayfa eslemesini elle kurmayi gereksiz kilar.

OSYM bolumleri neden ayri dugum: onceki kitaplarin haritalarinda OSYM sayfalari
bir onceki konunun araligina katilmisti. Burada katilmadi -- OSYM bolumu tum
bolumun konularindan soru tasiyor, tek bir alt konuya yazilmasi yanlis etiket
uretirdi.

## 9. Faz 1 kapilari -- mutasyonla olculdu

`backend/tests/e2e/test_orijinal_geo_harita.py` (63 test); canli DB de sayfa
goruntusu de istemez.

51 bozma denendi, her biri dosyanin kendisinde yapilip sonra geri yazildi:

    temiz durum: YESIL
    toplam 51 mutasyon, 0 kacan
    geri yazma dogrulamasi: YESIL

Bozmalardan ucu bilerek "iddiayi koruyan" kapilari hedefliyor:

- **okuma2'nin kaynagi okuma1 ile ayni** -- iki okuma ayni kirpimin kopyasi
  olsaydi "iki bagimsiz okuma" bos bir iddia olurdu.
- **bilinen sapma gizlendi** / **ucuncu sapma eklendi** -- 6. bolumdeki iki
  sapma tam olarak o ikisi; biri sessizce duzelir ya da yenisi cikarsa test
  kirmizi olur.
- **rozetli listesi elle duzenlendi** -- rozetli sayfa listesi ham olcumden
  turetilebilir olmali; elle dokunulursa yakalanir.

## 10. Faz 2'ye devredilen olcumler (bu belgede YAPILMADI)

1. Cevap seritlerinin YAPISAL dedektoru (esik degil desen) -> 231 birim;
   serit girdi toplami = okunan soru sayisi.
2. Buyutec simgesi sayimi (Faz 0 fisi: 2099) ile serit toplaminin esitligi.
3. Basili sayfa numarasinin 425 sayfada tam taranmasi (7 nokta kanit, tarama
   degil).
4. Kirpim kutulari ve sizinti kapisi: kirpim alti, o sayfadaki serit bandinin
   ustunde kalmali (iki satirlik serit dahil).
5. Turuncu OSYM bolumlerinin canli DB'deki resmi OSYM satirlariyla soru_hash
   carpismasi.
6. Ortme olcumu: Faz 0 fisi %2.72 (57 simge) demisti, cogunlugu SOL sutunda.
   0039'un dersi geregi "ortulu" bayragi tek basina dislama karari vermez;
   ortmenin soru metnini mi yoksa yalniz basili numarayi mi kapattigi olculur.
7. Test turu (sari/mavi/kirmizi/turuncu) her birime yazilmali -- iki bagimsiz
   renk kanali var (baslik bandi ve sayfa numarasi rozeti); ikisi uyusmuyorsa
   o sayfa durdurulur.

## 11. FAZ 2 ilk kapanis: birim haritasi (iki kanal ortusuyor)

10. bolumun 1. maddesi bu belgede yapildi. Sonuc 8. bolumdeki konu
haritasini da DUZELTTI; asagisi o duzeltmenin tutanagi.

### 11.1 Serit dedektoru: esik degil desen

7. bolumde ham murekkep sayiminin ise yaramadigi yazilmisti (ayni bantta 425
sayfanin 424'u esigi asiyor). Ayirt edici buyukluk MIKTAR degil BICIM:

- blok bandin kenarina degmiyor (degen blok, banda kirpilmis bir metin satiri)
- satir yuksekligi <= 8 px (soru metni satirlari 11-20)
- en genis murekkep kosusu <= 8 px (soru metninde harfler birlesip 10-12 verir)
- jeton sayisi >= 8

Ilk surumde kosu siniri 6 idi ve s417'nin seridi kaciyordu (iki glif birlesip
7 vermis). Kacak, birim kapanisi capraz kontrolunde ortaya cikti -- dedektor
kendi basina "231 buldum" demiyor, rozet kanaliyla kapanmak zorunda.

### 11.2 Iki kanal birebir kapaniyor

    birim baslangici (TEST rozeti + OSYM bolum basi) : 231
    birim sonu (cevap seridi)                        : 231
    eslesmeyen bas                                   : 0
    kullanilmayan serit                              : 0
    birimlere girmeyen soru sayfasi                  : 0

### 11.3 Sekiz sayfa hicbir konuya ait degil

Kapanis, kitabin 8 sayfasinin hicbir birime girmedigini gosterdi:

    149, 150, 260, 261, 321, 322, 388, 389

Sayfalar acilip bakildi: 149 "2. BOLUM" ayraci (bolumun konu listesi + OSYM
yil tablosu), 150 "BILGI NOTLARI" (formul ozeti). Ayni desen dortunde de var.

Bu, 8. bolumdeki konu haritasini duzeltti: OSYM dugumleri bolum ayracini
yutuyordu. Dogrusu:

| dugum | eski | dogru |
|-------|------|-------|
| B01-12 OSYM (Ucgenler)      | s145-150 | s145-148 |
| B02-09 OSYM (Cokgenler)     | s257-261 | s257-259 |
| B03-04 OSYM (Cember)        | s318-322 | s318-320 |
| B04-05 OSYM (Analitik)      | s386-389 | s386-387 |
| B05-05 OSYM (Kati Cisimler) | s428-432 | s428-432 (kitap burada bitiyor) |

UYARI (Faz 2'nin kalan maddelerini dogrudan etkiler): BILGI NOTLARI sayfalari
SORU TASIMIYOR ama OKUYUCU SIMGESI TASIYOR (s150'de 8 tane). Faz 0 fisinin
"2099 simge" sayimi bu sayfalari da iceriyor. Yani
**simge sayisi = soru sayisi denklemi once sayfa turune gore suzulmeden
kurulamaz.** Bu, 10. bolumun 2. maddesinin on kosuludur.

### 11.4 Ucuncu renk kanali: sayfa numarasi rozeti

Sayfa numarasi rozetinin rengi 425 sayfada olculdu ve tam 6 kume verdi:

| renk | sayfa | anlam |
|------|-------|-------|
| (255,203,5/6) sari  | 206 | Kazanimlari Ogreten Sorular |
| (1,174,239) mavi    | 165 | OSYM Tarzi Sorular |
| (236,2,140) pembe   | 29  | OSYM Tarzi Orijinal Sorular |
| (243,112,34) turuncu| 17  | OSYM'de Cikmis Sorular |
| (253,185,52) acik turuncu | 4 | BILGI NOTLARI |
| rozet yok           | 4   | BOLUM AYRACI |

Toplam 425. Bu kanal 11.3'teki 8 sayfayi BAGIMSIZ olarak da isaretliyor:
ayrac sayfalarinda rozet hic yok, bilgi notlarinda rengi farkli. Yani soru
disi sayfalar iki ayri yoldan bulundu (birim kapanisi ve rozet rengi) ve ayni
8 sayfayi verdi.

Her birimin tum sayfalarinin TEK tur tasidigi da dogrulandi (uretimde assert).
Birim turu dagilimi:

    kazanim 103 + osym_tarzi 95 + orijinal 28 = 226 adli test
    osym_cikmis 5                              =   5 bolum sonu
                                                 231 birim

### 11.5 Henuz iddia EDILMEYEN sey

`birim_haritasi.json` her birimde `serit_jetonu` tasiyor (seritteki murekkep
jetonu sayisi, toplam 6026). Bu **cevap sayisi DEGILDIR**: "12." gibi bir
girdi birden fazla jetona bolunebiliyor. Cevap anahtari, seridin jetonlarini
saymakla degil OKUMAKLA cikarilacak (Faz 3). Alan adi bu yuzden `serit_jetonu`;
`cevap_sayisi` demek olculmemis bir sey iddia etmek olurdu.

## 12. FAZ 2 ikinci kapanis: soru sayisi 2072, simge 2099

10. bolumun 2. maddesi. Uc sayi birbirine baglandi ve ucu de acikta kalmadi.

### 12.1 Soru sayisinin otoritesi cevap seridi

Seritteki GIRDI sayisi (jeton degil) sayildi. Jetonlari girdiye bolen kural
olculdu: girdi ICI bosluk <= 8 px, girdi ARASI bosluk >= 20 px; esik 12 ikisi
arasindaki genis boslukta duruyor.

Bir tuzak once buraya dusurdu: sayfa numarasi rozeti SABIT bir x penceresiyle
dislaniyordu; serit o pencereye tasidiginda son girdi kayboluyordu (s13'te 8
yerine 7). Rozet artik rengiyle bulunup YALNIZ kendi kutusu dislaniyor.
Kalibrasyon sayfalarinin onunda da (s13=8, s176=12, s417=8, s432=12+8=20)
basili anahtarla birebir.

    231 birim, toplam serit girdisi = 2072 soru

### 12.2 Simge sayaci: glif rengi + kapama

Iki deneme elendi:

- genis mor maske: glif sayfa cizimleriyle birlesiyordu (1940 buldu, 132 eksik)
- lila diski aramak: disk lila bir bara degince birlesip eleniyordu
  (s145'te 4 yerine 3)

Calisan bicim: glifin TAM rengi (69,39,160), 7x7 kapama ile tek parca, sonra
cevresindeki lila disk orani >= 0.25. Gercek simgelerin hepsi ayni imzayi
veriyor: alan 86, lila orani 0.44-0.51. Esige degil sabit bir desene oturuyor.

    tum kitapta simge = 2099

2099, Faz 0 fisinin verdigi sayinin AYNISI -- bagimsiz bir dedektorle
yeniden uretildi.

### 12.3 Ucu birden kapaniyor

| ne | sayi |
|----|------|
| cevap seridi girdisi (soru)            | 2072 |
| birim sayfalarindaki simge             | 2070 |
| bilgi notlari sayfalarindaki simge     |   29 |
| TOPLAM simge                           | 2099 |

29 simge soru degil: s5, s6, s7 (Bolum 1 bilgi notlari) ve s150, s261, s322,
s389. Bolum ayraci sayfalarinda (149, 260, 321, 388) simge YOK -- Faz 0
fisinin "simgesiz sayfalar" notuyla ayni.

### 12.4 Kalan 2 fark: kitap iki soruda simgeyi basmamis

Soru 2072, birim ici simge 2070. Fark iki birimde, ikisi de 1:

    GEO-ORJ24-B02-01-T01  s151-152  soru 15  simge 14
    GEO-ORJ24-B04-01-T01  s323-324  soru 12  simge 11

Iki sayfa da acilip bakildi: **s151'de 8. sorunun, s323'te 3. sorunun yaninda
okuyucu simgesi YOK.** Dedektor hatasi degil, kitabin dizgisi.

Sonuc, Faz 3 icin bir kural: **soru sayisinin otoritesi cevap seridi, simge
degil.** Simge yalniz kirpim kutusunun yerini soyler; simgesiz iki soruda
kirpim kutusu baska bir yoldan kurulmali (ya da o iki soru ayrica isaretlenip
elle gozden gecirilmeli). `birim_haritasi.json` bu iki soruyu
`simgesiz_sorular` alaninda tasiyor ve test onlari civiliyor.

### 12.5 Bu bolumde YAPILMAYAN

Serit OKUNMADI -- yalnizca girdi SAYISI cikarildi. Cevap anahtari (hangi soru
hangi sik) Faz 3'un isi; bu belgede hicbir cevap iddia edilmiyor.

## 13. FAZ 2 ucuncu kapanis: kirpim kutulari (2072 kutu)

10. bolumun 4. maddesi.

### 13.1 Kural

    kutu ustu = okuyucu simgesinin disk ustu - 6 px
    kutu altu = ayni sutundaki BIR SONRAKI simgenin disk ustu - 8 px
                yoksa sayfanin ALT SINIRI
    alt sinir = o sayfada cevap seridi varsa seridin ust kenari - 4 px
                yoksa 944
    sutunlar  = SOL (30, 349) / SAG (352, 700); 350-351 sutun ayirac cizgisi

Kutu bir sonraki simgeye kadar uzatiliyor, sayfa ortasina kadar DEGIL: soru
yuksekligi sabit degil (olculen dagilim: min 114, medyan 299, max 800 px).

### 13.2 Simgesiz iki sorunun kutusu

7. bolumde kurulan kural simge capasina dayaniyor; 12.4'te kitabin iki soruda
simgeyi basmadigi olculmustu. Ilk gecis bu yuzden 2070 kutu uretti ve s323'te
2. sorunun kutusu 3. soruyu da yutuyordu (goruntuyle dogrulandi).

Bu iki soru icin kutu ustu soru numarasinin ust kenarindan ELLE olculdu:

    s151 sag  "8."  y = 814  ->  kutu ustu 806
    s323 sol  "3."  y = 796  ->  kutu ustu 790

Baska hicbir kutu elle girilmedi. Cikti dosyasi bu iki kutuyu `elle: true` ile
isaretliyor; test "elle girilen kutu sayisi = simgesiz soru sayisi = 2" ve
"elle olmayan her kutunun capasi simge taramasinda var" diye capaliyor.

Bir ara adim burada elendi ve kayda geciyor: soru NUMARASINI (pembe metin)
genel bir capa yapmayi denedim; numara glifleri cok kucuk ve yari saydam
(s8'de "1." icin 11 piksel tam renk), ve ayni pembe "Bilgi:" kutucuklarinda da
kullaniliyor -- ilk denemede s323'te "Bilgi:" etiketini soru numarasi sandi ve
kutuyu yanlis yere boldu. Iki soruluk bir sapma icin guvenilmez bir dedektor
kurmak yerine iki olcum elle alindi.

### 13.3 Kapilar (hepsi otomatik, hepsi mutasyonla olculdu)

- kutu sayisi = soru sayisi (2072)
- her kutu kart icinde, ters degil, en az 40 px yuksek
- kutu x sinirlari sutun sinirlariyla BIREBIR (sutunlar ortusmuyor)
- ayni sayfa+sutundaki kutular cakismiyor
- **sizinti kapisi**: hicbir kutunun altu o sayfadaki seridin ust kenarini
  gecmiyor
- elle olmayan her kutunun capasi simge taramasindaki bir konum
- dosyadaki yukseklik ozeti gercek kutulardan yeniden hesaplanabiliyor

Ayrica goz kontrolu: s8, s100, s151, s176, s280, s323, s410 sayfalari kutular
cizilerek bakildi; kesme ya da tasma yok.

### 13.4 Bundan sonra

Kutular Faz 3'te kirpim uretmek icin hazir. Simge diskinin beyazlatilmasi
(C1CELL'deki KAPI 6: renk degil KONUM tabanli, kitabin kendi mor cizimleri
sagkalsin) Faz 3'e ait; bu belgede yapilmadi.

## 14. FAZ 2 dorduncu kapanis: ortme olcumu (disk beyazlatmak guvenli mi?)

10. bolumun 6. maddesi. Faz 0 fisi "%2.72 (57 simge) ortulu" demisti ve
0039'un dersi geregi bir bayragin tek basina dislama karari vermemesi
gerekiyordu. Sorulan soru su: **simge diskini beyazlatirsak (C1CELL KAPI 6)
altinda soru icerigi kalir mi?**

### 14.1 Olcum dolayli, cunku diskin ALTI gorunmuyor

Diskin altindaki pikseller zaten diskle kapli; oraya bakip "icerik var mi"
denemez. Onun yerine diskin hemen DISINDAKI ince halkaya bakildi (yaricap
17-21 px): disk beyaz zemine basilmissa halka bos olur, bir cizginin uzerine
basilmissa cizgi halkanin iki yanindan gorunur.

### 14.2 Sonuc

| kume | medyan | %95 | %99 | max |
|------|--------|-----|-----|-----|
| soru sayfalari (2070 simge) | 0 | 6 | 18 | 43 |
| soru disi sayfalar (29 simge) | 0 | 105 | 113 | 113 |

Soru sayfalarinda halka >= 20 olan **20 simge** var (%0.97). Bunlarin
**19'u SAG sutunda x=358-390**, biri SOL sutunda x=56. Bu x degerleri
yayinevinin sutun arasindaki soluk filigranina denk geliyor; en yuksek ornek
(s408) buyutulup bakildi: simge, sorunun icerigine degil, kenar bosluguna
basili "Y" logosuna ve dikey "ORIJINAL YAYINLARI" yazisina biniyor.

**Yani hicbir sorunun icerigi simge diskinin altinda kalmiyor; disk
beyazlatmak soru kaybettirmez.** Soru disi sayfalarda (bilgi notlari) halka
105-113'e cikiyor, cunku orada simge baslik bandina bitisik basilmis -- o
sayfalarda zaten soru yok.

### 14.3 Ayrica gorulen (Faz 3'e not)

SAG sutun kutulari x=352'den basliyor ve sutun arasindaki filigran (logo +
dikey yazi) bu araliga giriyor; kirpimlarin sol kenarinda soluk gri bir
filigran gorunebilir. Icerigi kesmemek icin sutun siniri daraltilmadi;
filigran soluk oldugu icin OCR'i bozmasi beklenmiyor, ama Faz 3'te kirpim
kalitesi olculurken bu bilinerek bakilmali.

## 15. FAZ 2 besinci kapanis: basili sayfa numarasi tam tarama

10. bolumun 3. maddesi. 4. bolumde 7 noktada okunmustu; bu bolum taramayi
425 sayfaya yayiyor.

### 15.1 Rakamin DEGERI okunmadi, BASAMAK SAYISI sayildi

Once deger okunmaya calisildi: rozet rengiyle bulundu, icindeki murekkep
rakamlara ayrildi, ayni rakamlar kumelenmeye calisildi. **Ise yaramadi:** her
sayfa ayri bir ekran goruntusu oldugu icin ayni rakam farkli piksel
fazlarinda dusuyor; 1063 glif 118 farkli bit desenine dagildi ve tam esleme
10 kumeye inmedi. Hamming esigiyle kumelemek de 42-88 kume verdi.

Deger okumak yerine her sayfada kac BASAMAK basili oldugu sayildi. Bilesen
etiketleme bitisen rakamlari birlestirdigi icin (s110 -> 2 parca) ayirma
dikey izdusumle yapildi, 6 pikselden genis parcalar esit bolundu.

### 15.2 Basamak sayisi neden yeterli

Tum kitap k kadar kaysaydi, basamak siniri gecilen her yerde (9/10 ve 99/100)
basamak sayisi uyusmazdi. s8-s432 araliginda bu sinirlar var ve **uyusmazlik
sifir** -- yani duzgun bir kaydirma bu olcumle diskanmis oluyor.

    taranan sayfa            425
    basamak sayisi uyusan    421
    uyusmayan                  0
    numarasiz (0 rakam)        4  -> 149, 260, 321, 388

Yerel (tek sayfalik) kaymalar icin uc dayanak daha var: 7 sayfada numara
dogrudan okundu (s8, s14, s116, s262, s390, s428, s432 -- hepsi ofset 0),
her konuda rozet dizisi 1..N kesintisiz, ve serit<->rozet kapanisi 231/231.

### 15.3 Numarasiz dort sayfa

149, 260, 321, 388 -- bolum ayraclari. Uzerlerinde basili sayfa numarasi hic
yok. **Renk kanali da ayni dort sayfayi rozetsiz isaretlemisti** (11.4); iki
bagimsiz olcum ayni dortluyu veriyor.

### 15.4 Ciktinin kendi sinirini soylemesi

`sayfa_numarasi.json` "rakamin DEGERI okunmadi" cumlesini tasiyor ve test
bunu capaliyor. Bir mutasyon bilerek bu cumleyi "her sayfadaki numara okundu"
yapiyor; test kirmizi oluyor. Olculmeyen bir seyin olculmus gibi yazilmasi
kapiyla engelleniyor.
