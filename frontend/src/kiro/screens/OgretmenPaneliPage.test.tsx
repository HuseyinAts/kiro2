import { render, screen, fireEvent } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { OgretmenPaneliPage } from './OgretmenPaneliPage';

expect.extend(toHaveNoViolations);

describe('OgretmenPaneliPage', () => {
  it('SideNav + "Panel" başlığı + KPI + öğrenci performansı tablosu render eder', async () => {
    render(<OgretmenPaneliPage />);
    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Panel', level: 1 })).toBeInTheDocument();
    // KPI (sunucu-otorite kpi.*)
    expect(await screen.findByText('Sınıf ortalama net')).toBeInTheDocument();
    expect(screen.getByText('72,4')).toBeInTheDocument();
    expect(screen.getByText('+3,1')).toBeInTheDocument();
    expect(screen.getByText('Aktif öğrenci (7g)')).toBeInTheDocument();
    // Tablo + gerçek öğrenci satırı
    expect(screen.getByRole('table')).toBeInTheDocument();
    expect(screen.getByText('Öğrenci Performansı')).toBeInTheDocument();
    expect(screen.getByText('Zeynep Kaya')).toBeInTheDocument();
  });

  it('tablo başlıkları th scope=col; satır linkinin erişilebilir adı = öğrenci adı → /ogretmen/ogrenci/:id', async () => {
    render(<OgretmenPaneliPage />);
    await screen.findByText('Öğrenci Performansı');
    const kolonBasliklari = screen.getAllByRole('columnheader');
    expect(kolonBasliklari.length).toBeGreaterThanOrEqual(3);
    kolonBasliklari.forEach((th) => expect(th).toHaveAttribute('scope', 'col'));
    // Satır linki: erişilebilir ad tam öğrenci adı (DoD)
    const satirLink = screen.getByRole('link', { name: 'Zeynep Kaya' });
    expect(satirLink).toHaveAttribute('href', '/ogretmen/ogrenci/o-zk');
  });

  it('topbar CTA rotaları: "Ödev oluştur" → /ogretmen/odev/yeni, "Yeni sınıf kur" → /ogretmen/sinif/yeni', async () => {
    render(<OgretmenPaneliPage />);
    await screen.findByText('Öğrenci Performansı');
    expect(screen.getByRole('link', { name: /Ödev oluştur/ })).toHaveAttribute('href', '/ogretmen/odev/yeni');
    expect(screen.getByRole('link', { name: 'Yeni sınıf kur' })).toHaveAttribute('href', '/ogretmen/sinif/yeni');
  });

  it('sınıf seçici gerçek <button> + aria-pressed; sınıf değişince seçim taşınır', async () => {
    render(<OgretmenPaneliPage />);
    await screen.findByText('Öğrenci Performansı');
    const aktif = screen.getByRole('button', { name: /12-A · Sayısal/ });
    expect(aktif).toHaveAttribute('aria-pressed', 'true');
    const diger = screen.getByRole('button', { name: /11-B · Eşit Ağırlık/ });
    expect(diger).toHaveAttribute('aria-pressed', 'false');
    fireEvent.click(diger);
    // Yeniden yükleme sonrası 11-B seçili olur (sunucu-otorite aktifSinifId)
    const yeniAktif = await screen.findByRole('button', { name: /11-B · Eşit Ağırlık/, pressed: true });
    expect(yeniAktif).toBeInTheDocument();
  });

  it('dikkat kartları (amber, salt-okur) + tabloda risk metni renk-dışı okunur', async () => {
    render(<OgretmenPaneliPage />);
    await screen.findByText('Öğrenci Performansı');
    expect(screen.getByText('Dikkat gerektiren öğrenciler')).toBeInTheDocument();
    // Burak Çelik hem dikkat kartında hem roster satırında görünür → en az bir düğüm
    expect(screen.getAllByText('Burak Çelik').length).toBeGreaterThanOrEqual(1);
    // Dikkat kartının kendine özgü metni (yalnız kartta)
    expect(screen.getByText('5 gündür giriş yok')).toBeInTheDocument();
    // Risk = metinle taşınır (yalnız renk değil): Can Yıldız satırında "Net düşüşte"
    expect(screen.getByText('Net düşüşte')).toBeInTheDocument();
    // Sınıf konu hâkimiyeti bloğu
    expect(screen.getByText('Sınıf konu hâkimiyeti')).toBeInTheDocument();
    expect(screen.getByRole('progressbar', { name: /Fonksiyonlar sınıf hâkimiyeti yüzde 80/ })).toBeInTheDocument();
  });

  it('reduced-motion: içerik korunur (paper motion guard)', async () => {
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
      render(<OgretmenPaneliPage />);
      expect(await screen.findByText('Öğrenci Performansı')).toBeInTheDocument();
    } finally {
      window.matchMedia = gercek;
    }
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<OgretmenPaneliPage />);
    await screen.findByText('Öğrenci Performansı');
    expect(await axe(container)).toHaveNoViolations();
  }, 40000);
});
