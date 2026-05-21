# KIRO2 Half-Done Work + TODO Inventory — DEEP

**Date:** 2026-05-21
**Scope:** Full project (backend, frontend, alembic, docs, _pilots)
**Methodology:** grep pattern matching + manual classification, excluding venv/site-packages/__pycache__/reward_hacking detector source/tests where noted
**Effort:** ~60 minutes

---

## Numerical Summary

| Category | Count | Notes |
|---|---:|---|
| **Backend TODO** (production code, excluding tests/venv/reward_hacking detector) | **55** | Real engineering debt |
| **Backend FIXME** (production code) | **0** | All 462 raw matches were inside venv/site-packages |
| **Backend HACK** (production code) | **0** | All 63 raw matches were inside venv/site-packages |
| **Backend XXX** (production code) | **1** | `image_match_metadata_v1.py:142` — variable doc, not a marker |
| **Frontend TODO/FIXME/XXX/HACK** | **2** | OSYMExamInterfaceRefactored + FSRSReviewPage |
| **Frontend "TODO" comments in real code** | 2 | Other 6 matches were `XXXXXXXXX` in Turkish phone validation regex docs |
| **NotImplementedError (production)** | **7** | qwen_provider, gemini_provider, veli_service (×3), repositories/base, mcp_servers |
| **HTTP 501 NOT_IMPLEMENTED responses** | **19** | admin.py (6), clustering_api.py (4), others |
| **pytest skip directives** | **1,108** | Includes `pytest.skip(...)`, `@pytest.mark.skip`, `@pytest.mark.skipif` |
| **`@pytest.mark.skipif(True, ...)` hardcoded** | **19** | Files unconditionally skipped — pure dead test |
| **`# type: ignore` in production** | **93** | Type-suppression debt |
| **`# noqa` in production** | **172** | Lint-suppression debt |
| **Mock-in-production occurrences (api/analytics.py alone)** | **24** | Severe — see SF audit |
| **Mock-in-production (api/content_management.py)** | **43** | Severe — entire file is mock data |
| **Mock-in-production (api/advanced_reports.py)** | **5** | Mock IRT, ZPD, learning style profiles |
| **Mock-in-production (api/agents.py)** | **2 endpoints** | Entire file is mock (1 hard-coded agent) |
| **_deprecated/ folders** | **9** | Backend (6) + Frontend (2) + mypy_cache mirror |
| **_deprecated/ source files (total)** | **152** | 56 services + 41 frontend pages + 13 misc + 42 in mypy_cache |
| **_deprecated/ LOC** | **38,567** | services=30,165, frontend=~7K, api=2,130, core=4,322, models=1,950 |
| **_deprecated files STILL referenced from non-deprecated code** | **20+** | Pages: LearningPathPage (10 refs!), StudentDashboard (5 refs), LoginPage (5), SettingsPage (4) |
| **Alembic migrations total** | **63** | + 2 .disabled (`20260126_additional_performance_indexes`, `cc2ead85e242_merge_cascade_and_irt_heads`) |
| **Active git stashes** | **3** | `pre-yolo checkpoint`, `frontend_tests_unknown_origin_20260422`, `WIP on clean-main` |
| **WIP commits in log** | **0** | Clean naming convention |
| **WIP/temp branches** | **0** | (zero WIP/temp/experimental branches detected) |
| **Untracked _pilots files** | **12** | Active investigation work (HIGH_tier_deep_audit_25k, deep_correctness_audit_v2, etc.) |
| **ORM schema drift HIGH findings** | **203** | Per `docs/audits/2026-04-12_orm-schema-drift-baseline.md` |
| **ORM schema drift MEDIUM** | **455** | |
| **ORM schema drift LOW** | **206** | |

---

## Top 10 Files by TODO Density (production)

