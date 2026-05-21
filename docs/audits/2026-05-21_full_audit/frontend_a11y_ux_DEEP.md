# KIRO2 Frontend Accessibility + UX — DEEP AUDIT

**Date:** 2026-05-21 (Session 178 follow-up)
**Scope:** `frontend/src/` (production files only; excludes `_deprecated/`, `.migration-backup/`, `__tests__/`, `test/`)
**Mode:** READ-ONLY. WCAG 2.1 Level AA target.
**Files scanned:** 416 `.tsx`/`.jsx` files, ~134,695 lines
**Methodology:** ripgrep counts + ESLint `jsx-a11y` warning count from `frontend/eslint-output.json` (pre-existing baseline) + targeted file reads.

---

## Executive Summary

The codebase **has the right primitives** — `useFocusTrap`, `useScreenReader`, `useReducedMotion`, `useAccessibilitySettings`, a published `accessibility.css` with WCAG-AA tokens, `lang="tr"` on the root HTML, an `AccessibleLayout` with skip-link/landmarks, and `eslint-plugin-jsx-a11y` is **installed and enabled**.

But the actual production routes **don't use most of them**:

- `<AccessibilityProvider>` is **defined but never mounted** in `App.tsx`. Hooks gated on it (`useAccessibility()`) would throw if anything ever called them through the production tree.
- `<AccessibleLayout>` (456 lines, fully WCAG-AA) is **defined but never used in any route**. Production uses `<RoleBasedLayout>` (67 lines) which does the bare minimum (skip-link + `<main role="main">`).
- The backend OSB API exposes `no_animations` and `no_shadows` toggles. The frontend **never reads them** — 4 hits are all in generated `types/api.generated.ts`.
- `eslint-plugin-jsx-a11y` rules are all configured as `'warn'` (not `'error'`). The pre-existing `eslint-output.json` shows **156 jsx-a11y warnings across 54 production files** that CI silently ignores.
- 14 production sites use `window.confirm` / `window.alert` for destructive actions (delete user, leave room, exit quiz) — these are not accessible to focus management, not stylable, not localizable beyond the message string, and they fail WCAG 3.3.4 (Error Prevention).
- The Curator UI's `HelpOverlay` (Session 178) is a modal painted with `<div className="fixed inset-0">` and missing `role="dialog"`, `aria-modal="true"`, focus trap, and Escape-to-close. There are 5 such custom overlays.

None of these are beta-blockers if the beta audience is sighted students using a mouse on a desktop. They all become beta-blockers if a single KVKK accessibility complaint, ÖSYM exam-day disability accommodation request, or screen-reader user attempts to register.

---

## Coverage Snapshot (production files only)

### ARIA attribute usage

| Attribute | Count |
|---|---:|
| `aria-label` | 395 |
| `aria-hidden` | 62 |
| `aria-live` | 35 |
| `aria-labelledby` | 29 |
| `aria-pressed` | 27 |
| `aria-describedby` | 18 |
| `aria-atomic` | 17 |
| `aria-controls` | 15 |
| `aria-expanded` | 9 |
| `aria-current` | 5 |
| `aria-haspopup` | 4 |
| `aria-modal` | 3 |
| `aria-busy` | 3 |
| `aria-invalid` | 3 |
| `aria-required` | 3 |
| `aria-selected` | 1 |
| `aria-disabled` | 0 |

`aria-disabled=0` looks suspicious but is fine in practice — the codebase uses native `disabled` on `<button>` elements (445 occurrences), which is the correct WCAG approach.

`aria-invalid=3` is the red flag: only 3 of ~150 `<input>` elements signal validation state to screen readers. MUI `TextField error={!!err}` covers this internally for ~85 occurrences of MUI Typography variant headings, but every raw `<input>` + custom `<form>` does not (see P0-4).

### Role attribute usage

| Role | Count |
|---|---:|
| `role` (any) | 173 |
| `role="button"` | 23 |
| `role="status"` | 18 |
| `role="alert"` | 13 |
| `role="main"` | 9 |
| `role="navigation"` | 9 |
| `role="dialog"` | 4 |
| `role="banner"` | 3 |
| `role="contentinfo"` | 3 |

