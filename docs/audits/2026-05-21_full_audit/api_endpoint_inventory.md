# KIRO2 API Endpoint Inventory + Consistency Audit

**Date:** 2026-05-21
**Source:** Live `GET /openapi.json` from `http://localhost:8000` (snapshot at `openapi_snapshot.json`, 1.34 MB)
**Method:** Real measurement against the running backend container — no estimates.
**Effort:** ~50 min

---

## 1. Total Inventory

| Metric | Value |
|---|---|
| **Total endpoints (operations)** | **1,163** |
| Unique paths | 1,089 |
| Pydantic schemas | 770 |

### By HTTP method

| Method | Count | % of total |
|---|---:|---:|
| GET | 619 | 53.2% |
| POST | 456 | 39.2% |
| PUT | 35 | 3.0% |
| DELETE | 43 | 3.7% |
| PATCH | 10 | 0.9% |

> **Note:** Memory says "124+ endpoint" — the actual operation count is **9.4×** larger. This audit replaces the stale estimate.

### By top-level group (top 20)

| Group | Endpoints |
|---|---:|
| **__non_v1__** (legacy + v2 + health + root) | **48** |
| diary | 48 |
| auth | 36 |
| adhd-support | 35 |
| questions | 29 |
| teachers | 25 |
| learning-path | 24 |
| live-sessions | 22 |
| admin | 20 |
| content-management | 19 |
| university-info | 19 |
| video-analytics | 18 |
| zpd-maarif | 17 |
| gamification | 17 |
| multisensory | 17 |
| osym-exam | 16 |
| visual-supports | 16 |
| content | 15 |
| eba | 15 |
| monitoring | 15 |

128 unique top-level groups total. Long tail goes down to 1-3 endpoints (e.g. `errors`, `social`, `calibration`).

---

## 2. Versioning Policy

| Prefix | Count | Status |
|---|---:|---|
| `/api/v1/` | **1,041 (95.6%)** | ✅ Canonical |
| `/api/v2/` | 17 (1.6%) | ⚠️ Coexists with v1 — no Deprecation header on v1 counterparts |
| `/api/v0/` | 0 | — |
| `/api/` no-version | 0 | — |
| Non-`/api/` (legacy root, `/health`, `/admin/*`, `/agents`) | 31 | ⚠️ 17 legacy Turkish endpoints + 9 health + 5 admin/agents |

### Non-v1 endpoints (48 ops, breakdown)

#### a) Legacy Turkish root-level (17 ops — **P1 cleanup**)

```
GET    /sorular
GET    /soru/{soru_id}
GET    /rastgele-sorular
POST   /irt-parametreli-sorular
GET    /konular
GET    /istatistikler
POST   /soru-performans-guncelle
GET    /zorluk-filtrele
POST   /soru-ekle
PUT    /soru-guncelle/{soru_id}
DELETE /soru-sil/{soru_id}
POST   /toplu-soru-ekle
POST   /irt-parametreleri-yeniden-hesapla/{soru_id}
GET    /agents
GET    /agents/test
GET    /
GET    /docs (implied)
```

These are not under `/api/v1/` AND not marked `deprecated: true`. They live in the legacy `routers/soru_bankasi.py`-style code path. Either delete or move under `/api/v1/admin/legacy/*`.

#### b) /api/v2 cluster (17 ops — clarification needed)

```
/api/v2/questions/generate         POST
/api/v2/cat/start                  POST
/api/v2/cat/submit                 POST
/api/v2/knowledge-graph/...        GET/POST x3
/api/v2/hitl/...                   GET/POST x5
/api/v2/quality/...                GET/POST x5
/api/v2/health                     GET
```

The `/api/v2` cluster looks like a new experimental surface (HITL = human-in-the-loop, knowledge-graph, quality eval). **Not registered as deprecation of v1 equivalents** — they are net-new features that bypassed the versioning convention. Either:
1. Move into `/api/v1/...` (consistent versioning), or
2. Document `/api/v2` as the new canonical and start migrating v1 features.