| Rank | File | TODO count | Severity |
|---:|---|---:|---|
| 1 | `backend/services/irt_analysis_service.py` | 7 | HIGH — repository pattern never built (5 query stubs) |
| 1 | `backend/api/enhanced_auth_api.py` | 7 | HIGH — device listing, session revocation, email sending (all mock) |
| 3 | `backend/tasks/bulk_tasks.py` | 5 | MED — KVKK export, cache cleanup, log archival never implemented |
| 4 | `backend/tasks/video_tasks.py` | 4 | MED — video processing, frame extract, subtitles (Celery task stubs) |
| 4 | `backend/tasks/report_tasks.py` | 4 | MED — class analytics, platform metrics aggregation stubs |
| 6 | `backend/tasks/email_tasks.py` | 3 | HIGH — `# TODO: Integrate with email service` (SendGrid/SES) |
| 6 | `backend/db/validation/schema_checker.py` | 3 | LOW — these are EMITTED TODOs in generated code, not in own code |
| 6 | `backend/api/auth.py` | 3 | MED — profile image (×2), password reset email |
| 6 | `backend/api/adhd_task_management_api.py` | 3 | LOW — enum value named "TODO", not real debt |
| 10 | `backend/services/hybrid_question_generator.py` | 2 | MED — fine-tuned model integration |

---

## Critical Half-Done Features (P0 — Blocking Beta)

### CHD-1: `api/analytics.py` is 24 Mock Endpoints in Production
**File:** `backend/api/analytics.py` (1,609 lines)
**Pattern:** `# Mock implementation - gerçek implementasyonda DB'den gelecek`
**Evidence:** 24 mock returns, returning hard-coded numbers like `"total_active_users": 15247`, `"system_uptime_percentage": 99.7`
**User impact:** Teacher dashboard, admin analytics, parent reports all read **fake numbers** that look real to the user. Numbers never change across loads — observable by any beta tester who reloads twice.
**Sample:** lines 640-660 (student performance metrics) — returns same 1247 questions, 0.715 accuracy, "increasing trend" hard-coded.

### CHD-2: `api/content_management.py` 43 Mock References
**File:** `backend/api/content_management.py` (834 lines)
**Pattern:** Line 13 header `# Mock implementations for testing`, applied to 20 real `@router` endpoints
**Evidence:** Admin "soru bankasındaki sorular" endpoint returns `f"Bu bir örnek soru metnidir - {i+1}"` (sample fake question text) instead of querying `question_bank` (77K real questions!)
**User impact:** Admin content management UI shows fake data. CRUD operations would never persist. Two-table-trap pattern repeated: real `question_bank` ignored, mocks served instead.

### CHD-3: `api/agents.py` Entire File Is 1-Item Mock
**File:** `backend/api/agents.py` (50 lines)
**Endpoints:** `/agents/test`, `/agents`
**Evidence:** Comments explicitly say "mock data". Returns single hard-coded "matematik_uzman" agent. Orchestrator has 20 real agents — this endpoint is disconnected.

### CHD-4: `services/ai_chat_service.py` Returns Placeholder AI Response
**File:** `backend/services/ai_chat_service.py:324-360`
**Evidence:** Verbatim comment: `# In production, call OpenAI API here / # For now, return a mock response`
**Output:** `"This is a placeholder AI response. In production, this would call the OpenAI API."`
**User impact:** AI chat feature is non-functional. Already covered partially in silent_failures SF-6 (bilge_alp.py mock fallback).

### CHD-5: `api/advanced_reports.py` Mock IRT + ZPD Profiles
**File:** `backend/api/advanced_reports.py` (922 lines)
**Evidence:** Lines 310, 395, 490, 615, 892 — Mock IRT analysis, mock ZPD range, mock hybrid learning style profile, mock exam parameters, mock trend data.
**Connection to real data:** IRT engine (bkt_service/irt_service) IS live in `record_answer()` pipeline, but advanced_reports endpoint **bypasses it** with mocks.

### CHD-6: `enhanced_auth_api.py` 7 TODOs — Session Management Is Smoke
**File:** `backend/api/enhanced_auth_api.py`
**TODOs:**
- L635: "Gercek cihaz listesi veritabanindan alinmali"
- L699: "Gercek cihaz silme islemi"
- L756: "Gercek giris gecmisi veritabanindan alinmali"
- L840: "Tum aktif oturumlari sonlandir"
- L930: "E-posta ile kodu gonder (production'da gercek email servisi)"
- L1129: "Gercek oturum listesi veritabani/Redis'ten alinmali"
- L1195: "Gercek oturum iptal islemi"
**User impact:** "Devices", "Login history", "Active sessions", "Email 2FA" — every security UI panel shows fabricated data. Logout-from-all-devices does nothing.

