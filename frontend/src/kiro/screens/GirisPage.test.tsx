import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { GirisPage } from './GirisPage';

expect.extend(toHaveNoViolations);

describe('GirisPage', () => {
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

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<GirisPage />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
