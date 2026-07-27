import { render, screen, fireEvent } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect, afterEach } from 'vitest';

import { configureKiroApi } from '../api/api-client';
import type { MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';
import { CevrimdisiPage } from './CevrimdisiPage';

expect.extend(toHaveNoViolations);

// Ekran mount'ta configureKiroApi'yi tam veriyle kurar; error/empty senaryoları
// config'i geçici override eder. Her testten sonra varsayılan mock'a döndür.
afterEach(() => {
  configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });
});

describe('CevrimdisiPage', () => {
  it('çevrimdışı: amber bant + hero + "Cihazında hazır" paketleri', async () => {
    render(<CevrimdisiPage durumBaslangic="cevrimdisi" />);
    // Bant (role=status) — kaygı-duyarlı başlık + alt
    expect(await screen.findByText('Çevrimdışısın')).toBeInTheDocument();
    expect(screen.getByText('— sorun değil, çalışman cihazında sürüyor.')).toBeInTheDocument();
    // Hero
    expect(screen.getByRole('heading', { level: 1, name: 'İnternet gitti. Çalışman gitmedi.' })).toBeInTheDocument();
    // Sol sütun + paketler
    expect(screen.getByRole('heading', { name: 'Cihazında hazır' })).toBeInTheDocument();
    expect(await screen.findByText('Bugünkü plan')).toBeInTheDocument();
    expect(screen.getByText('FSRS tekrar kartları')).toBeInTheDocument();
    // Son eşitleme (tabular)
    expect(screen.getByText(/Son eşitleme: bugün 14:32/)).toBeInTheDocument();
  });

  it('eşitleme kuyruğu: bekleyen öğeler + "kendiliğinden boşalır" güvencesi', async () => {
    render(<CevrimdisiPage durumBaslangic="cevrimdisi" />);
    expect(await screen.findByRole('heading', { name: 'Eşitleme kuyruğu' })).toBeInTheDocument();
    expect(screen.getByText('Türev seti — 12 yanıt')).toBeInTheDocument();
    expect(screen.getByText('Limit tekrarı — 3 kart')).toBeInTheDocument();
    expect(screen.getByText(/Bağlantı gelince bu liste kendiliğinden boşalır/)).toBeInTheDocument();
  });

  it('hazır olmayan paket: "Başla" yerine "Sırada" (bağlantı bekler)', async () => {
    render(<CevrimdisiPage durumBaslangic="cevrimdisi" />);
    // Hazır paket → "Başla" linki
    expect(await screen.findByRole('link', { name: 'Bugünkü plan — başla' })).toBeInTheDocument();
    // Konu videoları hazır değil → link YOK, "Sırada" çipi
    expect(screen.getByText('Konu anlatım videoları')).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /Konu anlatım videoları/ })).not.toBeInTheDocument();
    expect(screen.getByText('Sırada')).toBeInTheDocument();
  });

  it('bağlantı bekliyor: canlı yüzeyler statik listede', async () => {
    render(<CevrimdisiPage durumBaslangic="cevrimdisi" />);
    expect(await screen.findByRole('heading', { name: 'Bağlantı bekliyor' })).toBeInTheDocument();
    expect(screen.getByText('KIRO Koç (AI)')).toBeInTheDocument();
    expect(screen.getByText('Lig & Düello')).toBeInTheDocument();
  });

  it('bağlandı: success bant + "Hoş geldin" hero', async () => {
    render(<CevrimdisiPage durumBaslangic="baglandi" />);
    expect(await screen.findByText('Bağlantı geldi')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1, name: 'Hoş geldin — kaldığın yerdeyiz.' })).toBeInTheDocument();
  });

  it('reduced-motion: içerik korunur (animasyon/spring yok)', async () => {
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
      render(<CevrimdisiPage durumBaslangic="cevrimdisi" />);
      expect(await screen.findByText('Bugünkü plan')).toBeInTheDocument();
    } finally {
      window.matchMedia = gercek;
    }
  });

  it('yeniden_baglaniyor: dawn bant + DÜRÜST bekleme mesajı (kesintisiz-çalışma VAAT ETMEZ)', async () => {
    render(<CevrimdisiPage durumBaslangic="yeniden_baglaniyor" />);
    expect(await screen.findByText('Yeniden bağlanıyor…')).toBeInTheDocument();
    expect(
      screen.getByText('bağlantı kurulunca kaldığın yerden devam edebilirsin.'),
    ).toBeInTheDocument();
  });

  it('yükleme: veri gelmeden aria-busy iskelet gösterir', async () => {
    render(<CevrimdisiPage durumBaslangic="cevrimdisi" />);
    // İlk render: veri henüz yok → aria-busy yükleme bölgesi
    expect(screen.getByLabelText('Çevrimdışı durumu yükleniyor')).toHaveAttribute('aria-busy', 'true');
    // Veri gelince iskelet kaybolur, içerik render olur (act flush)
    expect(await screen.findByText('Bugünkü plan')).toBeInTheDocument();
  });

  it('boş kuyruk: EmptyState "Bağlantı bekleyen bir şey yok"', async () => {
    const bosKuyruk = {
      ...kiroData,
      cevrimdisi: { ...kiroData.cevrimdisi, kuyruk: [] },
    };
    configureKiroApi({ mode: 'mock', mockData: bosKuyruk as unknown as MockData });
    render(<CevrimdisiPage durumBaslangic="cevrimdisi" />);
    expect(await screen.findByText('Bağlantı bekleyen bir şey yok')).toBeInTheDocument();
    expect(screen.getByText('Her şey eşitlendi — kuyruğun tertemiz.')).toBeInTheDocument();
    // Kuyruk boşken "kendiliğinden boşalır" güvencesi gösterilmez
    expect(screen.queryByText(/kendiliğinden boşalır/)).not.toBeInTheDocument();
  });

  it('getCevrimdisiDurum reddi: ErrorState + retry veriyi getirir; persona hatası ekranı düşürmez', async () => {
    // mockData yok → hem getMe hem getCevrimdisiDurum reddeder
    configureKiroApi({ mode: 'mock', mockData: undefined });
    render(<CevrimdisiPage durumBaslangic="cevrimdisi" />);
    // Birincil hata → ErrorState (sakin, amber; kırmızı/hata kodu yok)
    expect(await screen.findByText('Çevrimdışı durumu şu an gelmedi.')).toBeInTheDocument();
    // Persona reddi tolere edildi → SideNav fallback "Öğrenci"
    expect(screen.getByText('Öğrenci')).toBeInTheDocument();
    // Retry: config düzelir, "Tekrar dene" veriyi yeniden getirir
    configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });
    fireEvent.click(screen.getByRole('button', { name: 'Tekrar dene' }));
    expect(await screen.findByText('Bugünkü plan')).toBeInTheDocument();
    expect(screen.queryByText('Çevrimdışı durumu şu an gelmedi.')).not.toBeInTheDocument();
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<CevrimdisiPage durumBaslangic="cevrimdisi" />);
    await screen.findByText('Bugünkü plan');
    expect(await axe(container)).toHaveNoViolations();
  }, 40000);
});
