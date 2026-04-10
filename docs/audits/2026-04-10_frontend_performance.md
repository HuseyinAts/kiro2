# Audit: Frontend Performance
Tarih: 2026-04-10 | Concern: Memory leak, re-render, bundle, lazy loading | Agent: 1

## P0 — Memory Leak (Production Crash Riski)

1. **src/api.ts:861,877** — WebSocket reconnect `setTimeout` + `heartbeatTimer setInterval` cleanup yok → sonsuz timer accumulation
2. **components/Accessibility/ADHD/VisualTimer.tsx:93** — `setInterval(fetchTimerData, 1000)` dep array'de `sessionId` yok, clearInterval garantisi yok
3. **components/Accessibility/Dyscalculia/GeometricShapes3D.tsx:113** — `window.addEventListener('mousemove')` conditional cleanup → listener sızıyor

## P1 — User-visible (Re-render / Bundle)

4. **components/Exam/ModernOSYMExamInterface.tsx:139** — Dual interval (1s countdown + 30s sync) → sync beforeunload'a taşı
5. **pages/ (15+ dosya)** — `import * as React` → tree-shaking engeli → direct import
6. **pages/LeaguePage.tsx:67** — `Math.max(...standings.map(s=>s.xp))` her render O(n) → useMemo
7. **pages/ExamPage.tsx:41** — `useEffect` dep array'de stale `initializePage` closure → useCallback
8. **pages/PhotoAskPage.tsx:89** — FileReader base64 10MB state'e alınıyor → URL.createObjectURL + cleanup

## P2 — Optimizasyon

9. **hooks/useAutoSave.ts:163** — `beforeunload`/`visibilitychange` listener `enabled` change'de cleanup yok
10. **pages/DailyQuestPage.tsx:75** — `useEffect([fetchQuests])` loop riski → useCallback ile stabilize
11. **pages/ (15+ dosya)** — Raw `apiRequest()` repeat calls, React Query cache yok
12. **context/AuthProvider.tsx:18** — `initializeAuth` useCallback wrapper eksik
13. **pages/YOLODetectionPage.tsx vb.** — `<img>` loading="lazy" eksik
14. **App.tsx:122** — SW reload loop: sessionStorage race condition → Promise koordinasyonu

## Notlar
- Lazy loading: 28 sayfa zaten `React.lazy()` ile sarılmış ✓
- Bundle: `import * as React` tree-shaking engeli (P1, 15+ dosya)
- İlk aksiyon: P0 memory leak'ler (api.ts WebSocket + VisualTimer interval)
