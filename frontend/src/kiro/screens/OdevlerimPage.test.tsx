import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { OdevlerimPage } from './OdevlerimPage';

expect.extend(toHaveNoViolations);

describe('OdevlerimPage', () => {
  it('SideNav + başlık render eder', () => {
    render(<OdevlerimPage />);
    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(screen.getAllByText('Ödevlerim').length).toBeGreaterThan(0);
  });

  it('mock ödevler listesini render eder (3 kart)', async () => {
    render(<OdevlerimPage />);
    expect(await screen.findByText('Türev soru paketi')).toBeInTheDocument();
    expect(screen.getByText('İntegral mini set')).toBeInTheDocument();
    expect(screen.getByText('Limit tekrar seti')).toBeInTheDocument();
  });

  it('durum çipleri + progressbar erişilebilir ad taşır', async () => {
    render(<OdevlerimPage />);
    await screen.findByText('Türev soru paketi');
    expect(screen.getByText('Açık · 2 gün')).toBeInTheDocument();
    expect(screen.getByText('Bekliyor')).toBeInTheDocument();
    expect(screen.getByRole('progressbar', { name: /Türev soru paketi — ilerleme yüzde 40/ })).toBeInTheDocument();
  });

  it('bekliyor kartı amber güvence notunu gösterir', async () => {
    render(<OdevlerimPage />);
    await screen.findByText('İntegral mini set');
    expect(screen.getByText(/Teslim geçti ama kapanmadı/)).toBeInTheDocument();
  });

  it('KANON: liste dipnotu absence-dili taşımaz', async () => {
    render(<OdevlerimPage />);
    await screen.findByText('Türev soru paketi');
    expect(screen.getByText(/Geciken ödev kapanmaz/)).toBeInTheDocument();
    expect(screen.queryByText(/\beksik\b/i)).not.toBeInTheDocument();
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<OdevlerimPage />);
    await screen.findByText('Türev soru paketi');
    expect(await axe(container)).toHaveNoViolations();
  }, 20000);
});
