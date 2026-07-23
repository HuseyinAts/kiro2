import { render, screen, fireEvent } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect, afterEach } from 'vitest';

import { configureKiroApi } from '../api/api-client';
import type { MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';
import type { AbonelikYonetim } from '../types';
import { PlanYonetimiPage } from './PlanYonetimiPage';

expect.extend(toHaveNoViolations);

// Fiyat/durum/fatura SUNUCU-otoriter → varyant matrisi mock yamasıyla kurulur.
function mockWith(patch: Partial<AbonelikYonetim>): MockData {
  return { ...kiroData, abonelikYonetim: { ...kiroData.abonelikYonetim, ...patch } } as unknown as MockData;
}

// Her testten sonra varsayılan (tam) mock'a döndür.
afterEach(() => {
  configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });
});

describe('PlanYonetimiPage', () => {
  it('veli · deneme · aylık: hero + durum pili + plan kartı (₺124/ay) + iptal kartı', async () => {
    configureKiroApi({ mode: 'mock', mockData: mockWith({ durum: 'deneme', fatura: 'aylik' }) });
    render(<PlanYonetimiPage rol="veli" />);

    // Serif hero (kilit kopya DC birebir)
    expect(await screen.findByRole('heading', { level: 1, name: 'Planını yönet.' })).toBeInTheDocument();
    // Durum pili — deneme → amber, DC copy
    expect(screen.getByText('Premium · Deneme')).toBeInTheDocument();
    // Fiyat sunucudan (plan.fiyatAy=124) + birim
    expect(screen.getByText('₺124')).toBeInTheDocument();
    expect(screen.getByText('/ay')).toBeInTheDocument();
    // Plan chip
    expect(screen.getByText('Deneme sürüyor')).toBeInTheDocument();
    // Yenileme satırı (deneme → ilk ödeme, e-posta hatırlatma güvencesi)
    expect(screen.getByText(/İlk ödeme 30 Temmuz 2026/)).toBeInTheDocument();
    // Ödeme yöntemi (yalnız son4 · PCI) + kart değiştir → /odeme?rol=veli
    expect(screen.getByText(/4242/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Kartı değiştir' })).toHaveAttribute('href', '/odeme?rol=veli');
    // Fatura satırı (₺0, Ödendi) + makbuz
    expect(screen.getByText('23 Temmuz 2026')).toBeInTheDocument();
    expect(screen.getByText('₺0')).toBeInTheDocument();
    expect(screen.getByText('Ödendi')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Makbuz' })).toBeInTheDocument();
  });

  it('iptal düğmesi coral METİN (#C2452B), destructive-RED DEĞİL', async () => {
    configureKiroApi({ mode: 'mock', mockData: mockWith({ durum: 'deneme', fatura: 'aylik' }) });
    render(<PlanYonetimiPage rol="veli" />);
    const iptalBtn = await screen.findByRole('button', { name: 'Aboneliği iptal et' });
    // #C2452B = rgb(194, 69, 43) — coral METİN, alarm-kırmızısı değil
    expect(iptalBtn).toHaveStyle({ color: 'rgb(194, 69, 43)' });
  });

  it('veli · aktif · yıllık: durum pili yeşil + ₺924/yıl + "Sonraki yenileme" + %38 indirim', async () => {
    configureKiroApi({ mode: 'mock', mockData: mockWith({ durum: 'aktif', fatura: 'yillik' }) });
    render(<PlanYonetimiPage rol="veli" />);

    expect(await screen.findByText('Premium · Aktif')).toBeInTheDocument();
    expect(screen.getByText('₺924')).toBeInTheDocument();
    expect(screen.getByText('/yıl')).toBeInTheDocument();
    expect(screen.getByText('Aktif')).toBeInTheDocument(); // plan chip
    expect(screen.getByText(/Sonraki yenileme 30 Temmuz 2026/)).toBeInTheDocument();
    // İndirim = yeşil success semantiği (metin), istemci fiyat üretmez → server indirimYuzde
    expect(screen.getByText(/yıllıkta %38 avantaj/)).toBeInTheDocument();
  });

  it('iptal akışı: "Aboneliği iptal et" → amber bant + "Geri aç"; iptal kartı gizlenir; geri aç geri getirir', async () => {
    configureKiroApi({ mode: 'mock', mockData: mockWith({ durum: 'deneme', fatura: 'aylik' }) });
    render(<PlanYonetimiPage rol="veli" />);

    fireEvent.click(await screen.findByRole('button', { name: 'Aboneliği iptal et' }));

    // Bant (role=status) + durum pili İptal + Geri aç
    expect(await screen.findByText('Deneme iptal edildi — ücret alınmadı.')).toBeInTheDocument();
    expect(screen.getByText('Premium · İptal edildi')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Geri aç' })).toBeInTheDocument();
    // İptal kartı gizli (iptalEdilebilir=false)
    expect(screen.queryByRole('button', { name: 'Aboneliği iptal et' })).not.toBeInTheDocument();

    // Geri aç → deneme durumuna döner, bant kaybolur
    fireEvent.click(screen.getByRole('button', { name: 'Geri aç' }));
    expect(await screen.findByRole('button', { name: 'Aboneliği iptal et' })).toBeInTheDocument();
    expect(screen.queryByText('Deneme iptal edildi — ücret alınmadı.')).not.toBeInTheDocument();
  });

  it('geri aç: SUNUCU-OTORİTE — post sonrası getAbonelikYonetim refetch; durum sunucudan (istemci türetmez)', async () => {
    configureKiroApi({ mode: 'mock', mockData: mockWith({ durum: 'deneme', fatura: 'aylik' }) });
    render(<PlanYonetimiPage rol="veli" />);

    fireEvent.click(await screen.findByRole('button', { name: 'Aboneliği iptal et' }));
    expect(await screen.findByText('Premium · İptal edildi')).toBeInTheDocument();

    // Sunucu artık 'aktif' döndürüyor (deneme→ücretli dönüşüm). Geri-aç refetch bunu
    // yansıtmalı; istemci-türetme 'deneme' sonucunu ÜRETMEZ (sunucu-otorite).
    configureKiroApi({ mode: 'mock', mockData: mockWith({ durum: 'aktif', fatura: 'aylik' }) });
    fireEvent.click(screen.getByRole('button', { name: 'Geri aç' }));

    expect(await screen.findByText('Premium · Aktif')).toBeInTheDocument();
    expect(screen.queryByText('Premium · Deneme')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Aboneliği iptal et' })).toBeInTheDocument();
  });

  it('ÖĞRENCİ FİYAT GİZLİ: VeliYonlendirmeKarti gösterilir; fiyat/plan/iptal YOK (KVKK)', async () => {
    render(<PlanYonetimiPage rol="ogrenci" />);
    expect(await screen.findByText('Aboneliğini velin yönetir')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Veli hesabına git' })).toHaveAttribute('href', '/veli');
    // Fiyat / plan / iptal ASLA
    expect(screen.queryByText(/₺|124|924/)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Aboneliği iptal et' })).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Planını yönet.' })).not.toBeInTheDocument();
    // MarkaBar YOK (salt-kart) → "KIRO2 Premium" tier adı öğrenciye sızmaz (KVKK)
    expect(screen.queryByText(/Premium/)).not.toBeInTheDocument();
  });

  it('fatura yok: kanonik soft-empty ("Henüz fatura yok — deneme sürüyor…"); makbuz/Ödendi yok', async () => {
    configureKiroApi({ mode: 'mock', mockData: mockWith({ durum: 'deneme', fatura: 'aylik', faturalar: [] }) });
    render(<PlanYonetimiPage rol="veli" />);
    expect(await screen.findByText(/Henüz fatura yok — deneme sürüyor, bugün ödeme alınmadı/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Makbuz' })).not.toBeInTheDocument();
    expect(screen.queryByText('Ödendi')).not.toBeInTheDocument();
  });

  it('yükleme: veri gelmeden aria-busy iskelet gösterir', async () => {
    configureKiroApi({ mode: 'mock', mockData: mockWith({ durum: 'deneme', fatura: 'aylik' }) });
    render(<PlanYonetimiPage rol="veli" />);
    expect(screen.getByLabelText('Plan yükleniyor')).toHaveAttribute('aria-busy', 'true');
    expect(await screen.findByText('Premium · Deneme')).toBeInTheDocument();
  });

  it('getAbonelikYonetim reddi: ErrorState (sakin/amber) + "Yeniden dene" veriyi getirir', async () => {
    configureKiroApi({ mode: 'mock', mockData: undefined });
    render(<PlanYonetimiPage rol="veli" />);
    expect(await screen.findByText('Plan bilgisi şu an gelmedi.')).toBeInTheDocument();

    configureKiroApi({ mode: 'mock', mockData: mockWith({ durum: 'deneme', fatura: 'aylik' }) });
    fireEvent.click(screen.getByRole('button', { name: 'Yeniden dene' }));
    expect(await screen.findByText('Premium · Deneme')).toBeInTheDocument();
    expect(screen.queryByText('Plan bilgisi şu an gelmedi.')).not.toBeInTheDocument();
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
      configureKiroApi({ mode: 'mock', mockData: mockWith({ durum: 'deneme', fatura: 'aylik' }) });
      render(<PlanYonetimiPage rol="veli" />);
      expect(await screen.findByRole('heading', { level: 1, name: 'Planını yönet.' })).toBeInTheDocument();
      expect(screen.getByText('Fatura geçmişi')).toBeInTheDocument();
    } finally {
      window.matchMedia = gercek;
    }
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    configureKiroApi({ mode: 'mock', mockData: mockWith({ durum: 'deneme', fatura: 'aylik' }) });
    const { container } = render(<PlanYonetimiPage rol="veli" />);
    await screen.findByText('Premium · Deneme');
    expect(await axe(container)).toHaveNoViolations();
  }, 40000);
});
