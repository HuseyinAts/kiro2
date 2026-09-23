# Dalga D / kitap #3 -- Orijinal 2024 TYT-AYT Geometri Soru Bankasi

> **DUZELTME (23 Eyl 2026):** asagida "#4 ayni yakalama / kurtarma kanali" deniyor; bu YANLIS.
> #4 (`Orijinal-Tyt Ayt Geometri Soru Bankasi`) 2025 baskisidir, bazi sorulari farklidir.
> `GEO_ORIJINAL_2024_FAZ1.md` 18.1 ve `ZKITAP_KITAP_DURUMU.md` bolum 2.

# FAZ 0 KESIF FISI

Plan: `ZKITAP_ISLEME_PLANI.md` bolum 1 (dalga D) ve bolum 3 (K0.1-K0.8).
On kesifte (`GEO_DALGA_D_KESIF.md`) #3 ile #4'un AYNI kitabin AYNI
yakalamasi oldugu olculmustu; ikisinden #3 islenecek, #4 ortme kurtarma
kanali olacak.

Bu fis SALT OKUNUR olcumlerin sonucudur: DB'ye yazilmadi, transkripsiyon
yapilmadi, hicbir soru cozulmedi. Tarih: 18 Eyl 2026.

Klasor: `veriseti/zkitap/screenshots/Orijinal-2024-Geometri Soru Bankasi`

---------------------------------------------------------------------

## K0.1 -- Sayfa karti ve sayfa sayisi uzlasmasi

11 ornek sayfada kart dikdortgeni **sapmasiz**:

| olcu | deger |
|---|---|
| kart x | 593 - 1326 |
| kart y | 46 - 1013 |
| kart boyutu | **734 x 968** |
| 11 ornekte sapma | 0 px |

Bu, ACIL 2023-2024 Geometri ile **ayni** kart: iki kitap ayni okuyucu
penceresinde yakalanmis. (Yine de olculdu; varsayilmadi.)

Sayfa sayisi: PNG 432, PDF `/Count 432`. **Uyusuyor.**

## K0.2 -- Sayfa haritasi ve basili sayfa no ofseti

| aralik | icerik |
|---|---|
| s1 - s4 | on kisim; s3 = ICINDEKILER |
| **s5 - s432** | **soru sayfalari (428 sayfa)** |

Simgesiz (0 buyutec) soru sayfasi: 149, 260, 321, 388 -- dordu de
OSYM bolumlerinin civari; Faz 1'de tek tek bakilacak.

Basili sayfa no = dosya no (**ofset 0**): s200 alt ortasindaki sari
yer imi "200", s230'da "230" yaziyor.

## K0.3 -- Anahtar bicimi: SAYFA ALTI ORTALANMIS SATIR

Anahtar, testin son sayfasinin altinda tek satir halinde duruyor
(`1.C 2.B 3.B ... 12.B`). Satir bandi kart-ici **y 884 - 903**.

**Onemli:** satirin x baslangici SABIT DEGIL, icerige gore ortalaniyor:
s200'de x0 = 82, s230'da x0 = 235. Ilk dedektor x0'i 70-100 arasinda
varsaydigi icin sayfalarin yarisini kaciriyordu; kisit kaldirildi.

### Sayim ucu acik birakildi (bilerek)

| yontem | bulunan satirli sayfa |
|---|---|
| dar esik (>=20 px, genislik >=150) | 196 |
| gevsek esik (>=10 px, genislik >=60) | 244 |
| **icindekiler (otorite)** | **226 test** |

Piksel dedektoru esige cok duyarli; gercek sayi 196 ile 244 arasinda
ve icindekilerin verdigi 226 bu araligin icinde. Dalga B2'de ogrenilen
ders aynen gecerli: **sayim otoritesi piksel degil, iki bagimsiz okuma
olmali.** Kesin test haritasi Faz 1'e birakildi; otorite icindekiler
tablosu + LLM okumasi olacak.

**Sizinti kapisi:** kirpim kutularinin alti kart-ici **y = 884**'un
ustunde kalmali.

## K0.4 -- Simge ortmesi: dusuk ama SIFIR DEGIL

2099 simge olculdu. Dairesel disk maskesi (r <= 15) ile:

| olcum | deger |
|---|---|
| disk dairesi icinde kitap murekkebi | **57 (%2,72)** |
| bunlarin sag sutunda olani | 14 |
| bunlarin sol sutunda olani | 43 |
| 3 px halkada murekkep | 64 (%3,05) |

ACIL kitabindan farkli: orada ortulen sey yalnizca sutun cizgisi ve
filigrandi, burada olaylarin dortte ucu SOL sutunda, yani soru
icerigine komsu. Emsal (Edebiyat %30,7) ile kiyaslandiginda yine de
dusuk. **Oneri: ithal et, etkilenen satirlari isaretle** -- ve #4
yakalamasi kurtarma kanali olarak elde zaten var.

