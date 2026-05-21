# Frontend Component Architecture + Complexity Deep Audit

**Tarih:** 2026-05-21
**Kapsam:** `frontend/src/**` — 706 toplam .tsx/.ts dosyası
**Metodoloji:** READ-ONLY static analysis. LOC + AST-proxy (grep) + import graph.

---

## 1. Executive Summary

- **Toplam dosya:** 706 .tsx/.ts (439 .tsx, 315 non-generated .ts)
- **Aktif componentler (non-test, non-deprecated):** 377 .tsx
  - `components/`: 107 dosya (alt dizin sayılmadı)
  - `pages/`: 39 dosya
- **Custom hooks:** 34 dosya `hooks/` + 6 `hooks/queries/` = **40 hook** (Memory'de "47" yazıyor, gerçekte 40)
- **Zustand stores:** 5 (`authStore`, `examStore`, `notificationStore`, `settingsStore`, `uiStore`) — ama yalnızca `authStore` yaygın kullanımda (29 component). `examStore`, `notificationStore`, `uiStore` neredeyse hiç tüketilmiyor.
- **Lazy routes:** 58 (App.tsx içinde `lazy(...)` çağrısı). `<Route ...>` say 70.
- **Deprecated dosyalar:** 45 .tsx (`_deprecated/` altında), aktif kod tabanında değil ama hâlâ disk'te.
- **Bilinen büyük dosya:** ModernLearningPathPage.tsx **1,165 LOC** — DOĞRULANDI. Daha kötüsü: DuelMode.tsx **1,072 LOC**.
- **Test:** 86 .test.tsx + 25 .test.ts (vitest), `__tests__/` altında 8,000+ LOC sadece test dosyaları.

**En sıkıntılı tek dosya:** `pages/ModernLearningPathPage.tsx` — 1,165 LOC, 14 useState + 13 useCallback + 4 useMemo + 6 inline fetch + 82 derin JSX nesting.

---

## 2. File size distribution

### TSX (production code, non-test, non-deprecated): 377 dosya

| Range | Count | % | Verdict |
|---|---|---|---|
| <100 LOC | 75 | 20% | Healthy |
| 100-300 | 167 | 44% | Healthy |
| 300-500 | 119 | 32% | OK |
| **500-800 (warn)** | **71** | **19%** | Refactor candidate pool |
| **800-1000 (red flag)** | **4** | **1%** | Split required |
| **>1000 (critical)** | **3** | **0.8%** | Hard split required |

### Tüm dosyalar (.tsx + .ts, test dahil): 706 dosya, dağılım kabaca aynı (test dosyaları da uzun).

### Önemli anomaliler

- **`types/api.generated.ts` = 77,286 LOC** — OpenAPI codegen, auto-generated, normaldir. `types/index.ts` = 741 LOC ELDE YAZILMIŞ, refactor adayı.
- **`api.ts` = 1,413 LOC** (top-level) — tek dosyada tüm API çağrıları toplanmış. Service layer parçalanmamış. KRİTİK refactor adayı.
- **`services/revolutionaryFeaturesService.ts` = 970 LOC** — tek service mega-file.

---

## 3. Top 20 largest components (non-test, non-deprecated, .tsx)

| # | LOC | File | Concerns |
|---|---|---|---|
| 1 | **1,165** | `pages/ModernLearningPathPage.tsx` | 14 useState, 13 useCallback, 4 useMemo, 82 deep nest, 6 direct fetch — God Page |
| 2 | **1,072** | `components/LearningPath/DuelMode.tsx` | 17 useState, 7 useCallback, 4 useEffect — God Component, no useMemo |
| 3 | **1,011** | `components/Exam/OSYMExamInterface.tsx` | 16 hooks, ama "Refactored" varyantı var (265 LOC) — dual version drift |
| 4 | 890 | `pages/ModernSettingsPage.tsx` | **192 deep nest** (en yüksek!), inline `useState({ ... })` initial object |
| 5 | 850 | `components/Chat/TurkishChatInterface.tsx` | 19 hooks |
| 6 | 824 | `pages/ModernTeacherContentPage.tsx` | 14 hook, 77 nest |
| 7 | 822 | `pages/_deprecated/ZPDMaarifVisualizationPage.tsx` | DEPRECATED |
| 8 | 792 | `pages/_deprecated/TextSimplificationPage.tsx` | DEPRECATED |
| 9 | 789 | `pages/SystematicDebuggingPage.tsx` | useEffect with `[]` deps (stale closure) |
| 10 | 786 | `components/Analytics/AdminSystemAnalytics.tsx` | 154 deep nest, 8 hook |
| 11 | 782 | `components/Common/AccessibleVideoPlayer.tsx` | **36 hook calls** (en yüksek hook density), 47 hook |
| 12 | 777 | `components/Quiz/QuizInterface.tsx` | 13 hook, 52 nest |
| 13 | 774 | `pages/ModernStudentDashboard.tsx` | Dashboard god page, 10 hook, 59 nest, 31 inline `={{` |
| 14 | 767 | `components/Exam/ModernOSYMExamInterface.tsx` | DUPLICATE of #3 with "Modern" prefix |
| 15 | 766 | `App.tsx` | 58 lazy imports, 70 routes — büyük ama amaç doğrultusunda |
| 16 | 764 | `pages/_deprecated/BionicReadingPage.tsx` | DEPRECATED |
| 17 | 759 | `components/Revolutionary/MultiAgentCoordination.tsx` | 11 hook |
| 18 | 733 | `components/LearningPath/ModernLearningPathVisualizer.tsx` | 17 hook |
| 19 | 727 | `pages/ModernAdminUsersPage.tsx` | 14 hook, 74 nest, inline `useState({...})` |
| 20 | 727 | `components/Exam/ModernExamStart.tsx` | Form-heavy |

### Composite complexity score (LOC + 5×hooks + 2×nest) — Top 15

```
1514  1165 LOC, 37 hooks, 82 nest  →  pages/ModernLearningPathPage.tsx
1344   890       , 14       , 192       →  pages/ModernSettingsPage.tsx
1290  1072       , 42       , 4         →  components/LearningPath/DuelMode.tsx
1182  1011       , 23       , 28        →  components/Exam/OSYMExamInterface.tsx
1134   786       , 8        , 154       →  components/Analytics/AdminSystemAnalytics.tsx
1048   824       , 14       , 77        →  pages/ModernTeacherContentPage.tsx
1045   782       , 47       , 14        →  components/Common/AccessibleVideoPlayer.tsx
 980   850       , 22       , 10        →  components/Chat/TurkishChatInterface.tsx
 956   777       , 15       , 52        →  components/Quiz/QuizInterface.tsx
 945   727       , 14       , 74        →  pages/ModernAdminUsersPage.tsx
 942   774       , 10       , 59        →  pages/ModernStudentDashboard.tsx
 938   759       , 11       , 62        →  components/Revolutionary/MultiAgentCoordination.tsx
 931   767       , 20       , 32        →  components/Exam/ModernOSYMExamInterface.tsx
 925   691       , 10       , 92        →  pages/ModernProfilePage.tsx
 924   733       , 17       , 53        →  components/LearningPath/ModernLearningPathVisualizer.tsx
```

---

## 4. JSX nesting depth (refactor candidates)

**Heuristic:** indented `≥16` spaces içinde JSX tag açılışı. Bu kabaca **>4 seviye** nesting demek.

| Nest count | File | Comment |
|---|---|---|
| **192** | `pages/ModernSettingsPage.tsx` | EN YÜKSEK — ayar formları flat tablar değil, iç içe accordion |
| 154 | `components/Analytics/AdminSystemAnalytics.tsx` | Chart + tab + grid panel iç içe |
| 123 | `pages/_deprecated/TextSimplificationPage.tsx` | _deprecated |
| 114 | `pages/_deprecated/ZPDMaarifVisualizationPage.tsx` | _deprecated |
| 103 | `components/Teacher/ClassReport.tsx` | |
| 101 | `components/Revolutionary/IRTMorphologyAnalysis.tsx` | |
| 100 | `components/Analytics/StudentAnalyticsDashboard.tsx` | |
| 92 | `pages/ModernProfilePage.tsx` | |
| 91 | `components/EbaTV/EbaTVDashboard.tsx` | |
| 82 | `pages/ModernLearningPathPage.tsx` | Tab + dialog + quiz iç içe |

`ModernSettingsPage` settings panel paradigması Material-UI iç içe `<Accordion>` + `<Tab>` + `<Card>` yığını — küçük parçalara bölünmesi gerek.

---

## 5. Re-render risk findings

### 5.1 useState inline object/array initializer

15 dosyada inline obj/array initial state (lazy init kullanılmamış). Mount sırasında allocation, ama setState sonrası tekrar değil — sınırlı sorun. Yine de form-heavy sayfalarda dikkat:

```
pages/ModernAdminUsersPage.tsx:78        const [newUser, setNewUser] = useState({ ... })
pages/ModernProfilePage.tsx:59           const [preferences, setPreferences] = useState({ ... })
pages/ModernSettingsPage.tsx:59          const [settings, setSettings] = useState({ ... })
pages/ModernTeacherAssignmentsPage.tsx   const [newAssignment, setNewAssignment] = useState({ ... })
pages/ModernTeacherClassesPage.tsx       const [newClass, setNewClass] = useState({ ... })
pages/ModernTeacherContentPage.tsx       const [newContent, setNewContent] = useState({ ... })
pages/ModernTeacherExamsPage.tsx         const [formData, setFormData] = useState({ ... })
components/Accessibility/ADHD/TaskManagement.tsx:125  const [newTask, setNewTask] = useState({ ... })
components/Admin/ContentManagement.tsx (2x)
components/Dashboard/ProfileEditor.tsx:102            const [formData, setFormData] = useState({ ... })
components/Exam/ExamTimer.tsx:98                      const [hasShownWarnings, setHasShownWarnings] = useState({ ... })
```

**Yapılması gereken:** Form state pattern: react-hook-form veya Zustand draft-state. 7 farklı form sayfasında tekrarlayan pattern.

### 5.2 useEffect with `[]` deps (potential stale closure)

Yalnızca **1 dosya:** `pages/SystematicDebuggingPage.tsx` — bu sayfa için kabul edilebilir (debug page). Aktif tehlike DEĞİL.

### 5.3 Inline `onClick={() =>` count (per file, top 10)

| count | file | comment |
|---|---|---|
| 30 | `components/Accessibility/Dyscalculia/ScientificCalculator.tsx` | Hesap makinesi her tuş = inline fn, calculator için tipik |
| 16 | `components/StudyRooms/FileManager.tsx` | Refactor adayı |
| 13 | `components/Accessibility/ReadingHelpers.tsx` | |
| 11 | `components/Accessibility/Dyscalculia/NumberBlocks.tsx` | |
| 10 | `pages/Admin/CuratorPage.tsx` | Action button cluster — bağlamsal |
| 9 | `components/Accessibility/Dyscalculia/GeometryTools.tsx` | |
| 8 | `components/StudyRooms/ChatInterface.tsx` | |
| 8 | `components/Revolutionary/FSRSScheduler.tsx` | |
| 8 | `components/LearningPath/ModernLearningPathVisualizer.tsx` | List of nodes, useCallback ile çözülebilir |
| 8 | `components/Exam/QuestionNavigation.tsx` | List of question buttons — `key`'li `.map()`'ten useCallback'li handler'a |

**Genel olarak:** inline arrow tek başına perf sorunu değil, ama `React.memo` ile sarılmış child component varsa her parent re-render'da child da render. Mevcut `React.memo` kullanımı: 13 dosya (377'den). Yani çoğu component memo'lanmamış → inline arrow tehlikesi düşük.

