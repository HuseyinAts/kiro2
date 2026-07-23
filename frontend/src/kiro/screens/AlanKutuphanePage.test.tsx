import { render, screen, fireEvent } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect, afterEach } from 'vitest';

import { configureKiroApi } from '../api/api-client';
import type { MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';
import { AlanKutuphanePage } from './AlanKutuphanePage';

expect.extend(toHaveNoViolations);

// Ekran modülü yüklenirken mock moda konfigüre olur; hata/yükleme dallarını
// test etmek için live'a çevirdiğimizde her testten sonra mock'a geri dön.
function mockModunaDon(): void {
  configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });
}
afterEach(mockModunaDon);

describe('AlanKutuphanePage', () => {
  it('render: başlık + 3 alan + katalog dersleri', async () => {
    render(<AlanKutuphanePage />);
    expect(screen.getByRole('heading', { level: 1, name: 'Alan Kütüphanesi' })).toBeInTheDocument();
    // 3 alan başlığı (heading — subtitle içindeki "Sayısal" ile karışmaz)
    expect(await screen.findByRole('heading', { name: 'Sayısal' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Eşit Ağırlık' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Sözel' })).toBeInTheDocument();
    // Katalog başlığı + 4 ders kartı
    expect(screen.getByRole('heading', { name: /Tüm dersler/ })).toBeInTheDocument();
    expect(screen.getByText('Matematik')).toBeInTheDocument();
    expect(screen.getByText('Fizik')).toBeInTheDocument();
    expect(screen.getByText('Kimya')).toBeInTheDocument();
    expect(screen.getByText('Biyoloji')).toBeInTheDocument();
  });

  it('geri-oku: aria-label + /panel href', async () => {
    render(<AlanKutuphanePage />);
    await screen.findByRole('heading', { name: 'Sayısal' });
    expect(screen.getByRole('link', { name: 'Panele dön' })).toHaveAttribute('href', '/panel');
  });

  it('"Senin alanın" rozeti yalnız seninKey (Sayısal) kartında', async () => {
    render(<AlanKutuphanePage />);
    await screen.findByRole('heading', { name: 'Sayısal' });
    expect(screen.getAllByText('Senin alanın')).toHaveLength(1);
  });

  it('akordeon aç: konular + coral "örnek soru havuzda" şeridi (soruSayisi>0)', async () => {
    render(<AlanKutuphanePage />);
    const matToggle = await screen.findByRole('button', { name: /Matematik/ });
    expect(matToggle).toHaveAttribute('aria-expanded', 'false');
    fireEvent.click(matToggle);
    expect(matToggle).toHaveAttribute('aria-expanded', 'true');
    // numaralı konu göründü
    expect(await screen.findByText('Fonksiyonlar')).toBeInTheDocument();
    // coral şerit — soruSayisi=340 > 0
    expect(screen.getByText(/340 örnek soru çözümüyle havuzda/)).toBeInTheDocument();
  });

  it('TEK-AÇILIR: Fizik açılınca Matematik kapanır', async () => {
    render(<AlanKutuphanePage />);
    const matToggle = await screen.findByRole('button', { name: /Matematik/ });
    fireEvent.click(matToggle);
    expect(await screen.findByText('Fonksiyonlar')).toBeInTheDocument();
    const fizToggle = screen.getByRole('button', { name: /Fizik/ });
    fireEvent.click(fizToggle);
    // Matematik konusu artık DOM'da değil; Fizik konusu göründü
    expect(screen.queryByText('Fonksiyonlar')).not.toBeInTheDocument();
    expect(screen.getByText('Newton Yasaları')).toBeInTheDocument();
  });

  it('soruSayisi=0: Kimya açılınca coral şerit GİZLİ', async () => {
    render(<AlanKutuphanePage />);
    const kimToggle = await screen.findByRole('button', { name: /Kimya/ });
    fireEvent.click(kimToggle);
    expect(await screen.findByText('Gazlar')).toBeInTheDocument();
    expect(screen.queryByText(/örnek soru çözümüyle havuzda/)).not.toBeInTheDocument();
  });

  it('reduced-motion: içerik korunur (bu ekran hareketsiz)', async () => {
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
      render(<AlanKutuphanePage />);
      expect(await screen.findByRole('heading', { name: 'Sayısal' })).toBeInTheDocument();
    } finally {
      window.matchMedia = gercek;
    }
  });

  it('axe: erişilebilirlik ihlali yok (açık akordeon dahil)', async () => {
    const { container } = render(<AlanKutuphanePage />);
    const matToggle = await screen.findByRole('button', { name: /Matematik/ });
    fireEvent.click(matToggle);
    await screen.findByText('Fonksiyonlar');
    expect(await axe(container)).toHaveNoViolations();
  }, 40000);

  it('getAlanKutuphane reddi → ErrorState; retry ile içerik döner', async () => {
    // baseUrl'siz live → getAlanKutuphane() reddeder (KiroApi: live modda baseUrl zorunlu).
    configureKiroApi({ mode: 'live' });
    render(<AlanKutuphanePage />);
    // Sakin hata durumu — ekranın serif başlığı + retry butonu (Tekrar dene).
    expect(await screen.findByText('Alan kütüphanesi şu an gelmedi.')).toBeInTheDocument();
    const retry = screen.getByRole('button', { name: 'Tekrar dene' });
    // Retry öncesi mock'a dön → yeniden dene başarılı olur ve içerik yüklenir.
    mockModunaDon();
    fireEvent.click(retry);
    expect(await screen.findByRole('heading', { name: 'Sayısal' })).toBeInTheDocument();
  });

  it('yükleme: veri beklerken aria-busy iskelet dalı', () => {
    // Hiç çözülmeyen fetch → getAlanKutuphane askıda kalır → yükleme dalı korunur.
    const bekleyen = (() => new Promise<Response>(() => undefined)) as unknown as typeof fetch;
    configureKiroApi({ mode: 'live', baseUrl: 'http://test', fetchImpl: bekleyen });
    render(<AlanKutuphanePage />);
    expect(screen.getByLabelText('Alan kütüphanesi yükleniyor')).toHaveAttribute('aria-busy', 'true');
  });
});
