# Mikro Orijinal TYT Fizik Soru Bankasi 2025 -- FAZ 0 KESIF FISI

Plan: `ZKITAP_ISLEME_PLANI.md` bolum 2 (K0.1-K0.8). Dalga B1.
Bu fis SALT OKUNUR olcumlerin sonucudur: hicbir sayfa transkribe
edilmedi, hicbir anahtar okunmadi, DB'ye yazilmadi. Tarih: 17 Eyl 2026.

Kaynak: `veriseti/zkitap/screenshots/Mikro Orijinal Tyt Fizik Soru
Bankasi 2025/` -- 400 PNG (1920x1080) + PDF.

---------------------------------------------------------------------

## K0.1 -- SAYFA KARTI

12 ornek sayfanin murekkep birlesimi, uygulama kromu maskelenerek:

    x 596-1323, y 51-1008

Kirpim kutusu `(596, 46, 1324, 1014)` = **728 x 968 px** alindi (Edebiyat
kitabiyla ayni okuyucu, ayni geometri). PNG 400 = PDF 400, uyusmazlik YOK.
PDF'te metin katmani yok; gomulu gorsel 1920x1080 -- cozunurluk tavani
ayni.

Basili sayfa numarasi dosya numarasiyla BIREBIR ayni (alt banttaki
numara kutusundan, 6 sayfada goruntuden dogrulandi).

## K0.2 -- SAYFA HARITASI (kitabin KENDI icindekilerinden + piksel)

Icindekiler sayfasi (f4) kitabin tam yapisini veriyor; 11 bolum:

| # | bolum | Kazanim | OSYM Tarzi | OSYM Tarzi ORIJINAL | sayfa |
|---|---|---|---|---|---|
| 01 | FIZIK BILIMINE GIRIS | 1-3 | 4-6 | -- | 7-18 |
| 02 | MADDE VE OZELLIKLERI | 1-6 | 7-9 | 10-11 | 21-42 |
| 03 | HAREKET | 1-9 | 10-12 | 13-14 | 45-72 |
| 04 | NEWTON'IN HAREKET YASALARI | 1-5 | 6-11 | 12-13 | 75-100 |
| 05 | IS VE ENERJI | 1-7 | 8-10 | 11-14 | 103-130 |
| 06 | ISI VE SICAKLIK | 1-11 | 12-16 | 17-18 | 133-168 |
| 07 | ELEKTRIK VE MANYETIZMA | 1-24 | 25-32 | 30/33-36 | 171-242 |
| 08 | BASINC | 1-8 | 9-13 | 14-15 | 245-274 |
| 09 | KALDIRMA KUVVETI | 1-4 | 5-6 | 7-8 | 277-292 |
| 10 | DALGALAR | 1-13 | 14-18 | -- | 295-330 |
| 11 | OPTIK | 1-26 | 27-29 | 30-33 | 333-398 |

Toplam **372 soru sayfasi**. Geri kalan 28 sayfa: kapak/kunye/sunu,
icindekiler, 11 bolum ayraci, arkada iki cevap kagidi izgarasi (f399,
f400) ve bos sayfalar.

KITABIN KENDI DIZGI KUSURU: bolum 07 ORIJINAL satiri "30 - 33 - 34 - 35 -
36" diyor (bes numara) ama sayfa araligi 235-242 = 8 sayfa = 4 test.
"30" fazladan/yanlis basilmis. Isaretlenecek.

## K0.3 -- CEVAP KAYNAGI: HER TESTIN SON SAYFASINDA SERIT

Her test **tam 2 sayfa** ve cevap seridi testin IKINCI sayfasinda basili;
serit o testin TUM cevaplarini tasir (ornek s50: `1.E 2.C 3.E 4.E 5.B
6.D 7.D 8.C`). Serit kutusunun alt cercevesi kart y=896'da, x 50-730
araliginda kesintisiz koyu cizgi olarak olculebiliyor.

Bu kanal metin HIC OKUNMADAN calistirildi:

| olcum | sonuc |
|---|---|
| serit bulunan sayfa | **186** |
| icindekilerden turetilen test sayisi (sayfa araligi / 2) | **186** |
| beklenen serit sayfasinda serit BULUNMAYAN | **0** |
| beklenmeyen sayfada serit BULUNAN | **0** |
| seritlerdeki toplam girdi (magenta numara kumesi) | **1326** |

Girdi sayisi dagilimi: 8 cevap 83 test, 7 cevap 48, 6 cevap 37, 5 cevap
11, 4 cevap 3, 9 cevap 3, 10 cevap 1.

Yani **beklenen soru sayisi 1326** ve bu sayi anahtardan degil, anahtarin
PIKSEL yapisindan gelir.

Not: "OSYM Tarzi ORIJINAL" testleri de coktan secmeli (A-E) ve onlarin da
seridi var; yalnizca testin ilk sayfasinda serit yok -- bu sayfa turu
farki degil, serit her testin SON sayfasinda oldugu icindir.

