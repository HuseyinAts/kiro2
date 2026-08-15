## Session Handoff — 2026-08-15 (S214)

**Branch:** `feature/self-evolution-optimization` · **HEAD:** `9488196cf` · **Push:** ✅ hepsi pushed
**Ana iş:** #485 — `question_bank` 69-alan split'inin JOIN göçü (S210/S211/S212/S213 devamı)
**Uncommitted:** bu işin dosyaları **temiz**. (Ağaçtaki 3390 kirli dosya = Gemini S210 devri, ayrı görev.)

### İlerleme — ÖLÇÜLDÜ, aritmetik değil

**Kalan: 14 erişim / 9 dosya** (S214 sonu; tur başında 21/11'di, 7 düzeltildi).
Alet kontrol koluyla doğrulandı: `HEAD~1`'de advanced_reports.py→**4** (beklenen).

> ⚠️ **ALETİN KÖR NOKTASI (S214'te ölçüldü).** Sayaç yalnız **sınıf düzeyi**
> `QuestionBankItem.<alan>` sayar. `mnemonic_service`'te asıl riski taşıyan
> kusur **örnek düzeyiydi** (`select(QuestionBankItem)` → sonra `question.alan`
> okuma → `MissingGreenlet`) ve sayaçta **hiç görünmedi**. Yani "kalan 14"
> işin ALT SINIRI. Her dosyada ayrıca `grep 'select(QuestionBankItem)'` koş.
>
> Kalan 9 dosyanın entity-seçim sayısı **önceden ölçüldü** (eager-load gerekecek):
> `api/osym_routes.py` **2** · `services/offline_sync_service.py` **2** ·
> `services/placement_assessment_service.py` **1** · `core/irt_daemon.py` **1** ·
> diğer 5 dosya **0**.

Ölçüm komutu (delegeli alan listesini kolonlardan türetir, ezbere liste yok):
```
python -c "import re,sys;sys.path.insert(0,'.');from models.question_bank import QuestionContent,QuestionMetadata,QuestionStatistics;
d={c.name for t in (QuestionContent,QuestionMetadata,QuestionStatistics) for c in t.__table__.columns if c.name!='id'};
from pathlib import Path;[print(len([m for m in re.finditer(r'QuestionBankItem\.(\w+)',p.read_text(encoding='utf-8')) if m.group(1) in d]),p) for x in ('services','api','core','app','tasks') for p in Path(x).rglob('*.py') if '__pycache__' not in p.parts and any(m.group(1) in d for m in re.finditer(r'QuestionBankItem\.(\w+)',p.read_text(encoding='utf-8',errors='ignore')))]"
```

| # | Dosya | Sınıf düzeyi | Entity seçimi |
|---|---|---|---|
| 1 | `api/osym_routes.py` | 2 | **2** |
| 2 | `services/placement_assessment_service.py` | 2 | **1** |
| 3 | `core/irt_daemon.py` | 2 | **1** |
| 4 | `services/difficulty_classification_service.py` · `tasks/mega_feature_tasks.py` | 2 ×2 | 0 |
| 5 | `services/offline_sync_service.py` | 1 | **2** |
| 6 | `services/parent_service.py` · `api/placement_assessment_api.py` · `core/osym_exam_engine.py` | 1 ×3 | 0 |

### Yapılanlar

| Commit | İş |
|---|---|
| `8713ab8e3` + `3c2580332` | **`backend/services/mnemonic_service.py` (7/17)** — 3/3 + **eager-load**. Seride iki kusur sınıfını birlikte taşıyan ilk dosya: sınıf düzeyi 3 JOIN, ARTI `generate_mnemonic` entity seçip `question.question_text`/`.correct_answer`/`.subject_area` okuyordu → `selectinload(content, metadata_info)`. + `tests/fast/test_mnemonic_service_split.py` (10 test, **8/8 mutasyon**). İkinci commit: mutasyon 2 testimin kusurunu buldu (aşağıda). |
| `9488196cf` | **`backend/api/advanced_reports.py` (6/17)** — 4/4. `_get_subject_irt_aggregate` **kurulma anında** patlıyordu (S212 A-sınıfı: SELECT listesinde yalnız `QuestionStatistics` kolonları → explicit `select_from` şart). irt_* → QuestionStatistics, subject_area → QuestionMetadata. Eager-load **N/A (ölçüldü)**. + `tests/fast/test_advanced_reports_split.py` (8 test, **6/6 mutasyon öldürüldü**) |
| `f661316fe` | **`backend/api/curator.py` (4/17)** — 10/10. `get_queue` WHERE'inde 3 ayrı JOIN (`QuestionStatistics` status+difficulty, `QuestionMetadata` subject, `QuestionContent` image_url). **3 entity-seçim sitesine eager-load**: `paged_query`, `get_flagged_queue` `q_rows`, `post_verdict` `fetch_stmt`. + `tests/fast/test_curator_split.py` (7 test) |
| `4b9988d09` | **`backend/services/productive_failure_service.py` (5/17)** — 9/9. `get_pretest_questions` kolon seçimi 3 JOIN'e çevrildi. Eager-load **N/A (ölçüldü)**. + `tests/fast/test_productive_failure_service_split.py` (4 test) |

**`post_verdict` en dişli bulgu:** `row.quality_review_status` hem **okunuyor hem set ediliyor**
(delege setter'ı da ilişkiye dokunur) → eager-load'suz **getter VE setter** `MissingGreenlet` atardı.

### S214 — MUTASYON İKİ TESTİMİ ÇÜRÜTTÜ (kaydedilecek ders)

mnemonic'te 7 mutasyonun 2'si **hayatta kaldı**. İkisi de bendeydi, ikisinin de
kök nedeni ölçüldü (`3c2580332`):

1. **Test kördü.** `test_is_active_filter_preserved` **tam SQL'de** alt-metin
   arıyordu. Ama `select(QuestionBankItem)` TÜM question_bank kolonlarını SELECT
   listesine koyar → `is_active` orada zaten var. Filtre WHERE'den tamamen
   silinse bile test geçiyordu. Ölçüldü: filtre yokken `'question_bank.is_active'
   in sql` → **True**, `whereclause` → `question_bank.id = 'q-1'`.
   **Bu, bu deponun kendi kuralının ihlaliydi** ("METİNLE değil YAPIYLA ölç").
   Düzeltme: yalnız `stmt.whereclause` derleniyor.
   → **Genel kural: entity seçen sorguda WHERE iddiasını asla tam SQL'de arama.**

2. **`select_from` burada ölçülen bir NO-OP'tu** — kaldırıldı. advanced_reports/
   curator'da yük taşıyordu (M1 orada 5 test düşürmüştü) çünkü SELECT listesi
   **yalnız** split kolonlarıydı. mnemonic'te listede `QuestionBankItem.id` var,
   sol taraf doğru çıkarılıyor; derlenmiş SQL `select_from`'lu ve'suz birebir
   aynı. #451 deseni tersten: **kodun var olması gerekli olduğunu kanıtlamaz.**
   → **Kural: `select_from` SELECT listesi split-only ise ZORUNLU, değilse süs.**

Düzeltmeden sonra 8/8 mutasyon öldürüldü (M3b dahil: yalnız `metadata_info`
eager-load'unu düşürmek de yakalanıyor).

### S214 — kapı borcu ilk kez çıktı (yeni sınıf)

`advanced_reports.py` **HEAD'de de** kapıyı geçmiyordu: 1 ruff + 29 mypy. Önceki 5 dosya
temizdi, bu yüzden bu sınıf ilk kez görüldü. Kullanıcı onayıyla temizlendi (0/0):

- **RUF006 gerçek kusurdu:** `asyncio.create_task` dönüşü tutulmuyordu → arka plan PDF
  görevi koşarken toplanabilir, PDF **sessizce** üretilmez. `_BACKGROUND_PDF_TASKS` + callback.
- `gather(return_exceptions=True)` daraltması `Exception` → `BaseException`. Eski hâli
  `CancelledError` gibi BaseException'ları **veri sanıp rapora gömerdi**.
- 6 sözlük + 2 imza anotasyonu (davranış aynı).
- **`from models import ...` üzerindeki `type: ignore` bir ALET ARTEFAKTI:** pre-commit
  mypy depo **kökünden** koşuyor, orada YOLO ağırlık klasörü `kiro2/models/` var (sadece
  `.pt`) ve `models` ona çözülüyor → 0 attribute. Çalışma zamanında CWD=backend.
  **Bu kalıcı bir tuzak: kökte `models` adlı Python-olmayan klasör var.**
- **`kiro2-api-import-smoke` hook'u bu makinede KIRIK.** Kontrol kolu: dokunulmayan
  `api/curator.py`'de de aynı 3 hata (`WinError 127`, eksik native DLL →
  `api.rag` / `api.youtube_routes` / `api.v1.semantic_search`). `SKIP=` ile atlandı.
  Aynı DLL `tests/fast/test_api_coverage_batch14.py`'de 5 setup ERROR üretiyor — **pre-existing**.

### Fail Eden Testler
- **mnemonic: 10/10 PASS**, mutasyon **8/8 öldürüldü** (ilk turda 5/7'ydi — bkz. üstte).
- **advanced_reports: 8/8 PASS**, mutasyon **6/6 öldürüldü** (hepsi `failed`, hiçbiri
  `error` değil — mutasyon Python ile uygulandı, kabuk tırnağı yok). Tüketiciler:
  `test_advanced_reports_schema_parity.py` 4/4, `test_mock_endpoint_flags.py` PASS.
- **S213 testleri: 11/11 PASS** (7 curator + 4 productive_failure). Mutasyon **4/4 öldürüldü**.
- ⚠️ `tests/test_curator_api.py` — **2 PRE-EXISTING kusur, HEAD'de de var, dokunulmadı** (pathspec'li stash ile ölçüldü):
  1. `test_get_queue_returns_items` — mock `SimpleNamespace` düz şekilli (split öncesi), `row.statistics` yok
  2. `TestCuratorVerdict` sınıfı **asılıyor** — `asyncio.to_thread(schedule_safe_pool_refresh)` test ortamında broker'a bağlanmaya çalışıyor, mock yok

### Engelleyiciler
YOK.

### Sonraki Adımlar
1. **#485 devamı — `api/osym_routes.py` (2 sınıf + 2 entity).** Sonra kalan 8 dosya.
   Her dosyada sırayla:
   - `pre-commit run --files <dosya>` ile **taban ölç** (advanced_reports gibi
     borçlu mu? borç varsa kullanıcıya sun — S214'te onay alındı, temizlendi).
   - `grep 'select(QuestionBankItem)' <dosya>` → **>0 ise eager-load ZORUNLU**,
     hangi alanların okunduğunu bul (setter de sayılır).
   - Testte WHERE iddiasını `stmt.whereclause` üzerinden ölç, tam SQL'de değil.
   - `select_from`'u yalnız SELECT listesi split-only ise ekle.
2. `tests/test_curator_api.py`'nin 2 pre-existing kusuru (stale mock + celery hang) — ayrı görev.
3. Kirli ağaç triyajı (3390 dosya) · test kirliliği (22 fail, `sys.modules` gölgeleme) · `#444` UI · `#467-471`.

### Kararlar (gelecek session tekrar tartışmasın)
- **4 adımlı kabul kriteri değişmedi** (derle · `get_final_froms()` · eager-load'u kolon/entity ayrımıyla ÖLÇ · gerçek modele test). Detay: `.claude/rules/audit-methodology.md`, S212 bölümü.
- **Skor 5/5 dosyada kusur** — kriter gevşetilmiyor.
- **Biçimlendirici import'u siliyor:** `models.question_bank`'tan yeni sınıf import edip gövdeyi
  henüz yazmadıysan hook onu **siler** (bu turda 2 kez oldu, `NameError` testte yakalandı).
  Yordam: **önce gövdeyi yaz, sonra import'u ekle, sonra dosyayı Read ile doğrula.**
- **`/tmp` iki namespace:** bash `/tmp` = MSYS, Python `/tmp` = `C:\tmp`. Kontrol kolu için
  dosya yazma — `subprocess`'le `git show` çıktısını doğrudan Python'a al.
- Pre-push bekçisinin mock/magic-number uyarıları **advisory** (exit 0), bloklamıyor.
