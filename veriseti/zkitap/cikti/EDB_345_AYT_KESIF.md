# 345 2025 AYT Turk Edebiyati Soru Bankasi -- FAZ 0 KESIF FISI

Tarih: 25 Eyl 2026. Salt okunur olcum; hicbir soru cozulmedi, DB'ye
yazilmadi. Olcum scriptleri git disi (`backend/_e345_gecici/`).

Secim gerekcesi: `ZKITAP_KITAP_DURUMU.md` bolum 4'te 345 ailesinin
siradaki ISLENEBILIR satiri.

## K0.0 -- YAKALAMA

Tek klasor: `345 2025 Ayt Turk Edebiyati Soru Bankasi`, 348 PNG
(1920x1080). Baska baski/yakalama YOK (kurtarma kanali yok).
Dosya 329-348, dosya 328'in piksel-ozdes kopyasi (okuyucu son sayfada
takilmis; durum raporundaki '20 sayfa art arda ayni' notu bu).
Icerik: dosya 1-328.

## K0.1 -- SAYFA KARTI

Kart (589, 43, 1331, 1020) = 742x977, 345 MAT/KIM ile ayni. Basili sayfa
numarasi = dosya numarasi. Sayfa basina `.json` dosyalari bos labelme
kaliplari (etiket yok).

## K0.2 -- ICINDEKILER (dosya 3-4)

**10 unite, 46 konu** (unite 10 = Genel Bakis Testleri, konusu yok).
Unite ayraclari: 5, 39, 71, 113, 147, 191, 221, 255, 275, 299.
Tam liste: `345_2025_ayt_edebiyat_konu_haritasi.json`.

## K0.3 -- SAYFA TURU VE CEVAP KAYNAGI

* Sayfa alti cevap seridi YOK (KIM/MAT'tan farkli). Cevaplar kitap sonunda
  ('Cevaplar', dosya 321-328): konu basina satir, satirda
  `Kazanim Odakli Sorular N`, `OSYM Tadinda N`, `Orijinal`, `Karma N`,
  unite 10'da `Genel Bakis Testleri 1-10`.
* Her soru sayfasinin ust bandi test turunu (logo) ve sirasini basar;
  devam sayfalari tekrarlar. 148 test: 138 iki sayfa, 10 uc sayfa.
* Soru numarasi / okuyucu simgesi 345 ailesiyle ayni renk ve yerde.

## K0.4 -- ORTAK METIN

Kirmizi cerceveli baslik ('7 - 8. sorulari asagidaki parcaya gore
cevaplayiniz.') altinda birden cok soruya ait parca: 11 adet, hepsi
sutun basinda (Faz 1'de olculdu, bkz. YONTEM bolum 3).

## K0.5 -- DB'DE BU KITAP (salt okunur, 25 Eyl)

`source_book` ILIKE '345%edebiyat%': **0 satir** (eski hat yok).
`subject_area` degeri `EDEBIYAT` (DB'de 1621 satir: BS 2024 AYT Edebiyat
1597, OSYM 2025 AYT 24). EDB kok konusu var (alt dugumler baska kitaplarin
agaclari).

## K0.6 -- KARAR: GIT

Engelleyici bulgu yok. Hat 345 AYT Kimya hattinin kopyasi; farklar:

1. Cevap kaynagi kitap sonu anahtar -> soru/sayfa/sutun konumu bant
   okumasi + sutun basina basili numara sayisindan turetilir.
2. Ortak metinler ayri kutu + ayri okuma, kapsamdaki sorularin govdesine.
3. Test turleri 5 (K, O konu duzeyi; R, M, G unite duzeyi).