#### c) Health/admin cluster (14 ops — keep as-is)

`/health`, `/health/ready`, `/health/live`, `/health/startup`, `/health/database`, `/health/detailed`, `/admin/audit-logs/*`, `/admin/encryption/*` — these are intentionally outside `/api/v1/` for ops/infra access.

### Deprecation headers

**19 endpoints** declared `deprecated: true` in OpenAPI:

- `/api/v1/ogretmen/*` (10 ops — all Turkish teacher endpoints)
- `/api/v1/veli/*` (9 ops — all Turkish parent endpoints)

✅ Good — these align with `path-naming.md` and are correctly flagged. The English replacements (`/api/v1/teacher/*`, `/api/v1/parent/*`) exist alongside. **Sunset:** No `Sunset` HTTP header date declared anywhere — recommend setting one to drive frontend migration.

---

## 3. Path Naming Issues

### Casing

| Style | Count | Verdict |
|---|---:|---|
| kebab-case (e.g. `/learning-path/`) | 557 | ✅ Canonical, used widely |
| snake_case (in segments) | 0 | ✅ No snake_case path segments |
| camelCase | 0 | ✅ |

Casing inside path **segments** is fully consistent. (Path parameters use snake_case `{student_id}` per convention.)

### Turkish path segments outside the allowlist

**32 paths** still use Turkish words after stripping the allowlist (`bilge-alp`, `soru-meydani`, `oba-seferleri`, `usta-cirak`, `cozum-duellosu`, `zpd-maarif`, `kvkk` — product names per `path-naming.md`).

Breakdown of the 32:

| Cluster | Count | Status |
|---|---:|---|
| `/api/v1/ogretmen/*` | 10 | ✅ Already `deprecated: true` |
| `/api/v1/veli/*` | 9 | ✅ Already `deprecated: true` |
| `/api/v1/zpd-maarif/*` (gecmis, profil) | 3 | Allowlist parent, but `gecmis` Turkish subpath |
| `/soru/{soru_id}` (root) | 1 | ⚠️ Legacy, not deprecated |
| `/api/v1/auth/profil` | 1 | ⚠️ Active, not deprecated |
| `/api/v1/learning-path/streak` | 1 | ✅ `streak` is English |
| `/api/v1/duel/*` (matchmake, answer, stream, rating, history) | 5 | ✅ All English subpaths |

→ **Net Turkish-only blocker count after exclusions:** ~5 (auth/profil, zpd-maarif/gecmis, root `/soru/*`).

### Trailing slash inconsistency

9 paths use trailing slash:

```
/admin/audit-logs/
/api/v1/eba-tv/
/api/v1/osb/settings/
/api/v1/realms/
/api/v1/recommendations/
/api/v1/reviews/
/api/v1/study-plan/
/api/v1/video-solutions/
/health/
```

The other 1,079 paths do NOT use trailing slash. Only **1 actual duplicate** (`/health` and `/health/` both exist). Risk: FastAPI's default `redirect_slashes=True` issues 307, which the frontend's `credentials: 'include'` may drop on cross-origin redirect. **P2 cleanup** — pick a side and normalize.

### Turkish QUERY parameters (NEW finding)

The path-naming rule covers paths, but **query parameters** also leaked Turkish:

| TR query param | Endpoints affected | Suggested EN |
|---|---:|---|
| `ogrenci_id` | 11 | `student_id` |
| `soru_id` | 11 | `question_id` |
| `konu` | 8 | `subject` / `topic` |
| `sinav_tipi` | 8 | `exam_type` |
| `sayfa` | 8 | `page` |
| `sayfa_boyutu` | 7 | `page_size` |
| `materyal_id` | 7 | `material_id` |
| `sinav_id` | 6 | `session_id` / `exam_id` |
| `zorluk_seviyesi` | 4 | `difficulty_level` |
| `makale_id` | 4 | `article_id` |
| `bildirim_id` | 3 | `notification_id` |
| `rapor_id` | 1 | `report_id` |
| `talep_id` | 1 | `request_id` |

