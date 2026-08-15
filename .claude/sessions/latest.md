## Session Handoff — 2026-08-15 (S213)

**Branch:** `feature/self-evolution-optimization` · **HEAD:** `4b9988d09` · **Push:** ✅ hepsi pushed
**Ana iş:** #485 — `question_bank` 69-alan split'inin JOIN göçü (S210/S211/S212 devamı)
**Uncommitted:** bu işin dosyaları **temiz**. (Ağaçtaki 3390 kirli dosya = Gemini S210 devri, ayrı görev.)

### İlerleme — ÖLÇÜLDÜ, aritmetik değil

**Kalan: 21 erişim / 11 dosya.** S212 handoff'u "41/14" diyordu; 19 düzeltince aritmetik
22/12 verir ama **ölçüm 21/11**. Fark ±1 — devredilen sayılar sayımdı, bu ölçüm.
Alet kontrol koluyla doğrulandı: `HEAD~2`'de curator.py→**10**, productive_failure→**9** (beklenen).

Ölçüm komutu (delegeli alan listesini kolonlardan türetir, ezbere liste yok):
```
python -c "import re,sys;sys.path.insert(0,'.');from models.question_bank import QuestionContent,QuestionMetadata,QuestionStatistics;
d={c.name for t in (QuestionContent,QuestionMetadata,QuestionStatistics) for c in t.__table__.columns if c.name!='id'};
from pathlib import Path;[print(len([m for m in re.finditer(r'QuestionBankItem\.(\w+)',p.read_text(encoding='utf-8')) if m.group(1) in d]),p) for x in ('services','api','core','app','tasks') for p in Path(x).rglob('*.py') if '__pycache__' not in p.parts and any(m.group(1) in d for m in re.finditer(r'QuestionBankItem\.(\w+)',p.read_text(encoding='utf-8',errors='ignore')))]"
```

| # | Dosya | Erişim |
|---|---|---|
| 1 | `api/advanced_reports.py` | 4 |
| 2 | `services/mnemonic_service.py` | 3 |
| 3 | `services/difficulty_classification_service.py` · `services/placement_assessment_service.py` · `api/osym_routes.py` · `core/irt_daemon.py` · `tasks/mega_feature_tasks.py` | 2 ×5 |
| 4 | `services/offline_sync_service.py` · `services/parent_service.py` · `api/placement_assessment_api.py` · `core/osym_exam_engine.py` | 1 ×4 |

### Yapılanlar

| Commit | İş |
|---|---|
| `f661316fe` | **`backend/api/curator.py` (4/17)** — 10/10. `get_queue` WHERE'inde 3 ayrı JOIN (`QuestionStatistics` status+difficulty, `QuestionMetadata` subject, `QuestionContent` image_url). **3 entity-seçim sitesine eager-load**: `paged_query`, `get_flagged_queue` `q_rows`, `post_verdict` `fetch_stmt`. + `tests/fast/test_curator_split.py` (7 test) |
| `4b9988d09` | **`backend/services/productive_failure_service.py` (5/17)** — 9/9. `get_pretest_questions` kolon seçimi 3 JOIN'e çevrildi. Eager-load **N/A (ölçüldü)**. + `tests/fast/test_productive_failure_service_split.py` (4 test) |

**`post_verdict` en dişli bulgu:** `row.quality_review_status` hem **okunuyor hem set ediliyor**
(delege setter'ı da ilişkiye dokunur) → eager-load'suz **getter VE setter** `MissingGreenlet` atardı.

### Fail Eden Testler
- **Yeni testler: 11/11 PASS** (7 curator + 4 productive_failure). Mutasyon **4/4 öldürüldü**.
- ⚠️ `tests/test_curator_api.py` — **2 PRE-EXISTING kusur, HEAD'de de var, dokunulmadı** (pathspec'li stash ile ölçüldü):
  1. `test_get_queue_returns_items` — mock `SimpleNamespace` düz şekilli (split öncesi), `row.statistics` yok
  2. `TestCuratorVerdict` sınıfı **asılıyor** — `asyncio.to_thread(schedule_safe_pool_refresh)` test ortamında broker'a bağlanmaya çalışıyor, mock yok

### Engelleyiciler
YOK.

### Sonraki Adımlar
1. **#485 devamı — `api/advanced_reports.py` (4).** Sonra `mnemonic_service.py` (3), kalan 9 dosya.
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
