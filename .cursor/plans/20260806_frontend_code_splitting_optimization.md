# Plan: Frontend Code-Splitting & Bundle Optimizations (Chunk Boyutu İyileştirmeleri)

## Kapsam ve Amaç
Vite build çıktısında ortaya çıkan 500 kB üstü chunk uyarılarını (`ModernLearningPathPage`, `mui-core`, `refractor`/`highlight` vb.) optimize etmek, HTTP loading şebeke yükünü hafifletmek ve PWA ilk açılış performansını (FCP / LCP) artırmak.

## Uygulama Adımları

1. **`vite.config.ts` Rollup `manualChunks` Güncellemesi:**
   - Vendor kütüphanelerini daha granüler ve dengeli chunk kümelere ayırma:
     - `vendor-mui-core`: `@mui/material`, `@mui/system`, `@emotion`
     - `vendor-mui-icons`: `@mui/icons-material`
     - `vendor-charts`: `recharts`, `d3-*`
     - `vendor-motion`: `framer-motion`
     - `vendor-katex`: `katex`, `react-katex`
     - `vendor-syntax`: `refractor`, `prismjs`, `highlight.js`
     - `vendor-utils`: `axios`, `react-query`, `dayjs`, `lodash`
     - `vendor-router`: `react-router`, `@remix-run`
   - React çekirdeğini (`react`, `react-dom`) entry chunk içinde tutma kuralını (Session 74 dersi: `createContext` sırası bozulmaması için) koruma.

2. **`App.tsx` Eager/Lazy Import Kontrolü:**
   - Eager import edilen fakat ilk ekran açılışında zorunlu olmayan bileşenleri / sayfaları kontrol etme ve dinamik `lazy()` import seviyesine çekme.

3. **Bileşen Seviyesi Dinamik Importlar (Heavy Components):**
   - Ağır matematik (KaTeX) veya syntax highlighter bileşenlerinin yalnızca ihtiyaç anında (özel soru/çözüm alanında) yüklenmesi.

4. **Doğrulama ve Testler:**
   - `npm run type-check` (0 Hata)
   - `cd frontend && npm test -- --run` (Vitest %100 Pass)
   - `npm run build` (Sıfır 500+ kB chunk uyarısı veya optimize edilmiş treemap dağılımı)
