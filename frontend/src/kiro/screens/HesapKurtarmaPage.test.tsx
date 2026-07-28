import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect, afterEach } from 'vitest';

import { configureKiroApi } from '../api/api-client';

import { HesapKurtarmaPage } from './HesapKurtarmaPage';

expect.extend(toHaveNoViolations);

// Sunucu politikasını (auth.py `_validate_password`) karşılayan şifre.
// ÖNCEDEN 'Guclu2024' idi: büyük+küçük+rakam var ama ÖZEL KARAKTER yok.
// Ekran onu kabul ediyordu, sunucu reddediyordu — test yanlış sözleşmeyi
// sabitlemişti. Ekran mock olduğu için fark edilmemişti.
const GECERLI_SIFRE = 'Guclu2024!';

const stubResponse = (body: unknown): Response =>
  ({ ok: true, status: 200, json: async () => body }) as unknown as Response;

afterEach(() => {
  configureKiroApi({ mode: 'mock' });
});

async function akisiKodAdimina(eposta = 'ali@eposta.com') {
  await userEvent.type(screen.getByLabelText('E-posta adresin'), eposta);
  await userEvent.click(screen.getByRole('button', { name: 'Kod gönder' }));
  expect(await screen.findByText('Kod yolda.')).toBeInTheDocument();
}

describe('HesapKurtarmaPage', () => {
  it('adım 1: e-posta adımı + serif başlık', () => {
    render(<HesapKurtarmaPage />);
    expect(screen.getByText('Adım 1 / 3')).toBeInTheDocument();
    expect(screen.getByText('Hesabını birlikte açalım.')).toBeInTheDocument();
    expect(screen.getByLabelText('E-posta adresin')).toBeInTheDocument();
  });

  it('geçersiz e-posta amber hint gösterir, absence-dili yok', async () => {
    render(<HesapKurtarmaPage />);
    await userEvent.type(screen.getByLabelText('E-posta adresin'), 'bozuk');
    await userEvent.click(screen.getByRole('button', { name: 'Kod gönder' }));
    expect(await screen.findByText(/yarım görünüyor/i)).toBeInTheDocument();
    expect(screen.queryByText(/eksik/i)).not.toBeInTheDocument();
  });

  it('tam akış: e-posta → kod → şifre → tamam', async () => {
    render(<HesapKurtarmaPage />);
    await akisiKodAdimina();
    expect(screen.getByText('al•••@eposta.com')).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText('Doğrulama kodu'), '123456');
    await userEvent.click(screen.getByRole('button', { name: 'Doğrula' }));

    expect(await screen.findByText('Yeni şifreni seç.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Şifreyi güncelle' })).toBeDisabled();
    await userEvent.type(screen.getByLabelText('Yeni şifren'), GECERLI_SIFRE);
    expect(screen.getByRole('button', { name: 'Şifreyi güncelle' })).toBeEnabled();
    await userEvent.click(screen.getByRole('button', { name: 'Şifreyi güncelle' }));

    expect(await screen.findByText('Hazırsın.')).toBeInTheDocument();
  });

  it('şifre kuralları sunucuyla aynı: özel karakteri olmayan şifre kabul edilmez', async () => {
    // Bu test olmasaydı ekran yine sunucudan farklı bir politika uygulayabilir
    // ve kullanıcı kodu girdikten SONRA reddedilirdi.
    render(<HesapKurtarmaPage />);
    await akisiKodAdimina();
    await userEvent.type(screen.getByLabelText('Doğrulama kodu'), '123456');
    await userEvent.click(screen.getByRole('button', { name: 'Doğrula' }));
    await screen.findByText('Yeni şifreni seç.');

    await userEvent.type(screen.getByLabelText('Yeni şifren'), 'Guclu2024');
    expect(screen.getByRole('button', { name: 'Şifreyi güncelle' })).toBeDisabled();

    await userEvent.type(screen.getByLabelText('Yeni şifren'), '!');
    expect(screen.getByRole('button', { name: 'Şifreyi güncelle' })).toBeEnabled();
  });

  it('kod adımında "Kodu yeniden gönder" → gönderildi bildirimi', async () => {
    render(<HesapKurtarmaPage />);
    await akisiKodAdimina();
    await userEvent.click(screen.getByRole('button', { name: 'Kodu yeniden gönder' }));
    expect(await screen.findByText(/Gönderildi — gelen kutuna bak/)).toBeInTheDocument();
  });

  it('canlı modda GERÇEK uçlara gider — /auth/recover diye bir uç yok', async () => {
    // Ekran mock modda çalıştığı için, var olmayan `/auth/recover` yoluna
    // gitmesi 4 ay boyunca fark edilmedi. Bu test yolları ve gövdeleri
    // sabitler: backend sözleşmesi değişirse burası kırmızıya döner.
    const cagrilar: Array<{ url: string; body: unknown }> = [];
    const sahteFetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
      const u = String(url);
      cagrilar.push({ url: u, body: init?.body ? JSON.parse(String(init.body)) : null });
      if (u.includes('/verify-reset-code')) return stubResponse({ success: true, token: 'tkn-1' });
      return stubResponse({ success: true, message: 'tamam' });
    }) as typeof fetch;

    configureKiroApi({ mode: 'live', baseUrl: 'http://test.local', fetchImpl: sahteFetch });
    render(<HesapKurtarmaPage />);

    await akisiKodAdimina();
    await userEvent.type(screen.getByLabelText('Doğrulama kodu'), '123456');
    await userEvent.click(screen.getByRole('button', { name: 'Doğrula' }));
    await screen.findByText('Yeni şifreni seç.');
    await userEvent.type(screen.getByLabelText('Yeni şifren'), GECERLI_SIFRE);
    await userEvent.click(screen.getByRole('button', { name: 'Şifreyi güncelle' }));
    await screen.findByText('Hazırsın.');

    expect(cagrilar.map((c) => c.url)).toEqual([
      'http://test.local/api/v1/auth/forgot-password',
      'http://test.local/api/v1/auth/verify-reset-code',
      'http://test.local/api/v1/auth/reset-password',
    ]);
    expect(cagrilar[0].body).toEqual({ email: 'ali@eposta.com' });
    expect(cagrilar[1].body).toEqual({ email: 'ali@eposta.com', code: '123456' });
    expect(cagrilar[2].body).toEqual({ token: 'tkn-1', newPassword: GECERLI_SIFRE });
  });

  it('sunucu kodu reddederse şifre adımına GEÇİLMEZ', async () => {
    // Eski davranış: kod istemcide doğrulanıyordu (kod.length === 6), yani
    // yanlış kodla da 3. adıma geçiliyordu ve kullanıcı boşa şifre yazıyordu.
    const sahteFetch = (async (url: RequestInfo | URL) => {
      const u = String(url);
      if (u.includes('/verify-reset-code')) return stubResponse({ success: false, token: null });
      return stubResponse({ success: true, message: 'tamam' });
    }) as typeof fetch;

    configureKiroApi({ mode: 'live', baseUrl: 'http://test.local', fetchImpl: sahteFetch });
    render(<HesapKurtarmaPage />);

    await akisiKodAdimina();
    await userEvent.type(screen.getByLabelText('Doğrulama kodu'), '999999');
    await userEvent.click(screen.getByRole('button', { name: 'Doğrula' }));

    expect(await screen.findByText(/Bu kod geçmiyor/i)).toBeInTheDocument();
    expect(screen.queryByText('Yeni şifreni seç.')).not.toBeInTheDocument();
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<HesapKurtarmaPage />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