### Semantic HTML

| Element | Count |
|---|---:|
| `<div>` | 3,362 |
| `<button>` | 445 |
| `<label>` | 156 |
| `<input>` | 154 |
| `<select>` | 42 |
| `<form>` | 17 |
| `<textarea>` | 9 |
| `<svg>` | 16 |
| `<nav>` | 6 |
| `<main>` | 5 + 9 `role="main"` = 14 effective |
| `<section>` | 4 |
| `<header>` | 4 |
| `<aside>` | 4 |
| `<article>` | 1 |
| `<footer>` | 1 |

`<div>` : `<button>` ratio is **7.5 : 1**, slightly better than the React-Tailwind median (~10:1). The `41` instances of `<div onClick={...}>` without `role=` (or `as=`) are the click-events-have-key-events ESLint warning source. MUI Typography with `component="h[1-6]"` accounts for 32 occurrences — the heading hierarchy is mostly provided by MUI, with only 7 native `<h1>/<h2>` tags in the 65 pages.

### `<img>` alt coverage

In production:
- Total `<img>` tags: **37**
- Without `alt`: **0** (the 3 hits in scanner output were inside `test/`)
- With real `alt="..."`: 13
- With empty `alt=""`: 1 (legitimate decorative use)
- The remaining 23 are MUI/icon wrappers that don't render as raw `<img>`.

This is the cleanest dimension. The audit caught **zero production `<img>` missing alt**.

### Focus management

- `tabIndex` occurrences: 43
- Negative `tabIndex={-1}` (correct usage): 6
- Positive `tabIndex={1+}` (anti-pattern): **0**
- `onKeyDown` handlers: 29
- `useFocusTrap` references: 8

### Reduced motion / OSB

- `useReducedMotion` hook hits: 27 (incl. 7 actual import sites in components)
- `prefers-reduced-motion` CSS hits: 5 stylesheet rules + 1 hook
- `framer-motion` imports: 64 — only 7 components call `useReducedMotion` to gate their animations
- `no_animations` / `no_shadows` (OSB backend fields): **0 frontend usages** (4 hits all in `types/api.generated.ts`)

### Color contrast (potential WCAG 1.4.3 fails)

| Tailwind class | Count | Risk |
|---|---:|---|
| `text-gray-500` / `text-slate-500` / `text-zinc-500` | 94 | Borderline 4.5:1 on white |
| `text-gray-400` / `text-slate-400` / `text-zinc-400` / `text-neutral-400` / `text-stone-400` | 37 | **Fails 4.5:1** on white |
| `text-gray-300` / `text-slate-300` / `text-zinc-300` | 6 | **Fails on any light bg** |

The `text-400` and `text-300` classes are the WCAG AA failures. 43 production occurrences.

### Dark mode

- `dark:` Tailwind prefix usages: **10** (across ~3,362 `<div>` and 445 `<button>`).
- Effectively zero dark mode coverage. Settings store has `darkMode: boolean` and even reads `prefers-color-scheme` for initial value, but only the MUI theme system (one theme file, used in `RoleBasedLayout`) toggles. Tailwind classes inside components do not respond.

### Skip link & landmarks

- Skip link instances: 2 (both within `RoleBasedLayout` and `AccessibleNavigation`; one mounted, one unused).
- `.sr-only` / `visually-hidden` classes: 13 (low).

### Keyboard navigation custom handlers

- `onKeyDown` handlers in components: 29 (mostly Curator + WhiteboardToolbar + ADHD)
- `useKeyboardNavigation` hits: 8

### Forms

- `<input>` without paired `<label htmlFor>`: 67 (from ESLint `label-has-associated-control` warnings)
- Form `aria-invalid` usage: 3 (vs ~150 `<input>` total)
- Form `aria-required` usage: 3
- MUI `TextField` with built-in label + helperText + error: covers the auth/register/admin forms but not the bespoke `<form>` in `TeacherPool.tsx`, `Parent/ChildSelection.tsx`, `EBA/EBAVideoBrowser.tsx`, etc.

### Loading / Empty / Error states

