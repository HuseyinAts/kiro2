# C1CELL 2024 TYT-AYT Geometri Soru Bankasi -- FAZ 0 KESIF FISI

Sahip karari: Wave D (dalga D) kitabi #5. ACIL 2023-2024 Faz 1 bitince
(PR #301-304) sirada bu kitap secildi. Bu fis kitap-basi Faz 0'dir
(K0.1-K0.8).

Salt okunur olcum: DB'ye yazilmadi, transkripsiyon yapilmadi, hicbir soru
cozulmedi. Tarih: 19 Eyl 2026.

Klasor: `veriseti/zkitap/screenshots/C1CELL-2024-TYT-AYT-Geometri Soru
Bankasi` (dosya adinda Turkce karakter var; scriptler glob ile buluyor.)

Yayinevi: **C1CELL Yayinlari** (on sozu Gokhan KECECI imzali). ACIL,
345, Mikro, Bilgi Sarmali'dan farkli yayinevi -- ayni sorunun tekrari
riski dusuk (yine de ithal aninda soru_hash kapisi var).

---------------------------------------------------------------------

## K0.1 -- Sayfa karti ve sayfa sayisi

| olcu | deger |
|---|---|
| kart x | 591 - 1328 |
| kart y | 46 - 1013 |
| kart boyutu | **738 x 968** |
| 5 ornekte sapma | 0 px |
| PNG | **416** |

Kart, ACIL geometri kartindan (734x968 @ 593,46) 4 px genis ve 2 px
sola kaymis -- ayni aileden AMA ayni degil; olculdu, varsayilmadi.
Wave D kesif fisinde bu kitap "420 PNG" yaziyordu; gercek sayi **416**
(K0.1 olcumu). Disk butun geometri kitaplariyla ayni FERNUS diski
(dolgu 240,238,247; simge merkezine gore -6/-5/22/24).

## K0.2 -- Sayfa haritasi ve basili sayfa no ofseti

| aralik | icerik |
|---|---|
| s1 - s2 | kapak / ic kapak |
| s3 | ON SOZ (Gokhan KECECI) |
| s4 | bos |
| **s5 - s6** | **ICINDEKILER (2 sayfa)** |
| **s7 - s414** | **konu icerigi (asagida)** |
| s415 - s416 | arka kisim |

Basili sayfa no = dosya no (**ofset 0**), UC bagimsiz yerden dogrulandi:
  * icindekiler "Dogruda Aci ... 7" diyor; dosya 7 = "DOGRUDA ACI" konu
    anlatim sayfasi.
  * dosya 9'un alt seridinde sayfa numarasi "9" yaziyor.
  * dosya 8 (sol/cift sayfa) altta solda "8", dosya 10 altta solda "10".

## K0.3 -- Anahtar bicimi: TEST SONU SAYFA-ALTI SERIDI

ACIL 2023-2024'ten (test sonu 2 satirli izgara kutusu) ve ACIL 2025
KURS'tan (her sayfada serit) FARKLI. Burada her testin SON (sag) sayfasinin
altinda tek satirlik yatay bir SERIT, testin tum sorularinin cevabini
birlikte veriyor.

Ornek s9 (TEST 1, sag sayfa): `1 E 2 E 3 D 4 A 5 E 6 C 7 A 8 C 9 B
10 A 11 D 12 C` -- 12 cevap; TEST 1 = s8 (soru 1-6) + s9 (soru 7-12).

| olcu | deger (tam goruntu koordinati) |
|---|---|
| serit y | 940 - 954 |
| serit x | ~620 - 1160 (iki sutunu birden kapsar) |
| kutu zemini | acik mavi kutucuklar, icinde koyu harf |

Sol (cift) sayfalarda serit YOK; altta solda sayfa no, sagda kosan
bolum adi ("DOGRUDA ACI") var. Serit yalniz testin bittigi sag sayfada.

**Sizinti kapisi: kirpim kutularinin alti bu seridin (y~938) ustunde
kalmali.**

## K0.4 -- Simge ortmesi (kalibre arac; PR #305/#307)

`ortme_olc.py` (ACIL 2023-2024 uzerinde 154 olayi birebir ureten
kalibre arac), C1CELL karti + FERNUS diskiyle:

| olcum | deger |
|---|---|
| sag sutun simgesi | 1036 |
| ortme sinyali (UST SINIR) | 301 |
| etkilenen sayfa | 239 |
| diskin sagindaki en kucuk bosluk | **3 px** |
| eski (yanlis) metrik | 145 -- ortme olcusu DEGIL |

**301 UST SINIRDIR, ortme sayisi degil**: bant hem gercek soru metnini
hem kitap mobilyasini yakalar (bkz. GEO_DALGA_D_KESIF ek + PR #307).
Kesin sayi Faz 1 adim 2'de "sik satirinda bes etiket gorunuyor mu"
kapisiyla belirlenir.

**Diskin sagindaki bosluk 3 px** (ACIL 2023-2024'te 27 px'ti). Yani
beyazlatma payi en fazla gx+24 olabilir; daha genis pay soru numarasini
siler. Bu kitapta KAPI 6 (bkz. acil_geo_kirp.py) SART ve payi dar.

## K0.5 -- YENI YAPISAL ZORLUK: IC ICE SAYFA TIPLERI

ACIL 2023-2024 saf test kitabiydi (her sayfa soru). C1CELL DEGIL --
her konu su dort tipi IC ICE tasiyor (icindekilerden ve gozle):

| tip | ornek | soru/cevap var mi |
|---|---|---|
| Konu anlatimi (Konu Ogren) | s7 "DOGRUDA ACI" | HAYIR |
| Ciz Ogren (cozumlu ornek) | s12 | HAYIR (cozum var) |
| Beceri Temelli Sorular | s13 | EVET |
| Numarali TEST | s8-9 "TEST 1" | EVET |

Sonuc: ACIL 2023-2024'te ise yarayan "sutun basina simge sayisi ==
cevap sayisi" kapisi burada DOGRUDAN uygulanamaz -- konu anlatimi ve
Ciz Ogren sayfalarinda buyutec simgesi VAR ama cevap seridi girdisi YOK.
Faz 1 once sayfalari {anlatim, cozumlu, soru} diye SINIFLANDIRMALI,
sonra yalniz soru sayfalarindan kutu turetip cevaba baglamali.

Bu Faz 0'da hizli otomatik siniflandirma denendi (mavi zemin orani +
serit tespiti) ama kaba kaldi (mavi %15 esigi 3 sayfa buldu, serit
tespiti sayfa numarasini da sayip 326 yaniladi). Duzgun siniflandirici
-- kosan bolum adi + ust baslik + numarali soru varligi + cevap seridi
birlikte -- Faz 1'in ILK adimidir. Bu, ACIL 2023-2024'e gore ek is ve
ek risktir; fise acik yazildi.

Sekil hatti: geometri, kirpim zorunlu. Iki sutun (sol simge gx~0-50,
sag simge gx~350). Tek/cift sayfada simge kaymasi Faz 1'de olculur.

## K0.6 -- Mukerrer / baska kitapla ortusme

Yayinevi C1CELL, digerlerinden farkli; DB'de C1CELL kitabi yok. Wave D
kesfinde #3/#4 (Orijinal) ikizi vardi; C1CELL o ikizin parcasi DEGIL
(farkli kart 738x968, farkli yayinevi). Ayni sorunun baska kitapta
tekrari ithal aninda soru_hash kapisiyla yakalanir.

## K0.7 -- Konu agaci: ICINDEKILER TAM ve OKUNAKLI (s5-s6)

Iki sayfalik icindekiler her konuyu UC alt tiple veriyor: ana konu,
"(Ciz Ogren)", "Beceri Temelli Sorular" -- her birinin baslangic
sayfasiyla. Ana konular (baslangic sayfasi):

Dogruda Aci 7; Ucgende Acilar 15; Dik Ucgen 49; Ikizkenar Ucgen 78;
Eskenar Ucgen 89; Aciortay-Kenarortay ve Ucgenin Merkezleri 103;
Ucgende Benzerlik 124; Ucgenin Alani 145; Aci-Kenar Bagintilari 168;
Cokgenler 183; Dortgenler 200; Yamuk 213; Paralelkenar 228; Eskenar
Dortgen ve Deltoid 241; Dikdortgen 249; Kare 262; Cember ve Daire 277;
Kati Cisimler 322; Nokta ve Dogrunun Analitik Incelenmesi 353; Donusum
Geometrisi 385; Cemberin Analitik Incelenmesi 401 (Beceri Temelli
Sorular 414'e kadar).

**21 ana konu.** Mevcut `topic_hierarchy`de bu agacin birebir karsiligi
yok (GEO-U* agaci farkli granuler) -> Faz 1'de C1CELL-2024 onekiyle ayri
alt agac + migration gerekir (ACIL 2025 KURS'un 0034 deseninin aynisi).

## K0.8 -- GO / NO-GO ve maliyet

| kalem | deger |
|---|---|
| PNG | 416 |
| soru sayfasi | Faz 1 siniflandirmasi belirleyecek (< 408) |
| beklenen soru | siniflandirma sonrasi olculur (kaba: 1500-2000) |
| kirpim | zorunlu |
| ortme borcu | UST SINIR 301; kesin sayi Faz 1 adim 2 |
| beyazlatma payi | dar (3 px) -- KAPI 6 sart |
| anahtar | her testin sag sayfasinda serit, eksiksiz |
| DB ortusmesi | yok |

**Karar: GIT.** ACIL 2023-2024 boru hatti buyuk olcude yeniden
kullanilir, AMA iki yeni is var: (1) sayfa-tipi siniflandirici (Faz 1
adim 1), (2) beyazlatma payinin ACIL 2025 KURS gibi dar olmasi -- KAPI 6
payi bu kitaba gore yeniden olculecek.

**Sahip karari (19 Eyl 2026): yeniden yakalama YOK.** Wave D ekinde
FERNUS "Zenginlestirme ve Aktivite Dugmelerini Goster" kapali yeniden
yakalama onerilmisti; sahip okuyucuya giris yapamadigi icin bu yol
KAPALI. Butun Wave D kitaplari MEVCUT yakalamalarla, ACIL 2023-2024'te
kanitlanan yolla islenir: KAPI 6 (beyazlatma payi kitaba gore olculur)
+ ortme dislama (diskin ortttugu sorular ortulu isaretlenip islenmez,
ACIL 2023-2024'teki 151 soru gibi). Bu kitapta ekranin yeniden
acilmasina gerek yok.

## Olcum dosyalari (git disi, `backend/_geo1_gecici/`)

`faz0_c1.json` (simge/murekkep taramasi), `ortme_c1.json` (kalibre ortme),
`_waved_ortme.py`, `c1_*.png` (ornek sayfa/serit/icindekiler goruntuleri).

## Faz 1 -- Cevap seridi okumasi + kirpim kapisi (19 Eyl 2026)

**Serit okumasi.** 163 test-sonu cevap seridi (Faz 0'da `yayilim>300 &
mavi_px>200` ile tespit) 8 montaj halinde birlestirilip gorsel okundu.
Montaj kirpimi ONCE x=1180'de kesiliyordu; sag-sayfa anahtarlari (x~1269)
budaniyordu -- tam genislige (x 630-1290) cekildi. Sonuc: **1770 cevap**.
N dagilimi: 118 birim x 12, 34 x 8, 3'er 4/6/10, 2 x 11. Tum harfler A-E.

> UYARI: cevap harfleri su an PROVISIONAL (tek gorsel okuma). Faz 4
> ikinci-okuma dogrulamasi ice-aktarimdan once yapilacak. N sayilari
> saglam (seritteki son numara); kapi zaten N ile capraz dogruluyor.

**Kirpim kapisi (birim cevap-sayisi).** Her birim icin iki bagimsiz
sayimin esitligi aranir: (a) sayfa basina SIMGE sayisi (faz0 'yer'),
(b) test sonu cevap sayisi N. Segmentasyon "N'e geri topla": serit
sayfasindan geriye simge biriktir, toplam==N olunca birim baslar (onceki
serit sinirinda). Simge_toplam==N ise birim GECER (kirpima uygun).

**Sonuc: 163/163 gecti (1770 soru).** Ilk turda 4 birim bayrakti; hepsi
simge-dedektorunun yanlis-pozitifiydi (gorsel dogrulandi, `_anomali_montaj.png`):

| birim | sorun | duzeltme |
|---|---|---|
| s14 (p14) | 2 sekil/figur ogesi soru sanilmis | 2 konum kaldirildi -> 4 soru |
| s69 (p68) | ust konu-kutusu (pembe formul) isareti | 1 konum kaldirildi -> 4 soru |
| s148 (p148) | Heron formul kutusu isareti | 1 konum kaldirildi -> 4 soru |
| s150 (p149) | Sinus alan formul kutusu isareti | 1 konum kaldirildi -> 4 soru |

Ham `faz0_c1.json`'a dokunulmadi; yanlis-pozitifler
`c1cell_2024_geometri_simge_duzeltme.json` overlay'ine gerekceleriyle
yazildi, kapi/kirpim overlay'i uygular. Kapi mutasyon-dogrulandi: temizde
bayrak=0; bir N bozulunca ya da gercek bir simge cikinca bayrak artiyor.

**Committed ciktilar:**
- `backend/scripts/kitap/c1cell_geo_kapi.py` -- kapi scripti
- `veriseti/zkitap/cikti/c1cell_2024_geometri_cevap_anahtari.json` -- 1770 cevap (PROVISIONAL)
- `veriseti/zkitap/cikti/c1cell_2024_geometri_kapi_raporu.json` -- 163 birim segmentasyon + gecer
- `veriseti/zkitap/cikti/c1cell_2024_geometri_simge_duzeltme.json` -- 4 dogrulanmis duzeltme

**Kalan (Faz 3-4):** cevap-anahtari ikinci-okuma dogrulamasi (Faz 4);
gecen birimlerin kirpimi + ithal + konu agaci (Faz 3).

## Faz 4 -- Cevap anahtari dogrulama (19 Eyl 2026)

163 serit UC BAGIMSIZ okundu: benim ilk okumam + iki ajan (montajlari
ayri ayri, biri ters sirada). Uc-yollu diff: 158/163 sayfa oybirligi;
yalnizca 5 pozisyon (4 sayfa) uyusmazlik -- hepsinde iki ajan ayni,
benim ilk okumam farkliydi. Her biri yuksek-zoom (4x) yeniden
incelendi; 5'inde de ajanlar hakli cikti:

| sayfa | poz | ilk okuma | dogru | tam anahtar (duzeltilmis) |
|---|---|---|---|---|
| s20  | 10   | B    | D    | BEBCADCDCDDB |
| s30  | 7,8  | C,D  | D,C  | CDCCBDDCDDCD |
| s191 | 9    | B    | D    | CECCDEBBDDCC |
| s287 | 10   | E    | C    | CEEBADBBECAD |

Ilk okuma dogrulugu: 1765/1770 (%99.72). Duzeltmeler uygulandi; cevap
sayilari degismedi (yalnizca harfler), kapi 163/163 sabit kaldi. Cevap
anahtari artik DOGRULANDI (PROVISIONAL degil) -- ithale hazir.

## Faz 3a-3b -- Kirpim ve 1770 soru transkripsiyonu (21 Eyl 2026)

**Kirpim kutulari (simgeden, LLM tahmini degil).** Kart (591,46) 738x968;
kolon x<180 sol / >=180 sag; simge x paritede kayiyor (tek ~30/348, cift
~47/365). Kutu ust = simge_y-6, alt = ayni sutunda sonraki simge_y-9 ya da
sayfa alt siniri. Sol sutun x:[gx_sol+22, gx_sag+18], sag x:[gx_sag+22, 690].

> DUZELTME (Faz 3): alt sinir once "seritteki ilk mavi piksel" ile
> bulunuyordu; bazi sayfalarda seridin USTUNDE duran ince mavi bir oge
> siniri ~30 px yukari cekip SON sorunun siklarini kesiyordu (ajanlar
> yakaladi: ~35 soruda sik bos). Serit aslinda FERNUS'ta SABIT kart-ici
> y~896'da; dedektor "genis mavi bant tepesi" (satir mavi sayisi > 80,
> [885,905]'e kilitli, yoksa sabit 896) olarak yeniden yazildi.
> Ikinci duzeltme: sol sutun x1 = gx_sag+1 iken tasan son sik kesiliyordu
> (4 soruda E bos); x1 = gx_sag+18 yapildi (beyazlatilan disk boslugu,
> sag numaraya degmez).

**Dort kapi GECTI:** kutu==1770; her birimde kutu==cevap sayisi N;
ayni sutunda ortusme/kisa kutu yok; her kutuda murekkep var. Kutu uretimi
deterministik (yeniden calistirinca bayt-ayni cikti).

**Transkripsiyon.** 1770 kirpim 295 montaja (6'sar, etiketli) toplanip 12
ajanla soru-granuler okundu. Sonuc: **1770/1770**, tekil gorsel anahtari,
bozuk JSON yok, duplike yok, manifestle bire bir; bos govde yok. Yalnizca
4 soruda E sikki okunamadi (sol-sutun tasmasi) -- dordu de yuksek-zoom ile
elle okunup dolduruldu (s0133_sol_2=8, s0146_sol_1=48, s0330_sol_2=16,
s0390_sol_2=-3). 1 soruda siklar gorsel (`sikler_gorsel`).

**Dogrulama:** her sorunun cevabi var; her sorunun DOGRU sikki dolu;
birim soru sayisi == N (163/163). 6 soruda kirpim ile transkripsiyon
gozle karsilastirildi -- govde, bes sik ve sekil aciklamasi birebir.

**Konu agaci haritasi.** Icindekilerdeki 21 ana konu 5 bolume toplandi
(GEO-C1C24 oneki); her birim bas_sayfasindan konuya dusuyor (konusuz
birim: 0).

**Committed ciktilar:**
- `backend/scripts/kitap/c1cell_geo_kutu.py` -- kutu uretimi + 4 kapi
- `backend/scripts/kitap/c1cell_geo_kirp.py` -- kutulardan soru gorseli (disk beyazlatma)
- `veriseti/zkitap/cikti/c1cell_2024_geometri_kirpim_kutulari.json` -- 1770 kutu
- `veriseti/zkitap/cikti/c1cell_2024_geometri_metin.json` -- 1770 soru metni
- `veriseti/zkitap/cikti/c1cell_2024_geometri_konu_haritasi.json` -- 21 konu / 5 bolum

Gorseller git'e girmez; `c1cell_geo_kirp.py` ile yeniden uretilir.

**Kalan:** -- (Faz 3c ve 3d tamamlandi, asagi bkz.)

## Faz 3d -- PASIF ithal araci + e2e testler

**Kaynak sozlesmesi.** `C1CELL 2024 TYT-AYT Geometri Soru Bankasi` adi
`KAYNAK_KAYITLARI`'na eklendi (onek `C1CELL_GEO_2024`). Ad yazdirilabilir
ASCII; normalize anahtari mevcut 14 kaynagin hicbiriyle cakismiyor
(olculdu: `cakisan_kaynak` None dondu).

**Ithal araci.** `backend/scripts/kitap/c1cell_geo_ithal.py`,
`acil_geo_ithal.py` desenini izler: satirlar `is_active=FALSE`,
`is_public=FALSE`, `review_status='PENDING'`, `pedagogical_status='PENDING'`
yazilir; yazimdan sonra "aktif ya da kapidan gecen satir var mi" diye
sorulur ve varsa 3 ile cikilir.

**Konu atamasi BIRIM duzeyinde.** Kitabin konu sinirlari sayfa araligi
olarak basili. Soru duzeyinde atama yapilsaydi bir birimin sorulari konu
sinirinda ikiye bolunebilirdi. Olculdu: 163 birimin 163'u tek bir konunun
araliginda kaliyor; atama birimin sayfa KUMESI uzerinden dogrulanarak
yapilir, iki konuya yayilan birim gorulurse script DURUR.

**Yapisal kapilar (ithal oncesi, DB'ye dokunmadan).**

| kapi | olctugu sey |
|---|---|
| sayi | 1770 soru / 163 birim / 1770 anahtar / 1770 kutu |
| ortulu | 0 -- C1CELL'de disarida birakilan soru YOK |
| numara paritesi | basili numara == birim ici sira (1770/1770) |
| metin<->anahtar | iki BAGIMSIZ hattin cevabi ayni (1770/1770) |
| konu | her birim tek konuda; her konu soru aliyor (21/21) |
| satir | 5 dolu sik, dolu govde, dolu anahtar sikki, benzersiz hash |
| gorsel | her satirda kirpim var; kutu ile gorsel yolu tutarli |

**Kapilarin kapi oldugu OLCULDU.** 13 mutasyon uygulandi (soru sil, kutu
sil, kutuyu ortulu isaretle, metin cevabini degistir, anahtar cevabini
degistir, basili numarayi kaydir, birimi iki konuya yay, sayfayi harita
disina cikar, govdeyi bosalt, sik anahtarini dusur, anahtar sikkini
bosalt, ayni soruyu iki kez koy, konu kodu onekini boz). Ilk gecis 12/13
yakaladi: "kutuyu ortulu isaretle" sessizce geciyordu -- satir gorselsiz
ithal edilirdi ve 1519 soru sekilsiz anlamsiz oldugu icin bu sessiz kayip
kabul edilemez. Kapi eklendi, ikinci gecis **13/13**. Mutasyonlar
`test_c1cellgeo_ithal.py` icinde parametrik test olarak duruyor; kapi
ileride zayiflarsa CI soyler.

**Testler.** `backend/tests/e2e/test_c1cellgeo_ithal.py` (ithal, mutasyon
dahil) ve `backend/tests/e2e/test_c1cellgeo_konu_agaci.py` (harita <->
0035 migration birebir; sayfa araliklari s7..s414 bosluksuz). Ikisi de
canli DB istemez. Yerel kosu: 71 gecti. `test_acilgeo_ithal.py` ve
`test_kaynak_sozlesmesi.py` regresyon icin birlikte kosuldu: 74 gecti,
3 atlandi (DB isteyenler).

**Ithal HENUZ KOSULMADI.** Araci ve kapilar hazir; canli DB'ye yazma ayri
bir adim ve ayri bir karar.
