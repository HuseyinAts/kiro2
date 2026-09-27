# 345 2025 TYT Turkce Soru Bankasi -- yontem kaydi

Kaynak: `veriseti/zkitap/screenshots/345 2025 Tyt T\u00fcrk\u00e7e Soru Bankas\u0131`
(FERNUS okuyucu ekran goruntuleri, 440 PNG, 1920x1080). Sayfa karti
(589, 43) - (1331, 1022) = 742x979; basili sayfa = dosya. Soru sayfalari
6-431 (420 sayfa); unite kapaklari 5, 149, 197, 215, 287, 341, 387;
cevap anahtari tablosu 432-439; 440 arka kapak.

Soru cozulmedi; tek cevap kaynagi kitabin basili anahtari.

## 0. Tarama (`tur345tyt_tarama.py`)

`345_2025_tyt_turkce_capa_taramasi.json`: sayfa basina okuyucu simgesi
(sos345tyt ile ayni ikon) ve camgobegi basili soru numarasi, sutun (L/R).

* Okuyucu simgesi bu kitapta soruya degil BLOGA konur: 'OSYM KOSESI'
  kutusu, 'a - b. sorulari asagidaki parcaya gore' ortak parcasi, oncullu
  soru girisi tek simge tasir. Simge 2067, soru 2070.
* Soru capasi basili numaradir: ust bant (y < 112; yapboz 'k. TEST' rozeti,
  'KAZANIM ODAKLI SORULAR' yazisi) ve sayfa numarasi bandi (y >= 915)
  disarida, kutu genisligi <= 16 px: numara 2070 == anahtar hucre sayisi,
  test test esit (207/207).
* Ust bantta 2 simge (s53, s307) sayilmaz.

## 1. Cevap anahtari (`tur345tyt_anahtar.py`)

Kitap sonu tablo (s432-439): konu basliklari altinda 'Kazanim Odakli
Sorular k' (KO), 'OSYM Tadinda Sorular k' (OT), 'Orijinal Sorular k' (OR),
'Karma Sorular k' (KA) satirlari; 207 test (KO 51, OT 98, OR 17, KA 41),
2070 hucre.

* Iki bagimsiz okuma (8 okuyucu; A parcalar ustten / hucreler soldan, B
  parcalar alttan / hucreler sagdan), 2.5x dort parca. A == B 2067 hucre;
  fark 3: s434 PARAGRAF YAPISI Karma 5 #4 (A 'B' / B 'D'), s435 NOKTALAMA
  OSYM 1 #7 (B '?'), s438 CUMLENIN OGELERI OSYM 4 #4 (A '?': numara '1.C'
  diye basili -- kitabin dizgi hatasi). Goz karari (5-6x): B, D, C.
* Piksel glif ucuncu kanal (harf 6 px, 8x8 gri vektor, en-yakin-komsu
  LOO): 2066/2070. Uyumsuz 4: biri goz karari hucresi, 3'u A == B iken
  5x gozle teyit (ZAMIR Orijinal 1 #3 'C', EK FIIL OSYM 1 #10 'D', CUMLE
  CESITLERI Orijinal 1 #8 'A'; kirpim kaymasi / sondaki nokta).
* Testler sirayla basili numaralari tuketir (sayfa, L sonra R, yukaridan
  asagi); birim `TRT345-Tnnn` (anahtar sirasi == kitap sirasi, bolum 2).

## 2. Harita (`tur345tyt_harita.py`) ve agac (0068)

* Ust bant: 420 sayfa iki bagimsiz okuma (tur, no, konu), fark 0.
* Her testin (anahtardan sayfalari) bandi (tur, no) == anahtar; KO / OT /
  OR testlerinde bant konusu (varsa) == anahtar konusu; 201 test 2 sayfa,
  6 test 3 sayfa (Karma 5 / Orijinal 1).
* Icindekiler (dosya 3-4, gozle): 7 unite + 'Karma Dil Bilgisi' (s420);
  27 konunun ilk test sayfasi == icindekiler sayfasi (kapi); unite
  kapaklari araliklarin arasinda (kapi).
* Dugum: KO / OT / OR testi KONU (TUR-345T25-Unn-Kmm, 27), KA testi UNITE
  (TUR-345T25-Unn, 8); KA bant konusu (`karma_konu`: 'SOZCUK VE CUMLE
  ANLAMI', 'PARAGRAF', 'SES - YAZIM - NOKTALAMA', 'ISIM SOYLU SOZCUKLER',
  'FIILLER', 'CUMLE BILGISI', 'ANLATIM BOZUKLUKLARI', 'KARMA DIL BILGISI')
  kayitta.
* 0068_trt345_agac: TUR kokunun altinda 8 unite + 27 konu; yerel tur
  upgrade -> downgrade -> upgrade temiz (35 dugum silinip yeniden eklendi).

## 3. Kirpim kutulari (`tur345tyt_kutu.py`, `tur345tyt_kirp.py`)

`sos345tyt_kutu.py` deseni; capa basili numara (840/840 sutun).

* Blok ustu: onceki numara ile bu numara (+12 px) arasinda simge varsa kutu
  ustu aramasi simgenin ustunden baslar (128 soru: kose kutusu, oncul,
  ortak parca). Simge en yakin ustteki numaraya aittir (s246R: simge
  numaranin 9 px altinda).
* Tavan y 112 (ust bant); 'OSYM KOSESI' etiketi kurali (33 kutu) + etiketin
  yaninda biten onceki sik satiri atlanir (T071_04).
* Ortak parca: 10 grup ('a - b. sorulari asagidaki parcaya gore'; 9 kirmizi
  cerceveli baslik tarandi, 1 kose kutusu icinde gozle). Ilk sorunun
  kirpimi parcayi icerir; sonraki soruya parca ustten eklenir (kirp).
* 2070 kutu, kapi ihlali 0; ortme suphesi 260 soru; kenar kapisi 0.
* Gorsel QA: ortak parca, kose, oncullu ve rastgele kirpimlar gozle.

## Testler

`backend/tests/e2e/test_tur345tyt_veri.py` (26): anahtar hamdan birebir,
toplamlar, farklar goz + glif, test turleri; A/B / gereksiz / yabanci /
'?' goz / bicim disi / kimlik / hucre-numara / teyitsiz glif mutasyonlari;
harita hamdan birebir, sayilar, bant (tur, no) / konu / icindekiler / A-B
mutasyonlari; migration == harita, kimlik; kutu kapilari, kutu <-> cevap,
blok ustu, kose yan satir, ortak parca, tavan.