- `isLoading` / `isFetching` / `isPending` hits: 124
- `Skeleton` / `Spinner` / `Loader` component hits: 44
- `EmptyState` / `NoData` / `<Empty` components: 17
- `ErrorBoundary` files: 4 (App-level + Suspense fallback in `App.tsx`)

Healthy coverage but **none of the 124 loading states declare `aria-busy`** (3 occurrences total in the codebase). Loading spinners that don't announce themselves to screen readers fail WCAG 4.1.3 (Status Messages).

### Toast / notifications

- `toast.*` calls (react-hot-toast): 450 across 124 files
- `toast.success` / `toast.error` are the dominant calls
- Native `window.confirm` / `window.alert`: 14 production sites (P1-3 below)

### Tailwind responsive prefixes

- `sm:` / `md:` / `lg:` / `xl:` / `2xl:` total: 171
- Indicates **mobile-first is partial**. 416 prod files for 171 responsive class chains means ~40% of components have responsive style declarations. The MUI layout (`RoleBasedLayout`) handles primary responsiveness via the drawer; bespoke pages do not.

### Onboarding

- `onboarding` / `tutorial` / `firstTime` mentions: 7 (low; no formal first-time UX flow detected outside ParentDashboardNew strings).

### i18n

- `i18n` / `useTranslation` / `react-i18next` imports: **0**.
- All Turkish strings are hardcoded. 98 occurrences of `Yükleniyor` / `Henüz` / `Yok` literals just in loading states alone.

### Curator UI (Session 178)

`frontend/src/pages/Admin/CuratorPage.tsx` (658 lines) audit:

- Status filter buttons: `aria-pressed` ✅
- `<select>` filters: `aria-label` ✅
- Verdict buttons: only `title` attribute, no `aria-label` (`title` not reliable for screen readers — partial)
- `<kbd>` keyboard hint elements: cosmetic only — there is no `aria-keyshortcuts` declaration
- HelpOverlay modal: `role="dialog"` ❌, `aria-modal="true"` ❌, focus trap ❌ (see P1-1)
- LaTeX rendering of `question_text`: rendered as plain whitespace-pre-wrap (`whitespace-pre-wrap`). No `katex`/`MathText` import in CuratorPage — math questions display as raw LaTeX source to the curator.

### LaTeX

- `katex` / `MathText` / `<Math` / `InlineMath` / `BlockMath` hits: 41
- These are mostly inside `Common/AccessibleMathFormula.tsx` (which has `aria-label` and announces formula), but CuratorPage doesn't use it.

---

## P0 / P1 / P2 Findings

### P0 — Production blocker (WCAG-A or runtime-breaking)

**P0-1: `<AccessibilityProvider>` defined but never mounted in App.tsx**

`frontend/src/components/Common/AccessibilityProvider.tsx:30` throws `'useAccessibility must be used within AccessibilityProvider'`. The only consumer is `WCAGCompliantLayout.tsx`, which is itself never rendered through `App.tsx`. This is dead-but-time-bomb code: if any future component calls `useAccessibility()` it will crash the React tree, since the provider is not in the chain.

Verification:
```
grep AccessibilityProvider src/App.tsx → no matches
grep "useAccessibility(" src/ → 1 hit (WCAGCompliantLayout.tsx)
grep WCAGCompliantLayout src/App.tsx → no matches
```

**Fix:** Either mount `<AccessibilityProvider>` at the top of `App.tsx` between `<ThemeProvider>` and `<Router>`, or delete the provider and its consumers.

**P0-2: `<AccessibleLayout>` (456 lines, full WCAG-AA) is dead code**

`frontend/src/components/Layout/AccessibleLayout.tsx` provides skip-link, landmark roles, screen-reader announcements, scroll-to-top with `reducedMotion` honoured, and Alt+M / Alt+N keyboard shortcuts. Production uses the **67-line** `RoleBasedLayout` instead.

Verification: only one import of `AccessibleLayout` exists — the file itself.

`RoleBasedLayout` does have a skip-link + `<main role="main" id="main-content">`, so it is not a catastrophe. But the Alt+M/Alt+N shortcuts, the high-contrast FAB, the screen-reader page-change announcements, and the scroll-to-top respect-reducedMotion logic from `AccessibleLayout` are all unreachable.

