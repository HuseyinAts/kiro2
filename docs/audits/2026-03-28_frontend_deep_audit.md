# Frontend Deep Audit Report

**Tarih:** 2026-03-28
**Concern'ler:** Security+Auth, Components+UI, Hooks+State+Utils, Performance+Build
**Agent sayisi:** 4 (paralel)
**Toplam bulgu:** 6 P0, 20 P1, 40 P2 = **66 bulgu**

---

## P0 — Hemen Fix (6 bulgu)

### Hooks & State (2)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| H1 | hooks/useExamTimer.ts:120 | Stale closure — `remainingTime` interval callback'te stale, otomatik bitirme kacirilabilir | `useExamStore.getState().remainingTime` kullan |
| H2 | hooks/useExamResults.ts:75-79 | Race condition — AbortController yok, stale response yeni sonucu ezer | AbortController + cleanup |

### Components (4)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| C1 | Gamification/LevelDisplay.tsx:38 | Memory leak — setTimeout cleanup yok | `return () => clearTimeout(timer)` |
| C2 | ADHD/StreakTracker.tsx:52 | Memory leak — setTimeout cleanup yok | Ayni fix |
| C3 | Dyscalculia/NumberBlocks.tsx:60,102 | Memory leak — 2x setTimeout cleanup yok | useRef + cleanup |
| C4 | AccessibilityValidator.tsx:34 | Memory leak — setTimeout cleanup yok | Ref + cleanup |

---

## P1 — Sprint Icinde Fix (20 bulgu)

### Security & Auth (7)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| S1 | services/revolutionaryFeaturesService.ts:383+ | 8 fetch cagrisinda `credentials:'include'` EKSIK | Ekle |
| S2 | services/chatService.ts:299,365,392 | 3 enhanced chat fetch'te credentials eksik | Ekle |
| S3 | services/fsrsService.ts:117,157,375,412 | 4 fetch'te credentials eksik | Ekle |
| S4 | services/multiAgentService.ts:80,174,208,382 | 4 fetch'te credentials eksik | Ekle |
| S5 | services/fsrsService.ts:199,234,269 | IDOR — student_id query param olarak gonderiliyor | Backend'den derive et |
| S6 | services/revolutionaryFeaturesService.ts:35+ | IDOR — studentId URL path'te | Backend ownership verify |
| S7 | Dashboard/NotificationPanel.tsx:306 | Open redirect — `notification.eylem_url` dogrulanmadan yonlendirme | Domain allowlist |

