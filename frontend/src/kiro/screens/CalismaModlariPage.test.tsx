import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { CalismaModlariPage } from './CalismaModlariPage';

expect.extend(toHaveNoViolations);

describe('CalismaModlariPage', () => {
  it('başlık + kicker + giriş metni render eder', async () => {
    render(<CalismaModlariPage />);
    expect(await screen.findByText('Çalışma Modları')).toBeInTheDocument();
    expect(screen.getByText('Tek Havuz · Çok Yol')).toBeInTheDocument();
    expect(screen.getByText(/Çeşitlilik hafızayı güçlendirir/)).toBeInTheDocument();
  });

  it('4 mod kartı adlarıyla listelenir', async () => {
    render(<CalismaModlariPage />);
    await screen.findByText('Çalışma Modları');
    expect(await screen.findByText('Kart')).toBeInTheDocument();
    expect(screen.getByText('Test')).toBeInTheDocument();
    expect(screen.getByText('Eşleştirme')).toBeInTheDocument();
    expect(screen.getByText('Hız')).toBeInTheDocument();
  });

  it('havuz kartı ve alt not (tek havuz anlatısı) görünür', async () => {
    render(<CalismaModlariPage />);
    expect(await screen.findByText('Türev · zincir kuralı havuzu')).toBeInTheDocument();
    expect(screen.getByText(/Dört mod da aynı/)).toBeInTheDocument();
    expect(screen.getByText(/Motor hangi modun hangi kartta en çok işe yaradığını öğrenir/)).toBeInTheDocument();
  });

  it('mod kartları gerçek rota çapaları (href) taşır', async () => {
    render(<CalismaModlariPage />);
    const test = await screen.findByText('Teste başla');
    const anchor = test.closest('a');
    expect(anchor).toHaveAttribute('href', '/soru-cozme');
  });

  it('axe: sayfa temiz', async () => {
    const { container } = render(<CalismaModlariPage />);
    await screen.findByText('Çalışma Modları');
    expect(await axe(container)).toHaveNoViolations();
  }, 20000);
});
