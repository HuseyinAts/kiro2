# 345 2025 TYT Kimya Soru Bankasi -- kesif olcumleri ve isleme plani

Kaynak: `veriseti/zkitap/screenshots/345 2025 Tyt Kimya Soru Bankasi/`
(klasor adi Turkce 'i' ile biter). DB'de eski hat: ayni kitabin klasor
adiyla 294 satir (hepsi aktif) + 2024 baskisinin (`345 Tyt Kimya Soru
Bankasi`) 213 satiri. Onek: `KMT345` (birim `KMT345-Tnnn`), kod oneki
(Faz 2) `KIM-345T25`.

## 0. Kesif olcumleri (27 Eyl)

| kalem | deger | kanal |
|---|---|---|
| PNG | 280, 1920x1080 | dosya sayimi |
| kart | (589, 43) - (1331, 1022) = 742x979 | 345 TYT Fizik ile ayni aile |
| basili sayfa | = dosya (s8 altinda '8') | gozle |
| soru sayfasi | 267 | cevap seridi bandi (kart y 899-904) + simge |
| seritsiz | 3-5 (icindekiler), 35/71/109/139/155/195/231/263 (unite ayraci) | piksel |
| seritli simgesiz | 1, 2 (kapak, kunye) | piksel |
| unite / konu | 9 / 35 | icindekiler (dosya 3-4), gozle |
| okuyucu simgesi (soru capasi) | 1307 | piksel (stm345 tanimi) |
| cevap seridi girdisi | 1307 (A) = 1307 (B) | iki gorsel okuma |
| test (numara 1'e donus) | 138 | okuma |

Sayfa tasarimi 345 TYT Fizik ile ayni: lila disk + mor buyutec simgesi,
camgobegi soru numarasi, sutun basina sayfa alti cevap seridi. Farklar:
cift sayfa sol sutunun ustunde 'N. TEST' rozeti (camgobegi rakam, numara
kanalina girer); unite sonunda 'OSYM TADINDA N' testleri; 3 sutunda
okuyucu simgesi sorunun degil 'OSYM TADINDA' basliginin yaninda.

## 1. Kapsam karari (varsayilan)

Serit tasiyan 267 sayfanin TUM sorulari (1307). Cikmis soru kutusundaki
etiket transkripsiyonda `etiket` alanina alinir.

## 2. Fazlar

### Faz 1 -- Tarama ve cevap anahtari (`kim345tyt_tarama.py`, `kim345tyt_anahtar.py`) -- TAMAM 27 Eyl
Iki bagimsiz okuma (A 5x sirali / B 7x TERS, 8'er okuyucu) 534 sutunun
534'unde birebir. Girdi sayisi == simge sayisi 534/534; numara surekliligi
1307/1307; glif LOO 1234/1307; '?' tasiyan ya da glifi tutmayan 106 sutun
5x gozle, hepsi okumayla ayni.

### Faz 2 -- Konu agaci (migration) -- TAMAM 27 Eyl
9 unite (icindekiler) + her unitenin ilk soru sayfasi bandi ('1. TEST' +
ilk konu adi) 9/9; migration 0062 (KIM-345T25-U01..U09), yerel round-trip
temiz (9 -> 0 -> 9).

### Faz 3 -- Kirpim kutulari -- TAMAM 27 Eyl
1307 kutu (simge 531 / numara 3 sutun), kapi ihlali 0, kenar 0, ortme
suphesi 117; gorsel QA temiz.

### Faz 4 -- Transkripsiyon
~40 soruluk gruplar, ayri okuyucular; on kayitli TAM ikinci okuma; soluk
isaret taramasi; okunamaz -> `[??]`.

### Faz 5 -- Mukerrer + eski hat
Formulu koruyan 3-gram x DB KIMYA; eski hat (294 + 213 satir) eslestirmesi.

### Faz 6 -- Ithal (PASIF) + kaynak sozlesmesi
### Faz 7 -- Testler, belge, PR
### Faz 8 -- Aktiflestirme
