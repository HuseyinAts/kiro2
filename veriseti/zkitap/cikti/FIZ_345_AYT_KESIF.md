# 345 2025 AYT Fizik Soru Bankasi -- FAZ 0 KESIF FISI

Plan: `ZKITAP_ISLEME_PLANI.md` bolum 2 (K0.1-K0.8). Dalga B2.
Bu fis SALT OKUNUR olcumlerin sonucudur: hicbir sayfa transkribe
edilmedi, hicbir cevap satiri okunmadi, DB'ye yazilmadi.
Tarih: 18 Eyl 2026.

Kaynak: `veriseti/zkitap/screenshots/345 2025 Ayt Fizik Soru Bankasi/`
-- 392 PNG (1920x1080) + PDF (392 sayfa), uyusmazlik YOK.
Es kaynak: `345 2024 Ayt Fizik Soru Bankasi/` -- 392 PNG + PDF.

---------------------------------------------------------------------

## K0.1 -- SAYFA KARTI (BU kitap icin olculdu, varsayilmadi)

Kart cercevesi 12 ornek sayfada sutun/satir murekkep profilinden
bulundu; 12'sinde de AYNI:

    x 584-1331, y 42-1021   ->  kirpim (584, 42, 1332, 1022) = 748 x 980

Bu, Mikro Orijinal TYT Fizik'in kartindan (596-1323 / 46-1013 =
728x968) FARKLIDIR. Kardes kitabin degeri kullanilsaydi her kirpim
kayardi -- "her kitap icin olc" kurali burada karsiligini verdi.

PDF'te metin katmani yok; gomulu gorsel 1920x1080 -- cozunurluk tavani
diger kitaplarla ayni. Basili sayfa numarasi dosya numarasiyla BIREBIR
ayni (s87 -> 87, s120 -> 120, s241 -> 241 goruntuden dogrulandi).

## K0.2 -- SAYFA HARITASI (kitabin KENDI icindekilerinden)

Icindekiler iki sayfa (f3, f4) ve kitabin tam bolum listesini veriyor.
**20 bolum**, basili baslangic sayfalariyla:

| # | bolum | sayfa |
|---|---|---|
| 1 | VEKTORLER | 6 |
| 2 | BAGIL HAREKET | 14 |
| 3 | NEWTON'IN HAREKET YASALARI | 26 |
| 4 | BIR BOYUTTA SABIT IVMELI HAREKET | 44 |
| 5 | IKI BOYUTTA HAREKET | 68 |
| 6 | ENERJI | 94 |
| 7 | ITME VE CIZGISEL MOMENTUM | 118 |
| 8 | TORK | 146 |
| 9 | DENGE | 148 |
| 10 | KUTLE VE AGIRLIK MERKEZI | 152 |
| 11 | BASIT MAKINELER | 168 |
| 12 | ELEKTRIK | 184 |
| 13 | MANYETIZMA | 208 |
| 14 | ALTERNATIF AKIM VE TRANSFORMATORLER | 232 |
| 15 | CEMBERSEL HAREKET | 246 |
| 16 | BASIT HARMONIK HAREKET | 280 |
| 17 | DALGA MEKANIGI | 302 |
| 18 | ATOM FIZIGINE GIRIS VE RADYOAKTIVITE | 326 |
| 19 | MODERN FIZIK | 352 |
| 20 | MODERN FIZIGIN TEKNOLOJIDEKI UYGULAMALARI | 380 |

DIKKAT -- BU KITAP KONU ANLATIMLI: sayfalarin bir kismi soru degil
konu anlatimi/ornek cozum tasiyor (ornek f120). Yani "sayfa sayisi /
2 = test" gibi bir esitlik YOK; soru sayfasi ile anlatim sayfasi Faz
1'de piksel kanaliyla ayrilacak.

## K0.3 -- CEVAP KAYNAGI: HER SAYFANIN ALTINDA, SUTUN BASINA SATIR

