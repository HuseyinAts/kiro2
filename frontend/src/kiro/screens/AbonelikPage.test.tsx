import { render, screen, fireEvent } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect, vi } from 'vitest';

import * as apiClient from '../api/api-client';
import { AbonelikPage } from './AbonelikPage';

expect.extend(toHaveNoViolations);

// NOT: vi.restoreAllMocks() KULLANMA — setup.ts global matchMedia vi.fn'ini bozar.
// Spy'lar mockRejectedValueOnce ile tek çağrıdan sonra kendiliğinden geri döner.

describe('AbonelikPage · veli (fiyat GÖRÜNÜR)', () => {
  it('kilit kopya "Şu an: Ücretsiz" + kişisel serif hero render eder', async () => {
    render(<AbonelikPage rol="veli" />);
    // Serif hero (getMe persona.ad = "Hüseyin Ateş" → ilk ad kişiselleştirir)
    expect(await screen.findByText('Hüseyin için tam erişim')).toBeInTheDocument();
    // Kilit kopya (DC birebir) — mevcut tier pili
    expect(screen.getByText('Şu an: Ücretsiz')).toBeInTheDocument();
  });

  it('ROI kanıt şeridi sunucu değerlerini gösterir (+8,5 · %86 · 12)', async () => {
    render(<AbonelikPage rol="veli" />);
    await screen.findByText('Hüseyin için tam erişim');
    expect(screen.getByText('+8,5')).toBeInTheDocument();
    expect(screen.getByText('%86')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
  });

  it('2 plan (Ücretsiz mevcut + Premium "En çok seçilen"); yıllık ₺924', async () => {
    render(<AbonelikPage rol="veli" />);
    await screen.findByText('Hüseyin için tam erişim');
    expect(screen.getByText('En çok seçilen')).toBeInTheDocument();
    // Ücretsiz plan mevcut → statik footer (CTA değil)
    expect(screen.getByText('Mevcut planın')).toBeInTheDocument();
    // Yıllık varsayılan → premium başlık fiyatı ₺924 (server figürü; istemci bölme yapmaz)
    expect(screen.getByText('₺924')).toBeInTheDocument();
    expect(screen.getByText('₺0')).toBeInTheDocument();
  });

  it('Premium CTA "gün ücretsiz başla" → /odeme?rol=veli&fatura=yillik (KANON coral)', async () => {
    render(<AbonelikPage rol="veli" />);
    await screen.findByText('Hüseyin için tam erişim');
    const cta = screen.getByRole('link', { name: /gün ücretsiz başla/ });
    // Veli varyantı (DC:225): çocuk kişiselleştirmesi + "başlat" (SİZ dili)
    expect(cta).toHaveTextContent('Hüseyin için 7 gün ücretsiz başlat');
    expect(cta).toHaveAttribute('href', '/odeme?rol=veli&fatura=yillik');
  });

  it('fatura toggle Aylık → fiyat ₺124 + CTA href fatura=aylik güncellenir', async () => {
    render(<AbonelikPage rol="veli" />);
    await screen.findByText('Hüseyin için tam erişim');
    fireEvent.click(screen.getByRole('radio', { name: 'Aylık' }));
    expect(await screen.findByText('₺124')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /gün ücretsiz başla/ })).toHaveAttribute(
      'href',
      '/odeme?rol=veli&fatura=aylik',
    );
  });

  it('güven çipleri: soru bankası + motorlar + kaygı-duyarlı tasarım', async () => {
    render(<AbonelikPage rol="veli" />);
    await screen.findByText('Hüseyin için tam erişim');
    expect(screen.getByText('187.835+ soru')).toBeInTheDocument();
    expect(screen.getByText('CAT/IRT · FSRS · BKT')).toBeInTheDocument();
    expect(screen.getByText('Kaygı-duyarlı tasarım')).toBeInTheDocument();
  });

  it('KANON: veli dili SİZ; yasak absence-dili yok', async () => {
    render(<AbonelikPage rol="veli" />);
    await screen.findByText('Hüseyin için tam erişim');
    // SİZ dili (dipnot)
    expect(screen.getByText(/fiyat baskısı görmez/)).toBeInTheDocument();
    expect(screen.getByText(/beğenmezseniz tek dokunuşla iptal/)).toBeInTheDocument();
    expect(screen.queryByText(/\beksik\b/i)).not.toBeInTheDocument();
  });
});

describe('AbonelikPage · öğrenci (FİYAT GİZLİ · KVKK)', () => {
  it('VeliYonlendirmeKarti render eder; fiyat/plan/CTA GÖSTERMEZ', async () => {
    render(<AbonelikPage rol="ogrenci" />);
    // Paylaşılan yönlendirme kartı (SEN dili)
    expect(await screen.findByText('Aboneliğini velin yönetir')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Veli hesabına git' })).toHaveAttribute('href', '/veli');
    // Fiyat/plan/tier pili GÖRÜNMEZ
    expect(screen.queryByText(/₺/)).not.toBeInTheDocument();
    expect(screen.queryByText('En çok seçilen')).not.toBeInTheDocument();
    expect(screen.queryByText(/Şu an:/)).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /gün ücretsiz başla/ })).not.toBeInTheDocument();
  });
});

describe('AbonelikPage · durumlar', () => {
  it('yükleme dalı: veri gelmeden aria-busy iskeleti gösterir', async () => {
    render(<AbonelikPage rol="veli" />);
    const busy = screen.getByLabelText('Abonelik seçenekleri yükleniyor');
    expect(busy).toHaveAttribute('aria-busy', 'true');
    // Akışı boşalt (act uyarısı yok)
    await screen.findByText('Hüseyin için tam erişim');
    expect(screen.queryByLabelText('Abonelik seçenekleri yükleniyor')).not.toBeInTheDocument();
  });

  it('getAbonelik reddi → sakin ErrorState; retry sonrası plan döner', async () => {
    const spy = vi.spyOn(apiClient, 'getAbonelik').mockRejectedValueOnce(new Error('baglanti'));
    render(<AbonelikPage rol="veli" />);
    expect(await screen.findByText('Abonelik seçenekleri şu an gelmedi.')).toBeInTheDocument();
    expect(screen.queryByText('En çok seçilen')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Tekrar dene' }));
    expect(await screen.findByText('Hüseyin için tam erişim')).toBeInTheDocument();
    expect(screen.queryByText('Abonelik seçenekleri şu an gelmedi.')).not.toBeInTheDocument();
    expect(spy).toHaveBeenCalled();
  });

  it('getMe reddi ekranı düşürmez; hero generic "Çocuğunuz"e düşer', async () => {
    vi.spyOn(apiClient, 'getMe').mockRejectedValueOnce(new Error('persona'));
    render(<AbonelikPage rol="veli" />);
    expect(await screen.findByText('Çocuğunuz için tam erişim')).toBeInTheDocument();
    // Birincil veri geldi → plan ızgarası render olur
    expect(screen.getByText('En çok seçilen')).toBeInTheDocument();
  });

  it('axe: erişilebilirlik ihlali yok (veli)', async () => {
    const { container } = render(<AbonelikPage rol="veli" />);
    await screen.findByText('Hüseyin için tam erişim');
    expect(await axe(container)).toHaveNoViolations();
  }, 20000);
});
