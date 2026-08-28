import { render, screen, fireEvent } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect, afterEach } from 'vitest';

import { configureKiroApi } from '../api/api-client';
import type { MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';
import { IlkHaftaPage } from './IlkHaftaPage';

expect.extend(toHaveNoViolations);

// Ekran modül-yükünde configureKiroApi'yi tam mock'la kurar; error/responsive
// senaryoları config'i geçici override eder. Her testten sonra varsayılana döndür.
afterEach(() => {
  configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });
});

describe('IlkHaftaPage', () => {
  it('başlık + eyebrow render eder (SideNav yok)', async () => {
    render(<IlkHaftaPage />);
    expect(await screen.findByRole('heading', { name: 'İlk 7 Gün' })).toBeInTheDocument();
    expect(screen.getByText('Momentum Haftası')).toBeInTheDocument();
    // ortalı tek-kolon: SideNav yok
    expect(screen.queryByRole('navigation')).not.toBeInTheDocument();
  });

  it('ilerleme özetini gösterir (sunucu currentDay + mesaj + CTA → /bugun)', async () => {
    render(<IlkHaftaPage />);
    expect(await screen.findByText('/ 7 gün')).toBeInTheDocument();
    // ozet.mesaj — SEN dili ("yarına taşırsın"), sunucudan
    expect(screen.getByText('Bugün 3. gün — tek görev kaldı, sonra yarına taşırsın.')).toBeInTheDocument();
    const cta = screen.getByRole('link', { name: /Bugünü tamamla/ });
    expect(cta).toHaveAttribute('href', '/bugun');
    // İlerleme çubuğu — progressbar rolü + valuenow sunucudan (yalnız-renk değil)
    const bar = screen.getByRole('progressbar', { name: 'İlk hafta ilerlemesi' });
    expect(bar).toHaveAttribute('aria-valuenow', String(kiroData.ilkHafta.ozet.yuzde));
    expect(bar).toHaveAttribute('aria-valuemin', '0');
    expect(bar).toHaveAttribute('aria-valuemax', '100');
  });

  it('7-gün yayını (gün etiketleri) render eder + klavye-erişilebilir grup', async () => {
    render(<IlkHaftaPage />);
    expect(await screen.findByText('Kalibrasyon · seviyen bulundu')).toBeInTheDocument();
    expect(screen.getByText('Kilometre taşı + dondurma')).toBeInTheDocument();
    // GÜN 1 yalnız yay etiketinde; GÜN 7 hem yayda hem kart tag'inde
    expect(screen.getByText('GÜN 1')).toBeInTheDocument();
    expect(screen.getAllByText('GÜN 7').length).toBeGreaterThanOrEqual(1);
    // Yatay-scroll yay klavyeyle kaydırılabilir (WCAG 2.1.1): tabIndex + role=group
    const yay = screen.getByRole('group', { name: 'İlk 7 gün' });
    expect(yay).toHaveAttribute('tabindex', '0');
    // Durum yalnız-renkle aktarılmaz — SR-only durum metinleri mevcut
    expect(screen.getByText('Bugün')).toBeInTheDocument();
    expect(screen.getAllByText('Tamamlandı').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Kilitli').length).toBeGreaterThanOrEqual(1);
  });

  it('4 kilometre-taşı kartını render eder', async () => {
    render(<IlkHaftaPage />);
    await screen.findByText('İlk 7 Gün');
    expect(screen.getByText('Gün 3 · tek görev')).toBeInTheDocument();
    expect(screen.getByText('Gün 4 · ilk rozet')).toBeInTheDocument();
    expect(screen.getByText('İlk hafta neden kritik')).toBeInTheDocument();
    // "Kilometre taşı" kart başlığı — "Kilometre taşı + dondurma" gün etiketinden ayrı düğüm
    expect(screen.getByText('Kilometre taşı')).toBeInTheDocument();
  });

  it('yükleme: veri gelmeden aria-busy iskelet gösterir', async () => {
    render(<IlkHaftaPage />);
    // İlk render: veri henüz yok (data===null) → aria-busy yükleme bölgesi
    expect(screen.getByLabelText('İlk hafta yükleniyor')).toHaveAttribute('aria-busy', 'true');
    // Veri gelince iskelet kaybolur, CTA + içerik render olur (act flush)
    expect(await screen.findByRole('link', { name: /Bugünü tamamla/ })).toBeInTheDocument();
    expect(screen.queryByLabelText('İlk hafta yükleniyor')).not.toBeInTheDocument();
  });

  it('getIlkHafta reddi → ErrorState + retry veriyi getirir', async () => {
    // baseUrl'siz live → getIlkHafta() reddeder (KiroApi: live modda baseUrl zorunlu).
    configureKiroApi({ mode: 'live' });
    render(<IlkHaftaPage />);
    // Sakin hata durumu — ekranın serif başlığı + retry butonu (kırmızı/hata kodu yok).
    expect(await screen.findByText('İlk hafta yayın şu an gelmedi.')).toBeInTheDocument();
    // Retry öncesi mock'a dön → "Tekrar dene" veriyi yeniden getirir.
    configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });
    fireEvent.click(screen.getByRole('button', { name: 'Tekrar dene' }));
    expect(await screen.findByRole('link', { name: /Bugünü tamamla/ })).toBeInTheDocument();
    expect(screen.queryByText('İlk hafta yayın şu an gelmedi.')).not.toBeInTheDocument();
  });

  it('dar (≤640px): tek-kolon dallar — içerik korunur', async () => {
    const gercek = window.matchMedia;
    window.matchMedia = ((q: string) => ({
      matches: q.includes('640'),
      media: q,
      onchange: null,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      addListener: () => undefined,
      removeListener: () => undefined,
      dispatchEvent: () => false,
    })) as unknown as typeof window.matchMedia;
    try {
      render(<IlkHaftaPage />);
      // dar=true iken de başlık + CTA + kartlar render olur (tek-kolon grid/padding dalları).
      expect(await screen.findByRole('heading', { name: 'İlk 7 Gün' })).toBeInTheDocument();
      expect(await screen.findByRole('link', { name: /Bugünü tamamla/ })).toBeInTheDocument();
      expect(screen.getByText('Gün 3 · tek görev')).toBeInTheDocument();
    } finally {
      window.matchMedia = gercek;
    }
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<IlkHaftaPage />);
    await screen.findByText('İlk 7 Gün');
    await screen.findByRole('link', { name: /Bugünü tamamla/ });
    expect(await axe(container)).toHaveNoViolations();
  }, 40000);
});
