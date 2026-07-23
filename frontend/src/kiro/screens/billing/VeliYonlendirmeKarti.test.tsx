import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { VeliYonlendirmeKarti } from './VeliYonlendirmeKarti';

expect.extend(toHaveNoViolations);

describe('VeliYonlendirmeKarti (paylaşılan · ÖĞRENCİ FİYAT GİZLİ)', () => {
  it('abonelik bağlamı: serif başlık + SEN dili + coral "Veli hesabına git" /veli; fiyat/rakam YOK', () => {
    render(<VeliYonlendirmeKarti />);
    // Serif başlık (öğrenci dili = SEN; "velin" yönetir)
    expect(screen.getByText('Aboneliğini velin yönetir')).toBeInTheDocument();
    // SEN dili (kaygı azaltıcı, çalışmaya yönlendir)
    expect(screen.getByText(/Sen çalışmaya odaklan/)).toBeInTheDocument();
    // CTA veli hesabına (link/buton, /veli rotasına)
    const cta = screen.getByRole('link', { name: 'Veli hesabına git' });
    expect(cta).toHaveAttribute('href', '/veli');
    // FİYAT/PLAN GÖSTERİLMEZ (₺ / TL / plan fiyatı yok)
    expect(screen.queryByText(/₺|\bTL\b|124|924/)).not.toBeInTheDocument();
  });

  it('yönetim bağlamı: plan/ödeme ayarları dili; yine SEN + coral CTA /veli', () => {
    render(<VeliYonlendirmeKarti baglam="yonetim" />);
    expect(screen.getByText(/Plan ve ödeme ayarların veli hesabından yönetilir/)).toBeInTheDocument();
    expect(screen.getByText('Aboneliğini velin yönetir')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Veli hesabına git' })).toHaveAttribute('href', '/veli');
  });

  it('axe: erişilebilirlik ihlali yok (paper kart)', async () => {
    const { container } = render(<VeliYonlendirmeKarti />);
    expect(await axe(container)).toHaveNoViolations();
  }, 20000);
});