Serit 4x buyutmede rahat okunuyor (ornek goruntu ile dogrulandi). Ayrica
her serit hem cevaplari hem BASILI SAYFA NUMARASINI ayni kirpimda tasiyor
-- sayfa numarasi denetimi bedava geliyor.

TESSERACT DENENDI VE ELENDI: serit metni 1x'te ~8 px yuksek; tesseract
(psm 7, whitelist) dort ornek seritte de bozuk okudu. Okuma LLM kanaliyla
yapilacak; ikinci kanal olarak testin iki sayfasindan degil, AYRI OLCEK +
AYRI GRUPLAMA ile ikinci bir okuma kurulacak.

## K0.4 -- OKUYUCU SIMGESI ORTMESI: KURTARMA KANALI YOK

Simge blogu (soru sayfalarinda): **1381**; sayfa basina dagilim 4 (242
sayfa), 3 (88), 2 (23), 5+ (19).

Metne temas eden (duzeltilmis metin maskesi, >=6 px): **121 blok**
(%8.8 ust sinir).

Edebiyat kitabindan FARKLI olarak bu kitabin ikinci bir yakalamasi YOK
(`screenshots` altinda tek klasor). Yani ortulen parca baska bir
kaynaktan kurtarilamaz; BS Turkce emsali gecerli olacak: okunabilen kismi
yaz, TAHMIN ETME, `okuyucu_simgesi_ortmesi` bayragini koy.

## K0.5 -- SEKIL YOGUNLUGU: SEKIL HATTI (kirpim ZORUNLU)

372 soru sayfasinin **%100'unde** 5000 pikselden fazla renkli icerik var
(medyan 23.118 renkli piksel/sayfa). Goz kontrolu (s39, s50): sorularin
cogunda grafik, tablo, duzenek cizimi var ve sekil olmadan soru eksik
kalir.

**Karar: SEKIL hatti.** Kardes kitap `Mikro Orijinal 2025 AYT Geometri`
ile ayni yayinevi, ayni dizgi, ayni serit mantigi; o ithalde sorularin
%88'i sekilliydi ve `question_image_url` TAM SORU KIRPIMI olarak
uretildi (`scripts/kitap/mikro_geo_kirp.py`). Burada da ayni desen
kullanilacak: kirpim kutulari SIMGE konumlarindan turetilir (LLM'e
koordinat tahmin ettirilmez), `<kitap>_kirp.py` ile PDF'ten yeniden
uretilebilir.

Simge sayisi (1381) ile beklenen soru sayisi (1326) arasindaki 55'lik
fark, segmentasyonun Faz 1'de tek tek aciklanmasi gereken kalemidir
(kardes kitapta da benzer sapmalar vardi ve hepsi aciklandi).

## K0.6 -- KOPYA / ORTUSME (on kontrol)

DB'de bu kitaptan satir yok (`source_book` listesinde gecmiyor). TYT
fizikte mevcut modern satirlar baska yayinevinden (`Neofizik TYT Fizik`,
891 satir). Hash ve kelime-kumesi ortusmesi transkripsiyon sonrasi
(Faz 1 / 2b kapisi) olculecek.

Ayrica bu kitabin ikinci bir cekimi ya da baska baskisi `screenshots`
altinda YOK -- yani baski ikilemi (Edebiyat'taki gibi) burada yok.

## K0.7 -- KONU AGACI

FIZ kokunun altinda mevcut agac var (14 seviye-2, 79 seviye-3 dugum).
Bu kitabin 11 bolumu ve test basliklari (sayfa ustundeki bant: ornek
"HAREKET / KAZANIM TESTI (Duzgun Dogrusal Hareket) - 3") mevcut agacla
ESLENECEK; eslesmeyen dallar icin migration gerekebilir. Bolum duzeyinde
eslesme, kardes kitaplardaki gibi `konu_eslesme_duzeyi` ile isaretlenir.

## K0.8 -- GO / NO-GO ve MALIYET

| kalem | deger |
|---|---|
| soru sayfasi | 372 |
| test | 186 (her biri 2 sayfa) |
| beklenen soru | **1326** (piksel kanali) |
| cevap seridi okumasi | 186 serit x 2 bagimsiz okuma |
| transkripsiyon grubu (12 sayfa) | ~31 |
| kirpim isi | simge tabanli segmentasyon + `_kirp.py` (kardes kitap deseni) |
| tahmini alt-ajan maliyeti | ~6-8M jeton |

**KARAR: GIT.** Engelleyici bulgu yok. Yapisal kanallar (icindekiler,
serit cizgisi, simge sayimi) birbirini dogruluyor: 186/186 test, 0 sapma.
Tek gercek risk sekil kirpimi ve ortme kurtarmasinin olmamasi; ikisi de
bayrakla yonetilebilir ve emsali var.

## Olcum dosyalari (git disi, `backend/_fiz_gecici/`)

`_kart.py`, `_sayfa_tur.py`/`sayfa_tur.json`, `_serit.py`,
`_serit2.py`/`serit2.json`, `_serit3.py`/`serit3.json`,
`_simge.py`/`simge.json`, `_glif.py`, `serit/` (374 serit kirpimi).
