import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { MolaPage } from './MolaPage';

expect.extend(toHaveNoViolations);

describe('MolaPage', () => {
  it('kicker + serif başlık render eder', async () => {
    render(<MolaPage />);
    expect(screen.getByText('NEFESLEN')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Mola da hazırlığın/ })).toBeInTheDocument();
  });

  it('orb altı kutu-nefesi etiketi + faz yönergelerini gösterir', () => {
    render(<MolaPage />);
    expect(screen.getByText('4 · 4 · 4 · 4 KUTU NEFESİ · ORBLA BİRLİKTE')).toBeInTheDocument();
    // Animasyonlu mod: crossfade faz metinleri (iki "Tut" → getAllByText)
    expect(screen.getByText('Nefes al')).toBeInTheDocument();
    expect(screen.getByText('Yavaşça bırak')).toBeInTheDocument();
    expect(screen.getAllByText('Tut').length).toBe(2);
  });

  it('4 dinlenme önerisi kartını gösterir', () => {
    render(<MolaPage />);
    expect(screen.getByText('2 dk nefes')).toBeInTheDocument();
    expect(screen.getByText('Göz dinlendir')).toBeInTheDocument();
    expect(screen.getByText('Su iç')).toBeInTheDocument();
    expect(screen.getByText('Kısa yürüyüş')).toBeInTheDocument();
  });

  it('CTA /bugun rotasına gider + studyLabel verisi gelince görünür', async () => {
    render(<MolaPage />);
    const cta = screen.getByRole('link', { name: /Hazır hissediyorum/ });
    expect(cta).toHaveAttribute('href', '/bugun');
    // persona.bugunCozulenDk = 30 → "30 dk"
    expect(await screen.findByText(/30 dk/)).toBeInTheDocument();
    expect(screen.getByText(/bu molayı hak ettin/)).toBeInTheDocument();
  });

  it('reduced-motion: nefes yönergeleri statik liste olarak kalır', async () => {
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
      render(<MolaPage />);
      expect(screen.getByText('4 sn nefes al')).toBeInTheDocument();
      expect(screen.getByText('4 sn bırak')).toBeInTheDocument();
      // crossfade spanları render edilmez
      expect(screen.queryByText('Yavaşça bırak')).not.toBeInTheDocument();
    } finally {
      window.matchMedia = gercek;
    }
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<MolaPage />);
    await screen.findByText(/30 dk/);
    expect(await axe(container)).toHaveNoViolations();
  }, 20000);
});
