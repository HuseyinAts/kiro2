# KIRO2 Documentation Quality Audit

**Date:** 2026-05-21
**Scope:** Inline docs, OpenAPI, architecture, runbooks, onboarding, freshness
**Method:** Live OpenAPI fetch + AST-based docstring analysis + filesystem inventory + git log analysis
**Status:** READ-ONLY. No files modified.

---

## TL;DR

| Area | Status | Reality |
|---|---|---|
| OpenAPI summary/tags | EXCELLENT | 100% / 100% |
| OpenAPI description | GOOD | 96% (35 endpoints missing) |
| Backend docstring (api/services/core/algorithms) | GOOD | 86-93% overall |
| Frontend JSDoc presence | GOOD | 642/706 files (91%) |
| Architecture diagrams | OK | 12 mermaid blocks in 2 files, but ALL diagrams stale (>6 months) |
| Runbook | PARTIAL | 1 file (health monitoring only, 363 lines) |
| Onboarding | OK | quickstart.md (488 lines) + contributing.md (665 lines) |
| README freshness | **STALE / DRIFT** | Last modified 2026-01-25; claims wrong numbers |
| docs/index.md | **STALE** | Last modified 2025-11-12 (~6 months old) |
| docs/architecture/ | **STALE** | 4/4 files from Mar 2026 or older |
| CLAUDE.md endpoint count | **WRONG** | Claims 124+, reality 1,163 (~9.4x off) |
| README test coverage | **WRONG** | Claims 97%, reality ~53% |
| .claude/rules/ | EXCELLENT | 12 files, 1869 lines, actively maintained |
| Doc/code commit ratio (14d) | OK | 37/115 = 0.32 (above 0.20-0.30 target — acceptable) |

**Critical findings:** 3 P0 (numerical drift in README/CLAUDE), 4 P1 (stale architecture, stale top-level READMEs), 5 P2 (orphan worktree READMEs, conventions).

---

## 1. API Documentation Completeness

**Source:** `curl http://localhost:8000/openapi.json` (live backend, 2026-05-21)
**File size:** 1,372,496 bytes

| Metric | Count | % |
|---|---|---|
| Total endpoints | 1,163 | 100% |
| With summary | 1,163 | 100% |
| With tags | 1,163 | 100% |
| With description | 1,128 | 96% |
| Missing description | 35 | 4% |
| Very short description (<15 chars) | 7 | 0.6% |

### Missing descriptions — by router prefix

| Count | Prefix |
|---|---|
| 13 | `/api/v1/teacher` |
| 5 | `/api/v1/admin` |
| 4 | `/api/v1/fsrs` |
| 3 | `/api/v1/placement` |
| 3 | `/api/v1/dag` |
| 2 | `/api/v1/cat` |
| 2 | `/api/v1/estimate` |
| 1 | `/api/v1/enhanced-chat` |
| 1 | `/api/v1/calibration` |
| 1 | `/api/v1/billing` |

### Sample missing-description endpoints

```
POST   /api/v1/placement/start                       (summary: "Placement test başlat")
POST   /api/v1/placement/{session_id}/answer         (summary: "Placement yanıtı gönder")
GET    /api/v1/placement/{session_id}                (summary: "Placement oturum durumu")
GET    /api/v1/fsrs/due                              (summary: "Vadesi gelen tekrar kartlarını getir")
POST   /api/v1/fsrs/review                           (summary: "Standalone tekrar yanıtla (CAT dışı)")
GET    /api/v1/fsrs/due-count                        (summary: "Vadesi gelen kart sayısı (hızlı)")
GET    /api/v1/fsrs/stats                            (summary: "Öğrencinin FSRS istatistikleri")
GET    /api/v1/cat/sessions/{session_id}             (summary: "Oturum durumunu getir")
DELETE /api/v1/cat/sessions/{session_id}             (summary: "Oturumu iptal et")
GET    /api/v1/dag/topics/{topic_id}/path            (summary: "Hedefe giden öğrenme yolu")
GET    /api/v1/dag/subjects/{subject_id}/next        (summary: "Sıradaki önerilen konu")
GET    /api/v1/dag/topics                            (summary: "Tüm konular (topolojik sırayla)")
GET    /api/v1/estimate/ayt/{puan_turu}              (summary: "AYT puan tahmini")
GET    /api/v1/estimate/full                         (summary: "Tam YKS tahmin raporu")
POST   /api/v1/enhanced-chat/bionic-reading          (summary: "Bionic Reading Enhanced Chat")
```

