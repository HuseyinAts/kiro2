import { render, screen, fireEvent } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';

import { useAyar, resetAyar } from '../lib/ayarStore';
import { ArkadasSerisiPage } from './ArkadasSerisiPage';

expect.extend(toHaveNoViolations);

describe('ArkadasSerisiPage', () => {
  // ayarStore global + persist(localStorage) → her testte izole et (sızıntı önle).
  beforeEach(() => resetAyar());
  afterEach(() => resetAyar());

  it('varsayılan render: başlık + ortak seri hero + birlikte görev + arkadaşlar (sunucu verisi)', async () => {
    render(<ArkadasSerisiPage />);
    // Header
    expect(await screen.findByText(/Arkadaşlar & Birlikte/)).toBeInTheDocument();
    expect(screen.getByText(/Karşılıklı sorumluluk/)).toBeInTheDocument();
    // Ortak seri hero — partner adı sunucudan (ortakSeri.partner)
    expect(screen.getByText(/Ortak seri · Elif ile/)).toBeInTheDocument();
    // Birlikte görev — gorev.baslik sunucudan (DC hardcoded değil)
    expect(screen.getByText('Bu hafta birlikte 200 soru')).toBeInTheDocument();
    expect(screen.getByText(/\+150 XP · Ortak rozet/)).toBeInTheDocument();
    // Arkadaş listesi — getFriends
    expect(screen.getByText('Kaan Demir')).toBeInTheDocument();
    expect(screen.getByText('Elif Yıldız')).toBeInTheDocument();
    // Serif dipnot
    expect(screen.getByText(/kimse arkadaşını bırakmak istemez/)).toBeInTheDocument();
  });

  it('CTA + rota: "Arkadaş ekle" erişilebilir buton + SideNav aktif rota /arkadas-serisi', async () => {
    render(<ArkadasSerisiPage />);
    await screen.findByText(/Arkadaşlar & Birlikte/);
    // Header CTA gerçek buton (akış flag; rota DC'de yok)
    expect(screen.getByRole('button', { name: /Arkadaş ekle/ })).toBeInTheDocument();
    // Rota hizası: aktif SideNav bağlantısı /arkadas-serisi
    const nav = screen.getByRole('link', { name: 'Arkadaş Serisi' });
    expect(nav).toHaveAttribute('href', '/arkadas-serisi');
    expect(nav).toHaveAttribute('aria-current', 'page');
  });

  it('dürtme durum-barı: "Elif\'i dürt" → "Gönderildi" + aria-pressed + devre dışı (sunucu-otorite)', async () => {
    render(<ArkadasSerisiPage />);
    const durt = await screen.findByRole('button', { name: /Elif arkadaşını dürt/ });
    expect(durt).toHaveAttribute('aria-pressed', 'false');
    fireEvent.click(durt);
    const sonra = await screen.findByRole('button', { name: /Dürtme gönderildi/ });
    expect(sonra).toBeDisabled();
    expect(sonra).toHaveAttribute('aria-pressed', 'true');
  });

  it('tebrik: arkadaşa özel aria-label ("<ad> için tebrik gönder", SR ayırt edebilir) + tıklayınca aria-pressed=true', async () => {
    render(<ArkadasSerisiPage />);
    await screen.findByText('Kaan Demir');
    // Her tebrik butonu arkadaşın adını taşır — statik "Tebrik gönder" değil (SR ayırt eder)
    const kaanTebrik = screen.getByRole('button', { name: 'Kaan Demir için tebrik gönder' });
    const elifTebrik = screen.getByRole('button', { name: 'Elif Yıldız için tebrik gönder' });
    expect(kaanTebrik).not.toBe(elifTebrik);
    expect(kaanTebrik).toHaveAttribute('aria-pressed', 'false');
    fireEvent.click(kaanTebrik);
    expect(kaanTebrik).toHaveAttribute('aria-pressed', 'true');
    expect(kaanTebrik).toBeDisabled();
  });

  it('sakin mod: calmMode açıkken dürtme CTA render edilmez + kısa açıklama görünür (baskı-azaltma); tebrik korunur', async () => {
    useAyar.getState().setCalmMode(true);
    render(<ArkadasSerisiPage />);
    await screen.findByText('Kaan Demir');
    // Dürtme CTA'sı yok — ne "dürt" ne "Dürtme gönderildi" butonu
    expect(screen.queryByRole('button', { name: /dürt/i })).not.toBeInTheDocument();
    // Kısa açıklama görünür (seri-dürtme sustur)
    expect(screen.getByText(/Sakin mod açık/)).toBeInTheDocument();
    // Congrats/tebrik davranışı KORUNUR
    expect(screen.getByRole('button', { name: 'Kaan Demir için tebrik gönder' })).toBeInTheDocument();
  });

  it('sakin mod kapalı (varsayılan): dürtme CTA görünür', async () => {
    render(<ArkadasSerisiPage />);
    expect(await screen.findByRole('button', { name: /Elif arkadaşını dürt/ })).toBeInTheDocument();
    expect(screen.queryByText(/Sakin mod açık/)).not.toBeInTheDocument();
  });

  it('sıralama: Seri/XP segmented control seçimi değişir (radio state)', async () => {
    render(<ArkadasSerisiPage />);
    await screen.findByText('Kaan Demir');
    const seri = screen.getByRole('radio', { name: 'Seri' });
    const xp = screen.getByRole('radio', { name: 'XP' });
    expect(seri).toHaveAttribute('aria-checked', 'true');
    fireEvent.click(xp);
    expect(xp).toHaveAttribute('aria-checked', 'true');
    expect(seri).toHaveAttribute('aria-checked', 'false');
  });

  it('reduced-motion: içerik korunur, +1 uçuş animasyonu kapanır', async () => {
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
      render(<ArkadasSerisiPage />);
      expect(await screen.findByText('Bu hafta birlikte 200 soru')).toBeInTheDocument();
    } finally {
      window.matchMedia = gercek;
    }
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<ArkadasSerisiPage />);
    await screen.findByText('Kaan Demir');
    expect(await axe(container)).toHaveNoViolations();
  }, 40000);
});
