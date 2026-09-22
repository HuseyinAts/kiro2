# Orijinal 2024 TYT-AYT Geometri Soru Bankasi -- FAZ 1 (test haritasi)

Tarih: 22 Eyl 2026
Onceki adim: `GEO_ORIJINAL_2024_KESIF.md` (Faz 0 fisi, karar GIT)

Faz 0 fisinin Faz 1 icin yazdigi talimat aynen suydu:

> Faz 1'in ILK isi, test haritasini piksel dedektoruyle degil icindekiler
> tablosundan kurmak ve iki bagimsiz okuma ile dogrulamak olmali.
> ... sayim otoritesi piksel degil, iki bagimsiz okuma olmali.

Bu belge o isin olcum tutanagidir. Her baslik bir OLCUMdur; hicbiri Faz 0
fisinden kopyalanmadi.

## 1. Kitap kimligi (kunye sayfasindan okundu, s2)

    ORIJINAL TYT - AYT GEOMETRI SORU BANKASI
    ISBN 978-605-06571-8-0
    30. BASKI -- Ozyurt Matbaacilik, ANKARA
    Orijinal Yayinlari

Sozlesme adi (kaynak_sozlesmesi.py'ye eklenecek):

    kaynak  : Orijinal 2024 TYT-AYT Geometri Soru Bankasi
    onek    : ORIJINAL_GEO_2024
    kod oneki: GEO-ORJ24

Ad, ACIL/C1CELL kalibiyla ayni bicimde kuruldu ve normalize anahtari mevcut
hicbir kaynakla cakismiyor (Mikro Orijinal kayitlari farkli anahtar veriyor).

## 2. Test turleri -- kitabin kendi tanimi (s1 semasi + s2 onsozu)

Kitap testleri RENKLE ayirir; onsoz bu renkleri adlandirir:

| renk    | test adi                     | onsozdeki tanim                    |
|---------|------------------------------|------------------------------------|
| sari    | Kazanimlari Ogreten Sorular  | klasik kurallarla cozulen sorular  |
| mavi    | OSYM Tarzi Sorular           | 2018 sonrasi yeni nesil sorular    |
| kirmizi | OSYM Tarzi Orijinal Sorular  | maviden biraz daha zorlayici       |
| turuncu | OSYM'de Cikmis Sorular       | gercek cikmis sorular (yil etiketi)|

Renk sadece baslik bandinda degil, SAYFA NUMARASI ROZETINDE de tasiniyor
(s175 sari, s177 mavi, s178 kirmizi, s428/s432 turuncu). Yani test turu icin
birbirinden bagimsiz iki piksel kanali var.

DIKKAT (Faz 2'ye tasinan risk): turuncu bolumler gercek OSYM sorulari
tasiyor. Canli DB'de zaten `OSYM 2025 TYT` / `OSYM 2025 AYT` kaynaklari var;
0039'da fizik kitaplarinda goruldugu gibi mukerrer aday cikabilir. Bu
bolumler ithal edilmeden once soru_hash carpismasi olculmeli.

## 3. Icindekiler -- iki bagimsiz okuma

Okuma 1: s3 kart kirpimi (734x968 @ (593,46)), tek gorsel, 2x buyutme.
Okuma 2: ayni sayfanin SOL ve SAG sutunlari ayri ayri kirpildi, 3x buyutme.

Iki okuma da JSON'a yazildi ve makineyle karsilastirildi (elle degil):

    okuma1 satir: 35  okuma2 satir: 35
    IKI OKUMA BIREBIR AYNI
    bolum: 5  adli konu: 30  OSYM bolumu: 5  adli test: 226
    sayfa monoton artan: True   ilk sayfa: 8   son sayfa: 428

Bolum bazinda:

| bolum | ad                      | adli konu | test |
|-------|-------------------------|-----------|------|
| 1     | Ucgenler                | 11        | 77   |
| 2     | Cokgenler ve Dortgenler | 8         | 61   |
| 3     | Cember ve Daire         | 3         | 31   |
| 4     | Analitik Geometri       | 4         | 35   |
| 5     | Kati Cisimler           | 4         | 22   |
|       | TOPLAM                  | 30        | 226  |

226, Faz 0 fisinin piksel dedektorunden bagimsiz olarak dogrulandi. Fisin
"gercek sayi 196 ile 244 arasinda" araligi ile tutarli; otorite artik aralik
degil, iki okuma.

OSYM bolumlerinin test sayisi icindekilerde YAZMIYOR; onlar tek birim olarak
sayiliyor. Toplam birim = 226 adli test + 5 OSYM bolumu = 231.

## 4. Basili sayfa <-> dosya sayfasi hizalamasi

Kart ici alt seritteki basili numara 7 bagimsiz noktada okundu:

| dosya        | basili numara |
|--------------|---------------|
| sayfa_0008   | 8             |
| sayfa_0014   | 14            |
| sayfa_0116   | 116           |
| sayfa_0262   | 262           |
| sayfa_0390   | 390           |
| sayfa_0428   | 428           |
| sayfa_0432   | 432           |

OFSET = 0. Mikro TYT Fizik'teki `basili_sayfa_dosya_sayfasiyla_ayni` kapisi
bu kitapta da gecerli; Faz 2'de kapi olarak kodlanacak (7 nokta orneklem
degil, kanit; tam tarama Faz 2'nin isi).

## 5. Haritanin ucuncu kanalla dogrulanmasi (sayfa basliklari)

Icindekilerin verdigi 35 baslangic sayfasinin her birinin baslik bandi
kirpilip okundu:

- 30 adli konu sayfasinin HEPSI "TEST 1" rozeti tasiyor ve baslik metni
  icindekilerdeki konu adiyla ayni konuyu adliyor.
- 5 OSYM sayfasinin HEPSI "OSYM'DE CIKMIS SORULAR" basligi ve turuncu tema
  tasiyor; TEST rozeti tasimiyor.

Yani "icindekilerin verdigi sayfa, o konunun Test 1'inin ilk sayfasidir"
iddiasi 35/35 dogrulandi. Bu, iki okumadan bagimsiz UCUNCU kanaldir.

Basliklardaki yazim icindekilerden bazen kisadir (icindekiler "Temel
Kavramlar ve Dogruda Acilar" <-> sayfa "DOGRUDA ACI"; "Dairede Cevre ve Alan"
<-> "DAIREDE ALAN"). Harita icindekiler yazimini otorite alir; sayfa yazimi
eslesme icin kullanilmaz.

## 6. Birim yapisi -- olculdu (s175-s179 vitrin kesiti)

| sayfa | rozet   | cevap seridi   | sonuc                          |
|-------|---------|----------------|--------------------------------|
| s175  | TEST 1  | yok            | Test 1 basliyor (sari)         |
| s176  | yok     | 12 girdi (1-12)| Test 1 bitiyor -> 12 soru, 2 sayfa |
| s177  | TEST 2  | 4 girdi (1-4)  | Test 2: mavi, 4 soru, 1 sayfa  |
| s178  | TEST 3  | 4 girdi (1-4)  | Test 3: kirmizi, 4 soru, 1 sayfa |
| s179  | TEST 1  | yok            | sonraki konu (Paralelkenar)    |

Cikan uc kural:

1. TEST rozeti YALNIZCA testin ILK sayfasinda var.
2. Cevap seridi YALNIZCA testin SON sayfasinda var; kart ici y ~870-930
   bandinda, x konumu sabit DEGIL (bazen sola, bazen saga yaslaniyor).
3. Test uzunlugu sabit DEGIL: 12 soru/2 sayfa da var, 4 soru/1 sayfa da.
   "Her test 2 sayfadir" varsayimi bu kitapta YANLIS olurdu.

Ek olarak s432'de serit IKI SATIR (1-20). Yani serit bandi tek satir
varsayilamaz -- kirpim sizinti kapisi iki satirlik seridi de hesaba katmali.

## 7. Uretilen harita

`cikti/orijinal_2024_geometri_konu_haritasi.json`
(c1cell_2024_geometri_konu_haritasi.json ile ayni sozlesme)

- 5 bolum, 35 konu dugumu (30 adli konu + 5 OSYM bolumu)
- sayfa kapsami s8-s432, bosluksuz ve cakismasiz (uretim sirasinda iddia
  edilmedi, assert ile dogrulandi)
- her dugumde `test_sayisi` alani var; OSYM dugumlerinde null (icindekiler
  yazmiyor, Faz 2 olcecek)

OSYM bolumleri neden ayri dugum: onceki kitaplarin haritalarinda OSYM
sayfalari bir onceki konunun araligina katilmisti. Burada o yol secilmedi --
OSYM bolumu tum bolumun konularindan soru tasiyor, tek bir alt konuya
yazilmasi yanlis etiket uretir. Ayri dugum, `Bolum adi` parantezinde
tasinarak hangi bolume ait oldugunu kendisi soyluyor.

## 8. Faz 2'ye devredilen olcumler (bu belgede YAPILMADI)

1. TEST rozetinin tum kitapta taranmasi -> 226 rozet cikmali (harita ile
   capraz kontrol; sapma varsa harita degil tarama suclu degil, once ikisi de
   yeniden okunur).
2. Cevap seritlerinin taranmasi -> 231 serit ve serit girdi toplami = okunan
   soru sayisi.
3. Okuyucu simgesi (buyutec) sayimi: Faz 0 fisi 2099 olcmustu; serit
   toplamiyla karsilastirilacak. Esit degilse ithal DURUR.
4. Kirpim kutulari ve sizinti kapisi: kirpim alti, o sayfadaki serit bandinin
   ustunde kalmali (iki satirlik serit dahil).
5. OSYM bolumlerinin canli DB'deki resmi OSYM satirlariyla soru_hash
   carpismasi.
6. Ortme (okuyucu simgesinin soru govdesini kapatmasi) olcumu: Faz 0 fisi
   %2.72 (57 simge) demisti, cogunlugu SOL sutunda. 0039'un dersi geregi
   "ortulu" bayragi tek basina disla(ma)ma karari vermez; ortmenin soru
   metnini mi yoksa yalniz basili numarayi mi kapattigi olculur.

## 9. Faz 1 kapilari -- mutasyonla olculdu

`backend/tests/e2e/test_orijinal_geo_harita.py` (16 test) haritayi ve iki
okumayi dosyadan okur; canli DB istemez.

Kapilarin kendisi de olculdu: 11 bozma denendi, her biri temiz dosyalarin
kopyasi uzerinde degil, dosyanin kendisinde yapilip sonra geri yazildi.

| bozma                                | sonuc     |
|--------------------------------------|-----------|
| okuma2'de bir test sayisi degisti    | yakalandi |
| okuma2'nin kaynagi okuma1 ile ayni   | yakalandi |
| okuma2'de bir sayfa numarasi degisti | yakalandi |
| haritada bir bas_sayfa degisti       | yakalandi |
| haritadan bir konu silindi           | yakalandi |
| haritada bir test_sayisi artti       | yakalandi |
| bir OSYM dugumunun adi degisti       | yakalandi |
| bir OSYM dugumune test sayisi yazildi| yakalandi |
| son sayfa 432 degil                  | yakalandi |
| iki konu ayni kodu tasiyor           | yakalandi |
| konu adinda ASCII disi karakter      | yakalandi |

    temiz durum: YESIL
    toplam 11 mutasyon, 0 kacan
    geri yazma dogrulamasi: YESIL

"okuma2'nin kaynagi okuma1 ile ayni" bozmasi bilerek konuldu: iki okuma ayni
kirpimin kopyasi olsaydi "iki bagimsiz okuma" iddiasi bos kalirdi ve hicbir
veri testi bunu fark etmezdi. Kapi, iddianin kendisini koruyor.
