## Session Handoff — 2026-06-12 (Serving-gate fix + commit'li conflict kurtarma)
**Branch:** `master` (origin ile senkron)
**Son commit:** `03ef96b83`
**Önceki session:** 2026-06-10 DB audit + R1-R5 remediation (aşağıda "Geçmiş").

### Bu session — 3 commit (hepsi push'lu)
- **`13eb6b07a` Option A** — `soru_bankasi_service.py` artık öğrenciye soruyu `v_safe_for_beta` view'inden servis ediyor (`id IN (SELECT id FROM v_safe_for_beta)`, helper `_safe_for_beta_gate()`, eski `_ACCEPTED_QUALITY_STATUS` kaldırıldı). Kod↔view drift bitti; servis havuzu 12,337→**9,913**; 2,424 tier1 tek-sinyal soru düştü. Canlı view ~256ms (kullanıcı seçimi: en basit; matview sonraya).
- **`818bacb21` Dalga 1** — master HEAD'e commit'lenmiş conflict marker'lı 7 dosya (kök: commit `28b2f8083` "Recovered stash 2"). Backend 6 + NodeDetailsPanel keep-upstream çözüldü. Bonus: `osym_exam_engine.py`'de düşmüş kapanış parantezi (`on_conflict_do_update`) düzeltildi. host py_compile temiz.
- **`03ef96b83` Dalga 2** — 5 frontend dosyası. Mekanik keep-upstream 78 tsc hatası verdi (mimari ayrışma). Çözüm: 3 özellik dosyasını (`ModernLearningPathPage`, `useLearningPath`, `QuizInterface`) `recover/clean-main-wip-1261` branch'inden aldık → WIP özellikleri (celebration/streak/adaptive-feedback/onboarding/skillgraph) **kurtarıldı**; 78→2; 2 prop hizalandı (ProductiveFailureFlow `topic/onComplete/onSkip`, SkillGraphView `subject`). App.tsx + ModernOSYMExamInterface keep-upstream (zaten temizdi).

### State
- **Tüm conflict marker'lar gitti; backend+frontend rebuild-güvenli.** 10 WIP component zaten mevcut ağaçta var.
- Backend container: Option A deploy edildi (docker cp + restart, health OK). Dalga 1/2 dosyaları henüz container'a kopyalanmadı (rebuild'de gelir; kaynak commit'li).

### Bilinen sorunlar / notlar
- **bash sandbox mount güvenilmez** (büyük dosyalarda stale/truncate — osym 1971'de kesik göründü ama host tamdı). Frontend/Python doğrulaması HOST araçlarıyla (Read/Grep + kullanıcı py_compile/tsc) yapıldı.
- `recover/clean-main-wip-1261` = stash WIP'in tam/tutarlı hali (gerekirse kaynak). `e25b1dd1d` = bozuk merge'in temiz parent'ı (pre-stash master).

### Sonraki adımlar (bu session'dan)
1. **Frontend testleri:** `useLearningPath.test.ts` + `.bugfix.test.ts` hook'u import ediyor; recover hook API'si farklı (`studySession/streak` vs eski `selectedSubject`). `cd frontend; npx vitest run src/hooks/__tests__` — kırılırsa güncelle.
2. **Düşen master özellikleri:** 3 frontend dosyasında `subject-switching` (selectedSubject/changeSubject), `DuelMode`, `ErrorClusterCard` düştü. Özellikle subject-switching geri port + SkillGraphView'a gerçek seçili ders bağla (şu an `pathNodes[0].title.split(' ')[0]`).
3. Opsiyonel: Option A için matview (`mv_safe_for_beta`) ile ~256ms→~3ms.

### Geçmiş (2026-06-10 audit) — özet
question_bank 187,834; aktif 110,895 (98,361 yargılanmamış ama servis v_safe_for_beta=9,913 ile gated). R1 student_answers→0, R2 is_calibrated 82,530→196, R4 exam→0, R5 FK eklendi. **R3 HNSW index migration'ı (`b2f1a9c7d3e4`) applied zincirde ama canlıda YOK** — sync-stamp atlamış; pgvector+mem hazır, tek komutla kurulabilir (P0). Detay: `docs/audits/2026-06-10_full_db_audit.md`.