**Verdict:** All missing-description endpoints HAVE meaningful summaries. Risk is low: clients see summary in OpenAPI UI. P2 cleanup task — extend top 10 high-traffic endpoints with description.

---

## 2. Docstring Coverage (Backend Python)

**Method:** AST-based analysis (`ast.get_docstring`). Skipped `__pycache__`, `_deprecated`, `venv`, `node_modules`, `.migration-backup`, `worktrees`.

| Directory | Files | Parse err | Modules | Classes | Functions | Overall |
|---|---|---|---|---|---|---|
| `backend/api/` | 150 | 0 | 98% (148/150) | 74% (515/694) | 96% (1408/1462) | **89%** |
| `backend/services/` | 201 | 1 | 97% (194/200) | 96% (370/382) | 92% (2079/2242) | **93%** |
| `backend/core/` | 248 | 0 | 100% (248/248) | 97% (952/972) | 86% (3753/4351) | **88%** |
| `backend/algorithms/` | 15 | 0 | 100% (15/15) | 98% (70/71) | 91% (200/218) | **93%** |
| `backend/models/` | 80 | 0 | 97% (78/80) | 98% (415/423) | 58% (86/147) | **89%** |
| `backend/api/schemas/` | 9 | 0 | 100% | 100% | 96% | **99%** |
| `backend/app/schemas/` | 3 | 0 | 66% | 0% | 100% | **15%** |
| `backend/core/middleware/` | 6 | 0 | 100% | 78% | 78% | **80%** |
| `backend/app/api/` | 10 | 0 | 90% | 11% | 21% | **28%** |
| `backend/tasks/` | 13 | 0 | 100% | 100% | 98% | **98%** |
| `backend/scripts/` | 183 | 0 | 100% | 65% | 58% | **64%** |
| `orchestrator/` | 48 | 0 | 97% | 100% | 80% | **86%** |

### Observations
- **Excellent:** `backend/api/`, `backend/services/`, `backend/core/`, `backend/algorithms/`, `backend/api/schemas/`, `backend/tasks/` all >85%.
- **Weak spots:**
  - `backend/app/schemas/` (15%) — but only 3 files, low impact
  - `backend/app/api/` (28%) — 10 files, low priority (orphan / experimental layer)
  - `backend/models/` functions only 58% — Pydantic-style property/validator functions often skipped
- **Single parse error** in `backend/services/` (encoding issue) — should be tracked down
- Algorithm docstrings include detailed context (e.g., `irt_model.py` has docstring "4-Parametreli IRT Model... YKS/TYT/AYT standardizasyonu, MEB müfredatı alignment").

### Algorithm-specific spot checks (head docstrings)
- `backend/algorithms/irt_model.py` — 14-line module docstring + class docstring with parameter ranges ✓
- `backend/services/bkt_service.py` — BKT+ZPD docstring, references FAZ-1 Görev 1.4 ✓
- `backend/algorithms/turkish_optimized_fsrs.py` — 11-line module docstring describing 17-parameter FSRS + Turkish cultural factors ✓

---

## 3. Frontend JSDoc / Inline Comments

**Method:** `grep -l "/\*\*"` per directory.

| Directory | Files | With JSDoc | % |
|---|---|---|---|
| `frontend/src/services/` | 41 | 39 | 95% |
| `frontend/src/hooks/` | 45 | 44 | 98% |
| `frontend/src/store/` | 8 | 8 | 100% |
| `frontend/src/pages/` | 108 | 103 | 95% |
| `frontend/src/utils/` | 24 | 23 | 96% |
| `frontend/src/components/` | 401 | 350 | 87% |
| **Total (all .ts/.tsx)** | **706** | **642** | **91%** |

**Verdict:** Frontend JSDoc presence is strong. Component coverage is lower (~87%) — this is the only minor gap. Note: `grep "/**"` only counts presence of at least one block, not per-function/class coverage. Real per-function frontend coverage was not measured (no equivalent of `interrogate` for TypeScript was used).

---

## 4. README Inventory

### Root-level (KIRO2-owned, no node_modules/worktrees)

| Path | Last modified | Size | Lines | Status |
|---|---|---|---|---|
| `README.md` | **2026-01-25** | 29,524B | 924 | **STALE — wrong metrics (see §10)** |
| `backend/README.md` | 2026-03-13 | 1,718B | 54 | OK — test stratification doc |
| `orchestrator/README.md` | 2026-03-31 | 847B | ~30 | OK — accurate (24 modules, 45 policies, 20 agents) |

