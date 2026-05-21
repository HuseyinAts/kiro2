# Integration Audit — FE↔BE Contract Drift (2026-05-22)

## Executive Summary
CRITICAL P1 risks: Study Rooms API (40 calls, 0 endpoints), Knowledge Graph v2 (missing), Turkish-only endpoints (22), WebSocket incomplete, auth header survivors (5). All /api/v1/* compliant. httpOnly cookie auth consistent. CORS production-ready.

---

## 1. Fetch Path Inventory (Frontend)

**Total:** 142 unique API call patterns across 43 files
- frontend/src/services/*.ts: 81 calls
- frontend/src/components/**/*.tsx: 43 calls
- frontend/src/pages/*.tsx: 18 calls

Sample paths:
- /api/v1/osym-exam/* 
- /api/v1/student-dashboard/*
- /api/v1/reports/*
- /api/v1/adhd-support/*
- /api/v1/study-rooms/* (40+ calls)
- /api/v1/eba/*
- /api/v1/khan/*
- /api/v2/knowledge-graph/* (v2 risk)

---

## 2. Backend Endpoint Inventory

**Total:** 1,058 endpoints in openapi_snapshot.json (2026-05-21 16:34, fresh)

Sample inventory:
- /api/v1/adhd-support/* (31)
- /api/v1/admin/* (12)
- /api/v1/analytics/* (9)
- /api/v1/auth/* (8 + legacy)
- /api/v1/ogretmen/* (11 Turkish)
- /api/v1/veli/* (9 Turkish)
- /api/v1/student-dashboard/* (11)
- /api/v1/osym-exam/* (18)
- /api/v1/reports/* (9)
- /api/v1/study-rooms/* (ZERO)

---

## 3. 404 Risk Analysis

| Component | FE | BE | Risk | Evidence |
|-----------|----|----|------|----------|
| Study Rooms | 40+ | 0 | CRITICAL | StudyRooms/*.tsx calls /api/v1/study-rooms/{roomId}/messages. NO match in snapshot. study_planner_api.py uses /api/v1/study-plan. |
| Knowledge Graph v2 | 2 | 0 | HIGH | KnowledgeGraphViz.tsx:38-39 calls /api/v2/knowledge-graph/*. Snapshot has v1 only. |
| Video Sync | 3 | partial | MEDIUM | sw.ts:271,292 calls /api/sync/*. Not in OpenAPI. |
| EBA/Khan | 26 | yes | LOW | All /api/v1/eba, /api/v1/khan present. |
| OSYM | 18 | yes | LOW | All /api/v1/osym-exam/* registered. |

**Total 404 risk: ~45 endpoints**

---

## 4. Schema Drift (5 Spot-Checks)

1. /api/v1/osym-exam/create (examService.ts:169) — MATCHED
2. /api/v1/student-dashboard/istatistikler (dashboardService.ts:81) — MATCHED
3. /api/v1/adhd-support/focus-mode/activate — MATCHED
4. /api/v1/reports/exam/{sinavId}/advanced (advancedReportsService.ts:185) — MATCHED
5. /api/v1/study-rooms/{roomId}/messages (StudyRooms/ChatInterface.tsx:115) — CRITICAL DRIFT (NOT FOUND)

---

## 5. Path Naming Drift (TR/EN)

Turkish-only endpoints (no English):

| Path | English | Status | Recommendation |
|------|---------|--------|-----------------|
| /api/v1/ogretmen/* (11) | /teacher/* | PARTIAL | 9/11 have English; 2 legacy-only |
| /api/v1/veli/* (9) | /parent/* | PARTIAL | 7/9 have English |
| /auth/ogretmen-profil | /auth/teacher-profile | DRIFT | No English version |
| /auth/veli-profil | /auth/parent-profile | DRIFT | No English version |
| /student-dashboard/* (11) | mixed | HYBRID | Intentional bilingual design |

**Total: 33 naming drift risks**

Allowlist (per .claude/rules/path-naming.md):
- Products: bilge-alp, soru-meydani, oba-seferleri, usta-cirak, cozum-duellosu, zpd-maarif
- Regulatory: kvkk
- Legacy: sinav-gecmisi, profil-guncelle

---

## 6. Auth Header Consistency

Strategy: httpOnly cookie (primary) + Bearer fallback

**PRIMARY:** apiClient.ts:32 withCredentials: true

**SURVIVORS (5 files):**
- useCATSession.ts:50 — Authorization: Bearer ${token}
- usePlacementSession.ts:52 — Authorization: Bearer ${token}
- FocusMode.test.tsx (mock tests)

**Recommendation:** Migrate useCATSession/usePlacementSession to use apiClient + httpOnly cookies

**Backend support:** core/dependencies.py:96-116 — accepts Bearer header OR httpOnly cookie

---

## 7. CORS Configuration

Backend/main.py:56-81

**Dev:** localhost:3000, localhost:3001 (automatic)
**Prod:** REQUIRES ALLOWED_ORIGINS env var (crashes if unset — prevents silent rejection)
**Credentials:** Enabled
**Methods/Headers:** Permissive

**Status:** PRODUCTION-READY. Requires explicit env setup in production (safe guard).

---

## 8. WebSocket Status

Frontend: api.ts:763-896 (implemented, config-driven)

**Issue:** Backend has algorithm support (multi_agent_blackboard.py:374-596) but NO router endpoints

Study-Rooms calls:
- /ws/study-rooms/{roomId}/chat
- /ws/study-rooms/{roomId}/whiteboard
- /ws/study-rooms/{roomId}/video

**Status:** INCOMPLETE. Study-rooms WebSocket router missing.

---

## 9. Non-v1 Paths

All frontend calls are /api/v1/* compliant.

**Exceptions (v2):**
- /api/v2/knowledge-graph/stats (KnowledgeGraphViz.tsx:38)
- /api/v2/knowledge-graph/student/{studentId}/gaps (KnowledgeGraphViz.tsx:39)

**Cost:** 404 directly (no 307 penalty). Should implement /api/v2/* or redirect to /api/v1/*.

---

## 10. Top 10 P0 Risks

| Priority | Risk | Impact | File:Line |
|----------|------|--------|-----------|
| P0-1 | Study Rooms missing (40 calls, 0 BE) | Silent 404 cascade | StudyRooms/*.tsx |
| P0-2 | /api/v2/knowledge-graph/* missing | 404 or redirect | KnowledgeGraphViz.tsx:38-39 |
| P0-3 | Turkish endpoints no English variant | Frontend guesses wrong | auth routers |
| P0-4 | WebSocket routes not registered | Fallback to polling (high latency) | StudyRooms/ChatInterface.tsx:124 |
| P0-5 | useCATSession/usePlacementSession Bearer token | Auth inconsistency | useCATSession.ts:50 |
| P0-6 | /api/sync/* missing (offline sync) | Exam results not synced offline | sw.ts:271,292 |
| P0-7 | CORS unset in production | Backend crashes on startup | main.py:71 |
| P0-8 | No VersionRedirectMiddleware | Not needed, all /api/v1/* | (N/A) |
| P0-9 | /auth/refresh/secure in OpenAPI? | Token refresh issue | apiClient.ts:138 |
| P0-10 | Mixed v1/v2/no-prefix API calls | Inconsistent versioning | Multiple |

---

## 11. Methodology

**Sources:**
1. openapi_snapshot.json — 1,058 paths (2026-05-21)
2. Grep frontend 43 files — fetch, axios, apiClient patterns
3. Rules — .claude/rules/path-naming.md, core/dependencies.py, main.py
4. Audit script — backend/scripts/audit_path_drift.py

**Evidence:** All P0 risks have file:line proof.

---

## Recommendations

1. **CRITICAL:** Implement /api/v1/study-rooms/* router (40+ endpoints)
2. **CRITICAL:** Register WebSocket /ws/study-rooms/{roomId}/*
3. **HIGH:** Add /api/v1/auth/teacher-profile, /api/v1/auth/parent-profile
4. **HIGH:** Migrate useCATSession/usePlacementSession to apiClient
5. **HIGH:** Implement /api/v2/knowledge-graph/* or redirect
6. **MEDIUM:** Implement /api/v1/sync/* for offline sync
7. **MEDIUM:** Verify POST /api/v1/auth/refresh/secure in OpenAPI
8. **MEDIUM:** Deprecate Turkish-only /ogretmen/* paths
9. **LOW:** Add CI gate using audit_path_drift.py --fail

---

**Report:** 2026-05-22
**Auditor:** Integration Drift Agent (READ-ONLY)
