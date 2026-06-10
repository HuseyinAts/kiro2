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

### Remediation UYGULANDI (2026-06-10, backup'lı, atomik, salt-veri)
- **R1:** `student_answers` 161,910 → **0** (4 test hesabı; backup `student_answers_backup_20260610`).
- **R2:** `is_calibrated` TRUE 82,530 → **196** (bootstrap-flag reset; backup `question_bank_iscalib_reset_backup_20260610` 82,334). Kalan 196 hepsi learning_event destekli ama irt_method hâlâ bootstrap_difficulty_prior (gerçek EM değil).
- **R3:** `question_bank.embedding` HNSW index (`idx_qb_embedding_hnsw`, vector_cosine_ops, CONCURRENTLY, valid) + migration `b2f1a9c7d3e4` (down_revision=5aabf9a6c658). Semantik arama artık ANN index'li.
- Detay + geri-alma: `docs/audits/2026-06-10_full_db_audit.md` §J. Script'ler: `docs/audits/2026-06-10_db_audit_artifacts/`.

- **R4:** exam_sessions 323→**0** + exam_questions 28,508→**0** (test temizliği, CASCADE; backup'lar `exam_*_backup_20260610`).
- **R5:** FK `student_answers_question_id_fkey` (question_id→question_bank.id) eklendi + migration `c3d2e1f0a9b8`. Artık junk insert DB seviyesinde engellenir.

### Sonraki Adımlar
1. **P0:** aktif havuz inceleme — judge pipeline (98,361 unverified/pending). Bütçe+API key gerektirir (~$5-7K, 27-40s); strateji belgelenmedi (atlandı). Pilot (1K, ~$60) ile başlanmalı.
2. **P1/P2:** 5 yeni backup tablosunu güven periyodu sonrası DROP; diğer kritik FK'ler; gerçek IRT kalibrasyon (yanıt büyüdükçe).
3. **P2:** 161 boş + 35 eski yedek tablo; json→jsonb (9 qb kolonu); tz'siz timestamp; 7 dup index.
4. **Not:** alembic zincir `5aabf9a6c658(head,untracked) → b2f1a9c7d3e4(HNSW) → c3d2e1f0a9b8(FK)`. 5aabf9a6c658'i commit'le (zincir tutarlılığı).
