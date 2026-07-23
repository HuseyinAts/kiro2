import { render, screen, fireEvent } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';

import { useAyar, resetAyar } from '../lib/ayarStore';
import { LigPage } from './LigPage';

expect.extend(toHaveNoViolations);

// ayarStore global — persist sızıntısını önlemek için her testte reset.
beforeEach(() => resetAyar());
afterEach(() => resetAyar());

describe('LigPage', () => {
  it('varsayılan: "Sen vs dün" seridi (kişisel ilerleme) sıralamadan önce + server tier', async () => {
    render(<LigPage />);
    // Kaygı-duyarlı birincil blok (serif mantra)
    expect(await screen.findByText('Yarıştığın tek kişi dünkü sensin.')).toBeInTheDocument();
    // Lig bandı başlığı = SERVER tier (mock: "Zümrüt Lig"), DC sabiti "Altın Ligi" DEĞİL
    expect(screen.getByRole('heading', { name: 'Zümrüt Lig' })).toBeInTheDocument();
    expect(screen.queryByText(/Altın Ligi/)).not.toBeInTheDocument();
    // Sakin-mod alt başlık: locative-ek grameri KALDIRILDI (tier + em-dash), "'ndesin" YOK
    expect(screen.getByText(/^Zümrüt Lig — kendi ritminde ilerle, sıralama ikincil\.$/)).toBeInTheDocument();
    expect(screen.queryByText(/ndesin/)).not.toBeInTheDocument();
    // Podyum ilk-3: rozet aria-hidden + DOM 2-1-3 → ekran okuyucu için görünmez sıra metni
    expect(screen.getByText('1. sıra')).toBeInTheDocument();
    expect(screen.getByText('2. sıra')).toBeInTheDocument();
    expect(screen.getByText('3. sıra')).toBeInTheDocument();
    // Podyum + liste doğrudan server standings'ten (ilk sıra + SEN satırı)
    expect(screen.getByText('Zeynep Aksoy')).toBeInTheDocument();
    // "Hüseyin Ateş" hem SideNav hem SEN satırında geçer → en az bir düğüm
    expect(screen.getAllByText('Hüseyin Ateş').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('SEN')).toBeInTheDocument();
    // "geçen haftaya" kişisel-ilerleme kopyası (senVsDun sunucudan)
    expect(screen.getByText(/geçen haftaya/)).toBeInTheDocument();
  });

  it('toggle: sıralamayı gizle → gizli-durum kartı + standings gizlenir + aria-live duyuru', async () => {
    render(<LigPage />);
    await screen.findByText('Zeynep Aksoy');
    const gizle = screen.getByRole('button', { name: /Sıralamayı gizle/ });
    expect(gizle).toHaveAttribute('aria-pressed', 'false');

    fireEvent.click(gizle);

    // Gizli-durum kartı görünür, standings artık DOM'da değil
    expect(await screen.findByText('Sıralama gizli — odak sende.')).toBeInTheDocument();
    expect(screen.queryByText('Zeynep Aksoy')).not.toBeInTheDocument();
    // Tek aria-live bölgesi duyurdu
    expect(screen.getByText('Sıralama gizlendi')).toBeInTheDocument();
    // "gizle" düğmesi kalmadı; band toggle "göster" + aria-pressed true
    expect(screen.queryByRole('button', { name: /Sıralamayı gizle/ })).not.toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /Sıralamayı göster/ })[0]).toHaveAttribute('aria-pressed', 'true');
  });

  it('store.hideRanking=true → sıralama başlangıçta gizli (Ayarlar ile tek kaynak)', async () => {
    // Ayarlar'daki "Sıralamayı gizle" store'u çevirmiş gibi — Lig prop'suz açılır.
    useAyar.getState().setHideRanking(true);
    render(<LigPage />);
    // Gizli-durum kartı görünür, standings DOM'da değil (yerel state değil, store kaynağı)
    expect(await screen.findByText('Sıralama gizli — odak sende.')).toBeInTheDocument();
    expect(screen.queryByText('Zeynep Aksoy')).not.toBeInTheDocument();
    // Band toggle "göster" durumunda (aria-pressed true)
    expect(screen.getAllByRole('button', { name: /Sıralamayı göster/ })[0]).toHaveAttribute('aria-pressed', 'true');
  });

  it('düğme store.hideRanking\'i çevirir (çift-yönlü senkron kaynağı)', async () => {
    render(<LigPage />);
    await screen.findByText('Zeynep Aksoy');
    expect(useAyar.getState().hideRanking).toBe(false);

    fireEvent.click(screen.getByRole('button', { name: /Sıralamayı gizle/ }));
    expect(useAyar.getState().hideRanking).toBe(true);

    fireEvent.click(screen.getAllByRole('button', { name: /Sıralamayı göster/ })[0]);
    expect(useAyar.getState().hideRanking).toBe(false);
  });

  it('override modu (siralamaGizli prop): toggle NO-OP — global store kirlenmez', async () => {
    // Storybook/test override: görünen durum prop'a kilitli, store kaynak DEĞİL.
    render(<LigPage siralamaGizli={false} />);
    await screen.findByText('Zeynep Aksoy');
    expect(useAyar.getState().hideRanking).toBe(false);

    // Override modunda toggle NO-OP: global store DEĞİŞMEZ + görünen durum prop'a kilitli kalır.
    fireEvent.click(screen.getByRole('button', { name: /Sıralamayı gizle/ }));
    expect(useAyar.getState().hideRanking).toBe(false);
    expect(screen.getByText('Zeynep Aksoy')).toBeInTheDocument();
    expect(screen.queryByText('Sıralama gizli — odak sende.')).not.toBeInTheDocument();
  });

  it('CTA rota: leveledUp → "Seviyeyi kutla" bağlantısı /kutlama?type=seviye', async () => {
    render(<LigPage leveledUp />);
    const cta = await screen.findByRole('link', { name: /Seviyeyi kutla/ });
    expect(cta).toHaveAttribute('href', '/kutlama?type=seviye');
  });

  it('reduced-motion: giriş stagger kapanır, içerik korunur', async () => {
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
      render(<LigPage />);
      expect(await screen.findByText('Yarıştığın tek kişi dünkü sensin.')).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Zümrüt Lig' })).toBeInTheDocument();
    } finally {
      window.matchMedia = gercek;
    }
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<LigPage />);
    await screen.findByText('Zeynep Aksoy');
    expect(await axe(container)).toHaveNoViolations();
  }, 40000);
});
