import { render, screen, fireEvent } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { VeliBaglamaPage } from './VeliBaglamaPage';

expect.extend(toHaveNoViolations);

// Mock demo kodu (kiro-data.veliBaglama.veliBaglamaKodu) — sunucu-otoriter doğrulama.
const KOD = '482913';

describe('VeliBaglamaPage', () => {
  it('veli · adım 1 (kod): resmi SİZ başlık + kodu alanı + "Adım 1 / 3" etiketi', async () => {
    render(<VeliBaglamaPage taraf="veli" />);
    // Serif başlık (VELİ dili = SİZ)
    expect(await screen.findByText('Çocuğunuzu güvenle bağlayın.')).toBeInTheDocument();
    // Kod alanı — aria-label ile (tabular 6-hane)
    expect(screen.getByLabelText('6 haneli bağlantı kodu')).toBeInTheDocument();
    // Adım göstergesi (aria-live etiket)
    expect(screen.getByText('Adım 1 / 3')).toBeInTheDocument();
    // Veli-tarafı rozeti
    expect(screen.getByText('Veli bağlantısı')).toBeInTheDocument();
  });

  it('veli · geçerli kod → rıza adımı: 2-sütun kapsam + KVKK CTA onaysız disabled → onay sonrası aktif', async () => {
    render(<VeliBaglamaPage taraf="veli" />);
    fireEvent.change(await screen.findByLabelText('6 haneli bağlantı kodu'), { target: { value: KOD } });
    fireEvent.click(screen.getByRole('button', { name: 'Devam et' }));

    // Adım 2 · Rıza — sunucu (verifyLinkCode) geçerli döndü
    expect(await screen.findByText('Neyi görürsünüz, neyi görmezsiniz?')).toBeInTheDocument();
    expect(screen.getByText('Görürsünüz')).toBeInTheDocument();
    expect(screen.getByText('Asla görmezsiniz')).toBeInTheDocument();

    // KVKK açık-rıza CTA onaysızken gerçek disabled
    const cta = screen.getByRole('button', { name: 'Rıza ver ve bağlantıyı başlat' });
    expect(cta).toBeDisabled();

    // Çekbox (link AYRI, tıklama-bölgesi AYRI) — işaretle → CTA aktifleşir
    const kvkkCheck = screen.getByRole('checkbox', { name: /KVKK Aydınlatma Metni/ });
    fireEvent.click(kvkkCheck);
    expect(kvkkCheck).toHaveAttribute('aria-checked', 'true');
    expect(cta).not.toBeDisabled();
    // KVKK linki çekboxtan ayrı bir bağlantı (iç-içe interaktif YASAK)
    expect(screen.getByRole('link', { name: 'KVKK Aydınlatma Metni' })).toHaveAttribute('href', '/kvkk');
  });

  it('veli · hatalı kod → amber "doğrulanamadı" ipucu (aria-live; alarm dili yok)', async () => {
    render(<VeliBaglamaPage taraf="veli" />);
    // 6 hane ama yanlış kod → sunucu gecerli:false
    fireEvent.change(await screen.findByLabelText('6 haneli bağlantı kodu'), { target: { value: '111111' } });
    fireEvent.click(screen.getByRole('button', { name: 'Devam et' }));
    expect(await screen.findByText(/Kod doğrulanamadı/)).toBeInTheDocument();
    // Rıza adımına geçilmedi
    expect(screen.queryByText('Neyi görürsünüz, neyi görmezsiniz?')).not.toBeInTheDocument();
  });

  it('veli · tam akış: rıza → bekle → (simüle onay) → tamam + "Veli paneline git" /veli', async () => {
    render(<VeliBaglamaPage taraf="veli" />);
    fireEvent.change(await screen.findByLabelText('6 haneli bağlantı kodu'), { target: { value: KOD } });
    fireEvent.click(screen.getByRole('button', { name: 'Devam et' }));

    await screen.findByText('Neyi görürsünüz, neyi görmezsiniz?');
    fireEvent.click(screen.getByRole('checkbox', { name: /KVKK Aydınlatma Metni/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Rıza ver ve bağlantıyı başlat' }));

    // Adım 3 · Bekle — çocuk adı sunucu yanıtından (Hüseyin)
    expect(await screen.findByText(/Şimdi söz Hüseyin/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Prototip: çocuk onayını simüle et/ }));

    // Tamam — pollLinkStatus 'onaylandi' döndü
    expect(await screen.findByText('Bağlantı kuruldu.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Veli paneline git' })).toHaveAttribute('href', '/veli');
  });

  it('öğrenci · akran SEN: bekleyen istek + kapsam → "Bağlantıyı onayla" → "Bağlandı — sınırlar sende."', async () => {
    render(<VeliBaglamaPage taraf="ogrenci" />);
    // Öğrenci dili (SEN) + veli kimliği sunucudan (getPendingParentRequest)
    expect(await screen.findByText(/Desteklemek istiyor/)).toBeInTheDocument();
    expect(screen.getByText('Ayşe Ateş')).toBeInTheDocument();
    expect(screen.getByText('Görebilir')).toBeInTheDocument();
    expect(screen.getByText('Asla göremez')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Bağlantıyı onayla' }));
    expect(await screen.findByText('Bağlandı — sınırlar sende.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Çalışmaya dön' })).toHaveAttribute('href', '/bugun');
  });

  it('reduced-motion: adım animasyonu kapanır, içerik korunur (paper — konfeti/spring yok)', async () => {
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
      render(<VeliBaglamaPage taraf="veli" />);
      expect(await screen.findByText('Çocuğunuzu güvenle bağlayın.')).toBeInTheDocument();
    } finally {
      window.matchMedia = gercek;
    }
  });

  it('axe: erişilebilirlik ihlali yok (veli · rıza — kapsam + split çekbox)', async () => {
    const { container } = render(<VeliBaglamaPage taraf="veli" />);
    fireEvent.change(await screen.findByLabelText('6 haneli bağlantı kodu'), { target: { value: KOD } });
    fireEvent.click(screen.getByRole('button', { name: 'Devam et' }));
    await screen.findByText('Neyi görürsünüz, neyi görmezsiniz?');
    expect(await axe(container)).toHaveNoViolations();
  }, 40000);
});