### Backend submodule READMEs (28 files)

```
backend/api/README_ADHD_SUPPORT.md
backend/api/README_MANIPULATIVES.md
backend/coverage_reports/README.md
backend/deployment/README.md
backend/docs/README.md
backend/hooks/README.md
backend/mcp_servers/zemberek_nlp/README.md
backend/migrations/README.md
backend/models/README_QUESTION_BANK.md
backend/scripts/README.md
backend/services/nlp_training/README.md
backend/services/README_enhanced_recommendation_engine.md
backend/services/README_error_handlers.md
backend/services/README_health_check_service.md
backend/services/README_OSYM_SCORING.md
backend/services/README_QUESTION_CRUD.md
backend/services/README_question_generation_engine.md
backend/services/README_SIMILAR_QUESTIONS.md
backend/services/README_soru_bankasi.md
backend/services/README_turkish_content_filter.md
backend/services/README_video_recommendation_monitoring.md
backend/services/README_video_recommendation_service.md
backend/services/README_VIDEO_SOLUTION.md
backend/tasks/README.md
backend/tests/{accessibility,contract,load,smoke,unit}/README.md (+ 4 specialty)
backend/tests/property/README_ZPD_PROPERTIES.md
backend/tests/README.md
backend/_pilots/README.md
backend/alembic/README
```

Mix of canonical (e.g., `README_QUESTION_BANK.md` describing 77K production data) and feature-specific (`README_OSYM_SCORING.md`). No automated freshness check applied per-file — sample inspection shows backend/README.md is current; submodule READMEs vary.

### Frontend READMEs (after excluding node_modules / dist)

```
frontend/public/fonts/README.md
frontend/src/assets/README.md
frontend/tests/README.md (404 lines, test suite documentation)
```

Frontend has very little inline README documentation — only 1 substantive file (tests). Components rely on JSDoc instead, which is OK.

### Worktree pollution

`.claude/worktrees/upbeat-haslett/` is a stale git worktree containing ~50 duplicated READMEs (mirror of main repo). **P2:** consider removing this worktree or `.gitignore` it.

---

## 5. Architecture Diagrams

### Inventory

| File | Last modified | Format | Mermaid blocks |
|---|---|---|---|
| `docs/architecture/overview.md` | **2025-11-12** | Markdown + Mermaid | 12 |
| `docs/index.md` | **2025-11-12** | Markdown + Mermaid | mentioned (count not enumerated) |
| `docs/architecture/ARCHITECTURE_REPORT_2026-03-26.md` | 2026-03-26 | Markdown | – |
| `docs/architecture/STRATEGIC_PLAN_2026-03-26.md` | 2026-03-26 | Markdown | – |
| `docs/architecture/ACTION_PLAN_2026-03-26.md` | 2026-03-26 | Markdown | – |
| `docs/health/architecture.md` | – | Markdown | – |
| `backend/docs/ARCHITECTURE.md` | **2025-11-01** | Markdown | – |
| `backend/docs/ARCHITECTURE_DIAGRAM.md` | **2025-11-01** | Markdown | – |

**No** `.drawio`, `.dio`, `.puml`, or standalone `.mmd` files found.

### Findings

- **All architecture documents are 2+ months stale.** Most recent is 2026-03-26 (~2 months). `overview.md` and `docs/index.md` haven't been touched since Nov 2025 — **6+ months old**.
- 12 Mermaid blocks in `overview.md` documenting client layer, gateway, app layer, etc. — these likely no longer match reality (CLAUDE.md says orchestrator v2.5.0, but overview.md predates it).
- Architecture report from 2026-03-26 may not reflect Wave 11-16 Golden Flow work, Faz 5+6 rule-based filtering, Curator UI (Session 178).

**P1:** Refresh `docs/architecture/overview.md` with current state (orchestrator v2.5.0, 1,163 endpoints, Curator UI, Phase 7 LLM rationale completion).

---

## 6. CLAUDE.md / MEMORY.md / Rules

### Sizes

| File | Lines | Bytes | Last modified |
|---|---|---|---|
| `CLAUDE.md` | 841 | 34,859 | 2026-05-15 |
| `CLAUDE.local.md` | 371 | 16,346 | 2026-05-02 |
| `~/.claude/projects/.../MEMORY.md` | 299 | 75,110 | 2026-05-21 |
| `.claude/sessions/latest.md` | 60 | 3,031 | 2026-05-21 |

