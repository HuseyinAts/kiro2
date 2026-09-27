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
* Sutun ayraci: olculen dikey cizgi parite varsayilanindan (372 / 369)
  CIZGI_SAPMA = 6 px'ten fazla saparsa varsayilan kullanilir. s104 ve
  s138'de 'OSYM KOSESI' cercevesinin dikey kenari (x 388) ayrac sanilmis,
  sag sutun kirpimi soldan kesilmisti (T050_03/04, T067_03 numarasiz
  okundu); duzeltme sonrasi 7 kirpim yeniden kesildi ve yeniden okundu.
* 2070 kutu, kapi ihlali 0; ortme suphesi 260 soru; kenar kapisi 0.
* Gorsel QA: ortak parca, kose, oncullu ve rastgele kirpimlar gozle.

## 4. Transkripsiyon (`tur345tyt_metin_harness.py`)

`345_2025_tyt_turkce_metin.json` (2070 soru). Kirpimlar 2x Lanczos; 43
grup (test sinirina hizali, ~48 soru), 43 ayri okuyucu. Talimat
`VeraFilm/to_metin_talimat.md`: 'kitap ne yaziyorsa o', soru cozme yok,
dil bilgisi / yazim kuraliyla karar VERME (yazim ve noktalama sorularinin
siklarindaki kasitli yanlislar ve dizgi hatalari basildigi gibi), anahtar
gosterilmedi; alti cizili `<u>`; tablo ` | `; ortak parcali sorularda
`ortak_baslik` ('1 - 2').

Kapilar (harness `kapi`): KAPI1 her kirpim bir kez; KAPI2 basili no ==
test ici sira; KAPI3 bes sik dolu; KAPI4 toplam 2070. **TUM KAPILAR
YESIL.** Null numara 0 (sutun ayraci duzeltmesinden sonra). Kaynak kusuru
notu 371 soru (cogu dusuk cozunurlukte iki adayli isaret). Etiket 71
(TYT 56, MSU 15); ortak_baslik 20 soru = 10 grup, kutu asamasiyla ayni.

### 4a. Ikinci okuma -- on kayitli TAM okuma

On kayit (`345_2025_tyt_turkce_ikinci_okuma.json`, karsilastirmadan
ONCE): ilk okumayi gormeyen 43 ayri okuyucu, ayni gruplar (teslim dizini
`to_metin_parca2`). Karsilastirma `_p345_gecici/tt_metin_karsilastir.py`.

* Normalizasyon (NFC, kesme / tirnak tipi, eksi / tire tipi, orta nokta,
  uc nokta, bosluk dolduran tire dizisinin uzunlugu, tire cevresi bosluk,
  bosluk) sonrasi 1906 soru ayni, 164 soru farkli (govde 118, sik 65,
  alti cizili kapsam 4; basili_no / sekil_var / etiket / ortak_baslik
  farki 0).
* 164 farkin hepsi 6 hakem partisinde kirpimdan gozle (4-16x NEAREST,
  piksel dokumu, ayni sayfadaki kesin virgul / nokta / tirnak ornegiyle
  yogunluk karsilastirmasi) karara baglandi (talimat
  `VeraFilm/to_hakem_talimat.md`): 5 yalniz bicim, 65 ilk okuma, 76
  ikinci okuma, 18 ikisi hatali.
* **Ilk okuma esasli hata 83 / 2070 (%4.0)**; ikinci okuma 94. Hata
  turleri: tek / cift tirnak; virgul / nokta, noktali virgul / iki nokta;
  sapka (edebi / milli (sapkali)); alti cizili kapsamin siniri; ekteki tek harf
  (tuttumaya, vermekte / vermekle); madde isareti. Kitabin dizgi hatalari
  ('tuttumaya', 'Sacima' vb., iki 'B)' sikki) korunur.
* Sinir: sayfa goruntusu ~742 px genislikte. Tek / cift tirnak ve
  virgul / nokta kararlarinin bir kismi (hakem gerekcelerinde 'orta
  guven') piksel yogunluguna dayanir; bu isaretler soru anlamini
  degistirmez, noktalama sorularinin siklari ise hakemce tek tek buyutuldu.

### 4c. Okunamaz -> `[??]`

Hicbir soruda gercekten okunamayan karakter kalmadi; belirsiz tek
karakterler en iyi okuma + aday olarak `kaynak_kusuru`nda.

## 5. Mukerrer olcumu (`tur345tyt_mukerrer.py`)

`345_2025_tyt_turkce_mukerrer_adaylari.json` (ithalden ONCE). KMT345
normal bicimi + kesme / tirnak tipi tek bicim + `<u>` silinir; govde
karakter 3-gram Jaccard (ters indeks). GUCLU = 3-gram >= 0.9 VE >= 3 ayni
sik. DB: TURKCE / EDEBIYAT (OSYM ve Paragraf kitabi dahil) + bu kaynak ve
eski hat adlari: 7121 satir.

* Pozitif kontrol: her 50. govdenin tirnak tipi degismis, bosluklari
  bozulmus, `<u>` sarili hali kendi sorusuna 1.0.
* Tam hash carpismasi 4: T041_07, T044_07, T045_08, T069_06 == '345 2025
  Paragraf Sifir Risk' satirlari (ayni yayinevi ayni cikmis sorulari
  basmis). Eski hatla ayni hash yok.
* Kitap ici: ayni hash yok, yakin cift yok (ortak parcali ciftler ayni
  govdeyi tasir ama siklari farkli).
* Eski hat uc aktarim: '345 2025 Tyt Turkce' 18 satir (10 modern
  karsilik), '345 Tyt Turkce' 11 (5), '345 Yayinevi TYT Turkce ... 2025'
  2 (2). Karsiliksiz 14 (esik alti ya da sik metni farkli).
