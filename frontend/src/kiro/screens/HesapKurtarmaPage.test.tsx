import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { HesapKurtarmaPage } from './HesapKurtarmaPage';

expect.extend(toHaveNoViolations);

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
    await userEvent.type(screen.getByLabelText('E-posta adresin'), 'ali@eposta.com');
    await userEvent.click(screen.getByRole('button', { name: 'Kod gönder' }));

    expect(await screen.findByText('Kod yolda.')).toBeInTheDocument();
    expect(screen.getByText('al•••@eposta.com')).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText('Doğrulama kodu'), '123456');
    await userEvent.click(screen.getByRole('button', { name: 'Doğrula' }));

    expect(await screen.findByText('Yeni şifreni seç.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Şifreyi güncelle' })).toBeDisabled();
    await userEvent.type(screen.getByLabelText('Yeni şifren'), 'Guclu2024');
    expect(screen.getByRole('button', { name: 'Şifreyi güncelle' })).toBeEnabled();
    await userEvent.click(screen.getByRole('button', { name: 'Şifreyi güncelle' }));

    expect(await screen.findByText('Hazırsın.')).toBeInTheDocument();
  });

  it('kod adımında "Kodu yeniden gönder" → gönderildi bildirimi', async () => {
    render(<HesapKurtarmaPage />);
    await userEvent.type(screen.getByLabelText('E-posta adresin'), 'ali@eposta.com');
    await userEvent.click(screen.getByRole('button', { name: 'Kod gönder' }));
    await screen.findByText('Kod yolda.');
    await userEvent.click(screen.getByRole('button', { name: 'Kodu yeniden gönder' }));
    expect(await screen.findByText(/Gönderildi — gelen kutuna bak/)).toBeInTheDocument();
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<HesapKurtarmaPage />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
