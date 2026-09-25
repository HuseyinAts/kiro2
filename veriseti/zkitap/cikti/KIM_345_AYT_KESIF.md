# 345 2025 AYT Kimya Soru Bankasi -- FAZ 0 KESIF FISI

Tarih: 24 Eyl 2026. Salt okunur olcum: hicbir sayfa transkribe edilmedi,
hicbir cevap satiri okunmadi, DB'ye yazilmadi. Olcum scriptleri git disi
(`backend/_k345_gecici/`).

Secim gerekcesi: `ZKITAP_KITAP_DURUMU.md` bolum 4'te 345 ailesinin
ISLENEBILIR ilk satiri ("345 2024 AYT Kimya Soru Bankasi"); 345 TYT ve
AYT Matematik hatti bu kitapla ayni yayinevi/yil sablonunda.

## K0.0 -- HANGI BASKI (durum raporu DUZELTILIR)

Iki yakalama var, ikisi de 336 PNG (1920x1080) + PDF:

| klasor | kunye (s1) | not |
|---|---|---|
| `345 2024 Ayt Kimya Soru Bankasi` | "2024 - 2025 egitim ve ogretim doneminde" | sekme '2024 - AYT Kimya S...' |
| `345 2025 Ayt Kimya Soru Bankasi` | "2025 - 2026 egitim ve ogretim doneminde" | sekme kutusunda arama metni ('2025 ayt fizik sb') -- sekme basligi guvenilmez |