* GUCLU aday 30 (eski hat 17, Paragraf 7, OSYM 2025 TYT 3, Aktif Ogrenme
  Dilbilgisi 3).
* Cevap harfi farki 95 (cogu zayif, 3-gram < 0.9); GUCLU olanlarin 3'unde
  DB'nin dogru sikkinin METNI bizde basili anahtarin harfinde (OSYM
  satirlari; kitap siklari yeniden siralamis), 4'unde icerik farki
  (hepsi eski hat: T020_09, T043_01, T080_04, T199_01; 0069 ile pasif).
  Bizim cevap her zaman basili anahtar; degistirilmez.

## 6. Ithal (`tur345tyt_ithal.py`)

PASIF ithal (is_active FALSE, is_public FALSE, review PENDING); kaynak
sozlesmesi `TRT345`. 2070 kayit uretildi; 4'u (yukaridaki hash
carpismasi) ayni id ile Paragraf kitabinda var -> `ayristir` YABANCI,
dokunulmadi; 2066 yeni satir. DB'de bu ithalin satirlari is_active 0,
kapidan gecen 0.

* `subject_area` TURKCE; konu testi (KO / OT / OR) konu dugumune, Karma
  testi (KA) unite dugumune (`konu_eslesme_duzeyi`); tur ile duzey
  baglamada kapi.
* Cevap kanali: `iki_okuma+glif` 2064, `iki_okuma_farki+goz(5-6x)+glif` 3
  (T071#4, T086#7, T173#4), `iki_okuma+glif_uyumsuz+goz_teyidi(5x)` 3
  (T120#3, T143#10, T180#8).
* Ortak parca: 10 takip sorusunun gorseli parca + 8 px + soru
  (`gorsel_boyu`, `ortak_parca_basligi`, `ortak_parca_ilk_soru`).
* Bayraklar (2070 kayit): kaynak_kusuru 371, okuyucu_diski_ortme 260,
  cikmis_soru 71 (TYT / MSU), mukerrer_aday 28, sik_tekrar 4, sikler_gorsel
  3, diger_kaynak_cevap_farki 4, diger_kaynak_sik_sirasi_farkli 3,
  db_hash_carpismasi 4.
* Kirpimlar `d-dataset/output/crops/TRT345/` (2070 PNG; boyut == kutu,
  ortak parcalilarda + parca + 8; olculdu, hata 0).

## 7. Eski hat pasif (0069_trt345_eski_hat_pasif)

Faz 5'te modern karsiligi GUCLU olan 17 eski satir (10 + 5 + 2)
`is_active=FALSE`; SILINMEZ. Guard: eski kaynak adi, ithal_araci yok,
aktif, VE modern karsilik bu kitabin ithal satiri olarak DB'de var.
Cevabi basili anahtardan farkli 4 satir bunlarin icinde. Karsiliksiz 14
eski satir aktif kalir. Yerel: 17 aday, 17 pasif.

## 8. Beta onayi (0070_trt345_beta_onay)

Kapi yuku olculdu (0069 sonrasi): pending 2066/2066, servis disi bayrak 0,
gorunen alanda `[??]` 0, bos sik / cevap 0, gorselsiz 0, konu bos 0,
aktif hash cakismasi 0. Hedef 2066; toplu beta sahibi onayi
(auto_judged_high, APPROVED; human_verified yazilmaz; is_ai_generated /
is_public dokunulmaz). 5 konsensus sinyali.

Yerel tur (0068 -> head -> 0068 -> head): head'de 2066 aktif / 2066 onay /
2066 kapida, eski hat 14 aktif; tabanda 0 aktif, eski hat 31 aktif; aktif
tekrar hash 0 her adimda.

## Testler

`backend/tests/e2e/test_tur345tyt_veri.py` (52): anahtar hamdan birebir,
toplamlar, farklar goz + glif, test turleri; A/B / gereksiz / yabanci /
'?' goz / bicim disi / kimlik / hucre-numara / teyitsiz glif mutasyonlari;
harita hamdan birebir, sayilar, bant (tur, no) / konu / icindekiler / A-B
mutasyonlari; migration == harita, kimlik; kutu kapilari, kutu <-> cevap,
blok ustu, kose yan satir, ortak parca, tavan, sutun ayraci sapmasi
(mutasyon: CIZGI_SAPMA=99 -> 388 doner); metin kapilari + kapi
mutasyonu, null numara yok, metin == kutular, kivrik kesme / numara notu
yok, ikinci okuma on kaydi + sonuc sayilari, duzeltmeler uygulanmis,
[??] yok, etiketler, ortak baslik == kutu gruplari.
Mukerrer (bolum 6, +7): ozet, eski hat uc aktarim, hash carpismasi
(Paragraf), hash degeri yazilmadi, cevap farki sik sirasi / icerik,
pozitif kontrol ve normal bicim, indeksli Jaccard == dogrudan.
Migration (bolum 7, +8): 0069 kimlik / zincir / ASCII, ciftler olcumden
turer, guard, durustluk; 0070 kimlik, dislama kurali, hedef 2066,
durustluk.
`backend/tests/e2e/test_tur345tyt_ithal.py` (56): veri seti butunlugu,
yapisal kapilar, test ici sira, cevap kanali, konu / unite dugumu ==
migration, ortak parca gorsel boyu, Paragraf hash ikizi ayni id,
sozlesme, ASCII, pasif sozlesme, cikmis, bayrak capalari, mukerrer
bayraklari, mutasyonlar (yapisal 9, on kontrol 8, baglama 9).
