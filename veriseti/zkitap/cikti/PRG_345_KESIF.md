# 345 2025 Paragraf Sifir Risk Soru Bankasi -- FAZ 0 KESIF FISI

Tarih: 25 Eyl 2026. Salt okunur olcum; hicbir soru cozulmedi, DB'ye
yazilmadi. Olcum scriptleri git disi (`backend/_p345_gecici/`).

Secim gerekcesi: `ZKITAP_KITAP_DURUMU.md` bolum 4'te 345 ailesinin
siradaki ISLENEBILIR satiri.

## K0.0 -- YAKALAMA

Tek klasor: `345 2025 Paragraf Sifir Risk Soru Bankasi`, 368 PNG
(1920x1080) + yalniz ekran goruntusu JPEG'lerinden olusan bir PDF (metin
katmani yok). Baska baski/yakalama YOK (kurtarma kanali yok).
Icerik: dosya 3-355; kitap sonu cevap anahtari: dosya 356-368.

## K0.1 -- SAYFA KARTI

Kart (589, 43, 1331, 1020) = 742x977, 345 ailesiyle ayni. Basili sayfa
numarasi = dosya numarasi.

## K0.2 -- BOLUMLER (icindekiler yerine bolum ayraclari)

**7 bolum** ('Sifir Risk 01-07'), ayrac sayfalari 3, 63, 123, 183, 251,
283, 329: Kesfet, Olc, Planla, Odaklan, Zenginlestir, Basar, Riskleri
Sifirla (tam adlar `345_2025_paragraf_konu_haritasi.json`). Bolumler konu
degil calisma asamasidir; mevcut TUR agaclariyla (TUR-BS*, TUR-D*)
ortusmez.

## K0.3 -- TEST YAPISI VE CEVAP KAYNAGI

* 85 test, 1012 soru: bolum 1-3 9'ar test x 20; bolum 4 Kondisyon 1-3
  (8'er), Odaklanma 1-7 (20'ser), OSYM Cikmis Sorular Ozel Denemesi (30,
  s242-250); bolum 5 15 temali test (s252-282); bolum 6 'OSYM Tadinda
  Sorular 1-22' (s284-328); bolum 7 10 test.
* '6. NUANS TESTI' (s340-343) acik uclu, anahtarda YOK -> kapsam disi.
* Sayfa alti cevap seridi YOK; cevaplar kitap sonunda: 356-364 kartli
  sayfalar, 365-368 tablo sayfalari.
* Soru numaralari SIYAH (345 AYT kitaplarindaki camgobegi degil); okuyucu
  simgesi ayni FERNUS glifi, 13x13.
* Tam genislikli tek sutun sayfalar: 348, 350-353, 355.

## K0.4 -- ORTAK METIN

Koyu cerceveli baslik ('7 - 8. sorulari asagidaki parcaya gore
cevaplayiniz.') altinda birden cok soruya ait parca; ilk taramada 26,
Faz 1'de 29 + 1 cercevesiz yonerge = 30 (bkz. YONTEM bolum 3).
'Algisal Butunluk Testi' parcalari BILEREK bulaniklastirilmis (tasarim).

## K0.5 -- DB'DE BU KITAP (salt okunur, 25 Eyl)

`source_book` = '345 2025 Paragraf Sifir Risk Soru Bankas<U+0131>':
**8 eski hat satiri** (7 TURKCE, 1 SOSYAL; hepsi aktif). ASCII ad ile ayni
normalize anahtara cozuluyor -> ad duzeltmesi gerekir (0054).
`subject_area` 'TURKCE' (3105 satir, TYT). TUR kok konusu var.

## K0.6 -- KARAR: GIT

Engelleyici bulgu yok. Hat 345 AYT Turk Edebiyati hattinin kopyasi;
farklar:

1. Siyah numara + 13x13 simge (tarama esikleri yeniden olculdu).
2. Konu agaci yerine 7 bolum dugumu (0055).
3. Eski hat 8 satiri: ad duzeltmesi (0054), cevaplar basili anahtarla
   karsilastirilir, satirlara baska dokunulmaz.
