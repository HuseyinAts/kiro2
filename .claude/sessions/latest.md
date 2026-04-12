## Session Handoff — 2026-04-12 Session 151
**Branch:** master
**Son commit:** (Wave 15 uncommitted — will be committed with this handoff)
**Uncommitted:** Wave 15 edits in 2 files (test_golden_flows.py + golden-flows.md)
**Pushed:** HAYIR — 20+ commit (Session 150 Wave 14 + Session 147-149 + Wave 15 + handoff) origin/master'a push bekliyor

### Yapilanlar — Session 151 (prophylactic list[dict] sweep + Wave 15)

**Prophylactic list[dict] sweep (rule-of-four tescil):**
- `grep -rn "Response(\*\*result)" backend/api/` taraması: 20 call site analiz edildi
- **2 gerçek bug, her ikisi de `backend/api/dina_api.py`'da** (Session 143 GF65 ile aynı dosya — rule-of-four)
- **GF151a `get_skill_profile`**: `services.dina_service.get_student_skill_profile` `list[dict]` döner (ya da `[]`), handler `SkillProfileResponse(**result)` yapıyordu → `TypeError: argument after ** must be a mapping, not list`. Fix: envelope transform (empty list → 404, populated list → per-row `SkillMasteryItem` map). **Rule-of-four established**: GF65 `estimate_student_mastery` + GF125 `error_cluster_api` x3 + GF151a `get_skill_profile` + GF151b `calibrate_parameters` = rule-of-four for service/caller `list[dict]` contract drift.
- **GF151b `calibrate_parameters` (three-part bug)**: (a) service function is a **pure sync math routine** (`responses, skill_masteries, q_matrix`), not async, not kwargs-compatible with handler call; (b) handler `await`ed the sync function; (c) service returns `tuple[dict, dict]`, `CalibrateResponse(**result)` cannot unpack. Endpoint **never worked**. Fix: degrade to 503 matching GF106/GF113/GF115 schema-drift pattern — admin EM pipeline out of scope, follow-up commit should either wire full pipeline (load responses/masteries/q-matrix from DB, run sync function off event loop, persist slip/guess) or delete the endpoint.
- Commit `d64299f`: `fix(dina): list[dict] contract drift prophylactic sweep — rule-of-four`

**Wave 15 — 10 probe, 0 real fix (%0 hit rate — all-time low):**

Frontend fetch mapping strategy: `grep -rhoE "fetch|axios" frontend/src/` → 173 unique paths, prefix-aware set difference vs 150 GF-covered = **164 uncovered**. Top 10 selected for surface diversity (student/teacher/parent dashboards, FSRS reads, gamification profile, manipulatives, GDPR export, push subscription):

- **GF130** fsrs/flashcards/due: first-probe PASS
- **GF131** learning-path/status: first-probe PASS
- **GF132** gamification/profile: first-probe PASS
- **GF133** parent/dashboard (PARENT login): first-probe PASS
- **GF134** ogretmen/dashboard (TEACHER login): first-probe PASS
- **GF135** student-dashboard/hedefler: first-probe PASS
- **GF136** manipulatives/progress/dashboard: first-probe PASS
- **GF137** teachers/my-appointments: first-probe PASS
- **GF138** user/export-data (GDPR/KVKK): first-probe PASS
- **GF139** push/subscribe (VAPID WebPush): first-probe PASS

**Final distribution:** 156 test → **154 PASS / 0 FAIL / 2 SKIP** (baseline korundu, +10 Wave 15 probes hepsi first-probe PASS).

`.claude/rules/golden-flows.md` Wave 15 tablosu + meta-lesson eklendi: hit rate trailing indicator curve güncellendi (Wave 10 %80 → 11 %50 → 12 %20 → 13 %50 → 14 %10 → **15 %0**), **hit rate bir probe selection artifact, kalite metriği değil** tescilli. Wave 16 strategy belirlendi: uncovered-164 pool'dan daha düşük traffic'li surface'lere bias (veli/*, zpd-maarif/*, monitoring/*, admin/content/*).