### 5.4 Inline JSX object/array prop (yeni allocation)

Top dosyalar:
```
45  pages/SystematicDebuggingPage.tsx          (debug page, kabul edilebilir)
38  components/Revolutionary/ZPDMaarifDashboard.tsx
34  components/LearningPath/DuelMode.tsx
31  pages/ModernStudentDashboard.tsx
31  pages/ModernLearningPathPage.tsx
30  pages/ModernSettingsPage.tsx
30  components/Chat/TurkishChatInterface.tsx
25  components/Revolutionary/MultisensoryLearning.tsx
24  pages/ParentDashboard.tsx
24  components/Revolutionary/MultiAgentCoordination.tsx
```

Bu pattern + `useEffect` deps array içinde aynı object → infinite render riski. Manuel inceleme tavsiye edilir; statik tarama kesin söyleyemez.

---

## 6. Hook density (split candidates)

### 25 component'te ≥12 hook çağrısı. Top 10:

| Hook count | File |
|---|---|
| **36** | `components/Common/AccessibleVideoPlayer.tsx` (782 LOC) |
| **29** | `components/StudyRooms/Whiteboard/CollaborativeWhiteboard.tsx` |
| **28** | `pages/ModernLearningPathPage.tsx` (1165 LOC) |
| 26 | `components/LearningPath/DuelMode.tsx` (1072 LOC) |
| 24 | `components/StudyRooms/VideoConference/VideoConference.tsx` |
| 21 | `components/Accessibility/Dyscalculia/GraphPlotter.tsx` |
| 19 | `components/Navigation/AccessibleNavigation.tsx` (649 LOC) |
| 19 | `components/Chat/TurkishChatInterface.tsx` (850 LOC) |
| 18 | `components/LearningPath/OnboardingWizard.tsx` (orphan!) |
| 17 | `pages/BossFightPage.tsx` (298 LOC) |

