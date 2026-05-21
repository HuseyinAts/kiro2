# Frontend Audit — Product Readiness (2026-05-22)

**Verdict**: TS build hâlâ fail (5 hata, dünkü 6→5 fix incomplete). Dead store consumers + 10 raw fetch survivor + 8 a11y violation.

## Build Status

| Item | Status |
|---|---|
| `npm run build` (tsc + vite build) | ❌ **FAIL — 5 TS errors** |
| `npm run build:fast` (vite only, no tsc) | ✅ Skips type check |
| TypeScript strict mode | ✅ Enabled (tsconfig.json:14) |
| `@ts-ignore` / `@ts-expect-error` in src/ | 0 (3 in test files only) |

**5 TS errors blocking production build**:
1. `src/App.tsx:107` — `ParentDashboardNew` declared but never read
2. `src/components/Exam/ModernOSYMExamInterface.tsx:560` — string|undefined not assignable to string
3. `src/pages/OSYMQuestionGeneratorPage.tsx:100` — duplicate object property
4. `src/pages/ParentDashboardNew.tsx:43` — Expected 1-2 args, got 3 (React.useCallback)
5. `src/store/authStore.ts:155` — Promise<boolean | "2fa_required"> not assignable to Promise<boolean>

**Note**: Commit 9094dd50c (May 22) supposedly fixed all TS errors via `cq` narrowing in ModernOSYMExamInterface. Agent finds errors still present — needs verification.

## Duplication Candidates

| # | Page | Duplicate? |
|---|---|---|
| 1 | ModernParentDashboard.tsx ↔ ParentDashboard.tsx | ✅ Confirmed |
| 2 | ParentDashboardNew.tsx | Declared, never imported (dead) |
| 3 | ModernAdminDashboard ↔ — | Intentional refactor only |
| 4-10 | 9× Modern* pages | No legacy duplicate found |

**jscpd 3.29% duplication** likely from Modern* refactor overlap — not real duplicates.

## Dead Store Consumers (P0)

May 22 commit marked `examStore`, `notificationStore`, `uiStore` as `@deprecated`. But:

| Store | Live consumers |
|---|---|
| `useExamStore` | **3 files** — OSYMExamInterfaceRefactored.tsx, hooks/useExamTimer.ts, hooks/queries/useExamQueries.ts |
| `useNotificationStore` | 1 file (hooks/useNotification.ts, test-only?) |
| `useUiStore` | 0 files ✅ |

**Risk**: Components depending on deprecated stores will silently break when stores are deleted.

## localStorage Auth Survivors (✅ CLEAN)

**0 production survivors**. Test files mock localStorage but no production code reads tokens.

## fetch() Outside services/

**286 fetch() total**, of which **10 in production services bypass apiClient**:

| File | fetch calls |
|---|---|
| services/revolutionaryFeaturesService.ts | **19** ⚠️ |
| services/chatService.ts | several |
| services/fsrsService.ts | — |
| services/backgroundSyncService.ts | — |
| services/culturalAdaptationService.ts | — |
| services/multiAgentService.ts | — |
| services/NetworkDetector.ts | — |
| services/offlineStorageService.ts | — |
| services/socialService.ts | — |
| services/VideoLoadingManager.ts | — |

**Risk**: Raw fetch bypasses centralized error handling, auth retry, rate limiting.

## A11y Findings (8 missing alt= sites)

| File | Issue |
|---|---|
| components/EbaTV/EbaTVRecommendations.tsx:336 | `<img>` no alt |
| components/EbaTV/EbaTVDashboard.tsx | 2 images no alt |
| components/EbaTV/EbaTVContentSearch.tsx | 1 |
| components/Gamification/BadgeEarned.tsx | 1 |
| components/StudyRooms/ChatInterface.tsx | 1 |
| components/MathSolution/SolutionStep.tsx | 1 |
| components/QuestionParser/YOLOQuestionDetector.tsx | 1 |
| components/ui/ImageZoomModal.tsx | 2 |

**WCAG 2.1 Level A failures** — production a11y audit will catch these.

## Bundle Config (vite.config.ts ✅ VERIFIED)

- `manualChunks` 4 groups: mui-icons (188 → 1), mui-core, charts (recharts+d3), router
- `react-syntax-highlighter` uses `dist/esm/light` (NOT full Prism) — confirmed in ChatMessage.tsx
- PWA cache: 24h realm, 30m gamification, 7d images
- terser minification with drop_console in production

## Hook Count: 45 (NOT 40)

`find frontend/src/hooks -type f | wc -l = 45`. MEMORY.md claims 40 → **+5 over target** (recent additions, scope creep risk).

## Deprecated Import Survivors (✅ CLEAN)

- `frontend/src/pages/_deprecated/` exists but empty (only Admin subdir leftover)
- 0 active imports from `_deprecated`

## Unprotected Routes (✅ COMPLIANT)

- 9 public routes (login/register/error/404/unauthorized + redirects)
- 40+ feature routes wrapped in `<ProtectedRoute requiredRoles={...}>`

## Top 10 P0 Product-Blockers

| # | Issue | Severity |
|---|---|---|
| 1 | TS build fails — 5 errors block CI/CD | 🔴 P0 |
| 2 | Dead store consumers — useExamStore in 3 active files | 🔴 P0 |
| 3 | Raw fetch() in revolutionaryFeaturesService.ts (19 calls) | 🔴 P0 |
| 4 | 8 missing alt= attributes (WCAG Level A) | 🔴 P0 |
| 5 | 2FA response type mismatch (authStore.ts:155) | 🟡 P1 |
| 6 | ParentDashboardNew declared but never imported (dead) | 🟡 P1 |
| 7 | Hook count +5 over target (scope creep) | 🟢 P2 |
| 8 | useNotificationStore deprecated but imported | 🟡 P1 |
| 9 | OSYMQuestionGeneratorPage:100 duplicate object property | 🟡 P1 |
| 10 | ParentDashboardNew.tsx:43 useCallback arity error | 🟡 P1 |

## Methodology

- TS errors: `npm run type-check` parsed
- Store audit: grep `from.*store/(examStore|notificationStore|uiStore)` + decorator
- Auth: grep `localStorage.getItem.*token`
- API: grep `fetch\(` in services/
- A11y: visual sample 5 components + `<img>` grep
- Bundle: vite.config.ts lines 151-171 review
- Hooks: `find /src/hooks -type f | wc -l`
- Routes: App.tsx lines 216-730 grep
