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
    Aktiflestirme hukuki onay bekler (kullanici karari). **AYT 2025** de
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

**Cozulemeyen:** icerik. 5.796 soru, dort ders tamamen eksik, yedekteki
36.967 soru halusinasyon. Bu bir veritabani sorunu degil, bir icerik sorunu.