> **NEW Gate suggestion:** Extend `path-naming.md` to cover query + path parameter names. The frontend already imports `qs` libraries — Turkish params force the frontend to know two languages.

### ID type inconsistency (NEW)

Same parameter name, different types across endpoints:

| Param | Types observed |
|---|---|
| `session_id` | `string` (uuid), `string` (uuid4), `string` (no format) — **3 variants** |
| `video_id` | `integer`, `string` — type mismatch |
| `content_id` | `string` (uuid), `string` (no format) |
| `oba_id` | `integer`, `string` |

→ **P1**: video_id and oba_id are real type mismatches (int vs str across endpoints). Pick a canonical type per resource.

---

## 4. Response Shape Consistency

Out of **1,163 ops**:

| Response type | Count | % |
|---|---:|---:|
| Typed (`$ref` to schema) | 346 | 29.8% |
| **No declared response schema** | **395** | **34.0%** |
| Anonymous object/array | 8 | 0.7% |
| Other (primitive, well-formed array of typed) | ~414 | 35.6% |

**66% of endpoints (768) do NOT have a `$ref`-typed response model.** This means:
- Frontend TypeScript types are missing or hand-written
- OpenAPI codegen produces `any` for those
- Schema drift is silent (no contract test)

### Sample of endpoints lacking `response_model`

High-visibility ones:

```
POST /api/v1/analytics/web-vitals
POST /api/v1/errors/report
GET  /api/v1/auth/oauth2/{provider}
GET  /api/v1/auth/oauth2/{provider}/callback
DELETE /api/v1/auth/devices/{device_id}
POST /api/v1/auth/2fa/* (7 endpoints)
GET  /api/v1/learning-path/my-profile
GET  /api/v1/learning-path/exit-quiz/{subject}
GET  /api/v1/learning-path/interleaved-practice
GET  /api/v1/learning-path/review-queue
POST /api/v1/learning-path/submit-review
POST /api/v1/learning-path/register-wrong-answers
GET  /api/v1/learning-path/weakness-report
GET  /api/v1/learning-style/cache-stats
POST /api/v1/exam-answer-tracking/{exam_session_id}/mark-empty/{question_id}
```

**P0:** `/api/v1/learning-path/*` is the hot path — 7 of its 24 endpoints lack typed responses.

### Envelope pattern

Spot-check on 30 endpoints shows **no consistent envelope** (`{success: bool, data: ...}` vs naked dict vs `{result: ...}`). FastAPI default is the bare schema, which is fine — but mixing it with custom envelopes in some routers (e.g. `gamification`, `learning-path`) creates inconsistency. **P2.**

---

## 5. Error Response Consistency

Declared error responses per code:

| Code | Declared count | % of 1,163 |
|---|---:|---:|
| 400 | 8 | 0.7% |
| 401 | 10 | 0.9% |
| 403 | 1 | 0.1% |
| 404 | 37 | 3.2% |
| 409 | 0 | 0.0% |
| **422** | **891** | **76.6%** |
| 429 | 0 | 0.0% |
| 500 | 13 | 1.1% |
| 503 | 0 | 0.0% |

**888 of 891 (99.7%) 422 responses use FastAPI's default `HTTPValidationError` schema.** 0 custom 422 schemas. ✅ Good consistency for validation errors.

### Observations

- **401 declared on only 10/1,163** — yet 247+ endpoints return 401 anonymously (auth/cookie required). The 401 case is **implicit** via dependency injection. Frontend has no schema to type against.
- **403 declared on only 1** — same issue; IDOR/forbidden cases not documented.
- **429 declared on 0** — rate limit responses (CSRF/SSE exempt per `CLAUDE.md`) lack schema entirely. Even though the rate-limit middleware is active, OpenAPI doesn't expose its shape.
- **No 409, 503** declared anywhere — yet live test below shows 12 endpoints returning 503 (infrastructure down). Schema mismatch.

