# B3 — Sınav Konu Kırılımı: ders bazı → konu bazı

**Tarih:** 21 Ağustos 2026 · **Dal:** `feature/self-evolution-optimization`
**Tasarım:** `docs/superpowers/specs/2026-08-21-b3-konu-kirilimi-design.md`
**A1 bağlamı:** altın yolun son ayağı — *"netini ve **konu kırılımını** görür"*

---

## TL;DR — tek cümlelik yargı

**Motor tarafı KAPANDI ve ölçüldü (1 kova → 13/14 kova, API == DB); B3 bir bütün olarak
KAPANMADI:** iki üretim tüketicisi sessizce bozuldu (aynı ders hem "zayıf" hem "güçlü";
tek sınav 13 sınav gibi sayılıyor), frontend imajı yeniden kurulmadığı için **öğrenci
hâlâ göremiyor**, ve tasarımın sıralama + "Konu atanmamış" şartları **%0 test kapsamında**.

---

## Methodology

Her sayı, altında yazan komutla üretildi. Beyan yok.

| Ölçüm | Alet / komut | N | Seçim | Tekrarlanabilir mi |
|---|---|---|---|---|
| DB konu sayısı | `psql -U postgres -p 5434 -d kiro2 -f <dosya>.sql` (Türkçe içerik → `-c` inline YASAK) | 40 soru / oturum | `exam_questions` ⋈ `question_bank` ⋈ `topic_hierarchy`, `GROUP BY th.code, th.name_tr` | Evet — SID sabit |
| API konu sayısı | `curl GET /api/v1/osym-exam/{sid}/subject-performance` (Bearer) | 13 / 14 satır | Aynı SID | Evet |
| Kapı (havuz) | `SELECT count(*), count(DISTINCT primary_topic_id) FROM mv_safe_for_beta` | 3560 / 26 konu | Tam sayım, örneklem değil | Evet |
| N+1 kontrolü | SQLAlchemy `before_cursor_execute` sayacı, HEAD sürümü container'a `_head_engine.py` olarak kopyalanıp aynı süreçte yan yana koşuldu | 2 sürüm × 1 oturum | — | Evet |
| Sorgu şekli | `stmt.compile(dialect=postgresql, literal_binds=True)` + `stmt.get_final_froms()` | 1 sorgu | — | Evet |
| Test yükü | Kaynak **bellekte** mutasyona uğratılıp `sys.modules`'a enjekte edildi (diske YAZILMADI — iş commit'sizdi, `verification.md` "GERİ ALIM BİR İDDİADIR") | 4 mutant × 663 test | M1 gruplama, M2 sıralama, M3 topic_code, M4 NULL-dalı | Evet — `B3V_MUT=<M>` |

**Seed/rastgelelik yok.** İki canlı oturum kullanıldı, ikisi de `status=completed`:

- `f7e0b054-41db-4215-9107-4c1d3c6169cf` — keşif fazında zaten vardı, 40 soru / DB'de **14** konu
- `5d2269fc-9f98-4666-9b2a-3d4960b68b80` — bu turda uçtan uca üretildi (kayıt → giriş →
  create → start → 25 cevap → complete), 40 soru / DB'de **13** konu

**Truncation:** yok. Aşağıdaki tüm liste çıktıları tam; kısaltılan yerlerde
"kalan N" satırı açıkça yazıldı.

**Bilinçli tasarım kararı:** 40 sorunun **25'i cevaplandı, 15'i boş bırakıldı**.
Sebep: `StudentAnswer` outerjoin'i (`osym_exam_engine.py:1368-1374`) — cevaplanmamış
sorunun kırılımdan **düşmediğini** ölçmek için. Hepsi cevaplansaydı bu dal hiç sınanmazdı.

---

## ÖNCE / SONRA — aynı veri, aynı süreç

Bu tablonun kanıt değeri şuradan gelir: **veri değişmedi, yalnız kod değişti.**
HEAD sürümü container'a ikinci bir modül olarak kopyalandı, iki sürüm aynı oturum
üzerinde arka arkaya koşuldu.