### Components (4)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| C5 | Exam/Results/ + Results/Tabs/ | Duplicate component'ler — BasicResultsTab, IRT, ZPD 2 yerde | Wrapper'lari sil, tek kaynaktan import |
| C6 | Exam/*.tsx | 3 nesil ayni arayuz — OSYMExamInterface (1011L), Refactored (266L), Modern (744L) | Eski 2'sini `_deprecated/`'e tasi |
| C7 | App.tsx (yalnizca) | Sayfa seviyesi ErrorBoundary YOK — tek crash tum app'i cokertiyor | Exam/LP/Chat/Dashboard'a wrapper |
| C8 | 24 dead component dizin/dosya | Import edilmeyen ~100+ .tsx dosya — bundle bloat | `_deprecated/`'e tasi |

### Hooks & State (4)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| H3 | useExamWebSocket.ts:85-150 | Render-loop — inline callback dep'leri `connect` useEffect'i surekli tetikliyor | useRef pattern |
| H4 | useGamification.ts:132+ | 5 sub-hook mount'ta 8 parallel API call, AbortController yok | AbortController + cleanup |
| H5 | useLearningPath.ts:447-453 | Suppressed exhaustive-deps — `loadPath` dep array'de degil | useRef stable ref |
| H6 | useWebSocket.ts:200-207 | Infinite reconnect loop riski — connect dep olarak useEffect'te | Ref pattern |

### Performance (5)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| P1 | App.tsx:20 | ParentDashboard eager import — lazy olmali | `React.lazy()` |
| P2 | App.tsx:7 + PageTransition.tsx:6 | framer-motion (~32KB gz) critical path'te — tum route'lari wrap ediyor | CSS transition veya lazy |
| P3 | ModernLoginPage.tsx:23 | framer-motion login page'de de eager — initial bundle'da | CSS animation ile degistir |
| P4 | 193 dosya | MUI icons barrel import — dev cold start yavasliyor | Path import: `@mui/icons-material/School` |
| P5 | package.json | `lodash` (full, 500KB) — sadece 1 dosya `debounce` kullaniyor | `lodash/debounce` single import |

---

## P2 — Teknik Borc (40 bulgu)

### Security (7)

| # | Dosya | Aciklama |
|---|-------|----------|
| S8 | MermaidThoughtTree.tsx:150 | `.innerHTML = svg` sanitize edilmeden |
| S9 | utils/lazyLoad.tsx:151 | `new Function()` — CSP unsafe-eval |
| S10 | services/offlineStorageService.ts:112 | credentials eksik (offline download) |
| S11 | services/NetworkDetector.ts:209 | credentials eksik (health check) |
| S12 | test/e2e/mvp-smoke.spec.ts:25 | Hardcoded test password committed |
| S13 | ADHD/__tests__/TaskProgress...test.tsx:63 | localStorage token pattern test'te |
| S14 | .migration-backup/ | Eski localStorage token dosyalari git'te |

### Components (6)

| # | Dosya | Aciklama |
|---|-------|----------|
| C9 | 20+ dosya (120 occurrence) | `any` type kullanimi |
| C10 | 80+ dosya (100+ occurrence) | `key={index}` anti-pattern (dinamik listelerde) |
| C11 | 25+ dosya (53 occurrence) | Inline `style={{}}` — Tailwind tercih edilmeli |
| C12 | 6 dosya | `dangerouslySetInnerHTML` (sanitize ediliyor, test gerekli) |
| C13 | TextToSpeech.tsx:249,258,267 | setTimeout cleanup yok (user-triggered, dusuk risk) |
| C14 | EbaTV/*.tsx | Hardcoded placeholder URL'ler (`via.placeholder.com`) |

### Hooks & State (14)

| # | Dosya | Aciklama |
|---|-------|----------|
| H7 | useApiIntegration.ts | Dead hook — 0 import, heavy `any` |
| H8 | useTurkishLanguageCorrection.ts | Dead hook — 0 import |
| H9 | useLocalStorage.ts | Dead hook — 0 import |
| H10 | useAPI.ts | Dead hook — 0 import |
| H11 | useVideoPlayer.ts | Dead hook — 0 import |
| H12 | useExamKeyboard.ts | Dead hook — 0 import |
| H13 | utils/subtitleParser.ts | Dead util — 0 import |
| H14 | utils/storeHelpers.ts | Dead util — sadece self-reference |
| H15 | useExamWebSocket.ts:24,33 | `any` type — data ve performance |
| H16 | useStreaming.ts:30,40,251,261 | `any` — metadata 4 yerde |
| H17 | useLearningPathVideos.ts:105 | `path: any` — tip guvenligi yok |
| H18 | utils/apiHelpers.ts:211,284 | Cache `data: any` — generic olmali |
| H19 | useExamResults.ts:37 | `loadResults` useCallback degil — her render'da yeniden olusur |
| H20 | useStudentProfile.ts:48-51 | AbortController yok — 2 paralel fetch |

### Performance (13)

| # | Dosya | Aciklama |
|---|-------|----------|
| P6 | package.json | three.js + @react-three (~500KB) — import yok, muhtemelen unused |
| P7 | package.json | d3 (~200KB) — direkt import yok |
| P8 | package.json | mermaid (~800KB) — import yok |
| P9 | 20 dosya | recharts shared chunk (auto-split OK, aksiyon gereksiz) |
| P10 | 64 dosya | framer-motion 64 dosyada — critical path disina cikarilsa lazy yuklenir |
| P11 | 55 dosya (180 occurrence) | console.log kalintilari (terser strip ediyor, console.warn haric) |
| P12 | package.json | react-window yuklu ama kullanilmiyor |
| P13 | vite.config.ts:133 | safari10 mangle disabled — minor optimization |
| P14 | vite.config.ts:156 | Dead code: bos external array |
| P15 | main.tsx:21-38 | Global fetch override her request'te URL parse |
| P16 | main.tsx:13 | Dexie boot'ta sync yukler — requestIdleCallback'e ertele |
| P17 | App.tsx:145 | `console.warn('SW registered')` production'da gorunur |
| P18 | vite.config.ts | `drop_console` console.warn kapsamiyor |

---

## Konsensus (2+ agent hemfikir)

| Konu | Agent'lar | Guvenilirlik |
|------|-----------|-------------|
| **credentials:'include' eksik (19 fetch)** | Security + Hooks | YUKSEK — 4 service dosyasinda |
| **Dead code/components yaygin** | Components + Hooks + Perf | YUKSEK — 24 component + 6 hook + 2 util |
| **AbortController yok** | Security + Hooks | YUKSEK — exam, gamification, profile |
| **any type cok yaygin** | Components + Hooks | YUKSEK — 120+ occurrence |
| **framer-motion bundle etkisi** | Perf + Components | ORTA — 32KB gz initial, 64 dosyada |
| **setTimeout memory leak** | Components (4 yer) | ORTA — dusuk risk ama kolay fix |

---

## Oncelikli Aksiyon Plani

### Faz 1 — Acil (Bu hafta)
1. **credentials:'include' batch fix** (S1-S4): 4 service dosyasinda 19 fetch cagrisina ekle
2. **useExamTimer stale closure** (H1): Sinav zamanlayici yanlislikla erken/gec bitebilir
3. **useExamResults race condition** (H2): AbortController ekle

### Faz 2 — Sprint (Bu ay)
4. **Dead code temizligi**: 24 component + 6 hook + 2 util → `_deprecated/` (~100+ dosya)
5. **Page-level ErrorBoundary** (C7): Exam, LP, Chat, Dashboard wrap
6. **framer-motion lazy** (P2-P3): PageTransition CSS'e gecir — 32KB initial bundle tasarrufu
7. **Unused deps kaldir** (P6-P8): three.js, d3, mermaid — 1.5GB+ install tasarrufu
8. **IDOR fix** (S5-S6): student_id backend'den derive

### Faz 3 — Teknik Borc (Sonraki sprint)
9. **lodash → lodash/debounce** (P5): 70KB tasarrufu
10. **MUI icons path import** (P4): Dev DX iyilestirme
11. **any type audit** (C9, H15-H18): 120+ yer — interface tanimlari
12. **key={index} fix** (C10): Dinamik listelerde stable ID

---

## Metrikler

| Kategori | P0 | P1 | P2 | Toplam |
|----------|----|----|----|----|
| Security & Auth | 0 | 7 | 7 | 14 |
| Components & UI | 4 | 4 | 6 | 14 |
| Hooks & State & Utils | 2 | 4 | 14 | 20 |
| Performance & Build | 0 | 5 | 13 | 18 |
| **TOPLAM** | **6** | **20** | **40** | **66** |

---

## Pozitif Bulgular

- localStorage auth production code'da TEMIZ — migration tamamlanmis
- dangerouslySetInnerHTML tum 6 kullanim DOMPurify ile sanitize ediliyor
- Route protection: Login/register/404 haric tum route'lar ProtectedRoute icinde
- authStore token saklamiyor — sadece display bilgisi persist
- 50+ sayfa React.lazy() ile lazy-loaded (5 critical-path haric)
- dayjs kullaniliyor (moment.js DEGIL)
- Dashboard'da Promise.all ile paralel fetch — waterfall yok
- Vite config iyi tuned: terser console strip, CSS code split, auto chunk

---

*Audit by: 4 parallel agents (Claude Opus 4.6)*
*Rapor: docs/audits/2026-03-28_frontend_deep_audit.md*
