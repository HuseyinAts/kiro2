import { render, screen, fireEvent } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import type { ThreeDSDurum } from '../types';
import { OdemePage } from './OdemePage';

expect.extend(toHaveNoViolations);

// 3DS preview seam'leri (sunucu-otorite yanıtını enjekte eder — istemci ÜRETMEZ).
const NEVER = (): Promise<ThreeDSDurum> => new Promise<ThreeDSDurum>(() => undefined);
const RET = (): Promise<ThreeDSDurum> => Promise.resolve('reddedildi');
const OK = (): Promise<ThreeDSDurum> => Promise.resolve('onaylandi');

/** Geçerli kart alanlarını doldur (PCI: UI-only). */
function kartDoldur(): void {
  fireEvent.change(screen.getByLabelText('Kart üzerindeki isim'), { target: { value: 'Ayşe Ateş' } });
  fireEvent.change(screen.getByLabelText('Kart numarası'), { target: { value: '4242424242424242' } });
  fireEvent.change(screen.getByLabelText('Son kullanma'), { target: { value: '1228' } });
  fireEvent.change(screen.getByLabelText('Güvenlik kodu'), { target: { value: '123' } });
}

describe('OdemePage', () => {
  it('form: veli SİZ başlık + 4 kart alanı + "Bugün ödeme alınmaz" (SAF-MOCK, PCI UI-only)', async () => {
    render(<OdemePage baslangicFazi="form" fatura="aylik" />);
    expect(await screen.findByText('Denemeyi birlikte başlatalım.')).toBeInTheDocument();
    // Veli dili (SİZ) + öğrenci fiyat baskısı görmez
    expect(screen.getByText(/veli hesabınızda tutulur/)).toBeInTheDocument();
    expect(screen.getByLabelText('Kart üzerindeki isim')).toBeInTheDocument();
    expect(screen.getByLabelText('Kart numarası')).toBeInTheDocument();
    expect(screen.getByLabelText('Son kullanma')).toBeInTheDocument();
    expect(screen.getByLabelText('Güvenlik kodu')).toBeInTheDocument();
    expect(screen.getByText(/Bugün ödeme alınmaz/)).toBeInTheDocument();
  });

  it('özet: SUNUCUDAN plan + 7 gün ücretsiz + tutar (₺124/ay, tabular)', async () => {
    render(<OdemePage baslangicFazi="form" fatura="aylik" />);
    // Skeleton → yüklenince özet satırları (getOdemeOzeti — istemci fiyat hesaplamaz)
    expect(await screen.findByText('₺124/ay')).toBeInTheDocument();
    expect(screen.getByText('Premium · Aylık')).toBeInTheDocument();
    expect(screen.getByText('7 gün ücretsiz')).toBeInTheDocument();
  });

  it('özet · yıllık: ₺924/yıl (fatura dönemi sunucu tutarına yansır)', async () => {
    render(<OdemePage baslangicFazi="form" fatura="yillik" />);
    expect(await screen.findByText('₺924/yıl')).toBeInTheDocument();
    expect(screen.getByText('Premium · Yıllık')).toBeInTheDocument();
  });

  it('form doğrulama: boş → amber isim ipucu (aria-live); 3ds’e GEÇMEZ', async () => {
    render(<OdemePage baslangicFazi="form" fatura="aylik" />);
    await screen.findByText('Denemeyi birlikte başlatalım.');
    fireEvent.click(screen.getByRole('button', { name: '7 gün ücretsiz denemeyi başlat' }));
    expect(await screen.findByText('Kart üzerindeki ismi de alalım.')).toBeInTheDocument();
    expect(screen.queryByText('Bankanız doğrulama istiyor.')).not.toBeInTheDocument();
  });

  it('kart alanları auto-format: numara 4’lü gruplanır, SKT "AA / YY"', async () => {
    render(<OdemePage baslangicFazi="form" fatura="aylik" />);
    await screen.findByText('Denemeyi birlikte başlatalım.');
    const numara = screen.getByLabelText('Kart numarası') as HTMLInputElement;
    fireEvent.change(numara, { target: { value: '4242424242424242' } });
    expect(numara.value).toBe('4242 4242 4242 4242');
    const skt = screen.getByLabelText('Son kullanma') as HTMLInputElement;
    fireEvent.change(skt, { target: { value: '1228' } });
    expect(skt.value).toBe('12 / 28');
  });

  it('mutlu yol: geçerli form → 3DS spinner → getOdeme3dsSonuc onaylandı → "Deneme başladı."', async () => {
    render(<OdemePage baslangicFazi="form" fatura="aylik" />);
    await screen.findByText('Denemeyi birlikte başlatalım.');
    kartDoldur();
    fireEvent.click(screen.getByRole('button', { name: '7 gün ücretsiz denemeyi başlat' }));
    // 3DS fazı (istemci 3DS sonucu ÜRETMEZ — getOdeme3dsSonuc döner)
    expect(await screen.findByText('Bankanız doğrulama istiyor.')).toBeInTheDocument();
    // Tamam (mock getOdeme3dsSonuc 400ms → 'onaylandi')
    expect(await screen.findByText('Deneme başladı.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Aboneliği yönet/ })).toHaveAttribute('href', '/abonelik/yonetim');
  });

  it('banka-red: getOdeme3dsSonuc reddedildi → forma dön + AMBER decline (alarm-kırmızı YOK)', async () => {
    render(<OdemePage baslangicFazi="form" fatura="aylik" resolve3ds={RET} />);
    await screen.findByText('Denemeyi birlikte başlatalım.');
    kartDoldur();
    fireEvent.click(screen.getByRole('button', { name: '7 gün ücretsiz denemeyi başlat' }));
    expect(await screen.findByText(/Kart bu sefer onaylanmadı/)).toBeInTheDocument();
    // Forma dönüldü — kart alanı hâlâ mevcut
    expect(screen.getByLabelText('Kart numarası')).toBeInTheDocument();
  });

  it('3DS fazı: spinner + bespoke 3-adım stepper (statik — resolve3ds bekliyor)', async () => {
    render(<OdemePage baslangicFazi="3ds" resolve3ds={NEVER} />);
    expect(await screen.findByText('Bankanız doğrulama istiyor.')).toBeInTheDocument();
    expect(screen.getByText('Kart bilgisi alındı')).toBeInTheDocument();
    expect(screen.getByText('Banka onayı')).toBeInTheDocument();
    expect(screen.getByText('Deneme başlar')).toBeInTheDocument();
    // Deneme henüz başlamadı (poll bekliyor)
    expect(screen.queryByText('Deneme başladı.')).not.toBeInTheDocument();
  });

  it('tamam fazı: "Deneme başladı." + Plan Yönetimi CTA (/abonelik/yonetim)', async () => {
    render(<OdemePage baslangicFazi="tamam" />);
    expect(await screen.findByText('Deneme başladı.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Aboneliği yönet/ })).toHaveAttribute('href', '/abonelik/yonetim');
    expect(screen.getByRole('link', { name: 'Veli paneline dön' })).toHaveAttribute('href', '/veli');
  });

  it('reduced-motion: spinner statik, içerik korunur (paper — hareket kapanır)', async () => {
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
      render(<OdemePage baslangicFazi="3ds" resolve3ds={NEVER} />);
      expect(await screen.findByText('Bankanız doğrulama istiyor.')).toBeInTheDocument();
    } finally {
      window.matchMedia = gercek;
    }
  });

  it('onay seam (DI): resolve3ds deterministik onaylandı → "Deneme başladı."', async () => {
    render(<OdemePage baslangicFazi="form" fatura="aylik" resolve3ds={OK} />);
    await screen.findByText('Denemeyi birlikte başlatalım.');
    kartDoldur();
    fireEvent.click(screen.getByRole('button', { name: '7 gün ücretsiz denemeyi başlat' }));
    expect(await screen.findByText('Deneme başladı.')).toBeInTheDocument();
  });

  it('rol=ogrenci guard: fiyat/kart/özet YOK → paylaşılan VeliYonlendirmeKarti (KVKK)', async () => {
    render(<OdemePage rol="ogrenci" fatura="aylik" />);
    // Öğrenci: yalnız veli yönlendirme kartı; satın-alma yüzeyi gizli
    expect(await screen.findByText('Aboneliğini velin yönetir')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Veli hesabına git' })).toHaveAttribute('href', '/veli');
    // Fiyat / kart alanı / form başlığı görünmez
    expect(screen.queryByText('₺124/ay')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Kart numarası')).not.toBeInTheDocument();
    expect(screen.queryByText('Denemeyi birlikte başlatalım.')).not.toBeInTheDocument();
  });

  it('axe: erişilebilirlik ihlali yok (form + yüklenmiş özet)', async () => {
    const { container } = render(<OdemePage baslangicFazi="form" fatura="aylik" />);
    await screen.findByText('₺124/ay');
    expect(await axe(container)).toHaveNoViolations();
  }, 40000);

  it('axe · 3DS fazı: spinner + stepper (role=list) ihlal yok', async () => {
    const { container } = render(<OdemePage baslangicFazi="3ds" resolve3ds={NEVER} />);
    await screen.findByText('Bankanız doğrulama istiyor.');
    expect(await axe(container)).toHaveNoViolations();
  }, 40000);

  it('axe · tamam fazı: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<OdemePage baslangicFazi="tamam" />);
    await screen.findByText('Deneme başladı.');
    expect(await axe(container)).toHaveNoViolations();
  }, 40000);

  it('axe · banka-red sonrası form: role="alert" decline + aria-invalid ihlal yok', async () => {
    const { container } = render(<OdemePage baslangicFazi="form" fatura="aylik" resolve3ds={RET} />);
    await screen.findByText('₺124/ay');
    kartDoldur();
    fireEvent.click(screen.getByRole('button', { name: '7 gün ücretsiz denemeyi başlat' }));
    await screen.findByText(/Kart bu sefer onaylanmadı/);
    expect(await axe(container)).toHaveNoViolations();
  }, 40000);

  it('rol=ogrenci guard: axe erişilebilirlik ihlali yok', async () => {
    const { container } = render(<OdemePage rol="ogrenci" fatura="aylik" />);
    await screen.findByText('Aboneliğini velin yönetir');
    expect(await axe(container)).toHaveNoViolations();
  }, 40000);
});