### CLAUDE.md structure

- **25 top-level `##` sections** (Karpathy Foundation, Session, Pre-flight, Testing, Debugging, Git, Project Overview, Tech Stack, etc.)
- **47 `###` subsections**
- Very dense, well-organized. Versioned (v3.6).

### MEMORY.md

- 75KB single file — system warns it's over the 200-char-per-entry guideline
- Contains topic-file index but most content is inlined
- Recent updates: Session 178 dated 2026-05-21

### .claude/rules/ (12 files, 1869 total lines)

| File | Lines | Topic |
|---|---|---|
| `testing.md` | 646 | 30 documented lessons (Sessions 11, 17, 78, 120, 121) |
| `verification.md` | 201 | Boris Cherny standards + Karpathy lessons |
| `systematic-debugging.md` | 175 | Phantom sorun filter + Docker vs local |
| `security.md` | 160 | OWASP + KIRO2 specifics |
| `case-convention.md` | 153 | Turkish case convention + subject_db/subject_key |
| `golden-flows.md` | 145 | GF1-GF8 read-path + 16 wave history |
| `audit-methodology.md` | 129 | Audit truncation lesson (Session 156) |
| `middleware.md` | 93 | HTTPException-in-middleware lesson (GF99) |
| `path-naming.md` | 79 | TR/EN duplicate endpoint ban |
| `deprecation-guard.md` | 39 | Pre-move import-tarama checklist |
| `debugging-first.md` | 26 | Root Cause Analysis table gate |
| `plan-before-execute.md` | 23 | 3+ file change gate |

**Verdict:** `.claude/rules/` is **the gold standard** of the docs ecosystem. Actively maintained, evidence-based, references specific incidents/sessions. This is excellent.

---

## 7. Runbook / Incident Response

### Found

| File | Lines | Scope |
|---|---|---|
| `docs/health/runbook.md` | 363 | Health monitoring runbook — alert response protocol, troubleshooting |

### Missing

- No incident response playbook (postmortem template, blast radius, declaration criteria)
- No on-call rotation doc
- No SEV-1/2/3 severity definition
- No runbook for database failures, Redis outage, deployment rollback, security incident

**P1:** Create at minimum:
- `docs/runbooks/database-failure.md` (PostgreSQL down, port 5434)
- `docs/runbooks/incident-response.md` (severity, escalation)
- `docs/runbooks/rollback.md` (Docker compose rollback, Alembic downgrade)

---

## 8. Onboarding Documentation

### Found

| File | Lines | Last modified | Content |
|---|---|---|---|
| `docs/getting-started/quickstart.md` | 488 | – | "Get started with Kiro2 in minutes!" |
| `docs/development/contributing.md` | 665 | – | "Contributing to Kiro2... this guide will help you get started" |
| `frontend/tests/README.md` | 404 | – | Frontend test suite docs |

### Other discovered docs

- `docs/BETA_LAUNCH_GUIDE.md` (May 2026, 5KB) — beta launch
- `docs/mvp-env-setup.md` (Mar 2026)
- `docs/CI_CD_SETUP_GUIDE.md` (Sep 2025) — likely stale
- `docs/GEMINI_3_MCP_SETUP.md` (Nov 2025)
- `docs/claude-code-cheatsheet.md` (Feb 2026)

**Verdict:** Onboarding exists but is spread across multiple files with overlapping/competing scope. **P2:** consolidate into single onboarding entrypoint.

---

## 9. .env.example Files

| Path | Purpose |
|---|---|
| `.env.example` | Root |
| `.env.expert-agents.example` | Expert agents config |
| `.env.mcp.example` | MCP servers |
| `.env.mvp.example` | MVP launch |
| `backend/.env.example` | Backend |
| `backend/.env.zemberek.example` | Zemberek NLP |
| `frontend/.env.example` | Frontend (Vite) |
| `.claude/files/01_documentation/.env.example` | Claude tooling |
| `.claude/files/07_configuration/.env.example` | Claude config |

**9 .env.example files.** Good coverage. Mirror to real `.env` not verified (would require live diff which user can run).

---

## 10. CHANGELOG / Release Notes

| Path | Status |
|---|---|
| `archive/obsolete/CHANGELOG.md` | **Archived as obsolete** |
| `.github/workflows/release.yml` | CI workflow exists |
| `backend/db/history` | Schema history |

