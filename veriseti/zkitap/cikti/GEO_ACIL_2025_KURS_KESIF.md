# ACIL 2025 KURS TYT-AYT Geometri Soru Bankasi -- FAZ 0 KESIF FISI

Sahip karari: **"ikisi de"** -- ACIL geometrinin hem 2023-2024 baskisi
(`GEO_ACIL_2324_KESIF.md`, 448 sayfa) hem de bu 2025 baskisi islenecek.
Bu fis ikincisinin kitap-basi Faz 0'idir (K0.1-K0.8).

Salt okunur olcum: DB'ye yazilmadi, transkripsiyon yapilmadi, hicbir
soru cozulmedi. Tarih: 18 Eyl 2026.

Klasor: `veriseti/zkitap/screenshots/ACIL-TYT-AYT-Geometri Soru Bankasi`
(okuyucu sekme adi: "ACIL - 2025 - TYT - AYT - Geometri Soru Bankasi")

---------------------------------------------------------------------

## K0.6 ONCE: iki baski AYNI KITAP DEGIL

Sahip "ikisi de" dedigi icin asil soru "hangisi" degil, "ayni sorular
iki kez mi girecek" oldu. Kunye sayfalari bunu piksel karsilastirmasina
gerek kalmadan kapatti:

| | 2023-2024 | 2025 (bu kitap) |
|---|---|---|
| ISBN | 978-625-7134-**31-6** | 978-625-7134-**96-5** |
| seri | duz Soru Bankasi | **KURS** serisi |
| yazarlar | Mahsum OZTURK, Ibrahim Turan BASAY, Zeynal BORAZAN | Ibrahim Turan BASAY, Kadir YIGIT, Baris ISCAN, Hamza SINCAR, Mehmet KARAYEL |
| editorler | Baris ISCAN, Mehmet KARAYEL, Yunus KARAKUS, Yilmaz Kemal YILDIZ, Hamza SINCAR | (yok) |
| dizgi | test bazli, test sonu izgara kutusu | "Konu Ogrenme" bantli, her sayfada serit anahtar |

Ortak tek yazar Ibrahim Turan BASAY; 2023-2024'un editorleri 2025'te
yazar olmus. ISBN'ler farkli, seri farkli, dizgi bastan asagi farkli.
**Iki ayri kitap.** Yani "ikisi de" karari bir surum cakismasi
yaratmiyor.