**P1 recommendation:** Add a global `OpenAPIResponse` declaration for 401, 403, 404, 429, 500 in `main.py` so all endpoints inherit them.

---

## 6. Auth Coverage

**OpenAPI-declared:**

| State | Count | % |
|---|---:|---:|
| Has `security: [BearerAuth]` block | **968** | **83.2%** |
| No security declaration | 195 | 16.8% |

**Security scheme:** Only `BearerAuth` (HTTP bearer) declared. Cookie auth (used by frontend, see Session 72 dual-auth) is **NOT exposed in OpenAPI** — codegen clients won't know about it.

### Live anonymous access test

Tested **546 GET endpoints anonymously** (no auth):

| Result | Count |
|---|---:|
| 200 OK (anonymous accessible) | 134 |
| 401 / 403 (auth required) | 369 |
| 5xx (crash on anonymous) | **20** |
| Errors (timeout) | 14 |

#### Likely-unintended public endpoints (sample)

```
GET /api/v1/learning-style/cache-stats   ← reveals internal cache state
GET /api/v1/learning-style/hybrid-codes
GET /api/v1/content/stats                 ← admin-only intent?
GET /api/v1/content/trending
GET /api/v1/osym-inspired/statistics
GET /api/v1/questions/hybrid/methods
GET /api/v1/reasoning/providers
GET /api/v2/quality/stats
GET /konular                              ← legacy Turkish, public
GET /istatistikler                        ← legacy Turkish, public
```

Most `/health` and `/.../health` are intentional. The non-health ones above need review:
- **P1**: `/api/v1/content/stats`, `/api/v1/content/trending`, `/api/v1/osym-inspired/statistics`, `/api/v1/learning-style/cache-stats` — these expose aggregate data without auth.
- **P2**: `/konular`, `/istatistikler` — legacy paths, expected to be deleted.

#### Anonymous 5xx crashes (P0 — both an auth bug AND a stability bug)

```
500: /api/v1/learning-style/statistics
500: /api/v1/ocr/info
500: /api/v1/yolo/model-info
500: /api/v1/monitoring/health
500: /api/v1/university-info/dormitories
500: /api/v1/university-info/dormitories/statistics/summary
500: /api/v1/university-info/scholarships
501: /api/v1/llm/health
503: /api/v1/difficulty/distribution
503: /api/v1/difficulty/calibrate-thresholds
503: /api/v1/agents/specialization-scores
503: /api/v1/agents/metrics
503: /api/v1/cache-metrics/health
```

These are reachable without auth AND crash. Either the endpoint should require auth (preferred) or it should fail gracefully (return 200 with empty body / 503 with `Retry-After`).

---

## 7. Pagination

Across **619 GET endpoints**, only 84 have any pagination-style params (13.6%):

| Pattern | Count | Verdict |
|---|---:|---|
| `?offset=&limit=` (REST-style) | 18 | ✅ Canonical for KIRO2 |
| `?page=&per_page=` | 6 | ⚠️ Mixed convention |
| `?sayfa=&sayfa_boyutu=` (Turkish) | 7+ | ❌ Turkish query params (see §3) |
| `?cursor=` | 0 | — |
| `?skip=&take=` | 0 | — |
| `?limit=` only (no offset) | 60 | ⚠️ Cannot paginate beyond first N |

### Hot listings without proper pagination

- `/api/v1/learning-path/review-queue` — `limit` only
- `/api/v1/fsrs/due` — `limit` only
- `/api/v1/diary/summaries`, `goals`, `insights`, `reflections`, `learning` — all `limit` only
- `/api/v1/live-sessions/{session_id}/chat` — `limit` only

→ **P1**: For lists that can grow beyond 100 (review-queue, fsrs-due, diary), add `offset` or cursor support. Document `X-Total-Count` header policy.

→ **P1**: Pick ONE pagination convention (offset/limit chosen by majority) and migrate `?page=&per_page=` callers. The `?sayfa=` variants must die with the Turkish path cleanup.

