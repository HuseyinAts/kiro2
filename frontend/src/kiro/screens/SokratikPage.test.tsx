import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect, afterEach } from 'vitest';

import { configureKiroApi } from '../api/api-client';
import type { MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';
import { SokratikPage } from './SokratikPage';

expect.extend(toHaveNoViolations);

const D = kiroData as unknown as MockData;

// Ekran modülü yüklenirken mock moda konfigüre olur; hata/boş/yükleme dallarını
// live'a çevirdiğimizde her testten sonra mock'a geri dön.
function mockModunaDon(): void {
  configureKiroApi({ mode: 'mock', mockData: D });
}
afterEach(mockModunaDon);

// matchMedia mock: `esles(query)` true dönerse o media-query eşleşir (railGizli/navDar
// kontrolü). jsdom matchMedia sağlamaz → sonrası restore ile izolasyon (resetAyar).
function mockMatchMedia(esles: (q: string) => boolean): () => void {
  const gercek = window.matchMedia;
  window.matchMedia = ((q: string) => ({
    matches: esles(q),
    media: q,
    onchange: null,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    addListener: () => undefined,
    removeListener: () => undefined,
    dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia;
  return () => { window.matchMedia = gercek; };
}

describe('SokratikPage', () => {
  it('topbar: Sokratik asistan başlığı + "cevabı vermez" mod pili', async () => {
    mockModunaDon();
    render(<SokratikPage />);
    expect(screen.getByText('KIRO Sokratik Asistan')).toBeInTheDocument();
    expect(screen.getByText('Qwen3-8B · Türkçe öğretmen modeli')).toBeInTheDocument();
    expect(screen.getByText('Sokratik mod · cevabı vermez')).toBeInTheDocument();
    // Açılış AI karşılaması (sunucudan — sokratik.acilis) yüklenir
    expect(await screen.findByText(D.sokratik.acilis)).toBeInTheDocument();
  });

  it('açılış: "cevabı vermez" bildirimi + sağ ray başlıkları', async () => {
    mockModunaDon();
    render(<SokratikPage />);
    await screen.findByText(D.sokratik.acilis);
    expect(screen.getByText('Bu mod cevabı vermez — birlikte düşünür. Öğrenme etkisi korunur.')).toBeInTheDocument();
    expect(screen.getByText('İpucu merdiveni')).toBeInTheDocument();
    expect(screen.getByText('Sokratik ilerleme')).toBeInTheDocument();
    expect(screen.getByText('ÜZERİNDE ÇALIŞILAN')).toBeInTheDocument();
  });

  it('mesaj gönder: kullanıcı balonu + streaming yönlendirici yanıt (cevabı VERMEZ)', async () => {
    mockModunaDon();
    render(<SokratikPage />);
    await screen.findByText(D.sokratik.acilis);

    const input = screen.getByLabelText('Düşünceni yaz');
    fireEvent.change(input, { target: { value: 'Türev nedir?' } });
    fireEvent.click(screen.getByRole('button', { name: 'Gönder' }));

    // Kullanıcı balonu görünür (+ sağ ray "üzerinde çalışılan soru" da öğrencinin
    // ilk mesajını gösterir → iki eşleşme; sunucu-otorite: istemci soru uydurmaz).
    expect((await screen.findAllByText('Türev nedir?')).length).toBeGreaterThanOrEqual(1);

    // Streaming tamamlanınca yönlendirici yanıt (adimlar[0]) akar — SUNUCU-OTORİTE
    await screen.findByText(
      (content) => content.includes(D.sokratik.adimlar[0]!),
      {},
      { timeout: 6000 },
    );
    // Cevabı VERMEZ: DC'nin doğrudan sayısal sonucu ("93") ekranda YOK
    expect(screen.queryByText(/\b93\b/)).not.toBeInTheDocument();
  }, 15000);

  it('İpucu merdiveni sayacı + basamak etiketleri render edilir', async () => {
    mockModunaDon();
    render(<SokratikPage />);
    await screen.findByText(D.sokratik.acilis);
    expect(screen.getByText('Kavramı hatırlat')).toBeInTheDocument();
    expect(screen.getByText('Yöntemi yönlendir')).toBeInTheDocument();
    expect(screen.getByText('İlk adımı birlikte yap')).toBeInTheDocument();
    // Başlangıç sayacı 0 / 3
    expect(screen.getByText('0 / 3')).toBeInTheDocument();
  });

  it('railGizli (≤1023): "Çözümü göster (son çare)" + kompakt ilerleme ana kola taşınır', async () => {
    mockModunaDon();
    // 1023 eşleşir (sağ ray gizli), 760 eşleşmez (nav geniş kalır)
    const restore = mockMatchMedia((q) => q.includes('1023'));
    try {
      render(<SokratikPage />);
      await screen.findByText(D.sokratik.acilis);
      // Sağ ray unmount → rail başlıkları YOK
      expect(screen.queryByText('Sokratik ilerleme')).not.toBeInTheDocument();
      expect(screen.queryByText('İpucu merdiveni')).not.toBeInTheDocument();
      // "Çözümü göster (son çare)" affordance ana koldan erişilebilir (rail yerine)
      expect(screen.getByText('Çözümü göster (son çare)')).toBeInTheDocument();
      // Kompakt ilerleme sayacı ana kolda görünür (rail sayaçları unmount → tek eşleşme)
      expect(screen.getByText('0/3')).toBeInTheDocument();
    } finally {
      restore();
    }
  });

  it('Sokratik ilerleme: adım-metni (3 basamak) sayaç (/3) ile hizalı', async () => {
    mockModunaDon();
    render(<SokratikPage />);
    await screen.findByText(D.sokratik.acilis);
    // Adım-metni 3 basamağa indirildi → sayaç /3 ve İpucu merdiveni (3 basamak) ile örtüşür
    expect(screen.getByText('Adım: ilişki → yöntem → sonuç.')).toBeInTheDocument();
    // Eski 5-basamaklı metin ("değerler") artık YOK
    expect(screen.queryByText(/değerler/)).not.toBeInTheDocument();
    // Rail sayaçları /3 (İpucu merdiveni "0 / 3" + Sokratik ilerleme "0/3")
    expect(screen.getByText('0 / 3')).toBeInTheDocument();
    expect(screen.getByText('0/3')).toBeInTheDocument();
  });

  it('KANON: açılışta absence-dili yok', async () => {
    mockModunaDon();
    render(<SokratikPage />);
    await screen.findByText(D.sokratik.acilis);
    expect(screen.queryByText(/eksik/i)).not.toBeInTheDocument();
  });

  it('reduced-motion: içerik korunur (streaming motion RM-guard)', async () => {
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
      render(<SokratikPage />);
      expect(await screen.findByText(D.sokratik.acilis)).toBeInTheDocument();
    } finally {
      window.matchMedia = gercek;
    }
  });

  it('axe: erişilebilirlik ihlali yok (aria-live log + giriş dock)', async () => {
    mockModunaDon();
    const { container } = render(<SokratikPage />);
    await screen.findByText(D.sokratik.acilis);
    expect(await axe(container)).toHaveNoViolations();
  }, 40000);

  it('getSohbet reddi → ErrorState; retry ile içerik döner', async () => {
    // baseUrl'siz live → getSohbet() reddeder (live modda baseUrl zorunlu).
    configureKiroApi({ mode: 'live' });
    render(<SokratikPage />);
    expect(await screen.findByText('Sokratik oturum şu an açılmadı.')).toBeInTheDocument();
    const retry = screen.getByRole('button', { name: 'Tekrar dene' });
    mockModunaDon(); // retry öncesi mock'a dön → yeniden başarılı
    fireEvent.click(retry);
    expect(await screen.findByText(D.sokratik.acilis)).toBeInTheDocument();
  });

  it('boş oturum (mesajsız) → EmptyState açılış daveti', async () => {
    // live + boş sessions listesi → getSohbet mesajlar=[] → EmptyState.
    const bosFetch = (async () => ({ ok: true, status: 200, json: async () => [] })) as unknown as typeof fetch;
    configureKiroApi({ mode: 'live', baseUrl: 'http://test', fetchImpl: bosFetch });
    render(<SokratikPage />);
    expect(await screen.findByText('Birlikte başlayalım.')).toBeInTheDocument();
  });

  it('yükleme: veri beklerken aria-busy iskelet dalı', () => {
    const bekleyen = (() => new Promise<Response>(() => undefined)) as unknown as typeof fetch;
    configureKiroApi({ mode: 'live', baseUrl: 'http://test', fetchImpl: bekleyen });
    render(<SokratikPage />);
    expect(screen.getByLabelText('Sohbet yükleniyor')).toHaveAttribute('aria-busy', 'true');
  });
});
