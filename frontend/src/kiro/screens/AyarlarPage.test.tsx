import { render, screen, fireEvent, act } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { beforeEach, afterEach, describe, it, expect, vi } from 'vitest';

import * as apiClient from '../api/api-client';
import { AyarlarPage } from './AyarlarPage';
import { useAyar, resetAyar } from '../lib/ayarStore';

expect.extend(toHaveNoViolations);

// ayarStore global — persist sızıntısını önlemek için her testte reset.
beforeEach(() => resetAyar());
afterEach(() => resetAyar());

describe('AyarlarPage', () => {
  it('SideNav + "Ayarlar & Profil" başlığı render eder', () => {
    render(<AyarlarPage />);
    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(screen.getByText('Ayarlar & Profil')).toBeInTheDocument();
  });

  it('persona yüklenince profil-hero + abonelik banner gösterir', async () => {
    render(<AyarlarPage />);
    // persona.ad hem SideNav hem hero'da → en az 1
    expect((await screen.findAllByText('Hüseyin Ateş')).length).toBeGreaterThan(0);
    // GÖMÜLÜ DUSK abonelik banner (free → upsell) /abonelik'e köprü
    const banner = screen.getByRole('link', { name: /Premium/ });
    expect(banner).toHaveAttribute('href', '/abonelik');
    expect(screen.getByText('Sınava kadar tam erişim')).toBeInTheDocument();
  });

  it('5 bildirim anahtarı render eder ve toggle store\'a yazar + "Kaydedildi" flash', async () => {
    render(<AyarlarPage />);
    await screen.findAllByText('Hüseyin Ateş');

    const anahtarlar = [
      'FSRS tekrar hatırlatması',
      'Zayıf konu dokunuşu',
      'Seri hatırlatması',
      'Düello daveti',
      'Başarım bildirimi',
    ];
    for (const ad of anahtarlar) {
      expect(screen.getByRole('switch', { name: ad })).toBeInTheDocument();
    }

    // Varsayılan hepsi açık; FSRS'i kapat.
    expect(useAyar.getState().bildirim.fsrs).toBe(true);
    fireEvent.click(screen.getByRole('switch', { name: 'FSRS tekrar hatırlatması' }));
    expect(useAyar.getState().bildirim.fsrs).toBe(false);
    // Diğer anahtarlar dokunulmadı.
    expect(useAyar.getState().bildirim.seri).toBe(true);
    // Optimistik flash göründü.
    expect(screen.getByText('Kaydedildi')).toBeInTheDocument();
  });

  it('Sakin mod + Sıralamayı gizle store bayraklarını çevirir', async () => {
    render(<AyarlarPage />);
    await screen.findAllByText('Hüseyin Ateş');

    expect(useAyar.getState().calmMode).toBe(false);
    fireEvent.click(screen.getByRole('switch', { name: 'Sakin mod' }));
    expect(useAyar.getState().calmMode).toBe(true);

    expect(useAyar.getState().hideRanking).toBe(false);
    fireEvent.click(screen.getByRole('switch', { name: 'Sıralamayı gizle' }));
    expect(useAyar.getState().hideRanking).toBe(true);
  });

  it('günlük hedef stepper + / − store\'u 15 dk adımla günceller', async () => {
    render(<AyarlarPage />);
    await screen.findAllByText('Hüseyin Ateş');

    expect(useAyar.getState().dailyGoalMinutes).toBe(30);
    expect(screen.getByText('30 dk')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Günlük hedefi artır' }));
    expect(useAyar.getState().dailyGoalMinutes).toBe(45);
    expect(screen.getByText('45 dk')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Günlük hedefi azalt' }));
    expect(useAyar.getState().dailyGoalMinutes).toBe(30);
  });

  it('Görünüm KİLİTLİ: tema anahtarı disabled + kilit kopyası birebir', async () => {
    render(<AyarlarPage />);
    await screen.findAllByText('Hüseyin Ateş');

    const tema = screen.getByRole('switch', { name: 'Tema' });
    expect(tema).toHaveAttribute('aria-disabled', 'true');
    expect(screen.getByText('Çalışma ekranları göz konforu için hep aydınlık kalır.')).toBeInTheDocument();
    expect(screen.getByText('Otomatik — ekran türüne göre')).toBeInTheDocument();
  });

  it('KANON: absence-dili (yasak sözcük) taşımaz + kilit kopya + hesap', async () => {
    render(<AyarlarPage />);
    await screen.findAllByText('Hüseyin Ateş');
    expect(screen.getByText('Sakin varsayılan: az ve zamanında. Baskı yok.')).toBeInTheDocument();
    expect(screen.getByText('Çıkış yap')).toBeInTheDocument();
    expect(screen.getByText('doğrulandı')).toBeInTheDocument();
    expect(screen.queryByText(/\beksik\b/i)).not.toBeInTheDocument();
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<AyarlarPage />);
    await screen.findAllByText('Hüseyin Ateş');
    expect(await axe(container)).toHaveNoViolations();
  }, 20000);

  it('Görünüm "Vurgu rengi" + Hesap "Şifre değiştir" / "Gizlilik & veri" kilitli satırları render eder', async () => {
    render(<AyarlarPage />);
    await screen.findAllByText('Hüseyin Ateş');
    // Vurgu rengi kilitli bilgi satırı (kanon-güvenli coral swatch; #FF6F5C YOK)
    expect(screen.getByText('Vurgu rengi')).toBeInTheDocument();
    expect(screen.getByText('Şafak mercanı')).toBeInTheDocument();
    // Hesap gezinme satırları (KVKK giriş noktası dâhil)
    expect(screen.getByRole('button', { name: 'Şifre değiştir' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Gizlilik & veri' })).toBeInTheDocument();
  });
});

describe('AyarlarPage · durumlar & sınırlar', () => {
  it('getMe reddi → sakin ErrorState; "Tekrar dene" sonrası ayarlar döner', async () => {
    const spy = vi.spyOn(apiClient, 'getMe').mockRejectedValueOnce(new Error('persona'));
    render(<AyarlarPage />);
    expect(await screen.findByText('Ayarların şu an gelmedi.')).toBeInTheDocument();
    // Hata dalı → içerik kartları yok
    expect(screen.queryByRole('switch', { name: 'Sakin mod' })).not.toBeInTheDocument();
    // onRetry → useEffect yeniden koşar, gerçek getMe çözülür
    fireEvent.click(screen.getByRole('button', { name: 'Tekrar dene' }));
    expect((await screen.findAllByText('Hüseyin Ateş')).length).toBeGreaterThan(0);
    expect(screen.queryByText('Ayarların şu an gelmedi.')).not.toBeInTheDocument();
    expect(spy).toHaveBeenCalled();
  });

  it('yükleme dalı: persona gelmeden aria-busy iskeleti gösterir', async () => {
    render(<AyarlarPage />);
    const busy = screen.getByLabelText('Ayarlar yükleniyor');
    expect(busy).toHaveAttribute('aria-busy', 'true');
    // akışı boşalt (act uyarısı yok)
    await screen.findAllByText('Hüseyin Ateş');
    expect(screen.queryByLabelText('Ayarlar yükleniyor')).not.toBeInTheDocument();
  });

  it('"Kaydedildi" flash 1600ms sonra sonlu şekilde kalkar', async () => {
    render(<AyarlarPage />);
    await screen.findAllByText('Hüseyin Ateş');
    vi.useFakeTimers();
    try {
      fireEvent.click(screen.getByRole('switch', { name: 'Sakin mod' }));
      expect(screen.getByText('Kaydedildi')).toBeInTheDocument();
      act(() => {
        vi.advanceTimersByTime(1600);
      });
      expect(screen.queryByText('Kaydedildi')).not.toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });

  it('günlük hedef stepper HEDEF_MIN 15 / HEDEF_MAX 180 sınırında clamp + buton disabled', async () => {
    render(<AyarlarPage />);
    await screen.findAllByText('Hüseyin Ateş');

    const azalt = () => screen.getByRole('button', { name: 'Günlük hedefi azalt' });
    const artir = () => screen.getByRole('button', { name: 'Günlük hedefi artır' });

    // 30 → 15 (alt sınır); azalt disabled olur, tekrar tık no-op (clamp)
    fireEvent.click(azalt());
    expect(useAyar.getState().dailyGoalMinutes).toBe(15);
    expect(azalt()).toBeDisabled();
    fireEvent.click(azalt());
    expect(useAyar.getState().dailyGoalMinutes).toBe(15);

    // üst sınır: store'u 180'e getir → artır disabled, tık no-op (clamp)
    act(() => useAyar.getState().setDailyGoal(180));
    expect(screen.getByText('180 dk')).toBeInTheDocument();
    expect(artir()).toBeDisabled();
    fireEvent.click(artir());
    expect(useAyar.getState().dailyGoalMinutes).toBe(180);
  });
});