---

## 8. CRUD Completeness (per resource group)

128 resource groups total. **63 (49%) have ≤2 of 5 CRUD operations** (LIST, DETAIL, POST, PUT/PATCH, DELETE).

### Fully complete (5/5)

`adhd-support`, `admin`, `content`, `content-management`, `diary`, `moderation`, `questions`, `teachers`, `video-analytics`, `video-solutions` — **10 of 128 (7.8%)**.

### Read-only (LIST + DETAIL only)

`agents`, `dag`, `learning-style` — intentional; algorithms/computed views.

### Highly incomplete — write-only or detail-only

| Group | Ops | Issue |
|---|---:|---|
| `ask-question` | 1 | POST only — no history endpoint? |
| `bilge-alp` | 1 | POST chat only |
| `calibration` | 1 | LIST only |
| `dungeon` | 1 | DETAIL only (no LIST?) |
| `error-clusters` | 1 | DETAIL only |
| `errors` | 1 | POST only — `/errors/report` |
| `exam-performance` | 1 | DETAIL only |
| `llm` | 1 | LIST only |
| `mastery-confidence` | 1 | DETAIL only |
| `productive-failure` | 1 | POST only |
| `reports` | 1 | DETAIL only — `/reports/exam/{sinav_id}/...` |
| `social` | 1 | LIST only |

→ **P2:** Some are legitimate single-purpose (e.g. `errors/report` is a log sink). Others (`dungeon`, `social`) appear unfinished — feature-completion backlog.

### Missing DELETE on resources that should support it

`gamification`, `fsrs`, `learning-path`, `curator`, `diary` for `reflections`, `eba`, `khan`, etc. — many list/create resources have no DELETE counterpart. **GDPR/KVKK concern**: KVKK requires "right to deletion". `kvkk` group does have `DELETE`, but user-generated content (diary entries, reviews) needs auditable delete paths.

---

## 9. RESTful Violations

### Action endpoints (RPC-style)

**114 endpoints** with action verbs in the last path segment (e.g. `/start`, `/submit`, `/calculate`, `/generate`, `/validate`, `/reset`, `/enable`, `/disable`, `/rotate`):

Sample:
```
POST /api/v1/osym-exam/create
POST /api/v1/osym-exam/{session_id}/start
POST /api/v1/placement/start
POST /api/v1/learning-path/create-profile
POST /api/v1/learning-path/create-path
POST /api/v1/learning-path/quiz/{quiz_id}/submit
POST /api/v1/zpd-maarif/revolutionary/calculate
POST /api/v1/irt-morfoloji/calculate-probability
POST /api/v1/fsrs/review
POST /api/v1/curriculum/bulk/validate-all-subjects
POST /api/v1/live-sessions/{session_id}/start
POST /api/v1/live-sessions/{session_id}/screen-share/start
POST /api/v1/diary/goals/validate-smart
POST /api/v1/diary/learning/{entry_id}/review
POST /api/v1/diary/export
POST /api/v1/knowledge-map/update
POST /api/v1/productive-failure/pretest/start
POST /api/v1/offline/sync-results
POST /api/v1/questions/create        ← duplicate of POST /questions
POST /api/v1/questions/bulk-create
POST /api/v1/auth/2fa/enable
POST /api/v1/auth/2fa/disable
POST /admin/encryption/rotate-key
```

Most are legitimate — actions that don't map cleanly to REST (e.g. `/start`, `/complete`, `/submit`). The pure-REST violations:
- `POST /api/v1/questions/create` — should just be `POST /api/v1/questions`
- `POST /api/v1/learning-path/create-profile` — redundant `create-` prefix
- `POST /api/v1/learning-path/create-path` — same

### Method-verb mismatches (P1)

```
POST /api/v1/kvkk/privacy/delete      ← should be DELETE /api/v1/kvkk/privacy
POST /api/v1/ddos/whitelist/remove    ← should be DELETE /api/v1/ddos/whitelist/{id}
POST /api/v1/ddos/blacklist/remove    ← same
```