**No active CHANGELOG.md, HISTORY.md, or RELEASE_NOTES.md** in repo root. The `.claude/sessions/latest.md` (60 lines) and MEMORY.md serve as informal handoff/changelog mechanism.

**P2:** Decide if KIRO2 needs a proper CHANGELOG.md for beta launch communication. Given v2.0.0 badge in README, a versioned changelog would be expected.

---

## 11. Doc / Code Freshness (last 14 days)

| Metric | Count |
|---|---|
| Doc commits (`docs/`) | 37 |
| Code commits (`backend/`) | 115 |
| Code commits (`backend/api/`) | 6 |
| Code commits (`backend/services/`) | 5 |
| docs/audits/ commits | 10 |
| **Doc/code ratio** | **0.32** (target 0.20-0.30) |

**Verdict:** Doc-to-code commit ratio is **slightly above** the healthy band. This is GOOD for an audit-heavy phase. The bulk of code commits (115) come from non-`api/services` files — likely tests, scripts, migrations.

### Audit reports

- 24 dated audit reports in `docs/audits/` matching `2026-*.md` pattern
- 20 audit files in `docs/audits/2026-05-21_full_audit/` (current session)
- **30 audit files >30 days old, 21 audit files <14 days old**
- `docs/audit/` (legacy, distinct from `docs/audits/`) has 11 files — pre-March 2026 audit phase

---

## 12. Numeric Drift — README and CLAUDE.md vs Reality

### Critical drift items

| Source | Claim | Reality | Drift |
|---|---|---|---|
| `README.md:12` | Coverage 80% (badge) | ~53% backend | **P0** — 27pp off |
| `README.md:601-602` | Tam Kontrol Listesi 97.0% / Entegrasyon 97.0% | Backend coverage ~53% | **P0** — misleading |
| `README.md:619` | Test Kapsamı %97 entegrasyon | ~53% | **P0** |
| `README.md:638` | Test Coverage Target >95% / Current 97.0% / Status ✅ | ~53%, marked ❌ | **P0** |
| `README.md:10` | Version 2.0.0 (badge) | Not validated against package.json/pyproject | **P3** |
| `CLAUDE.md:242` | API Routers — FastAPI, 124+ endpoint | 1,163 endpoints live | **P0** — 9.4x off |
| `CLAUDE.md:331` | api/ — FastAPI routers (124+ endpoints) | 1,163 | **P0** — same drift |

### Verified consistent items

| Claim | Verified |
|---|---|
| CLAUDE.md: 77,336 production questions (v3.5+) | ✓ matches MEMORY.md |
| CLAUDE.md: PostgreSQL 15, port 5434 | (not externally verified in this audit) |
| CLAUDE.md: orchestrator v2.5.0, 24 modules, 45 policies, 20 agents | ✓ matches `orchestrator/README.md` |
| CLAUDE.md: 80 README files (backend) | not explicitly verified, but inventory shows ~28 backend READMEs (which may not include subdirectories) |
| CLAUDE.md: backend test coverage ~53% | ✓ Self-consistent |

### Worst offender

`README.md` (last modified **2026-01-25** — ~4 months stale) is the **most damaging stale doc**. It is the first thing new contributors see; it claims 97% test coverage and 80% coverage badge, both inflated. The README also claims Teknofest 2025 readiness with green CI badges — these may be accurate but cannot be assumed from this audit.

---

## 13. .claude/sessions/ — Handoff docs

| File | Lines | Last modified |
|---|---|---|
| `latest.md` | 60 | 2026-05-21 (Session 178) |

Active session handoff exists, well-formatted with branch, commit, completed/blocked/next sections. This is the de-facto progress doc.

---

## 14. Pydantic Schema / Middleware

| Directory | Files | Notes |
|---|---|---|
| `backend/api/schemas/` | 9 | 99% docstring coverage ✓ |
| `backend/app/schemas/` | 3 | 15% — but only 3 files |
| `backend/app/middleware/` | (empty, no .py files at top level) | – |
| `backend/core/middleware/` | 6 | 80% coverage |
| `backend/middleware/` | (empty, no .py files at top level) | – |
| `backend/_deprecated/middleware/` | – | excluded |

**Architectural smell:** Schemas/middleware split across `app/`, `core/`, top-level. Inconsistent. **P2:** consolidate or document the layered intent.

---

## Findings

### P0 — Critical (fix this week)