Yine de ayni sorunun iki kitapta tekrarlanmasi mumkun; bu, ithal
aninda `soru_hash` kapisinin isi (metin + sik md5'i). Faz 0 duzeyinde
ek bir engel yok.

DB tarafinda ortusme: DB'de ACIL yayinevinden geometri kitabi yok.

## K0.1 -- Sayfa karti ve sayfa sayisi

| olcu | deger |
|---|---|
| kart | **734 x 968** @ (593, 46) |
| 11 ornekte sapma | 0 px |
| PNG | 400 |
| PDF `/Count` | 400 |

Kart 2023-2024 baskisiyla ayni (ayni okuyucu penceresi); yine de
olculdu, varsayilmadi.

## K0.2 -- YAKALAMA TEKRARI var, sayfa no ofseti -4

Bu kitapta ilk kez bir **yakalama kusuru** olculdu: `sayfa_0003.png`,
`sayfa_0004.png` ve `sayfa_0005.png` **bayt bayt ayni dosya** (ucu de
kapak). Tum kitabin md5 taramasi bu tek grubu buldu:

| olcu | deger |
|---|---|
| dosya | 400 |
| benzersiz goruntu | **398** |
| tekrar grubu | 1 (dosya 3-4-5) |
| tekrardan gelen fazlalik | 2 dosya |

PDF de ayni PNG'lerden uretildigi icin `/Count 400` bu fazlaligi
iceriyor -- yani "PNG = PDF" esitligi burada uzlasma DEGIL, ayni
kusurun iki kez sayilmasi.

Basili sayfa no = **dosya no - 4**, 12 ornekte sabit (dosya 7 -> basili
3; dosya 20 -> 16; dosya 100 -> 96; dosya 200 -> 196; dosya 398 -> 394).
Tekrar eden dosyalar basili 1. sayfadan once kaldigi icin ofset kitap
boyunca kaymiyor.

| aralik | icerik |
|---|---|
| dosya 1-2 | on kapak / ic kapak |
| dosya 3-5 | kapak (ayni goruntu, 3 kez) |
| dosya 6 | kunye (basili 2) |
| **dosya 7 - 398** | **soru sayfalari (392 sayfa, basili 3-394)** |
| dosya 399-400 | arka kisim |

## K0.3 -- Anahtar: HER SAYFANIN ALTINDA SERIT

392 soru sayfasinin **392'sinde** serit var (istisnasiz).

| olcu | deger (kart-ici) |
|---|---|
| serit metni | y 914 - 920 |
| ayrac suslemeleriyle birlikte bant | y 910 - 924 |
| x araligi | 119 - 613 (iki sutunu birden kapsiyor) |

345 kitaplarindaki "sayfa alti sutun satiri" bicimine yakin ama ondan
farkli: burada serit sutun basina degil, sayfa basina tek parca.

**Sizinti kapisi: kirpim kutularinin alti kart-ici y = 908'in ustunde
kalmali.**

## DUZELTME (19 Eyl 2026) -- K0.4'teki %8,40 ORTME OLCUSU DEGIL

Asagidaki K0.4, ACIL 2023-2024 fisiyle ayni yanlis metrigi kullaniyor:
"disk dairesinin icinde kitap murekkebi". Disk OPAK oldugu icin bu metrik
ortmeyi goremez; kenardan tasan sayfa mobilyasini sayar. **%8,40 bir
ortme orani DEGILDIR.**

Bu kitap icin dogru metrikle (diskin sol kenarindan 7-13 px'lik bantta
metin) yeniden olculdu -- olcum 2023-2024 kitabinda 154 olayi birebir
yeniden ureten, yani kalibre edilmis dedektorle yapildi:

| olcum | ACIL 2023-2024 | ACIL 2025 KURS |
|---|---|---|
| sag sutun simgesi | 916 | **961** |
| bantta sinyal | 154 (%16,8) | **403 (%41,9)** |
| etkilenen sayfa | 136 | **313** |
| eski (yanlis) metrik | 228 | 149 |
| diskin sagindaki en kucuk bosluk | 27 px | **3 px** |

Iki uyari:

1. **403 rakami ORTME SAYISI DEGIL, UST SINIRDIR.** 16 olay gozle
   incelendi: bir kismi gercekten diske dayanan soru metni, bir kismi ise
   bu kitaba ozgu sayfa mobilyasi (sari "Konu Ogrenme" basligi, ilerleme
   seridi, sekil kenari). 2023-2024'un bandi bu sikisik dizgide mobilyayi
   da yakaliyor. Kesin sayi ancak Faz 1 adim 2'de kirpim kutulari
   cikinca, "sik satirinda bes etiket (A-E) gorunuyor mu" kapisiyla
   belirlenebilir.
2. **Diskin sagindaki bosluk 3 px.** Yani beyazlatma payi en fazla
   `gx+23` olabilir; daha genis bir pay soru numarasini siler. ACIL
   2023-2024'te tam bu hata yapilmisti (pay 27, ilk metin gx+26) ve
   basili "8" kirpimda "3" gibi okundu. Bu kitapta pay daha da dar.

**Onemli oneri (sahip karari gerektirir):** FERNUS okuyucusunun ayar
panelinde "Zenginlestirme ve Aktivite Dugmelerini Goster" anahtari var.
Bu kitap Faz 1 icin YENIDEN YAKALANIRSA (anahtar kapali) simge sinifi
tamamen ortadan kalkar: ne ortme, ne beyazlatma payi, ne KAPI 6. 392
sayfalik yeniden yakalama, %42'ye varabilecek bir ortme borcunu ve onun
butun kapilarini bir defada siler. Kirpim kutulari simge konumundan
turetildigi icin yakalama degisirse o adim yeniden olculur.

Asagidaki K0.4 metni TARIHSEL KAYIT olarak birakildi.

## K0.4 -- Simge ortmesi: uc geometri kitabinin EN YUKSEGI

1964 simge olculdu (soru sayfalarinda 1951). Dairesel disk maskesi ile:

| olcum | deger |
|---|---|
| disk dairesi icinde kitap murekkebi | **165 (%8,40)** |
| 3 px halkada murekkep | 512 (%26,07) |

Karsilastirma:

| kitap | disk icinde murekkep |
|---|---|
| ACIL 2023-2024 | %8,9 ama tamami sutun cizgisi/filigran -- soru icerigi 0 |
| Orijinal 2024 | %2,72 |
| **ACIL 2025 KURS** | **%8,40, sayfa mobilyasi degil icerik** |

Sebep dizgi: "Konu Ogrenme" bantli sikisik yerlesimde simgeler metne
daha yakin duruyor. Yine de emsalin (Edebiyat %30,7) cok altinda.

**Oneri: ithal et, etkilenen satirlari isaretle.** Dikkat: 2023-2024
baskisi bu kitabin kurtarma kanali OLAMAZ -- farkli kitap, farkli
dizgi, simge konumlari karsilastirilamaz.

## K0.5 -- Sekil hatti ve dizgi kurallari

Geometri; kirpim zorunlu. Simge sutunlari yine tek/cift sayfada
kayiyor, bu kez **16 px**: sol sutun gx 20 / 36, sag sutun gx 348 / 364.

## K0.7 -- Konu agaci: ICINDEKILER SAYFASI YAKALAMADA YOK

Bu kitapta kunye (dosya 6) hemen ardindan ilk icerik sayfasi geliyor;
icindekiler sayfasi yakalanmamis. Diger iki geometri kitabinda konu
agaci dogrudan icindekilerden cikarilmisti, burada cikarilamiyor.

**Konu agaci Faz 1'de sayfa basliklarindan turetilecek** (her sayfanin
ust bandinda kirmizi konu adi ve "Konu Ogrenme / Test" etiketi var).
Bu, diger kitaplara gore ek is ve ek hata riski demek; fise acik
eksiklik olarak yaziliyor.

## K0.8 -- GO / NO-GO ve maliyet

| kalem | deger |
|---|---|
| soru sayfasi | 392 |
| beklenen soru | ~**1951** (simge sayimi) |
| grup (12 sayfa) | ~33 |
| transkripsiyon kaba maliyet | ~33 x 150k = **~5,0M jeton** |
| kirpim | zorunlu |
| ortme borcu | %8,40 -- isaretlenecek, kurtarma kanali YOK |
| anahtar | her sayfada serit, eksiksiz |
| DB ortusmesi | yok |
| iki baski cakismasi | yok (farkli ISBN / farkli kitap) |

**Karar: GIT.** Iki acik nokta Faz 1'e tasiniyor: (1) konu agaci sayfa
basliklarindan kurulacak, (2) ortme isaretlemesi kurtarma kanalsiz
yapilacak.

## Olcum dosyalari (git disi, `backend/_geo1_gecici/`)

`_kart.py`, `_faz0_genel.py` + `faz0_acil25.json`, `_ortme_genel.py`,
`_acil25.py` (sarmalayici), `_acil25_anahtar.py` + `acil25_anahtar.json`,
`acil25_sayfano.png` (basili sayfa no montaji).
