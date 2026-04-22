# Component — React Component Scaffold (KIRO2 Pattern)

KIRO2'nin frontend pattern'larına uygun yeni React component iskeleti üretir.
Zustand (store/ tekil) + TanStack Query + Tailwind + MSW test.

## Ne Zaman Kullanılmalı

- Yeni UI feature'ı başlarken
- Mevcut component'i yeniden yapılandırırken (cleanup)
- Teamcülük için baseline sağlarken

## Ne Zaman KULLANMA

- Basit, stateless presentational component (inline yazmak daha hızlı)
- 3rd party library wrapper (kütüphanenin kendi pattern'ı var)
- Test-first zaten yazdın, component iskele gerekmiyor

## Kullanım

```
/component <ComponentName> [--with-api] [--with-state] [--modal]
```

Örnekler:
- `/component ExamCard` — basit presentational
- `/component ExamResults --with-api` — TanStack Query içeriyor
- `/component UserProfile --with-state` — Zustand store ekli
- `/component ConfirmDialog --modal` — modal varyantı

## Üretilecek Dosyalar

Component adı `ExamCard` için:

```
frontend/src/features/exam/
├── ExamCard.tsx            ← Ana component
├── ExamCard.test.tsx       ← Vitest + RTL + MSW
├── ExamCard.stories.tsx    ← Storybook (opsiyonel)
└── index.ts                ← Re-export
```

## Template — Basit Component

```tsx
// frontend/src/features/exam/ExamCard.tsx

import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/utils';

interface ExamCardProps {
  title: string;
  description?: string;
  onStart?: () => void;
  className?: string;
}

export default function ExamCard({
  title,
  description,
  onStart,
  className,
}: ExamCardProps) {
  const { t } = useTranslation();

  return (
    <div
      className={cn(
        'rounded-lg border bg-white p-6 shadow-sm',
        'dark:bg-zinc-900 dark:border-zinc-700',
        'hover:shadow-md transition-shadow',
        className
      )}
    >
      <h3 className="text-lg font-semibold">{title}</h3>
      {description && (
        <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
          {description}
        </p>
      )}
      {onStart && (
        <button
          type="button"
          onClick={onStart}
          className="mt-4 rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
          aria-label={t('exam.start')}
        >
          {t('exam.start')}
        </button>
      )}
    </div>
  );
}
```

## Template — With API (TanStack Query)

```tsx
// frontend/src/features/exam/ExamResults.tsx

import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { useTranslation } from 'react-i18next';

interface ExamResultsProps {
  examId: string;
}

export default function ExamResults({ examId }: ExamResultsProps) {
  const { t } = useTranslation();

  const { data, isLoading, error } = useQuery({
    queryKey: ['exam-results', examId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/exams/${examId}/results`);
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 dakika
  });

  if (isLoading) {
    return <div role="status">{t('common.loading')}</div>;
  }

  if (error) {
    return (
      <div role="alert" className="text-red-600">
        {t('common.error')}: {error.message}
      </div>
    );
  }

  return (
    <div>
      <h2>{t('exam.results')}</h2>
      <p>{t('exam.score', { score: data.score })}</p>
      {/* ... detay göster */}
    </div>
  );
}
```

## Template — With Zustand State

```tsx
// frontend/src/features/user/UserProfile.tsx

import { useAuthStore } from '@/store/authStore';  // store/ TEKİL
import { useTranslation } from 'react-i18next';

export default function UserProfile() {
  const { t } = useTranslation();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  if (!user) {
    return null;
  }

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold">{user.name}</h2>
      <p className="text-zinc-600">{user.email}</p>
      <button
        type="button"
        onClick={logout}
        className="mt-4 rounded border px-4 py-2 hover:bg-zinc-100"
      >
        {t('auth.logout')}
      </button>
    </div>
  );
}
```

## Template — Modal Variant

```tsx
// frontend/src/features/common/ConfirmDialog.tsx

import { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmDialog({
  open,
  title,
  description,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const { t } = useTranslation();
  const dialogRef = useRef<HTMLDivElement>(null);

  // Esc ile kapat
  useEffect(() => {
    if (!open) return;

    const handleKeydown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel();
    };
    window.addEventListener('keydown', handleKeydown);
    return () => window.removeEventListener('keydown', handleKeydown);
  }, [open, onCancel]);

  // Focus trap (başlangıç focus)
  useEffect(() => {
    if (open) dialogRef.current?.focus();
  }, [open]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="dialog-title"
    >
      <div
        ref={dialogRef}
        tabIndex={-1}
        className="rounded-lg bg-white p-6 shadow-xl dark:bg-zinc-900 max-w-md"
      >
        <h2 id="dialog-title" className="text-lg font-semibold">
          {title}
        </h2>
        {description && <p className="mt-2 text-sm">{description}</p>}
        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="rounded px-4 py-2 hover:bg-zinc-100"
          >
            {t('common.cancel')}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
          >
            {t('common.confirm')}
          </button>
        </div>
      </div>
    </div>
  );
}
```

## Test Template (MSW + Vitest + RTL)

```tsx
// frontend/src/features/exam/ExamCard.test.tsx

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import ExamCard from './ExamCard';

describe('ExamCard', () => {
  it('title ve description render eder', () => {
    render(<ExamCard title="TYT Matematik" description="40 soru" />);
    expect(screen.getByText('TYT Matematik')).toBeInTheDocument();
    expect(screen.getByText('40 soru')).toBeInTheDocument();
  });

  it('onStart tıklandığında çağırır', async () => {
    const onStart = vi.fn();
    render(<ExamCard title="TYT" onStart={onStart} />);

    await userEvent.click(screen.getByRole('button'));
    expect(onStart).toHaveBeenCalledTimes(1);
  });

  it('onStart verilmezse button render etmez', () => {
    render(<ExamCard title="TYT" />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
```

## KIRO2-Özel Checklist

Her yeni component üretimde:

- [ ] TypeScript strict (no `any`)
- [ ] Props interface + default export
- [ ] i18n: String literal yok, `t('key')` kullanılmış
- [ ] Accessibility: aria-*, semantic HTML (button, dialog, etc.)
- [ ] Dark mode: `dark:` variant'lar var
- [ ] Store'dan state: `@/store/` (tekil, çoğul değil)
- [ ] API çağrısı: TanStack Query + MSW handler
- [ ] Test dosyası otomatik oluşturulmuş
- [ ] Türkçe i18n key'leri `locales/tr/common.json`'a eklenmeli

## Design Mode ile Kombinasyon

Component oluşturulduktan sonra:
1. Integrated Browser'da localhost:3001'e git
2. `⌘+Shift+D` Design Mode
3. Component'i görsel olarak iterate et
4. `.cursor/skills/design-mode/SKILL.md` rehberi

## Referans

- `.cursor/rules/20-frontend.mdc` — frontend pattern kuralları
- `.cursor/skills/design-mode/SKILL.md` — UI iteration workflow
- https://ui.shadcn.com/docs — shadcn/ui referans
- https://tanstack.com/query/latest — TanStack Query docs