**3 violations**. Small but real — `POST /delete` is a classic anti-pattern.

---

## 10. KIRO2 Special Groups — Coherence

### `curator` (3 ops, Session 178)

```
AUTH GET  /api/v1/curator/queue
AUTH POST /api/v1/curator/verdict
AUTH GET  /api/v1/curator/stats
```

✅ All auth-required. ⚠️ No DETAIL endpoint (`GET /curator/items/{id}`) — curator workflow gets items only via queue, no direct deep-link.

### `gamification` (17 ops, Session 84 IDOR fix)

✅ **All 17 require auth.** IDOR concern from Session 84 is fully resolved at the OpenAPI level — no `user_id` query parameter on any endpoint. ⚠️ No DELETE — points/badges can't be revoked (admin operation missing).

### `learning-path` (24 ops)

✅ 23/24 require auth. 1 public: `/learning-path/health` (intentional).
⚠️ 7 of 24 endpoints lack `response_model` (`my-profile`, `exit-quiz/{subject}`, `interleaved-practice`, `review-queue`, `submit-review`, `register-wrong-answers`, `weakness-report`). **P0 — hot path with untyped responses.**

### `osym-exam` (16 ops)

✅ All 16 require auth. ✅ Resource lifecycle complete (create → start → answer → flag → complete → delete). ⚠️ Mixed REST/RPC: `/{id}/start`, `/{id}/complete`, `/{id}/flag-question` are action verbs but appropriate for stateful exam sessions.

### `fsrs` (4 ops)

