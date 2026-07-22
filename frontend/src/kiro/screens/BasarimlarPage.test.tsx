import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { BasarimlarPage } from './BasarimlarPage';

expect.extend(toHaveNoViolations);

describe('BasarimlarPage', () => {
  it('başlık + kazanılan rozet özetini gösterir', async () => {
    render(<BasarimlarPage />);
    expect(screen.getByRole('heading', { name: 'Başarımlar' })).toBeInTheDocument();
    // kazanilan = usta+fethedildi (3) + açılan taş (7·14·21 = 3) = 6
    expect(await screen.findByText(/8 rozet kazanıldı · yolun kanıtı/)).toBeInTheDocument();
  });

  it('hero bandı seviye + XP verisini gösterir', async () => {
    render(<BasarimlarPage />);
    expect(await screen.findByText('Seviye 7')).toBeInTheDocument();
    expect(screen.getByText(/XP toplandı/)).toBeInTheDocument();
    expect(screen.getByText(/2\.?450/)).toBeInTheDocument();
  });

  it('ders başına hâkimiyet halkası (role=img) + kademe etiketi', async () => {
    render(<BasarimlarPage />);
    const halkalar = await screen.findAllByRole('img');
    expect(halkalar.length).toBe(5);
    // En yüksek hâkimiyet önce: Türkçe %83 → Usta
    expect(halkalar[0]).toHaveAttribute('aria-label', 'Türkçe yüzde 83, Usta');
    expect(screen.getByRole('heading', { name: 'Hâkimiyet Rozetleri' })).toBeInTheDocument();
  });

  it('seri kilometre taşları — açılan + kilitli durumları', async () => {
    render(<BasarimlarPage />);
    // seriRekor = 21 → 7·14·21 açıldı, 30·50·100 kilitli
    expect(await screen.findByText('100')).toBeInTheDocument();
    expect(screen.getAllByText('açıldı').length).toBe(3);
    expect(screen.getAllByText('kilitli').length).toBe(3);
  });

  it('kademe lejantı 4 kademe + aralık gösterir', async () => {
    render(<BasarimlarPage />);
    expect(await screen.findByText('0–40')).toBeInTheDocument();
    expect(screen.getByText('40–65')).toBeInTheDocument();
    expect(screen.getByText('65–85')).toBeInTheDocument();
    expect(screen.getByText('85–100')).toBeInTheDocument();
  });

  it('reduced-motion: içerik hareketsiz de eksiksiz render eder', async () => {
    const gercek = window.matchMedia;
    window.matchMedia = ((q: string) => ({
      matches: q.includes('reduce'),
      media: q,
      onchange: null,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      addListener: () => undefined,
      removeListener: () => undefined,
      dispatchEvent: () => false,
    })) as unknown as typeof window.matchMedia;
    try {
      render(<BasarimlarPage />);
      expect(await screen.findByText('Seviye 7')).toBeInTheDocument();
      expect(screen.getAllByRole('img').length).toBe(5);
    } finally {
      window.matchMedia = gercek;
    }
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<BasarimlarPage />);
    await screen.findByText('Seviye 7');
    expect(await axe(container)).toHaveNoViolations();
  }, 40000);
});
