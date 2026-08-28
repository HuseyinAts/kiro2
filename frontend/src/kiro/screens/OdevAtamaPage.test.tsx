import { render, screen, fireEvent } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { OdevAtamaPage } from './OdevAtamaPage';

expect.extend(toHaveNoViolations);

describe('OdevAtamaPage', () => {
  it('render: başlık + zayıf-önde konu + Özet + kaygı-duyarlı varsayılanlar', async () => {
    render(<OdevAtamaPage />);
    // Zayıf konu (server sıralı) önde — İntegral ilk sırada
    expect(await screen.findByText('İntegral')).toBeInTheDocument();
    expect(screen.getByText('Yeni ödev')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Özet' })).toBeInTheDocument();
    // Kanon kartı — öğretmene ürün sözünü öğretir, asla kaldırılmaz
    expect(screen.getByText(/Kaygı-duyarlı varsayılanlar/)).toBeInTheDocument();
    // Geri-ok tek statik aria-label
    expect(screen.getByRole('link', { name: 'Öğretmen paneline dön' })).toHaveAttribute('href', '/ogretmen');
  });

  it('varsayılan tüm öğrenciler seçili → checkbox bırakınca sayaç düşer', async () => {
    render(<OdevAtamaPage />);
    await screen.findByText('İntegral');
    // odevAtama roster = 7 öğrenci; hepsi seçili başlar
    expect(screen.getByText(/7 \/ 7 seçili/)).toBeInTheDocument();
    const zeynep = screen.getByRole('checkbox', { name: /Zeynep Kaya/ });
    expect(zeynep).toHaveAttribute('aria-checked', 'true');
    fireEvent.click(zeynep);
    expect(zeynep).toHaveAttribute('aria-checked', 'false');
    expect(screen.getByText(/6 \/ 7 seçili/)).toBeInTheDocument();
  });

  it('CTA "Ödevi ata" → başarı bandı (role=status) görünür', async () => {
    render(<OdevAtamaPage />);
    await screen.findByText('İntegral');
    const cta = screen.getByRole('button', { name: /Ödevi ata/ });
    fireEvent.click(cta);
    const bant = await screen.findByRole('status');
    expect(bant).toHaveTextContent(/Ödev atandı — öğrencilere sakin bir bildirim gitti/);
  });

  it('θ switch: kapatınca Özet zorluğu "Herkese aynı set" olur', async () => {
    render(<OdevAtamaPage />);
    await screen.findByText('İntegral');
    expect(screen.getByText('Kişiye özel (θ tabanlı)')).toBeInTheDocument();
    const sw = screen.getByRole('switch', { name: 'Kişiye özel zorluk' });
    expect(sw).toHaveAttribute('aria-checked', 'true');
    fireEvent.click(sw);
    expect(sw).toHaveAttribute('aria-checked', 'false');
    expect(screen.getByText('Herkese aynı set')).toBeInTheDocument();
  });

  it('ön-seçim: ?ogrenci → yalnız o öğrenci seçili başlar', async () => {
    render(<OdevAtamaPage ogrenciId="o-cy" />);
    await screen.findByText('İntegral');
    expect(screen.getByText(/1 \/ 7 seçili/)).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: /Can Yıldız/ })).toHaveAttribute('aria-checked', 'true');
    expect(screen.getByRole('checkbox', { name: /Zeynep Kaya/ })).toHaveAttribute('aria-checked', 'false');
  });

  it('reduced-motion: içerik korunur (animasyon/spring yok)', async () => {
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
      render(<OdevAtamaPage />);
      expect(await screen.findByText('İntegral')).toBeInTheDocument();
    } finally {
      window.matchMedia = gercek;
    }
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<OdevAtamaPage />);
    await screen.findByText('İntegral');
    expect(await axe(container)).toHaveNoViolations();
  }, 40000);
});
