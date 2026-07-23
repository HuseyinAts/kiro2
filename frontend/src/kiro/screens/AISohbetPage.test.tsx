import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect, vi } from 'vitest';

import * as apiClient from '../api/api-client';
import { AISohbetPage } from './AISohbetPage';

expect.extend(toHaveNoViolations);

// NOT: vi.restoreAllMocks() KULLANMA — setup.ts'in global matchMedia vi.fn'ini bozar.
// Spy'lar mockRejectedValueOnce/mockImplementationOnce ile tek çağrıdan sonra orijinale döner.

// getSohbet('direct') açılış AI mesajı (kiro-data.sohbet — SEN dili, sunucu-otoriter).
const ACILIS = 'Ben senin çalışma arkadaşınım';
// streamSohbet('direct') server-sim yanıtı (sohbetScriptedYanit — istemci cevap uydurmaz).
const YANIT = 'Tabii, birlikte bakalım';

describe('AISohbetPage', () => {
  it('SideNav + topbar (AI Öğretmen Asistanı, çevrimiçi pili) render eder', () => {
    render(<AISohbetPage />);
    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(screen.getByText('AI Öğretmen Asistanı')).toBeInTheDocument();
    expect(screen.getByText('Çevrimiçi · Türkçe · Qwen3-8B')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Yeni sohbet' })).toBeInTheDocument();
  });

  it('boş sohbet: getSohbet açılış AI mesajını (role=log) render eder', async () => {
    render(<AISohbetPage />);
    expect(await screen.findByText(new RegExp(ACILIS))).toBeInTheDocument();
    expect(screen.getByRole('log')).toBeInTheDocument();
  });

  it('composer: yer-tutucu DC birebir + disclaimer', async () => {
    render(<AISohbetPage />);
    await screen.findByText(new RegExp(ACILIS));
    expect(screen.getByPlaceholderText('Bir soru sor ya da takıldığın konuyu yaz…')).toBeInTheDocument();
    expect(screen.getByText('KIRO AI hata yapabilir — önemli sonuçları kontrol et.')).toBeInTheDocument();
  });

  it('KANON: açılış mesajı SEN dili; yasak absence-dili taşımaz', async () => {
    render(<AISohbetPage />);
    await screen.findByText(new RegExp(ACILIS));
    expect(screen.queryByText(/\beksik\b/i)).not.toBeInTheDocument();
  });

  it('Enter=gönder: kullanıcı balonu + streamSohbet yanıtı (sunucu-otoriter) akar', async () => {
    render(<AISohbetPage />);
    await screen.findByText(new RegExp(ACILIS));
    const alan = screen.getByLabelText('Soru yaz');
    fireEvent.change(alan, { target: { value: 'Türev nedir?' } });
    fireEvent.keyDown(alan, { key: 'Enter' });
    // Kullanıcı mesajı hemen görünür (rol ben)
    expect(await screen.findByText('Türev nedir?')).toBeInTheDocument();
    // AI yanıtı token token akar → tam metin gelir (istemci uydurmaz)
    expect(await screen.findByText(new RegExp(YANIT), undefined, { timeout: 4000 })).toBeInTheDocument();
  }, 10000);

  it('Shift+Enter göndermez (yeni satır); metin composer\'da kalır', async () => {
    render(<AISohbetPage />);
    await screen.findByText(new RegExp(ACILIS));
    const alan = screen.getByLabelText('Soru yaz') as HTMLTextAreaElement;
    fireEvent.change(alan, { target: { value: 'Bekleyen satır' } });
    fireEvent.keyDown(alan, { key: 'Enter', shiftKey: true });
    // Balon olarak GÖNDERİLMEZ (textarea değerini hariç tut); metin composer'da kalır
    expect(screen.queryByText('Bekleyen satır', { ignore: 'script, style, textarea' })).not.toBeInTheDocument();
    expect(alan.value).toBe('Bekleyen satır');
  });

  it('gönder düğmesi boş girdide devre dışı, metin girilince etkin', async () => {
    render(<AISohbetPage />);
    await screen.findByText(new RegExp(ACILIS));
    const gonder = screen.getByRole('button', { name: 'Gönder' });
    expect(gonder).toBeDisabled();
    fireEvent.change(screen.getByLabelText('Soru yaz'), { target: { value: 'Merhaba' } });
    expect(gonder).toBeEnabled();
  });

  it('Yeni sohbet: açılış oturumunu yeniden yükler (getSohbet tekrar çağrılır)', async () => {
    const spy = vi.spyOn(apiClient, 'getSohbet');
    render(<AISohbetPage />);
    await screen.findByText(new RegExp(ACILIS));
    const ilk = spy.mock.calls.length;
    fireEvent.click(screen.getByRole('button', { name: 'Yeni sohbet' }));
    await waitFor(() => expect(spy.mock.calls.length).toBeGreaterThan(ilk));
    expect(await screen.findByText(new RegExp(ACILIS))).toBeInTheDocument();
    spy.mockRestore();
  });

  it('getSohbet reddi ErrorState açar; retry sonrası açılış mesajı döner', async () => {
    vi.spyOn(apiClient, 'getSohbet').mockRejectedValueOnce(new Error('baglanti'));
    render(<AISohbetPage />);
    expect(await screen.findByText('Sohbet şu an yüklenemedi.')).toBeInTheDocument();
    expect(screen.queryByText(new RegExp(ACILIS))).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Tekrar dene' }));
    expect(await screen.findByText(new RegExp(ACILIS))).toBeInTheDocument();
    expect(screen.queryByText('Sohbet şu an yüklenemedi.')).not.toBeInTheDocument();
  });

  it('stream hatası: onError → sakin ErrorState (tekrar)', async () => {
    vi.spyOn(apiClient, 'streamSohbet').mockImplementationOnce((_args, h) => {
      h.onError?.(new Error('stream'));
      return () => undefined;
    });
    render(<AISohbetPage />);
    await screen.findByText(new RegExp(ACILIS));
    fireEvent.change(screen.getByLabelText('Soru yaz'), { target: { value: 'Limit sorusu' } });
    fireEvent.click(screen.getByRole('button', { name: 'Gönder' }));
    expect(await screen.findByText('Sohbet şu an yüklenemedi.')).toBeInTheDocument();
  });

  it('persona (getMe) reddi ekranı düşürmez; nav "Öğrenci"e düşer', async () => {
    vi.spyOn(apiClient, 'getMe').mockRejectedValueOnce(new Error('persona'));
    render(<AISohbetPage />);
    expect(await screen.findByText(new RegExp(ACILIS))).toBeInTheDocument();
    expect(screen.getByText('Öğrenci')).toBeInTheDocument();
  });

  it('onConnected: server session_id sonraki gönderide oturumId olur (sunucu-otorite)', async () => {
    const YENI_ID = 'srv-oturum-42';
    const oturumIdler: Array<string | undefined> = [];
    const spy = vi.spyOn(apiClient, 'streamSohbet').mockImplementation((args, h) => {
      oturumIdler.push(args.oturumId);
      h.onConnected?.(YENI_ID); // sunucu gerçek oturum kimliğini bildirir
      h.onToken?.('yanıt');
      h.onFinished?.({ id: 'ai-' + oturumIdler.length, rol: 'ai', metin: 'yanıt' });
      return () => undefined;
    });
    render(<AISohbetPage />);
    await screen.findByText(new RegExp(ACILIS));
    const alan = screen.getByLabelText('Soru yaz');

    // 1. gönder → açılış oturum id'si kullanılır, onConnected server-id atar
    fireEvent.change(alan, { target: { value: 'İlk soru' } });
    fireEvent.keyDown(alan, { key: 'Enter' });
    await screen.findByText('İlk soru');

    // 2. gönder → artık server-atanmış id kullanılmalı (istemci kendi id'sini dayatmaz)
    fireEvent.change(alan, { target: { value: 'İkinci soru' } });
    fireEvent.keyDown(alan, { key: 'Enter' });
    await screen.findByText('İkinci soru');

    expect(oturumIdler).toHaveLength(2);
    expect(oturumIdler[1]).toBe(YENI_ID);
    expect(oturumIdler[0]).not.toBe(YENI_ID);
    spy.mockRestore();
  });

  it('a11y 2.4.7: ana textarea inline outline:none taşımaz; odak halkası CSS :focus-visible ile', async () => {
    render(<AISohbetPage />);
    await screen.findByText(new RegExp(ACILIS));
    const alan = screen.getByLabelText('Soru yaz') as HTMLTextAreaElement;
    // Inline outline:none KALDIRILDI → CSS kuralı ezilmez
    expect(alan.style.outline).toBe('');
    const stiller = Array.from(document.querySelectorAll('style')).map((s) => s.textContent).join('\n');
    expect(stiller).toContain('.k-chat-field:focus-visible');
    expect(stiller).toContain('.k-chat-field{outline:none;}');
  });

  it('a11y: AI beklerken görünmez SR "KIRO yazıyor…" işareti belirir, yanıt gelince kalkar', async () => {
    let yakalanan: apiClient.SohbetStreamHandlers | null = null;
    const spy = vi.spyOn(apiClient, 'streamSohbet').mockImplementation((_args, h) => {
      yakalanan = h;
      h.onConnected?.('oturum-x');
      // onToken/onFinished ÇAĞIRMA → pending durumda kal (AI "yazıyor")
      return () => undefined;
    });
    render(<AISohbetPage />);
    await screen.findByText(new RegExp(ACILIS));
    fireEvent.change(screen.getByLabelText('Soru yaz'), { target: { value: 'Bekleyen' } });
    fireEvent.keyDown(screen.getByLabelText('Soru yaz'), { key: 'Enter' });

    // Beklerken SR işareti görünür (TypingDots aria-hidden olduğundan SR bunu duyar)
    expect(await screen.findByText('KIRO yazıyor…')).toBeInTheDocument();

    // Yanıt tamamlanınca işaret kalkar (streaming bitti)
    act(() => {
      yakalanan!.onFinished?.({ id: 'ai-son', rol: 'ai', metin: 'Tamamlandı' });
    });
    await waitFor(() => expect(screen.queryByText('KIRO yazıyor…')).not.toBeInTheDocument());
    expect(screen.getByText('Tamamlandı')).toBeInTheDocument();
    spy.mockRestore();
  });

  it('breakpoint ≤1023px: matchMedia matches → SideNav 64px ikon rayına çöker (bölüm başlığı gizli)', async () => {
    const gercek = window.matchMedia;
    window.matchMedia = ((q: string) => ({
      matches: q.includes('max-width: 1023px'),
      media: q,
      onchange: null,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      addListener: () => undefined,
      removeListener: () => undefined,
      dispatchEvent: () => false,
    })) as unknown as typeof window.matchMedia;
    try {
      render(<AISohbetPage />);
      await screen.findByText(new RegExp(ACILIS));
      // Daralınca bölüm başlıkları + etiketler gizlenir (yalnız ikon rayı kalır)
      expect(screen.queryByText('Çalışma')).not.toBeInTheDocument();
      expect(screen.getByRole('navigation')).toBeInTheDocument();
    } finally {
      window.matchMedia = gercek;
    }
  });

  it('breakpoint >1023px: matchMedia matches yok → SideNav genişler (bölüm başlığı görünür)', async () => {
    const gercek = window.matchMedia;
    window.matchMedia = ((q: string) => ({
      matches: false, // hiçbir sorgu eşleşmez → dar=false
      media: q,
      onchange: null,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      addListener: () => undefined,
      removeListener: () => undefined,
      dispatchEvent: () => false,
    })) as unknown as typeof window.matchMedia;
    try {
      render(<AISohbetPage />);
      await screen.findByText(new RegExp(ACILIS));
      expect(screen.getByText('Çalışma')).toBeInTheDocument();
    } finally {
      window.matchMedia = gercek;
    }
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<AISohbetPage />);
    await screen.findByText(new RegExp(ACILIS));
    expect(await axe(container)).toHaveNoViolations();
  }, 20000);
});