## K0.5 -- Sekil yogunlugu: SEKIL hatti

Geometri kitabi; sayfa basina 4-6 soru, sorularin cogunda sekil
(s200'de 6/6, s230'da 6/6 gozle sayildi). Renkli/grafik icerik her
soru sayfasinda var. **Karar: SEKIL hatti**, kirpim zorunlu.

Simge x konumlari ACIL kitabindaki gibi iki sabit sutun degil, soru
basina degisiyor (sik gorulen degerler: sol 30/36/46/49, sag
351/353/369; ayrica 180 dagilmis konum). Yani kirpim kutusu sol
kenari **simgeden turetilmeli**, sabit bir sutundan degil.

## K0.6 -- Surum / kopya

DB'de Orijinal yayinevinden geometri kitabi yok (havuzdaki iki geometri
kitabi `345 2025 TYT-AYT Geometri` ve `Mikro Orijinal 2025 AYT
Geometri`).

Ayni yayinevinden havuzda uc klasor var:

| klasor | PNG | durum |
|---|---|---|
| `Orijinal-2024-Geometri Soru Bankasi` | 432 | **bu fis** |
| `Orijinal-Tyt Ayt Geometri Soru Bankasi` | 432 | ayni yakalama (on kesif), kurtarma kanali |
| `Orijinal-2024-Geometri` | 160 | kismi/yarim yakalama -- islenmeyecek |

## K0.7 -- Konu agaci (simdiye kadarki en zengin icindekiler)

s3 hem konulari hem her konunun **TEST SAYISINI** hem de baslangic
sayfasini veriyor. 5 bolum / 30 konu / 5 OSYM bolumu, toplam **226
test**.

| bolum | konu (test sayisi / baslangic sayfasi) |
|---|---|
| 1 Ucgenler | Temel Kavramlar ve Dogruda Acilar (3/8); Ucgende Acilar (9/14); Dik ve Ozel Ucgenler (10/28); Ikizkenar Ucgen (6/46); Eskenar Ucgen (6/56); Ucgende Aciortay Bagintilari (6/66); Ucgende Kenarortay Bagintilari (6/76); Ucgende Eslik ve Benzerlik (13/86); Ucgende Merkezler (3/110); Ucgende Alan (11/116); Ucgende Aci-Kenar Bagintilari (4/137); OSYM'DE CIKMIS SORULAR (145) |
| 2 Cokgenler ve Dortgenler | Cokgen ve Duzgun Cokgenler (9/151); Dortgenler (5/167); Deltoid (3/175); Paralelkenar (10/179); Eskenar Dortgen (6/197); Dikdortgen (10/207); Kare (9/225); Yamuk (9/241); OSYM'DE CIKMIS SORULAR (257) |
| 3 Cember ve Daire | Cemberde Aci (9/262); Cemberde Uzunluk (11/278); Dairede Cevre ve Alan (11/298); OSYM'DE CIKMIS SORULAR (318) |
| 4 Analitik Geometri | Noktanin Analitik Incelenmesi (8/323); Dogrunun Analitik Incelenmesi (11/337); Analitik Duzlemde Donusumler (7/358); Cemberin Analitik Incelenmesi (9/370); OSYM'DE CIKMIS SORULAR (386) |
| 5 Kati Cisimler | Prizmalar (11/390); Piramit (7/410); Kure (3/422); Donel Cisimler (1/426); OSYM'DE CIKMIS SORULAR (428) |

Bolum toplamlari: 77 + 61 + 31 + 35 + 22 = **226 test**.

Mevcut `topic_hierarchy`de karsiligi yok -> migration gerekiyor.

## K0.8 -- GO / NO-GO ve maliyet

| kalem | deger |
|---|---|
| soru sayfasi | 428 |
| beklenen soru | ~**2099** (simge sayimi; s200 ve s230'da 6/6 gozle dogrulandi) |
| test | 226 (icindekiler) |
| grup (12 sayfa) | ~36 |
| transkripsiyon kaba maliyet | ~36 x 150k = **~5,4M jeton** |
| kirpim | zorunlu; kutu sol kenari simgeden turetilmeli |
| ortme borcu | %2,72 (57 satir) -- isaretlenecek; #4 kurtarma kanali var |
| anahtarsiz test | olculmedi (Faz 1) |
| DB ortusmesi | yok |

**Karar: GIT.** Faz 1'in ILK isi, test haritasini piksel dedektoruyle
degil icindekiler tablosundan kurmak ve iki bagimsiz okuma ile
dogrulamak olmali.

## Olcum dosyalari (git disi, `backend/_geo1_gecici/`)

`_kart.py` (K0.1), `_faz0_genel.py` + `faz0_ori.json` (tam kitap
taramasi), `_ori_anahtar.py` ... `_ori_anahtar5.py` (cevap satiri
dedektorunun bes kademesi), `_ortme_genel.py` (K0.4).
