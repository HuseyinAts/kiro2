## Session Handoff — 2026-06-10 (Tam DB Audit + Kök Neden)
**Branch:** `fix/linguistic-concurrency-issues`
**Son commit:** `d73f0de1e` — docs(audit): 2026-06-10 tam DB audit (sema+kalite+kok-neden, 5 gecis)
**Uncommitted:** 70+ önceden var olan `M` dosya (config.py dahil — benim değil) + paralel audit artefaktları untracked. Audit dosyaları commit'lendi.

### Yapılanlar
- **Tam DB audit** (host PG18 `host.docker.internal:5434/kiro2`, backend container üzerinden, salt-okunur, 5 geçiş, evren-level).
- Rapor: [2026-06-10_full_db_audit.md](file:///C:/Users/husey/kiro2/docs/audits/2026-06-10_full_db_audit.md); ham çıktı+script: `docs/audits/2026-06-10_db_audit_artifacts/` (12 dosya).
- **Bulgular:** 276 tablo (161 boş), question_bank 187,834. Aktif havuz %88.7 incelenmemiş. embedding vector(768) ama HNSW index YOK. 35 yedek + 19 ölü kolon + 74 FK-siz link + 7 dup index + 38 json(jsonb değil) + 30 tz'siz ts.
- **Kök neden A:** `is_calibrated=82,530` → 82,517'si `bootstrap_difficulty_prior` (`bootstrap_irt_params.py`), `irt_calibrated=0`; reset script (`irt_reset_bootstrap_flags.py`) hiç koşmamış. CAT motoru bootstrap-prior'u kalibre sanıyor.
- **Kök neden B:** `student_answers` 161,910 → 161,658'i 2026-06-09 load-test artığı (4 user, sabit 15.5s, uniform şık, is_correct boş, %99.8 orphan). Gerçek sinyal `kiro2_learning_events` (287, temiz).
- Düzeltmeler: metadata enrichment %89 (ilk "11" ters okumaydı); yedekler ~50MB (1.8GB değil); control char gerçek bozulma ~179+NUL.

### State
- DB: host PG18 :5434 sağlıklı; sandbox host'a ulaşamıyor (insan-döngüsü psql/docker).
- Phantom-doğrulandı: rejected/legacy aktif=0 (Lesson #31 kapalı), 0 FK orphan (tanımlı FK), subject_area UPPERCASE, tek alembic head.

### Engelleyiciler / Notlar
- Alembic head `5aabf9a6c658_fix_schema_drift_concurrently.py` git'te **untracked** (DB head sürüm kontrolünde değil).
- Kökte paralel audit artefaktları (`ENTERPRISE_*_AUDIT.md`, `_universal_db_auditor_results.json`, `brutal_db_*.py`) — phantom önlemek için bizim raporla karşılaştır.

### Sonraki Adımlar
1. **P0:** `irt_reset_bootstrap_flags.py --dry-run` → uygula (is_calibrated temizliği); CAT önceliklendirmesini gözden geçir.
2. **P0:** `student_answers` load-test artığını ayıkla (`answered_at::date='2026-06-09'` + 4 test-user); load-test'i prod DB'den ayır; is_correct grading bağla.
3. **P1:** embedding HNSW index; 161 boş + 35 yedek + 2 ölü tablo temizliği; kritik FK'ler (önce student_answers temizliği).
