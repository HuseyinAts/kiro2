## Session Handoff — 2026-06-12 (Serving-gate fix + conflict kurtarma + frontend reconcile)
**Branch:** `master` (origin ile senkron)
**Önceki session:** 2026-06-10 DB audit + R1-R5 remediation (aşağıda "Geçmiş").

### Bu session — commit zinciri (hepsi push'lu)
- **`13eb6b07a` Option A** — `soru_bankasi_service.py` öğrenciye soruyu `v_safe_for_beta` view'inden servis ediyor (`_safe_for_beta_gate()` = `id IN (SELECT id FROM v_safe_for_beta)`). Kod↔view drift bitti; havuz 12,337→**9,913**; 2,424 tier1 tek-sinyal düştü. Canlı view ~256ms.
- **`818bacb21` Dalga 1** — master HEAD'e commit'lenmiş conflict marker'lı 7 dosya (kök: `28b2f8083` "Recovered stash 2"). Backend 6 + NodeDetailsPanel keep-upstream. Bonus: `osym_exam_engine.py` düşmüş kapanış parantezi düzeltildi.
- **`03ef96b83` Dalga 2** — 5 frontend dosyası. Mekanik keep-upstream 78 tsc hatası verdi (mimari ayrışma). 3 özellik dosyası `recover/clean-main-wip-1261`'den alındı → WIP özellikleri (celebration/streak/adaptive-feedback/onboarding/skillgraph) **kurtarıldı**; 2 prop hizalandı.
- **`934e1ff29`** — handoff.
- **(son) feat: subject-switching + Fix 5 + test rewrite** — recover hook'a `selectedSubject`/`changeSubject` portlandı (Chip seçici + SkillGraphView gerçek derse bağlı); recover-base'in kaybettiği **Fix 5** (`updateProgress/markNodeComplete` → `{success, allCompleted}` path-tamamlandı tespiti) geri kazanıldı; `useLearningPath.test.ts` cookie-auth mimarisine yeniden yazıldı. **tsc=0, 20/20 test yeşil.**

### State
- **Tüm conflict marker'lar gitti; backend+frontend rebuild-güvenli, tsc=0, hook testleri yeşil.** 10 WIP component zaten ağaçta mevcut.
- Backend container: Option A deploy edildi (health OK). Dalga 1/2 + frontend dosyaları henüz container'a kopyalanmadı (rebuild'de gelir; kaynak commit'li).

### ✅ Bu session kapanan takipler
- **Frontend testleri** — yeniden yazıldı, 20/20 geçiyor (eski `learningPathService` mimarisi → cookie-auth).
- **Subject-switching port** — geri eklendi, SkillGraphView gerçek seçili derse bağlı.

### Açık işler (öncelik sıralı)
1. **P0 — HNSW embedding index** (2026-06-10 audit'ten): migration `b2f1a9c7d3e4` applied zincirde AMA canlıda **YOK** (sync-stamp atlamış). pgvector + maintenance_work_mem hazır. Tek komut: `CREATE INDEX CONCURRENTLY idx_qb_embedding_hnsw ON question_bank USING hnsw (embedding vector_cosine_ops);`
2. **P2 — düşen master özellikleri:** recover-base 3 frontend dosyasından `DuelMode` + `ErrorClusterCard` düştü (küçük; istenirse portlanır). subject-switching + Fix 5 zaten geri alındı.
3. **P2 — Option A matview** (`mv_safe_for_beta` + id index + REFRESH): ~256ms→~3ms.
4. **P2 — DB temizlik** (audit): 161 boş + 35 eski yedek tablo; json→jsonb (9 qb kolonu); tz'siz timestamp; 7 dup index; 5 remediation backup tablosu (güven periyodu sonrası DROP).

### Notlar
- **bash sandbox mount güvenilmez** (büyük dosyalarda stale/truncate — osym 1971'de kesik göründü ama host tamdı). Frontend/Python doğrulaması HOST araçları + kullanıcı py_compile/tsc/vitest ile yapıldı.
- `recover/clean-main-wip-1261` = stash WIP'in tam/tutarlı kaynağı. `e25b1dd1d` = bozuk merge'in temiz parent'ı (pre-stash master).

### Geçmiş (2026-06-10 audit) — özet
question_bank 187,834; aktif 110,895 (98,361 yargılanmamış ama servis `v_safe_for_beta`=9,913 ile gated). R1 student_answers→0, R2 is_calibrated 82,530→196, R4 exam→0, R5 FK eklendi. Detay: `docs/audits/2026-06-10_full_db_audit.md`.