### CHD-7: Background Task Stack (Celery) Is All TODOs
**Files:** `backend/tasks/{bulk_tasks,video_tasks,report_tasks,email_tasks,push_tasks}.py`
**TODOs:** 16 across 5 files
**Status:** Every Celery task body is `# TODO: Implement X` — bulk DB insert, KVKK export, cache cleanup, statistics aggregation, log archival, video processing, ffmpeg extraction, subtitle extraction, cache warming, class analytics, platform metrics, weekly aggregation, email service integration, template generation, bulk email, VAPID push.
**User impact:** Any frontend feature that schedules a Celery job receives a task_id then **nothing happens**. (See SF-5 in silent_failures.md — background task with no propagation.)

### CHD-8: `services/irt_analysis_service.py` 7 Repository Stubs
**File:** `backend/services/irt_analysis_service.py`
**Pattern:** "TODO: Replace with proper repository when available" — repeated 6 times for query methods
**Note:** L23 says "Create SoruRepository and SinavCevabiRepository in repositories/" — never done. Methods use direct model access as workaround. Not a runtime bug, but ~700 lines locked into legacy pattern.

---

## Pending Tasks Mapping (Active Work, From Sessions/Plans)

### Quality Hardening Sprint (`docs/superpowers/plans/2026-05-18-quality-hardening-sprint.md`)
| Task | Status | Scope |
|---|---|---|
| Task 1 — student_feedback API tests | **DONE** | 5 TDD tests |
| Task 2 — UNIQUE constraint + IntegrityError handler | **DONE** | Migration `20260518_student_flags_unique.py` |
| Task 3 — rate_limit decorator on feedback | **DONE** | |
| Task 4 — `extractErrorDetail.ts` helper | **DONE** | Frontend |
| Task 5 — 15 critical API smoke tests | **PARTIAL** | 8 PASS / 7 mock-DB artifact (per latest.md L21) |
| **Task 6 — fetch → apiClient migration (30+ files)** | **PENDING** | per latest.md L52, "ayrı session" |
| **Task 7 — Redis unified rate limiter** | **PENDING** | per latest.md L53, "büyük refactor" |
| **Task 8 — CI gate + 7-rule new-endpoint checklist** | **PENDING** | per latest.md L22, also `.github/workflows/test-coverage-gate.yml` not yet created |

### R1 Legacy_v3 FN Restore Pipeline
- Pilot %87 confidence, dry-run 15,321 rows generated
- **PENDING:** Manual verify of 20-30 rows in `backend/_pilots/20260521_r1_fn_restore_pilot_RAW.tsv`
- **PENDING APPLY:** `backend/scripts/quality/r1_legacy_v3_restore_apply.py --apply`
- Per latest.md: blocker until human marks `manual_verdict` column

### Curator Workflow (Faz 3.x — completed in Session 21 May)
| Sub-task | Status |
|---|---|
| Faz 3.1 backend (api/curator.py) | DONE — 17 tests PASS |
| Faz 3.2 frontend (CuratorPage) | DONE — 9 vitest PASS |
| Faz 3.3 keyboard shortcuts | DONE |
| Faz 3.4 queue filters | DONE |
| Faz 3.6 audit logs | **PARTIAL** — `reviewed_at` column not in DB (only JSON-embedded). Pending separate migration. |

### Quality Pool Plan v1 (Faz tasks)
Per MEMORY.md and latest.md:
- **Faz 7.1 beta expansion** — pending, 5-10 student invite blocked on Curator UI (now DONE)
- Faz 5.3 / 6.1-6.4 / 7.5 — judge pipeline tasks (no clear status indicator in session notes)
- Faz 5.8 math-specific judge — pending ($1,710 estimated cost)
- v11b single-option distinctive match — mentioned in inventory request, not in latest.md
- Faz 4.4 Sapphire inter-rater — mentioned in inventory request, not in latest.md
- Faz 3.5 Curator audit — mentioned in inventory request, status unclear

### Bug Fix Pending
- **SQLAlchemy import**: `func.case(else_=)` → `case(else_=)` — per latest.md (no file:line specified)

---

## Deprecated Code Still Actively Referenced (P1)

### Frontend Pages — 20 Deprecated Files Still Imported