| Ölçüm | ÖNCE (HEAD) | SONRA (çalışma ağacı) |
|---|---|---|
| Dönen kova sayısı — `f7e0b054` | **1** | **14** |
| Dönen kova sayısı — `5d2269fc` | **1** | **13** |
| Farklı `topic_code` | **0** (alan yoktu) | 14 / 13 |
| `sum(total_questions)` | 40 | **40** (kartezyen yok) |
| Farklı `subject` | `['matematik']` | `['matematik']` |
| SQL `execute` sayısı | **4** | **4** (S220'nin 361→4 kazancı korundu) |

Ham çıktı:

```
--- HEAD (degisiklik ONCESI) ---
  execute sayisi       : 4
  donen kova sayisi    : 1
  sum(total_questions) : 40
--- CALISMA AGACI (degisiklik SONRASI) ---
  execute sayisi       : 4
  donen kova sayisi    : 13
  sum(total_questions) : 40
SONUC: execute 4 -> 4 | kova 1 -> 13
```

Canlı API çıktısı (`5d2269fc`, ilk 5 satır, hepsi `subject="matematik"`):

```json
{"total_questions":6,"correct_answers":0,"wrong_answers":4,"empty_answers":2,"success_rate":0.0,"topic_code":"MAT.MTL","topic_name":"Mutlak Değer"}
{"total_questions":5,"correct_answers":0,"wrong_answers":3,"empty_answers":2,"success_rate":0.0,"topic_code":"MAT.DNK","topic_name":"Denklemler"}
{"total_questions":5,"correct_answers":0,"wrong_answers":5,"empty_answers":0,"success_rate":0.0,"topic_code":"MAT.PRB","topic_name":"Problemler"}
{"total_questions":4,"correct_answers":1,"wrong_answers":1,"empty_answers":2,"success_rate":25.0,"topic_code":"MAT.OLS","topic_name":"Olasılık"}
{"total_questions":4,"correct_answers":1,"wrong_answers":1,"empty_answers":2,"success_rate":25.0,"topic_code":"MAT.POL","topic_name":"Polinomlar"}
```

Kalan 8: `MAT.CRP` Çarpanlara Ayırma 4 · `MAT.KMB` Kombinasyon 3 · `MAT.FON` 2 ·
`MAT.SAY` 2 · `MAT.USL` 2 · `MAT.EST` 1 · `MAT.PRM` 1 · `MAT.IST` 1.

---

## Kabul kriteri

> Gerçek bir sınav oturumu için `GET /api/v1/osym-exam/{sid}/subject-performance`
> **≥5 farklı `topic_code`** dönmeli. Karşı-ölçüm: API'nin döndürdüğü adet ile
> DB'den sayılan adet **EŞİT** olmalı.

| Kriter | Hedef | Ölçülen | Sonuç |
|---|---|---|---|
| Farklı `topic_code` (`5d2269fc`) | ≥5 | **13** | **GEÇTİ** |
| Farklı `topic_code` (`f7e0b054`) | ≥5 | **14** | **GEÇTİ** |
| Karşı-ölçüm API == DB | eşit | 13 == 13 · 14 == 14 | **GEÇTİ** |
| `topic_code IS NULL` dönen kova | 0 | **0** (sessiz varsayılana düşme yok) | **GEÇTİ** |
| Toplam korunumu Σ`total_questions` == `exam_questions` | eşit | 40 == 40 | **GEÇTİ** |

Karşı-ölçüm **sayı eşitliğiyle bırakılmadı** — 13 == 13 tesadüfen de tutabilir.
`(topic_code, topic_name, soru_sayısı)` **üçlülerinin kümesi** karşılaştırıldı:
`API − DB = ∅`, `DB − API = ∅`, `KÜMELER AYNI = True`.

**Kabul kriteri GEÇTİ.** Ama kabul kriteri B3'ün tamamı değil — aşağıya bak.

---

## Ölçüm aleti arızası — bulundu, düzeltildi, gizlenmedi

Kayıt altına alınmasının sebebi: bunlar bulgu diye raporlansaydı 3 fantom üretirdi.

| Belirti | Gerçek sebep | Nasıl elendi |
|---|---|---|
| Küme karşılaştırması "False", 8 konu farklı göründü | `open('.b3_perf.json')` — `encoding=` verilmedi, Windows cp1254 varsaydı, API tarafı mojibake oldu | `od -c` ile ham bayt okundu (`b'Mutlak De\xc4\x9fer'` = geçerli UTF-8) → `encoding='utf-8'` + NFC → kümeler eşitlendi. **Fark veride değil ölçümdeydi.** |
| `docker exec ... /app/x` → "No such file" | Git Bash mutlak yolu `C:/Program Files/Git/app/x` diye yeniden yazıyor | `MSYS_NO_PATHCONV=1` |
| `grep ... \| head` sonrası `$?` = 0 | Boru hattında `$?` **son halkayı** (head) ölçer | Sayım ayrı komuta alındı + `wc -l` kontrol kolu |
| `/tmp_run1.txt` → `Permission denied` | bash `/tmp` = MSYS `AppData\Local\Temp`, Python `/tmp` = `C:\tmp` — iki namespace | Depo-içi göreli yola geçildi |
| Testin ayrı dosyaya konması | `tests/integration/test_osym_exam_engine.py:17-24` `patch.dict("sys.modules")` motoru **MagicMock'lu `core.database`** ile import ediyor; blok çıkışında modülleri siliyor (`e2 is e -> False`) | Yeni dosya `test_osym_exam_konu_kirilimi.py` — gerekçe RED raporunda ölçüldü |

---

## Değişiklikler (dosya:satır)

**`backend/core/osym_exam_engine.py`**
`:30-35` `TopicHierarchy` import · `:113-117` `SubjectPerformance`'a `topic_code` +
`topic_name` **SONA, varsayılanlı** · `:1351-1358` SELECT listesine `code`, `name_tr`
KOLON olarak · `:1375-1379` `.outerjoin(TopicHierarchy, ...)` · `:1384` döngü 4-tuple ·
`:1392-1400` kova anahtarı `subject` → `(subject, primary_topic_id)` · `:1461-1466`
`sort(key=lambda p: (-p.total_questions, p.topic_name or ""))`. `selectinload` üçlüsüne
DOKUNULMADI.

**`backend/api/sinav.py`**
`:257-258` `SubjectPerformanceResponse` iki yeni alan · `:271-272` `json_schema_extra` ·
`:905-906` mapping.

**`frontend/src/pages/ModernExamResultsPage.tsx`** `:63` tip · `:126-131` `topic:
s.topic_name || s.subject` · `:407` "Ders" başlığı (6 → 7 sütun) · `:422` hücre.
**`frontend/src/services/examService.ts`** `:137-141` sözleşme paritesi.

**Testler:** `tests/integration/test_osym_exam_konu_kirilimi.py` (YENİ, 4 test) ·
`tests/fast/test_osym_exam_engine_split.py` (fikstür 2-tuple → 4-tuple + 1 yeni test) ·
`tests/unit/test_api_batch2.py` (plain `Mock()` → öznitelikli) ·
`tests/unit/test_sinav_api.py` (pozisyonel çağrı **kanaryaya** çevrildi) ·
`frontend/src/test/pages/ModernExamResultsPage.konu-kirilimi.test.tsx` (YENİ).

**Neden "SONA + varsayılanlı":** `test_sinav_api.py:1118` dataclass'ı **pozisyonel**
çağırıyor (`SubjectPerformance("MATEMATIK", 40, 28, 10, 2, 70.0, 65.5, 0.8)`).
Başa/ortaya eklenen alan bu çağrıyı **sessizce yanlış alana** bağlardı. Ölçüldü:
o dosya 93/93 geçti, gerekçe tuttu.

---

## Çürütücü merceklerin bulguları

Üç bağımsız çürütücü mercek koşuldu (DOĞRULUK · REGRESYON · ÖLÇÜM GEÇERLİLİĞİ).
**3/3'ü iddianın ikinci yarısını ("hiçbir regresyon üretmeden") çürüttü.**
Hiçbiri birinci yarısını ("konu bazında dönüyor") çürütemedi.

### Çürütülemeyen (saldırıldı, ayakta kaldı) — SİLİNMEDİ, kayıtta

| # | İddia | Çürütme denemesi | Sonuç |
|---|---|---|---|
| S1 | Gruplama gerçekten `(subject, topic)` | `git show HEAD:` ile eski anahtar okundu → `subject_stats[subject]` (yalnız ders) | Değişiklik gerçek |
| S2 | `outerjoin` gerçekten OUTER | Sorgu sıfırdan bağımsız kuruldu + `postgresql` derlemesi | `LEFT OUTER JOIN topic_hierarchy` = True |
| S3 | Kartezyen yok | `get_final_froms()` = **1** (`_ORMJoin`); Σ40 == DB 40 | Yok |
| S4 | N+1 yok | `before_cursor_execute` sayacı: 4 → 4 | S220 kazancı korundu |
| S5 | `topic_hierarchy.is_active` tuzağı | `count(*) FILTER (WHERE NOT is_active)` = **0/45** | Bugün etkisiz |
| S6 | Sıralama deterministik | Aynı oturum 2 kez koşuldu, `diff` boş | Deterministik |
| S7 | Çok-dersli aynı-konu çakışması | `HAVING count(DISTINCT subject_area)>1` → **0 satır**; 8 oturumun 8'i tek dersli | Vektör boş |
| S8 | Pozisyonel dataclass çağrısı kırılmadı | `test_sinav_api.py` 93/93 | Kırılmadı |
| S9 | Test yükü taşıyor | M1 (gruplama) → 2 failed · M3 (`topic_code=None`) → failed | Çivili |

### Çürütülen — gerçek regresyonlar

**P0-1 · `backend/core/osym_exam_engine.py:2168-2171` — `session_to_sinav_sonucu`
güncellenmedi.**
Adaptör hâlâ `KonuPerformansi(konu=sp.subject)` kuruyor. Motor artık ders başına 1
değil **konu başına 1** nesne döndürdüğü için 13 satırın 13'ü de `konu='matematik'`.

Canlı ölçüm (gerçek DB + gerçek Redis oturumu, mock yok):
```
konu_performanslari adedi : 13
konu adlari  : ['matematik'] x13
zayif_konular: ['matematik'] x11
guclu_konular: ['matematik'] x1
ayni etiket HEM zayif HEM guclu mu : True
```
Değişiklikten **önce** (tek kova) bu çıktı **yapısal olarak imkânsızdı**.
Yayılım: `api/advanced_reports.py:92,169,204,240,278` (5 uç) ·
`services/ogretmen_service.py:533,550` · `utils/pdf_generator.py:386-401`.

**P0-2 · `backend/api/advanced_reports.py:1528` — öğrenciye 11 birebir aynı öneri.**
Gerçek fonksiyon canlı veriyle koşuldu:
```
uretilen oneri adedi : 12
benzersiz aciklama   : 2
   konu_pekistirme | matematik konusunda temel kavramları pekiştirin   <- 11 KEZ
   ileri_seviye_gelistirme | matematik konusunda ileri seviye problemlere odaklanın
```
`services/ogretmen_service.py:550` → `', '.join(zayif[:3])` = `matematik, matematik, matematik`.

**P0-3 · `backend/services/ogretmen_service.py:210` — tek sınav 13 sınav gibi sayılıyor.**
`konu_performanslari[konu]['sinav_sayisi'] += 1` döngüsü artık 13 satır üzerinde dönüyor:
```
SID 5d2269fc: {'matematik': {'toplam_soru': 40, 'toplam_dogru': 5,  'sinav_sayisi': 13}}
SID f7e0b054: {'matematik': {'toplam_soru': 40, 'toplam_dogru': 7,  'sinav_sayisi': 14}}
```
ÖNCE: `sinav_sayisi = 1`. Öğretmen panelindeki sınav sayacı ~13× şişiyor.

**P1-1 · `backend/application/commands/sinav.py:830-843` — `GET /performance` alanı
ayırt edilemez.** Mapping 8 alan kopyalıyor, `topic_code`/`topic_name` **geçirmiyor**:
```
satir sayisi : 13 | topic_code/topic_name alani : YOK
ayirt edilemez (tam ayni) tuple : ('matematik', 4, 1, 1, 2) iki kez
```
**Neden gözden kaçtı:** GREEN fazının tüketici taraması
`grep -rln ... tests/ api/ core/ services/` idi — **`application/` dizini kapsam dışı**
kaldı ve geçişli tüketici `session_to_sinav_sonucu` hiç izlenmedi.

**P1-2 · Bu regresyonları hiçbir test yakalayamaz (yapısal körlük).**
```
$ grep -rn "session_to_sinav_sonucu" backend/tests --include=*.py
tests/fast/test_api_coverage_batch14.py:1010,1025,1055,1072  -> patch hedefi
tests/unit/test_api_coverage_final.py:455,470,485            -> AsyncMock(return_value=None)
tests/unit/test_services_remaining_batch1.py:869             -> AsyncMock(return_value=None)
```
4/4 referans mock. Tüketici paketleri değişiklikten sonra **58/58 YEŞİL**:
```
$ pytest tests/fast/test_advanced_reports_split.py tests/unit/test_ogretmen_api.py -q
======================= 58 passed, 31 warnings in 9.78s =======================
```

**P2-1 · Sıralama şartı %0 test kapsamında.**
M2 mutasyonu = `sort(...)` bloğu tamamen silindi:
```
$ B3V_MUT=M2 pytest <6 paket> -q
========== 631 passed, 32 skipped, 262 warnings in 119.51s ==========
```
**SIFIR FAIL.** Sıralamayı assert ettiğini söyleyen iki test
(`test_osym_exam_engine_split.py:511-517`, `test_osym_exam_konu_kirilimi.py:359`)
fikstür sırasının tesadüfen doğru olması sayesinde geçiyor — S238 sınıfı
(boş/tekil kümede kendiliğinden geçen bekçi).

**P2-2 · "Konu atanmamış" dalı ölü — ne üretimde ne testte koşuyor.**
```
SELECT count(*) FILTER (WHERE primary_topic_id IS NULL), count(*) FROM question_bank; -> 0|3922
question_bank LEFT JOIN topic_hierarchy ... WHERE primary_topic_id IS NOT NULL AND th.id IS NULL -> 0
```
M4 mutasyonu = tasarımın **açıkça yasakladığı** davranış (`topic_name or subject`,
yani ders adına düşme) enjekte edildi → `31 passed, 1 skipped`, **sıfır fail**.
Bekçi testi (`:398`) her koşumda çalışma anında SKIP oluyor. Frontend'teki
`s.topic_name || s.subject` fallback'i de (`ModernExamResultsPage.tsx:130`) hiç koşmuyor.

**P2-3 · Frontend canlıda değil — öğrenci göremiyor.**
```
$ docker image inspect kiro2-frontend --format '{{.Created}}' -> 2026-07-31T00:02:27Z
$ stat -c '%y' frontend/src/pages/ModernExamResultsPage.tsx  -> 2026-08-21 07:06:02 +0300
$ docker exec kiro2-frontend sh -c 'grep -o "topic" /usr/share/nginx/html/js/ModernExamResultsPage-BOz4h0fG.js | wc -l'
0
```
Bundle'daki tek `topic_name` eşleşmesi `js/DailyPlanPage-DbI-wRmO.js` — **ilgisiz chunk**.

**P3-1 · Sıralama tie-break'i Türkçe alfabetik değil, Unicode kod-noktası sırası.**
Eşit `total_questions=4` olan üç kova: `Olasılık → Polinomlar → Çarpanlara Ayırma`.
Python `str`: `'O'`(79) < `'P'`(80) < `'Ç'`(U+00C7=199). Türkçe alfabede Ç, C'den hemen
sonra gelir ve üçünün **başında** olmalıydı. Deterministik ama tasarım metniyle uyuşmuyor.

**P3-2 · İş commit'siz ölçüldü.** Bu belge yazılırken üretim değişikliği yalnız çalışma
ağacındaydı; canlıda koşan bayt dizisi hiçbir git referansıyla eşleşmiyordu. Bu yüzden
mutasyonlar **diske yazılamadı** (bkz. `verification.md` "GERİ ALIM BİR İDDİADIR" —
bu depoda commit'siz işi mutasyona sokmak iki kez veri kaybına yol açtı), bellek-içi
enjeksiyonla aşıldı. Bu commit ile kapanıyor.

---

## Kalite kapıları — ham durum

| Kapı | Sonuç | Not |
|---|---|---|
| `pytest` (6 backend paketi) | **628 passed / 31 skipped / 0 failed** | Baseline 627 + 1 yeni test |
| `tests/integration/test_osym_exam_konu_kirilimi.py` | 3 passed / 1 skipped | RED'de 2 failed idi |
| `tsc --noEmit` | **exit 0** | Keşifteki "4 mevcut TS hatası" notu **BAYAT** — canlı 0 |
| `npm run build` | **exit 0**, 1m48s | tek uyarı: önceden var olan >500 kB chunk |
| `vitest` (2 dosya) | 29 passed | yeni test kontrol kolu: değişiklik yokken **2/2 FAIL** |
| `eslint` | exit 1, **9 problem** | Kontrol kolu: HEAD'de **8 problem**, aynı küme, satırlar kaymış → **0 yeni bulgu** |
| `pre-commit` (ruff format) | Passed (2. koşumda sabit nokta) | 1. koşumda `test_osym_exam_engine_split.py` yeniden yazıldı, testler tekrar koşuldu |
| `pre-commit` (ruff lint) | **Failed, 15 hata** | **FANTOM** — kontrol kolu `git stash push` ile ölçüldü: HEAD sürümünde de `Found 15 errors.`, aynı ankrajlar (`test_sinav_api.py:19-110`), benim hunk'larım `:1099+` |
| `pre-commit` (mypy) | **Failed, 3 hata** | **FANTOM** — kontrol kolu: `git checkout HEAD --` sonrası aynı 3 `no-any-return`, aynı satırlar (+4/+6 kayma), üçü de `return await command_bus.execute(command)` — dokunmadığım satırlar |

---

## Kapsanmayanlar — sessiz kısaltma YOK

Her kalem için **neden** atlandığı yazılı.

1. **P0-1/2/3 ve P1-1 tüketici düzeltmeleri YAPILMADI.** Bu tur B3'ün motor+API+frontend
   sözleşmesini kapatmak üzere planlanmıştı; tüketici zinciri (adaptör → 5 rapor ucu →
   öğretmen servisi → PDF) 4+ dosya ve ayrı bir Root Cause + TDD turu gerektiriyor.
   `plan-before-execute.md` gereği onaysız girilmedi. **Açık iş olarak kayıtta.**

2. **Frontend container rebuild YAPILMADI.** `docker compose build frontend` +
   `up -d --no-deps frontend` gerekli. Görev kapsamı backend deploy + ölçümdü;
   frontend imajı 31 Tem tarihli. **A1'in "öğrenci konu kırılımını GÖRÜR" ayağı
   bu yüzden hâlâ açık.**

3. **`frontend/src/types/api.generated.ts` GÜNCELLENMEDİ.** Üç blokaj ölçüldü:
   (a) yeniden üretim zinciri `python backend/export_openapi_schema.py` ile başlıyor ve
   `backend/openapi.json`'ı **üzerine yazıyor** — o turun "backend'e dokunma" kısıtını
   ihlal ederdi; (b) mevcut `backend/openapi.json` **bayat** (`SubjectPerformanceResponse`
   içinde `topic_code` **yok**), üretilse bile alan gelmezdi; (c) `openapi-typescript`
   **kurulu değil** (`node_modules/openapi-typescript/package.json` → yok).
   **Etki ölçüldü:** dosyanın `frontend/src` içinde **0 importer**'ı var,
   `tsconfig.json` `exclude` listesinde, drift kapısı yok, son dokunuş 23 Nis 2026 →
   güncellememek hiçbir derleme/çalışma hatası üretmiyor. **Ayrı commit'e konu.**
   Gereken komut belgede: `npx openapi-typescript backend/openapi.json --output
   frontend/src/types/api.generated.ts --export-type --path-params-as-types`.

4. **MSW `handlers.ts` güncellenmedi.** Ölçüldü: 8 `osym-exam` handler'ı var ama
   `subject-performance` handler'ı **yok** → güncellenecek alan yok. Sözleşmeyi ölçen
   handler yeni test dosyasının içine (`server.use(...)`) kondu — böylece mock ölü kod
   olmuyor, doğrudan bir assert'i besliyor.

5. **`tests/integration/test_osym_exam_engine.py:722`** hâlâ 2'li tuple kuruyor; motor
   4 açıyor. Dosya `:55` ve `:844`'te `skipif(True)` ile **26/26 koşulsuz skip** —
   düzeltmem **doğrulanamaz** olurdu (skip'li test ne yeşil ne kırmızı verir).
   Un-skip edilirse `:734`'teki `assert len(...) > 0` düşecek. **Kayıt burada.**
   Aynı gerekçeyle `test_osym_exam_api.py:603-622` (31/31 skip) de dokunulmadı —
   oradaki keyword çağrısı zaten yeni sözleşmeyle uyumlu.

6. **L2 — e-posta doğrulama HÂLÂ YOK.** A1 altın yolunun 2. adımı
   ("e-postasını doğrular"). S241'de de açıktı, bu turda kapsam dışıydı.
   Blokaj: SMTP kimlik bilgisi (operatör) — görev #441.

7. **B3'ün "kırılım" tanımı hâlâ tek dersli veriyle sınandı.** DB'de
   `MATEMATIK 391 / KIMYA 3531` var, 8 oturumun 8'i de tek dersli. Çok-dersli bir
   sınavda `(subject, topic)` anahtarının davranışı **üretimde hiç koşmadı**
   (tasarım gereği doğru olması bekleniyor ama ölçülmedi).

8. **Sıralama ve NULL-kova için bekçi yazılmadı.** P2-1 ve P2-2 mutasyonla ölçüldü,
   boşluk **görünür bırakıldı** (`ders_kaydi.yaml` disiplini: kapatılamayan boşluk
   gizlenmez). Bekçi yazmak yeni fikstür + DB'de yapay NULL satır gerektirir.

---

## Açık işler (öncelik sırasıyla)

| # | İş | Şiddet | Dosya |
|---|---|---|---|
| 1 | `session_to_sinav_sonucu` → `KonuPerformansi.konu` = `topic_name`, zayıf/güçlü listeleri konu bazlı | **P0** | `core/osym_exam_engine.py:2168` |
| 2 | `sinav_sayisi` şişmesi — konu bazlı toplamada sınav sayacı ayrıştırılmalı | **P0** | `services/ogretmen_service.py:210` |
| 3 | `konu_data` mapping'ine `topic_code`/`topic_name` | **P1** | `application/commands/sinav.py:831` |
| 4 | `session_to_sinav_sonucu` için gerçek-veri testi (4/4 mock şu an) | **P1** | `tests/unit/test_api_coverage_final.py:455` |
| 5 | Frontend imaj rebuild + deploy | **P1** | `docker compose build frontend` |
| 6 | Sıralama bekçisi (M2 mutasyonu 631 testi geçiyor) | P2 | `tests/fast/test_osym_exam_engine_split.py:511` |
| 7 | Türkçe collation tie-break (`Ç` sona düşüyor) | P3 | `core/osym_exam_engine.py:1463` |
| 8 | `api.generated.ts` yeniden üretimi (ayrı commit) | P3 | `frontend/src/types/api.generated.ts` |

---

## Hijyen

Ölçüm için üretilen hiçbir geçici dosya kalmadı. Container'daki probe'lar
(`_head_engine.py`, `_verif_probe*.py`) `docker exec -u root ... rm -f` ile silindi;
kontrol kolu koşuldu (kalan `security_headers.py` / `install_verify_langchain.py` /
`verify_test_fixes.sh` **önceden vardı**). Host tarafındaki `.b3_*`, `_b3v_*` dosyaları
silindi. Üretim dosyalarının sha256'sı üç bağımsız çürütücü turunun sonunda da aynı:

```
backend/core/osym_exam_engine.py = 52a35eaf0ab4545927590541cb8948e8ad4d7810a3e4055dd72af54f8fd5ed59
backend/api/sinav.py             = b3dc00c9d893b72e31298f9990f1577c44886053ab4046f5c0b1fb1919e55343
```

Container içindeki kopyalar da **birebir aynı** (`MSYS_NO_PATHCONV=1 docker exec
kiro2-backend sha256sum /app/core/osym_exam_engine.py /app/api/sinav.py`) →
canlı ölçüm bayat imajı değil, bu baytları ölçtü. Bağımsız teyit: çalışan sürecin
kendi beyanı — `GET /openapi.json` içinde `SubjectPerformanceResponse` alanları
`topic_code` ve `topic_name` **içeriyor** (keşif fazında içermiyordu), 1119 yol.

`backend/semantic_cache.pkl` bu oturumun başındaki `git status`'ta zaten `M` idi —
bu işe ait değil, dokunulmadı, commit'e **alınmadı**.

---

## İlişkili

`docs/superpowers/specs/2026-08-21-b3-konu-kirilimi-design.md` (tasarım) ·
`docs/audits/2026-08-20_a1_altin_yol_olcum.md` (S241, A1 teslim ayağı) ·
`.claude/rules/audit-methodology.md` ("hacim bir vekil ölçümdür", "ölçüm aletini doğrula") ·
`.claude/rules/verification.md` ("doğrulama kapsamı = değişikliğin kapsamı" — P1-1'in
kök nedeni tam olarak bu kuralın `application/` dizinini atlaması)