**Rule of thumb:** >15 hook çağrısı = state machine extract veya custom-hook çıkar. `AccessibleVideoPlayer` (36) çok dağıtık.

### useCallback / useMemo / memo kullanım dağılımı

- **useCallback:** 66 dosya (377'nin %17.5'i)
- **useMemo:** 22 dosya (%5.8)
- **React.memo:** 13 dosya (%3.4)

→ Memoization yetersiz. ~%82 component memo / callback / useMemo kullanmıyor. Liste-render eden component'ler için sorun.

---

## 7. Prop drilling

**Heuristic:** `props.X` access pattern.

| count | prop |
|---|---|
| 5 | `onRetry` |
| 4 | `onError` |
| 4 | `fallback` |
| 2 | `resetKeys` |
| 2 | `children` |
| 1 | `value` |
| 1 | `listName` |

**Yorum:** Düşük sinyal — `props.X` kullanımı az çünkü dest. yaygın. Real drilling olmuş olmuş olabilir ama bu heuristic'te görünmüyor. Manuel inceleme: `ModernLearningPathPage` props chain'i (PathVisualizer → NodeDetails → QuizPanel) muhtemel drill noktası.

---

## 8. Hook usage frequency

40 custom hook'tan **9 hook hiç kullanılmıyor** veya yalnızca tek yerde:

### En çok kullanılanlar (top 10)
```
9  useScreenReader
8  useAccessibilitySettings
5  useGamification
4  useRoleAccess
3  useAutoSave
2  useStreaming
2  useKeyboardNavigation
2  useExamTimer
2  useDungeonMap
```

### 1 kez kullanılan hooks (potansiyel orphan veya gereksiz abstraction)

`useSequentialThinking`, `useReducedMotion`, `useReadingHelpers` (649 LOC!), `usePlacementSession`, `usePerformanceMonitor`, `usePWA`, `usePDFGeneration`, `useNotification`, `useNeurodiversityPrefs`, `useMathSolution`, `useLearningPathVideos`, `useLearningPath`, `useKeyboardShortcuts`, `useFocusTrap`, `useExamWebSocket`, `useExamResults`, `useCATSession`, `useCuratorQueue` (S178 yeni)

**KISS/YAGNI ihlali sinyali:** 18 hook tek-kullanımlı. Bunlar inline çekilse component'ler daha okunabilir olur. Ama bazıları (`useCuratorQueue`, `useExamWebSocket`) gerçekten reusable interface — manuel triaj gerek.

### Hook LOC top 5

```
649 hooks/useReadingHelpers.ts          ← çok büyük tek-kullanımlık hook
476 hooks/useLearningPath.ts            ← tek kullanım, ama core feature
435 hooks/useKeyboardNavigation.ts
398 hooks/useGamification.ts            ← 5 kullanım, makul
377 hooks/useScreenReader.ts            ← 9 kullanım, makul
```