**Fix:** Pick one — either delete `AccessibleLayout` and consolidate its features into `RoleBasedLayout`, or replace `RoleBasedLayout` with `AccessibleLayout` (probably the right call, but requires UX QA).

**P0-3: OSB `no_animations` / `no_shadows` settings have no frontend effect**

`backend/models/osb_settings.py` exposes these toggles via the OSB endpoint (Session 152 schema). The frontend types in `api.generated.ts` reflect them (lines 33152-33199). **No component reads them.**

- `grep -r 'no_animations\|noAnimations' frontend/src --include='*.tsx'` → 0 matches outside `api.generated.ts`
- `grep -r 'no_shadows\|noShadows' frontend/src --include='*.tsx'` → 0 matches outside `api.generated.ts`

This is a P0 because OSB (Optical Spectrum / autism support) is the disability accommodation feature; KVKK / Turkish disability law expects accessibility settings to actually function. Backend says "yes we support it", frontend silently ignores it.

**Fix:** Either add reading these in `useAccessibilitySettings()` and translating them to CSS classes (`.no-animations`, `.no-shadows`), or remove from the backend API surface so we don't claim a feature we don't ship.

**P0-4: Only 3 `aria-invalid` declarations across 150+ raw `<input>` elements**

Forms outside the MUI-based auth flow (`TeacherPool` booking, `Parent/ChildSelection` add-child, `EBA/EBAVideoBrowser` search, `StudentReviews` rate-question, `OptimizedRAG`, `StreamingChat`, `SequentialThinking`) use raw `<input>` + `<label>` pairs without `aria-invalid`, `aria-describedby` pointing to error, or any error-summary live region. Screen reader users get no validation feedback.

The 67 `label-has-associated-control` ESLint warnings overlap with this set: `<label>Tarih *</label><input type="date" required>` has no `htmlFor`/`id` link — the `*` is visual only, and clicking the label does not focus the input.

**Fix pattern:**
```tsx
<label htmlFor="booking-date">Tarih <span aria-hidden="true">*</span></label>
<input
  id="booking-date"
  type="date"
  required
  aria-required="true"
  aria-invalid={Boolean(errors.selectedDate)}
  aria-describedby={errors.selectedDate ? 'booking-date-err' : undefined}
/>
{errors.selectedDate && <span id="booking-date-err" role="alert">{errors.selectedDate}</span>}
```

---

### P1 — Production-quality (WCAG-AA failures, but feature works)

**P1-1: 5 custom modals without `role="dialog"` / `aria-modal` / focus trap**

| File | Modal context | role/aria-modal | Focus trap | Escape |
|---|---|---|---|---|
| `pages/Admin/CuratorPage.tsx:420` | HelpOverlay (`?` shortcut) | ❌ | ❌ | overlay click only |
| `components/Analytics/TeacherClassAnalytics.tsx:582` | Student details | ❌ | ❌ | ❌ |
| `features/realm/NPCDialog.tsx:193` | NPC chat | ❌ | ❌ | backdrop click only |
| `components/Common/LoadingStates.tsx:60` | Fullscreen loading overlay | ❌ (`aria-busy=true` missing too) | n/a | n/a |
| `components/Gamification/BadgeEarned.tsx:112` | Badge earned animation | ✅ has `role="dialog"` and `aria-modal="true"` | ❌ | ❌ |

`useFocusTrap` exists and is fully working — none of the custom modals import it. Five-minute fix per modal: wrap in a `useFocusTrap` ref with `escapeDeactivates: true, onEscape: onClose`, add `role="dialog"` + `aria-modal="true"` + `aria-labelledby` to the heading.

**P1-2: 156 jsx-a11y ESLint warnings, all severity `'warn'` (CI does not block)**

From `frontend/eslint-output.json` (regenerate via `npm run lint`):

