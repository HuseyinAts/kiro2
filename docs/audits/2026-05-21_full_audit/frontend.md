# KIRO2 Frontend Audit — 2026-05-21 Session 178

## Executive Summary

The KIRO2 frontend is a large React 18 + TypeScript + Vite 7 + Zustand + Tailwind codebase with ~50K lines across 400+ source files. The core architecture is sound: cookie-based auth is complete, lazy-loading covers all 40+ routes, `tsconfig.json` strict mode is active, and the new Curator UI (Session 178) is clean and well-tested.

Three issues are beta-blockers: a raw `fetch()` SSE stream call in `chatService.ts` that bypasses cookie auth (P0), dual parent-dashboard routes with conflicting role logic (P0), and `react-query` v3 being used while v4/v5 API (`useQuery` object-arg form) is mixed — the Curator hooks use v3 syntax that will silently fail if upgraded (P1). The `any` count (341 across 134 files) and 1,165-line `ModernLearningPathPage.tsx` are quality debt but not blockers.

---

## Findings

### P0 — Beta-Blocker

**P0-1: SSE stream request in `chatService.ts` missing `credentials: 'include'`**

`frontend/src/services/chatService.ts` line 108:
```
const response = await fetch(STREAM_ENDPOINT, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  // NO credentials: 'include' here
  body: JSON.stringify({ ... })
});
```
All other `fetch()` calls in this file (lines 203, 235, 251, 300, 363, 396, 425, 447) correctly include `credentials: 'include'`. The SSE endpoint is the main chat streaming call — the one students hit most often. Without the cookie header it will 401 in production where CORS is restricted. The other 10 raw-`fetch()` services (`revolutionaryFeaturesService.ts`, `multiAgentService.ts`, etc.) all correctly pass credentials via a shared `request()` helper. Only this one streaming call is missing it.

**Fix:** Add `credentials: 'include'` to the `fetch(STREAM_ENDPOINT, {...})` call at line 108.

**P0-2: Dual parent dashboard routes with role mismatch**

`frontend/src/App.tsx` has three overlapping parent routes:
- `/veli-takip` → `<ParentDashboard>` (role: `'veli'`) — eager-loaded, not lazy
- `/parent-new` → `<ParentDashboardNew>` (role: `'veli' | 'admin'`) — lazy
- `/parent/dashboard` → `<ParentDashboardPage>` (role: `'veli'`) — lazy

`ParentDashboard` at line 20 is eager-imported (`import { ParentDashboard } from './pages/ParentDashboard'`) — it is NOT lazy. This adds to initial bundle regardless. More critically, `/veli-takip` is a Turkish-path route alongside English `/parent/*` routes — `.claude/rules/path-naming.md` prohibits this coexistence unless it is a brand name. `veli-takip` is not a brand name. The three routes serve overlapping audience with no clear canonical path, meaning the navigation menu probably links to one while auth redirects go to another.

**Fix:** Deprecate `/veli-takip` and `/parent-new` in favor of `/parent/dashboard`; move `ParentDashboard` import to lazy.

---

### P1 — Production-Quality

**P1-1: react-query v3 (`^3.39.3`) — version drift risk**

`frontend/package.json` line 32: `"react-query": "^3.39.3"`. The codebase uses the RQ v3 object-argument API form (`useQuery<T, E>({ queryKey, queryFn, keepPreviousData, ... })`). In react-query v4+ `keepPreviousData` was renamed to `placeholderData: keepPreviousData` and the object form changed. The 13 files importing from `'react-query'` are all using v3 syntax. If `npm update` pulls a v4 peer, silent breakage occurs. The Curator hooks (`useCuratorQueue.ts:115`) use `keepPreviousData: true` directly — this is the riskiest because curator functionality is newest and least tested at upgrade time.

**Recommendation:** Pin exactly to `"react-query": "3.39.3"` (remove `^`) until a deliberate v4/TanStack Query v5 migration is planned.

**P1-2: `any` type sprawl — 341 occurrences in 134 files**

`.ts` files: 130 occurrences in 40 files. `.tsx` files: 211 occurrences in 94 files. Hot spots:
- `frontend/src/utils/apiHelpers.ts` — 10 occurrences. The `apiRequest<T>` generic is typed but internal `err` parsing uses `any` heavily (lines 134, 135, 460, 461).
- `frontend/src/services/revolutionaryFeaturesService.ts` — 7 occurrences.
- `frontend/src/components/Common/AccessibleTable.tsx` — 6 occurrences.
- `frontend/src/utils/dateUtils.ts` — 6 occurrences.
- `frontend/src/utils/performance.tsx` — 6 occurrences.

`tsconfig.json` has `strict: true` and `noImplicitAny: true` (implied by strict). However `src/test/` and `src/**/__tests__` are excluded from tsconfig, so test files' `any` counts are not enforced. The non-test production `any` is the concern — approximately 150-180 occurrences in non-test, non-deprecated files.

**P1-3: `authStore.ts` persists `isAuthenticated` + `user` to localStorage**

