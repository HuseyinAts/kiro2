import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { OgrenciOzetiPage } from './OgrenciOzetiPage';

expect.extend(toHaveNoViolations);

describe('OgrenciOzetiPage', () => {
  it('sağlıklı (o-ha): kimlik + salt-okur + KPI + ders hâkimiyeti; risk şeridi YOK', async () => {
    render(<OgrenciOzetiPage ogrenciId="o-ha" />);
    // Kimlik bandı — ad sunucudan
    expect(await screen.findByText('Hüseyin Ateş')).toBeInTheDocument();
    // Salt-okur görünüm pili (a11y: durum metinle)
    expect(screen.getByText('Salt-okur görünüm')).toBeInTheDocument();
    // Sağlıklı durum şeridi — renk-dışı metin
    expect(screen.getByText(/Ritmi sağlıklı/)).toBeInTheDocument();
    expect(screen.queryByText(/9 gündür oturum açmadı/)).not.toBeInTheDocument();
    // KPI etiketleri (net/hâkimiyet/seri/çözülen) + çözülen değeri (312, benzersiz)
    expect(screen.getByText('Son deneme TYT net')).toBeInTheDocument();
    expect(screen.getByText('Genel hâkimiyet')).toBeInTheDocument();
    expect(screen.getByText('Çalışma serisi')).toBeInTheDocument();
    expect(screen.getByText('Çözülen soru')).toBeInTheDocument();
    expect(screen.getByText('312')).toBeInTheDocument();
    // Ders hâkimiyeti — konu-düzeyi ProgressBar (Matematik yüzde 78)
    expect(screen.getByLabelText('Matematik hâkimiyeti yüzde 78')).toBeInTheDocument();
    // Gizlilik kutusu — SIZ kanonu
    expect(screen.getByText('Öğrenci gizliliği')).toBeInTheDocument();
    expect(screen.getByText(/yalnız yetişkine gösterilir/)).toBeInTheDocument();
  });

  it('dikkat (emre-sahin): amber riskMetni + "yalnız size görünür" + net regex', async () => {
    render(<OgrenciOzetiPage ogrenciId="emre-sahin" />);
    expect(await screen.findByText('Emre Şahin')).toBeInTheDocument();
    // Sunucu risk metni + gizlilik alt-satırı (SIZ)
    expect(screen.getByText('9 gündür oturum açmadı')).toBeInTheDocument();
    expect(screen.getByText(/yalnız size görünür/)).toBeInTheDocument();
    // Sağlıklı şerit görünmez
    expect(screen.queryByText(/Ritmi sağlıklı/)).not.toBeInTheDocument();
    // net = 58,5 (tabular, tr-TR)
    expect(screen.getByText('58,5')).toBeInTheDocument();
  });

  it('CTA "Bu öğrenciye ödev ata" → Ödev Atama link; geri-link → /ogretmen', async () => {
    render(<OgrenciOzetiPage ogrenciId="o-ha" />);
    const cta = await screen.findByRole('link', { name: /Bu öğrenciye ödev ata/ });
    expect(cta.getAttribute('href')).toMatch(/^\/ogretmen\/odev-ata/);
    const geri = screen.getByRole('link', { name: /Öğretmen Paneli/ });
    expect(geri).toHaveAttribute('href', '/ogretmen');
  });

  it('reduced-motion: içerik korunur (paper — spring/konfeti yok)', async () => {
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
      render(<OgrenciOzetiPage ogrenciId="o-ha" />);
      expect(await screen.findByText('Hüseyin Ateş')).toBeInTheDocument();
      expect(screen.getByText('Ders hâkimiyeti')).toBeInTheDocument();
    } finally {
      window.matchMedia = gercek;
    }
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<OgrenciOzetiPage ogrenciId="o-ha" />);
    await screen.findByText('Hüseyin Ateş');
    expect(await axe(container)).toHaveNoViolations();
  }, 40000);
});