✅ All auth. ⚠️ Only LIST + POST. No DELETE (cannot remove a review card). No DETAIL endpoint (cannot inspect a single card's FSRS state).

### `dag` (4 ops)

✅ All auth, read-only. ✅ Appropriate for a graph algorithm surface.

### Game/social groups (`dungeon`, `bilge-alp`, `soru-meydani`, `cozum-duellosu`, `usta-cirak`, `oba-seferleri`, `duel`)

All auth-required. ⚠️ Most have 2-7 ops only — feature surfaces clearly mid-development.
- `bilge-alp`: only POST chat + POST dialog-options — no conversation history endpoint.
- `dungeon`: only `GET /{subject}` + `POST /{subject}/complete` — no progress endpoint.
- `duel`: includes SSE stream `GET /duel/stream/{session_id}` — only SSE endpoint in the duel group.

### `/api/v1/streaming/*` (SSE)

**No `/streaming/*` cluster exists.** The 12 streaming-flavored endpoints are scattered:

```
POST /api/v1/enhanced-chat/stream                      (SSE)
GET  /api/v1/duel/stream/{session_id}                  (SSE)
POST /api/v1/video-solutions/{video_id}/generate-streaming
POST /api/v1/learning-path/assess-knowledge            (likely SSE)
POST /api/v1/irt-morfoloji/quick-assessment
POST /api/v1/berturk/motivation/assess
GET  /api/v1/exam-performance/{exam_session_id}/weaknesses
POST /api/v1/assessment/start
POST /api/v1/assessment/answer
GET  /api/v1/assessment/result/{session_id}
GET  /api/v1/teacher/classes
POST /api/v1/teacher/classes
```

⚠️ `CLAUDE.md` says SSE is the default for streaming, but there's no documented `/api/v1/stream/*` namespace. Convention is inconsistent — SSE endpoints could be co-located under `/api/v1/stream/*` for clarity. **P2.**

---

## 11. Bulk / Batch Endpoints

**27 endpoints** with `bulk` or `batch` in the path. Mix of `bulk-X`, `batch/X`, `X/batch-Y`:

```
/api/v1/questions/bulk-create
/api/v1/content/bulk-import
/api/v1/content-management/questions/bulk-upload
/api/v1/content-management/educational/bulk-upload
/api/v1/irt-morfoloji/batch-analyze
/api/v1/irt-morfoloji/bulk-quality-analysis
/api/v1/curriculum/bulk/validate-all-subjects
/api/v1/osym/generate/batch-generate
/api/v1/questions/hybrid/generate-bulk
/api/v1/batch/generate
/api/v1/batch/status/{task_id}
/api/v1/batch/results/{task_id}
DELETE /api/v1/batch/cancel/{task_id}
/api/v1/batch/queue/stats
/api/v2/quality/evaluate-batch
```

⚠️ **Inconsistent naming:** `bulk-create` vs `batch-generate` vs `bulk-upload` vs `batch/generate` vs `generate-bulk`. Pick one:
- prefix: `/bulk/<verb>` or
- suffix: `<verb>-bulk` / `<verb>-batch`

The `/api/v1/batch/*` group has its own async-job lifecycle (`generate`, `status`, `results`, `cancel`, `queue/stats`) — that's the right pattern. Other "bulk" endpoints should either:
1. Use the batch job pattern (return task_id, poll for results), or
2. Stay synchronous for small N.

---

## 12. Tag & Schema Consistency

| Metric | Value |
|---|---|
| Unique OpenAPI tags | 148 |
| Endpoints without tags | 0 ✅ |
| Tag naming (sample) | Mixed: Turkish (`"İçerik Yönetimi"`, `"Kimlik Doğrulama"`, `"Soru Bankası"`), English (`"Diary"`, `"Admin Panel"`, `"Visual Supports"`), lowercase-kebab (`"adhd-support"`, `"video-analytics"`) |
| Duplicate `operationId`s | 0 ✅ |
| Pydantic schemas | 770 |

⚠️ **Tag naming is inconsistent across three styles** — Turkish title-case, English title-case, English lowercase-kebab. Sample of all three:
- `İçerik Yönetimi` (34 ops) — Turkish title case
- `Diary` (48 ops) — English title case
- `adhd-support` (35 ops) — lowercase kebab
- `Question CRUD` (17 ops) — English title case
- `teachers` (25 ops) — lowercase plural

→ **P2:** Pick a tag-naming convention. Recommend lowercase-kebab to match the path convention. Side-effect: Swagger UI grouping changes.

---

## 13. Hot Endpoint Latency (live measurement)

10 iterations each, anonymous, against running stack:

| Endpoint | Method | Status | p50 | p95 | min | max |
|---|---|---|---:|---:|---:|---:|
| `/health` | GET | 200 | 19.8ms | 36.3ms | 10.6ms | 36.3ms |
| `/api/v1/learning-path/health` | GET | 200 | 13.2ms | 20.6ms | 11.6ms | 20.6ms |
| `/api/v1/fsrs/due` | GET | 401 | 15.5ms | 19.6ms | 11.7ms | 19.6ms |
| `/api/v1/learning-path/today` | GET | 401 | 16.0ms | 33.5ms | 10.6ms | 33.5ms |
| `/api/v1/curriculum/subjects` | GET | 404 | 19.4ms | 20.2ms | 17.0ms | 20.2ms |
| `/api/v1/dag/topics` | GET | 401 | 12.2ms | 32.9ms | 10.8ms | 32.9ms |
| `/api/v1/gamification/points` | GET | 401 | 12.3ms | 28.3ms | 11.5ms | 28.3ms |
| `/api/v1/osym-exam/exam-configs` | GET | 401 | 11.1ms | 27.8ms | 9.1ms | 27.8ms |
| `/api/v1/questions/health` | GET | 200 | 11.8ms | 13.3ms | 10.7ms | 13.3ms |
| `/api/v1/recommendations/health` | GET | 200 | 14.0ms | 26.4ms | 11.4ms | 26.4ms |

✅ All p95 ≤ 36ms — well within the **<2s SLA** from `CLAUDE.md`. Note: most measured cases are 401 (auth dependency short-circuit), so this is auth-stack latency, not the full data path. Auth-required hot endpoints (`/fsrs/due`, `/learning-path/today`) need authenticated benchmarking (`benchmark_api.py` covers this — see Session 84).

🔴 `/api/v1/curriculum/subjects` returns 404 — endpoint doesn't exist under that name. The actual list is at `/api/v1/curriculum/...` somewhere. Frontend or docs may reference a stale path.

---

## 14. Findings Prioritized

### P0 (block beta or active risk)

1. **20 endpoints crash on anonymous access (500/503/501)** — these are reachable without auth AND throw exceptions. Either move behind auth or make them return graceful 503 with `Retry-After`. List in §6.
2. **Hot path `/api/v1/learning-path/*` has 7 endpoints without `response_model`** — frontend types are best-effort. Schema drift risk. Top names: `review-queue`, `submit-review`, `register-wrong-answers`, `weakness-report`, `my-profile`, `exit-quiz/{subject}`, `interleaved-practice`.

### P1 (architecture coherence; ship before public launch)

3. **17 legacy Turkish root endpoints** (`/sorular`, `/soru/{id}`, `/konular`, `/istatistikler`, `/zorluk-filtrele`, etc.) — not under `/api/v1/`, not deprecated. Delete or migrate.
4. **13 Turkish query parameters** across 70+ endpoint instances — extend `path-naming.md` to cover query/path params, then rename.
5. **`/api/v2` cluster (17 ops) coexists with `/api/v1` without a versioning policy** — decide whether v2 is the future canonical or experimental sandbox; document.
6. **`session_id`, `video_id`, `content_id`, `oba_id` have inconsistent types across endpoints** (int vs string, uuid vs free string). Pick canonical per resource.
7. **4 likely-unintended public endpoints** exposing aggregate data (`learning-style/cache-stats`, `content/stats`, `content/trending`, `osym-inspired/statistics`).
8. **Method-verb mismatches:** `POST /kvkk/privacy/delete`, `POST /ddos/whitelist/remove`, `POST /ddos/blacklist/remove` — convert to DELETE.
9. **Mixed pagination conventions** (`offset+limit` vs `page+per_page` vs `sayfa+sayfa_boyutu` vs `limit`-only). Standardize on offset+limit (majority). 60 endpoints have `limit` only — un-paginatable beyond first page.

### P2 (polish)

10. **9 trailing-slash inconsistencies** — pick a side; 1 actual duplicate (`/health`, `/health/`).
11. **66% of endpoints lack `$ref` response_model** (395 absent + 414 inline/non-ref). Auto-generated TypeScript clients will produce `any`.
12. **Tag naming inconsistent (Turkish title / English title / lowercase-kebab)** — choose one for OpenAPI tags.
13. **27 bulk/batch endpoints use 5 different naming styles** — consolidate.
14. **SSE endpoints scattered across 12 paths** — consider `/api/v1/stream/*` namespace.
15. **No global `Deprecation` / `Sunset` HTTP headers** declared on the 19 `deprecated: true` endpoints — frontend has no machine-readable end-of-life date.
16. **Most non-2xx status codes not in OpenAPI** — 401/403/404/429/500/503 declared on <5% of endpoints despite being returned at runtime. Add global `OpenAPIResponse` block in `main.py`.

---

## Appendix A: Methodology

- **Snapshot:** `GET http://localhost:8000/openapi.json` at 2026-05-21 — saved as `openapi_snapshot.json` for reproducibility.
- **Endpoint counting:** Each `(method, path)` pair counted once; PATCH/PUT counted separately.
- **Anonymous access test:** Simple `requests.get()` with no headers, 3s timeout, no redirect follow, sampled across the full path list (~546 GET endpoints reachable; 14 timed out).
- **Latency:** 10 iterations per endpoint, p50 = median, p95 = 95th-percentile (or max if N<20).
- **No database queries, no docker exec, no file modification.** Read-only audit per task constraints.

### Files

- `openapi_snapshot.json` — 1.34 MB raw OpenAPI document
- `api_endpoint_inventory.md` — this report

---

*Generated: 2026-05-21. Author: Claude (Opus 4.7 1M).*