`frontend/src/store/authStore.ts` lines 319-327 — the `persist` middleware `partialize` saves `{ user, isAuthenticated }` to `localStorage` key `'auth-storage'`. While tokens are correctly removed (httpOnly cookie migration done), this means a stale `isAuthenticated: true` can survive a cookie expiry. The `ProtectedRoute` guard at `frontend/src/components/Auth/ProtectedRoute.tsx:28` handles this correctly — it waits for `loading` (which reflects the `initializeAuth` cookie check). But the `loading` initial value is `true` in the store and is NOT persisted, so on a hard refresh the store re-hydrates with `isAuthenticated: true` from localStorage and `loading: true`. Auth init happens in `AuthProvider`. If `initializeAuth` is slow, the user may briefly see protected content before `loading` flips back to `false`. This is a TOCTOU race, not a security hole (server validates the cookie) but it causes a visible flash for logged-out users with stale localStorage.

**Recommendation:** Remove `isAuthenticated` from `partialize` — only persist `user` for display continuity, not auth decision.

**P1-4: `ModernLearningPathPage.tsx` — 1,165 lines, monolithic**

`frontend/src/pages/ModernLearningPathPage.tsx` is 1,165 lines and contains rendering logic for: quiz modal, video tab, path visualization, error cluster, pretest flow, subject selector, and loading states. The `deprecation-guard.md` threshold is 500 lines = warn, 800 = red flag. This is above both. It mixes container and presentation concerns heavily. Several inline sub-components are defined inside the file without named exports.

**Other oversized files:**
- `frontend/src/components/Exam/OSYMExamInterface.tsx` — 1,012 lines
- `frontend/src/components/Exam/ModernOSYMExamInterface.tsx` — 767 lines

**Recommendation:** Extract the quiz modal, video tab, and pretest flow from `ModernLearningPathPage.tsx` into named sub-components.

**P1-5: StudyRooms feature — no routes, orphaned components**

`frontend/src/components/StudyRooms/` contains `VideoConference.tsx`, `CollaborativeWhiteboard.tsx`, `VideoConference/VideoGrid.tsx`, `VideoConference/ParticipantList.tsx`, `VideoConference/ScreenShare.tsx` etc. None of these are mounted in `App.tsx`. The `.claude/rules/path-naming.md` audit baseline from Session 135 noted ~40 `/api/v1/study-rooms/*` frontend 404s as "missing-feature, not naming drift." These components exist, compile, but are unreachable. They represent dead-code risk.

---

### P2 — Improvement

**P2-1: `react-query` v3 `keepPreviousData` in Curator UI — watch for v4 migration**

`frontend/src/hooks/useCuratorQueue.ts:115` — `keepPreviousData: true`. In TanStack Query v4 this is `placeholderData: keepPreviousData` (imported function). In v5 it's `placeholderData: 'keep'`. Since the Curator UI is new (Session 178) and well-tested, it's the right place to start a migration pilot.

**P2-2: `useKeyboardShortcuts.ts` — `bindings` object dep array leak**

`frontend/src/hooks/useKeyboardShortcuts.ts:88` — the `useEffect` depends on `[bindings, enabled, allowInInputs]`. In `CuratorPage.tsx` the `keyBindings` is correctly memoized with `useMemo` (line 538) so this is fine. However `useKeyboardShortcut` (singular, line 39-54) depends on `[key, handler, enabled, allowInInputs]`. If a caller passes an inline arrow function `() => doSomething()` without `useCallback`, the handler reference changes every render, causing the effect to re-add/remove the listener on every render. No current call site is confirmed broken, but it is a latent bug pattern.

**P2-3: `authStore.ts` uses Zustand `persist` + `devtools` together — state shape**

The `persist` middleware wraps the `devtools` middleware. The recommended Zustand v4 order is `devtools(persist(...))` (outer devtools). The current code at `authStore.ts:87` is `devtools(persist(...))` which is correct. But `settingsStore.ts` has similar structure — verify it follows the same order.

**P2-4: `ModernOSYMExamInterface.tsx` — 6 pre-existing TypeScript errors**

Confirmed from MEMORY.md: `ModernOSYMExamInterface.tsx` has 6 pre-existing TS errors. These are excluded from `tsc --noEmit` gate because the tsconfig excludes test files but NOT `src/components`. This means `npm run build` (`tsc && vite build`) will fail on these unless `build:fast` (bypasses tsc) is used. The `build:fast` script is marked in MEMORY.md as "no longer needed" since the bug was fixed (Session 80), but the 6 errors remain.

**P2-5: OSB settings frontend hookup — partial**

`useReducedMotion.ts` correctly reads from `settingsStore.accessibility.reduceMotion`. `settingsStore.ts` has `reduceMotion`, `disableAnimations` fields. However the MEMORY.md notes `osb_settings` DB table columns `no_shadows`, `no_animations`, `reduced_motion` — these are backend fields. The frontend `settingsStore` operates independently (localStorage) and does not sync with the `osb_settings` DB endpoint. If the backend stores these preferences and the frontend doesn't read them on login, user settings are not cross-device persistent.

