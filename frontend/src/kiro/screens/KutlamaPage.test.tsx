import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { KutlamaPage } from './KutlamaPage';

expect.extend(toHaveNoViolations);

describe('KutlamaPage', () => {
  beforeEach(() => window.history.replaceState({}, '', '/'));

  it('günlük (varsayılan): eyebrow + başlık + ödül + mantra + CTA href', async () => {
    render(<KutlamaPage />);
    expect(await screen.findByText('Bugünkü tuğlanı koydun.')).toBeInTheDocument();
    expect(screen.getByText('GÜNLÜK HEDEF')).toBeInTheDocument();
    expect(screen.getByText('+40')).toBeInTheDocument();
    expect(screen.getByText('XP · bugünkü kazanç')).toBeInTheDocument();
    expect(screen.getByText(/Büyük duvarlar tek tuğlayla yükselir\./)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Devam et/ })).toHaveAttribute('href', '/bugun');
  });

  it('tören: başlığa programatik odak (role=status)', async () => {
    render(<KutlamaPage />);
    const h = await screen.findByRole('heading', { name: 'Bugünkü tuğlanı koydun.', level: 1 });
    expect(h).toHaveFocus();
  });

  it('boss (mor tür): ejderha başlığı + ustalık rozeti + en zayıf konu + CTA', async () => {
    window.history.replaceState({}, '', '/kutlama?type=boss');
    render(<KutlamaPage />);
    expect(await screen.findByText('Ejderha yenildi!')).toBeInTheDocument();
    expect(screen.getByText('ustalık rozeti')).toBeInTheDocument();
    // bonus rozet değeri = en zayıf mat konu (Türev, %48)
    expect(screen.getByText('Türev')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Zaferi kutla/ })).toHaveAttribute('href', '/bugun');
  });

  it('konfeti: hareket açıkken (varsayılan) mount edilir', async () => {
    const { container } = render(<KutlamaPage />);
    await screen.findByText('Bugünkü tuğlanı koydun.');
    expect(container.innerHTML).toContain('kiroCfall');
  });

  it('reduced-motion: konfeti render EDİLMEZ, içerik yine gelir', async () => {
    const orig = window.matchMedia;
    window.matchMedia = vi.fn().mockImplementation((q: string) => ({
      matches: q.includes('reduce'),
      media: q,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })) as unknown as typeof window.matchMedia;
    try {
      const { container } = render(<KutlamaPage />);
      expect(await screen.findByText('Bugünkü tuğlanı koydun.')).toBeInTheDocument();
      expect(container.innerHTML).not.toContain('kiroCfall');
    } finally {
      window.matchMedia = orig;
    }
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<KutlamaPage />);
    await screen.findByText('Bugünkü tuğlanı koydun.');
    expect(await axe(container)).toHaveNoViolations();
  }, 20000);
});
