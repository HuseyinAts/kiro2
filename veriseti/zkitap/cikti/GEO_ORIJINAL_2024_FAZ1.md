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

Harita dugumlerinde: `test_sayisi` (rozetten), `test_sayisi_icindekiler`
(denetim), `test_bas_sayfalari` (her testin ilk sayfasi). Sonuncusu Faz 3'te
birim -> sayfa eslemesini elle kurmayi gereksiz kilar.

OSYM bolumleri neden ayri dugum: onceki kitaplarin haritalarinda OSYM sayfalari
bir onceki konunun araligina katilmisti. Burada katilmadi -- OSYM bolumu tum
bolumun konularindan soru tasiyor, tek bir alt konuya yazilmasi yanlis etiket
uretirdi.

## 9. Faz 1 kapilari -- mutasyonla olculdu

`backend/tests/e2e/test_orijinal_geo_harita.py` (23 test); canli DB de sayfa
goruntusu de istemez.

19 bozma denendi, her biri dosyanin kendisinde yapilip sonra geri yazildi:

    temiz durum: YESIL
    toplam 19 mutasyon, 0 kacan
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
