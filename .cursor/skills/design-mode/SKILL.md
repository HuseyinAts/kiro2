---
name: design-mode
description: Cursor 3'ün Design Mode'u ve Integrated Browser'ı ile UI iteration. Browser'da element'e tıkla, agent'a hedefle — KIRO2 frontend geliştirmede hızlandırıcı.
---

# Design Mode — Browser'da UI'ı Agent'a Gösterme

Cursor 3.0'ın (2 Nisan 2026) getirdiği Design Mode: Agents Window'un
integrated browser'ında UI element'lerine tıklayarak agent'a doğrudan
hedef göstermek. "Bu butonu daha büyük yap" gibi kelimelerle uğraşmak
yerine **literal olarak point and tell**.

## Ne Zaman Yüklenmeli

- KIRO2 frontend iteration (Dashboard, Exam UI, Question Player)
- Styling/layout değişiklikleri
- Design mockup'tan implementation
- Responsive behavior testi
- Accessibility review

## Ne Zaman KULLANMA

- Backend work (Design Mode frontend'a özel)
- Pure state/logic değişikliği
- Performance profiling

## Aktivasyon

**Klavye kısayolları** (Agents Window'da browser açıkken):

| Kısayol | İşlev |
|---|---|
| `⌘ + Shift + D` | Design Mode toggle |
| `Shift + drag` | Alan seç (birden çok element) |
| `⌘ + L` | Seçili element'i chat'e ekle |
| `⌥ + click` | Element'i prompt input'una ekle |
| Ok tuşları | Element tree'de navigate (3.1 ile) |

## KIRO2 Workflow

### Adım 1 — Integrated Browser'ı Aç

Agents Window → sağ panel → Browser sekmesi
URL: `http://localhost:3001` (KIRO2 frontend dev server)

### Adım 2 — Element Seç

1. `⌘+Shift+D` ile Design Mode aktif
2. Dashboard'a git → Exam Card'ına tıkla
3. Kenarlık + label görünür (element seçili)

### Adım 3 — Agent'a Prompt Yaz

```
[⌘+L ile Exam Card seçili]

Bu card'ın:
- Shadow'ını Tailwind shadow-lg yap
- Hover'da scale 1.02
- Dark mode'da bg-zinc-900

Pattern: frontend/src/components/ui/card.tsx variant="elevated"
```

Agent, seçili element'in DOM path'ini ve React component ref'ini alır.
Doğrudan ilgili dosyaya (Dashboard.tsx veya ExamCard.tsx) gider.

### Adım 4 — Canlı Doğrulama

Agent kod değiştirince Vite hot-reload yapar → browser'da anında görürsün.
Beğenmedinse yine Design Mode ile yeni feedback ver.

## KIRO2 Kullanım Senaryoları

### Senaryo 1: Design Mockup'tan Implementation

```
[Figma/Screenshot'ı chat'e yapıştır]

Bu mockup'a göre frontend/src/features/exam/ExamStart.tsx'i güncelle.
Mevcut: basit form. Hedef: mockup'taki kartlar.

[Design Mode ile mevcut ExamStart'ı göster]
```

Agent hem mockup'u hem mevcut DOM'u görür, diff'i uygular.

### Senaryo 2: Responsive Debug

```
[Browser'ı 375px genişliğe daralt — Design Mode açık]

Navbar mobile'da overflow oluyor. İlgili element:
[⌘+L ile navbar seçili]

Mobile breakpoint'te hamburger menu'ye geç. Tailwind md: breakpoint.
```

### Senaryo 3: Accessibility İterasyonu

```
[Exam question player'a odaklan — Design Mode]

Screen reader için:
- Soru metni <h2> olmalı
- Seçenekler <fieldset role="radiogroup">
- Keyboard navigation: Tab ile seçenekler arası

Mevcut seçili element:
[⌘+L ile question container]
```

### Senaryo 4: Dark Mode Tutarlılık

```
[Dark mode toggle et — Agents Window'da]

Dashboard.tsx'teki istatistik kartlarında bg-gray-100 dark mode'da
kontrast sağlamıyor. Şu element:
[⌘+L ile stat card]

Pattern: shadcn/ui dark mode variant kullan.
```

## Element Tree Navigation (Cursor 3.1)

Cursor 3.1 ile (13 Nisan 2026) Design Mode'da klavye ile element tree'de
gezinebilirsin:

- `↑` parent element
- `↓` ilk child
- `←` / `→` sibling elementler

Kullanım: Yanlış element'i seçtinse fare yerine klavye ile ayarla.

## Integrated Browser'ın Diğer Yetenekleri

Sadece Design Mode değil, Browser agent için tool olarak da kullanılır:

```
"Frontend'i test et:
1. http://localhost:3001/login'e git
2. test@kiro2.local / Test1234! ile login ol
3. Dashboard'a yönlendirildiğini doğrula
4. 'TYT Matematik' sekmesinin görünür olduğunu kontrol et
5. Screenshot al"
```

Agent browser'ı otomatik kontrol eder, kendi screenshot'ını alır, DOM'u
analiz eder. Manuel test sürecini otomatikleştirir.

## KIRO2 frontend Stack Uyumu

KIRO2 frontend'te kullanılan:
- React 18 + TypeScript
- Tailwind CSS
- Zustand (authStore `store/` tekil)
- TanStack Query
- Vite dev server

Design Mode bu stack'le native çalışır — özel konfigürasyon gerekmiyor.
React Developer Tools Design Mode'la entegre: agent component tree'yi görür.

## Mobile Responsive Test

Integrated Browser'da viewport değiştir:
- Mobile (375px)
- Tablet (768px)
- Desktop (1280px)
- Wide (1920px)

Design Mode her boyutta çalışır. Agent media query'leri buna göre önerir.

## Anti-pattern'lar

- **Design Mode + uzun prompt** — spesifik element yerine belirsiz talep
  ("her şeyi güzelleştir")
- **Browser'ı dev server olmadan kullanmak** — localhost:3001 çalışır olmalı
- **Production URL üzerinde Design Mode** — localhost'ta yap, production'a push
- **Element seçmeden prompt yazmak** — agent nereye bakacağını bilmez

## Entegre Araçlarla Kombinasyon

- **Design Mode + Plan Mode**: "Şu mockup'u implement et, ama önce plan yaz"
- **Design Mode + Best-of-N**: "Bu card'ı 3 farklı stilde dene, en iyi öner"
- **Design Mode + Figma MCP**: Figma'dan doğrudan component import

## Referans

- Cursor 3.0 changelog: Design Mode tanıtımı
- Cursor 3.1 changelog: Element tree klavye navigation
- Resmi doc: https://cursor.com/docs/agent/tools/browser
