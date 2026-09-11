# Veritabani Tam Denetimi -- 9 Eylul 2026

Kapsam: `kiro2` PostgreSQL veritabaninin TAMAMI. 255 tablo, 940 indeks, 141 MB.
Yontem: her rakam canli veritabaninda `count(*)` / `pg_total_relation_size` /
`information_schema` sorgusu ile olculdu. Tahmin yok, orneklem yok.

Olcum betikleri: `backend/_ci_art/db_envanter.py`, `db_yedek_analiz.py`,
`db_kalite2.py`, `db_butunluk.py`, `db_irt_agac.py`, `db_yapi.py`,
`db_kod_uyum.py`, `kod_erisim.py`, `db_kritik.py`.

---

## 0. Yonetici ozeti

Bes bulgu, onem sirasina gore:

1. **`billing_subscriptions` tablosu YOK, ama onu sorgulayan endpoint CANLI.**
   Kesin 500. Bunu yakalayan test Backend Tests'te kosuyor ve su an kirmizi
   (bolum 7.2); gormeyen yer yalnizca `golden-flows.yml`.
2. **Aktif alembic zinciri 4 dosya.** `billing_subscriptions`, `kvkk_data_*` ve
   `video_cache` tablolarini yaratan migration'larin tamami `versions_archive/`
   altinda. Temiz bir kurulumda bu tablolar ASLA olusmaz.
3. **Yedekteki 36.967 soru kurtarilamaz -- halusinasyon.** Eksik derslerin
   (FIZIK, BIYOLOJI, GEOMETRI, EDEBIYAT) oradan geri getirilmesi mumkun degil.
   20 Agustos temizligi DOGRU bir karardi.
4. **IRT calismiyor.** 5.796 sorunun 5.776'si kalibre degil, `irt_n_responses`
   TUM satirlarda 0. Yani mevcut `irt_difficulty` degerleri ogrenci verisinden
   gelmiyor -- uretilmis sayilar.
5. **Semantik arama olu.** `vector(1536)` kolonu ve pgvector 0.8.2 kurulu,
   ama 5.796 satirin 5.796'sinda `embedding IS NULL`.
6. **FSRS araliklamiyor** (bolum 5.5, cozum turunda bulundu). 107 kartin
   106'sinda `stability=2.3`, `scheduled_days=0`; `reps=40` olan kart bile
   hep "bugun tekrar et" durumunda. Aralikli tekrarin cekirdek vaadi
   calismiyordu.

---

## 1. Envanter

| Olcut | Deger |
|---|---|
| Tablo | 255 |
| Indeks | 940 |
| Veritabani boyutu | 141 MB |
| Dolu tablo | 53 |
| Bos tablo | 202 |
| Toplam satir | 184.611 |

202 bos tablonun tamami "olu sema" degil: `env.py:65` zaten "108 tablo henuz
DB'de olusturulmamis (gelecek ozellikler icin model var)" diyor. Ama 202 sayisi
sadece "hic kullanici yok" ile aciklanamaz -- asagidaki bolum 7 farki ayiriyor.

---

## 2. Yedek/cop tablolari -- 34,9 MB, veritabaninin ~%25'i

Dokuz tablo:

| Tablo | Satir | Boyut |
|---|---|---|
| question_content_cop_yedek_20260820 | 36.967 | 11 MB |
| question_statistics_cop_yedek_20260820 | 36.967 | 9256 kB |
| question_metadata_cop_yedek_20260820 | 36.967 | 7720 kB |
| question_bank_cop_yedek_20260820 | 36.967 | 6696 kB |
| question_statistics_terfi_yedek_20260820 | 3.979 | 344 kB |
| student_answers_is_correct_yedek_20260827 | 546 | 136 kB |
| question_statistics_terfi_yedek_tur_20260907 | 919 | 136 kB |
| question_statistics_terfi_yedek_r2_20260907 | 509 | 72 kB |
| question_statistics_terfi_yedek_sos_20260907 | 446 | 72 kB |

Dokuzunun da PRIMARY KEY'i yok (ayrica `temp_import` tablosu da PK'siz).

### 2.1 Yedekteki 36.967 soru neydi?

Ders dagilimi -- canlida EKSIK olan her ders burada VAR:

```
Genel 17.826 | MATEMATIK 7.816 | GEOMETRI 2.589 | FIZIK 2.307
EDEBIYAT 1.709 | TURKCE 1.543 | KIMYA 1.201 | TARIH 702
BIYOLOJI 584 | SOSYAL 337 | FEN 223 | COGRAFYA 130
```

Canli tablo ile id kesisimi: **0**. Yani yedekteki 36.967 sorunun tamami
canlida yok, canlidaki 5.796 sorunun tamami yedekte yok. Iki ayri kume.

Ilk hipotezim "veri kaybi, geri getirilebilir" idi. **Yanlis cikti.** Icerigi
olctum:

| Olcut | Canli (5.796) | Yedek (36.967) |
|---|---|---|
| Benzersiz soru metni | 5.739 | 34.330 |
| Bos secenek A / E | 0 / 0 | 106 / 116 |
| Aciklamasiz soru | 1.929 | **36.967 (tamami)** |
| Ortalama metin uzunlugu | 269 karakter | 131 karakter |

Yedegin en cok tekrar eden metinleri:

```
"Asagidaki ifadelerden hangisi dogrudur?"                      169 kez
"Bir dik ucgenin dik acilari arasindaki acilar toplami..."     154 kez
"Gorseldeki tum metni dikkatli oku ve JSON formatinda cikar."   84 kez
```

Ucuncu satir bir SORU degil -- OCR pipeline'inin **prompt metni**, soru
alanina sizmis. Ikinci satir matematiksel olarak sacma ("dik acilari"
coguldur) ve FIZIK olarak etiketlenmis.

FIZIK etiketli ornekler (birebir):

- "Duzenli motion ucagi icin, pilotun ucagina etki eden kuvvetlerin sirasi..."
  (Ingilizce "motion" kelimesi metne sizmis, secenekler arasinda "uzay direnci")
- "Harmonik, hamartali gomulu devir ve hamartali titreme" (anlamsiz)

"Genel" etiketli ornek: *"Kesinlikle bir matematik sorusu degil, bir metin
parcasi iceriyor. Bu metin parcasi Turkce YKS matematik sinavi icin bir ornek
soru degildir."* -- bu modelin RET cevabi, soru olarak kaydedilmis.

**Sonuc: yedek kurtarilabilir icerik degil. 20 Agustos'ta 36.967 halusinasyon
sorunun temizlenmesi dogru bir karardi.** Eksik dersler oradan gelmez.

**Karar sende (veri silme):** dokuz yedek tablonun DROP edilmesi 34,9 MB
kazandirir. Ben veri silmiyorum -- onay verirsen migration'i yazarim.

---

## 3. Canli soru bankasi -- 5.796 soru

### 3.1 Butunluk: KUSURSUZ

Sifir yetim kayit. Olculen alt sorgular:

```
content'te var bank'ta yok           : 0
bank'ta var content'te yok           : 0
bank'ta var metadata'da yok          : 0
bank'ta var statistics'te yok        : 0
primary_topic_id topic_hierarchy'de yok : 0
primary_topic_id NULL                : 0
soru_hash tekrari                    : 0
```

Dort tablo (bank/content/metadata/statistics) 1:1 FK ile bagli ve hicbiri
kirik degil. Bu kismi ovmek gerek -- sema disiplini saglam.

### 3.2 Icerik kalitesi

| Olcut | Deger | Yorum |
|---|---|---|
| Toplam | 5.796 | hepsi `is_active=true`, `review_status='approved'` |
| Benzersiz metin | 5.739 | **57 tekrar eden soru** |
| Aciklamasiz | 1.929 | **%33,3 -- ucte biri cozumsuz** |
| `is_ai_generated` | 5.796 satirda `false` | |
| `is_anchor` | 5.796 satirda `false` | **capa soru yok** |
| Kalite durumu | 5.796 satirda `auto_judged_high` | ortalama 85,27 |

Iki nokta:

- **Insan incelemesi yok.** 5.796 sorunun tamami `auto_judged_high` -- yani
  onay makine kararidir. `reviewed_by` alani da kullanilmamis.
- **Capa (anchor) soru yok.** IRT'de olcek sabitlemesi capa sorularla yapilir.
  Sifir capa, bolum 5'teki kalibrasyon sorununun bir parcasi.

En cok tekrar eden gercek metin 4 kez gecen bir HF (hidrojen florur) sorusu --
bu muhtemelen ayni soru govdesine bagli coklu kok, gercek kopya degil; ama
57 tekrarin tamami tek tek dogrulanmadi (kapsam disi).

### 3.3 Dogru cevap dagilimi -- dengesiz

```
C 1.393 (%24,0)   E 1.205 (%20,8)   D 1.188 (%20,5)
B 1.102 (%19,0)   A   908 (%15,7)
```

Beklenen tekduze dagilim %20. A secenegi %15,7, C %24,0. OSYM sinavlarinda
cevap anahtari kabaca dengelidir; bu sapma soru toplama surecinin bir
yanliligini gosteriyor. Ogrenci acisindan somut etki: "emin degilsen C isaretle"
stratejisi bu bankada gercekten calisir -- yani banka olcmesi gerekeni olcmuyor.

**Aksam olcumu (madde 12, PR #236).** Sapma sinava tasiniyor mu? TYT
blueprint'i mevcut havuzdan 3.000 kez rastgele cekildi
(`backend/_ci_art/anahtar_mc.py`): en baskin sikkin payi p50 %25,2, p90
%28,0, p99 %32,7; denemelerin %54'unde bir sik %25'i, %3,4'unde %30'u
asiyor. Kaynaga gore egiklik ayni degil: 345 2025 TYT `C` 90 / `B` 34,
Aktif Ogrenme "0'dan Baslayanlara" `A` 52 / diger siklar 113-121.

**OCR anahtar hatasi hipotezi ("C cok cunku anahtar yanlis okundu")
DUSTU.** Supheli iki kesitten 20 soru elle cozuldu: Aktif Ogrenme
`D` anahtarli 10/10, 345 2025 TYT `C` anahtarli 10/10 dogru. 0/20 hata --
hata orani %14 ve ustu olsaydi 0/20 gorme olasiligi %5'in altinda. Egiklik
kaynagin kendi anahtar dagilimi; veri duzeltmesi yapilmadi.

Care secim aninda: sik SIRASI degistirilmez (bicim/gorsel sabit), sinav
olusturulurken sinav boyu her sik icin tavan `ceil(n * 0,25)`; asan sikkin
sorulari ayni dersin havuzundan takas edilir, aday yoksa tavan gevser (soru
sayisi ve ders kotasi hic degismez). Ayni 3.000 cekimle: p99 %25,2, >%30
sifir, ortalama 1,1 takas/deneme. `core/cevap_anahtari_dengesi.py` +
`osym_exam_engine._anahtar_dengele`; 20 sorunun altinda devreye girmez.

Yan bulgu: 1.140 aktif sorunun aciklamasi "Dogru cevap: X (Guven: %..,
Kaynak: ...)" kalibinda (TURKCE 641, KIMYA 269, MATEMATIK 84, TARIH 54,
GEOMETRI 47, SOSYAL 28, COGRAFYA 17); 467'si kaynak olarak `bayes_*`
cozucu oylamasini gosteriyor ve bunlarin 267'si `bayes_1ofN` -- yani
anahtar, N cozucuden yalnizca BIRININ orijinal anahtarla uyusmasina
dayaniyor. Insan anahtari degil, zayif kanit. Bu kesit icin ayri dogruluk
orneklemesi yapilmadi; icerik karari (madde 10 ile birlikte).

### 3.4 Ders kapsami -- URUNUN ASIL DARBOGAZI

```
KIMYA 3.531 | TURKCE 919 | MATEMATIK 900 | TARIH 291
COGRAFYA 123 | SOSYAL 32
FIZIK 0 | BIYOLOJI 0 | GEOMETRI 0 | EDEBIYAT 0
FELSEFE 0 | DIN 0 | INGILIZCE 0
```

TYT 5.430 / AYT 366.

Bir TYT denemesi 120 soru ister: Turkce 40, Matematik 40 (Geometri dahil ~14),
Fen 20 (Fizik 7 + Kimya 7 + Biyoloji 6), Sosyal 20. Fizik, Biyoloji ve Geometri
sifir oldugu icin **sadik bir TYT denemesi uretilemez.** Bu, bolum 2'de gosterildigi
gibi yedekten de cozulemez.

---

## 4. Mufredat agaci -- 69 konu, yapisal olarak bozuk

`topic_hierarchy` toplam 69 satir. Seviye dagilimi:

```
level 1 : 21 konu (21'i parent_id NULL -- dogru)
level 2 : 46 konu (5'i parent_id NULL -- YANLIS)
level 3 :  1 konu (parent_id NULL -- YANLIS)
level 4 :  1 konu (parent_id NULL -- YANLIS)
```

### 4.1 Agac yetimi: 14 konu, 3.266 soru

**Duzeltme (ayni gun, onarim sirasinda).** Bu bolumu once "7 konu" diye
yazdim. Eksik olcumdu: yalnizca `level > 1` olanlara bakmisim. Dogru olcut
"`subject_area` DOLU ama `parent_id` NULL" -- yani bir derse ait oldugunu
soyleyip hicbir derse bagli olmayan her konu. Gercek sayi **14**:

```
KIM.DEN     Kimyasal Denge                level 2   soru 1262
KIM.ASI     Asitler ve Bazlar             level 2   soru  478
KIM.ORG     Organik Kimya                 level 2   soru  366
TYT-KIM-02  Periyodik                     level 2   soru  350
TYT-KIM-04  Reaksiyonlar                  level 4   soru  282
TYT-KIM-01  Atom Yapisi                   level 1   soru  277
TYT-KIM-03  Kim Baglar                    level 3   soru  104
TYT-KIM-09  Cozeltiler ve Karisimlar      level 1   soru   50
KIM.TER     Termokimya                    level 2   soru   37
TYT-KIM-11  Cevre Kimyasi                 level 1   soru   37
TYT-KIM-10  Maddenin Halleri ve Gazlar    level 1   soru   17
SOC02       Turk Tarihi Temel             level 1   soru    2
SOC03       Dunya Cografyasina Giris      level 1   soru    2
TYT-KIM-12  Mol ve Kimyasal Hesaplamalar  level 1   soru    2
```

Toplam **3.266 / 5.796 soru (%56)** agac disinda asili.

### 4.1.1 Bu bir arayuz kusuru, veri hijyeni degil

`services/question_bank_service.py:226-231` "kok konu"yu `parent_id IS NULL`
diye tanimliyor:

```python
query = select(TopicHierarchy).where(TopicHierarchy.is_active.is_(True))
if parent_id:  query = query.where(TopicHierarchy.parent_id == parent_id)
else:          query = query.where(TopicHierarchy.parent_id.is_(None))
```

Olculdu -- `get_topic_hierarchy(parent_id=None)` **28 kayit** donuyordu:
13 gercek ders + 14 konu + 1 test artigi. Ogrenci ana konu listesinde
"Kimyasal Denge"yi "Matematik"in yaninda bir DERS olarak goruyordu.

Ve alt konu sayilari:

```
MAT 20    KIM 0   <- en cok icerige sahip ders (3.531 soru)
TUR  7    SOS 0
TAR  7    FIZ 0
COG  7    BIO 0
```

Kimya'ya tiklayan ogrenci **bos liste** goruyordu.

**Durum: DUZELTILDI** -- `alembic/versions/0005_mufredat_agaci_onarim.py`.
Onarimdan sonra: kok liste 28 -> 13, KIM alt konu 0 -> 12, SOS 0 -> 2,
agac disi soru 3.266 -> 0. Bekci: `tests/db/test_mufredat_agaci_saglik.py`.

