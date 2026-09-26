# 345 2025 TYT Fizik Soru Bankasi -- kesif olcumleri ve isleme plani

Kaynak: `veriseti/zkitap/screenshots/345 2025 Tyt Fizik Soru Bankasi/`
(klasor adi Turkce 'i' ile biter). DB'de bu kitabin satiri YOK (eski hat
dahil). `ZKITAP_KITAP_DURUMU.md`'de sonraki ISLENEBILIR kitap.
Onek: `FZT345` (birim `FZT345-Tnnn`), kod oneki (Faz 2) `FIZ-345T25`.

## 0. Kesif olcumleri (26 Eyl)

| kalem | deger | kanal |
|---|---|---|
| PNG | 368, 1920x1080 | dosya sayimi |
| kart | (589, 43) - (1331, 1022) = 742x979 | cerceve cizgisi, 10 ornek sayfa ayni |
| basili sayfa | = dosya (s7 altinda '7') | gozle |
| soru sayfasi | 357 | cevap seridi bandi (kart y 899-904) + simge |
| seritsiz | 3-5 (icindekiler), 43/99/161/225/273/315 (ayrac) | piksel |
| seritli simgesiz | 1, 2 (kapak, kunye) | piksel |
| unite | 19 | icindekiler (dosya 3-4), gozle |
| okuyucu simgesi (soru capasi) | 1397 | piksel (stm345 tanimi) |
| cevap seridi girdisi | 1397 (A) = 1397 (B) | iki gorsel okuma |
| test (numara 1'e donus) | 176 | okuma |

Sayfa tasarimi Start Matematik ile ayni aile: lila disk + mor buyutec
simgesi, camgobegi soru numarasi, sutun basina sayfa alti cevap seridi.
Fark: serit fontu 6 px; girdi sayisi pikselden guvenilir cikmiyor
(bosluk histogrami 3-5 px'te vadisiz) -> girdi sayisinin bagimsiz
kanali okuyucu simgesi.

Sayfa turleri (goz): 'Kazanim Odakli Sorular', 'Orijinal Sorular' (pembe),
'Yeni Nesil' sayfalari, 'OSYM Kosesi / Cikmis Soru' kutulari (etiket
ornek 'TYT - 2018'). Hepsinin cevabi ayni seritte -> hepsi kapsamda.

## 1. Kapsam karari (varsayilan)

Serit tasiyan 357 sayfanin TUM sorulari (1397). Cikmis soru kutusundaki
etiket transkripsiyonda `etiket` alanina alinir (mat345tyt deseni).

## 2. Fazlar

### Faz 1 -- Tarama ve cevap anahtari (`fiz345tyt_tarama.py`, `fiz345tyt_anahtar.py`) -- TAMAM 26 Eyl
Iki bagimsiz okuma (A 5x sirali / B 7x TERS, 8'er okuyucu) 714 sutunun
713'unde birebir; tek fark (s277 R '6.D' / '8.D?') 10x gozle ve numara
surekliligiyle '6.D'. Girdi sayisi == simge sayisi 714/714; numara
surekliligi 1397/1397; glif LOO 1380/1397 (tutmayan 17'si okuyucu
simgesinin seride bindigi sutunlar); tereddutlu/tutmayan 70 sutun 10x gozle.

### Faz 2 -- Konu agaci (migration) -- TAMAM 26 Eyl
Sonuc: 19 unite, 19/19 baslangic bandi dogrulandi; migration 0060 (FIZ-345T25-U01..U19), yerel round-trip temiz.
19 unite (icindekiler) + sayfa ustu 'N. bolum' rozeti ile capraz kontrol;
MAT deseninde FIZ kokunun altinda `FIZ-345T25-Unn`.

### Faz 3 -- Kirpim kutulari
Capa = okuyucu simgesi (1397); tavan/taban stm345_kutu kurallari;
cikmis soru kutusu, pembe sayfa zemini ayrica olculur.

### Faz 4 -- Transkripsiyon
~40 soruluk gruplar, ayri okuyucular; on kayitli ikinci okuma; soluk
isaret taramasi; okunamaz -> `[??]`.

### Faz 5 -- Mukerrer
Formulu koruyan 3-gram (stm345_mukerrer) x DB FIZIK; OSYM cikmis
sorulari ile ozellikle.

### Faz 6 -- Ithal (PASIF) + kaynak sozlesmesi
### Faz 7 -- Testler, belge, PR
### Faz 8 -- Aktiflestirme (AYRI sahip karari)
