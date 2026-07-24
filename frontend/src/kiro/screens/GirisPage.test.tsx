import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect, vi, afterEach } from 'vitest';

import { GirisPage } from './GirisPage';
import * as apiClient from '../api/api-client';

expect.extend(toHaveNoViolations);

describe('GirisPage', () => {
  afterEach(() => vi.restoreAllMocks());

  it('giriş sekmesi seçili + serif başlık render eder', () => {
    render(<GirisPage />);
    expect(screen.getByRole('radio', { name: 'Giriş' })).toHaveAttribute('aria-checked', 'true');
    expect(screen.getByText('Tekrar hoş geldin.')).toBeInTheDocument();
  });

  it('Kayıt sekmesine geçince başlık + Ad alanı gelir', async () => {
    render(<GirisPage />);
    await userEvent.click(screen.getByRole('radio', { name: 'Kayıt' }));
    expect(screen.getByText('Başlayalım.')).toBeInTheDocument();
    expect(screen.getByLabelText('Adın')).toBeInTheDocument();
  });

  it('şifre göster/gizle aria-pressed toggle eder', async () => {
    render(<GirisPage />);
    const toggle = screen.getByRole('button', { name: 'Şifreyi göster' });
    expect(toggle).toHaveAttribute('aria-pressed', 'false');
    await userEvent.click(toggle);
    expect(screen.getByRole('button', { name: 'Şifreyi gizle' })).toHaveAttribute('aria-pressed', 'true');
  });

  it('geçersiz e-posta amber hint gösterir, absence-dili yok', async () => {
    render(<GirisPage />);
    await userEvent.type(screen.getByLabelText('E-posta adresin'), 'bozuk');
    await userEvent.type(screen.getByLabelText('Şifren'), 'sifre123');
    await userEvent.click(screen.getByRole('button', { name: 'Devam edelim' }));
    expect(await screen.findByText(/yarım görünüyor/i)).toBeInTheDocument();
    expect(screen.queryByText(/eksik/i)).not.toBeInTheDocument();
  });

  it('geçerli giriş → tamam durumu (İçerdesin.)', async () => {
    render(<GirisPage />);
    await userEvent.type(screen.getByLabelText('E-posta adresin'), 'ali@eposta.com');
    await userEvent.type(screen.getByLabelText('Şifren'), 'sifre123');
    await userEvent.click(screen.getByRole('button', { name: 'Devam edelim' }));
    expect(await screen.findByText('İçerdesin.')).toBeInTheDocument();
  });

  it('onLanding verilince giriş-tamam CTA rol landing ile çağrılır (ogrenci→/dashboard)', async () => {
    const onLanding = vi.fn();
    render(<GirisPage onLanding={onLanding} rol="ogrenci" />);
    await userEvent.type(screen.getByLabelText('E-posta adresin'), 'ali@eposta.com');
    await userEvent.type(screen.getByLabelText('Şifren'), 'sifre123');
    await userEvent.click(screen.getByRole('button', { name: 'Devam edelim' }));
    await userEvent.click(await screen.findByRole('button', { name: 'Panele geç' }));
    expect(onLanding).toHaveBeenCalledWith('/dashboard');
  });

  it('onLanding verilince kayıt-tamam CTA seviye-ölçüme yönlendirir (/onboarding)', async () => {
    const onLanding = vi.fn();
    render(<GirisPage onLanding={onLanding} />);
    await userEvent.click(screen.getByRole('radio', { name: 'Kayıt' }));
    await userEvent.type(screen.getByLabelText('Adın'), 'Ali');
    await userEvent.type(screen.getByLabelText('E-posta adresin'), 'ali@eposta.com');
    await userEvent.type(screen.getByLabelText('Şifren'), 'sifre123');
    await userEvent.click(screen.getByRole('button', { name: 'Hesabımı aç' }));
    await userEvent.click(await screen.findByRole('button', { name: 'Seviyeni ölçelim' }));
    expect(onLanding).toHaveBeenCalledWith('/onboarding');
  });

  it('getRol mount\'ta çağrılmaz, giriş başarısından sonra çekilir (sunucu-otorite)', async () => {
    const spy = vi.spyOn(apiClient, 'getRol').mockResolvedValue('ogrenci');
    render(<GirisPage />);
    expect(spy).not.toHaveBeenCalled();
    await userEvent.type(screen.getByLabelText('E-posta adresin'), 'ali@eposta.com');
    await userEvent.type(screen.getByLabelText('Şifren'), 'sifre123');
    await userEvent.click(screen.getByRole('button', { name: 'Devam edelim' }));
    await screen.findByText('İçerdesin.');
    expect(spy).toHaveBeenCalled();
  });

  it('onLanding verilmezse giriş-tamam CTA no-op (regresyon, kırılmaz)', async () => {
    render(<GirisPage />);
    await userEvent.type(screen.getByLabelText('E-posta adresin'), 'ali@eposta.com');
    await userEvent.type(screen.getByLabelText('Şifren'), 'sifre123');
    await userEvent.click(screen.getByRole('button', { name: 'Devam edelim' }));
    await userEvent.click(await screen.findByRole('button', { name: 'Panele geç' }));
    expect(screen.getByText('İçerdesin.')).toBeInTheDocument();
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<GirisPage />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
