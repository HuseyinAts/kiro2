import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { SonucPage } from './SonucPage';

expect.extend(toHaveNoViolations);

describe('SonucPage', () => {
  it('net-birincil: hero + halka + "yalnız yön göstergesi" + döküm + AI + zayıf', async () => {
    render(<SonucPage />);
    expect(await screen.findByText(/Güzel iş,/)).toBeInTheDocument();
    expect(screen.getByText('Toplam net')).toBeInTheDocument();
    expect(screen.getByText(/yalnız yön göstergesi/)).toBeInTheDocument();
    expect(screen.getByText('Ders Bazında Net Dökümü')).toBeInTheDocument();
    expect(screen.getByText('AI Analizi')).toBeInTheDocument();
    expect(screen.getByText('Geliştirilecek konular')).toBeInTheDocument();
    expect(screen.getByText(/yanlışı tekrar et/)).toBeInTheDocument();
    expect(screen.getByRole('img', { name: /Doğru oranı yüzde/ })).toBeInTheDocument();
  });

  it('stat satırı: Doğru/Yanlış/Boş', async () => {
    render(<SonucPage />);
    await screen.findByText(/Güzel iş,/);
    expect(screen.getByText('Doğru')).toBeInTheDocument();
    expect(screen.getByText('Yanlış')).toBeInTheDocument();
    expect(screen.getByText('Boş')).toBeInTheDocument();
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<SonucPage />);
    await screen.findByText(/Güzel iş,/);
    expect(await axe(container)).toHaveNoViolations();
  }, 20000);
});
