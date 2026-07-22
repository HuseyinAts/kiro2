import { fireEvent, render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, expect, it, vi } from 'vitest';

import { DuelloPage } from './DuelloPage';

expect.extend(toHaveNoViolations);

describe('DuelloPage', () => {
  it('varsayılan render: VS bandı (Sen/Rakip) + mod chip + Tur 1 (sunucu-otoriter)', async () => {
    render(<DuelloPage />);
    // Yükleme sonrası slim bar başlığı
    expect(await screen.findByText('1v1 Düello')).toBeInTheDocument();
    // Mod chip matchmake('mat') → "Matematik · Hızlı"
    expect(screen.getByText('Matematik · Hızlı')).toBeInTheDocument();
    // SEN persona (getMe) + RAKİP (matchmake.rakip)
    expect(screen.getByText('Hüseyin')).toBeInTheDocument();
    expect(screen.getByText('Mert K.')).toBeInTheDocument();
    // İlk tur
    expect(screen.getByText('SORU 1')).toBeInTheDocument();
    // Süre halkası — role=timer, kalan saniye erişilebilir etikette
    expect(screen.getByRole('timer')).toHaveAttribute('aria-label', expect.stringMatching(/^kalan \d+ saniye$/));
  });

  it('seçenekler gerçek <button> (play fazında etkin) + senkron kopya', async () => {
    render(<DuelloPage />);
    await screen.findByText('1v1 Düello');
    // Play fazında tek buton grubu = A-E şık butonları (Kapat bir <a> link'tir)
    const secenekler = screen.getAllByRole('button');
    expect(secenekler.length).toBeGreaterThanOrEqual(4);
    expect(secenekler.every((b) => !b.hasAttribute('disabled'))).toBe(true);
    expect(secenekler[0]).toBeEnabled();
    // DC senkron kopyası (async model seçilmedi)
    expect(screen.getByText(/kendi hızında çözer/)).toBeInTheDocument();
    expect(screen.getByText(/Hızlı \+ doğru cevap = daha çok puan/)).toBeInTheDocument();
  });

  it('kapat (X) bağlantısı → /lig', async () => {
    render(<DuelloPage />);
    await screen.findByText('1v1 Düello');
    const kapat = screen.getByRole('link', { name: 'Kapat' });
    expect(kapat).toHaveAttribute('href', '/lig');
  });

  it('reduced-motion: kfRing keyframe enjekte EDİLMEZ, içerik yine gelir', async () => {
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
      const { container } = render(<DuelloPage />);
      expect(await screen.findByText('1v1 Düello')).toBeInTheDocument();
      expect(container.innerHTML).not.toContain('kfRing');
    } finally {
      window.matchMedia = orig;
    }
  });

  it('reveal: doğru + hızlı cevap → tur bandı "Turu kazandın!" (turSonucu SUNUCUDAN)', async () => {
    // MAJOR-1 regresyon: band eskiden ASLA "me" gösteremiyordu (turSonucu stream timer'ında
    // undefined userRound ile hesaplanıyordu). Artık postDuelAnswer server-sim'de hesaplar.
    render(<DuelloPage />);
    await screen.findByText('1v1 Düello');
    // mat-turev-1 doğru şıkkı B (index 1); hızlı tıklama (benSure ≪ rakipSure 4200) → 'me'.
    const secB = screen.getByText('B').closest('button');
    expect(secB).not.toBeNull();
    fireEvent.click(secB!);
    // Band rakip açıldıktan (stream onAnswer ~900 ms) sonra gelir; sonuç postDuelAnswer'dan.
    expect(await screen.findByText('Turu kazandın!', undefined, { timeout: 4000 })).toBeInTheDocument();
    expect(screen.getByText('Doğru ve hızlıydın — puanlar senin.')).toBeInTheDocument();
  }, 10000);

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<DuelloPage />);
    await screen.findByText('1v1 Düello');
    expect(await axe(container)).toHaveNoViolations();
  }, 40000);
});