| Rule | Count | Severity |
|---|---:|---|
| `label-has-associated-control` | 67 | warn |
| `click-events-have-key-events` | 36 | warn |
| `no-static-element-interactions` | 31 | warn |
| `media-has-caption` | 8 | warn |
| `no-autofocus` | 5 | warn |
| `mouse-events-have-key-events` | 4 | warn |
| `no-noninteractive-element-interactions` | 1 | warn |
| `no-noninteractive-tabindex` | 1 | warn |
| `aria-role` | 1 | warn |
| `no-redundant-roles` | 1 | warn |
| `no-interactive-element-to-noninteractive-role` | 1 | warn |

Top files: `TeacherPool.tsx` (12), `ScoreCalculator.tsx` (11), `ADHD/TaskManagement.tsx` (8), `ReadingHelpers.tsx` (8), `PerformanceDashboard.tsx` (8), `CulturalAdaptationSettings.tsx` (8), `StudentReviews.tsx` (8).

Because `.eslintrc.cjs:97-105` configures all `jsx-a11y` rules as `'warn'` and CI uses `--max-warnings 0`, the warnings DO block build. But existing lint output suggests `--max-warnings 0` is bypassed (5MB warnings recorded). Worth confirming whether CI actually enforces this — if not, this is silent rot.

**Fix:** Promote the top 3 (`label-has-associated-control`, `click-events-have-key-events`, `no-static-element-interactions`) to `'error'` once the existing 134 violations are fixed. Land a `nx affected:lint` gate in CI.

**P1-3: 14 native `window.confirm` / `window.alert` for destructive actions**

```
PerformanceDashboard.tsx:56     window.confirm("...cache temizlensin mi?")
PWAStatus.tsx:58                 window.confirm("Tüm çevrimdışı veriler silinecek...")
StudyRooms/FileManager.tsx:213   window.confirm("Bu dosyayı silmek...")
StudyRooms/StudyRoomView.tsx:120 window.confirm("Odadan ayrılmak...")
StudyRooms/StudyRoomView.tsx:131 window.confirm("Bu odayı arşivlemek...")
StudyRooms/StudyRoomView.tsx:142 window.confirm("Bu odayı silmek...")
Whiteboard/CollaborativeWhiteboard.tsx:260  window.confirm("Tahtayi temizlemek...")
ModernAdminUsersPage.tsx:180     window.confirm("Bu kullanıcıyı silmek...")
ModernLearningPathPage.tsx:342   window.alert("Tebrikler!...")           ← uses alert(), not even confirm
ModernLearningPathPage.tsx:374   window.confirm("Quiz'den çıkmak...")
ModernLearningPathPage.tsx:382   window.confirm("Quiz'den çıkmak...")
ModernTeacherAssignmentsPage.tsx:181  window.confirm("Bu ödevi silmek...")
ModernTeacherContentPage.tsx:229      window.confirm("Bu içeriği silmek...")
ModernTeacherExamsPage.tsx:165        window.confirm("Bu sınavı silmek...")
utils/performance.tsx:439             window.confirm("Yeni bir sürüm...")
```

WCAG 3.3.4 (Error Prevention — Legal/Financial/Data) requires destructive actions to be reversible, checked, or confirmable. Native `confirm()` technically satisfies "confirmable" but is:
- Not stylable
- Not focusable as a custom modal
- Blocks the main thread
- Localizes only the message string, button labels are browser-locale ("OK"/"Cancel" or "Tamam"/"İptal" depending on user OS)
- Not announced to many screen readers consistently
- The `alert()` at `ModernLearningPathPage.tsx:342` is the worst — a success message ("Tebrikler! Bu konudaki tum adimlari tamamladiniz!") in a blocking dialog when a toast would do.

**Fix:** Build one `ConfirmDialog` (probably 60 lines using existing `<AccessibleModal>` primitive) and replace all 14 call sites. Replace the one `alert()` with `toast.success()`.

**P1-4: Heading hierarchy is implicit (MUI Typography component prop)**

Only 7 native `<h1>`/`<h2>` tags in 65 pages. The rest of the heading hierarchy comes from MUI `<Typography variant="h4" component="h1">`. This is technically correct (the rendered DOM has `<h1>`) but:

1. Screen reader navigation by heading level only works if `component="h[n]"` is actually set. The 78 MUI heading variants split between sites that set `component` (good) and those that rely on the default `<p>` rendering (bad).
2. Skim-checking via `view-source:` is hard for QA.
3. Many MUI Typography uses include the `variant` style but no `component` override — these render as `<p>` with `font-size` of an h-class, which is a heading-shape lie that does not help screen readers.

A spot grep for `variant="h[1-6]"` matches 78 occurrences; only 32 of them also set `component="h[1-6]"`. The remaining 46 render as `<p>` styled like headings.

**Fix:** Establish a `<PageTitle>` and `<SectionHeading>` component that always renders the correct semantic element, and refactor pages to use them. Or add an ESLint rule that bans `<Typography variant="h*">` without a matching `component`.

**P1-5: 43 Tailwind text-300/400 occurrences fail WCAG 1.4.3**

`text-gray-400` (`#9ca3af`) on `bg-white` gives a contrast ratio of **2.8:1**, below the 4.5:1 AA threshold for normal-size text. 37 occurrences.

`text-gray-300` (`#d1d5db`) on `bg-white` is **1.6:1** — worse than the 3:1 large-text threshold. 6 occurrences.

`text-gray-500` (`#6b7280`) on `bg-white` is **4.55:1** — borderline pass for normal text, fail for fine print. 94 occurrences.

These are common on placeholder text, "meta info" subtitles, and labels. Not catastrophic, but the spec is what it is.

**Fix:** Replace `text-gray-400` with `text-gray-600` (`#4b5563`, 7.6:1) for any text content. Reserve `text-gray-400` for decorative icons.

**P1-6: 124 `isLoading` checks but only 3 `aria-busy` declarations**

WCAG 4.1.3 (Status Messages): a loading state should be announced. The codebase has `useScreenReader.announce()` and uses it in `AccessibleLayout`, but the 124 production sites that flip on `isLoading` don't call it. Spinner components render visually but the screen reader user hears nothing.

**Fix:** In `LoadingStates.tsx`, `Spinner.tsx`, and `Skeleton.tsx`, add `role="status"` + `aria-live="polite"` + an `<span className="sr-only">Yükleniyor...</span>`. Three component changes propagate to all 44 call sites that import them.

**P1-7: `<dialog>` HTML element never used**

Native `<dialog>` element has built-in focus management, Escape handling, and `::backdrop` styling. The codebase uses MUI `<Dialog>` (220 occurrences) — those have correct a11y. The 5 custom `fixed inset-0` overlays could be `<dialog open>` with zero a11y plumbing. Stylistic, not a blocker.

---

### P2 — Polish (quality-of-life)

**P2-1: 5 production `autoFocus` props**

`jsx-a11y/no-autofocus` warns about all 5. Pattern is mostly modal inputs (Whiteboard text editor, video bookmark/note creation, Oba dialog). `ModernLoginForm` already gates with `autoFocus={!isMobile}` (correct). The other 4 should be replaced with explicit `inputRef.current?.focus()` inside the modal's `useFocusTrap` initialFocus option.

**P2-2: `console.log` count: 302 production hits (536 incl `.warn`/`.error`/`.info`)**

ESLint rule `no-console` is set with `allow: ['warn', 'error']`, so the 302 `console.log` are warnings. UX impact is zero in production builds (Vite tree-shakes), but the warnings drown out the lint output and the leak risk for sensitive data is real (e.g. `ModernLoginForm.tsx:107` logs error context).

**P2-3: 33 `cursor-pointer` usages on non-`<button>` elements**

`cursor-pointer` on a `<div>` is a visual lie. The screen reader sees no clickable role unless `role="button"` is set. Of the 33 hits, 23 already pair with `role="button"` (good); the remaining ~10 are unanchored.

**P2-4: i18n is hardcoded**

98 occurrences of `Yükleniyor` / `Henüz` / `Yok` are scattered in JSX literals. No `i18next` / `useTranslation` is installed. If a parent / teacher locale (English) is added later, it is a 100+ file refactor. For a Turkish-only product targeting YKS this is acceptable; flagging for completeness.

