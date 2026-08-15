## Session Handoff — 2026-08-15 (S214)
**Branch:** `feature/self-evolution-optimization`
**Son commit:** `34e68da23` chore: S214 handoff — mnemonic 3/3 + eager-load; kalan 14/9 ÖLÇÜLDÜ
**Uncommitted:** bu işin dosyaları **temiz**, hepsi pushed. (Ağaçtaki 3388 kirli dosya = Gemini S210 devri, ayrı görev.)

### Yapılanlar — #485 JOIN göçü, 2 dosya (6/17 ve 7/17)
- `backend/api/advanced_reports.py:410` — `_get_subject_irt_aggregate` 4 erişim JOIN'e (`9488196cf`). Sorgu **kurulma anında** patlıyordu; SELECT listesi split-only olduğu için `.select_from()` ZORUNLU. Eager-load N/A (ölçüldü: `select(QuestionBankItem)` = 0). + `backend/tests/fast/test_advanced_reports_split.py` 8 test, 6/6 mutasyon.
- Aynı commit'te kapı borcu 0'landı (HEAD'de de vardı: 1 ruff + 29 mypy). **RUF006 gerçek kusurdu:** `asyncio.create_task` dönüşü tutulmuyordu → arka plan PDF görevi toplanabilir, PDF sessizce üretilmez (`advanced_reports.py:334` `_BACKGROUND_PDF_TASKS`). Ayrıca `gather(return_exceptions=True)` daraltması `Exception`→`BaseException` (eskisi CancelledError'ı veri sanıp rapora gömerdi).
- `backend/services/mnemonic_service.py` — 3 sınıf-düzeyi JOIN **+ eager-load** (`8713ab8e3`). Seride iki kusur sınıfını birlikte taşıyan ilk dosya: `generate_mnemonic:70` entity seçip `question.question_text/.correct_answer/.subject_area` okuyordu → `selectinload(content, metadata_info)`. + `backend/tests/fast/test_mnemonic_service_split.py` 10 test, 8/8 mutasyon.
- `3c2580332` — mutasyon **2 testimi çürüttü**, ikisi de düzeltildi (aşağıda Kararlar).
- `.claude/rules/audit-methodology.md` + `.claude/lessons/ders_kaydi.yaml` — 3 yeni ders (82→85), bekçi 9/9 PASS.

### Fail Eden Testler
- Yeni testler: **18/18 PASS** (8 advanced_reports + 10 mnemonic). Mutasyon **14/14 öldürüldü**.
- Tüketiciler: `tests/unit/test_advanced_reports_schema_parity.py` 4/4, `test_mock_endpoint_flags.py` PASS.
- ⚠️ **PRE-EXISTING, dokunulmadı:** `tests/fast/test_api_coverage_batch14.py::TestYoutubeRoutesCoverage` 5 setup ERROR — `import api.youtube_routes` → `OSError: [WinError 127]` (eksik native DLL).

### Engelleyiciler
- **`kiro2-api-import-smoke` hook'u bu makinede KIRIK.** Kontrol kolu: dokunulmayan `api/curator.py`'de de aynı 3 hata (`api.rag`, `api.youtube_routes`, `api.v1.semantic_search` → `WinError 127`). `api/**` dosyalarını commit ederken `SKIP=kiro2-api-import-smoke` gerekiyor. Ortam kusuru.
- **Kökte `models/` = YOLO ağırlık klasörü** (`.pt` dosyaları, Python değil). pre-commit mypy kökten koştuğu için `from models import X` ORAYA çözülüyor (namespace paketi, 0 attribute). `models`'tan import eden her dosyada tekrar edecek; `advanced_reports.py:27`'de gerekçeli `type: ignore` var.

### Sonraki Adımlar
1. **#485 devamı — `backend/api/osym_routes.py`** (2 sınıf + **2 entity** → eager-load gerekecek). Sonra: `services/offline_sync_service.py` (1+**2**), `services/placement_assessment_service.py` (2+**1**), `core/irt_daemon.py` (2+**1**), `services/difficulty_classification_service.py` (2), `tasks/mega_feature_tasks.py` (2), `services/parent_service.py` (1), `api/placement_assessment_api.py` (1), `core/osym_exam_engine.py` (1).
2. Her dosyada sırayla: `pre-commit run --files <dosya>` ile **taban ölç** (borçluysa kullanıcıya sun) → `grep 'select(QuestionBankItem)' <dosya>` → derle + `get_final_froms()` → gerçek modele test → mutasyon.
3. `tests/test_curator_api.py`'nin 2 pre-existing kusuru (stale mock + celery hang) — S213'ten devir.
4. Kirli ağaç triyajı (3388 dosya) · `#444` Öğretmen Öğrenciler UI · `#467-471`.

### Kararlar (gelecek session tekrar tartışmasın)
- **Kalan sayısı: 14 erişim / 9 dosya — ÖLÇÜLDÜ** (tur başında 21/11). Alet kontrol koluyla doğrulandı (`HEAD~1`'de advanced_reports → 4, beklenen). Ölçüm komutu bu dosyanın git geçmişinde (`0edb593df`).
- ⚠️ **Sayaç örnek düzeyini GÖRMEZ** → "14" bir **alt sınır**. `mnemonic_service`'in en riskli kusuru sayaçta 0 göründü. Ders: `L-s214-sayac-ornek-duzeyini-gormez`.
- **WHERE iddiasını tam SQL'de arama** — `select(Entity)` tüm kolonları SELECT'e koyar, filtre silinse bile alt-metin eşleşir. Yalnız `stmt.whereclause` derle. Ders: `L-s214-where-iddiasi-whereclause`.
- **`select_from` koşulludur** — SELECT listesi split-only ise ZORUNLU, `QuestionBankItem.id` içeriyorsa SÜS (mnemonic'te kaldırıldı; derlenmiş SQL birebir aynıydı). Ders: `L-s214-select-from-kosullu`.
- **Kapı borcu politikası:** dosya HEAD'de de kapıyı geçmiyorsa kullanıcıya sun, onay alıp temizle (S211/S214 precedent). Sessizce `--no-verify` YOK.
- 4 adımlı kabul kriteri değişmedi. **Skor: elden geçen 7 dosyanın 7'sinde kusur** — kriter gevşetilmiyor.
- Biçimlendirici, gövdesi yazılmamış import'u siler: **önce gövde → sonra import → sonra Read ile doğrula.**
