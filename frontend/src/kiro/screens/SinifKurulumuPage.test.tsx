import { render, screen, fireEvent } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { SinifKurulumuPage } from './SinifKurulumuPage';

expect.extend(toHaveNoViolations);

describe('SinifKurulumuPage', () => {
  it('adım 1 (bilgi): başlık + form + rol rozeti + adım göstergesi', async () => {
    render(<SinifKurulumuPage />);
    expect(await screen.findByText('İlk sınıfını kur.')).toBeInTheDocument();
    // Rol dili — öğretmen yüzeyi
    expect(screen.getByText(/Öğretmen · sınıf kurulumu/)).toBeInTheDocument();
    // Adım göstergesi (aria-live etiket)
    expect(screen.getByText('Adım 1 / 3 · Bilgi')).toBeInTheDocument();
    // Form alanları (etiketli input + iki radiogroup)
    expect(screen.getByLabelText('Sınıf adı')).toBeInTheDocument();
    expect(screen.getByRole('radiogroup', { name: 'Düzey' })).toBeInTheDocument();
    expect(screen.getByRole('radiogroup', { name: 'Alan' })).toBeInTheDocument();
  });

  it('segment radiogroup: varsayılan seçim + tıklamada aria-checked taşınır', async () => {
    render(<SinifKurulumuPage />);
    await screen.findByText('İlk sınıfını kur.');
    // Varsayılan düzey = 12. Sınıf, alan = Sayısal
    expect(screen.getByRole('radio', { name: '12. Sınıf' })).toHaveAttribute('aria-checked', 'true');
    expect(screen.getByRole('radio', { name: 'Sayısal' })).toHaveAttribute('aria-checked', 'true');
    // Mezun'a tıkla → seçim taşınır
    fireEvent.click(screen.getByRole('radio', { name: 'Mezun' }));
    expect(screen.getByRole('radio', { name: 'Mezun' })).toHaveAttribute('aria-checked', 'true');
    expect(screen.getByRole('radio', { name: '12. Sınıf' })).toHaveAttribute('aria-checked', 'false');
  });

  it('"Sınıfı oluştur" → davet adımı: sunucu kodu (postSinif) görünür; "Devam et" → hazır + /ogretmen/panel', async () => {
    render(<SinifKurulumuPage />);
    fireEvent.change(await screen.findByLabelText('Sınıf adı'), { target: { value: '12-B' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sınıfı oluştur' }));

    // Adım 2 · Davet — kod bloğu sunucudan gelir (istemci üretmez)
    expect(await screen.findByText('Sınıf katılım kodu')).toBeInTheDocument();
    // Kod deterministik değil → 6 hane (XXX XXX) formatını regex ile doğrula
    expect(screen.getByText(/^\d{3}\s\d{3}$/)).toBeInTheDocument();
    expect(screen.getByText('Adım 2 / 3 · Davet')).toBeInTheDocument();

    // "Devam et" → Adım 3 · Hazır + panel rotası
    fireEvent.click(screen.getByRole('button', { name: 'Devam et' }));
    const panele = await screen.findByRole('link', { name: 'Panele git' });
    expect(panele).toHaveAttribute('href', '/ogretmen/panel');
    expect(screen.getByText('12-B kuruldu.')).toBeInTheDocument();
  });

  it('kopyala: pano-kopya + "Kopyalandı" etiketi (aria-live geri bildirim)', async () => {
    render(<SinifKurulumuPage />);
    fireEvent.click(await screen.findByRole('button', { name: 'Sınıfı oluştur' }));
    const kopyaBtn = await screen.findByRole('button', { name: /Kodu kopyala/ });
    fireEvent.click(kopyaBtn);
    expect(await screen.findByText('Kopyalandı')).toBeInTheDocument();
  });

  it('reduced-motion: adım animasyonu kapanır, içerik korunur', async () => {
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
      render(<SinifKurulumuPage />);
      expect(await screen.findByText('İlk sınıfını kur.')).toBeInTheDocument();
    } finally {
      window.matchMedia = gercek;
    }
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<SinifKurulumuPage />);
    await screen.findByText('İlk sınıfını kur.');
    expect(await axe(container)).toHaveNoViolations();
  }, 40000);
});