1. **README.md test coverage claim is wrong** (97% claimed, ~53% reality). 4 specific lines need correction (lines 12, 601-602, 619, 638). High-visibility doc.
2. **CLAUDE.md "124+ endpoint" claim** (lines 242, 331). Reality: 1,163. Off by ~9.4x. CLAUDE.md is loaded into every agent context — wrong numbers propagate.
3. **README.md Coverage badge** (line 12) shows 80% green — at minimum demote to "in progress" or update to actual figure.

### P1 — Important (fix this sprint)

4. **Architecture docs are 2-6 months stale.** `docs/architecture/overview.md` (Nov 2025), `backend/docs/ARCHITECTURE.md` (Nov 2025), `docs/index.md` (Nov 2025) all predate orchestrator v2.5.0, Curator UI, Phase 7 LLM completion, and Wave 16 saturation.
5. **No incident response runbook.** Only `docs/health/runbook.md` (health monitoring). Missing: DB failure, Redis outage, rollback, security incident.
6. **35 OpenAPI endpoints lack `description`** (only `summary`). Top affected: `/api/v1/teacher` (13), `/api/v1/admin` (5), `/api/v1/fsrs` (4).
7. **`docs/index.md` predates everything (Nov 2025)** — first doc shown to readers via mkdocs/etc, but content is ~6 months out of date.

### P2 — Cleanup (fix next month)

8. **Onboarding docs scattered:** `getting-started/quickstart.md` + `development/contributing.md` + `BETA_LAUNCH_GUIDE.md` + `mvp-env-setup.md`. Consolidate into single onboarding entrypoint with clear "Start here" link.
9. **Orphan worktree** `.claude/worktrees/upbeat-haslett/` duplicates ~50 READMEs. Either gitignore or remove.
10. **`backend/app/api/`** (10 files, 28% docstring) and **`backend/app/schemas/`** (3 files, 15%) look like orphan/experimental layers — clarify intent or delete.
11. **No active CHANGELOG.md** — only `archive/obsolete/CHANGELOG.md`. Given v2.0.0 versioning, add release notes for beta.
12. **One parse error** in `backend/services/` (encoding issue) — find and fix.

### P3 — Nice to have

13. **Mermaid diagram refresh** — 12 blocks in `overview.md` likely reference deleted/renamed components.
14. **Per-function frontend coverage** (current measure only counts file-level JSDoc presence).
15. **CLAUDE.md backups** — `CLAUDE.local.md.bak-20260427.md` referenced in CLAUDE.local.md but not verified to exist.
16. **CI_CD_SETUP_GUIDE.md** (Sep 2025) is 8 months old — verify accuracy or delete.

---

## What's Working Well

- **`.claude/rules/`** — 12 rule files, 1869 lines, actively maintained, evidence-based with session references
- **`.claude/sessions/latest.md`** — handoff doc kept current
- **OpenAPI summary/tags** — 100% coverage
- **Backend docstring coverage** — 86-93% for major directories
- **Frontend JSDoc presence** — 91% of TS/TSX files
- **Algorithm files** — well-documented module headers (IRT, BKT, FSRS)
- **Audit cadence** — 20 audit files generated for current session alone, regular sweeps
- **.env.example coverage** — 9 .env templates across project

---

## Methodology

- **OpenAPI:** Fetched live from `http://localhost:8000/openapi.json` (1.37MB).
- **Docstring coverage:** Custom Python AST walker (interrogate failed on BOM/encoding). All `*.py` files in target directory, excluding `__pycache__`, `_deprecated`, `venv`, `node_modules`, `.migration-backup`, `worktrees`.
- **JSDoc presence:** `grep -l "/\*\*"` — counts files with at least one JSDoc block, not per-function coverage.
- **Architecture inventory:** Filesystem search for `.drawio`, `.dio`, `.mmd`, `.puml`, `architecture*.md` + Mermaid block grep.
- **Freshness:** `git log --since="14 days ago"` for commit counts; `stat -c '%y'` for filesystem mtimes.
- **README inventory:** `find -name "README*.md"` with strict exclusion of `node_modules`, `.git`, `_deprecated`, `worktrees`, `dist`, `venv`, `_pilots`, `.pytest_cache`.

**Limitations:**
- Frontend per-function JSDoc coverage not measured (only file-level presence).
- README content quality (e.g., are links live, do code blocks compile) not validated.
- `.env.example` ↔ real `.env` field alignment not verified (real `.env` not read for security).
- Git log "doc commits" treats all `docs/` commits equally (no severity weighting).
- 1 single `backend/services/` file failed AST parsing (encoding) and is invisible to this audit.