### 4.1.2 Ikinci olcum hatasi: "14" da yereldi

Yukaridaki 14 sayisi **yerel veritabaninin** sayisidir. Migration'i once o
14 kodu tek tek sayarak yazdim; CI'da yeni bekci kirmizi verdi ve orada
listede olmayan kayitlar oldugunu gosterdi:

```
MVP.MAT.GOLDEN  "MVP Matematik (Golden seed)"   12 soru   <- yetim
TEST.BATCH1B    "Test Konu Batch1B"                       <- ikinci fixture
```

Ders: bir migration "olculdugu ortami onarmak" icin degil, invaryanti HER
ortamda saglamak icindir. Liste tabanli yaklasim tanimi geregi eksik.
Migration kural tabanli hale getirildi:

- yetim baglama: `subject_area IS NOT NULL AND parent_id IS NULL` olan her
  satir, `subject_area -> kok` eslemesine gore baglanir; eslesme yoksa
  satira dokunulmaz.
- test artigi: `code LIKE 'TEST.%' OR name_tr ILIKE 'Test Konu%'` -- bu
  desen bekcideki desenle birebir ayni tutuldu.

Bu hatayi bulan sey, kendi yazdigim bekciydi. Bekci olmasaydi migration
"yesil" gorunup CI ortamini yarim onarmis olacakti.

Not: `parent_id` isaret ettigi halde hedefi bulunmayan kirik referans YOK, ve
cocuk-ebeveyn seviye tutarsizligi da YOK. Sorun sadece "parent hic atanmamis".

`TYT-KIM-03` level 3, `TYT-KIM-04` level 4 -- ust seviyeleri olmadan. Bu
degerler bir agactan degil, muhtemelen elle atanmis.

### 4.2 Ayni isimde birden fazla konu

```
"Paragraf"     3 kayit : PAR, TYT-TR-03, TUR.PAR
"Dil Bilgisi"  2 kayit : TYT-TR-02, TUR.DIL
"Geometri"     2 kayit : GEO (kok), MAT.GEO (Matematik altinda)
```

Iki ayri taksonomi ic ice gecmis: bir tarafta `MAT.*` / `TUR.*` kodlu duzenli
agac, diger tarafta `TYT-XXX-NN` kodlu duz liste. Sonuc: "Paragraf" sorulari
uc ayri konuya dagilmis (TYT-TR-03'te 134, TUR.PAR'da 7, PAR'da 0).

### 4.3 Test artigi uretimde

```
TEST.BATCH2A  "Test Konu Batch2A"  level 1  subject_area NULL
```

Bir test fixture'i uretim mufredat agacinda duruyor -- ve kok konu listesinde
ogrenciye gorunuyor.

**Durum: DUZELTILDI** (0005) -- `is_active = false`. Silinmedi: kalici silme
veri silme islemidir, ayri onay ister. `is_active` uc uretim servisinde
zaten suzuldugu icin pasife almak listeden cikarmaya yetiyor.

### 4.4 `total_questions` sayaci tamamen yanlis

57 konuda denormalize sayac gercek sayimla uyusmuyor. Ornekler:

```
KIM.DEN  sayac 0   gercek 1.262
TUR      sayac 0   gercek   643
KIM.ASI  sayac 0   gercek   478
MAT.TRV  sayac 129 gercek     0   <- ters yonde yanlis
```

Yani sayac hic guncellenmemis (56 konu) ya da bayat kalmis (`MAT.TRV`).
Bu alani okuyan her ekran yanlis sayi gosterir.

**Durum: DUZELTILDI** (0005) -- sayac gercek sayimla dolduruldu ve
`tests/db/test_mufredat_agaci_saglik.py::test_total_questions_sayaci_gercekle_uyusur`
sapmayi bundan sonra CI'da yakaliyor.

### 4.5 Bos konular

13 konuda sifir soru var. Icinde: `BIO`, `EDB`, `GEO`, `MAT` (kok),
`MAT.TRG`, `MAT.TRV`, `MAT.INT`, `MAT.LMT`, `MAT.LOG`, `MAT.DIZ`.
Yani Matematik'in AYT tarafi (turev, integral, limit, logaritma, trigonometri,
diziler) tamamen bos.

---

## 5. IRT -- parametreler sinirlar icinde, ama veriden gelmiyor

### 5.1 Iyi haber: sinir ihlali sifir

```
irt_difficulty     [-4, 4]     disinda: 0    NULL: 0
irt_discrimination [0.2, 4]    disinda: 0    NULL: 0
irt_guessing       [0, 0.35]   disinda: 0    NULL: 0
```

Degismezler tutuyor. Kod tarafindaki dogrulama calisiyor.

### 5.2 Kotu haber: kalibrasyon yok

```
is_calibrated = false : 5.776
is_calibrated = true  :    20
irt_calibrated = true :     0
irt_n_responses > 0   :     0   <- TUM satirlarda sifir
irt_a / irt_b / irt_c dolu : yalnizca 82 satir
```

`irt_n_responses` her satirda 0. IRT kalibrasyonu tanimi geregi ogrenci
yanitlarindan yapilir. Sifir yanitla kalibrasyon olamaz. Dolayisiyla
`irt_difficulty` sutunundaki 3.658 farkli deger **olculmus zorluk degil**;
bir yerden uretilmis (heuristik/LLM tahmini) sayilardir.

Dagilim: min -1,050 / ort 0,132 / maks 0,887. Gercek bir YKS soru havuzunda
b parametresi kabaca [-3, +3] araligina yayilir. Buradaki ~2 birimlik dar
band da uretilmis olduklarini destekliyor.

Somut sonuc: **adaptif soru secimi (CAT) su an gercek bir yetenek olcumu
yapmiyor.** Sistem calisir, sayi uretir, ama sayinin psikometrik gecerliligi
yok. Bunu urun iddiasi olarak kullanmak "iddia > olcum" olur.

