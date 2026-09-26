# 345 2025 Start Matematik -- kesif olcumleri ve isleme plani

Tarih: 25 Eyl 2026. Durum raporundaki (ZKITAP_KITAP_DURUMU.md, 345 tablosu)
sira: ISLENEBILIR olan ilk 345 kitabi. Bu belge Faz 0 olcumlerini ve
sonraki fazlarin planini tutar; her iddia asagidaki olcumlere dayanir.

## 0. Kesif olcumleri (salt okuma, 25 Eyl)

| olcu | deger | nasil |
|---|---|---|
| klasor | `veriseti/zkitap/screenshots/345 2025 Start Matematik` | - |
| PNG | 320 sayfa (`sayfa_0001..0320`, bosluk yok) + 3 `_enhanced_*` (1024x576, kullanilmaz) | dosya listesi |
| cozunurluk | 1920x1080, kart (589,43)-(1331,1020) = 742x977 (diger 345'lerle ayni) | olculdu |
| basili sayfa | dosya - 1 (s3 icindekiler 'Sayfa (3)' = dosya 4; dosya 11 alti '10') | gozle |
| sekme basligi | '2025 start matematik' | gozle |
| icerik | 16 unite (icindekiler dosya 3 'KITAP BITIRME PLANI') | gozle |
| sayfa turleri | 'SINAVA GECIS' test sayfasi 90; '0'DAN BASLA' konu sayfasi 100; digeri 130 (cift sayfalar, ayrac, NOTLARIM) | baslik renk siniflamasi |
| test | 45 test x 2 sayfa (baslik numarasi montajdan gozle: her test tam 2 sayfa) | `sg_basliklar.png` |
| cevap | HER test sayfasinin altinda, sutun basina basili satir ('1.C 2.B 3.E' / '4.A 5.C 6.E'); 90/90 sayfada serit murekkebi var, test disi sayfada yok (s1-2 kunye haric) | olculdu + gozle |
| soru tahmini | ~372 (okuyucu diski sayimi, 90 sayfada 3-6); kesin sayi anahtar seridinden | disk bilesen sayimi |
| konu sayfalari | acik uclu alistirmalar ('islemin sonucu kactir?', siksiz) + ara ara 'ISINDIRMA KOSESI' coktan secmeli kutusu; BU SAYFALARDA ANAHTAR YOK | gozle (dosya 7) |
| eski hat | 3 satir, 3'u AKTIF (s194/203/209; 'Dortgenin alanini bulmak icin hangi formul kullanilir?' gibi genel metinler; biri subject_area GEOMETRI) | DB |
| baska kitapla ortaklik | 345 TYT Matematik SB %0, 345 2024 TYT Mat %0 (durum raporu bolum 8) | onceki olcum |

Unite -> test sayfalari (dosya no; unite baslangici icindekiler + 1):

| unite | baslik | baslangic | test sayfalari | test |
|---|---|---|---|---|
| 01 | Toplama ve Cikarma Islemi | 4 | 11-16 | 3 |
| 02 | Carpma ve Bolme Islemi | 18 | 33-36 | 2 |
| 03 | Islem Onceligi | 38 | 47-50 | 2 |
| 04 | Harfli Ifadeler | 52 | 65-68 | 2 |
| 05 | Basit Denklem Cozumu | 70 | 81-88 | 4 |
| 06 | Rasyonel Sayilar | 90 | 113-120 | 4 |
| 07 | Ondalik Gosterim | 122 | 137-142 | 3 |
| 08 | Sayi Kumeleri | 144 | 157-160 | 2 |
| 09 | Oran ve Oranti | 162 | 171-174 | 2 |
| 10 | Rasyonel Denklemlerin Cozumu | 176 | 185-188 | 2 |
| 11 | Iki Bilinmeyenli Denklemler | 190 | 197-200 | 2 |
| 12 | Basit Esitsizlikler | 202 | 213-218 | 3 |
| 13 | Mutlak Deger | 220 | 233-238 | 3 |
| 14 | Uslu Ifadeler | 240 | 261-268 | 4 |
| 15 | Koklu Ifadeler | 270 | 291-298 | 4 |
| 16 | Carpanlara Ayirma | 300 | 315-320 | 3 |

Her test sayfasi kendi unitesinin araliginda: 90/90.

## 1. Kapsam karari (varsayilan; sahip degistirebilir)

* KAPSAM ICI: 45 'Sinava Gecis' testinin tum sorulari (anahtar basili).
* KAPSAM DISI: konu sayfalarindaki acik uclu alistirmalar (sik yok,
  anahtar yok) ve 'Isindirma Kosesi' coktan secmelileri (anahtar basili
  DEGIL; soru cozmek yasak). Olculdu (Faz 3): Isindirma Kosesi 83 kutu; acik uclu alistirmalar sayilmadi.
* RISK: kitap dosya 320'de (basili 319) U16 Test 3'un ikinci sayfasiyla
  bitiyor. Diger 3-testli unitelerle (U1, U7, U12, U13) tutarli; arka kapak /
  arka madde yakalanmamis olabilir. Test sorulari eksiksiz gorunuyor; Faz 1
  test ici numara surekliligi bunu dogrular.

## 2. Fazlar

Sablon: 345 TYT Matematik hatti (`mat345tyt_*`, ayni yayinevi, ayni sayfa
alti anahtar satiri) + PRG345 dersleri (ortme kenar kapisi, sahipsiz
murekkep, ikinci okuma on kaydi, kitap ici tekrar, beta migration'i).
Dosya oneki `stm345_*`, onek `STM345`, kod oneki `MAT-345S25`.

### Faz 1 -- Tarama ve cevap anahtari (`stm345_tarama.py`, `stm345_anahtar.py`) -- TAMAM 25 Eyl

Sonuc (`STM_345_YONTEM.md` bolum 1): 45 test, 371 cevap; A == B 371/371,
glif LOO 358/359, 13 girdi 10x gozle; butun kapilar yesil.

1. Sayfa siniflamasi betige alinir (baslik rengi), 90 test sayfasi kilitlenir.
2. Serit kirpimi: kart y ~905-925 (ekran y ~960), sol/sag sutun ayri; 5x ve 7x montaj.
3. Okuma A (sayfa sirasi, 5x) ve okuma B (ters sira, 7x) bagimsiz; girdi
   sayisi okuyucuya soylenmez. Hedef A == B, farklar 10x gozle.
4. Ucuncu kanal: harf glifi en-yakin-komsu LOO (B/E, C/G ayrimi).
5. Kapilar: test ici numara 1'den kesintisiz; sayfa gecisi 'devam' ya da
   'yeni test 1'; her sayfadaki serit numaralari == o sayfadaki disk sayisi.
6. Cikti: `345_2025_start_matematik_{cevap_anahtari,ham_okumalar}.json`.

### Faz 2 -- Konu agaci (migration 0057) -- TAMAM 25 Eyl

Sonuc (`STM_345_YONTEM.md` bolum 2): 16 dugum MAT-345S25-U01..U16; ayrac
== icindekiler 16/16, bant 90/90; round-trip temiz.

16 unite dugumu, MAT kokunun altinda `MAT-345S25-U01..U16`, adlar
icindekiler sayfasindan birebir (ASCII katlanmis); testler unite dugumune
baglanir (`konu_eslesme_duzeyi` = 'unite'). Bandtaki konu adi == unite
adi kapisi. Kaynak adi DB'deki eski hat adiyla ayni ('345 2025 Start
Matematik'); ASCII disi karakter yok -> ad migration'i gerekmez (Faz 1'de
teyit edildi: DB'deki 3 eski satirin adi birebir bu).

### Faz 3 -- Kirpim kutulari (`stm345_kutu.py`, `stm345_kirp.py`) -- TAMAM 25 Eyl

Sonuc (`STM_345_YONTEM.md` bolum 3): 371 kutu, kapi ihlali 0, 371 kirpim
gozle; yanlis simge (s83 sekil) halka olcusuyle elendi; ortme 6 soru;
Isindirma Kosesi 83 (kapsam disi).

1. Capa: basili soru numarasi + okuyucu diski (iki kanal); anahtar
   seridindeki numaralar hangi capanin dogru oldugunu secer.
2. Serit bandi ve sayfa numarasi kutunun disinda (sizinti kapisi:
   hicbir kutu serit ust sinirini gecmez).
3. Baslik bandi ('SINAVA GECIS n', unite adi, 'Simdi Sinava Isinalim'
   rozeti) kutu disinda.
4. Ortme kapisi: disk kenar halkasinda notr murekkep -> `okuyucu_diski_ortme`.
5. Sekil / grafik / tablo iceren sorular `sekil_var`; sik gorsel ise
   `sikler_gorsel` (dosya 320'de kesirli siklar, ussel ifadeler).
6. Kirpimlar `d-dataset/output/crops/STM345/` (gitignored).

### Faz 4 -- Transkripsiyon (`stm345_metin_harness.py`) -- TAMAM 26 Eyl

Sonuc (`STM_345_YONTEM.md` bolum 4): 371 soru, kapilar yesil; TAM ikinci
okuma (on kayitli); 54 fark piksel/6x ile hukum; soluk '+' taramasi iki
okumanin ortak 2 hatasini buldu; 6 soru [??].

1. Talimat: 'kitap ne yaziyorsa o'; matematik icin tutarli duz metin
   gosterimi (MAT345TYT talimatiyla ayni: us '^', kesir 'a/b', kok
   'sqrt()', mutlak '|x|'); anahtar gosterilmez; soru cozulmez.
2. ~40 soruluk gruplar (test sinirina hizali), ayri okuyucular.
3. Kapilar: her kirpim bir kez; basili no == test ici sira; bes sik dolu;
   toplam == anahtar girdi sayisi.
4. Ikinci okuma: ONCE on kayitli orneklem (her gruptan 8, sabit tohum),
   CP95 ust siniri <= %3 degilse TAM ikinci okuma; farklar kirpimdan 3x
   gozle.

### Faz 5 -- Mukerrer ve eski hat (`stm345_mukerrer.py`) -- TAMAM 26 Eyl

Sonuc (`STM_345_YONTEM.md` bolum 5): DB tam hash carpismasi 0; kitap ici
tekrar 0; 16235 MATEMATIK/GEOMETRI satirina karsi GUCLU aday 0 (en yuksek
govde 3-gram 0.847, 15 aday >= 0.75 gozle hepsi farkli formul); cikmis
soru etiketi 0. Eski hat 3 satir kitapta YOK -> pasif onerisi.
Olcu degisti: kelime Jaccard matematikte bos cikti (369 aday / 111
'guclu', hepsi yanlis pozitif); formulu koruyan 3-gram kullanildi.

Plan (ilk hali):
1. `soru_hash` ile DB geneli kesin cakisma; govde Jaccard >= 0.75 VE >= 3
   sik birebir -> `mukerrer_aday` (ozellikle 'Simdi Sinava Isinalim'
   rozetli sorular cikmis soru olabilir -> OSYM satirlariyla).
2. Kitap ici tekrar (ayni hash) -> `kitap_ici_tekrar`.
3. Eski hat 3 satir: basili s194/203/209 (dosya 195/204/210) sayfalarinda
   gozle aranir. Kitapta YOKSA ikiz degil, uydurma satirdir -> pasif onerisi
   (SAHIP KARARI).

### Faz 6 -- Ithal (`stm345_ithal.py`) + kaynak sozlesmesi
PASIF ithal; TYT / MATEMATIK; sinif 12 (ev sozlesmesi); `ithal_araci`,
`telif`, bayraklar, `cozum_dogrulamasi` = 'yapilmadi_urun_karari'.
`kaynak_sozlesmesi.py` girdisi. Kirpimlar `/static/crops/STM345/`.

### Faz 7 -- Testler, belge, PR
`test_stm345_veri.py` (ham okumadan yeniden turetme, kapilar,
mutasyonla dogrulanmis) + `test_stm345_ithal.py`; `STM_345_YONTEM.md`;
durum raporu satiri. Git akisi: dal -> adla ekleme -> PR -> CI kirmizi
kumesi == miras kume -> squash.

### Faz 8 -- Aktiflestirme (AYRI sahip karari)
0056 deseni: kapi yuku olculur, uc kilit acilir, gunluklu geri alinabilir.

## 3. Sahip kararlari (bu plan varsayilanla ilerler)

1. KARAR VERILDI (25 Eyl): Isindirma Kosesi / acik uclu alistirmalar kapsam disi.
2. Eski hat 3 satirin akibeti: OLCULDU (Faz 5) -- uc satir da kitapta
   yok; pasif onerisi SAHIP KARARI bekliyor.
3. Aktiflestirme (Faz 8).
