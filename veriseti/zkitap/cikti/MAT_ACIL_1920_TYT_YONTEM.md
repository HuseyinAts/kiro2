# 2019-2020 ACIL TYT Matematik Soru Bankasi -- yontem kaydi

Kaynak adi (DB): `2019-2020 ACIL TYT Matematik Soru Bankasi`, onek `ACL20T`.
Klasor: `screenshots/2019-2020-ACIL-TYT-Soru Bankasi` (Turkce harfli), 432 PNG,
FERNUS okuyucu 1920x1080; sayfa karti (589,43)-(1331,1022) = 742x979; zemin
krem (255,254,247); basili sayfa = dosya no. Sahip talimati (27 Eyl 2026):
"sirada ki islenmemis kitabi isle" -- tam otonom Faz 0-8.

Hicbir soru cozulmedi. Tek cevap kaynagi kitabin basili cevap seridi.
Okunamayan yer `[??]`; tahmin yazilmadi.

## 0. Tarama (`acil1920tyt_tarama.py`)

- Sayfa turu ust banttan: koyu (teal) bantli **test** sayfasi 265, acik
  bantli **on calisma** sayfasi 167. On calisma sorulari acik uclu ve sayisal
  cevaplidir -> kapsam disi (Start Matematik emsali).
- Test = ardisik test sayfalari; son sayfada sag altta sari cevap seridi.
  Olculen 95 test.
- Capa = kirmizi basili soru numarasi (227,41,45), her okuyucu simgesinin
  (69,39,160) sagindaki/altindaki pencerede (PENCERE -6..62 x 18..52).
  Simge x konumu tek sayfa L27/R357, cift L43/R371; numara x tek 50/377,
  cift 67/394 (tolerans 3). Sutun disindaki simgeler (s141 sekil ikonu,
  s367 fotograf) capa degil (`capa_olmayan_glif` 2). Ince "3" iki lekeye
  ayriliyordu -> genisletme (dilation).
- KAPI: test basina capa sayisi == seritteki hucre sayisi: 95/95, toplam 1203.

## 1. Cevap anahtari (`acil1920tyt_anahtar.py`)

- Serit kirpimlari (5x) iki bagimsiz gorsel okumayla okundu (A, B):
  1203/1203 hucre ayni.
- Ucuncu kanal: piksel glif en-yakin-komsu LOO. Gri harf esigiyle
  bolutlenen 1133 hucrenin 1133'u ayni. Glifin bolutleyemedigi 6 test
  (20, 25, 31, 40, 67, 82; 70 hucre) 5x gozle (C kanali) okundu: hepsi ayni.
- Dagilim A 133, B 226, C 349, D 317, E 178.
- Kapilar (testli): A==B, numara 1..N, A-E, glif uyumsuz yok, goz_c
  kapsami == glif disi testler, capa sayisi == serit.

## 2. Harita (`acil1920tyt_harita.py`) ve agac (0071)

- Icindekiler (dosya 3): 17 bolum, 32 konu, baslangic sayfalari.
- Her test tek bir konu araligina duser VE testin ust bandindaki konu adi
  (iki okuma, A==B) o konuyla eslesir. Basili esdegerler: KARMA -> Temel
  Kavramlar; EBOB-EKOK; KUMELER / KARTEZYEN CARPIM -> Kumeler-Kartezyen
  Carpim; GRAFIKLER -> Grafik.
- Icindekiler dizgi hatasi "EBOK-EKOK" dugum adinda "EBOB-EKOK";
  `icindekiler_adi` basildigi gibi korunur.
- Kodlar: bolum `MAT-ACL20T-Bnn`, konu `MAT-ACL20T-Bnn-Kmm`, MAT koku
  altinda (0071; 49 dugum, round trip).

## 3. Kirpim kutulari (`acil1920tyt_kutu.py`, `acil1920tyt_kirp.py`)

- Okuyucu diski: simge merkezi (gy+5, gx), yaricap 26, YALNIZ okuyucu
  renklerinde beyazlatilir. Diskin disindaki halkada (17-21 px, sag 90
  derece haric) kitap murekkebi olculur -> `ortme` (244 halka / 234 soru).
  Sag sutun diski sol sutun satir sonlarini ortuyor: altindaki yazi
  goruntude YOKTUR.
- Sutun sinirlari: tek L[45,356] R[370,700]; cift L[62,370] R[386,716]
  (kirmizi logo motifi disarida; kenar kapisi 0).
- Ust: numaradan yukari en az 10 bos satir, pay 3; tavan onceki numara ya
  da UST_BANT 76 (bant alti dekoratif cizgi y72-74).
- Alt: sonraki kutunun ustu; sutun sonunda SAYFA_ALTI 904 (en alt metin
  y902); seritli sutunda serit ustu - 12 (seridi saran mavi cerceve seridin
  ~8 px ustunde; ilk surumde 6 idi, cerceve cizgisi 7 kirpima giriyordu).
- Sayfa numarasi rozetinin mavi/kirmizi firca lekesi (y >= 880, x 320-440,
  doygun renk) beyazlatilir; sutun sonu kirpimlarinda leke kalmadi (olculdu;
  yalniz soluk pembe kalinti pikselleri).