`useReadingHelpers.ts` 649 LOC ve tek-kullanım → hook DEĞİL, bu bir feature module. Hook adı altında saklanan büyük dosya.

---

## 9. Dead code / orphan components

Heuristic taraması (372 component): **54 orphan candidate** bulundu. Bazıları false positive (dynamic import veya barrel `index.ts` üzerinden import edilenler), ama spot-check ile **kesin orphan'lar:**

### Kesin orphan (0 import, dosya kendisi dışında)

| LOC | File |
|---|---|
| 212 | `components/Exam/AdvancedExamResultsRefactored.tsx` (Refactor-then-abandon) |
| 413 | `components/Exam/ModernExamInterface.tsx` (Modern but no Modern caller) |
| 465 | `components/Exam/AYTOptikForm.tsx` |
| ~600 | `components/LearningPath/OnboardingWizard.tsx` |
| 577 | `components/Exam/ExamHistory.tsx` |
| ~200 | `components/Examples/DashboardWithErrorHandling.tsx` (Example/demo) |
| ~200 | `components/Examples/ErrorHandlerDemo.tsx` (demo) |
| ~? | `components/Common/AccessibleTable.tsx` (sadece test dosyası tarafından import) |
| ~? | `components/Common/ListErrorBoundary.tsx` |
| ~? | `components/Common/ComingSoon.tsx` |
| ~? | `components/Common/Notification.tsx` |
| ~? | `components/Dashboard/{GoalManager,NotificationPanel,ProfileEditor}.tsx` |
| ~? | `components/Layout/{AccessibleLayout,ModernLayout}.tsx` |
| ~? | `components/LearningPath/{AccessibilitySettings,AdaptiveFeedbackPanel,MasteryConfidenceBar,ProactiveCoachWidget,SkillGraphView}.tsx` |
| ~? | `components/MathSolution/{AlternativeSolutionsViewer,ErrorHighlight,SolutionComparison,StepByStepSolution}.tsx` (4 dosya MathSolution tamamen ölü?) |
| ~? | `components/Parent/ChildPerformanceView.tsx` |
| ~? | `components/Revolutionary/{MultisensoryLearning,VisualSupports}.tsx` |
| ~? | `components/ui/AccessibilityAnnouncer.tsx` |
| ~? | `components/VideoLoadingUI.example.tsx` (`.example.` suffix — sample) |

**Refactored-then-abandoned pattern (sinyal):**
- `components/Exam/AdvancedExamResultsRefactored.tsx` → 0 refs
- `components/Exam/OSYMExamInterfaceRefactored.tsx` → 1 ref (kendi dışında)
- `pages/_deprecated/LearningPathPageRefactored.tsx` → _deprecated

Anlam: Refactor çalışmaları yarım kaldı, eski versiyon hâlâ kullanılıyor. Bilinçli karar mı yoksa unutulmuş çöp mü? Manuel triaj gerek.

### Top-level `components/*.tsx` (alt klasörsüz) — organizasyon kokusu

12 dosya organize edilmemiş:
```
KnowledgeGraphViz.tsx, OfflineModeUI.tsx, OptimizedRAG.tsx, PWAStatus.tsx,
PerformanceDashboard.tsx, QuestionGeometry.tsx, QuestionGraph.tsx,
QuestionMapDiagram.tsx, QuestionTable.tsx, StreamingChat.tsx,
VideoLoadingUI.example.tsx (orphan), VideoLoadingUI.tsx
```

`Question*.tsx` 4 dosya — `components/Questions/` altına taşınmalı.

---

## 10. State management consistency