Bu kitapta cevaplar kitabin sonunda degil, **her soru sayfasinin
altinda, sutun basina ayri** basili (ornek f87: solda `5.C 6.D`,
sagda `7.D 8.E`; f241: solda `5.E 6.A`, sagda `7.D 8.A`). Kucuk gri
punto, kart koordinatinda y ~810-880 bandinda.

Bu, simdiye kadar islenen kitaplardan FARKLI bir anahtar bicimidir
(BS: kitap sonu izgarasi; Mikro: test sonu seridi). Avantaji: cevap
dogrudan SAYFA ve SUTUN'a bagli, yani numara-cevap eslesmesi icin
araya test kimligi girmiyor.

Tam kitap taramasi (392 sayfa, kart y 810-880 bandinda murekkep):

| olcum | sonuc |
|---|---|
| bantta murekkep olan sayfa | 364 (UST SINIR; sus/dekor de sayilabilir) |
| her iki sutunda murekkep | 326 |
| bantta murekkep OLMAYAN sayfa | 28 (f4, f24-25, f42-43, f62-63, f90-92, ...) |

Bu sayim bir UST SINIRDIR: bant icindeki dekoratif ogeleri de
sayabilir. Kesin "bu sayfada cevap satiri var/yok" kapisi Faz 1'de,
satir yuksekligi ve punto filtresiyle kurulacak.

## K0.4 -- OKUYUCU SIMGESI ORTMESI: KURTARMA KANALI **VAR**

Glif rengine (69,39,160) yakin bloklar, 392 sayfanin tamami:

| olcum | sonuc |
|---|---|
| simge blogu (>=40 px, bilesen tabanli) | 4172 |
| metne TEMAS eden blok (>=6 px kitap murekkebi, 3 px mesafede) | 144 (%3.5) |

Not: kaba izgara yontemi ayni taramada 1778 blok saydi; iki yontem
arasindaki fark (kitabin kendi lacivert basliklarinin glif rengine
yakin dusmesi) Faz 1'de tek bir kesin dedektorle kapatilacak. Faz 0
icin onemli olan ORAN: %3.5, islenen kitaplarin en dusugu.

**KURTARMA KANALI VAR.** 2024 ve 2025 yakalamalarinda simgeler AYNI
YERDE DEGIL (ornek f280: 2025'te temas eden simge yok, 2024'te
(93,112)'de var; f320'de tam tersi). Edebiyat kitabindaki desenin
aynisi: bir yakalamada ortulen parca digerinden okunabilir.

## K0.5 -- SEKIL YOGUNLUGU: SEKIL HATTI (kirpim ZORUNLU)

392 sayfada renkli piksel medyani **24.555** (5000'in altinda kalan
tek sayfa var). Goz kontrolu (f87, f120, f241): sorularin cogunda
grafik, devre semasi, duzenek cizimi var ve sekil olmadan soru eksik
kalir.

**Karar: SEKIL hatti** -- Mikro Orijinal TYT Fizik'te kurulan desen
(simge tabanli tam soru kirpimi + `<kitap>_kirp.py`) burada da
gecerli.

## K0.6 -- SURUM/KOPYA: 2024 ve 2025 AYRI BASKI, KOPYA DEGIL

DB'de bu kitaptan satir yok. Daha da onemlisi: DB'de **hicbir 345
fizik kitabi yok** (345 markasindan gelen satirlar geometri, biyoloji
ve kimya). FIZIK dersinin tamami: Mikro Orijinal TYT 1326, Neofizik
AYT 1218, Neofizik TYT 891, OSYM 21.

**#11 (2024) vs #12 (2025) tam tarama, 392 sayfa, YALNIZ kart bolgesi:**

| olcum | sonuc |
|---|---|
| farkli piksel orani medyani | **0,28%** |
| oran > 1% olan sayfa | 25 |
| oran > 2% | 18 |
| oran > 5% | 6 |
| en yuksek | 0,77 (f1 kapak) |

Yani iki klasor ayni kitabin iki baskisi ve sayfa duzeni buyuk olcude
ayni. Medyan %0,28'lik fark okuyucu simgelerinin kaymasindan geliyor
(fark bloklari x 13-51 ve x 346-385 -- iki sutunun simge kolonlari).

