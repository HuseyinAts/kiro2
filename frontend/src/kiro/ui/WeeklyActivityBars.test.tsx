import { render, screen, within } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import type { HaftaGun } from '../types';
import { WeeklyActivityBars } from './WeeklyActivityBars';

expect.extend(toHaveNoViolations);

const HAFTA: HaftaGun[] = [
  { label: 'Pzt', dk: 45, aktif: true },
  { label: 'Sal', dk: 60, aktif: true },
  { label: 'Çar', dk: 30, aktif: true },
  { label: 'Per', dk: 0, aktif: false },
  { label: 'Cum', dk: 50, aktif: true },
  { label: 'Cmt', dk: 90, aktif: true },
  { label: 'Paz', dk: 40, aktif: true },
];

describe('WeeklyActivityBars', () => {
  it('grup adını ariaLabel ile yansıtır', () => {
    render(<WeeklyActivityBars gunler={HAFTA} ariaLabel="Haftalık aktivite" />);
    expect(screen.getByRole('group', { name: 'Haftalık aktivite' })).toBeInTheDocument();
  });

  it('her gün için görünmez SR metni ("{label}: {dk} dk") çizer', () => {
    render(<WeeklyActivityBars gunler={HAFTA} ariaLabel="Haftalık aktivite" />);
    expect(screen.getByText('Pzt: 45 dk')).toBeInTheDocument();
    // Çalışma olmayan gün (pasif) de sayı taşır — 0 dk, alarm dili yok
    expect(screen.getByText('Per: 0 dk')).toBeInTheDocument();
    expect(screen.getByText('Cmt: 90 dk')).toBeInTheDocument();
  });

  it('7 çubuğun tümünü render eder (SR metinleri sayılır)', () => {
    render(<WeeklyActivityBars gunler={HAFTA} ariaLabel="Haftalık aktivite" />);
    const dk = screen.getAllByText(/\d+ dk$/);
    expect(dk).toHaveLength(7);
  });

  it('toplamSa + trend verilince başlık satırını çizer', () => {
    render(<WeeklyActivityBars gunler={HAFTA} ariaLabel="Haftalık aktivite" toplamSa={6.5} trend="+1,1 sa" />);
    expect(screen.getByText('6,5')).toBeInTheDocument();
    expect(screen.getByText('+1,1 sa')).toBeInTheDocument();
  });

  it('toplamSa yoksa başlık satırı çizilmez (yalnız çubuklar)', () => {
    render(<WeeklyActivityBars gunler={HAFTA} ariaLabel="Haftalık aktivite" />);
    expect(screen.queryByText(/ sa$/)).not.toBeInTheDocument();
    // Görünen gün etiketleri aria-hidden ama grubun içinde mevcut
    const grp = screen.getByRole('group', { name: 'Haftalık aktivite' });
    expect(within(grp).getByText('Pzt')).toBeInTheDocument();
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(
      <WeeklyActivityBars gunler={HAFTA} ariaLabel="Haftalık aktivite" toplamSa={6.5} trend="+1,1 sa" />,
    );
    expect(await axe(container)).toHaveNoViolations();
  }, 40000);
});
