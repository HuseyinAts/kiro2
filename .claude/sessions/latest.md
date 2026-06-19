## Session Handoff — 2026-06-19 (Serving-path leak fix + gate2c demote + answer-wrong scan)
**Branch:** `feature/self-evolution-optimization`
**Son commit:** `cce6807fe` (offline_sync F821) | `7c6731940` (serving-path gate)

### Bu session — 4 iş, hepsi kanıtlı/geri-alınabilir
1. **Serving-path sızıntı fix (HEADLINE, committed):** placement (`load_assessment_items`) ve offline (`build_sync_package`) `question_bank`'i yalniz `is_active` ile sorguluyor, `v_safe_for_beta` kapisini BYPASS ediyordu. Canli DB: placement havuzu **110.895 (94.443 unverified/pending) → 6.544 (%100 v_safe)**. TDD: `tests/test_serving_path_leak.py` kaynak-introspeksiyon guard (red→green), 26 mevcut placement testi geçti. Fix = kanonik `id IN (SELECT id FROM v_safe_for_beta)` her iki serviste (3'er sorgu).
2. **gate2c demote (committed, D6):** 62 Opus-doğrulanmış çöp soru (50 dup/OCR proxy + 12 Opus-confirmed garble) → geri-alınabilir `gate2c_demoted` exclusion tablosu + view predicate. **v_safe 6.606 → 6.544**, leak=0 (canlı teyit). `correct_answer`/`is_active`'e DOKUNULMADI.
3. **Answer-wrong taraması (214/214, %100):** consensus answer-wrong (gemma3==qwen3≠stored) Opus ile kör-çözüldü. **~%1,4 wrong-key** (3 aday, biri güçlü), ham %27 değil. Anahtar değişikliği YOK (`correct_answer` korumalı). Detay aşağıda.
4. **offline_sync F821 fix (committed `cce6807fe`):** `process_sync_results` tanımsız `questions_map`/`cards` kullanıyordu (her cevap sessizce failed) + `_next_sync_at_iso` `timezone.utc` (tanımsız). Döngü öncesi soru/kart ön-getirme + `UTC`. TDD `tests/test_offline_sync_service.py` (3 test red→green); kullanılmayan import'lar da çözüldü.

### Önemli durum düzeltmesi
Eski handoff'taki "v_safe 13.831" ESKİ. Bu session öncesi **D5 sıkılaştırması** (coherence/promote bayrak şartı) 13.831 → 6.606 indirdi; D6 demote 6.606 → **6.544**. Bu kasıtlı (status-only gate çok gevşekti).

### Açık işler (öncelik sıralı)
1. **Push** — `7c6731940` push'landı; `cce6807fe` + bu handoff bekliyor (`git push origin feature/self-evolution-optimization`).
2. **3 wrong-key adayı** (manuel uzman onayı, `correct_answer` korumalı): `f41b7323`(stored C→D, güçlü), `e9c247a6`(B→A), `e829870c`(E→C, bozuk soru). + ~25 bozuk soru (seçenekte cevap yok / çoklu doğru) → gate2c'ye eklenebilir.
3. **`verified_provisional` 5.879** — v_safe'in en büyük denetlenmemiş bloğu, sıradaki Opus turu hedefi.

### Notlar / araçlar
- DB: native PG 5434 (servis `postgresql-x64-18`, bu session admin/RunAs ile başlatıldı). Read'ler MCP `dbhub-kiro2` ile.
- bash VM bu session boyunca çökük → tüm script'ler HOST PowerShell ile çalıştırıldı (human-in-loop).
- gate2c scaffolding: `backend/scripts/quality/_gate2b/` (D6_*.sql, build_final_demote.py, final_demote_ids.json committed; gate2c_*.py + preds/batches/master.csv transient, commit edilmedi).
- **Serving-path:** sadece placement+offline canlı sızıntıydı. `exam_performance_service` = geçmiş analiz (düşük risk), `question_repository` = admin (student-facing değil) — fix kapsamı dışı.