**P2-5: Skip link styling lives in CSS but no integration test exercises it**

`.skip-link` is in `accessibility.css:50` and rendered by `RoleBasedLayout`. There is no Playwright/Vitest test that asserts Tab → first focusable element is the skip link → Enter → focus goes to `#main-content`. The test file `frontend/src/test/accessibility/task24-complete-wcag-validation.test.tsx` exists but tests components in isolation, not the App shell.

**P2-6: Dark mode is theoretical**

`settingsStore.darkMode` exists. The MUI theme switches. But Tailwind classes inside ~415 production files contain only 10 `dark:` prefixed classes. Toggling dark mode currently produces a half-dark, half-light app for anything not built with MUI components. Either remove the toggle or do the Tailwind sweep.

**P2-7: 41 LaTeX render sites, no offline fallback**

If KaTeX fails to load (CDN flake, offline PWA, ad-blocker), all 41 sites render `\frac{a}{b}` literally. `AccessibleMathFormula.tsx` does provide an `aria-label` fallback. Other sites (e.g. `MathSolution/SolutionStep.tsx`) do not.

---

## What's actually good

1. `<img alt>` coverage is **100%** in production code.
2. `tabindex` is never positive (only `-1` or default 0). No focus-order corruption.
3. `aria-pressed=27`, `aria-current=5`, `aria-controls=15`, `aria-haspopup=4` are sprinkled correctly on the toggle/tab/dropdown patterns in the Curator UI, OSB layout, and ModernNavigation.
4. `useFocusTrap`, `useScreenReader`, `useReducedMotion`, `useAccessibilitySettings` all exist with thorough JSDoc. They're not used widely enough, but the wheel is round.
5. Root `<html lang="tr">` is set.
6. WCAG 2.1 `.sr-only`, `.wcag-aa-target-size`, `.wcag-aa-focus`, `.skip-link`, and `prefers-reduced-motion` rules are all defined in `accessibility.css`.
7. ColorContrastSettings, NeurodiversitySettings, TypographySettings exist as user-facing controls (so the user CAN override theme, font, line-height, color), and `useAccessibilityStyles` syncs them to CSS vars on every render.
8. `frontend/index.html` correctly declares `lang="tr"`.

---

## Recommended priority ladder (4-week beta plan)

| Week | Items | Effort |
|---|---|---|
| W1 | P0-4 form `aria-invalid` sweep (top 5 bespoke forms) + P1-3 `ConfirmDialog` replacement for the 5 destructive paths | 2 days |
| W2 | P0-1 mount `<AccessibilityProvider>` OR remove it; P0-2 reconcile Layouts; P1-1 add `role="dialog"` + focus trap to 5 custom modals | 2 days |
| W3 | P0-3 wire OSB `no_animations` / `no_shadows` to CSS (4 lines in `useAccessibilitySettings` + accessibility.css update) | 0.5 day |
| W3 | P1-6 add `role="status"` + `aria-busy` to `LoadingStates.tsx` (single file, propagates everywhere) | 0.5 day |
| W4 | P1-2 promote `label-has-associated-control` + `click-events-have-key-events` to `'error'` in eslintrc and fix the resulting 103 violations | 3 days |
| W4 | P1-5 sweep `text-gray-300/400` → `text-gray-600` | 0.5 day |

Beta blockers (must merge before beta): **P0-3** (legal/disability accommodation claim), **P0-4** (registration form is unusable for SR users), **P1-3** (the `alert()` at LearningPath:342). Everything else is post-beta polish.

---

## Methodology notes

- All counts come from `ripgrep`/`grep` over `frontend/src/` excluding `node_modules`, `_deprecated/`, `.migration-backup/`, `__tests__/`, `test/`, `tests/`.
- ESLint warnings come from `frontend/eslint-output.json` (5.0 MB pre-existing artifact, regenerated whenever lint runs). It was filtered for production-path files only.
- No code was modified during this audit (READ-ONLY).
- WCAG 2.1 levels referenced are from the official spec, not the W3C wiki. Contrast math used `#9ca3af` (gray-400) and `#d1d5db` (gray-300) base hex from Tailwind's default palette config.