- Kapilar: 1203 kutu == anahtar; kart ici; >= 40 px; cakisma yok; numara
  kutuda; seride girmiyor; sutun ici kutusuz murekkep yok. Yukseklik
  min 77 / medyan 343 / max 820.

## 4. Transkripsiyon (`acil1920tyt_metin_harness.py`)

- 29 grup (~36-45 kirpim), her grup ayri okuyucu; kirpim 2x. Matematik
  yazim sozlesmesi (eksi U+2212, kesir a/b, us x^2, kok, kume isaretleri,
  tablo ` | `), alti cizili `<u>`, komsu icerik `komsu_not`.
- Anahtar okuyuculara GOSTERILMEDI; metin kaydinda cevap alani yok (kapi).

### 4a. Ikinci okuma -- on kayitli TAM okuma

- `acil_1920_tyt_matematik_ikinci_okuma.json` okumadan ONCE kaydedildi.
  29 bagimsiz ikinci okuyucu, ilk okumanin dosyalarini acmadan.
- Karsilastirma: NFC, kesme/tirnak, eksi/tire tipi, U+22C5, tek karakterli
  us/indis parantezi, (gorsel)/(sekil) ve TUM bosluk/satir kirilimi
  normalize (yalniz bosluk farki olan 67 soru ayni sayildi).
- 160 farkli soru; 6 hakem kirpimdan gozle (4-14x, piksel dokumu) karar
  verdi: okuma_1 50, okuma_2 50, ikisi 9, yok 51. Ilk okuma esasli hata
  59/1203, ikinci okuma 59/1203. Karar `duzeltme.json` ile ilk okumanin
  yerine gecer (160 soru).
- SINIR: iki okumanin AYNI bicimde atladigi sekil verisi (orn. sekil
  icindeki etiket) karsilastirmada gorunmez. Ogrenci her zaman tam soru
  kirpimini gorur (`question_image_url`).

### 4b. Okunamaz -> `[??]`

- 192 soruda gorunen alanda `[??]`: 188'i ortme olcumunde (disk satir
  sonunu ortuyor), 4'u hakemin okunamaz dedigi soluk isaret. Bayrak
  `okunamaz_isaret`; beta kapisinda disarida.

## 5. Mukerrer olcumu (`acil1920tyt_mukerrer.py`)

- DB: MATEMATIK/GEOMETRI + bu kaynak ve eski hat adi (16606 satir).
  Govde 3-gram Jaccard (normal bicim) + sik eslesmesi; GUCLU = 3-gram
  >= 0.9 VE >= 3 sik birebir. Pozitif kontrol 25/25 = 1.0.
- Kitap ici tekrar 0. GUCLU aday 14 (eski hat + ACIL'in diger yillari);
  hicbirinde cevap farki yok.
- Tam hash carpismasi 2: T093_06 (eski hat satiri, eski id semasi farkli)
  ve T092_04 ('2023-2024 ACIL TYT Matematik' kitabinda aktif).
- Eski hat '2019-2020-ACIL-TYT-Soru Bankasi': 9 satir (MATEMATIK 8,
  GEOMETRI 1), 5'i modern karsilikli; cevaplari basili anahtarla ayni.

## 6. Ithal (`acil1920tyt_ithal.py`)

- PASIF: is_active/is_public FALSE, review PENDING, is_ai_generated TRUE.
- 1203 satir yazildi (DB'de ayni id yok). Konu duzeyi baglama; subject_area
  MATEMATIK; cevap kanali iki_okuma+glif 1133, iki_okuma+goz(5x) 70.
- Gorseller `d-dataset/output/crops/ACL20T/ACL20T-Tnnn_ss.png` (git disi;
  `acil1920tyt_kirp.py` kutulardan yeniden uretir).
- Bayraklar: kaynak_kusuru 360, okuyucu_diski_ortme 234, okunamaz_isaret
  192, mukerrer_aday 13, sik_tekrar 24, sikler_gorsel 28,
  db_hash_carpismasi 2.

## 7. Eski hat pasif (0072_acl20t_eski_hat_pasif)

- Modern karsiligi DB'de olan 5 eski satir is_active=FALSE (GUNLUK ile
  geri alinir); 4 eski satir aktif kalir. Silme yok.

## 8. Beta onayi (0073_acl20t_beta_onay)

- 1203 - 192 (`[??]`) - 1 (aktif hash ikizi T092_04) = **1010** satir
  acildi: quality_review_status auto_judged_high, review APPROVED,
  onay_turu toplu_beta_sahibi, bireysel_denetim_yapildi=false.
  human_verified yazilmaz; is_ai_generated / is_public'e dokunulmaz.
- Round trip (upgrade / downgrade / upgrade) yerel DB'de denendi.

## Testler

- `backend/tests/e2e/test_acil1920tyt_veri.py`: anahtar, mutasyonlar,
  harita, 0071, capa/kutu, leke beyazlatma, metin, ikinci okuma, mukerrer,
  0072/0073.
- `backend/tests/e2e/test_acil1920tyt_ithal.py`: veri butunlugu, yapisal
  kapi, konu baglantisi, sozlesme, ASCII, durustluk, mutasyon.
