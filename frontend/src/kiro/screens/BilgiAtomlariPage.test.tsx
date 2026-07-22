import { render, screen, within } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { BilgiAtomlariPage } from './BilgiAtomlariPage';

expect.extend(toHaveNoViolations);

describe('BilgiAtomlariPage', () => {
  it('başlık + kicker + atom kırılımı yüklenir', async () => {
    render(<BilgiAtomlariPage />);
    // Statik başlık hemen görünür
    expect(screen.getByText('Konu Değil · Tam Adım')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Bilgi Atomları' })).toBeInTheDocument();
    // Veri yüklenince radiogroup gelir
    expect(await screen.findByRole('radiogroup', { name: 'Odak konu' })).toBeInTheDocument();
  });

  it('içgörü kutusu + breadcrumb sunucudan gelen en zayıf atomu gösterir', async () => {
    render(<BilgiAtomlariPage />);
    await screen.findByRole('radiogroup', { name: 'Odak konu' });
    // İçgörü kutusu metni (BİREBİR kopya fragmanı, tek text node)
    expect(screen.getByText(/onlarla vakit harcamıyoruz/)).toBeInTheDocument();
    // Türev'in en zayıf atomu = İç-fonksiyon türevi (breadcrumb + atom listesi)
    expect(screen.getAllByText('İç-fonksiyon türevi').length).toBeGreaterThanOrEqual(2);
  });

  it('odak konu chip seçici radiogroup + aria-checked (varsayılan Türev)', async () => {
    render(<BilgiAtomlariPage />);
    const grp = await screen.findByRole('radiogroup', { name: 'Odak konu' });
    const radios = within(grp).getAllByRole('radio');
    expect(radios.length).toBeGreaterThan(0);
    expect(within(grp).getByRole('radio', { name: 'Türev' })).toBeChecked();
  });

  it('CTA ported rota /soru-cozme için gerçek çapa üretir', async () => {
    render(<BilgiAtomlariPage />);
    const cta = await screen.findByRole('link', { name: /atomunu çöz/ });
    expect(cta).toHaveAttribute('href', '/soru-cozme');
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<BilgiAtomlariPage />);
    await screen.findByRole('radiogroup', { name: 'Odak konu' });
    expect(await axe(container)).toHaveNoViolations();
  }, 20000);
});
