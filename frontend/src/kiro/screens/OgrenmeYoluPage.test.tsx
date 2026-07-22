import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, expect, it, vi } from 'vitest';

import { OgrenmeYoluPage } from './OgrenmeYoluPage';

expect.extend(toHaveNoViolations);

describe('OgrenmeYoluPage', () => {
  it('layout: SideNav + başlık + ünite bandı + ders değiştirici', async () => {
    render(<OgrenmeYoluPage />);
    expect(await screen.findByText('Temel Kavramlar')).toBeInTheDocument();
    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Öğrenme Yolu', level: 1 })).toBeInTheDocument();
    // ders pilleri (5 ders) — hepsi ≥44px dokunma hedefi
    expect(screen.getByRole('button', { name: 'Matematik', pressed: true })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Fizik' })).toBeInTheDocument();
  });

  it('sağ ray: Sıradaki adım = en zayıf konu + Konuya başla CTA + atom linki', async () => {
    render(<OgrenmeYoluPage />);
    expect(await screen.findByText('Sıradaki adım')).toBeInTheDocument();
    // mat en zayıf konu = Türev (%48)
    expect(screen.getByRole('heading', { name: 'Türev', level: 2 })).toBeInTheDocument();
    expect(screen.getByText(/Bu derste en düşük hâkimiyetli konun/)).toBeInTheDocument();
    const cta = screen.getByRole('link', { name: /Konuya başla/ });
    expect(cta).toHaveAttribute('href', '/soru-cozme');
    // Türev'in atom kırılımı var → ikincil "Atomlara in" linki
    expect(screen.getByRole('link', { name: /Atomlara in/ })).toBeInTheDocument();
  });

  it('patika: düğüm butonları + kilitli aria-disabled + checkpoint', async () => {
    render(<OgrenmeYoluPage />);
    await screen.findByText('Temel Kavramlar');
    // done düğüm (Sayı kümeleri) tıklanabilir buton
    expect(screen.getByRole('button', { name: 'Sayı kümeleri' })).toBeInTheDocument();
    // kilitli konu düğümü aria-disabled (5. ünite kilitli)
    const kilitli = screen.getByRole('button', { name: 'Oran-orantı' });
    expect(kilitli).toHaveAttribute('aria-disabled', 'true');
    // checkpoint: 3. ünite (current) → Boss
    expect(screen.getByRole('button', { name: '3. ünite · ÜNİTE TESTİ · BOSS' })).toBeInTheDocument();
  });

  it('ders değiştirici: Fizik seçilince patika yeniden çizilir', async () => {
    render(<OgrenmeYoluPage />);
    await screen.findByText('Temel Kavramlar');
    await userEvent.click(screen.getByRole('button', { name: 'Fizik' }));
    expect(await screen.findByText('Fizik Bilimine Giriş')).toBeInTheDocument();
    // Fizik en zayıf konu = Elektrik
    expect(screen.getByRole('heading', { name: 'Elektrik', level: 2 })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole('button', { name: 'Fizik', pressed: true })).toBeInTheDocument());
  });

  it('reduced-motion: hareket kapalıyken içerik yine render olur', async () => {
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
      render(<OgrenmeYoluPage />);
      expect(await screen.findByText('Temel Kavramlar')).toBeInTheDocument();
      expect(screen.getByText('BAŞLA')).toBeInTheDocument();
    } finally {
      window.matchMedia = orig;
    }
  });

  it('axe: sayfa temiz', async () => {
    const { container } = render(<OgrenmeYoluPage />);
    await screen.findByText('Temel Kavramlar');
    expect(await axe(container)).toHaveNoViolations();
  }, 40000); // ağır patika — jsdom+axe yavaş; paralel yük altında 20s yetmiyor
});
