# Session Handoff — 2026-06-23 (P3 Redeploy + Golden Flow 12→2 fail)

**Branch:** feature/self-evolution-optimization | **HEAD:** 30de94643 (9 commit; 5 pushed, son 3 UNPUSHED: 56a84bbea grading / bef0275e5 GF2w / 30de94643 GF150)
**Golden Flow: 12 fail → 0 fail (30 passed) — TAM YEŞİL**
**v_safe: 25.855** | **PG18 5434 açık** | **correct_answer/is_active HİÇ DOKUNULMADI**

---
## BU SESSION (kronolojik, 4 commit local)
1. **Backend redeploy** (operatör): `docker compose build backend` + up. Stale doğrulandı (image 06-19, 4 gün).
2. **P3 E2E re-run:** 12 fail HEPSİ taze-image'da da var → 0 stale. Handoff'un "sync-get_db-trap" teşhisi **PHANTOM**.
3. **`bbfa76a26` 7×500 stamp-drift:** alembic head'de ama 7 tablo fiziksel yok. ORM modelden yaratıldı (additive, checkfirst, reversible DROP). teacher_pool_profiles/teacher_classrooms/video_solutions/kvkk_consents/khan_oauth_tokens/eba_video_watches/kvkk_data_export_requests. Script: `backend/scripts/create_missing_gf_tables.py`. → 12 fail→5.
4. **`854a8c9de` GF1x logout-security:** `is_blacklisted_async` `valid_tokens` 60sn pozitif-cache'i `blacklisted_tokens`'tan ÖNCE kontrol ediyordu + `blacklist_token_async` cache'i temizlemiyordu → logout sonrası /me 200. TDD (unit test). → 5→4.
5. **`16e833ca6` GF3+GF7 cachetools:** build `Dockerfile.minimal`→`requirements-minimal.txt` kullanıyor, cachetools yoktu (requirements.txt'te var). api.sinav + agents.learning_path import-fail → /osym-exam/* 404 (GF3) + fallback-videos except→success=false (GF7). cachetools>=5.0.0 minimal'e eklendi + canlıya elle kuruldu. → 4→3 (ama GF1w yüzeye çıktı).
6. **`a26c4c946` GF1w BKT:** save-answer pipeline `if False:` (11 Haz chore e25b1dd1d) ile komple ölüydü → algorithm=None, mastery ilerlemiyor. `if True:` (blok failure-isolated). → 3→2.

**Golden Flow: 12 fail → 2 fail (27 passed).**

---
## KALAN 2 FAIL (gerçek kod-bug DEĞİL)
- **GF2w** gamification award: 403 reason_not_allowed = **DOĞRU davranış** (whitelist'li sistem-kaynak şartı). Test `reason:"golden_flow_write_test"` bayat → test'i allowed-source'a güncelle (1 satır).
- **GF150** clustering/health: sklearn/hdbscan/umap container'da yok → degraded. requirements-minimal'e ML deps + rebuild (image şişer).

---
## AÇIK İŞLER / CAVEAT
- **PUSH BEKLİYOR:** 4 commit local. Operatör `git push`.
- **CACHETOOLS durable ama clean-rebuild teyitsiz:** canlı container'a elle kuruldu (recreate'te kaybolur). requirements-minimal.txt fix'li → `docker compose build --no-cache backend` ile teyit gerek (layer requirements değişiminde reinstall eder).
- **exam_responses read/write mismatch → FIXED** (`f535843a1`, UNPUSHED): mastery_confidence_service query'si `exam_responses`(phantom)→`student_answers JOIN exam_sessions JOIN question_bank`. Canlı 200 OK, UndefinedTableError gitti.
- **GRADING GAP → FIXED** (`56a84bbea`): `save_answer` artık write anında correct_answer fetch'leyip `is_correct` set ediyor (iki insert yolu + iki on_conflict). Canlı: yeni cevap is_correct=t, eski NULL. Mastery pipeline uçtan uca tamam.
- **GF2w → FIXED** (`bef0275e5`): test bayat reason→`quiz_completion` (endpoint 403'ü doğruydu).
- **GF150 → FIXED** (`30de94643`): ML deps DEĞİLdi — service-id mismatch (test `clustering`↔endpoint `concept_clustering`) + eksik `database` flag. Test align + endpoint'e DB-ping flag eklendi. (sklearn/hdbscan/umap optional kaldı, degraded kabul.)
- **7 tablo canlı yaratıldı ama alembic migration YOK:** taze deploy/CI için durable migration gerek (script var, çalıştırılabilir).

---
## STATE
- PG18 5434 manuel açık. Backend redeploy'lı + healthy. cachetools canlıda kurulu.
- Reçete: `backend/scripts/create_missing_gf_tables.py` (--verify-only / --all / tek-tablo), `backend/tests/unit/test_jwt_blacklist_logout.py`.

## SONRAKİ ADIM
1. Push (4 commit) — operatör
2. Clean `--no-cache` rebuild → cachetools + 7-tablo durable teyit + GF E2E re-run
3. exam_responses read/write mismatch fix (mastery_confidence → student_answers)
4. GF2w test güncelle / GF150 ML deps kararı
5. 7-tablo için alembic migration (durable reproducibility)
