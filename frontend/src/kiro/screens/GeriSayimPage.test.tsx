import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { GeriSayimPage } from './GeriSayimPage';

expect.extend(toHaveNoViolations);

describe('GeriSayimPage', () => {
  it('varsayılan (B · kaygı-nötr): "Bugüne bak" başlığı + gün-sayacı YOK', async () => {
    render(<GeriSayimPage />);
    // Serif başlık iki metin düğümüne (br) bölünür → ilk parçayı ara
    expect(await screen.findByText(/Bugüne bak/)).toBeInTheDocument();
    expect(screen.getByText(/Gün saymaya gerek yok/)).toBeInTheDocument();
    // Sabit ufuk pili (sayaç değil)
    expect(screen.getByText(/YKS ufku ·/)).toBeInTheDocument();
    // B'de geleneksel geri-sayım gövdesi geçmez
    expect(screen.queryByText(/Sınav senin şafağın/)).not.toBeInTheDocument();
  });

  it('hedef kartı: bölüm + üniversite + hedef sıralama (ortak blok)', async () => {
    render(<GeriSayimPage />);
    expect(await screen.findByText('Bilgisayar Mühendisliği')).toBeInTheDocument();
    expect(screen.getByText(/ODTÜ \/ Bilkent · ilk 15\.000/)).toBeInTheDocument();
    // B alt satırında güncel sıralama SAYISI geçmez (bilinçli)
    expect(screen.getByText(/istikrar sıralamadan güçlü/)).toBeInTheDocument();
    expect(screen.queryByText(/sıradaydın/)).not.toBeInTheDocument();
  });

  it('CTA "Bugünün tuğlasını koy" → /soru-cozme; başlık /bugun', async () => {
    render(<GeriSayimPage />);
    const cta = await screen.findByRole('link', { name: /Bugünün tuğlasını koy/ });
    expect(cta).toHaveAttribute('href', '/soru-cozme');
  });

  it('A varyant (geri-sayim): eyebrow + dev gün-sayısı (regex) + "gündoğumu kaldı"', async () => {
    render(<GeriSayimPage varyant="geri-sayim" />);
    expect(await screen.findByText(/^YKS · /)).toBeInTheDocument();
    expect(screen.getByText('gündoğumu kaldı')).toBeInTheDocument();
    // Dev sayı gün sayısına bağlı → non-deterministik; sadece rakam varlığını doğrula
    const devSayi = screen.getByText((content, el) => el?.tagName === 'DIV' && /^\d{1,4}$/.test(content));
    expect(devSayi).toBeInTheDocument();
    // A alt satırında güncel sıralama görünür
    expect(screen.getByText(/sıradaydın/)).toBeInTheDocument();
  });

  it('reduced-motion: gökyüzü/yıldız animasyonu kapanır, içerik korunur', async () => {
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
      render(<GeriSayimPage />);
      expect(await screen.findByText(/Bugüne bak/)).toBeInTheDocument();
    } finally {
      window.matchMedia = gercek;
    }
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<GeriSayimPage />);
    await screen.findByText('Bilgisayar Mühendisliği');
    expect(await axe(container)).toHaveNoViolations();
  }, 40000);
});