| Pattern | Component count |
|---|---|
| `useState` (local state) | **250 / 377** (%66) |
| `useAuthStore` (Zustand) | 29 (%8) |
| `useExamStore` (Zustand) | **1** (orphan store!) |
| `useNotificationStore` (Zustand) | **1** (orphan store!) |
| `useSettingsStore` (Zustand) | 4 |
| `useUIStore` (Zustand) | **0** (TAMAMEN ÖLÜ store!) |
| `useContext` (React context) | 5 |
| `useReducer` | ~0 (grep'te görünmedi) |
| Mixed (Zustand + useState) | 22 |

**KRİTİK BULGU:**
- **3 Zustand store ölü/orphan:** `examStore`, `notificationStore`, `uiStore` — 5 store'un 3'ü kullanılmıyor. KISS ihlali, dead state machinery.
- Yalnızca `authStore` ciddi tüketim alıyor. Belki tüm 5 store gerekli değildi.
- `useContext` 5 yer — `AuthProvider` + birkaç düşük-trafikli context.
- `useReducer` yok — kompleks state geçişleri yine `useState` ile.

---

## 11. Component naming convention

### PascalCase ihlalleri (lowercase tsx)
```
components/AgentChat/index.tsx              ← barrel, kabul edilebilir
components/Manipulatives/index.tsx           ← barrel
components/StudyRooms/index.tsx              ← barrel
components/StudyRooms/VideoConference/index.tsx
components/StudyRooms/Whiteboard/index.tsx
components/ui/alert.tsx                      ← shadcn convention?
components/ui/badge.tsx
components/ui/button.tsx
components/ui/card.tsx
components/ui/input.tsx
```

`components/ui/*` shadcn-ui konvansiyonu (lowercase). 18 file. Kabul edilebilir ama PascalCase export `Button`/`Card`/`Input` ile bir tutarsızlık — diğer 21 component dir PascalCase isimli.

**Tutarsızlık:** `components/Common/Notification.tsx` (TS naming) vs `components/ui/alert.tsx` (shadcn naming). İki paradigm aynı projede.

---

## 12. KIRO2-specific feature analysis

| File | LOC | useState | useEffect | useCallback | useMemo | JSX nest | fetch | onClick arrow | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| `pages/Admin/CuratorPage.tsx` | 658 | 6 | 4 | 4 | 3 | 3 | 0 | 10 | OK — hook helper'a delegate (useCuratorQueue) |
| `pages/SoruMeydaniPage.tsx` | 325 | **16** | 2 | 2 | 0 | 21 | 0 | 7 | useState fazla — useReducer / state machine adayı |
| `pages/ObaSeferleriPage.tsx` | 232 | 8 | 2 | 2 | 0 | 26 | 0 | 1 | OK, ama 26 nest yüksek (232 LOC'ta) |
| `pages/UstaCirakPage.tsx` | 188 | 7 | 2 | 2 | 0 | 14 | 0 | 1 | OK |
| `pages/CozumDuellosuPage.tsx` | 286 | 10 | 2 | 2 | 0 | 23 | 0 | 2 | OK |
| `pages/BossFightPage.tsx` | 298 | **14** | 3 | 2 | 0 | 3 | 0 | 5 | useState fazla — battle state karmaşık |
| `pages/PhotoAskPage.tsx` | 418 | 8 | 2 | 6 | 0 | 18 | 3 | 5 | Direct fetch! service'e taşınmalı |
| `pages/ModernLearningPathPage.tsx` | **1165** | 14 | 3 | 13 | 4 | 82 | 6 | 3 | **GOD PAGE** — 6 direct fetch, 82 nest, hard split lazım |
| `pages/DuelPage.tsx` | 338 | 9 | 2 | 2 | 0 | 12 | 0 | 2 | OK |
| `components/LearningPath/DuelMode.tsx` | **1072** | 17 | 4 | 7 | 0 | 4 | 0 | 1 | **GOD COMPONENT** — 0 useMemo, 17 useState |

### `Bilge Alp` özelliği
- **`pages/BilgeAlpPage.tsx` BULUNAMADI.**
- Memory'de Bilge Alp = AI tutor olarak bahsediliyor ama frontend page'i yok. Backend feature varsa frontend entry point eksik VEYA başka isimle kayıtlı.

### `Soru Meydani` (question arena)
- `pages/SoruMeydaniPage.tsx` (325 LOC) — kabul edilebilir boy. Ama 16 useState çok, state machine ile basit XState veya useReducer pattern uygulanabilir.

### `OBA Seferleri / Usta-Çırak / Çözüm Düellosu`
- Sadece sayfa formatında (`pages/*.tsx`), **alt component dizini yok**. Memory'de "`components/OBASeferleri/`" gibi dizinlerden bahsediliyor ama yoklar. Tüm logic tek sayfada yazılmış.

### `CuratorPage` (Session 178)
- 658 LOC, fakat **iyi yapılandırılmış**: `useCuratorQueue` + `useCuratorStats` + `useCuratorVerdict` + `useKeyboardShortcuts` hook'larına logic delegate edilmiş. Inline `useState` sadece 6. JSX nest 3. Yeni eklenen kod **mevcut diğer 700+ LOC sayfalardan daha temiz**.

---

## 13. UI library inconsistency

- **MUI (`@mui/material`):** 221 / 377 dosya (%59)
- **TailwindCSS (className-based):** 158 / 377 dosya (%42)
- **Hem MUI hem Tailwind aynı dosyada:** **25 dosya** (mix style systems)

→ Style sistem tutarsızlığı. MUI sx prop ile Tailwind class aynı componentte birlikte. Görsel olarak sorun yaratmaz ama bundle size ikiye katlanır + theming çakışması olabilir.

`shadcn/ui` (`components/ui/`) → 3. style system (Radix + Tailwind). Üç paradigm bir projede.

---

## 14. _deprecated/ klasörü

- 45 .tsx + 7 yardımcı = **52 dosya _deprecated**
- 822 LOC `ZPDMaarifVisualizationPage`, 792 LOC `TextSimplificationPage`, 764 LOC `BionicReadingPage` — büyük dosyalar bekliyor
- Disk'te kalıyor ama hiçbir aktif route bunları import etmiyor (.claude/rules/deprecation-guard.md var)

**Yapılması gereken:** Silinmek üzere işaretle, 1-2 sprint sonra disk'ten kaldır.

---

## 15. Service layer / direct fetch

- **30 service dosyası** (`services/*.ts`), 10,455 LOC toplam
- `services/revolutionaryFeaturesService.ts` = 970 LOC — split adayı
- **15 dosyada direct `fetch(` çağrısı >2 kez:**
  - `pages/ModernLearningPathPage.tsx` (6 direct fetch) — service'e taşınmalı
  - `components/Khan/KhanDashboard.tsx` (8)
  - `pages/PhotoAskPage.tsx` (3)
  - `components/TeacherPool/TeacherPool.tsx` (6)
  - `components/Admin/ContentManagement.tsx` (6)

→ Service abstraction bütün API çağrıları için zorunlu değil. Bazı sayfalarda hâlâ inline fetch.

---

## 16. Refactor priorities

### P0 — Acil (1165+ LOC ve aktif olarak modifiye ediliyor)

1. **`pages/ModernLearningPathPage.tsx`** (1165 LOC, 82 nest, 6 direct fetch)
   - Action: 3-4 alt sayfa veya tab component'ine böl: `LearningPathOverview`, `QuizPanel`, `InterleavedSession`, `DuelLaunchPanel`
   - Direct fetch'leri `services/learningPathService.ts`'e taşı
   - State'i `useReducer` veya XState ile yönet

2. **`components/LearningPath/DuelMode.tsx`** (1072 LOC, 17 useState, 0 useMemo)
   - Action: `useReducer` + child component split (DuelArena, DuelHud, DuelTimer, DuelResults)

3. **`components/Exam/OSYMExamInterface.tsx`** (1011 LOC)
   - Action: `OSYMExamInterfaceRefactored.tsx` (265 LOC) zaten var — orijinal mi yoksa refactor mu kullanılacak karar verilmeli, biri kaldırılmalı

### P1 — Önemli

4. `pages/ModernSettingsPage.tsx` (890 LOC, **192 nest**) — accordion/tab split
5. `components/Common/AccessibleVideoPlayer.tsx` (782 LOC, **36 hook**) — custom hook çıkar (`useVideoControls`, `useVideoCaptions`)
6. `api.ts` (1413 LOC root) — domain bazında parçala (authApi, examApi, ...)
7. `services/revolutionaryFeaturesService.ts` (970 LOC) — feature başına split
8. `hooks/useReadingHelpers.ts` (649 LOC, tek-kullanım) — hook değil, modül; uygun yere taşı

### P2 — Temizlik

9. **Orphan component'leri sil** (~30 kesin orphan, ~8000+ LOC çöp)
10. **`Refactored.tsx` varyantlarını birleştir** (3 dosya)
11. **Top-level `components/*.tsx` dizine taşı** (12 dosya, özellikle `Question*.tsx` → `Questions/`)
12. **3 ölü Zustand store sil**: `examStore`, `notificationStore`, `uiStore` (yalnızca `authStore` ve `settingsStore` aktif)
13. **`_deprecated/` siligi planla** (45 dosya, 1-2 sprint görünürlük sonra)
14. **MUI/Tailwind/shadcn üçlüsünü** standart bir paradigma altında topla (en azından mix'i 25→0)

### P3 — İzleme

15. **Memoization audit**: 377 component'in %82'si memo/callback/useMemo kullanmıyor — liste-render eden componentleri spot-fix
16. **18 tek-kullanımlı hook'u triaj** — gerçekten reusable mı yoksa premature abstraction mı?

---

## 17. Bilinen pozitif noktalar

- **CuratorPage (Session 178)** temiz mimari örneği: 658 LOC ama logic 4 ayrı hook'a delegate, JSX nest 3, sadece 6 useState. Yeni eklenen kod kalitesi yükseliyor.
- **Code-splitting iyi:** 58 lazy route, ~%40-50 bundle azaltma. PageSkeleton fallback var.
- **Test coverage cover ediyor:** 86 .test.tsx — özellikle StudyRooms ve VideoAnalytics test ağırlığı yüksek (`__tests__/` 750-1078 LOC).
- **Hooks dizini ayrı** (40 hook), business logic component'lerden ayrılmış.

---

## 18. Numerical summary table

| Metric | Value |
|---|---|
| Toplam frontend src dosya | 706 |
| Aktif .tsx (non-test, non-deprecated) | 377 |
| Custom hooks | 40 |
| Zustand stores (aktif) | 2 / 5 |
| Lazy routes | 58 |
| Deprecated dosyalar | 52 |
| Orphan candidate | ~30 (54 raw, ~24 false positive) |
| >1000 LOC dosya | 3 (`ModernLearningPathPage`, `DuelMode`, `OSYMExamInterface`) |
| >800 LOC dosya (warn) | 7 (3 critical + 4 dahil) |
| 500-800 LOC dosya | 71 |
| JSX nest >50 | 18 file |
| Hook density >15 | 8 file |
| Inline `onClick={() =>` >5 | 16 file |
| useState inline obj | 15 file |
| Mixed MUI+Tailwind | 25 file |
| Direct fetch (no service) | 15 file |
| useCallback usage | 66 file (%17.5) |
| useMemo usage | 22 file (%5.8) |
| React.memo usage | 13 file (%3.4) |

---

## 19. Sonuç

Codebase **77K satır ve 706 dosya** ile büyük. Mimarinin sağlık skoru orta — bilinen anti-pattern'ler var ama doku iyileşiyor (CuratorPage örneği):

**Negatifler:**
- **3 god dosya** (>1000 LOC) ana feature path'lerde
- **3/5 Zustand store ölü** (state machinery yetersiz değerlendirilmiş)
- **~30 orphan component** (refactor-then-abandon)
- **3 UI library** birlikte (MUI + Tailwind + shadcn)
- **Memoization yetersiz** (%82 component kullanmıyor)
- **18 tek-kullanımlı hook** (premature abstraction sinyali)

**Pozitifler:**
- Code splitting iyi (58 lazy route)
- Test coverage var (86 test file)
- Yeni kod (Session 178+) daha temiz pattern'lerle yazılıyor
- Service layer mostly mevcut (15 dosya hâlâ direct fetch, ama 30 service dosyası kullanılıyor)
- 75 dosya <100 LOC — küçük focused component'ler hâlâ baskın

**Tek metrik özetlerse:** En kritik refactor noktası `pages/ModernLearningPathPage.tsx` (composite score 1514). Bu sayfa öğrenci ana akışında — 1165 LOC + 6 direct fetch + 82 nest aktif olarak büyüyor. Önceliklendirilmesi gerek.

---

*Audit READ-ONLY. Hiçbir dosya düzenlenmedi.*
*Metodoloji: bash + grep statik analiz. AST-tabanlı (eslint/madge) doğrulama tavsiye edilir.*