**P2-6: Turkish NFC normalization — present in helpers but absent in search inputs**

`frontend/src/utils/learningPathHelpers.ts:18` correctly calls `.normalize('NFC')` before Turkish lowercase for title matching. However search inputs elsewhere (admin content search, exam start subject filter) use plain `toLowerCase()` without `normalize('NFC')` first. This can cause matching failures for Turkish text entered via IME or copy-paste from PDFs.

**P2-7: `apiHelpers.ts` — dual fetch wrapper pattern**

`frontend/src/utils/apiHelpers.ts` exports both `fetchWithErrorHandling` (line 384) and `apiRequest` (line 432) — two separate raw-`fetch` wrappers with overlapping purpose. `apiRequest` is used by `useCuratorQueue.ts`, `useLearningPathQueries.ts`, and `authService.ts`. `fetchWithErrorHandling` appears unused in production code (only referenced in tests).

**Recommendation:** Remove `fetchWithErrorHandling`, standardize on `apiRequest` for raw-fetch use cases and `apiClient` (axios) for everything else.

**P2-8: Velocity timer in CuratorPage — memory-safe**

`frontend/src/pages/Admin/CuratorPage.tsx:493-497` — the `setInterval` is correctly cleaned up via `return () => window.clearInterval(t)`. The `itemStartRef` correctly uses `useRef` (not state) for the timestamp so it doesn't trigger re-renders. No memory leak.

**P2-9: Test coverage**

86 vitest test files. Coverage threshold configured at 80% globally. The test suite excludes `src/test/`, `src/**/__tests__` from tsconfig type checking — two test files incorrectly set `localStorage.setItem('token', ...)` which is the old auth pattern and will not affect production but is misleading.

**P2-10: Bundle — `manualChunks: undefined` correctly set**

`vite.config.ts:139` — `manualChunks: undefined`. This is the KIRO2 lesson from Session 74 (vendor chunk React context bug).

**P2-11: PWA — `start_url: '/dashboard'`**

`vite.config.ts:57` — PWA manifest `start_url: '/dashboard'`. This is a student-only route. Consider `start_url: '/'` which redirects to `/login` then role-appropriate dashboard.

---

## Metrics

| Metric | Value |
|---|---|
| TS/TSX source files | ~400+ (excludes `_deprecated/`, tests) |
| Total `any` occurrences | 341 (130 `.ts` + 211 `.tsx`) |
| Production `any` (estimated) | ~150-180 (excluding test/deprecated) |
| Test files (vitest) | 86 |
| Coverage threshold (configured) | 80% all metrics |
| Pre-existing TS errors | 6 (`ModernOSYMExamInterface.tsx`) |
| Lazy-loaded routes | 40+ |
| Eager-loaded pages | 4 (Login, Register, Unauthorized, + ParentDashboard bug) |
| react-query version | 3.39.3 |
| `_deprecated/` pages | 32 files, correctly isolated |
| Oversized components (>800 lines) | 3 (`ModernLearningPathPage.tsx:1165`, `OSYMExamInterface.tsx:1012`) |
| `credentials: 'include'` missing | 1 (chatService.ts:108 SSE stream) |
| localStorage auth references (production) | 0 (migration complete) |
| Zustand stores | 5 |
| Custom hooks | 47 |
| StudyRooms orphaned components | ~8 files (no route) |

---

## Key File References

- `frontend/src/App.tsx` — Route definitions, lazy imports, dual parent routes (P0-2)
- `frontend/src/services/apiClient.ts` — Axios singleton, `withCredentials: true`
- `frontend/src/services/chatService.ts:108` — Missing `credentials: 'include'` on SSE stream (P0-1)
- `frontend/src/utils/apiHelpers.ts` — `apiRequest` + `fetchWithErrorHandling` dual wrapper (P2-7)
- `frontend/src/store/authStore.ts:319-327` — `persist` partialize includes `isAuthenticated` (P1-3)
- `frontend/src/components/Auth/ProtectedRoute.tsx` — Role guard, loading wait pattern
- `frontend/src/pages/Admin/CuratorPage.tsx` — 658 lines, well-structured, velocity timer safe
- `frontend/src/hooks/useCuratorQueue.ts:115` — `keepPreviousData: true` (v3 syntax, P1-1)
- `frontend/src/hooks/useKeyboardShortcuts.ts:88` — latent inline-fn risk (P2-2)
- `frontend/src/pages/ModernLearningPathPage.tsx` — 1,165 lines, needs split (P1-4)
- `frontend/src/utils/learningPathHelpers.ts:18,38` — `.normalize('NFC')` present
- `frontend/tsconfig.json` — `strict: true`, excludes test/deprecated
- `frontend/vite.config.ts:139` — `manualChunks: undefined` (KIRO2 lesson applied)
- `frontend/package.json:32` — `"react-query": "^3.39.3"` (pin recommended)