### Fail Eden Testler
- YOK. 156 test → 154 PASS / 0 FAIL / 2 SKIP.

### Engelleyiciler
- YOK

### Session 151 Bulgular / Notlar

- **Rule-of-four (GF65 + GF125 x3 + GF151a + GF151b)** — `list[dict]` contract drift artık sistemik bir class olarak tescilli. Prophylactic sweep Session 150 commit'iyle **proaktif olarak** yakalandı; Wave 15 yeni bug getirmediği için Wave 16 öncesi yapılacak prophylactic sweep kategorisi: **Pydantic `Response(**result)` pattern** fail-safe olmalı — service return type annotation'ları incelenerek list/tuple/dict ayrımı doğrulanmalı.
- **Wave 15 %0 hit rate — trailing indicator curve'un dibine yapıldı**: Frontend fetch mapping-driven target selection real production traffic'i yansıttığı için probe'lar zaten production-working surface'lere düştü. **Hit rate bir probe selection artifact**, kalite metriği değil. Curve: 80 → 50 → 20 → 50 → 10 → 0.
- **Wave 16 shift**: uncovered-164 pool'dan **daha düşük traffic** surface'lere bias gerekli (veli/cocuklar, zpd-maarif/hesapla, monitoring/bottlenecks, admin/content/educational, text-simplification/detect-complex-words, visual-supports/color-schemes). Beklenen hit rate 10-20% + GF125-style stacked-bug spike olasılığı.
- **Golden Flow suite saturation signal**: Wave 16 de ≤%10 dönerse, suite **single-handler bug'lar için doygun** ilan edilmeli. Sonraki development phase: (a) schema drift migration backlog (GF106 StudentReview + GF113 COPPA + GF115 OSB), (b) sync-service async port backlog (GF112 DifficultyClassificationService ~700 satir, GF117 api_key_manager ~300 satir), (c) DINA EM calibration pipeline wiring (Session 151 GF151b 503 shim'i kaldir).

### Sonraki Adimlar (maks 5)

1. **COMMIT + PUSH** — Wave 15 + Session 151 handoff commit + tüm pending (Session 147-150 + Wave 15 + handoff) origin/master'a push.
2. **Wave 16 planning** — uncovered-164 pool'dan düşük traffic disjoint top-10 seç (admin tools, compliance, i18n). Beklenen %10-20.
3. **Prophylactic sweep — Pydantic `Response(**result)` ile servisin annotated dönüş tipi diff** (P2) — rule-of-four'dan sonra rule-of-five beklemeden proactive type diff. Service signature `-> list[dict]` veya `-> tuple` ise handler'ın envelope transform yapması gerekli.
4. **Schema drift migration backlog** (P2, devam) — StudentReview (GF106) + COPPA child_id (GF113) + OSB settings missing cols (GF115) — üç farklı `alembic revision --autogenerate` ile 503 shim'leri kaldir.
5. **Sync service async port backlog** (P2) — DifficultyClassificationService ~700-line (GF112) + api_key_manager ~300-line (GF117) + DINA EM pipeline (GF151b) — shim'ler 503 dönüyor, port edildikçe kaldırılır.

### Kararlar (gelecek session tekrar tartismasin)
- Wave 15 tamamlandı: 10 probe, 0 real fix, hit rate %0 (all-time low). Trailing indicator curve: %80→%50→%20→%50→%10→**%0**.
- Golden Flow suite 156 test, 154 PASS / 0 FAIL / 2 SKIP baseline sabit.
- `list[dict]` contract drift rule-of-four tescil edildi (GF65 + GF125 x3 + GF151a + GF151b).
- Hit rate bir **probe selection artifact**, kalite metriği değil — Wave 15'in sıfıra inmesi "bug yok" değil "real production traffic surface'leri zaten çalışıyor" demek.
- Wave 16'da hedef aday seçimi: low-traffic uncovered surface bias, NOT high-traffic frontend mapping (zaten Wave 15'te tüketildi).
