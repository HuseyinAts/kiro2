import { fireEvent, render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, expect, it, vi } from 'vitest';

import { BossSavasiPage } from './BossSavasiPage';

expect.extend(toHaveNoViolations);

describe('BossSavasiPage', () => {
  it('arena: boss adı (en zayıf mat konu) + zayıf nokta + boss can barı', async () => {
    render(<BossSavasiPage />);
    // en zayıf mat konu = Türev (%48)
    expect(await screen.findByText('Türev Ejderhası')).toBeInTheDocument();
    expect(screen.getByText('Konu Canavarı · Türev')).toBeInTheDocument();
    const can = screen.getByRole('progressbar', { name: 'Boss canı' });
    expect(can).toHaveAttribute('aria-valuemax', '2000');
    expect(can).toHaveAttribute('aria-valuenow', '2000');
  });

  it('saldırı döngüsü: seçenek seç → Saldır → reveal (Sonraki saldırı)', async () => {
    render(<BossSavasiPage />);
    await screen.findByText('Türev Ejderhası');

    // Saldır seçimsizken devre dışı
    const saldirBtn = screen.getByRole('button', { name: 'Saldır!' });
    expect(saldirBtn).toBeDisabled();

    // İlk seçenek (aria-pressed taşıyan buton = seçenek)
    const secenek = screen.getAllByRole('button').find((b) => b.getAttribute('aria-pressed') !== null);
    expect(secenek).toBeTruthy();
    fireEvent.click(secenek!);
    expect(saldirBtn).toBeEnabled();

    fireEvent.click(saldirBtn);
    // Sunucu-otoriter yanıt sonrası reveal fazına geçer
    expect(await screen.findByRole('button', { name: 'Sonraki saldırı' })).toBeInTheDocument();
  });

  it('ödül şeridi: XP + rozet + konu fethi sunucu verisinden', async () => {
    render(<BossSavasiPage />);
    await screen.findByText('Türev Ejderhası');
    expect(screen.getByText('+800 XP')).toBeInTheDocument();
    expect(screen.getByText('Efsanevi rozet')).toBeInTheDocument();
  });

  it('reduced-motion: keyframe enjekte EDİLMEZ, içerik yine gelir', async () => {
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
      const { container } = render(<BossSavasiPage />);
      expect(await screen.findByText('Türev Ejderhası')).toBeInTheDocument();
      expect(container.innerHTML).not.toContain('kfBoss');
    } finally {
      window.matchMedia = orig;
    }
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<BossSavasiPage />);
    await screen.findByText('Türev Ejderhası');
    expect(await axe(container)).toHaveNoViolations();
  }, 40000);
});