**Aksam (madde 11, PR #235).** `is_calibrated=true` olan 20 satirin hepsinde
`calibration_sample_size=0`, `irt_n_responses=0`, `irt_calibrated=false`,
`times_asked<=1`: yanlis pozitif. Kaynak, bayragi yanit orneklemi OLMADAN
true yapan iki uyuyan yol: `core/irt_daemon.py::_update_questions_db`
(daemon baslatilmasi `core/application.py:181`de yorum satirinda) ve
`services/irt_analysis_service.py::calibrate_soru_difficulty` (uretimde
cagiran yok). `irt_method='bootstrap_difficulty_prior'` 5.796 satirin
hepsinde oldugu icin hangisinin yazdigi ayirt edilemiyor. Yapilan: 0008
migration bayraklari gunluk tablosuyla (`is_calibrated_sifirlama_gunlugu`)
geri alinabilir sekilde sifirlar (yerel gidis-donus 20 -> 0 -> 20 -> 0);
iki uyuyan yoldan bayrak yazimi kaldirildi;
`question_bank_service.calibrate_question_irt` artik `sample_size < 1`
kabul etmiyor. Iki bekci: gercek PG'de `is_calibrated => orneklem > 0`;
AST ile uretim kodunda `is_calibrated=True` yalnizca o tek fonksiyonda.
Capa seti (madde 11'in asil sorusu) hala bos: 510 yanit, en cok sorulan
soru 10 kez -- capa secmek icin once yanit gerekir.

### 5.3 Kullanim istatistigi

```
times_asked > 0 olan soru : 348
hic sorulmamis            : 5.448
toplam sorulma            : 510
```

5.796 sorunun 5.448'i hic bir ogrenciye gosterilmemis. 53 kullanici,
628 `student_answers` satiri -- veri gelistirme/test verisi seviyesinde.

### 5.4 Semantik arama olu

```
pgvector uzantisi : vector 0.8.2 (kurulu)
kolon             : question_statistics.embedding vector(1536)
dolu satir        : 0
bos satir         : 5.796
```

Altyapi tam, veri sifir. Embedding'e dayanan her ozellik (benzer soru
onerisi, semantik arama, kopya tespiti) su an calismiyor.

### 5.5 FSRS: aralikli tekrar ARALIKLAMIYOR

Bu bulgu ilk raporda yoktu -- cozum turunda `fsrs_cards` tablosunu
inceleyince cikti. 107 satir:

```
stability=2.3 ve difficulty=5.0 olan satir : 106
scheduled_days = 0 olan satir              : 106
state = 'review' olan satir                : 107
reps araligi                               : 1 .. 40
farkli stability degeri                    : 2
```

`reps=40` olan bir kart hala `stability=2.3` ve `scheduled_days=0`. FSRS'te
imkansiz: 40 basarili tekrardan sonra aralik aylara cikmali.

**Ogrenci acisindan:** konuyu ilk seferde bilen ile 40 kez tekrar eden ayni
karti ayni siklikta goruyor.

Uc kok neden olculdu:

1. **Sessiz bozuk mod.** `services/fsrs_v6_service.py`'nin "fsrs paketi yok"
   dali tam bu imzayi uretiyor: aralik tablosu (`days`) hesaplanip
   KULLANILMADAN atiliyor, `due_date` her cagrida bugune sabitleniyor,
   `stability`/`difficulty` girdiden degismeden geri donuyor. Uyari yalnizca
   import aninda bir kez veriliyordu -- 106 bozuk satir hicbir calisma-zamani
   sinyali uretmeden yazildi. (`requirements.txt:106` paketi zaten
   `fsrs==6.3.1` olarak pinliyor; kok neden ileriye donuk kapali, dalin
   kendisi degildi.)
2. **`reps` sozlesme ihlali.** `card.step` kart Review durumuna gecince
   `None` olur ve bu deger dogrudan `"reps"` diye donuyordu. Geri besleyen
   cagirici ucuncu tekrarda `TypeError: '<' not supported between instances
   of 'int' and 'NoneType'` aliyor (dogrudan calistirilarak uretildi).
   Mevcut uretim cagiricilari degeri geri beslemedigi icin canli cokme
   degil -- tesadufi bir `or` korumasina bagli.
3. **`scheduled_days` / `elapsed_days` hic yazilmiyordu.**
   `services/bkt_service.py` FSRS blogu sekiz alan yaziyor, bu ikisine
   dokunmuyordu.

**Durum: DUZELTILDI** -- PR #221. Bekci:
`tests/fast/test_fsrs_bozuk_mod.py` (11 test; mutasyon kontrolu: eski kodda
11/11 dusuyor).

**Not -- test mi kod mu yanlis:** `tests/property/test_fsrs_properties.py`
icindeki `TestHardGradeBehavior` master'da kirmizi. 4.000 rastgele ornekte
olctum: HARD notu stability'i **hic kucultmuyor** (0 vaka) ve **hic GOOD'u
asmiyor** (0 vaka). Kod FSRS semantigine uygun -- basarili hatirlama
stability'i dusurmez. Testin varsayimi yanlis: `turkish_params[1] = 0.7186`
kodda YENI kart icin mutlak baslangic stability'si, carpan degil (dortlu
`[0.4072, 0.7186, 2.4063, 5.8145]` FSRS'in kanonik w0-w3 agirliklari).
Ayri PR olacak.

---

## 6. Sema butunlugu ve indeksler

```
NOT NULL kisiti : 1.748
FOREIGN KEY     :   352
PRIMARY KEY     :   245  (255 tablodan -- 10 tablo PK'siz)
UNIQUE          :    55
CHECK           :    37
```

**PK'siz 10 tablo:** 9 yedek tablo + `temp_import`. Uretim tablolarinin
tamaminda PK var -- bu iyi.

**Indekssiz FK kolonu: 112.** Bu kolonlar uzerinden yapilan JOIN ve
`ON DELETE CASCADE` silmeleri tam tablo taramasi yapar. Su an tablolar bos
oldugu icin agri hissedilmiyor; olceklendiginde hissedilir. Ornekler:
`room_chat_messages.room_id`, `session_participants.session_id`,
`teacher_reviews.teacher_id`, `question_bank.created_by`.

**Hic kullanilmamis indeks (idx_scan = 0): en buyuk 25'i olculdu.** Basta
`exam_questions_pkey` (568 kB) ve `idx_qb_primary_topic` (336 kB). Bu, indeks
gereksiz demek degil -- veritabanina henuz gercek trafik gelmedigi anlamina
geliyor. Karar icin uretim trafigi gerekir.

---

## 7. Sema-kod uyumu -- EN KRITIK BULGU

2.713 Python dosyasi tarandi, `__tablename__` bildirimleri DB ile karsilastirildi.

```
ORM'de tanimli tablo : 268
DB'de tablo          : 255
Kodda var, DB'de yok :  29
DB'de var, ORM'de yok:  16
```

### 7.1 `billing_subscriptions` -- canli 500

```
Tablo DB'de           : YOK
Sorgulayan kod        : backend/api/billing_api.py:62 (SELECT), :118 (INSERT)
Router kayitli mi     : EVET -- routers/loader.py:33
                        "api.billing_api": ("security", "api.billing_api")
```

`GET /api/v1/billing/me` cagrildiginda `UndefinedTableError` -> 500.
Bu bir tahmin degil: tablo yok, sorgu raw SQL, router yukleniyor.

### 7.2 Bu sinifi yakalayan test KOSUYOR ve SU AN KIRMIZI

**Duzeltme.** Bu bolumu once "test hic kosmuyor" diye yazdim. Yanlisti. CI
beni duzeltti: PR #218'in Backend Tests kosumunda (job 102289449141) test
gercekten kosuyor ve dusuyor:

```
FAILED tests/e2e/test_db_schema_parity.py::test_critical_tables_exist
  AssertionError: su tablolar DB'de YOK ama canli kod onlari sorguluyor
```

Yani bagimsiz olarak buldugum bulgu, CI tarafindan da dogrulanmis durumda.
Neden bugune kadar gorunmedi: Backend Tests bu kampanyanin basinda 1.866
testte oluyordu; testin kendisine hic sira gelmiyordu. Zincir onarildiktan
sonra 14.776 test kosuyor ve bu kirmizi ortaya cikti.

Kosmayan yer golden-flows.yml. Asagidaki tespit orada gecerli.

`backend/tests/e2e/test_db_schema_parity.py` tam olarak bu hata sinifi icin
yazilmis. Kendi docstring'i durumu 27 Temmuz 2026'da soyle olcmus: son 72
saatte `billing_subscriptions` 17 kez `UndefinedTableError` firlatti.

Testin `CRITICAL_TABLES` listesindeki 6 tablonun bugunku durumu:

```
billing_subscriptions       *** YOK ***
student_question_flags      VAR
teacher_classroom_students  VAR
teacher_exam_configs        VAR
teacher_assignments         VAR
teacher_contents            VAR
```

Bes tablo geri gelmis, `billing_subscriptions` gelmemis.

Ve test kapiya girmiyor: `.github/workflows/golden-flows.yml:278`

```
pytest tests/e2e/test_golden_flows.py -m golden_flow -v --tb=short
```

Secim DOSYA kapsamli. `test_db_schema_parity.py` bu secime dahil degil --
testin kendi docstring'i de bunu not etmis. Golden Flows kapisi bu sinifi
gormuyor; ic sinyal Backend Tests'ten geliyor.

### 7.3 Kok neden: aktif migration zinciri 4 dosya

```
backend/alembic/versions/
  0001_baseline_squash.py
  0002_is_active_server_default.py
  0003_restore_user_item_fsrs.py
  f1954b057565_add_performance_indexes.py     <- DB'nin alembic_version'i
```

`billing_subscriptions`'i yaratan migration'larin TAMAMI `versions_archive/`
altinda, yani aktif zincirin disinda:

```
versions_archive/20260423_billing_subscriptions_mvp.py   (tabloyu yaratan)
versions_archive/20260727_restore_dropped_tables.py      (geri getiren)
versions_archive/c555a10f4b93_sync_db_changes.py         (145 DROP TABLE)
versions_archive/add_kvkk_tables.py                      (KVKK tablolari)
```

`0001_baseline_squash.py` bu tablolari icermiyor. Sonuc: **temiz bir kurulumda
`alembic upgrade head` calistirildiginda `billing_subscriptions`,
`kvkk_data_processing_logs`, `kvkk_data_subject_requests`, `kvkk_data_breaches`
ve `video_cache` tablolari hic olusturulmaz.** Baseline squash, o anki DB
durumunu dondurdugu icin eksikleri de birlikte dondurmus.

### 7.4 Diger eksik tablolar

```
kvkk_data_processing_logs   YOK   core/kvkk_compliance.py
kvkk_data_subject_requests  YOK   core/kvkk_compliance.py:1010
kvkk_data_breaches          YOK   core/kvkk_compliance.py
kvkk_consents               VAR
video_cache                 YOK   repositories/video_cache_repository.py
```

**DUZELTME (ayni gun, cozum turunda).** Bu bolumu once "KVKK tablolarinin
uclu eksigi teknik sorunun otesinde bir uyum sorunu" diye yazdim ve bolum
8'de "add_kvkk_tables.py'yi aktif zincire tasi" diye is yazdim. **Ikisi de
yanlisti.** Olctum:

```
core/kvkk_compliance.py:276   Base = declarative_base()      <- KENDI ozel Base'i
models/kvkk_models.py:22      from .base import Base         <- uygulamanin Base'i
```

Iki ayri sinif ayni tabloyu iddia ediyor:

| | `core/kvkk_compliance.py` | `models/kvkk_models.py` |
|---|---|---|
| `KVKKConsent.__tablename__` | `kvkk_consents` | `kvkk_consents` |
| `id` | `Column(Integer)` | `Mapped[str]`, uuid7 |
| `user_id` | `Column(Integer)` | `Mapped[str]` |
| `organization_id` | yok | var |
| Base | kendi `declarative_base()` | uygulamanin Base'i |

Canli `kvkk_consents` tablosu: `id` VARCHAR, `user_id` VARCHAR,
`organization_id` VAR, `purpose`/`status` native ENUM. Yani **DB
`models/kvkk_models.py` ile uyusuyor**, `core/kvkk_compliance.py` ile
uyusmuyor.

Uc sonuc:

1. `core/kvkk_compliance.py` kendi ozel `declarative_base()`ini kullandigi
   icin alembic'in `target_metadata`'sinda **hic gorunmuyor**. Tablolarinin
   olusmamasinin sebebi bu -- bir kayip degil, hic kayitli olmamis olmalari.
2. Uretimde bu modulden **yalnizca `is_minor` fonksiyonu** import ediliyor
   (`application/commands/auth.py:15`). ORM siniflari uretim yolunda
   kullanilmiyor -- yani canli bir 500 YOK.
3. Eksik uc tabloyu `add_kvkk_tables.py`'den yaratmak **zarar verirdi**:
   uuid7 tabanli bir sistemde Integer anahtarli golge sema olustururdu.

Dogru is, tablo yaratmak degil `core/kvkk_compliance.py`'nin bayat ORM
katmanini emekliye ayirmak (ya da kanonik olani secmek). Bu bir tasarim
karari; asagida "senin kararin" bolumune tasindi.

`video_cache_repository.py` uretimde hicbir yerden import edilmiyor (0 sonuc,
testler haric) -- bu gercekten olu kod.

Kalan 24 "kodda var DB'de yok" kaydi `models_unified.py` ve
`database/models_backup.py` icindeki Turkce isimli eski modeller
(`kullanicilar`, `sorular`, `ogrenme_profilleri`...). Bunlar terk edilmis
model dosyalari; `models_unified` yalnizca `setup_database.py` ve
`core/database_query_optimizer.py` tarafindan, `models_backup` yalnizca
`database/repositories.py` tarafindan import ediliyor.

### 7.5 DB'de var, ORM'de yok (16)

9'u yedek tablo, ayrica `alembic_version`, `schema_migrations`, `temp_import`
(altyapi), ve `daily_plans`, `learning_progress_daily`, `user_item_fsrs`,
`yks_exam_goals`. Son dorde ORM tarafindan `__tablename__` ile erisilmiyor --
raw SQL ile mi kullaniliyorlar yoksa olu mu, ayri olcum gerektirir.

---

### 7.6 Backend Tests'in su anki kirmizi kumesi (baglamsal)

Bu denetimin dogrulanmasi sirasinda olculdu (PR #218, job 102289449141;
kapsama gecti: "Required test coverage of 41% reached. Total coverage:
43.08%"). Yedi dusen test, hicbiri #218'in konusu degil -- master'dan miras:

```
test_db_schema_parity.py::test_critical_tables_exist       <- bu raporun 7.1'i
test_fsrs_properties.py::TestHardGradeBehavior             <- FSRS HARD kusuru
test_fsrs_card_persistence.py                              DB stability 1.0 != 2.3065
test_semantic_search.py::TestSearchHealth                  'healthy' != 'unhealthy'  <- bu raporun 5.4'u
test_es_index_schema_split.py                              httpx.ConnectError (ES yok)
test_smoke_database.py::test_postgresql_for_kiro2          sqlite dusmus
test_coverage_final_50.py                                  AttributeError (morfoloji profili)
```

Yedi kirmizinin ucu bu denetimin bagimsiz olarak buldugu bulgularla ayni
seyi soyluyor. CI artik dogru sinyal veriyor.

**Gun sonu (9 Eyl 2026, 6 PR sonra):** listedeki 7'den 4'u kapandi
(parity 7.1 -> #220; FSRS HARD ve property -> #221/#223;
`test_fsrs_card_persistence` -> #229, asagida). Kalan 4 sabit altyapi
kirmizisi: ES yok (`ConnectError`), sqlite smoke, morfoloji `AttributeError`,
semantic health -- hicbiri bu denetimin PR'larinin konusu degil, hepsi ayri
is. `test_fsrs_card_persistence`'in "CI-only" kirmiziligi icin onceki
hipotez (`_global_process_pool`) YANLISTI: olcum (job 102477252081) dusen
satirin tohum kart degil sifirdan yaratilmis kart oldugunu gosterdi; kok
neden uc unit test dosyasinin ayni kullanici/konu satirini paylasip xdist
altinda birbirinin ortasinda silmesi (madde 17).

### 7.7 `osym_inspired_generator.py` -- bolunmus tablodan onceki ham SQL (canli 500)

Golden Flows secimi genisletilince (#224) bulundu; 7.1 ile ayni sinif
("kod eski semayi varsayiyor"), farkli yuzey. `services/osym_inspired_generator.py`
bes ham asyncpg sorgusunda `question_bank`'tan S210 split'iyle
`question_content`/`question_metadata`'ya tasinan kolonlari okuyordu
(`question_text`, `subject_area`, `exam_type`, `osym_format_compliant`,
`correct_answer`, `osym_year`). CI postgres log'u:
`column "question_text" does not exist`. `/api/v1/osym-inspired/{examples,
style-guide,statistics}` uclerinin ucu de 500'du.

Neden hicbir bekci gormedi: `scan_split_accesses.py` ORM attribute
erisimini sayar, `audit_dual_table_trap.py` eski `questions` modeli
import'unu arar -- ham SQL string'i ikisinin de gorus alani disinda.

Duzeltme PR #226: bes sorgu JOIN'li yeniden yazildi; iki bekci
(AST tabanli DB'siz + gercek Postgres'e karsi) mutasyonla civili
(eski kod 6/7 FAILED, yeni 7/7). Genel bir "ham SQL bolunmus kolon"
tarayicisi hala yok -- diger servislerde ayni tuzak olabilir; ayri is
(madde 15).

---

## 8. Yapilacaklar

Onem x maliyet sirasina gore. "Ben" = bu oturumda yapacagim; "sen" = senin
karar/onay vermen gereken.

### Simdi (ben)

1. **`billing_subscriptions` migration'i** -- YAPILDI, PR #220.
   `versions/0004_billing_subscriptions.py`, tanim
   `20260423_billing_subscriptions_mvp.py`'den birebir, `IF NOT EXISTS`
   korumali. Gidis-donus dogrulandi, parite testi yesile dondu.
2. **Golden Flows kapisini genislet** -- YAPILDI, PR #224. Patlama yaricapi
   olculdu: dar secim 186, genis 202 (fark 16 test / 7 dosya). Genis secim
   iki seyi hemen buldu: (a) `DATABASE_URL_SYNC` verilmeyince bes gercek-DB
   bekcisi CI'da sessizce skip oluyordu (duzeltildi); (b) ilk genis kosum
   `hata=1 atlanan=7` -> kapi kirmizi. `hata=1`: `/osym-inspired/examples`
   500 (bolum 7.7, PR #226). Atlananlarin 3'u `test_es_answer_leak.py`
   (CI'da Elasticsearch servisi yok) -> `needs_elasticsearch` marker'i ile
   secim disi, ES gelince tek satirla geri gelir. Kapi kurali
   (`toplam >= 170 / hata == 0 / atlanan <= 5`) gevsetilmedi.
3. **`osym_exam_engine.py:187` bayat yorumu** -- YAPILDI. "~44.000 soru"
   yaziyordu, gercek 5.796 (sekiz kat sapma). Yorum olculmus dagilimla
   degistirildi ve "GEOMETRI 14 / FIZIK 7 / BIYOLOJI 6 isteniyor ama havuzda
   sifir" sonucu ayrica not dusuldu.
4. **`TEST.BATCH2A` konusunu uretim agacindan cikar** -- YAPILDI (0005,
   PR #222). `is_active = false`; silinmedi.

### Sonraki (ben, ayri PR)

5. **Agac yetimlerine `parent_id` ata** -- YAPILDI (0005, PR #222).
   14 konu (7 degil, bkz. bolum 4.1 duzeltmesi), 3.266 soru.
6. **`total_questions` sayaci** -- YAPILDI (0005, PR #222). Gercek sayimla
   dolduruldu; sapmayi bundan sonra CI bekcisi yakaliyor.
6b. **FSRS bozuk mod** -- YAPILDI (PR #221, bkz. bolum 5.5).
6c. **`TestHardGradeBehavior` testinin yanlis varsayimi** -- ayri PR
   bekliyor (bolum 5.5 sonundaki not).
7. ~~**KVKK uclu tablosu** -- `add_kvkk_tables.py`'yi aktif zincire tasi.~~
   **IPTAL -- yanlis is.** Bolum 7.4'teki duzeltmeye bakin: o tablolari
   yaratmak uuid7 sistemine Integer anahtarli golge sema eklerdi. Karar
   maddesi 13'e tasindi.
8. **Cift taksonomiyi tekillestir** -- YAPILDI (0006, PR #225; #222'ye
   bagli). Paragraf ve Dil Bilgisi: noktali kod kanonik (`name_en` dolu,
   `seed_dungeon_topics.py` bilincli kuruyor), 185 soru `TUR.PAR`/`TUR.DIL`'e
   tasindi, `TYT-TR-02/03` ve bos `PAR` koku pasife alindi (silinmedi).
   Her tasima `topic_birlestirme_gunlugu`na yazilir, downgrade birebir geri
   alir. Geometri KOPYA DEGIL: `GEO` koku GEOMETRI dersinin bos yuvasi,
   `MAT.GEO` (63 soru) matematik alt konusu; sinav motoru ikisini ayri
   anahtar bekliyor. MAT.GEO'nun GEOMETRI diye yeniden etiketlenmesi icerik
   karari -> madde 14.
8b. **Agac bekcileri CI'da neden kirmiziydi** -- migrasyon degil SIRA: CI'da
   alembic once kosuyor, `seed_mvp_data.py` sonra `MVP.MAT.GOLDEN`'i kok
   seviyesinde yaratiyor, unit test fixture'lari `TEST.BATCH*`i aktif
   birakiyor. Kaynakta duzeltildi (PR #222 ikinci commit): seed once `MAT`
   koku sonra alt konu; fixture satirlari `is_active=false` (17/17 test
   pasif satirla da gecer). Taze DB'de CI sirasi birebir olculdu: 5/5 bekci.

### Senin kararin

9. **9 yedek tabloyu DROP edeyim mi?** 34,9 MB. Veri silmiyorum.
    **Aksam karari (onaylandi):** dort `*_cop_yedek_20260820`
    (36.967 x 4, ~34,7 MB; FK 0, view 0, ORM yok, okuyan yok) arsivlenip
    dusurulecek; bes `terfi_yedek_*` + `student_answers_is_correct_yedek`
    (toplam ~760 KB, 7 Eyl terfi kosumlarinin geri alma noktalari) 7 Ekim'e
    kadar kalir; `temp_import` 8 KB, bos. Arac PR #237:
    `scripts/quality/cop_yedek_arsivle.py dump | verify | drop --onay SIL`.
    Canli kosum: dump 6,87 MB, gecici DB'ye gercek restore 4 x 36.967
    satir esit, manifest dogrulandi. **Gece: kullanici "sil" dedi, DROP
    calistirildi** (manifest kapilari gecti); DB 141 MB -> 107 MB. Geri
    yukleme yolu manifest'te.
    Migration degil arac: tablolar ORM'siz CTAS kopyalari, alembic head'in
    ortama gore farkli is yapmasi yanlis yer.
10. **Icerik stratejisi.** FIZIK/BIYOLOJI/GEOMETRI/EDEBIYAT sifir ve yedekten
    gelmiyor. Bu urunun onundeki tek gercek engel; muhendislik tarafi degil.
    **Aksam olcumu:** 5.796 sorunun tamami ticari kaynak kitaplardan
    (Apotemi, 345, Bilgi Sarmal, Aktif Ogrenme, Esen, Edebiyat Sokagi;
    `source_book` %100 dolu), `osym_year` dolu 1, `is_ai_generated` 0.
    KIMYA %61. Karar: once OSYM gecmis yil sorulari (PDF'ler senden, hukuki
    kontrol senin), sonra uretim.
    **Gece (ithal hatti, PR #244):** 2025 TYT resmi kitapcigi (43 sayfa, iki
    sutun, metin katmani var) `scripts/osym/kitapcik_cikar.py` ile okundu:
    **125/125 soru** (TUR 40 / SOS 25 / MAT 40 / FEN 20; SOS'un 21-25'i Din
    muafi icin ek Felsefe), 125/125 anahtar (son sayfadaki tablo x-konumuyla
    eslestirildi), hepsi 5 sikli. Eski deneme (17 Agu, tek akis) 73 soru / 0
    anahtar vermisti. Bayraklar: 42 gorsel (sekil/grafik), 11 sik_bos (formul
    grafik), 41 alti cizili (`$\\underline{\\text{...}}$` ile korundu; mevcut
    56 "alti cizili" sorusunda bu bilgi kayipti), 4 roma rakami etiketi
    (kelimeye baglandi), 5 alt/ust simge (8pt), 5 sutun asan soru (dikey
    birlestirilmis kirpi). 78 soru icin soru bolgesi PNG kirpildi
    (`/static/crops/OSYM_2025_TYT/`, mevcut crops sozlesmesi). Ithal
    `scripts/osym/kitapcik_ithal.py` ile **pasif** yapildi (is_active=false,
    is_public=false, review_status=pending; 125 satir, id=uuid5(soru_hash),
    idempotent). Kitapcigin telif notu: "her hakki saklidir ... yazili izin
    olmadan kullanilmasi yasaktir" -- sayfalarda da diyagonal filigran var.
    Aktiflestirme hukuki onay bekler (kullanici karari) -- **10 Eylul:
    onay geldi, aktiflestirildi (asagida, "10 Eylul sabahi").** **AYT 2025** de
    okundu (50 sayfa): **166/166 soru** (TDE-SB1 40 = Edebiyat 24 + Tarih-1
    10 + Cografya-1 6; SB2 46 = Tarih-2 11 + Cografya-2 11 + Felsefe 12 +
    Din 6 + ek Felsefe 6; MAT 40; FEN 40 = Fizik 14 + Kimya 13 + Biyoloji
    13), 166/166 anahtar, hepsi 5 sikli (bir kimya tablo sorusunda govdedeki
    "( 1H, 6C)" ilk sik sanilmisti; kural: siklar A'dan baslar). 100 PNG
    kirpi. 166 satir pasif ithal edildi. Toplam pasif OSYM: **291 soru**;
    bos derslere ilk resmi icerik: FIZIK 21, BIYOLOJI 19, EDEBIYAT 24.
    Yan etki: FIZ/BIO koklerine ilk sorular pasif olarak girdi; agac bekcisi
    `test_icerigi_olan_dersin_alt_konusu_vardir` artik yalnizca AKTIF
    sorulari sayiyor (pasif soru urunde degil).
11. **`is_anchor` capa soru seti** -- IRT'yi anlamli kilmak icin gerekli.
    **Aksam:** capa secilemez (510 yanit, en cok sorulan soru 10 kez); ama
    20 sahte `is_calibrated=true` bayragi sifirlandi ve bayrak tek kapiya
    baglandi (0008, PR #235; bolum 5.2 aksam notu). Capa seti yanit
    biriktikten sonra secilir.
12. **Cevap anahtari dengesizligi** (A %15,7 / C %24,0) -- YAPILDI, PR #236
    (bolum 3.3 aksam notu). OCR anahtar hatasi hipotezi 20/20 elle cozumle
    dustu; veri degismedi, secim aninda sinav boyu %25 tavani + ayni dersten
    takas. Uretim icin not: uretilen sorularda anahtar dagilimi uretim
    aninda dengeli tutulmali (madde 10 hattina).
13. **KVKK ORM ikizligi.** -- YAPILDI, PR #233. `core/kvkk_compliance.py`
    1.213 satirdan 36'ya: yalnizca `is_minor` + `KVKK_RESIT_YASI` kaldi
    (uretimde tek kullanim buydu); golge ORM/Base/Column silindi, iki eski
    test dosyasi ve unit dosyasindaki bes sinif kaldirildi. Bekci
    `tests/fast/test_kvkk_tek_model.py`: `kvkk_*` tablosu tam bir ORM
    modelinde ve `models/` altinda; modul yalnizca bes ad disari verir.
    Mutasyon: eski modul geri konunca 2/2 FAILED.
14. **`MAT.GEO`'nun 63 sorusu GEOMETRI dersine mi ait?** -- YAPILDI, 0007,
    PR #234. Olcum: 63'un 57'si guclu geometri terimi tasiyor, 6'si degil
    (4 geometrik dizi -> MAT.DIZ, 1 sembol tanimi -> MAT.SAY, 1 kartezyen
    carpim -> MAT.FON; sabit id ile). Kalan 57 `GEOMETRI`, konu GEO kokune
    (kod `MAT.GEO` korundu; seed/dungeon scriptleri koda bagli). Sinav
    motoru MAT dalini `code IN (MAT, GEO, ...)` VEYA `subject_area IN
    (matematik, geometri)` ile kurdugu icin MATEMATIK derlemesi kucul-MEDI,
    ustune GEOMETRI yuvasi 0 -> 57 doldu (blueprint 14 istiyor). Gidis-donus
    birebir; iki yeni agac bekcisi (konu-kok ders uyumu, GEO altinda
    GEOMETRI etiketi). Yan bulgu: 21 soru daha kokuyle uyusmuyor (SOS
    kokunde 11 TARIH + 4 COGRAFYA, FIZ kokunde 5 KIMYA, FEN'de 1 KIMYA) ve
    1.011 soru dogrudan kok konuya bagli (kok `subject_area` NULL) -- ayri
    kucuk migration, siradaki.
15. ~~Genel "ham SQL bolunmus kolon" tarayicisi yazilsin mi?~~ **OLCULDU**
    (AST, `backend/` altinda `FROM question_bank` gecen string sabitleri,
    tests/arsiv haric): 325 sabit, 137'si bolunmus kolon okuyup ilgili
    yavru tabloya JOIN etmiyor. 137'nin 132'si `scripts/` altinda (tek
    seferlik/arsiv nitelikli araclar, cogu split oncesi; kosulursa kirilir
    ama uretim yolu degil). **Uretim yolunda 2 gercek kusur daha:**
    `api/wave2b_quality_routes.py:124` (`question_text`, `subject_area`,
    `correct_answer` dogrudan `question_bank`'tan) ve
    `services/photo_ask_service.py:157` (ayni + `embedding`, o da
    `question_statistics`'te). Ikisi de 7.7 ile ayni sinif; ayri PR
    (madde 16, ben). `api/photo_ask_api.py:140` yanlis pozitif (docstring).
16. **`wave2b_quality_routes` + `photo_ask_service` dual-table duzeltmesi**
    -- YAPILDI, PR #227. Duzeltme: `photo_ask_service` 500 veriyordu;
    `wave2b_quality_routes` ise 500 DEGIL -- `except Exception` hatayi
    yutuyor, uc sessizce bos referans listesiyle calisiyordu (sessiz
    bozulma). Ikisi de b/c/m/s JOIN ile yazildi; AST bekcisi
    `tests/fast/test_ham_sql_bolunmus_kolon.py` (osym_inspired'in ozel
    bekcisi de buraya katildi, uc uretim modulu tek listede) + gercek-PG
    bekcisi; CI'da PG'ye karsi gecti.
17. **`test_fsrs_card_persistence` CI'da rastgele kirmizi** -- YAPILDI,
    PR #229 (bkz. 7.6 gun sonu notu). Uc unit test dosyasi ayni
    `REAL_USER_ID`/`TEST_TOPIC_ID`'yi paylasip fixture'da o kullanicinin
    satirlarini siliyordu; `-n auto --dist=loadscope` altinda yaris.
    Yerelde `-n 3` ile 5 kosumun 3'unde yeniden uretildi; dosyaya ozel
    kimliklerle 8/8 yesil. Ayrica `test_fsrs_card_persistence` kullanici
    satirini hic kurmuyordu (batch1b'nin alfabetik olarak once kosmasina
    gizli bagimlilik) -- kendi org/user satirini kuruyor.
    **Bu katman gerekliydi ama yetmedi** -- #229'un ilk CI kosumu ayni
    testleri yine dusurdu. Ikinci katman: dusen satirin degerleri
    (`stability 1.0 / difficulty 0.5 / state new / reps 1`) batch1b'nin
    `_FSRS_MOCK_RETURN` sozlugu birebir. `services/bkt_service.py:18`
    `ProcessPoolExecutor` modul yuklenirken kurulur; Linux'ta cocuk surecler
    ilk `submit`te **fork** ile dogar ve o an aktif `unittest.mock.patch`i
    kalici miras alir (batch1b'nin EAP yolu havuza is verir). Ayni worker'da
    sonra kosan test havuz yoluna girip cocuktan mock sonucunu alir.
    Windows'ta spawn oldugu icin yerelde hic gorunmez. Duzeltme test
    tarafinda: `tests/conftest.py` oturum boyu havuzu `None` yapar (surec ici
    yol); `tests/unit/test_bkt_havuz_zehirlenmesi.py` havuz yolunu TAZE
    havuzla olcer ve mekanizmayi fork platformunda kanitlar (CI'da 3/3
    PASSED). Uretim kodu degismedi -> madde 18.
18. **Surec havuzu `fork` ile dogsun mu?** -- YAPILDI, PR #232: ne fork ne
    spawn, havuz kaldirildi. Olcum (p50): `review_card` surec ici 1,65 ms /
    thread 1,47 / surec havuzu 2,70; `eap_theta` 3,31 / 2,69 / 3,24; surec
    havuzunda ilk cagri p95 578 ms (cocuk dogumu). Saf hesap icin surec
    havuzu kazanc degil maliyet; `asyncio.run_in_executor(None, ...)`
    (thread havuzu) ile fork/pickle/mock-miras sinifi tamamen kalkti.
    `tests/conftest.py`'deki gecici fixture kaldirildi; bekci
    `test_bkt_havuz_zehirlenmesi.py` AST ile `ProcessPoolExecutor`/
    `concurrent.futures` yoklugunu ve sonucun thread'de aynen geldigini
    olcer. CI: yalnizca miras 3 kirmizi, FSRS testleri yesil.
19. **Aksam yan bulgulari (yeni, karar/siradaki is):**
    - `source_book = "Esen Apt Ayt Fizik 2025"` etiketli 61 soru icerik
      olarak KIMYA (3 ornek elle okundu: bag entalpisi, denge sabiti,
      hibritlesme) -- `subject_area` dogru, kaynak adi yanlis; 52'si
      `exam_type=TYT` ama konular AYT. **YAPILDI (0009, PR #240):** 52 soru
      AYT'ye cevrildi (gunluklu). Kaynak adi bilinmedigi icin dokunulmadi.
    - 21 kok uyusmazligi (madde 14 yan bulgusu) **YAPILDI (0009, PR #240):**
      21'i de okundu, icerik `subject_area` ile uyusuyor, konu yanlisti;
      dersin kokune tasindi. Yeni bekci tum kokler icin
      (`test_sorunun_dersi_ile_konusunun_koku_uyusur`).
    - Cozucu-oylamali anahtarlar **OLCULDU (0009, PR #240):** kapidan gecen
      31 `bayes_*` anahtarli sorunun hepsi elle cozuldu -- 26 dogru, 5
      supheli, 3'u kesin kusurlu ve pasife alindi (cd403a4d: cozum 2 carpma
      / siklar 3..7; ef3e1c75: sayim 90, anahtar "26"; c1ab0540: OCR bozuk
      metin). Yayinevi anahtarli 20/20 (madde 4b) vs cozucu anahtarli 26/31:
      `bayes_1ofN` anahtar zayif kanit. Kalan 2 supheli (kullanici karari
      devretti, 0010 / PR #243): 1dd54e6a (Tevhid-i Tedrisat; anahtar C,
      dogru A) PASIF; dab0707f (paragrafa cumle yerlestirme; anahtar B
      savunulabilir) KALDI. Uretim hatti kurali onerisi: anahtar tek-cozucu
      uyusmasiyla yazilmasin.
    - `core/irt_daemon.py` **SILINDI (PR #241):** hic baslamiyordu, bolunmus
      semaya gore kirikti, bayragi orneklemsiz yaziyordu, cagirani yoktu;
      gercek kalibrasyon `services/irt_calibration_service.py`de. Yeniden
      yazma yok -- verisi olmayan kalibrasyona altyapi kurmak sirada degil.
    - KIM.DEN ("Kimyasal Denge") altinda 1.173 `exam_type=TYT` soru; konu
      KIMYA'nin %36'si icin cop kovasi (TYT kitaplarindan gelen sorular da
      burada). TYT sinavi KIMYA'yi bu havuzdan cekiyor. Konu atamasi ayri,
      buyuk is; dokunulmadi.
    - `tests/test_smoke_api_critical.py::test_smoke_fsrs_review_queue` tek
      basina kosunca master'da da duser (`app/services/fsrs_service.py` raw
      SQL'de `::text`, test sqlite'ta): CI'da yalnizca test sirasi sayesinde
      geciyor (#235 ilk kosumunda dustu, yeniden kosumda gecti). Miras,
      sira-bagimli test; ayri is.

---

## 9. Ozetle: veritabani ne durumda?

**Iyi olan:** referans butunlugu kusursuz (0 yetim, 0 kirik FK, 0 hash
tekrari), IRT parametreleri sinirlar icinde, PK disiplini uretim tablolarinda
tam, sema modern (pgvector, JSON, enum).

**Kirik OLAN (denetim sabahi):** `billing_subscriptions` uretimde 500
veriyordu (Backend Tests kirmizi gosteriyor, Golden Flows kapisi
gormuyordu); migration zinciri baseline squash sirasinda uc tablo grubunu
kaybetmisti; mufredat agacinin en dolu konusu agaca bagli degildi, Paragraf
ve Dil Bilgisi ikiser kez vardi; uc uretim yolu (`osym_inspired_generator`,
`photo_ask_service` 500; `wave2b_quality_routes` sessiz bos referans)
bolunmus tablodan onceki ham SQL kullaniyordu ve hicbir bekci bu sinifi
gormuyordu; FSRS bozuk modda uydurma psikometri yaziyordu; bir test dosyasi
CI'da rastgele kirmiziydi.

**Gun sonunda kapananlar (#220-#230 birlesti; #225 #228 olarak yeniden
acildi):** yukaridakiler master'da duzeltildi ve her biri
mutasyonla civili bekciyle korunuyor; Golden Flows kapisi 199 testi
gercekten kosuyor (`hata=0 atlanan=4`).

**Aksam turu (#232-#238 birlesti):** yedi karar
maddesi olculerek kapatildi -- surec havuzu kaldirildi (#232), KVKK golge
ORM emekli (#233), MAT.GEO -> GEOMETRI 57 soru (#234), 20 sahte kalibrasyon
bayragi sifirlandi ve bayrak tek kapiya baglandi (#235), cevap anahtari
%25 tavani + OCR hipotezinin 20/20 ile cokusu (#236), yedek tablolar icin
dump -> gercek restore ile dogrulanmis arsiv araci, DROP "sil" bekliyor
(#237). Her PR mutasyonla civili bekci tasiyor.

**Gece turu (#239-#241):** izomorf uretecte isim geri donusu (CI flake'i,
uretimde de kusur) duzeltildi; 0009 ile 21 soru dogru koke, 52 soru AYT,
3 kesin yanlis anahtar pasif (hepsi gunluklu); `irt_daemon` emekli.
Madde 19'daki bulgularin karari yukarida, kalan ikisi (2 supheli anahtar,
"sil") kullanicida.

**Hala kirik:** IRT kalibrasyonu ogrenci verisi olmadigi icin gercek degil
(artik en azindan "kalibre" DEMIYOR); semantik arama altyapisi bos (0
embedding); CI'da ES servisi yok; altyapi testleri (7.6 gun sonu +
`test_get_history_deep` 404 + Kanon lint) sabit kirmizi -- master'da da.

**10 Eylul sabahi (0011 + D9):** kullanici "OSYM sorularini aktiflestir"
dedi. Duz `is_active=true` yetmedi -- olcum (`backend/_ci_art/_aktif_olcum.py`)
gosterdi ki gercek servis kapisi (`v_safe_for_beta`, `core/quality_gate.py`)
uc alan daha ister: `question_bank.review_status='approved'`,
`question_statistics.quality_review_status IN ('human_verified',
'auto_judged_high')`, ve `question_metadata.pipeline_metadata` icinde bir
"coherence signal" anahtari (student_coherent/verified_provisional/
consensus_2signal_run/math_promote_run/verbal_promote_run) -- OSYM
ithalatinin hicbiri bunlara sahip degildi. Var olan bir imzayi odunc almak
yanlis provenance yazardi (OSYM icerigi blind-solve/konsensustan gecmedi,
resmi cevap anahtarindan geldi); bunun yerine yeni bir imza eklendi:
`osym_resmi_kaynak`. Ayrica FIZ/BIO/EDB kokleri SIFIR alt konuya sahipti
(agac bekcisi bu ana kadar sessizdi, cunku sayilan sorular pasifti);
aktiflestirme bu koklere 21+19+24=64 aktif soru koyacagindan bekci
firlardi.

Iki dosya birlikte calisti:
- `backend/migrations/D9_safe_for_beta_osym_resmi_kaynak.sql` (+ ROLLBACK):
  `v_safe_for_beta`'nin coherence-signal daline `osym_resmi_kaynak` eklendi.
  D6-D8 numaralari kasitli bos: gate2b/wave1 kampanyalarinda ayni isimle
  scratch dizinlerine (`scripts/quality/_gate2b/`, `_wave1/`) uygulanmis
  ama `backend/migrations/`e hic tasinmamis (canli view D5 + o dalgalarin
  toplami; `pg_get_viewdef` ile dogrulandi, D5'in kendi dosyasindan farkli).
  Elle uygulanir (bu view alembic zincirinin DISINDA, bkz
  `20260727_mv_safe_for_beta.py` docstring'i).
- `backend/alembic/versions/0011_osym_aktiflestirme.py`: 291 satirin
  `is_active`, `review_status`, `quality_review_status` alanlarini cevirdi;
  `pipeline_metadata`'ya `osym_resmi_kaynak` anahtarini ekledi; FIZ/BIO/EDB
  altina birer "GENEL" alt konu yaratip (kod: `FIZ-OSYM-GENEL` vb., sabit
  uuid5 id) o derslerin OSYM sorularini koklerden bu alt konuya tasidi (64
  soru); `total_questions` sayaclarini yeniden hesapladi;
  `refresh_safe_for_beta()`i cagirdi (fonksiyon yoksa -- taze/CI DB --
  sessizce atlar). Gunluklu (`aktiflestirme_gunlugu_0011`), geri alinabilir.

`quality_review_status='human_verified'` secildi, `auto_judged_high` degil:
canli DB'de su an hicbir satir `human_verified` degildi (hepsi
`auto_judged_high`; D4 migration'inin kendi docstring'i bunu "beklenen 0"
diye not dusmustu). OSYM icerigi bir LLM tarafindan "auto_judged" edilmedi;
resmi kaynagin kendi cevap anahtari + tam eslesen cikarici (125/125 TYT,
166/166 AYT, `tests/fast/test_osym_kitapcik.py`) + elle cozulen supheli alt
kume (0009/0010) ile kuruldu -- bu "auto_judged" degil "human_verified"
tanimina yakin.

Dogrulama (canli DB, uygulamadan once/sonra): `v_safe_for_beta` 4.959 ->
5.250 (+291, tam OSYM sayisi); 291/291 OSYM sorusu `mv_safe_for_beta`
icinde; FIZ/BIO/EDB her biri artik 1 alt konuya sahip (soru sayilari
sirasiyla 21/19/24 ile eslesiyor); `core/osym_exam_engine.py`nin gercek
sorgu deseni (is_active + safe_for_beta_gate) FIZIK icin 21 soru donuyor.
Mutasyon testi: `alembic downgrade -1` sonrasi yeni bekci
(`tests/e2e/test_osym_aktiflestirme.py`, gercek Postgres ister) 2/3 testte
FIRLADI (aktiflestirilmemis durumu yakaladi), `alembic upgrade head` ile
tekrar 3/3 yesil. `tests/e2e/test_quality_gate_leak.py` (donen sorularin
kapinin alt kumesi oldugunu dogrulayan, sayi iddia etmeyen bekci) ve
`tests/db/test_mufredat_agaci_saglik.py` etkilenmedi, hala yesil.

**10 Eylul (D10 + 0012, push-oncesi bulunan kusur):** `duzeltme/
0011-osym-aktiflestirme` dalini pushlarken `ders-zorlayici` pre-push
bekcisi (`test_icerik_gecerliligi.py::test_k2_anahtar_dolu_bir_sikka_
isaret_ediyor`) 28 satirin cevap anahtarinin GECERSIZ oldugunu buldu:
dogru sikkin metni BOS. Teshis (`backend/_ci_art/_r5_teshis.py`,
`_bayrak_analiz.py`): 28/28 satir OSYM ithalati, hepsi MATEMATIK, hepsi
`kitapcik_ithal.py`'nin ITHALAT ANINDA kendi koydugu `pipeline_metadata->
'bayraklar'` isaretinde `sik_bos` tasiyor -- birebir ortusme (havuzun geri
kalaninda, 5.250-28 satirda, SIFIR R5 hatasi var). Kok neden: bu sorularin
dogru sikki bir GORSEL/GRAFIK (metin degil) -- import script'i bunu
ithalat aninda saptayip bayrakladi ama D9 (`osym_resmi_kaynak` imzasi) 28'i
elemeden butun 291'i tek imzayla ice aldi. **Kusur gercek** (test bayat
degil): bu 28 soru mevcut metin-tabanli sunum katmaninda hicbir ogrenci
tarafindan yanitlanamaz.

Duzeltme iki dosya:
- `backend/migrations/D10_safe_for_beta_exclude_sik_bos.sql` (+ ROLLBACK):
  `v_safe_for_beta`'ya bagimsiz bir disari-atma eklendi -- `bayraklar`
  icinde `sik_bos` tasiyan hicbir satir kapidan gecemez (kaynagi ne olursa
  olsun, genel kural). `osym_resmi_kaynak` imzasina DOKUNULMADI (cevap
  HARFI hala resmi kaynaktan dogrulanmis, sorun harfin dogrulugu degil
  sikkin metninin eksikligi).
- `backend/alembic/versions/0012_osym_sikki_bos_pasif.py`: ayni 28 satirin
  `is_active`'ini FALSE'a cevirdi (kapi zaten disliyor ama is_active=true
  birakmak DB'yi dogrudan okuyan baska araclara yanlis bilgi verirdi).
  Gunluklu (`sikki_bos_gunlugu_0012`), geri alinabilir. `review_status`a
  dokunulmadi ('approved' kalir).

Dogrulama: uygulamadan once dogrulama sorgusu
(`backend/_ci_art/_d10_dogrula.py`) 5.250->5.222 (-28), OSYM 291->263
bekledi; uygulamadan sonra olcum tam eslesti. Mutasyon testi: D10 geri
alinip (`_d10_geri_al.py`) is_active=true birakildiginda AYNI 28 satir
R5'i tekrar tetikledi (ne fazla ne eksik); D10 + `alembic upgrade head`
ile tekrar 0/0. `tests/e2e/test_osym_aktiflestirme.py`'ye ters yonlu bir
bekci eklendi (`test_osym_sik_bos_sorulari_kapi_disinda`) ve mevcut iki
test sik_bos'u BILEREK haric tutacak sekilde guncellendi
(`_osym_ids_servis_edilebilir` / `_osym_ids_sik_bos`). Sonuc: 291 OSYM
sorusundan 263'u servis ediliyor, 28'i gorsel-sik destegi eklenene kadar
pasif (ileride yeniden aktif edilebilir -- bkz D10 dosyasinin ust notu).

**Cozulemeyen:** icerik. 5.796 soru, dort ders tamamen eksik, yedekteki
36.967 soru halusinasyon (simdi OSYM'nin 263 sorusuyla biraz azaldi, ama
FIZIK/BIYOLOJI/EDEBIYAT/GEOMETRI hala buyuk olcude eksik; 28 OSYM sorusu
gorsel-sik destegi bekliyor). Bu bir veritabani sorunu degil, bir icerik
sorunu.

**10 Eylul (0013 + Neofizik ithalati, 1.218 satir):** "Neofizik AYT Fizik
Soru Bankasi 2025" (336 sayfa, taranmis PDF) hibrit bir okuma hattiyla
cikarilip veri tabanina PASIF olarak alindi. Bu, D10 notunun kapanisinda
"cozulemeyen" diye isaretlenen FIZIK icerik acigina karsi atilan ilk adim.

Neden hibrit hat: PDF'in METIN KATMANI YOK -- 336 sayfada toplam 0
karakter olculdu, stok docling 10 sayfadan yalnizca 14 karakter cikardi.
Yani tek motorlu hicbir cozum (docling dahil) bu kitabi okuyamaz; okuma,
mizanpaj tespiti ve dogrulama ayri katmanlara bolundu.

Cikarim ve olcumler (`veriseti/zkitap/cikti/YONTEM.md` tam raporu tutar):
- Bolutleme, kitabin KENDI basili cevap anahtarlarina karsi dogrulandi:
  145 test blogundan 139'u birebir esti.
- 1.319 sorunun tamami IKI KEZ bagimsiz okundu; %89,3'u bayt-bayt ayni
  cikti. Bicim farklari normalize edilince gercek icerik uyusmazligi 18
  soruda (%1,36) kaldi; hepsi piksel duzeyinde kanitla karara baglandi,
  askida kalan yok.
- Cozum-dogrulama BAGIMSIZ bir kanal olarak kullanildi, cevap kaynagi
  olarak DEGIL (PhysUniBench, arXiv 2506.17667: en iyi model coklu-ortam
  fizik sorularinda %63,6'da kaliyor -- model cevabi anahtar yerine
  gecemez). Basili anahtarlarla uyum %96,0 (yuksek guvenli altkumede
  %98,1). Bu kanal 1.319 soruda tam 1 gercek yazim hatasi yakaladi
  (s297-01, alt indis 88<->86), ayrica 3 kitap dizgi hatasi ve 2 supheli
  kitap anahtari isaretlendi.
- D10'da OSYM'yi vuran `sik_bos` sorunu bu hatta ithalattan ONCE ele
  alindi: sikki gorsel olan 44 sorunun 42'sinde secenek gorselleri
  DocLayout-YOLO (arXiv 2410.12628) ile ayri varlik olarak cikarildi.

Veri tabanina yansiyan degisiklik dort dosya:
- `backend/alembic/versions/0013_neofizik_konu_agaci.py`: FIZ kokunun
  altina 6 bolum + 44 yaprak konu tanimladi (bu kosumda eklenen dugum:
  50). Gunluklu (`neofizik_konu_gunlugu_0013`), tekrar kosulabilir,
  geri alinabilir (`downgrade` yalnizca kendi ekledigi ve referanssiz
  dugumleri siler). NOT: `topic_hierarchy.code` varchar(50) -- konu
  kodlari bu sinira gore kisaltiliyor, 44 kodda carpisma yok.
- `backend/scripts/kitap/neofizik_ithal.py`: 1.218 `ONAYA_HAZIR` satiri
  yazar. Yazmadan once bir on kontrol kapisi var (5 sik + dolu anahtar +
  R5: anahtarin gosterdigi sikkin metni dolu + dolu soru metni); tek bir
  ihlalde ithalat baslamadan durur.
- `backend/scripts/kitap/neofizik_kirp.py`: gorselleri PDF'ten yeniden
  uretir. Gorseller git'e GIRMEZ (`d-dataset/` zaten .gitignore'da,
  satir 216); veri setinde her kaydin kirpim kutusu durdugu icin
  gorseller her ortamda yeniden uretilebilir -- tasinan tek sey
  koordinatlar.
- `backend/tests/e2e/test_neofizik_ithal.py`: 6 bekci.

Ithalat sozlesmesi (bilerek muhafazakar): her satir
`is_ai_generated = true` + `review_status = 'PENDING'` + `is_active =
false` ile yazildi. Bu kombinasyon `v_safe_for_beta`'nin
`(is_ai_generated = false OR review_status = 'APPROVED')` kolunu
DUSURUR, yani insan onayi gelmeden hicbir soru ogrenciye gitmez.

Dogrulama (canli dev DB, uygulamadan sonra olculdu): `question_bank`
6.087 -> 7.305 (+1.218); `v_safe_for_beta` 5.222 -> 5.222 (DEGISMEDI --
ithalatin kapiyi hic kimildatmadigi olcumle sabit); Neofizik satirlari
icin `is_active` 0, kapidan gecen 0, farkli yaprak konu 44 (yani sorular
FIZ kokune yigilmadi, gercek konulara bagli).

Gorsel referanslari: her satirin `question_content.question_image_url`
alani ve `question_metadata.pipeline_metadata->'gorsel_varliklar'`
listesi `/static/crops/NEOFIZIK_2025/...` yollarini tutar; bu montaj
`core/application.py:441`deki `CROP_IMAGE_DIR` eslemesiyle ayni. Olcum
(`backend/_ci_art/_neo_url_kontrol.py`): 1.218 soru gorseli + 1.215
varlik referansinin tamami diskte mevcut, eksik 0.

Mutasyon testi (bekcinin gercekten KAPIYI izledigini kanitlamak icin):
ilk denemede yalnizca `is_ai_generated`/`review_status` cevrildi ve
sonuc BELIRSIZ cikti -- satir hala kapinin disindaydi (kapidan gecen 0),
yani yalnizca bayrak testi kizardi, kapi bekcisi kizarmadi. Bunun uzerine
kapi yuklemi bastan olculdu (`_neo_kapi_teshis.py`) ve UC kilit birden
cevrildi: `quality_review_status = 'human_verified'`, `pipeline_metadata`
icine `student_coherent: "true"`, `is_ai_generated = false` +
`review_status = 'APPROVED'`. Sonuc: kapidan gecer mi = 1 ve
`test_neofizik_sorulari_kapidan_gecmiyor` sizan satirin id'siyle FIRLADI;
tam geri alma sonrasi 6/6 yesil. Yani bekci bayat degil.

`golden_flow` isareti BILEREK konulmadi -- ayni gerekce
`test_osym_aktiflestirme.py`de de gecerli: bu veri elle kosulan bir
ithalat script'inden gelir, CI'da hic tohumlanmaz, dolayisiyla isaretli
olsa her kosumda atlanir ve en fazla 5 atlama butcesini bosa harcardi.

Kalan is (icerik karari, kod degil): 1.319 sorunun 101'i insan incelemesi
kuyrugunda (`veriseti/zkitap/cikti/inceleme_kuyrugu.csv`); 1.218 satirin
tamami `review_status = 'PENDING'` bekliyor. Onay verilene kadar FIZIK
acigi kapanmis SAYILMAZ -- sorular DB'de duruyor ama servis edilmiyor.

Depoya NE GIRMEDI (bilerek): kitabin cikarilmis metni
(`veriseti/zkitap/cikti/neofizik_2025_sorular_v2.json`, 1.319 soru),
yontem raporu (`YONTEM.md`) ve inceleme kuyrugu, `.gitignore:380`
(`veriseti/`) tarafindan disarida tutuluyor; gorseller de `.gitignore:216`
(`d-dataset/`) ile. Gerekce iki katmanli: (1) bu depo PUBLIC ve soz konusu
kitap TICARI bir yayin -- 1.319 sorunun tam metnini herkese acik bir
depoya koymak telif acisindan yanlis olur; (2) gorseller zaten
koordinatlardan yeniden uretilebiliyor. Sonuc: bu commit ithalat
MEKANIZMASINI tasir, kitabin ICERIGINI tasimaz. Veri seti yalnizca yerel
makinede durur; baska bir ortamda ithalat kosulacaksa dosyanin oraya elle
kopyalanmasi gerekir.

**10 Eylul, ogleden sonra (0014, karar degisikligi):** Urun sahibi bireysel
insan denetimini ATLAYIP toplu denetimi beta surumune ertelemeye karar
verdi. 0013'un muhafazakar sozlesmesi (hepsi pasif, hepsi PENDING) bu
kararla degisti; 0014 onu uygular.

Kapi yuklemi tahminle degil BIRINCIL KAYNAKTAN okundu (`pg_views`,
`v_safe_for_beta` tanimi) ve her kolu ayri ayri olculdu
(`backend/_ci_art/_neo_kapi_olc.py`). Uc kol engelliyordu:
`quality_review_status` 1218/1218 'pending'; uyum sinyali 0/1218; AI/onay
kolu 0/1218. Diger kollar (demoted_at, topic_match_quality, match_tier)
zaten 1218/1218 geciyordu.

Uc alan degisti ve UCU DE GERCEGI SOYLUYOR:
- `quality_review_status` -> `'auto_judged_high'`. Dogru: hat bu sorulari
  otomatik ve yuksek guvenle yargiladi (iki bagimsiz okuma + cozum
  dogrulama). `'human_verified'` YAZILMADI -- hicbir insan bunlari tek tek
  dogrulamadi.
- `pipeline_metadata` += `consensus_2signal_run`. Dogru: iki sinyalli
  uzlasma kosumu gercekten yapildi.
- `review_status` -> `'APPROVED'`, YANINDA `onay_turu='toplu_beta_sahibi'`
  ve `bireysel_denetim_yapildi=false`. 'APPROVED' tek basina "biri bu
  soruyu inceledi" gibi okunur; iz olmadan "servis edilen kac soru hic
  bireysel denetimden gecmedi" sorusu bir daha yanitlanamazdi.

`is_ai_generated` alanina DOKUNULMADI -- true kalir. Kapiyi acmanin kolay
ama yanlis yolu bu alani false yapmakti (view'in oteki kolu); o yol DB'ye
yanlis bir kaynak beyani birakirdi. Bir bekci artik bunu koruyor.

KAPSAM -- 37 satir BILEREK disarida: D10'un genel kurali (`bayraklar`
icinde `sik_bos` tasiyan hicbir satir kapidan gecemez) BOZULMADI. 1218
Neofizik satirindan 37'si bu bayragi tasiyor: sikki metin degil gorsel
oldugu icin mevcut metin-tabanli sunum katmaninda eksik gorunurler. Toplu
onay bu satirlari kapsamadi; gorsel-sik destegi gelene kadar pasif
kalirlar. Yani 1218 degil, **1181** satir aktiflesti.

Dogrulama (canli dev DB, once/sonra):

| Olcum | Once | Sonra |
|---|---|---|
| `v_safe_for_beta` | 5.222 | **6.403** (+1.181, hedefle birebir) |
| Neofizik `is_active` | 0 | **1.181** |
| Neofizik kapidan gecen | 0 | **1.181** |
| Servis edilen FIZIK sorusu | 21 | **1.202** |

Mutasyon testi: `alembic downgrade 0013` sonrasi `v_safe_for_beta` TAM
OLARAK 5.222'ye dondu (kayma yok -- geri alinabilirligin kaniti) ve yeni
bekci `test_neofizik_temiz_sorular_kapidan_geciyor` FIRLADI; `upgrade head`
ile 6.403 ve 8/8 yesil.

Bekciler guncellendi (`tests/e2e/test_neofizik_ithal.py`, 6 -> 8 test).
`test_neofizik_sorulari_kapidan_gecmiyor` artik yanlis sozlesmeyi
savundugu icin kaldirildi, ama YERINE KOYULMADAN degil:
- `test_neofizik_temiz_sorular_kapidan_geciyor` (ters yon, ayni kapi)
- `test_neofizik_sik_bos_sorulari_kapi_disinda` (D10 hala gecerli)
- `test_neofizik_toplu_onay_izi_kayitli` (onay_turu izi kaybolamaz)
- `test_neofizik_ai_isareti_korunuyor` (is_ai_generated cevrilemez)
R5 bekcisi (`test_icerik_gecerliligi.py`) ve mevcut kapi/agac bekcileri
1.181 satir CANLIYKEN kosuldu: 34 passed, 0 failed.

**Yeni olculebilir gercek:** servis edilen 6.399 sorunun 1.181'i (%18,5)
hicbir bireysel denetimden gecmedi. Bu sayi `onay_turu='toplu_beta_sahibi'`
sorgusuyla her an olculebilir; beta toplu denetimi ilerledikce dusmeli.

**10 Eylul, DUZELTME (0013/0014 raporlarindaki iki sisik rakam):** Yukleme
sonrasi yapilan tam denetimde, bu belgenin ve PR #246/#247'nin metninde
YANLIS iki rakam bulundu. Rakamlar sikistirma oncesi bir ara ozetten
alinmis, kaynaktan yeniden olculmemisti -- yani "raporlar bayatlar,
birincil kaynagi oku" ve "olcum kapsami = iddia kapsami" kurallarinin tam
olarak yakalamak icin var oldugu hata yapildi. Commit mesajlari ve PR
govdeleri degistirilemez; dogru rakamlar burada duruyor.

| Yazilan | Olculen (canli 1181 satir) |
|---|---|
| iki bagimsiz okuma %89,3 bayt-bayt ayni | **%83,3** (984/1181) |
| cozum-dogrulama %96,0 uyum (1319 soruda) | oran dogru (**%96,0**) ama kapsam yanlis |

Kanit tabaninin GERCEK genisligi (`_ci_art/_neo_kanit_tabani.py`):

- cift okuma kosuldu: **1.164 / 1.181 (%98,6)** -- kalan 17 hakem yolundan gecti
- iki okuma birebir ayni: **984 (%83,3)**; ortalama uyum 0,9915
- bagimsiz cozum kosuldu: **374 (%31,7)**; bunlarin 359'u anahtarla uyustu (%96,0)
- **bagimsiz cozum KOSULMADI: 807 (%68,3)**

Karari degistirir mi: `auto_judged_high` etiketi hala savunulabilir --
cift okuma canli satirlarin %98,6'sinda kosuldu ve cevaplarin tamami
kitabin BASILI anahtarindan geliyor (`cevap_kaynagi=kitap_anahtari`,
1218/1218), model cikariminan degil. Ama beta toplu denetimi yapilirken
bilinmeli: sorularin ucte ikisinde anahtari dogrulayan ikinci bir bagimsiz
kanal yok. Denetime cozum kontrolu kosmamis 807 soruyla baslamak
rastgele baslamaktan olculebilir sekilde daha verimli.

**10 Eylul, YUKLEME TAM DENETIMI:** "eksiksiz ve sorunsuz yuklendi mi"
sorusu iddiayla degil, kaynak JSON ile DB'nin alan alan karsilastirilmasiyla
yanitlandi (`_ci_art/_neo_tam_denetim.py`). Karsilastirma hash uzerinden
DEGIL alanlar uzerinden yapildi -- hash zaten alanlardan turedigi icin hash
karsilastirmasi kendi kendini dogrulayan bos bir test olurdu.

| Denetim | Sonuc |
|---|---|
| JSON'da olup DB'de olmayan | 0 |
| DB'de olup JSON'da olmayan | 0 |
| cocuk tablo yetimi (content/statistics) | 0 |
| id = uuid5(soru_hash) tutarli | 1.218/1.218 |
| soru metni birebir | 1.218/1.218 |
| 5 sik birebir | 6.090/6.090 |
| cevap anahtari birebir | 1.218/1.218 |
| kaynak sayfa + kayit_id izi birebir | 1.218/1.218 |
| bozuk kodlama (mojibake) | 0 |
| FIZ-NEO-B* yapraginda | 1.218/1.218 (44 farkli konu) |
| gorsel dosyalari diskte | 1.218 soru + 1.215 varlik, eksik 0 |
| ithal edilmeyenler = inceleme kuyrugu | 101 = 101, simetrik fark 0 |
| durum tutarliligi | temiz 1.181 tam, sik_bos 37 pasif |

Bir yanlis alarm: `A` (U+00C5) tasiyan bir satir mojibake sanildi --
`neofizik2025-s318-06`, fotoelektrik sorusu, **Angstrom** simgesi yerinde
kullanilmis ve kaynak JSON ile birebir ayni. Dedektorden `A`/`A"`
cikarildi.

CEVAP DAGILIMI EGRILIGI (arastirildi, kusur DEGIL): A=%13,6 B=%16,4
C=%24,0 D=%21,8 E=%24,2; ki-kare 54,9 (df=4) -- duzgun dagilimdan anlamli
sapma. Cikarim hatasi mi kitabin kendisi mi diye ayirt edildi: cozum
dogrulamasinin UYUSTUGU altkumede A=%13,4, UYUSMADIGI altkumede A=%13,7 --
egrilik iki kumede AYNI, yani cikarim A'lari sistematik kacirmiyor. Ayrica
cevaplarin tamami kitabin basili anahtarindan geliyor. Karsilastirma
tabani: OSYM'nin 291 resmi sorusu neredeyse duzgun (ki-kare 1,4), yani
olcum yontemi kendi basina egrilik uretmiyor. Sonuc: egrilik KITABIN
basili anahtarinin ozelligi.

**10 Eylul, DUZELTMENIN DUZELTMESI (%89,3 / %83,3):** Bir onceki notta
"%89,3 yazildi, gercek %83,3" dendi. Bu eksik dogruydu. Hattin kendi
raporu (`veriseti/zkitap/cikti/YONTEM.md`) ve `uyum_olc.py` birincil
kaynaktan okununca: %89,3 rakami **normalize edilmis uyum >= 0,995**
esigiyle olculmus (noktalama, tirnak/tire cesitleri, bosluk elenerek);
%82,8 / %83,3 ise **ham >= 1,0** (bayt-bayt) esigi. Ayni JSON uzerinde
ikisi de dogru: >=1,0 -> %82,8; >=0,995 -> %89,3; >=0,95 -> %95,5.
Yanlis olan rakam degil, raporun 0,995 esigine "birebir ayni" etiketini
yapistirmasiydi. Cozum-dogrulama KAPSAMI hakkindaki duzeltme (374/1181,
%31,7) aynen gecerli -- o hata rapordan degil, PR metnini hafizadan
yazmaktan kaynaklandi.

## 10 Eylul -- Neofizik TYT Fizik Soru Bankasi ithali (0015)

Ayni yayinevinin TYT kitabi. AYT'den iki noktada ayrilir ve bu iki fark
denetimin de sekillini degistirir:

1. **Cevap kaynagi tek: kitabin basili anahtari.** Urun sahibi sorularin
   tekrar cozulerek dogrulanmasini istemedi. Bu yuzden `explanation` NULL
   birakildi; uretilmemis bir cozumun sonradan "varmis gibi" gorunmemesi
   icin bekci `explanation IS NOT NULL` sayisini sifirda tutuyor.
2. **Turetik alanlar sabit degil, hesaplaniyor.** AYT ithali
   `readability_score=50.0` ve `morphology_complexity=0.5` sabitleriyle
   yazmisti; TYT'de ikisi de repo'nun KENDI servislerinden geciyor.

### Kitaptan olculen sayilar

| Olcu | Sonuc |
|---|---|
| PDF metin katmani | **0 karakter / 256 sayfa** (tam raster) |
| icerik sayfasi | 238 |
| soru | **891** |
| test blogu | 109 |
| unite / konu | 7 / 35 |
| cikmis soru (OSYM + MSU) | 91 |

### Segmentasyon: iki bagimsiz yer gercegi

El etiketi (82 sayfa, 308 kutu) ve basili cevap anahtarlari (109 blok)
birbirinden bagimsiz. Nihai tespit **82/82 sayfa** ve **109/109 blok**
birebir. Anahtar sayimi, el etiketinin goremedigi iki hatayi yakaladi
(s215 ikon penceresi kirpigi, s243 sekil ici gurultunun baskin kumeyi
kazanmasi); ikisi de olcumle duzeltildi, tahminle degil.

Ayrica basili soru numaralarinin **891'i 891** gorsel olarak dogrulandi --
"sayfa ici okuma sirasi" artik varsayim degil olcum.

### Transkripsiyon

238 sayfa iki kez, bagimsiz okundu. Ham normalize uyum %98,0 (873/891).
Iki BICIMSEL ayrisma deseni (Unicode alt simge harfi; icerigi sekil olan
bos roma maddeleri) normalize edildikten sonra **hakem disi 870 sorunun
870'i birebir**. Kalan 21 soru hakem turunda yuksek cozunurluklu kirpimla
cozuldu.

Hakem bulgusu: uyusmazliklarin **hicbiri okuma hatasi degildi**. Hepsi ya
konvansiyon farkiydi (sekil-sik etiketi yazilir mi, sekil alti roma
maddeleri soru kokune girer mi) ya da kitabin kendi dizgi hatasiydi
("III ve III", ayni metinli iki sik, iki kez basilan "Yalniz I"). Dizgi
hatalari oldugu gibi korundu.

### Cevap dagilimi egriligi -- kontrol grubu kitabin kendi icinde

Egrilik var (ki-kare 33,0; df=4). AYT'de bunun kitaba mi hatta mi ait
oldugunu ayirt etmek icin disaridan OSYM verisi gerekmisti. Burada kontrol
grubu kitabin icinde:

| Altkume | n | ki-kare | A% | E% |
|---|---|---|---|---|
| Cikmis sorular (OSYM/MSU) | 91 | **4,1** | 16,5 | 22,0 |
| Yayinevinin kendi sorulari | 800 | **33,2** | 14,1 | 26,4 |

Ayni sayfalar, ayni tespit edici, ayni okuyucular. OSYM sorulari duzgun
dagilirken yayinevi sorulari egri -- egrilik **yayinevinin** ozelligi.

Ek capraz dogrulama: 91 cikmis sorunun 91'inde metinde basili sinav-yil
etiketi var ve bu, konu agacindan gelen "Cikmis Sorular" etiketiyle 91/91
ortusuyor.

### Yonlendirici adayi TYT'de REDDEDILDI

PR #250'nin harness'i AYT verisinde `alt_ust_simge >= 1 VEYA tablo_sik
VEYA ondalik >= 1` kuralini ADAY isaretlemis, "bir sonraki kitapta
dogrulanmali" demisti. TYT'de 891 sorunun tamami iki kez okundugu icin
kuralin recall'u dogrudan olculdu: hakeme giden 6 sorunun **3'unu**
yakaliyor, birebir-olmayan 18 sorunun **9'unu** -- ve bunu %28,4
yonlendirme maliyetiyle yapiyor. Sifir tolerans kurali geregi **RET**.
AYT'deki 18/18 sonucu o kitaba asiri uyum cikti.

Bu, harness'in ise yaramadigi anlamina gelmiyor; tam tersine harness'in
sordugu soruyu cevapladi ve kurali uretime tasimadan once eledi.

### Ithal sonucu

| Denetim | Sonuc |
|---|---|
| yazilan satir | 891 |
| `is_active` | **0** |
| `v_safe_for_beta` kapisindan gecen | **0** |
| JSON <-> DB simetrik fark | 0 / 0 |
| soru metni / 5 sik / cevap / sayfa birebir | 891/891 (her biri) |
| FIZ-NEOT yapraginda | 891/891 |
| kirpim dosyasi diskte | 891 soru + 951 varlik |
| cocuk tablo yetimi | 0 |
| mojibake | 0 |
| bekci mutasyonu | **5/5 bozuk durumda kirmizi** |

### Doldurulamayan tek alan ve nedeni

`morphology_complexity` 891 satirin tamaminda **0,35** -- yani sabit.
Sebep uydurma degil, olcum: repo'nun Zemberek'siz yolu
(`_simple_root_suffix_split`) kelime basina EN FAZLA BIR ek soyuyor, bu
yuzden soru duzeyinde deger {0,0; 0,35} ikilisine cokuyor ve her fizik
sorusunda en az bir ekli kelime bulundugu icin 0,35 cikiyor.

Alan bu haliyle bilgi tasimiyor. Iki secenek vardi: (a) 0,5 sabitini
yazmak (AYT'nin yaptigi), (b) hesaplanan sabiti yazip ACIKCA isaretlemek.
(b) secildi: `pipeline_metadata.morfoloji_kaynagi =
'heuristik_zemberek_yok_sabit'`. Bir bekci bu isaretin dusmesini yakalar,
boylece ileride kimse bu sabiti "olculmus morfolojik karmasiklik"
sanmaz. Makinede `zemberek-full.jar` var ama jpype Java 9+ istiyor ve
kurulu Java 8; Zemberek acildiginda `--meta-guncelle` 891 satiri yeniden
hesaplar.

### 10 Eylul -- TYT toplu beta onayi (0016)

Urun sahibi bireysel insan denetimini atlayip toplu denetimi beta surumune
ertelemeye karar verdi; AYT icin ayni karar 0014 ile uygulanmisti.

**Kapi yuku once OLCULDU.** `v_safe_for_beta` tanimi pg_views'ten okundu ve
her kosul TYT satirlarina karsi ayri sayildi:

| Kosul | TYT'de |
|---|---|
| demoted_at yok | 891/891 geciyor |
| pipeline_metadata NOT NULL | 891/891 geciyor |
| sik_bos yok | 827/891 (64'u engelli) |
| quality_review_status in (human_verified, auto_judged_high) | **0/891 ENGEL** |
| (is_ai_generated=false OR review_status=APPROVED) | **0/891 ENGEL** |
| uyum sinyali (6 anahtardan biri) | **0/891 ENGEL** |

Uc kilit acildi, `sik_bos` kilidi ACILMADI. Sonuc: **827 satir kapidan
geciyor, 64'u pasif kaldi.**

#### AYT'den ayrilan nokta: konsensus gerekcesi

0014 (AYT) `auto_judged_high`i **cift okuma VE bagimsiz cozum-dogrulamasina**
dayandirmisti. TYT'de cozum dogrulamasi YOK -- urun karari geregi sorular
tekrar cozulmedi. Ayni gerekceyi kopyalamak yanlis bir kalite beyani olurdu.

TYT'nin iki sinyali sunlar ve ikisi de olculdu:

1. **Cift bagimsiz okuma** (tam kapsam): bicimsel normalizasyon sonrasi hakem
   disi 870/870 birebir; kalan 21 soru hakem turunda cozuldu; uyusmazliklarin
   hicbiri okuma hatasi degildi.
2. **Basili cevap anahtari capraz kontrolu** (iki duzeyde): soru duzeyinde
   anahtarin harfi transkript edilen siklarda var (891/891); blok duzeyinde
   anahtardaki cevap sayisi bloktaki soru sayisina esit (109/109).

Bu iki sinyal **transkripsiyonu** dogrular. **Cevabin kendisi dogrulanmadi**;
cevap kitabin basili anahtarindan gelir ve tek kaynaktir. Ayrim kaybolmasin
diye metadata'ya acikca yazildi:

    konsensus_sinyalleri = ['cift_bagimsiz_okuma',
                            'basili_anahtar_capraz_kontrolu']
    cozum_dogrulamasi    = 'yapilmadi_urun_karari'   (ithalden beri duruyor)

`human_verified` YAZILMADI, `is_ai_generated` true KALDI.

#### Iki hata, ikisi de olcumle yakalandi

**1. SQL NULL tuzagi (bekcide).** `toplu_onay_izi` bekcisi 0016'dan ONCE de
yesildi. Sebep: anahtar hic yokken `pipeline_metadata ->> 'onay_turu'` NULL
doner, `NULL <> 'toplu_beta_sahibi'` de NULL uretir ve `FILTER` onu saymaz --
yani **iz hic yokken bekci yesil kaliyordu**. Karsilastirmalar
`IS DISTINCT FROM` ile NULL-guvenli hale getirildi; duzeltmeden sonra bekci
0016 oncesi dogru sekilde kirmizi oldu.

**2. Alembic revizyon adi 32 karakteri asti.** Ilk ad
`0016_neofizik_tyt_beta_toplu_onay` (33 karakter) idi;
`alembic_version.version_num` `varchar(32)` oldugu icin migration kendi
UPDATE'lerini kosduktan SONRA patladi ve islem tamamen geri alindi (DB
dokunulmadan kaldi). Ad `0016_neofizik_tyt_beta_onay` (27) olarak
kisaltildi. **Revizyon adlari 32 karakteri asmamali.**

#### Bekci mutasyonu

| Mutasyon | Bozukken | Geri alinca |
|---|---|---|
| `quality_review_status = 'pending'` | KIRMIZI | yesil |
| `onay_turu` anahtarini sil | KIRMIZI | yesil |
| `quality_review_status = 'human_verified'` | KIRMIZI | yesil |
| `konsensus_sinyalleri` anahtarini sil | KIRMIZI | yesil |
| **AYT gerekcesini kopyala** (cozum dogrulamasi iddiasi) | **KIRMIZI** | yesil |
| `is_ai_generated = false` | KIRMIZI | yesil |

**6/6.** Ayrica `sik_bos` kilidi ayri dogrulandi: bir `sik_bos` satirina TAM
onay izi verilse bile kapidan gecmiyor (kural view'de zorunlu tutuluyor).

#### Sonuc

| Kitap | Toplam | Aktif | Kapidan gecen | sik_bos |
|---|---|---|---|---|
| Neofizik AYT Fizik Soru Bankasi 2025 | 1218 | 1181 | 1181 | 37 |
| Neofizik TYT Fizik Soru Bankasi | 891 | **827** | **827** | 64 |

Konu sayaclari yenilendi: FIZ-NEOT agacinda toplam 827 aktif soru.
Bekciler: TYT 13 + AYT 8 = **21/21 yesil**.

---

## 11 Eylul -- Mikro Orijinal 2025 AYT Geometri Soru Bankasi ithali (0017)

Baska bir yayinevinin geometri kitabi PASIF ithal edildi: **1211 yeni satir**
(veri setinde 1213 soru; 2'si asagida anlatilan nedenle zaten DB'de). Yontem
ve tum olcumler `veriseti/zkitap/cikti/GEO_YONTEM.md`'de.

### Kaynak: cozunurluk tavani 1080p

Kitap 416 sayfa, PDF'te metin katmani YOK ve gomulu goruntu 1920x1080 --
kaynak PNG'ler de ayni. Gercek icerik alani ~725x790 piksel; cevap seridi
metni 8 piksel yuksek. Daha yuksek cozunurluk YOK, yontem bu tavana gore
secildi.

### Neofizik'ten ayrilan uc nokta

**1. Sayfa turu ayrimi gerekiyordu.** Kitapta iki tur icerik sayfasi var:
coktan secmeli test sayfalari ve acik uclu "Ornek" (konu anlatimi) sayfalari.
Ornek sayfalari ithal EDILMEMELI. Ayirt edici olcu, sayfa alti serit
kutusunun cerceve genisligi: test sayfalarinda 615/616, ornek sayfalarinda
443-446. 403 icerik sayfasi -> **237 test sayfasi**. 8 aykiri deger tek tek
goruldu, hepsi ornek sayfasi cikti.

Once "kirmizi konu sekmesinin tarafi sayfa turunu ayirir" hipotezi denendi ve
OLCUMLE CURUTULDU (solda 202 / sagda 201; taraf sayfa PARITESINE bagli).

**2. Sayfa paritesi kaymasi.** Icerik blogu tek/cift sayfalarda ~15 px
kayiyor (tek: sol ikon x=627, cift: 642; 237/237 istisnasiz). Sabit sutun
siniri kullanilamiyor; sinirlar her sayfada ikon x'inden turetiliyor.

**3. Birincil sinyal IKON.** Neofizik'te magenta soru numarasiydi; burada
numara zayif bordo, buna karsilik buyutec ikonu cok kararli (alan 115-145 px,
14x14). Ikon birincil, bordo numara dogrulayici.

### Segmentasyon dogrulamasi

| Olcum | Sonuc |
|---|---|
| El etiketi (20 sayfa) | **20/20 sayfa, 108/108 soru** |
| Kutu disinda kalan murekkep pikseli | **237 sayfanin 237'sinde 0** |
| Toplam soru kutusu | **1213** |

"Kutu disinda sifir piksel" olcusu, segmentasyonun hicbir icerigi
kaybetmediginin dogrudan kanitidir -- IoU gibi dolayli bir skor degil.

### Uc bagimsiz kanalin ayni sonuca varmasi

| Kanal | Sonuc |
|---|---|
| Cevap seridi, iki bagimsiz okuma | 237/237 sayfa **sifir uyusmazlik** |
| Serit girdi sayisi == tespit edilen soru sayisi | **237/237 sayfa** |
| Serit numara zincirinden cikan test grubu | **149** |
| Sayfa basligindan (banner) cikan test grubu | **149**, sayfa kumeleri **birebir ayni** |
| Kitabin icindekiler sayfasi | 149 test (iki dizgi hatasi birbirini goturuyor) |
| Kirpim etiketindeki tahmin == basili numara | **1209 / 1213** |

### Iki YAYINEVI dizgi hatasi (kitabin kendi hatasi)

1. **s77 numara kaymasi.** Sayfada basili numaralar 6,7,8,9; sayfanin cevap
   seridi 7,8,9,10 diyor (onceki sayfa 1-5'te bitiyor, yani BASILI olan
   dogru). Iki bagimsiz okuma da 6,7,8,9 okudu. Cevap eslemesi KONUMSAL
   oldugu icin sonuc degismiyor; sapma
   `pipeline_metadata.anahtar_numara_sapmasi=true` ile 4 satirda isaretli ve
   bir bekci bunun yalnizca o 4 satirda kalmasini koruyor.
2. **Icindekiler ile kitap celisiyor.** Icindekiler "CEMBERDE UZUNLUK ...
   Kazanim Testi 1-2-3-4-5" diyor, kitapta 4 tane basili ("Kiris Ozellikleri
   1" var, 2 yok). Buna karsilik icindekilerin "DOGRUNUN ANALITIGI" basligi
   altina sakladigi ayri bir test var: **ESITSIZLIK GRAFIKLERI** (s358-359).
   Ikisi birbirini goturuyor. Konu agaci bu yuzden icindekilerden DEGIL,
   her sayfanin kendi basligindan uretildi: 5 unite, **31 konu**.

### Iki bagimsiz transkripsiyon + hakem

1213 soru iki kez bagimsiz okundu:

| Uyum | Soru |
|---|---|
| Birebir (>= 0.995) | **1187** |
| Yuksek (0.95-0.995) | 16 |
| Hakeme giden (< 0.95) | **10** |
| Dusuk (< 0.85) | 0 |
| `basili_no` farkli okunan | **0 / 1213** |

Hakem turu 46 kalem (10 dusuk uyum + okuyucularin supheli isaretledigi 37,
tekillestirilmis): 39 kez P, 6 kez Q, 1 kez hakemin kendi okumasi.

Ayrica ilk montajlarda kutu dibinin 13 px kisa olmasi nedeniyle icerik kaybi
olup olmadigi PIKSEL DUZEYINDE olculdu: 1213 sorunun **2'sinde** toplam 2
satir piksel disarida kalmisti; ikisi de tam kirpimla yeniden okundu ve metin
degismedi.

### DIS DOGRULAMA: OSYM ile birebir carpisma

Ithal, iki sorunun DB'de ZATEN var oldugunu bildirdi. Inceleme: her ikisi de
`OSYM 2025 TYT` kaynagindan (s33 ve s34) daha once ithal edilmis satirlar.
Yani iki tamamen bagimsiz hat -- biri resmi OSYM PDF'inden, digeri bir
yayinevinin 1080p ekran goruntusu kitabindan -- ayni soru icin:

| Alan | OSYM kaynagi | Geometri hatti |
|---|---|---|
| Soru metni + 5 sik | ayni md5 | ayni md5 |
| Dogru cevap | E / D | E / D |
| Sinav yili | 2025 / 2025 | 2025 / 2025 |
| Sinav turu | TYT / TYT | TYT / TYT (rozetten) |

Bu, segmentasyon + transkripsiyon + konumsal cevap eslemesi + rozet okumasi
zincirinin tamaminin sifir serbestlik dereceli bir dis kontrolu. Iki satir
OSYM kaynagina bagli KALDI (ithal atladi; idempotent).

### Cevap dagilimi -- kontrol grubu yine kitabin icinde

| Kume | n | A | B | C | D | E | ki-kare (sd=4) |
|---|---|---|---|---|---|---|---|
| Tumu | 1213 | 198 | 245 | 295 | 262 | 213 | **24.70** |
| OSYM cikmis (kontrol) | 86 | 11 | 17 | 20 | 23 | 15 | **4.93** |
| Yayinevinin kendi yazdigi | 1127 | 187 | 228 | 275 | 239 | 198 | **21.64** |

p<0.05 esigi 9.49. Kontrol grubu esigin ALTINDA, yayinevi kumesi USTUNDE:
sapma HATTAN degil YAYINEVINDEN geliyor. Ayni tasarim Neofizik TYT'de
kurulmustu; burada bagimsiz bir kitapta tekrarlandi.

### Cikmis soru rozetleri

Turuncu "Cikmis Soru (YIL / SINAV)" rozeti renkle tespit edildi; 91 adayin
iki bagimsiz okumasi **sifir uyusmazlikla** 5'inin turuncu bir SEKIL oldugunu
(rozet degil) bildirdi. Bagimsiz ikinci dedektor (renk + sekil filtresi) ayni
**86** rozeti buldu. Dagilim: TYT 39, AYT 28, MSU 17, YGS 1, LYS 1
(2012-2025). `osym_year` yalniz bu satirlarda dolu.

### Gorseller

Sorularin **1069 / 1213**'u sekil iceriyor; sekil olmadan soru eksik kalir.
`question_image_url` TAM SORU KIRPIMIDIR ve kirpim kutusu her satirda
saklanir, yani gorseller PDF'ten her ortamda yeniden uretilebilir
(`scripts/kitap/mikro_geo_kirp.py`, 1213 gorsel uretildi). Neofizik'teki gibi
VARLIK DUZEYINDE ayristirma yapilmadi; bu bilerek boyle ve
`gorsel_kaynagi='tam_soru_kirpimi'` ile isaretli -- bos bir varlik listesi
"aradik bulamadik" gibi okunmasin diye.

### Bekci mutasyonu

| Mutasyon | Sonuc |
|---|---|
| `cevap_eslemesi` izini degistir | **KIRMIZI** |
| s77 disinda bir satira sapma isareti koy | **KIRMIZI** |
| `kirpim_kutusu`'nu bosalt | **KIRMIZI** |
| Anahtarin gosterdigi sikki bosalt (R5) | **KIRMIZI** |
| Rozetsiz satira `osym_year` yaz | **KIRMIZI** |
| `review_status='APPROVED'` yap | **KIRMIZI** |
| `onay_turu` (toplu onay izi) ekle | **KIRMIZI** |

**7/7.** Her mutasyon uygulandi, test kosuldu, deger geri alindi; sonrasinda
DB durumu birebir eski haline dondu (dogrulandi).

### Sonuc

| Olcu | Deger |
|---|---|
| Toplam satir | **1211** |
| `is_active` | **0** |
| `is_public` | **0** |
| `is_ai_generated` | 1211 |
| `review_status='PENDING'` | 1211 |
| **Kapidan (`v_safe_for_beta`) gecen** | **0** |
| Yaprak konuya bagli | 1211 / 1211 (31 konu) |
| `explanation` dolu | 0 |
| R5 ihlali | 0 |

**Bekleyen karar (urun sahibi):** Neofizik'te oldugu gibi toplu beta onayi
verilecek mi? Verilmedigi surece bu 1211 soru kapinin disinda kalir.
Geometride sik_bos bayrakli soru YOK, yani onay verilirse 1211'in tamami
kapidan gecmeye aday olur.

### 11 Eylul (ayni gun, ithal sonrasi) -- "eksiksiz mi?" denetimi iki kusur buldu

Ithal merge edildikten sonra sorulan "tum sorular ve gorseller eksiksiz
kaydedildi mi?" sorusu uzerine yapilan olcum, ikisi de gercek olan iki kusur
cikardi.

#### 1. Kirpim kutusu 291 soruda 1-3 piksel kesiyordu

Sol sutunun sag siniri `sagx - 8` idi. Bu deger, kendi olcum penceresi
`sagx - 8`'de bittigi icin dogru gorunen bir SONUC DEGIL, PENCERE
ARTEFAKTIYDI. Sinirsiz tarama gercek dagilimi verdi: sol sutun metni
`sagx - 3`'e kadar uzaniyor, sag sutun ikonu ise `sagx - 6`'dan basliyor --
iki sutun x ekseninde CAKISIYOR, onlari ayiran sey dikey konum.

Kayip neden daha once gorulmedi: "237 sayfanin 237'sinde kutu disinda sifir
murekkep" olcusu SAYFA duzeyindeydi ve sol/sag kutular oluk bolgesinde ust
uste bindigi icin sol sutundan kesilen pikseller SAG kutunun icine dusuyordu.
Birlesim her seyi kapsiyordu, tekil kutu kapsamiyordu. Olcum KUTU BAZINA
indirilince kayip gorundu.

Ayni hata dikey sinirda da vardi (`nxt - 11`, 8 sinirda kesiyordu). Yeni
degerler: `bol = sagx - 2`, `alt = nxt - 9`. Duzeltme sonrasi dort kenarda da
kutu bazinda kayip **0**. Metin ve cevaplar DEGISMEDI (transkripsiyon
montajlari zaten x=976'ya kadar genisti; soru_hash ve id sabit kaldi);
yalnizca `kirpim_kutusu` ve 1213 PNG yenilendi.

#### 2. `--meta-guncelle` baska bir kaynagin 2 satirini ezdi ve servisten dusurdu

Kutulari duzelttikten sonra kosulan `mikro_geo_ithal.py --meta-guncelle`,
"id'si zaten var olan" TUM satirlari yeniliyordu ve kaynak kitap kontrolu
yoktu. Bu kitaptaki iki soru resmi `OSYM 2025 TYT` kitapciginda da var (ayni
metin + ayni 5 sik -> ayni soru_hash -> ayni id). Sonuc: o iki OSYM satirinin
`pipeline_metadata`'si geometri hattininkiyle degisti, `osym_resmi_kaynak`
sinyali kayboldu ve **iki satir da `v_safe_for_beta`'dan dustu** -- aktif
kalmalarina ragmen servis havuzundan sessizce cikmis oldular.

Geri yukleme TAHMINLE YAPILMADI. `scripts/osym/kitapcik_cikar.py`
`backend/data/osym/tyt_2025.pdf` uzerinde yeniden kosuldu ve iki sorunun
orijinal `soru_no` (34, 36) ve `bayraklar` (`["gorsel"]`) degerleri dogrudan
PDF'ten okundu. Sabit alanlar ve skaler sutunlar ayni sayfalardaki kardes
OSYM satirlarindan birebir alindi; `question_image_url` OSYM adlandirma
kuralindan uretildi (kural 4 kardes satirda dogrulandi, iki dosya da diskte).
Iki satir da yeniden kapidan geciyor.

**Kok neden:** `--meta-guncelle` artik yalnizca `source_book`'u bu kitap olan
satirlara dokunuyor; baska kaynakta duran ayni-hash'li satirlari adiyla
listeleyip atliyor. Regresyonu yakalayan bekci eklendi
(`test_mikro_geo_ayni_hash_li_yabanci_satirlar_bozulmamis`), mutasyonla
dogrulandi (temiz veride yesil, OSYM satirina geometri izi eklenince
kirmizi, geri alininca yesil).

#### Duzeltme sonrasi olculen son durum

| Olcu | Deger |
|---|---|
| Dort tabloda satir (bank/content/metadata/statistics) | 1211 / 1211 / 1211 / 1211 |
| Bos sik, bos metin, R5 ihlali | 0, 0, 0 |
| Diskte OLMAYAN gorsel | **0 / 1211** |
| Acilamayan / kutu boyutuyla uyumsuz / tek renk gorsel | 0 / 0 / 0 |
| Toplam gorsel | 1213 dosya, 52,7 MB |
| Ayni-hash'li 2 OSYM satiri | kendi kaynaginda, aktif, kapidan geciyor |
| Geometri satirlarindan kapidan gecen | 0 (toplu onay hala verilmedi) |
| Bekci | **14/14 yesil**, mutasyon **8/8 kirmizi** |

Ders: "toplamda kayip yok" turu bir metrik, bilesenler ust uste biniyorsa
tekil kayiplari gizler. Kapsama olcusu, kapsamasi gereken BIRIMIN duzeyinde
alinmali. Ve bir olcum penceresi, olctugu buyuklugun beklenen araligindan
DAR olmamali -- yoksa cevap penceresinin kenarindan gelir.

### 11 Eylul -- Mikro Geometri toplu beta onayi (0018)

Urun sahibi ayni gun, ithal ve duzeltmelerden sonra toplu beta onayini verdi.
Fizik kitaplarindaki (0014 AYT, 0016 TYT) karara denk; kapsam ve gerekce
FARKLI.

#### Kapi yuku olculdu

`v_safe_for_beta` tanimi `pg_views`'ten okundu, her kosul 1211 satira karsi
ayri sayildi. Uc kilit vardi (`quality_review_status`, `review_status`/
`is_ai_generated`, uyum sinyali); diger bes kosulu 1211/1211 satir zaten
geciyordu. **`sik_bos` bayrakli soru YOK** -- bu kitapta sikki gorsel olan
soru cikmadi, sikler her zaman metin. Bu yuzden hedef, TYT'den farkli
olarak, satirlarin TAMAMI: 1211 (TYT'de 891'in 827'si).

#### Konsensus gerekcesi fizigin gerekcesi DEGIL

0014 gerekcesi bagimsiz cozum dogrulamasina dayaniyordu; geometride sorular
tekrar cozulmedi. 0016 iki sinyal kullanmisti. Geometride DORT sinyal var ve
ikisi TYT'de hic yoktu:

| Sinyal | Olcum | TYT'de var mi |
|---|---|---|
| `cift_bagimsiz_okuma` | 1213/1213 iki kez okundu; 1187 birebir, 10 hakeme, 0 dusuk; basili numara 1213/1213 ayni | var |
| `anahtar_seridi_cift_okuma` | 237 serit iki bagimsiz okuma, **uyusmazlik sifir** | YOK |
| `basili_anahtar_capraz_kontrolu` | soru duzeyi 1211/1211 (R5), sayfa duzeyi 237/237 | var |
| `banner_anahtar_zinciri_ortusmesi` | serit zinciri 149 test, banner 149 test, sayfa kumeleri birebir ayni | YOK |

Dordu de TRANSKRIPSIYONU ve SEGMENTASYONU dogrular; CEVABIN KENDISI
dogrulanmadi ve `cozum_dogrulamasi='yapilmadi_urun_karari'` izi yerinde
kaldi. OSYM ile birebir carpisma (2 soru) bilerek sinyal listesine
KONULMADI -- 1213'un 2'sini kapsayan bir bulguyu satir duzeyi sinyal gibi
yazmak diger 1209 icin fazla iddia olurdu.

#### Bekcinin gercekten olctugunun kaniti

Degisen/yeni dort bekci migration'dan ONCE kosuldu ve **4/4 KIRMIZI** cikti;
migration sonrasi yesile dondu. Ayrica 8 mutasyon uygulandi, **8'i de
yakalandi**: is_active=false, review_status=PENDING, human_verified,
onay_turu silme, **fizigin gerekcesini kopyalama**, cozum_dogrulamasi silme,
is_ai_generated=false, ve tam onay izi olan bir satira `sik_bos` eklenince
view'in onu kapinin disina atmasi (D10 kilidi).

#### Geri alinabilirlik iddia degil, olcum

`downgrade` CANLI kosuldu: 1211 satir birebir eski haline dondu (aktif 0,
PENDING 1211, quality pending 1211, eklenen dort anahtar silindi, onceki
anahtarlar -- `kirpim_kutusu`, `cozum_dogrulamasi` -- korundu, gunluk
tablosu dusuruldu, kapidan gecen 0). Sonra yeniden `upgrade` kosuldu ve
37/37 bekci yesile dondu.

#### Sonuc

| Kitap | Toplam | Aktif | Kapidan gecen | sik_bos |
|---|---|---|---|---|
| Neofizik AYT Fizik Soru Bankasi 2025 | 1218 | 1181 | 1181 | 37 |
| Neofizik TYT Fizik Soru Bankasi | 891 | 827 | 827 | 64 |
| **Mikro Orijinal 2025 AYT Geometri** | **1211** | **1211** | **1211** | **0** |

`is_ai_generated` uc kitapta da true KALIR; `is_public` uc kitapta da false.
Konu sayaclari yenilendi (ornek: GEO-MIKRO-U1-BENZERLIK 79, UCGENDE-ACI 74).
Bekciler: geometri 16 + TYT 13 + AYT 8 = **37/37 yesil**.

---

## EK-4: `source_book` bir kimliktir -- adlandirma sozlesmesi (11 Eyl 2026)

### Sorun nasil gorundu

Mikro geometri ithali icin yazilan devir notunda `source_book` degerinin evde
iki turlu yazildigi gorundu: modern ithaller ASCII
(`Mikro Orijinal 2025 AYT Geometri Soru Bankasi`), eski kayitlar Turkce
karakterli (`345 2025 Tyt Kimya Soru Bankasi`). "Hangisi dogru" sorusu
tahminle degil sayimla cevaplandi.

### Olcum (canli DB, tum kolon tarandi)

| Kume | Farkli deger | Satir | ASCII |
|---|---|---|---|
| `pipeline_metadata ? 'ithal_araci'` (modern ithaller) | 5 | 3.611 | 5/5 |
| Eski hattan kalan, ASCII | 50 | 2.973 | -- |
| Eski hattan kalan, Turkce karakterli | 137 | 2.823 | -- |
| **Toplam** | **192** | **9.407** | |

Yani ortada canli bir anlasmazlik YOK: ASCII yazim modern ithal araclarinin
yazdigi yazimdir ve 5/5 tutarlidir. Turkce karakterli olanlarin tamami eski
hattan kalmadir. Sozlesme bu olcumden turetildi, secilmedi.

### Asil bulgu: bolunmus ad

192 deger Turkce katlanip (c-cedilla -> c vb.) kucuk harfe indirilip
alfanumerik disi karakterler atilarak normalize edildi. **Tek bir cakisma**
cikti -- ayni kitap iki yazimla bolunmus, fark tek harfte:

| source_book | Satir | Fark |
|---|---|---|
| `Aromat Tyt T<u>rkce Model Sorular` | 8 | duz `c` (U+0063) |
| `Aromat Tyt T<u>rk<c>e Model Sorular` | 1 | `c` cedilla (U+00E7) |

Hangisinin dogru oldugu OLCULDU: diskteki kitap klasoru
`veriseti/zkitap/screenshots/` altinda duz `c` ile yazili, yani 8 satirlik
yazimla birebir. Tek satirlik olan dizgi hatasidir.

**Neden onemli:** `source_book` bu depoda etiket degil KIMLIKTIR -- toplu
onay/aktiflestirme migration'lari (0011, 0012, 0014, 0016, 0018) hedeflerini
bu kolona gore secer. Bolunmus ad, bu kolona bakan HER korumada sessiz bir
delik acar: koruma "benim kitabim" derken 9 satirin 1'ini disarida birakir.

### Ikinci bulgu: koruma kopyalanmamis

PR #254'te `mikro_geo_ithal.py`'ye eklenen yabanci-satir korumasi
(`--meta-guncelle` yalnizca bu kitabin satirlarina dokunsun) diger iki ithal
script'ine TASINMAMISTI. 11 Eyl 2026'da olculdu:

| Script | Eski ayrimsiz desen | Ortak koruma |
|---|---|---|
| `mikro_geo_ithal.py` | yok (PR #254'te duzeltildi) | yoktu (kendi kopyasi vardi) |
| `neofizik_ithal.py` | **VAR** | **YOK** |
| `neofizik_tyt_ithal.py` | **VAR** | **YOK** |

Yani `soru_hash` carpismasi durumunda (ayni metin + ayni 5 sik -> ayni
`id`) iki fizik ithali de baska bir kitabin satirini ezebiliyordu. Ayni acik
11 Eyl 2026'da 2 resmi OSYM satirinin metadata'sini ezmis ve ikisi de servis
kapisindan dusmustu. Depoda `source_book` sabiti tanimlayan **26 ayri yer**
var; korumayi kopyalanacak bir kalip olarak birakmak, her yeni kitapta
unutulma sansi demekti.

### Yapilan

1. **`backend/scripts/kitap/kaynak_sozlesmesi.py`** (yeni): kanonik ad
   kayitlari (`KAYNAK_KAYITLARI`), ad dogrulama (`kaynak_adi_dogrula`),
   normalize anahtar (`normalize_anahtar`) ve yabanci-satir ayrimi
   (`ayristir`). Koruma artik kopyalanan bir kalip degil, cagrilan tek
   fonksiyon.
2. **Uc ithal script'i** adi ve onegi bu kayittan okuyor; ucu de `ayristir`
   kullaniyor.
3. **`0019_kaynak_adi_tekil`**: bolunmus Aromat yazimini birlestirir.
   Yalnizca `source_book` kolonu degisir; silme yok, gunluk tablosu var,
   `downgrade` tam tersini yapar.
4. **`tests/e2e/test_kaynak_sozlesmesi.py`** (yeni, 13 bekci): adlandirma
   kurallari, "iki farkli yazim ayni kitaba cozulmesin", modern ithallerin
   kayitli+ASCII olmasi, uc script'in ortak korumayi kullanmasi ve eski
   desenin geri gelmemesi.

### Bekcilerin gercekten olctugunun kaniti

- `test_iki_yazim_ayni_kitaba_cozulmuyor` migration'dan **ONCE KIRMIZI**
  (Aromat ciftini adiyla raporladi), migration sonrasi yesil.
- `test_ithal_scriptleri_ortak_korumayi_kullaniyor` icin HEAD surumleri
  ayni olcutle tarandi: 3/3 script "ortak koruma yok", 2/3 ayrica "eski
  ayrimsiz desen var" -- yani bekci yamasiz kodda **KIRMIZI** olurdu.
  Calisma agacinda 3/3 temiz.
- `downgrade` CANLI kosuldu: 8 + 1 dagilimi birebir geri geldi, gunluk
  tablosu dusuruldu; sonra yeniden `upgrade` kosuldu.
- Ilgili paket: `test_kaynak_sozlesmesi` + `test_mikro_geo_ithal` +
  `test_neofizik_ithal` + `test_neofizik_tyt_ithal` +
  `test_osym_aktiflestirme` = **54/54 yesil**.

### Yan urun: satir numarasi yerine bekci

Ayni devir notu `/static/crops` mount'unu `core/application.py:441` diye
SATIR NUMARASIYLA anlatiyordu. Satir numarasi ilk refactor'de bayatlar ve
bayat bir referans dogrulanmis bir gercek gibi gorunur. Depoda kirpim
URL'sinin BICIMINI dogrulayan uc test vardi ama mount'un varligini
dogrulayan yoktu. `tests/fast/test_kirpim_mount_sozlesmesi.py` (3 bekci) bu
boslugu kapatir: mount yolu, `CROP_IMAGE_DIR` ile disaridan ayarlanabilirlik
ve "dizin yoksa mount etme" korumasi icerikten dogrulanir. Artik dokumanin
satir numarasi vermesine gerek yok, testin adini vermesi yeter.

### Kalan borc (bu turda KAPSAM DISI, bilerek)

- Eski hattan kalan 187 deger (5.796 satir) normalize EDILMEDI. Bunlarin
  cogu diskteki klasor adiyla birebir; toplu yeniden adlandirma ayri bir
  olcum ve ayri bir karar ister. Yeni bekci yalnizca `ithal_araci` tasiyan
  satirlari kapsar -- kapsam boyle secildi ki "yesil" yanlis bir sey
  iddia etmesin.
- Eski degerlerde gorunen dizgi hatalari (`Sopru Bankasi`, `Soeu Bankasi`,
  `Matemateik`, `Porblemler`, `Sohagi`, `Aramot`) duzeltilmedi; hicbiri
  normalize cakismasina yol acmiyor, yani bugun bir korumayi delmiyorlar.
