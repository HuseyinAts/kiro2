import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { HaftalikPlanPage } from './HaftalikPlanPage';

expect.extend(toHaveNoViolations);

describe('HaftalikPlanPage', () => {
  it('SideNav + başlık render eder', () => {
    render(<HaftalikPlanPage />);
    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(screen.getAllByText('Haftalık Plan').length).toBeGreaterThan(0);
  });

  it('giriş metnini gösterir', async () => {
    render(<HaftalikPlanPage />);
    expect(await screen.findByText(/Motor bu haftayı senin için kurdu/)).toBeInTheDocument();
  });

  it('mock hafta bloklarını render eder', async () => {
    render(<HaftalikPlanPage />);
    expect(await screen.findByText('Türev')).toBeInTheDocument();
    // "Harmanlanmış Deneme" başlığı SideNav etiketiyle çakışır → deneme bloğunu benzersiz meta ile doğrula
    expect(screen.getByText('TYT + AYT · ~135 dk')).toBeInTheDocument();
    expect(screen.getByText('Nefes molası')).toBeInTheDocument();
  });

  it('gün sütunu erişilebilir ad taşır (bugün)', async () => {
    render(<HaftalikPlanPage />);
    await screen.findByText('Türev');
    expect(screen.getByText('BUGÜN')).toBeInTheDocument();
    expect(screen.getByRole('region', { name: /Pazartesi · .* blok · .* dk/ })).toBeInTheDocument();
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<HaftalikPlanPage />);
    await screen.findByText('Türev');
    expect(await axe(container)).toHaveNoViolations();
  }, 20000);
});