These files are in `frontend/src/pages/_deprecated/` but **referenced from non-deprecated code**:

| Deprecated File | Refs | Risk |
|---|---:|---|
| `LearningPathPage.tsx` | **10** | HIGH — touched by 10 active files including App.tsx, ModuleProgressCard, NodeDetailsPanel, 3 Tab components, VideoAnalyticsCard, ModernLearningPathPage |
| `StudentDashboard.tsx` | 5 | HIGH — referenced by Dashboard/StudentDashboard.tsx (likely re-export chain) |
| `LoginPage.tsx` | 5 | MED |
| `SettingsPage.tsx` | 4 | MED |
| `RegisterPage.tsx`, `ExamStartPage.tsx` | 3 each | MED |
| `AdminContentPage`, `AdminSettingsPage`, `AdminUsersPage`, `ChatPage`, `ExamHistoryPage`, `ExamResultsPage`, `ParentChildrenPage`, `ParentNotificationsPage`, `ParentPage`, `ParentReportsPage`, `ProfilePage` | 2 each | LOW |
| `AdminDashboardPage`, `LearningPathPageRefactored`, `ParentDashboardPage` | 1 each | LOW |

**Violation:** `.claude/rules/deprecation-guard.md` says "0 referans → güvenle taşı; 1+ referans → referansları ÖNCE güncelle, SONRA taşı". 20 files were moved to `_deprecated/` while still imported. Either the imports need updating or the files don't belong in `_deprecated/`.

### Frontend Services — 2 Deprecated, Still Referenced
- `frontend/src/services/_deprecated/VideoErrorHandler.ts` — 2 refs
- `frontend/src/services/_deprecated/modernApiClient.ts` — 1 ref

### Backend Deprecated Modules (LOC)
| Folder | Files | Total LOC |
|---|---:|---:|
| `backend/services/_deprecated/` | 54 | 30,165 |
| `backend/core/_deprecated/` | 3 | 4,322 |
| `backend/api/_deprecated/` | 4 | 1,820 |
| `backend/api/v1/_deprecated/` | 2 | 310 |
| `backend/models/_deprecated/` | 9 | 1,950 |
| `backend/_deprecated/` | (top-level) | — |
| **TOTAL** | **72** | **~38,567 LOC** |

No backend `_deprecated/` modules are imported from active code (grep returned 0 hits, except via internal cross-references inside `_deprecated/`).

---

## HTTP 501 NOT_IMPLEMENTED Endpoints (19 total)

Endpoints that return 501 — feature scaffolded but not implemented:

| File | Line | Detail |
|---|---:|---|
| `backend/api/admin.py` | 111, 466, 475, 482, 493, 504 | `educational_materials` table not created; "Toplu soru yukleme henuz implement edilmedi" |
| `backend/api/clustering_api.py` | 184, 231, 277, 310 | 4 clustering endpoints stubbed |
| (others to enumerate via `grep -rn '501\|NOT_IMPLEMENTED' backend/api`) | | |

These endpoints are **routable** (will respond 501) but return no useful data. Frontend that calls them will display error.

---

## Test-Hidden Code (Suppression Debt)

| Pattern | Count | Notes |
|---|---:|---|
| `@pytest.mark.skipif(True, ...)` | 19 | Files PERMANENTLY skipped. Net test loss with no tracking. |
| `pytest.skip(..., allow_module_level=True)` | (subset of 1108) | Several test modules entirely skipped via module-level `pytest.skip` per testing.md lesson #11 |
| `# type: ignore` | 93 | Type debt — mypy noise suppression |
| `# noqa` | 172 | Ruff lint suppression |

---

## Empty / Placeholder Endpoints

Cleanly empty or returning fixed stub responses:

| File:Line | Pattern |
|---|---|
| `backend/api/pdf_processing_api.py:121` | Bare `pass` after a try-block — read-only filesystem fallback (deliberate) |
| `backend/api/monitoring.py:453` | "Token projection stub — not yet implemented" |
| `backend/api/pwa_sync_api.py:117` | "Push subscription stub — not yet implemented" |
| `backend/content/multimedia_content_processor.py:1418` | `task.add_error("Format conversion not yet implemented")` |
| `backend/debug_stub.py:13` | "not yet implemented" |
| `backend/api/rate_limit_api.py:296` | "This is a placeholder. Real implementation would..." |
| `backend/api/encryption_management.py:116` | "⚠️ ENCRYPTION_KEY not set. Using temporary key (NOT FOR PRODUCTION!)" |
| `backend/api/audit_api.py:129` | "Convert AsyncSession to sync (temporary solution)" |
| `backend/api/kvkk_privacy_api.py:127` | "For now, create a placeholder export" |
| `backend/api/question_bank_v2_routes.py:243` | `"confidence": 0.8, # Mock for now` |
| `backend/api/video_solution.py:644` | "CDN upload placeholder" |
| `backend/api/v1/expert_agents_api.py:354` | `visualizations=[], # Simplified for now` |
| `backend/api/enhanced_chat.py:411` | "Fallback: smart placeholder" |
| `backend/services/video_solution_service.py:821-822` | "Şimdilik placeholder implementation" + "CDN upload placeholder" |
| `backend/services/video_transcript_service.py:48` | "Şimdilik placeholder implementation" |
| `backend/services/export_service.py:670` | "Share URL (placeholder — gerçek URL host'a göre ayarlanmalı)" |
| `backend/services/mnemonic_service.py:139` | "proxy: random for now" |
| `backend/services/hybrid_question_generator.py:522` | "Grammar Quality (placeholder — needs actual Turkish NLP)" |
| `backend/services/offline_sync_service.py:87` | "use card id as placeholder question_id" |
| `backend/services/bloom_taxonomy_classifier.py:126` | "Model henüz eğitilmemişse, placeholder" |
| `backend/services/social_content_filter.py:10` | "Layer 7: AI classification (placeholder, timeout 500ms)" |
| `backend/services/taxonomy/multi_taxonomy_analyzer.py:151,184` | "Webb DOK (placeholder — will be implemented in separate task)" + "Infer Webb DOK from Bloom (temporary until Webb classifier is ready)" |
| `backend/services/visual_supports_service.py:219,378` | "PNG export için placeholder" / "Export to {format} (placeholder)" |
| `backend/services/quality/metrics.py:300` | "For now, return a placeholder" |
| `backend/services/video_conference_service.py:481,491` | "Trigger async processing (placeholder)" + "PLACEHOLDER: Implement actual video processing in production" |
| `backend/services/psychometrics/calibration.py:127` | "Create temporary IRT model" |

### NotImplementedError (7 production raises)
| File:Line | Context |
|---|---|
| `backend/core/error_monitoring.py:181` | Abstract method? |
| `backend/services/llm/gemini_provider.py:210` | "Gemini fine-tuning not yet supported via API" |
| `backend/services/llm/qwen_provider.py:268` | Qwen-specific abstract method override |
| `backend/services/veli_service.py:137, 153, 274` | **3 parent service methods unimplemented** — HIGH for parent role |
| `backend/repositories/base.py:136` | Abstract base — OK |
| `backend/mcp_servers/zemberek_nlp/tools/base.py:170` | Abstract tool method — OK |

---

## Frontend Half-Done

### Stub Hooks (WebSocket placeholders)
- `frontend/src/services/chatService.ts:460` — "No-op: chat WebSocket endpoint not implemented"
- `frontend/src/services/examService.ts:573` — "No-op: /ws/exam/* endpoint not implemented; exam uses polling"
- `frontend/src/services/multiAgentService.ts:347` — "No-op: /api/v1/multi-agent/ws/* endpoint not implemented"

### Direct TODOs
- `frontend/src/components/Exam/OSYMExamInterfaceRefactored.tsx:151` — "Wire this to the exit confirmation dialog"
- `frontend/src/pages/FSRSReviewPage.tsx:143` — "implement correct answer highlighting" (currently `void _isCorrectOpt` — variable computed and discarded)

### ComingSoon Component
- `frontend/src/components/Common/ComingSoon.tsx` — defined and exported, **zero usage in non-self imports**. Built-in scaffold for unimplemented features but never wired up.

---

## Active Investigation / WIP (Pilots)

`backend/_pilots/` has **201 files** total (`57 .py scripts + 49 RESULT.md`), of which **12 are untracked** at audit time:

```
?? backend/_pilots/HIGH_tier_deep_audit_25k.py
?? backend/_pilots/_tmp_view2.sql
?? backend/_pilots/beta_password_test.py
?? backend/_pilots/beta_users_verify.py
?? backend/_pilots/beta_users_verify_RESULT.md
?? backend/_pilots/bug_5_sample_check.out
?? backend/_pilots/deep_correctness_audit_v2.py
?? backend/_pilots/final_correctness_audit.py
?? backend/_pilots/nuke_pool.out
?? backend/_pilots/strict_correctness_audit_10k.py
?? backend/_pilots/wrong_case_deep_dive.py
?? backend/_pilots/20260519_beta_flag_resolver_dryrun_RESULT.md
```

Also stashed (git stash):
1. `stash@{0}: On master: pre-yolo checkpoint`
2. `stash@{1}: On master: frontend_tests_unknown_origin_20260422`
3. `stash@{2}: WIP on clean-main: 4f11966 chore: update claude settings`

---

## Migration Backlog

### Alembic — 63 migrations + 2 disabled
**Disabled:**
- `20260126_additional_performance_indexes.py.disabled`
- `cc2ead85e242_merge_cascade_and_irt_heads.py.disabled`

**Recent stack:**
1. `curator_audit_20260521.py` (HEAD)
2. `20260518_student_flags_unique.py`
3. `20260517_student_question_flags.py`
4. `20260514_quality_review_status_v3_bronze.py`
5. `20260515_quality_review_status_v2_convention.py`

### ORM Schema Drift Backlog
Per `docs/audits/2026-04-12_orm-schema-drift-baseline.md` (Session 155):
- **203 HIGH** — ORM declares column missing in DB
- **455 MEDIUM**, **206 LOW**

**Three clusters:**

#### Cluster 1 — University-info (140 findings / 8 tables, COLD)
`dormitory_info`, `scholarship_programs`, `city_living_costs`, `campus_info`,
`career_opportunities`, `department_curricula`, `salary_expectations`,
`sector_analyses` — ORM models written but Alembic migration never executed.
Recommended action: single batch migration.

#### Cluster 2 — Inverse rule-of-seven (41 findings / 22 tables, PRODUCTION-CRITICAL)
ORM declares VARCHAR while DB is UUID. Tables with real data:
- `kiro2_learning_events` — 243 rows
- `topic_prerequisites` — 106 rows
- `kiro2_cat_sessions` — 8 rows
- `osym_questions` — many rows

Currently working via raw SQL or `str(uuid)` shim. Any ORM-as-declared INSERT will trip `DatatypeMismatchError`. Each fix is one-line.

#### Cluster 3 — int-vs-string (4 findings / 2 tables)
`badges.id`, `user_badges.id`, `user_badges.badge_id` — ORM Integer, DB varchar.
Badges feature half-wired (5 seeded, 0 user_badges).

### Faz 3.6 Schema Drift (latest.md L46)
- `reviewed_at` column missing in DB — only JSON-embedded. Pending separate migration.

---

## Feature Flags Inventory

### Backend (off-by-default)
- `FEATURE_2FA_ENABLED` (default false) — `api/two_factor_auth_api.py:24`
- `LEARNING_PATH_VERBOSE_LOGGING` (default false) — `agents/learning_path/config.py:145`
- `ENABLE_STREAMING` (default false) — `core/langchain_llm_service.py:82`

### Backend (on-by-default)
- `ENABLE_MONITORING`, `ENABLE_REDIS_CACHE`, `ENABLE_CIRCUIT_BREAKER`, `ENABLE_RESOURCE_RANKING`, `ENABLE_LEARNING_STYLE_DETECTION`, `ENABLE_LLM_CACHE`, `SENTRY_ENABLE_TRACING`, `ENABLE_QUERY_LOGGING`, `ENABLE_N_PLUS_ONE_DETECTION`

### Frontend
- `VITE_ENABLE_ANALYTICS`, `VITE_ENABLE_DEBUG`, `VITE_ENABLE_WEBSOCKET` — only consumed in `components/Examples/DashboardWithErrorHandling.tsx` (example component, **not in production paths**)

**Observation:** Frontend feature-flag system has minimal real use. Flag exists but no production component reads it. Either remove or wire to actual gates.

---

## Documentation Gaps