**Farkli cikan sayfalar GERCEKTEN farkli icerik:** f241 gozle
karsilastirildi -- 5. ve 7. soru ayni, ama 6. soru TAMAMEN degismis
(2024: "Elektrikli ev aleti", CIKMIS SORU AYT-2022; 2025: "Bilgehan,
laboratuvarda...", CIKMIS SORU AYT-2025) ve alt cevap satiri da buna
gore farkli (2024 `5.E 6.E`, 2025 `5.E 6.A`). f87'de 2025 baskisi
2024'te HIC OLMAYAN bir 8. soru eklemis (AYT-2025 cikmis sorusu).

Sonuc: **2025 baskisi islenir** (guncel ve kapsayan); 2024 baskisi
ISLENMEZ ama ortme kurtarma kanali olarak kullanilir. Plan'in
"#11 ancak farkli icerik varsa" kosulu boylece "hayir" ile kapaniyor:
2024'un 2025'te olmayan sorulari OLABILIR (f241'deki AYT-2022
sorusu gibi) -- bu, Faz 1 sonunda 2024 baskisindaki farkli 25 sayfanin
ayrica taranmasi olarak borc listesine yazilir, ayri bir dalga degil.

## K0.7 -- KONU AGACI

Kitap AYT fizigin tamamini 20 bolumde tariyor. FIZ kokunun altinda
mevcut agac (14 seviye-2 dugum) ve B1'de eklenen FIZ-MO alt agaci var.
Bu kitabin bolum adlari ikisiyle de birebir ortusmuyor (ornek "ITME VE
CIZGISEL MOMENTUM", "MODERN FIZIGIN TEKNOLOJIDEKI UYGULAMALARI").
Emsal: kitabin KENDI agaci `FIZ-345` onekiyle ayri alt agac olarak
kurulur (TUR-BS / EDB-BS / FIZ-MO deseni). Alt konu adlari sayfa
ustundeki baslik bandindan alinacak (Faz 1).

## K0.8 -- GO / NO-GO ve MALIYET

| kalem | deger |
|---|---|
| toplam sayfa | 392 |
| cevap satiri tasiyan sayfa (ust sinir) | 364 |
| bolum | 20 |
| beklenen soru sayisi | **Faz 1'de cevap satirlarindan gelecek** (Faz 0'da tahmin edilmedi) |
| simge ortmesi | %3.5 -- ve kurtarma kanali VAR |
| sekil hatti | evet (kirpim zorunlu) |
| transkripsiyon grubu (12 sayfalik) | ~31-33 |
| tahmini alt-ajan maliyeti | ~6-8M jeton |

**KARAR: GIT.** Engelleyici bulgu yok. Uc kanal (icindekiler, alt
cevap satiri, simge sayimi) birbirini dogrulayacak sekilde kurulabilir;
ortme orani islenen kitaplarin en dusugu ve ustelik ikinci yakalamayla
kurtarilabilir.

**ACIK RISK (Faz 1'de kapanacak):**
1. Konu anlatimi sayfalari ile soru sayfalari ayrilmali; "sayfa/2"
   gibi bir kestirme YOK.
2. Alt cevap satiri dedektoru punto/yukseklik filtresi ister; 364
   rakami ust sinirdir.
3. Simge sayiminda iki yontem 1778 ve 4172 dedi; tek dedektorde
   birlestirilecek.
4. 2024 baskisinda olup 2025'te olmayan sorular olabilir (f241
   ornegi); borc olarak izlenecek.

## Olcum dosyalari (git disi, `backend/_f345_gecici/`)

`_k06_cift.py`, `_k06_tam.py`/`k06_tam.json`, `_k06_nerede.py`,
`_k06_blob.py`, `_k01_kart.py`/`_k01b.py`/`_k01c.py`/`_k01d.py`,
`_k02345.py`/`k02345.json`, `_k04_ortme.py`/`k04.json`,
`_kart_cift.py`, `_kart_kirp.py`, `_alt_bant.py`.
