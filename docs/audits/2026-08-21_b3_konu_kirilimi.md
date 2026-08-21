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

> **[FAZ 2 EKI, ayni gun]** Yukaridaki iki uretim tuketicisi ARTIK duzeltildi ve
> mutasyonla civilendi; frontend imaji da yeniden kuruldu. Ama B3 yine kapanmadi ve
> bu paragraf **bilerek duzeltilmedi** (Faz 1'in yargisi tarihsel kayittir).
> Guncel yargi: **[F2-TL;DR](#f2-tldr--tek-cumlelik-yargi)**.

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

# FAZ 2 — 21 Ağu 2026, aynı gün ikinci tur

> Faz 1 bu belgenin yukarısında. **Faz 1'in hiçbir satırı silinmedi veya düzeltilmedi** —
> çürütülen iddiaları dahil, olduğu gibi duruyor. Aşağısı onun üstüne yazılan ölçümdür.
> Faz 1'in "Açık işler" tablosundaki 1/2/3 numaralı P0-P1 kalemleri bu turda kapandı,
> 5 ve 6 kısmen, geri kalanı hâlâ açık (§F2-5).

## F2-TL;DR — tek cümlelik yargı

**Faz 1'in ürettiği ve *beyan edilen* üç tüketici regresyonu ÖLÇÜLEREK kapandı ve iki
mutasyonla (M2/M4) çivilendi; B3 bir bütün olarak yine KAPANMADI:** aynı kardinalite
değişikliği (1 → 13) `advanced_reports.py`'de **üç yeni sessiz kusur** üretti (biri Faz 2'nin
kendi tüketici taramasında "etkilenmiyor" diye **yanlış sınıflandırıldı**), fix'in ikinci
yarısı (`sinav.py:844`) **bekçisiz** (M6 hayatta), frontend rebuild'i "konu sütunu"nu
getirirken **kimlik-doğrulanmış rotalarda sert yüklemede boş sayfa** kusurunu da canlıya
taşıdı, ve öğrenci ekranını besleyen yol bu turun **iki değişikliğinin de dışında**.

---

## F2-1 · Faz 1'in ürettiği regresyon — ÖNCE / SONRA (canlı sayılar)

Kanıt değeri şuradan gelir: **veri değişmedi, yalnız etiketleme satırı değişti.**
ÖNCE değerleri devir notundan alıntı DEĞİL — aynı canlı `subject_performances`
verisi üzerinde `konu=sp.subject` ile **karşı-olgusal olarak yeniden türetildi**;
böylece ÖNCE ve SONRA aynı oturumdan, aynı bayttan gelir.

Canlı oturum `62d6b582-1d1d-4fc6-b254-c9c22311c41b` (40 soru, **13 kova, 2 ders** —
Faz 1'in tek dersli oturumundan farklı olarak ders-arası çakışmayı da sınar):

| # | Tüketici (dosya:satır) | Ölçüm | ÖNCE | SONRA |
|---|---|---|---|---|
| a | `core/osym_exam_engine.py:2181` | `konu_performanslari.konu` benzersiz etiket | **2** / 13 kova | **13** / 13 |
| b | `api/advanced_reports.py:1391` | `zayıf ∩ güçlü` | `{kimya, matematik}` | **`[]`** |
| c | `api/advanced_reports.py:1517` | benzersiz öneri açıklaması (12 öneri) | **4** | **12** |
| d | `services/ogretmen_service.py:210` | `sinav_sayisi > 1` olanlar (TEK sınav) | `{kimya: 9, matematik: 4}` | **`{}`** |
| f | `api/sinav.py:891` (ana kazanç) | `subject-performance` satır / benzersiz `topic_code` / `sum(total_questions)` | — | 13 / 13 / **40** (bozulmadı) |

Faz 1'de **aynı ders hem "zayıf" hem "güçlü" listesindeydi**; şimdi 6 zayıf / 6 güçlü,
kesişim boş. (c) satırında ÖNCE çıktısının 12 önerisinin 9'u birebir
`"kimya konusunda temel kavramları pekiştirin"` idi; SONRA çıktısı
`"Organik Kimya konusunda temel kavramları pekiştirin"` /
`"Üslü ve Köklü Sayılar konusunda temel kavramları pekiştirin"` üretiyor —
kullanıcının **düz konu adı** kararının doğal Türkçe okunduğunun doğrudan kanıtı.
(c) ölçümü taklit değil: `_generate_personalized_recommendations` **gerçek fonksiyonu**
koşuldu, ÖNCE değeri de aynı gerçek fonksiyona faz-1 etiketleri beslenerek alındı.

**ÇOK-SINAVLI kontrol** (Faz 1'in "hiç ölçülmedi" dediği dal): (d)'nin döngüsü
3 tamamlanmış oturumla koşuldu — `Kimyasal Denge` 3, `Asitler ve Bazlar` 3,
`Periyodik` 3, `Organik Kimya` 2, `Atom Yapısı` 2 … ve konu bazında **gerçek**
oturum sayısıyla karşılaştırıldı: **uyuşmazlık yok**. Yanlış sayım üretilemedi.
`:210`'daki sayaç fonksiyondan dışarı çıkmadığı için salt-okunur `sys.settrace` ile
`return` frame'inden okundu — **kod değiştirilmedi**.

**`or sp.subject` fallback'i ÖLÇÜLDÜ ve HİÇ DEVREYE GİRMEDİ**: `topic_name IS None` = 0,
`topic_name == ''` = 0 (13/13 dolu). Erişilebilirliği ayrıca sınandı → §F2-4/B6.

### F2-1b · Faz 1 devir notunun bir premisi ÇÜRÜDÜ

Devir notu *"`GET /performance` ayırt edilemez 13 satır döndürüyor"* diyordu.
Ölçüldü: o uç `konu_performanslari` alanını **hiçbir zaman doldurmuyor**.

```
GET /api/v1/osym-exam/62d6b582-.../performance -> HTTP 200
konu_performanslari tipi: list   uzunluk: 0
zayif_konular: None   guclu_konular: None

sed -n '734,832p' backend/api/sinav.py | grep -c "konu_performanslari"  -> 0
backend/api/sinav.py:219  konu_performanslari: list[dict] = []   # varsayılan, hiç yazılmıyor
```

Yani 13 değil **0** satır döner ve bu değişiklikten önce de böyleydi
(`git status -uno -- backend/api/sinav.py` → boş, dosyaya dokunulmadı).
`sinav.py:841-844` fix'inin **gerçek taşıyıcısı POST /complete'tir**. İki bağımsız
oturumda doğrulandı: 13/13 ve 5/5 satırda `topic_code`/`topic_name` **dolu**, mevcut
8 alan korunmuş (10 anahtar) — sözleşme **eklemeli**.

---

## F2-2 · Kök neden — bu bir SÜREÇ kusuru, tek satırlık hata değil

Faz 1 `core/osym_exam_engine.py`'de gruplama anahtarını `(subject)` → `(subject, topic)`
yaptı ve tüketicileri taradı. Tarama **iki yapısal boşluk** bıraktı:

1. **`application/` dizini hiç taranmadı.** `application/commands/sinav.py:831`
   `konu_data` mapping'i yalnız 8 alan geçiriyordu; yeni `topic_code`/`topic_name`
   alanları o sınırda sessizce düşüyordu. Faz 1'in kendi "Kapsanmayanlar" bölümü
   bu boşluğun *sonucunu* (P1-1) kaydetti ama *sebebini* değil.
2. **Geçişli tüketici izlenmedi.** `session_to_sinav_sonucu` (adaptör) → `SinavSonucu`
   → 5 rapor ucu → öğretmen servisi → PDF zinciri, doğrudan çağrı grafiğinde
   `get_subject_performance`'ın **iki adım** ötesindeydi.

`verification.md#DOGRULAMA-KAPSAMI` zaten "kapsamı dizin yakınlığıyla değil **grep ile**
belirle" diyor; kural vardı, `application/` yine atlandı.

### DERS (ölçüldü) — `L-s241-kardinalite-degisiminde-SAYAN-tuketici`

> **Kardinalite değiştiren bir değişikliğin en kırılgan tüketicisi listeyi OKUYAN değil,
> listeyi SAYAN / etiketi ANAHTAR SANAN koddur.**

Neden okuyanlar güvenli: `for p in konu_performanslari: rapor_satiri(p)` 1 kova yerine
13 kova alınca **13 satır** üretir — istenen davranış (`pdf_generator.py:346-401` tam olarak
budur; `+= 1` / `len(` / `Counter` / `groupby` eşleşmesi **0**, bozulmadı). Neden sayanlar bozuluyor:

| Desen | Örnek | 1 → 13 olunca |
|---|---|---|
| **Sözlük anahtarı** | `d[konu]["sinav_sayisi"] += 1` | tek sınav 13 sınav sayılır |
| **Küme üyeliği** | `zayif` / `guclu` aynı etiketle dolar | aynı ders hem zayıf hem güçlü |
| **Bölen** | `toplam / len(liste)` | ağırlıksız ortalama **kayar** (ölçüldü: **+9,91 puan**) |
| **Kimlik varsayımı** | `f(etiket)` — `etiket`i ders kimliği sanar | eşleşme **0**'a düşer, ya da **yanlış satırı yer** |

Aranacak desenler (bu turda dördü de **gerçek kusur** buldu):
`+= 1` · `len(` · `Counter` · `groupby` · `set(` · `in normalize_tr(` · `X[etiket]` ·
`f(etiket)` — özellikle `f`'nin **başka bir kolona** eşitleme yaptığı yerler.

Bu ders `.claude/lessons/ders_kaydi.yaml`'a **kanıtla** eklendi; zorlayıcısı
`backend/tests/integration/test_osym_exam_konu_tuketiciler.py` (T1/T2/T3).
Kardeş ders: `L-s241-bir-katmanda-kapatilan-sizinti-digerini-kapatmaz` — aynı kusur
sınıfı bir katman yukarıda tekrarlıyor (§F2-4/B1, B2, B3).

---

## F2-3 · Mutasyon tablosu — M1…M6

**Yöntem:** mutasyon **diske yazılmadı** (iş commit'sizdi — `verification.md`
"commit'siz işi mutasyona sokma"). `sys.meta_path`'e takılan bir `MetaPathFinder`
kaynağı **bellekte** değiştirip `compile()` ile derledi; `.pyc` önbelleği `get_code`
override'ıyla tamamen atlandı. **Mutasyonun uygulandığı bağımsız ölçüldü:** yüklenmiş
modülün `dis.dis()` çıktısındaki işaret sayısı, mutasyonsuz kontrol koluyla
karşılaştırıldı (7/7'de fark + yükleyici `SourceFileLoader` → `_MutLoader`).
Ankraj tekilliği önceden doğrulandı (7/7 desen `occurrences=1`).

Kontrol kolu (mutasyonsuz temel): `-n 0` → **502 passed / 31 skipped / 0 failed**;
xdist → **501 / 32 / 0**. Eklentinin xdist worker'larına **taşındığı** ayrıca ölçüldü —
taşımasaydı tüm mutasyonlar sahte "hayatta kaldı" verirdi.

| # | Mutasyon | dosya:satır | Faz 1 | **Faz 2** | Öldüren test |
|---|---|---|---|---|---|
| M1 | gruplama anahtarı `(subject, topic)` → `subject` | `osym_exam_engine.py:1394` | öldürüldü | **öldürüldü** | 8 test (T1-T5 + kırılım×2 + split×1) — aşırı çivi |
| M2 | `subject_performances.sort(...)` bloğu SİLİNDİ | `:1463-1465` | 🔴 **HAYATTA** (631 passed, **0 fail**) | 🟢 **ÖLDÜ** | **T4 tek başına** — `test_kovalar_azalan_sirali_ve_tie_break_deterministik` |
| M2b | yalnız tie-break kaldırıldı (`key=(-total,)`) | `:1464` | ölçülmemişti | 🟢 **ÖLDÜ** | **T4 tek başına** — T4 sıralamayı *ve* tie-break'i ayrı ayrı çiviliyor |
| M3 | `"topic_code": topic_code` → `None` | `:1399` | öldürüldü | **öldürüldü** | 4 test |
| M4 | `topic_name or "Konu atanmamis"` → `or subject` | `:1400` | 🔴 **HAYATTA** (31 passed, **0 fail**; bekçisi her koşumda **SKIPPED**) | 🟢 **ÖLDÜ** | **T5 tek başına** — `test_adsiz_konu_gorunur_konu_atanmamis_kovasinda`, **SKIP yok** |
| M5 | `konu=sp.topic_name or sp.subject` → `sp.subject` (fix'in geri alımı) | `:2181` | — (fix yoktu) | 🟢 **ÖLDÜ** | T1 + T2 + T3, **üçü de bağımsız** |
| M6 | `"topic_name": p.topic_name` anahtarı SİLİNDİ | `application/commands/sinav.py:844` | — | 🔴 **HAYATTA KALDI** | **YOK — bekçisiz** |

**M2 ve M4, Faz 1'in "%0 test kapsamında" dediği iki dalın tam kendisiydi; Faz 2'de
ikisi de öldürülüyor** ve her biri **tek** bir testin yükünü taşıyor (ne aşırı-çivi,
ne kör nokta). M4'ün Faz 1'deki bekçisi (`test_osym_exam_konu_kirilimi.py:398`)
çalışma anında SKIP oluyordu; ölçüm gösterdi ki o sayaç **hiçbir zaman artamaz**
(§F2-4/B6) — yani **kalıcı olarak ölü** bir bekçiydi.

**M6 dürüstçe hayatta:** uydurma bekçi sunulmuyor. Kapsam dizin yakınlığıyla değil
grep ile belirlendi (`grep -rln "CompleteExamCommandHandler\|konu_data\|complete_exam\|topic_name" backend/tests`),
14 ek dosya koşuldu; kontrol ve M6 çıktıları **birebir aynı**
(12 failed / 2055 passed / 102 skipped — aynı 12 önceden var olan golden-flow hatası).
**DELTA = 0.** Bağımsız teyit: `grep -rln "konu_data\|CompleteExamCommandHandler" backend/tests` → **çıktı yok**.

---

## F2-4 · Çürütücü bulguları — SİLİNMEZ, kanıtıyla durur

İki bağımsız çürütücü mercek koştu; **ikisi de ana iddiayı çürüttü**. Aşağıdaki
bulgular bu belgeden **kaldırılmayacak**; kapananın yanına kapanış kanıtı yazılır.

### 🔴 B1 (HIGH, AÇIK) — `api/advanced_reports.py:474` + `:1167`: IRT toplulaştırması sıfıra düştü, **ve bir konu sessizce DERS istatistiğini yiyor**

`_get_subject_irt_aggregate(konu_perf.konu)` girdiyi `.upper()` yapıp
`QuestionMetadata.subject_area == canonical` ile sorguluyor. Etiket ders adıyken
eşleşiyordu; konu adıyken eşleşmiyor. Canlı ölçüm:

```
konu='Kimyasal Denge'     -> sample_size=   0  avg_diff=0.0000  avg_disc=1.0000
konu='Asitler ve Bazlar'  -> sample_size=   0  ...
konu='Organik Kimya'      -> sample_size=   0  ...
konu='Kimya'              -> sample_size=3531  avg_diff=0.0729   <-- !!!
DERS='kimya'              -> sample_size=3531  avg_diff=0.0729
DERS='matematik'          -> sample_size= 391  avg_diff=0.1258
```

Kök neden (etiket kümesi ile kolon kümesi örtüşmüyor):
`SELECT subject_area, count(*) FROM question_metadata GROUP BY 1;` → `KIMYA|3531`, `MATEMATIK|391`.

Bu **"hepsi bozuk"** değil, **tekdüzelik bozan** bir bozulma: `topic_hierarchy`'de
`KIM` kodlu, adı tam olarak `Kimya` olan bir **level-1** konu var ve
`'Kimya'.upper() == 'KIMYA' == subject_area`. Yani aynı yanıt içinde 12 konu varsayılan
sıfır, 1 konu tüm dersin istatistiğini taşıyor — sabit-varsayılan hâlinden **daha zor**
fark edilir. Yan etki: `ci_half` (`:482`) `sample_n=0` olduğu için `0.5` sabitine
çivileniyor; Redis'te `irt_aggregate:<KONU ADI>` biçiminde konu başına yeni anahtar açılıyor.

**Bu turda ölçülen ek (çürütücünün kaçırdığı):** çakışma **tek değil**. Level-1 konuların
tamamı sayıldı —

```
SELECT th.code, th.name_tr, th.level, count(qb.id)
FROM topic_hierarchy th LEFT JOIN question_bank qb ON qb.primary_topic_id = th.id
WHERE th.level = 1 GROUP BY 1,2,3 ORDER BY 4 DESC;
  KIM|Kimya|1|263     <- AKTİF çakışma ('KIMYA' == subject_area)
  MAT|Matematik|1|0   <- LATENT çakışma ('MATEMATIK' == subject_area), bugün 0 soru
```

`MAT|Matematik|1` de `subject_area='MATEMATIK'` ile çakışır, ama bugün **0 soru** taşıdığı
için latent. Bir soru o level-1 konuya atandığı gün ikinci çakışma **kendiliğinden** açılır.

**Neden düzeltilmedi:** doğru düzeltme `KonuPerformansi`'ye ders alanı eklemeyi
gerektiriyor (modelde ders alanı **yok**) — model/şema kararı, tek satır değil.
Bunu yakalayan test **yok**.

### 🔴 B2 (HIGH, AÇIK) — `api/advanced_reports.py:761` + `:869` + `:873`: Faz 2'nin kendi tüketici taraması "sayan kod yok" dedi, **SAYAN KOD VAR**

Faz 2'nin GREEN turundaki tüketici tablosu bu satırlar için *"çıktı 13 ayrık konu satırı;
**sayan/dedup eden kod yok**"* yazdı. Bağımsız grep:

```
backend/api/advanced_reports.py:761:    n = len(konu_zpd_analizleri)
backend/api/advanced_reports.py:869:                / len(konu_zpd_analizleri),
backend/api/advanced_reports.py:873:                / len(konu_zpd_analizleri),
```

`konu_zpd_analizleri` doğrudan `temel_sonuc.konu_performanslari` üzerinde dönerek
kuruluyor (`:698-700`) → uzunluğu = **kova sayısı**. Canlı etki:

```
ÖNCE  kova= 2  n=2   ortalama_basari=41.6667
SONRA kova=13  n=13  ortalama_basari=51.5751
fark  = +9.9084 puan   (ağırlıksız ortalama, kova sayısına BAĞLI)
SONRA kovalar: ['57.1','80.0','0.0','100.0','33.3','100.0','0.0','0.0','100.0','100.0','0.0','100.0','0.0']
```

`genel_zpd_profili.ortalama_mevcut_seviye` / `ortalama_optimal_zorluk` **+9,91 puan kaydı**.
HTTP 200, şema aynı — tamamen sessiz. Daha kötüsü: 13 kovanın **6'sı tek soruluk**,
%0/%100 uç değerleri üretip ağırlıksız ortalamayı domine ediyor.

**Bu bulgunun asıl değeri metodolojik:** Faz 2 kök nedeni "SAYAN tüketicileri ara"
diye teşhis etti, tarama tablosunu yazdı, **ve aynı turda bir `len()` çağrısını
gözden kaçırdı**. Ders yazmak, dersi uygulamak değildir; tarama sonucu bağımsız
bir mercekle **tekrar** ölçülmelidir.

### 🟠 B3 (MEDIUM, AÇIK) — `api/advanced_reports.py:933` + `:1051`: öğrenme stili ders dalları ÖLDÜ

```
SONRA(konu adı): {'matematik-dali': 0, 'turkce-dali': 0, 'else-dali': 13}
ÖNCE (ders adı): {'matematik-dali': 4, 'turkce-dali': 0, 'else-dali':  9}
```

`"matematik" in normalize_tr(konu_perf.konu)` ders adına göre yazılmış; konu adında o
alt dize yok → tüm kovalar `else` dalına düşüp `uyum_skoru = sum(vark_profili.values())/4`
alıyor. VARK-visual + Felder sequential_global dalları **hiç koşmuyor**. Sessiz:
istisna yok, şema değişmiyor, sadece skor tekdüzeleşiyor. Bunu yakalayan test **yok**.

### 🟠 B4 (MEDIUM, AÇIK) — `application/commands/sinav.py:844` BEKÇİSİZ

M6 hayatta (§F2-3). `POST /complete` çıktı sözleşmesini assert eden **hiçbir test yok**;
mevcut testlerin hiçbiri o dict'in anahtar kümesine bakmıyor. Kapatmak için gereken:
`konu_data` anahtar kümesini assert eden bir sözleşme testi. **Görev #506 kod olarak
kapandı, bekçi olarak AÇIK** → yeni görev #510.

### 🔴 B5 (P0, AÇIK — B3 kapsamının DIŞINDA, ama bu rebuild'le canlıya çıktı) — `frontend/src/App.tsx:348`: kimlik-doğrulanmış rotalarda **sert yüklemede boş sayfa**

Frontend rebuild'i "konu sütunu"nu getirdi (chunk `BOz4h0fG` → `C5Q5ku7s`, `topic` 0 → 3,
eski chunk container'da 0 dosya), **ama aynı imajla ikinci bir kusur da canlıya çıktı.**
İki bağımsız çürütücü, iki ayrı hesapla, aynı yolu (login formu → `page.goto(results)`)
tekrarladı:

```
opacity (10 x 400ms) : ["0","0","0","0","0","0","0","0","0","0"]
header               : ["Ders","Konu","Doğru","Yanlış","Boş","Başarı","Durum"]
rowCount = 8   distinctTopics = 8      <- tablo DOM'da VAR, GÖRÜNMEZ
uygulama-içi gezinme : opacity 0.148 -> 0.997 -> 1  (~320 ms)  <- SAĞLIKLI
```

**Kapsam ölçüldü** (frontend raporunun "tüm kimlik-doğrulanmış rotalar" ifadesi fazla geniş):
`/exams` sert yükleme → `["0"]×6` **BOZUK** · `/dashboard` sert yükleme → `["1"]×8` **SAĞLIKLI** ·
`/login` ve `/404` → opacity-0 element **yok**.

**Yeni olduğu kanıtlandı:** `git show f357e4647:frontend/src/App.tsx` (31 Tem imajının kaynağı)
→ results rotası `<ProtectedRoute>` ile sarılı, `PageTransition` **YOK**. Şimdiki
`App.tsx:348` → `element={<PageTransition>…}` (7 Ağu, `af99079c2`).

**Kök neden iddiası ÇÜRÜDÜ:** frontend raporu `PageTransition.tsx:57`
(`AnimatePresence mode="wait"` + `initial={opacity:0}`, ilk mount'ta `animate`
tetiklenmiyor) dedi. Kontrol kolu: **aynı bileşenle sarılı PUBLIC rota `/register`
opacity 1'de açılıyor** (`opacitySifirBuyukElement: []`). Tetikleyici `ProtectedRoute` +
`PageTransition` **bileşimi**; teşhis yeniden yapılmalı.

**Ayrıca frontend raporu kendi içinde çelişiyor:** `docs/audits/kanit/2026-08-21_b3-tablo-gorunur.png` tabloyu
GÖRÜNÜR gösteriyor, aynı rapor tarif ettiği yolda opacity 10/10 = 0 ölçtüğünü yazıyor.
İkisi ancak **farklı gezinme kiplerinden** gelebilir; ekran görüntüsünün hangi kipte
alındığı açıklanmamış → **provenans eksik**, o artefakt "öğrenci görüyor" kanıtı sayılmaz.

### 🟢 B6 (LOW, ÖLÇÜLDÜ-KAPANDI) — `osym_exam_engine.py:2181` `or sp.subject` **ÖLÜ KOD**

Kullanıcı kararının gerekçesi *"fallback `topic_name` None ise devreye girer"* ölçülünce
**erişilemez** çıktı:

```
UPDATE question_bank SET primary_topic_id = NULL
  -> ERROR: null value in column "primary_topic_id" ... violates not-null constraint
information_schema : question_bank.primary_topic_id  is_nullable = NO
                     topic_hierarchy.name_tr         is_nullable = NO
pg_constraint      : question_bank_primary_topic_id_fkey FK -> topic_hierarchy(id), convalidated = t
canlı              : name_tr NULL=0, name_tr ''=0, toplam=45; dangling primary_topic_id=0
```

Üstelik `:1400` zaten falsy'yi `"Konu atanmamis"`a çeviriyor. `or` operatörünün koruduğu
falsy sınıfın erişilebilir tek üyesi **boş dize** (`name_tr` üzerinde CHECK yok —
`pg_constraint`'te yalnız `check_osym_relevance` + `check_topic_level`).
T5 tam olarak bu yolu kullanıyor: işlem içinde `name_tr=''` olan sentetik bir
`topic_hierarchy` satırı INSERT edildi, FK geçerli, test koştu, `ROLLBACK` —
geri alım **bağımsız bir bağlantıyla** doğrulandı (`question_bank.primary_topic_id`
eski değerinde, sentetik satır `count = 0`).

**Yan bulgu:** kardeş dosyadaki `test_osym_exam_konu_kirilimi.py:398` bekçisi
çalışma anında SKIP oluyordu ("NULL konulu satır 0"). Ölçüm gösteriyor ki o sayaç
**hiçbir zaman artamaz** → o bekçi **kalıcı olarak ölü**, kendiliğinden koşacağı bir gün yok.
**Kalan boşluk (AÇIK):** iki farklı konu `name_tr=''` taşırsa ikisi de AYNI
`"Konu atanmamis"` etiketine çöker; T5 tek adsız konu ürettiği için bu **çakışmayı
çivilemiyor**.

### 🟢 B7 (LOW, ÖLÇÜLDÜ-KAPANDI) — `api/sinav.py:219`: `GET /performance` `konu_performanslari` HER ZAMAN `[]`

§F2-1b. Devir notunun premisi çürüdü; fix'in taşıyıcısı `POST /complete`.
Dosyaya dokunulmadı.

### 🟢 B8 (P0, **BU COMMIT'LE GİT AYAĞI KAPANDI**) — fix ne commit'liydi ne imajda

Çürütücü ölçtü, bağımsız tekrarlandı (4 katman, `MSYS_NO_PATHCONV=1` ile):

```
worktree            : grep -c "topic_name or sp.subject"  -> 1
git show HEAD:      : ...                                 -> 0   <- COMMIT'Lİ DEĞİLDİ
docker run IMAGE    : ...                                 -> 0   <- İMAJDA YOK
docker exec RUNNING : ...                                 -> 1   <- yalnız yazılabilir katman
```

Tek bir `docker compose up -d` fix'i **sessizce geri alırdı**. Bu commit git ayağını
kapatıyor; **imaj ayağı hâlâ AÇIK** (`docker compose build backend` yapılmadı) → §F2-5/1.

### 🟢 B9 (P1, **BU COMMIT'LE KAPANDI**) — çiviyi tutan test dosyası git'te takipli değildi

`git status --short -- backend/tests/` → `?? backend/tests/integration/test_osym_exam_konu_tuketiciler.py`.
CI hiç koşmaz, başka makinede yoktur, `git clean -fd` siler. "Çivilendi" iddiası
**tek makineye özeldi**. Bu commit'le takibe alındı.

### 🔴 B10 (P1, AÇIK) — bu turun iki değişikliği de **öğrenci ekranını beslemiyor**

```
frontend/src/pages/ModernExamResultsPage.tsx:93  -> /api/v1/osym-exam/{id}/subject-performance
                                            :131 -> topic: s.topic_name || s.subject
backend/api/sinav.py:891 -> get_subject_performance(...) ÇAĞRISINDAN DOĞRUDAN kuruluyor
```

Yani öğrenci tablosu `session_to_sinav_sonucu` (`:2181`) ve `CompleteExamCommandHandler`
`konu_data` (`:844`) yollarının **ikisini de atlıyor**. Öğrenci-görünür teslim tamamen
**Faz 1 commit'i `da59ef871` + frontend rebuild'inden** geliyor; bu turun iki değişikliği
**rapor/öğretmen katmanını** düzeltiyor ve o katmanın ölçülmüş bir UI tüketicisi yok.
M6'nın bekçisiz hayatta kalması aynı sonucu bağımsız olarak işaret ediyor.

### ⚪ B11 (bilgi, AÇIK — B3 kapsamı dışı) — `net_score` formülü: S241'in ölçümü iki hipotezi AYIRT ETMEMİŞ

Canlı complete yanıtı: `correct=22, wrong=18, net_score=22.0`. D − Y/4 = **17,5**.
Motor `net = doğru` kullanıyor (`api/sinav.py:786` yorumu: *"ÖSYM 2023+ 1/4 ceza kaldırıldı"*).
Bağımsız ikinci oturum: `D=7, Y=33, net_score=7.0` (D−Y/4 = −1,25 **değil**).
**S241'in "NET=1.0 = D−Y/4" ölçümü D=1, Y=0 ile yapılmış** — o noktada iki formül
**çakışır**, yani o ölçüm iki hipotezi hiç ayırt etmemiş. Hangi formülün doğru olduğu
bir **ürün kararı**; kod değiştirilmedi. `docs/audits/2026-08-20_a1_altin_yol_olcum.md`
buna göre okunmalı. *(Ölçüm dersi: tek gözlemde çakışan iki hipotezi ayırt eden bir
girdi seç — D=1,Y=0 hiçbir zaman ayırt edici değildi.)*

---

## F2-5 · Kapsanmayanlar — hâlâ açık olan her şey, NEDEN açık

| # | Açık kalem | Neden açık | Şiddet | Görev |
|---|---|---|---|---|
| 1 | **Backend imajı yeniden kurulmadı** (`docker compose build backend`) | Bu tur belge + commit turuydu; imaj kurulumu ayrı bir doğrulama zinciri (health + E2E, `Start-Sleep 90`) gerektirir. Fix şu an git'te **var**, imajda **yok**, çalışan container'da **var** → `docker compose up -d` geri alır. | **P0** | **#511** |
| 2 | **B1** — `_get_subject_irt_aggregate(konu_perf.konu)` | Doğru düzeltme `KonuPerformansi`'ye ders alanı eklemeyi gerektiriyor (modelde yok) → model/şema kararı, tek satır değil. `plan-before-execute.md` gereği onaysız girilmedi. Yakalayan test yok. | **P0** | **#512** |
| 3 | **B2** — `len(konu_zpd_analizleri)` ağırlıksız ortalaması | Doğru düzeltme bir **ağırlıklandırma kararı**dır (soru sayısına göre mi, kova sayısına göre mi?) — ürün kararı, mekanik fix değil. | **P0** | **#512** |
| 4 | **B3** — öğrenme stili ders dalları ölü | B1 ile aynı kök neden (etiketi ders kimliği sanmak); aynı model kararına bağlı, ayrı düzeltilirse aynı yere iki kez dokunulur. | P1 | **#512** |
| 5 | **B4/M6** — `sinav.py:844` bekçisiz | Kod düzeltmesi yapıldı; sözleşme testi yazılmadı. Yeni fikstür gerektirmiyor, ayrı bir TDD turu. **Uydurma bekçi sunulmadı.** | P1 | **#510** |
| 6 | **B5** — sert yüklemede boş sayfa | Frontend kaynağına dokunulmadı (görev kapsamı dışı) **ve** kök neden iddiası kontrol koluyla çürütüldü → teşhis yeniden yapılmalı. | **P0** | **#513** |
| 7 | **B10** — öğrenci ekranı bu turun değişikliklerinden beslenmiyor | Bir kusur değil, bir **kapsam ölçümü**: rapor/öğretmen katmanının UI tüketicisi ölçülmedi. | P1 | #512 kapsamında |
| 8 | **B6 kalanı** — iki boş-adlı konu aynı etikete çöker | T5 tek adsız konu üretiyor; çakışmayı çivilemek için ikinci sentetik satır gerekir. Boşluk **görünür bırakıldı** (`ders_kaydi.yaml` disiplini). | P2 | #508 (açık kalır) |
| 9 | **Kapı borcu** — `SKIP=ruff,mypy` (`da59ef871`) | **Kontrol kolu koşuldu:** `git show HEAD:` üzerinde **aynı 4 bulgu** çıkıyor (`sinav.py:242 PLR0912`, `:315 SIM117`, `:292/:315 mypy _bkt_semaphore`) → **önceden var olan borç**, bu turun 15 satırı değil. Eklenen satırlar için `ruff format` **Passed**. | P1 | #509 (açık kalır) |
| 10 | **L2 — e-posta doğrulama** | A1 altın yolunun 2. adımı, S241'de de açıktı. Blokaj: SMTP kimlik bilgisi (operatör). | **P0** (A1) | #441 |
| 11 | `frontend/src/types/api.generated.ts` · `test_osym_exam_engine.py:722` · `api/sinav.py` GET /performance doldurma | Faz 1'in Kapsanmayanlar 3/5'i; koşullar **değişmedi** (bayat `openapi.json`, `openapi-typescript` kurulu değil, 26/26 koşulsuz skip → düzeltme doğrulanamaz olurdu). | P3 | — |
| 12 | **B11** — `net_score` formülü | Ürün kararı; kod değiştirilmedi. | bilgi | — |

---

## F2-6 · Hijyen — kanıt, iddia değil

**Ölçüm turlarında üretim kodu DEĞİŞMEDİ.** Mutasyon ve çürütme turlarının başında ve
sonunda sha256 birebir aynı:

```
9b70d0b2a3b6b2a53aeba824c5dc1cd0a887f3d2ada37b7036b466def6e54690  backend/core/osym_exam_engine.py
ec7047c6c3648d8f176da06aa73e84dd202856a7606f5e7563bd80bd9cc1e981  backend/application/commands/sinav.py
```

- Diske hiç mutasyon yazılmadı; yine de üç bağımsız kontrol yapıldı: `git status -uno`
  başta = sonda · sha256 eşleşmesi · diskteki 7/7 **orijinal ankraj** yeniden sayıldı (hepsi `1`).
- Geçici probe'lar silindi ve **doğrulandı**: host `_b3*.py` / `_b3v_mut.py` / `_cv_*.py` →
  `git status` boş; container `/tmp/_b3*` ilk `rm`'de *"Operation not permitted"* verdi
  (dosyalar root'a ait, container non-root koşuyor) → `docker exec -u root` ile silindi,
  `ls` ile doğrulandı. **Silme iddiası doğrulanmasaydı container'da 3 artık kalacaktı.**
- Probe'un açtığı Redis anahtarları (`irt_aggregate:FONKSIYONLAR`, `:MUTLAK DEĞER`,
  `:KONU ATANMAMIS` …) `DEL` ile temizlendi → kalan yalnız önceden var olan `irt_aggregate:MATEMATIK`.
- **Benim olmayan artık — silinmedi, bildiriliyor:** `backend/.b3_read.py` (takipsiz,
  07:45, bu turlardan önce oluşmuş). Cerrahi müdahale kuralı.
- **DB'de kasıtlı bırakılanlar** (A1'in canlıda çalıştığının kalıcı kanıtı):
  3 test öğrencisi (`b3olcum…@ornektest.com`, `cv1787300428@…`, `cv1787300216@…`)
  + 4 tamamlanmış sınav oturumu.
- `backend/semantic_cache.pkl` bu işe ait **değil** — hiçbir turda dokunulmadı,
  commit'e **alınmadı**.

### Ölçüm aleti arızaları (tekrar edenler için)

| Arıza | Belirti | Çözüm |
|---|---|---|
| Git Bash yol dönüşümü | `docker exec … /app/x` → `C:/Program Files/Git/app/x`, "dosya yok" → **"fix kurulmamış" yanlış teşhisi** | `MSYS_NO_PATHCONV=1` |
| Container PYTHONPATH | `docker exec -w /app python x.py` → `ModuleNotFoundError: No module named 'core'` | `-e PYTHONPATH=/app` |
| Türkçe SQL inline | `psql -c "…"` → `invalid byte sequence for encoding "UTF8": 0xd0 0x45` | `-f dosya.sql` |
| `pytest -p no:xdist` | `unrecognized arguments: -n --dist=loadscope` (`pytest.ini` addopts) | tek süreç için `-n 0` |
| asyncpg bind tipi | `AmbiguousParameterError` — aynı bind hem `varchar` kolona hem karşılaştırmaya girerse | ayrı kolon (`qc.id`) kullan |
| Kolon adı tahmini | `topic_hierarchy.topic_name` → `column does not exist` | gerçek adlar `code` / `name_tr` |
| Servis singleton adı | `services.ogretmen_service.ogretmen_service` → yok | Türkçe: `ogretmen_servisi` |
| Probe yolu | prob `get_subject_performance`'ı **modül düzeyinde** aradı (aslında `OSYMExamEngine` metodu) → `pytest_sessionstart` INTERNALERROR, `grep` **boş çıktı** | "çıktı yok = sorun yok" **DEĞİL** — ham çıktı okundu; yalnız grep'e bakılsaydı 5 mutasyonda prob hiç koşmamış olacaktı |

---
## İlişkili

`docs/superpowers/specs/2026-08-21-b3-konu-kirilimi-design.md` (tasarım) ·
`docs/audits/2026-08-20_a1_altin_yol_olcum.md` (S241, A1 teslim ayağı) ·
`.claude/rules/audit-methodology.md` ("hacim bir vekil ölçümdür", "ölçüm aletini doğrula") ·
`.claude/rules/verification.md` ("doğrulama kapsamı = değişikliğin kapsamı" — P1-1'in
kök nedeni tam olarak bu kuralın `application/` dizinini atlaması)

---

# FAZ 3 — konu kimliği modele, metrik kovalama-değişmez (S244, 21 Ağu 2026)

**Kapsam:** #511 (imaj) · #512 (model + 3 sessiz kusur) · #510 (M6 bekçisi)
**Tasarım:** `docs/superpowers/specs/2026-08-21-b3-faz3-design.md`
**Plan:** `docs/superpowers/plans/2026-08-21-b3-faz3-uygulama.md`
**Aralık:** `ee5ef3c03..a9c826dee` (8 commit)

## 1. Kök neden — bu sefer modelde

FAZ 2 doğrudan tüketicileri onardı. Bir katman yukarıda üç kusur kaldı ve üçü de
tek bir yapısal eksiğe bağlıydı:

> `KonuPerformansi` (`models/exam.py:83`) yalnız `konu: str` taşıyordu.
> **Ders kimliği için alan yoktu.** Ders kimliğine ihtiyacı olan her tüketici
> `konu` dizesini ders sanmak zorunda kaldı.

`ders: str | None` + `konu_kodu: str | None` eklendi (sona, varsayılanlı —
`SubjectPerformance`'taki aynı disiplin). Üretici `session_to_sinav_sonucu`
`ders=sp.subject, konu_kodu=sp.topic_code` yazıyor.

**`topic_hierarchy.subject_area` KULLANILAMADI** — ölçüldü, o satırlarda NULL
(`MAT|Matematik||1`). Ders kimliği yalnız `question_metadata` üzerinden gelir.

## 2. Üç kusur — ÖNCE/SONRA (canlı DB, port 5434, db `kiro2`)

### (a) IRT agregasyonu — `advanced_reports.py:474`, `:1149`

`_get_subject_irt_aggregate(konu_perf.konu)` içeride `.upper()` yapıp
`WHERE question_metadata.subject_area = <upper>` sorguluyordu.

```
"Kimyasal Denge" -> "KIMYASAL DENGE" ->    0 satir   (konunun gercegi 1262)
"Kimya"          -> "KIMYA"          -> 3531 satir   (konunun gercegi  263)
```

İkincisi tehlikeli olan: **sıfır dönmek gürültülü, YANLIŞ dersin verisini
dönmek sessizdir.** Sebep `topic_hierarchy`de level-1 KONU adının DERS adıyla
çakışması (`KIM|Kimya`, `MAT|Matematik`). `topic_hierarchy.code` ASCII ve
çakışmasız — ayırt edici anahtar odur.

Fix: `_get_irt_aggregate(*, topic_code, ders)`. Kod varsa `topic_hierarchy` JOIN,
yoksa derse düşer. **Cache anahtarı ayrışır** (`irt_aggregate:topic:*` /
`:subject:*`) — tek şema ikisini karıştırırdı.

Eski fonksiyon **silinmedi**: `tests/fast/test_advanced_reports_split.py` onu
çağırıp #485 split JOIN yapısını çiviliyor. Nihai incelemenin Important bulgusu
üzerine tanım yerine "URETIMDE OLU" işareti kondu.

### (b) ZPD ortalaması — `:761` (real) + `:869/873` (mock)

Toplam bölü kova sayısı biçimi kova sayısına bağlıydı; kardinalite 1 → 13 olunca
ortalama sessizce kaydı (**+9,91 puan**, S243 ölçümü). `_agirlikli_ortalama`
soru sayısıyla ağırlıklandırır.

**Asıl kazanç bugünkü sapmanın düzelmesi değil:** ağırlıklı biçim
**kovalamadan bağımsızdır** — aynı veri hangi kovalamayla verilirse verilsin
aynı sonucu üretir, yani bir SONRAKİ kardinalite değişiminde de kaymaz.
S243'ün deftere yazdığı dersin yapısal panzehiri budur.

### (c) Ders dalı — `:934` (real) + `:1051` (mock)

Dize eşleşmesiyle dallanıyordu (`normalize_tr(kp.konu)` içinde "matematik"
aranıyordu). İki sebeple kırılgandı: `konu` artık konu adı taşıyor (dal ölü), ve
`normalize_tr` bir subject identifier'a uygulanamaz (`case-convention.md`
yasağı, Türkçe locale I → ı).

`_ders_uyum_skoru(ders, vark, felder)` çıkarıldı; `subject_key(ders)` ile
dallanır. **Kardeş sessiz kusur** de kapandı: kanon küme ölçüldü
`{KIMYA, MATEMATIK}` — ASCII. Eski koddaki Türkçe harfli dize kanonla hiçbir
zaman eşleşemezdi; ASCII `turkce` yapıldı.

## 3. #510 — M6 öldü

`POST /osym-exam/{sid}/complete` mapping'i FAZ 2'de `topic_code`/`topic_name`
kazanmıştı ama **bekçisi yoktu**: M6 mutasyonu 2069 testte DELTA=0 veriyordu.

T7 eklendi (gerçek Postgres, `AsyncMock` YOK — FAZ 2'nin kök nedeni mock
körlüğüydü). Test yeşil doğduğu için RED kanıtı **mutasyonla** üretildi:
iki alan mapping'den silinince T7 **tek başına** FAIL veriyor.

`None` olmayan `topic_code`'ların benzersizliği assert edilir; `None`'lar
**dışlanır** — ölçüldü `primary_topic_id IS NULL = 0/3922`, dışlamasak assert
boş kümede kendiliğinden geçerdi (S238'de iki bekçi tam bu yüzden XPASS
vermişti).

## 4. #511 — git == imaj (kabul kriteri)

```
ONCE  : imajda topic_code sinav.py=0  osym_exam_engine.py=0   git=1 / 5
SONRA : md5 esitligi 5/5 dosyada OK
        (sinav.py, osym_exam_engine.py, advanced_reports.py,
         models/exam.py, core/turkish_nlp_utils.py)
        imajda _ders_uyum_skoru=3, _agirlikli_ortalama=5, _get_irt_aggregate=3
```

İki derleme yapıldı: ilki sigorta (imaj 3 gün bayattı, derlemenin yeşil olduğunu
kanıtladı), ikincisi kriteri kapattı.

## 5. Canlı E2E (yeni imaj, beta-practice yolu)

```
kayit 201, giris 200, beta-practice 200, start 200, complete 200
  kova = 8   topic_code dolu = 8/8   benzersiz = 8
  ornek: {"subject":"kimya", ..., "topic_code":"KIM.DEN", "topic_name":...}
subject-performance 200  satir=8  farkli topic_code=8
zpd 200, irt-analysis 200, learning-style 200, osym-ets 200  ->  5XX YOK
```

**UYARI:** `create` (tam TYT) **400** verdi: *"Yeterli soru bulunamadı.
Gerekli: 120, Mevcut: 33"*. Bu B3 ile ilgisiz bir **havuz kapasitesi** sınırı —
kapıda 3.560 soru var ama tam TYT dağılımını karşılayacak ders/konu bileşimi
yok. Ayrı açık iş.

## 6. Kapı

```
1292 passed / 1 skipped / 0 failed
  (test_konu_kimligi, test_irt_aggregate_topic_split, test_advanced_reports_split,
   test_advanced_reports_schema_parity, test_exam_curriculum_models,
   test_osym_exam_konu_tuketiciler T1-T7, test_osym_exam_konu_kirilimi)
```

## 7. DÜRÜST SINIRLAR (iddia EDİLMEYEN şeyler)

| # | Sınır | Neden |
|---|---|---|
| 1 | **(a) IRT kusuru CANLIDA DEĞİLDİ** | Ölçüldü: `config/mock_endpoint_flags.json` — 5/5 `advanced_reports.*` bayrağı `false`. İki çağrı yeri de `_real` yolda, yani **uykuda**. Gerçek kusur (operatör bayrağı çevirince sessizce aktifleşir) ama *"bugün öğrenciyi bozuyor"* aşırı iddia olurdu. Kanıt uçtan değil **doğrudan SQL**'den alındı. |
| 2 | **TURKCE dalı E2E ile doğrulanamadı** | Canlı DB'de `TURKCE` satırı yok (kanon küme `{KIMYA, MATEMATIK}`). Sentetik birim testle çivili. |
| 3 | **`sample_size` konu bazında KÜÇÜLDÜ** | Beklenen ve doğru: CI yarı-genişliği `0.5/sqrt(n)` ile büyür. Gerileme değil. |
| 4 | **+9,91 rakamı bu turda yeniden ölçülmedi** | S243'ten devralındı. Bu turda ölçülen: ağırlıklı biçimin kovalama-değişmez olduğu (testle). |
| 5 | **Bayat-mock assert'i mutasyonla kanıtlanmadı** | `await_count > 0` assert'i eklendi ama ankrajı eski ada geri alan mutasyon o assert'e **ULAŞMADAN** sqlite hatasıyla düştü. Bu ortamda yakalayan şey assert değil, DB'nin boş olması. |
| 6 | **Gerçek yolun ders dalı çivilenmedi** | `_get_hibrit_..._real` çağrı yeri kapsanmadı (`learning_style_service` mock'lamamak için). Bugün ölü; bayrak çevrilirse açık. |
| 7 | **`get_subject_morphology_factor` ölü** | `advanced_reports.py:561` — `hasattr` guard'ı daima `False`, `morfoloji_faktoru` hep `0.1`. Önceden var olan, bu turun sorumluluğu değil; nihai incelemede tespit edildi. |

## 8. Çürütülen iddialar (dürüst kayıt — üçü de PLANI YAZANIN)

1. **"(c) dalı B3 öncesi de ölüydü"** — tasarım turunda kuruldu, **ölçüm
   çürüttü**: `osym_exam_engine.py:1387` `subject_area.lower()` üretiyor, yani
   `normalize_tr("matematik")` eşitlik veriyordu. Dal **canlıydı**, B3 öldürdü.
2. **Planın kovalama-değişmezlik test verisi DEJENEREYDİ** — implementer
   aritmetiği kontrol edince yakaladı: ağırlıksız ortalamalar **6.0 vs 6.0**,
   yani `test_kovalama_degismez` **hatalı implementasyona karşı da geçerdi** ve
   mutasyon gereksinimi tatmin edilemezdi. Bağımsız hakem doğruladı. Veri
   asimetrik yapıldı (6.0 vs 7.0).
3. **`normalize_tr` başka yerde kullanılıyor sanılmıştı** — plan "koru" diyordu;
   ölçüldü, üç kullanımın üçü de değiştirilen bloklardaydı, import ölü kaldı.

## 9. Kapatılan test-kalitesi kusurları (3 ayrı çivi)

Bu turda **üç dişsiz assert** bulundu ve değiştirildi — üçü de kendi bekçisini
boşa çıkarıyordu:

1. T6'nın son assert'i önceki ikisi tarafından **kapsanıyordu** → `konu`
   DEĞİŞKEN / `ders` SABİT invaryantıyla değiştirildi.
2. `test_konu_adi_ders_dalini_secmez` topic adını **hiç geçirmiyordu**;
   inceleyici çağrı yerini `.ders` → `.konu` mutasyonuyla test etti:
   **7 passed, 0 failed**. Çağrı-yeri düzeyinde gerçek testle değiştirildi.
3. `test_advanced_reports_schema_parity.py` **bayat mock ankrajı** — taşınan
   fonksiyonun eski adına patch yapıyordu, sessizce hiçbir şeyi yakalamıyordu.

Nihai inceleme **dördüncüyü aradı, bulamadı**.

## 10. Orkestrasyon dersi (bu tur ısırdı)

Paralel ajanlarla çalışırken **depoda tek git index vardır.** İki ajan aynı anda
`git add` yaparsa biri diğerinin işini kendi commit'ine süpürebilir. Task 5
bunu fark edip pathspec'li `git commit -F msg -- <dosya>` kullandı; `git add .`
yapmamak **yeterli koruma değil**, commit'in kendisi pathspec istiyor.

İkinci tuzak: **dosya-değiştiren inceleyici, aynı dosyadaki implementer ile
paralel koşturulmamalı.** Task 2'nin spec inceleyicisi `cp` yedek/geri-yükleme
ile mutasyon koştururken Task 3 aynı dosyayı düzenliyordu; olası veri kaybı
penceresi oluştu (bütünlük sonradan doğrulandı, kayıp yok). Sonraki incelemeler
**salt-okunur** ve `git show <sha>:<yol>` üzerinden yapıldı.

## 11. Açık kalan

| İş | Durum |
|---|---|
| **#513** sert-yüklemede boş sayfa (frontend) | ~~kapsam dışıydı, açık~~ → **ÖLÇÜLDÜ, TEKRARLANMIYOR** (bkz. EK, bu dokümanın sonu) |
| **L2** e-posta doğrulama | SMTP bloklu (#441) |
| **#509** kapı borcu | +1: `test_advanced_reports_schema_parity.py` 5x E402 (kontrol koluyla önceden-var-olan ölçüldü, `SKIP=ruff` kullanıldı) |
| Tam TYT `create` 400 | havuz kapasitesi (120 gerekli / 33 mevcut) — yeni açık iş |
| `_get_subject_irt_aggregate` ölü ikiz | işaretlendi; silinmesi ayrı iş (bekçisi taşınmalı) |

---

# EK — #513 ÖLÇÜLDÜ: TEKRARLANMIYOR (S244 kapanış turu, 21 Ağu 2026)

S243 devir notu: *"`App.tsx:348` — sert yüklemede **boş sayfa** (`/exams` bozuk,
`/dashboard` sağlıklı); rebuild'le ilk kez canlıda"*. Kök neden iddiası
(`PageTransition:57`) o turda zaten kontrol koluyla çürütülmüştü (`/register`
sağlıklı).

## 1. Ankraj ile proza ÇELİŞİYOR (ölçüldü)

```
App.tsx:348  ->  path="/exam/:sinavId/results"   (ExamResultsPage, ogrenci+admin)
App.tsx:356  ->  path="/exams"                   (ExamHistoryPage, ogrenci)
```

Devir notunun **ankrajı** `:348` = `/exam/:sinavId/results`; **prozası** `/exams`
diyor. Bunlar farklı rotalar. `App.tsx` S243'ten beri **hiç değişmedi**
(`frontend/src`'ye 20 Ağu'dan beri dokunan tek commit `da59ef871`, o da B3 FAZ 1).

## 2. Sarmal kök neden OLAMAZ — yapısal kontrol kolu

Sağlıklı diye raporlanan ile bozuk diye raporlanan rota **birebir aynı bileşimi**
kullanıyor:

```tsx
/dashboard : <PageTransition><ProtectedRoute requiredRoles={['ogrenci']}><StudentDashboardPage/>…
/exams     : <PageTransition><ProtectedRoute requiredRoles={['ogrenci']}><ExamHistoryPage/>…
```

Aynı sarmal, aynı guard, aynı rol, ikisi de `lazy()`. `/register` kontrol kolundan
daha güçlü bir kontrol: **aynı bileşim hem sağlıklı hem bozuk olamaz.**

## 3. Canlı tarayıcı ölçümü (Playwright, kimlik doğrulanmış `ogrenci`)

Hesap `p513@kiro2-e2e.dev` (rol `ogrenci`), yeni kurulan backend imajı,
frontend imajı 21 Ağu 07:20 UTC.

| Test | Sonuç |
|---|---|
| `/login` → giriş | 200, "İçerdesin." |
| **`/exams` SERT YÜKLEME** | **tam render** — kenar çubuğu, kullanıcı kimliği, "Sınav Geçmişi", 4 istatistik kartı, sekmeler, "Yeni Sınav Başlat". **0 konsol hatası** |
| **`/exam/{sid}/results` SERT YÜKLEME** | **tam render** — "Sınav Sonuçları", istatistik kartları, "Konu Bazlı Performans". **0 konsol hatası** |
| Konu kırılımı tablosu | **9 satır**, `Ders \| Konu` iki sütun |
| Backend `/subject-performance` | **200, 9 satır** (`KIM.DEN` / "Kimyasal Denge" …) |

**Ekran == backend: 9 == 9.** Örnek satırlar: `kimya \| Kimyasal Denge`,
`matematik \| Polinomlar`, `matematik \| Çarpanlara Ayırma`,
`kimya \| Çözeltiler ve Karışımlar`.

Bu, B3'ün kullanıcı-görünür kabul kriteridir ve **sert yüklemede karşılanıyor**.

## 4. 🔴 KENDİ ÖLÇÜM ALETİM YANILDI — dürüst kayıt

Ara adımda "Konu Bazlı Performans tablosu BOŞ" diye bir bulgu üretildi:
erişilebilirlik snapshot'ı `<table>` altında iki boş `rowgroup` gösteriyordu.

**Bu bir alet artefaktıydı.** Snapshot `depth: 7` ile alınmıştı; tablo ağaçta
daha derinde olduğu için çocukları kesilmişti. Tabloyu hedefleyen (`target:
"table"`, derinlik sınırsız) ikinci ölçüm 9 satırın tamamını gösterdi.

Ayırt edici sinyal, bulgu raporlanmadan önce yakalandı: `<TableHead>` **statik**
hücreler içeriyor (`Ders`, `Konu`, `Doğru`, …) ve statik hücrelerin boş çıkması
veri kaynaklı bir kusurla açıklanamaz — yalnız görüntülemenin kesildiğiyle
açıklanabilir.

Kural (`audit-methodology.md` "ölçüm aletini doğrula"): `depth` bir
**görüntüleme** parametresidir ama çıktısı bir **ölçüm** gibi okunur; kesilmiş
`rowgroup` gerçekten boş bir tablodan ayırt edilemez. Bu turda az kalsın fantom
üretiliyordu.

## 5. Sonuç ve DÜRÜST SINIR

**#513 bugünkü yığında TEKRARLANMIYOR.** İki rota da sert yüklemede sağlıklı,
konu kırılımı görünüyor, konsol temiz.

**"Tekrarlanmıyor" ≠ "hiç yoktu".** Ölçüm koşulları:
- tek hesap (`ogrenci`), tek tarayıcı oturumu
- **backend imajı bugün İKİ KEZ yeniden kuruldu** (#511) — S243 bayat 18 Ağu
  imajıyla gözlem yapıyordu
- frontend imajı değişmedi (21 Ağu 07:20)

En olası açıklama: gözlenen davranış bayat backend imajından kaynaklanıyordu ve
#511 ile yan etki olarak düzeldi. **Bu KANITLANMADI** — eski imaj geri kurulup
karşı-olgusal test yapılmadı. Yapılırsa #513 "fantom" yerine "şu commit'te
düzeldi" diye kapanır.

Kapanış türü: **ÖLÇÜLDÜ → TEKRARLANMIYOR** (kod değişikliği YAPILMADI).