Durum raporu (bolum 7, #32) 2025 klasorunu '#27'nin kopyasi' sayiyordu.
Olcum: ayni indekste sha256 ozdes sayfa **0/336**; kart piksel farki
medyani %0,10; >%1 fark 29 sayfa. Bunlar:

* s1-s4: kapak/kunye/icindekiler baski yili.
* 12 unite ayraci (s5, 39, 71, 107, 127, 151, 175, 205, 243, 265, 295,
  325; ~%4,8): ayni grafik, piksel kaymasi.
* ~13 soru sayfasi (%1-3): **soru degismis**. Gozle s35: 9. soru
  2024'te periyodik sistem grafigi sorusu, 2025'te 'AYT - 2025' cikmis
  sorusu; alt cevap satiri da farkli. 345 AYT Fizik'teki desenin aynisi.

Sonuc: iki ayri baski, kopya DEGIL. **2025 islenir** (guncel, cikmis
sorulari guncellenmis); 2024 islenmez, ortme kurtarma kanalidir. 2024'te
olup 2025'te olmayan ~13 soru borc olarak izlenir.

## K0.1 -- SAYFA KARTI

6 ornek sayfada (7, 20, 60, 150, 250, 330) sutun/satir profili ayni:
sol golge x 583-588, sag golge x 1331-1339, ust cizgi y 42, alt bosluk
y 1014-1019 -> kart **(589, 43, 1331, 1020) = 742x977**, 345 TYT/AYT
Matematik ile birebir ayni. Basili sayfa numarasi = dosya numarasi.

## K0.2 -- ICINDEKILER (s3-s4)

**12 unite, 50 konu**, basili baslangic sayfalariyla (goz ile okundu):

| unite | ad | konular (sayfa) |
|---|---|---|
| 01 | Modern Atom Teorisi | Atomun Kuantum Modeli 6, Elektron Dizilimleri 12, Periyodik Ozellikler 16, Elementleri Taniyalim 22, Yukseltgenme Basamaklari 26 |
| 02 | Gazlar | Gazlarin Ozellikleri 40, Gaz Yasalari 42, Ideal Gaz Yasasi 46, Gazlarda Kinetik Teori 50, Gaz Karisimlari 52, Gercek Gazlar 58 |
| 03 | Sivi Cozeltiler ve Cozunurluk | Cozucu-Cozunen Etkilesimleri 72, Derisim Birimleri 74, Koligatif Ozellikler 82, Cozunurluk 90, Cozunurluge Etki Eden Faktorler 92 |
| 04 | Kimyasal Tepkimelerde Enerji | Tepkimelerde Isi Degisimi 108, Entalpi Turleri 112, Bag Enerjileri 116, Tepkime Isilarinin Toplanabilirligi 118 |
| 05 | Kimyasal Tepkimelerde Hiz | Kimyasal Tepkimeler ve Carpisma Teorisi 128, Tepkime Hizi 130, Tepkime Hizini Etkileyen Faktorler 134 |
| 06 | Kimyasal Tepkimelerde Denge | Kimyasal Denge 152, Dengeyi Etkileyen Faktorler 160 |
| 07 | Sulu Cozelti Dengeleri | Asit-Baz 176, Cozunurluk Dengesi 188 |
| 08 | Kimya ve Elektrik | Indirgenme-Yukseltgenme Tepkimeleri 206, Metalik Aktiflik 212, Elektrokimyasal Hucreler ve Elektrot Potansiyelleri 214, Elektroliz 226 |
| 09 | Karbon Kimyasina Giris | Organik ve Anorganik Bilesikler 244, Basit ve Molekul Formul 246, Dogada Karbon 248, Lewis Formulleri 250, Hibritlesme ve Molekul Geometrisi 252 |
| 10 | Organik Bilesikler - 1 | Alkanlar 266, Alkenler 274, Alkinler 280 |
| 11 | Organik Bilesikler - 2 | Aromatik Bilesikler 296, Fonksiyonel Gruplar 298, Alkoller 300, Eterler 304, Karbonil Bilesikleri 306, Karboksilik Asitler 310, Esterler 314 |
| 12 | Enerji Kaynaklari ve Bilimsel Gelismeler | Fosil Yakitlar 326, Alternatif Enerji Kaynaklari 328, Surdurulebilirlik 330, Nanoteknoloji 332 |

Unite ayraclari piksel kanalinda da tam bu 12 sayfa (sag/sol kenar
doygunlugu > 0.3).

## K0.3 -- SAYFA TURU VE CEVAP KAYNAGI

Kitap KONU ANLATIMLI: konu basliklari da okuyucu simgesi tasiyor (s6).
Cevaplar her soru sayfasinin altinda, **sutun basina** kucuk gri punto
('1.E 2.D 3.C' | '4.B 5.E'), kart y **899-904** (345 AYT Matematik ile
ayni bant). Serit dedektoru: y 899-904'te gri murekkep VE hemen ustu
(y 878-897) bos.

| sayfa turu | adet |
|---|---|
| iki sutunda cevap seridi | 233 |
| tek sutunda serit (diger sutun konu anlatimi; ornek s8) | 83 |
| seritsiz (kapak/kunye/icindekiler, 12 ayrac, tam konu anlatimi s6, 108, 206, 252) | 20 |

Yani soru tasiyan sutun sayisi en fazla 549. Soru sayisi Faz 1'de cevap
satirlarinin iki bagimsiz okumasindan gelecek (Faz 0'da tahmin edilmedi;
MAT AYT basili-numara kanali kaba tarama 1507 numara saydi -- alt sinir).

## K0.4 -- OKUYUCU SIMGESI VE KURTARMA KANALI

MAT AYT simge dedektoru degistirilmeden 1376 simge buldu (konu baslik
simgeleri dahil). Her 3. sayfada 2025 simgelerinin 221'i 2024
yakalamasinda ayni yerde, **250'si farkli yerde** -> ortulen metin
buyuk olcude 2024 yakalamasindan okunabilir (kurtarma kanali VAR).
Ortme orani Faz 1'de kirpim adiminda (disk halkasinda kitap murekkebi)
olculecek.

## K0.5 -- SEKIL

Tablolar, orbital/molekul cizimleri, grafikler yaygin; tam soru kirpimi
zorunlu (345 hatti zaten kirpimli).

## K0.6 -- DB'DE BU KITAP (salt okunur, 24 Eyl)

Eski hattan **363 satir, hepsi AKTIF ve PUBLIC**, iki klasor adiyla:

| source_book | exam_type | satir | beta gorunumunde | gorselli |
|---|---|---|---|---|
| `345 2024 Ayt Kimya Soru Bankas<U+0131>` | AYT | 52 | 22 | 34 |
| `345 2024 Ayt Kimya Soru Bankas<U+0131>` | TYT (yanlis etiket) | 150 | 144 | 64 |
| `345 2025 Ayt Kimya Soru Bankas<U+0131>` | AYT | 43 | 13 | 34 |
| `345 2025 Ayt Kimya Soru Bankas<U+0131>` | TYT (yanlis etiket) | 118 | 114 | 48 |

Kaynak `kiro2_batch_v4.14e` (gemini-2.5-flash). Ornek: s7 soru 1 cevabi
E -- basili seritle ayni. Modern ithal bu satirlarla soru duzeyinde
kesisecek; mukerrer taramasi ve basili anahtarla celiski kontrolu
(0047 deseni, sahip karari: basili cevap baz alinir) Faz 1'de.

## K0.7 -- KONU AGACI

DB'de KIM agaci yalniz kok + 4 dugum (KIM.ASI, KIM.DEN, KIM.ORG,
KIM.TER). Emsal (MAT-345A25): kitabin kendi agaci ayri onekle
(12 unite + 50 konu) kurulur; sorular konu dugumune baglanir.

## K0.8 -- KARAR: GIT

Engelleyici bulgu yok. Hat, 345 AYT Matematik hattinin (`MAT_345_AYT_YONTEM.md`)
ayni kart, ayni cevap bandi ve ayni simge/numara renkleriyle kopyasi olarak
kurulur. Farklar:

1. Konu anlatimi sutunlari -- kutu yalniz cevap seridi olan sutunda uretilir.
2. 12 unite ayraci + 4 tam konu sayfasi soru disi.
3. 363 aktif eski hat satiri: mukerrer / celiski taramasi zorunlu.
4. 2024 baskisindaki ~13 degismis soru borc.
