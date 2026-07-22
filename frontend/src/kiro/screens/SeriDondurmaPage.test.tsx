import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { SeriDondurmaPage } from './SeriDondurmaPage';

expect.extend(toHaveNoViolations);

describe('SeriDondurmaPage', () => {
  it('başlık + hero seri + "En uzun · {rekor} gün" pili (sunucu-otorite)', async () => {
    render(<SeriDondurmaPage />);
    expect(screen.getByText('Seri & Motivasyon')).toBeInTheDocument();
    expect(screen.getByText('Alışkanlık koru — affedicilikle, baskıyla değil')).toBeInTheDocument();
    // Hero: seri=12 → "günlük seri" + rekor=21 pili
    expect(await screen.findByText('günlük seri')).toBeInTheDocument();
    expect(screen.getByText(/En uzun · 21 gün/)).toBeInTheDocument();
  });

  it('bu hafta: freeze günü sunucu durumundan türer + dondurma hakkı metinle erişilebilir', async () => {
    render(<SeriDondurmaPage />);
    // hafta[]'da Per=freeze → "Per günü dondurma kurtardı" (istemci hesaplamaz, okur)
    expect(await screen.findByText('Per günü dondurma kurtardı')).toBeInTheDocument();
    // dondurmaHak=2 → SR metni ("{n} dondurma hakkın kaldı"); lejant "Dondurma"
    expect(screen.getByText(/2 dondurma hakkın kaldı/)).toBeInTheDocument();
    expect(screen.getByText('Dondurma')).toBeInTheDocument();
    // hafta karoları role=img + tek-string aria-label (freeze → tam metin)
    expect(screen.getByLabelText('Per günü dondurma ile korundu')).toBeInTheDocument();
    // today karosu label'i zaten 'Bugün' → 'Bugün · bugün' tekrarı önlenir, anlamlı metin
    expect(screen.getByLabelText('Bugün · henüz tamamlanmadı, sıra sende')).toBeInTheDocument();
  });

  it('Seri Dondurma kartı: affedicilik gövdesi + %48 istatistiği ÇIKARILDI + agresif nudge PORTLANMADI', async () => {
    render(<SeriDondurmaPage />);
    expect(await screen.findByText('Seri Dondurma')).toBeInTheDocument();
    expect(screen.getByText('affedicilik mekanizması')).toBeInTheDocument();
    expect(screen.getByText(/ayların emeğini silmesin/)).toBeInTheDocument();
    expect(screen.getByText('İNSANİ NUDGE')).toBeInTheDocument();
    // Kullanıcı kararı: %48 istatistik kutusu yazılmadı
    expect(screen.queryByText(/%48/)).not.toBeInTheDocument();
    // Anti-örnek agresif ton ASLA portlanmaz
    expect(screen.queryByText(/TEHLİKEDE/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/tonu değiştir/)).not.toBeInTheDocument();
  });

  it('kilometre taşları: Alev → Şu an → Rekor → Taç (client kaldı yalnız gösterim)', async () => {
    render(<SeriDondurmaPage />);
    expect(await screen.findByText('Kilometre taşları')).toBeInTheDocument();
    expect(screen.getByText('Şu an')).toBeInTheDocument();
    // seri=12, rekor=21 → kaldi(rekor)=9, kaldi(30)=18
    expect(screen.getByText('Rekor · 9 gün')).toBeInTheDocument();
    expect(screen.getByText('18 gün kaldı')).toBeInTheDocument();
  });

  it('CTA "Bugünü tamamla" → /soru-cozme; hero "Seriyi kutla" → /kutlama?type=seri', async () => {
    render(<SeriDondurmaPage />);
    const cta = await screen.findByRole('link', { name: 'Bugünü tamamla' });
    expect(cta).toHaveAttribute('href', '/soru-cozme');
    const kutla = screen.getByRole('link', { name: /Seriyi kutla/ });
    expect(kutla).toHaveAttribute('href', '/kutlama?type=seri');
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
      render(<SeriDondurmaPage />);
      expect(await screen.findByText('günlük seri')).toBeInTheDocument();
      expect(screen.getByText('Seri Dondurma')).toBeInTheDocument();
    } finally {
      window.matchMedia = gercek;
    }
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<SeriDondurmaPage />);
    await screen.findByText('Seri Dondurma');
    expect(await axe(container)).toHaveNoViolations();
  }, 40000);
});