### API Docstring Coverage (sample)
| File | Functions | Endpoints | Docstrings |
|---|---:|---:|---:|
| `backend/api/admin.py` | 18 | 17 | 19 (good) |
| `backend/api/analytics.py` | 41 | 8 | 51 (good — but content is wrong, mocks) |
| `backend/api/content_management.py` | 20 | 19 | 20 (good — but content is wrong, mocks) |
| `backend/api/advanced_reports.py` | 23 | 7 | 30 (good) |
| `backend/api/agents.py` | 2 | 2 | 2 (good) |

**Sample finding:** Files have docstrings but content lies (says "production DB query" while body is mock).

### Other doc gaps (qualitative)
- No README.md under most subfolders (`backend/services/`, `backend/api/`, `frontend/src/components/`)
- 19 HTTP 501 endpoints have no centralized "feature roadmap" document
- Schema drift remediation has baseline doc but no per-cluster tracking issue

---

## Recommendations

### P0 — Blocking Beta Launch
1. **Replace `api/analytics.py` 24 mocks with real DB queries** — beta testers will see fake "15,247 active users" and lose trust.
2. **Replace `api/content_management.py` 43 mocks** — admin UI fundamentally broken for Curator workflow handoff.
3. **`services/ai_chat_service.py` and `api/bilge_alp.py` mock fallback** — see also silent_failures SF-6. Decide: gate behind feature flag OR remove the endpoint until real LLM wired.
4. **Quality Hardening Task 6 + Task 7** — fetch→apiClient + Redis rate limiter — track-able sprint items.
5. **R1 legacy_v3 FN restore apply** — single human verification step blocking 15,321 row restore.

### P1 — Important Tech Debt
1. **20 `_deprecated/` pages still referenced** — either revert from `_deprecated/` or fix all 20+ imports. Violation of `deprecation-guard.md`.
2. **Cluster 2 schema drift (22 tables, 41 findings)** — 22 production tables where the next ORM-declared INSERT will crash. One-line fixes each.
3. **Celery task stack 5 files / 16 TODOs** — every Celery task is a stub. Schedule a job → nothing happens. Either implement or remove the scheduling endpoints.
4. **`enhanced_auth_api.py` 7 TODOs** — security UI showing fabricated session/device data. Either implement or hide these UI panels.
5. **3 stashed WIP** — review `stash@{0}` pre-yolo, `stash@{1}` frontend_tests, `stash@{2}` clean-main. Drop or apply.
6. **2 disabled migrations** — decide: re-enable or delete `20260126_additional_performance_indexes` and `cc2ead85e242_merge_cascade_and_irt_heads`.
7. **`veli_service.py` 3 NotImplementedError** — parent-role service has unimplemented methods.

### P2 — Nice-to-Have
1. **Cluster 1 schema drift (140 findings, 8 cold tables)** — one batch migration once university-info feature is greenlit.
2. **Cluster 3 int-vs-string (4 findings)** — fix when badges feature is unblocked.
3. **`services/irt_analysis_service.py` repository pattern** — 7 TODOs reference a never-built `SoruRepository`. Either build or remove the TODOs.
4. **`tasks/email_tasks.py` SendGrid/SES integration** — `auth.py:1330` password reset email also blocked on this. 3+ TODOs reference unbuilt email service.
5. **`ComingSoon` component unused** — wire to 501 endpoints or remove.
6. **`# type: ignore` 93 + `# noqa` 172** — periodic cleanup sprint.
7. **`@pytest.mark.skipif(True)` 19 files** — review and either un-skip or delete.

---

## Methodology Notes

- **TODO/FIXME/HACK/XXX raw counts misleading:** raw `grep -rn` returned 30/559/1503/119 for backend, but after excluding `venv/`, `site-packages/`, and `backend/hooks/reward_hacking/` (which scans for these as detection patterns), the real production debt is **55 TODO / 0 FIXME / 0 HACK / 1 XXX**.
- **Mock-in-production confirmed via context read**, not just grep — `analytics.py:200-208` and `content_management.py:50-75` quoted above.
- **`_deprecated` reference checking** done by extracting basename and grepping non-deprecated `frontend/src/` — caught the 20 leaked refs.
- **Pilot/stash status** is point-in-time (`git status` + `git stash list` at audit start).
- **Read-only audit** — no files modified.
