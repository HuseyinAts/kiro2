import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { BugunPage, gunlukMantra } from './BugunPage';

expect.extend(toHaveNoViolations);

describe('BugunPage', () => {
  it('gökyüzü hero başlığı yüklenir (tuğla sayacı)', async () => {
    render(<BugunPage />);
    const h1 = await screen.findByRole('heading', { level: 1 });
    expect(h1.textContent ?? '').toMatch(/tuğla|yerinde/);
  });

  it('görev kartı bugünkü ilk bloğu gösterir (Türev)', async () => {
    render(<BugunPage />);
    expect(await screen.findByRole('heading', { level: 2, name: 'Türev' })).toBeInTheDocument();
    expect(screen.getByText('BUGÜNKİ İLK TUĞLA')).toBeInTheDocument();
  });

  it('ders kartları koyu paletle render eder', async () => {
    render(<BugunPage />);
    expect(await screen.findByText('Türkçe')).toBeInTheDocument();
    expect(screen.getByText('Derslerin')).toBeInTheDocument();
  });

  it('mood radiogroup 5 seçenek + seçimde aria-live mesajı', async () => {
    render(<BugunPage />);
    const grp = await screen.findByRole('radiogroup', { name: 'Bugün nasılsın?' });
    const radios = within(grp).getAllByRole('radio');
    expect(radios).toHaveLength(5);
    await userEvent.click(radios[0]!);
    expect(radios[0]!).toHaveAttribute('aria-checked', 'true');
    expect(await screen.findByText(/Tükendiysen bugün 10 dakika yeter/)).toBeInTheDocument();
  });

  it('günün mantrasını gösterir', async () => {
    render(<BugunPage />);
    expect(await screen.findByText(new RegExp(gunlukMantra().slice(0, 12).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')))).toBeInTheDocument();
  });

  it('prefers-reduced-motion açıkken de içerik render eder', async () => {
    const orijinal = window.matchMedia;
    window.matchMedia = ((query: string) => ({
      matches: query.includes('reduce'),
      media: query,
      onchange: null,
      addListener: () => undefined,
      removeListener: () => undefined,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      dispatchEvent: () => false,
    })) as unknown as typeof window.matchMedia;
    try {
      render(<BugunPage />);
      const h1 = await screen.findByRole('heading', { level: 1 });
      expect(h1).toBeInTheDocument();
    } finally {
      window.matchMedia = orijinal;
    }
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<BugunPage />);
    await screen.findByRole('heading', { level: 2, name: 'Türev' });
    expect(await axe(container)).toHaveNoViolations();
  }, 20000);
});
