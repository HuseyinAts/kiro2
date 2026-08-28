import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { VeliPaneliPage } from './VeliPaneliPage';

expect.extend(toHaveNoViolations);

describe('VeliPaneliPage', () => {
  it('salt-okur panel: başlık + çocuk özet bandı + KPI (sunucudan)', async () => {
    render(<VeliPaneliPage />);
    // Topbar h1 (sayfa başlığı)
    expect(await screen.findByRole('heading', { level: 1, name: 'Genel Bakış' })).toBeInTheDocument();
    // Çocuk özet bandı — tam ad (aktif çocuk)
    expect(await screen.findByText('Hüseyin Ateş')).toBeInTheDocument();
    // KPI etiketleri
    expect(screen.getByText('Çözülen soru')).toBeInTheDocument();
    expect(screen.getByText('Plan uyumu')).toBeInTheDocument();
    // SİZ dili yüzeyi (öğrenci "sen" değil)
    expect(screen.getByText(/deneme bitmeden hatırlatırız/)).toBeInTheDocument();
  });

  it('ChildSwitcher tablist: 2 sekme + aktif çocuk aria-selected', async () => {
    render(<VeliPaneliPage />);
    const tablist = await screen.findByRole('tablist', { name: 'Çocuk seçimi' });
    expect(tablist).toBeInTheDocument();
    const tabs = screen.getAllByRole('tab');
    expect(tabs).toHaveLength(2);
    const secili = screen.getByRole('tab', { selected: true });
    expect(secili).toHaveTextContent('Hüseyin');
  });

  it('Premium CTA "7 gün ücretsiz deneyin" → /abonelik?rol=veli', async () => {
    render(<VeliPaneliPage />);
    const cta = await screen.findByRole('link', { name: /7 gün ücretsiz deneyin/ });
    expect(cta).toHaveAttribute('href', '/abonelik?rol=veli');
  });

  it('reduced-motion: içerik korunur (spring/animasyon kapalı)', async () => {
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
      render(<VeliPaneliPage />);
      expect(await screen.findByText('Hüseyin Ateş')).toBeInTheDocument();
      expect(screen.getByText('Uyarılar & Öne Çıkanlar')).toBeInTheDocument();
    } finally {
      window.matchMedia = gercek;
    }
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<VeliPaneliPage />);
    await screen.findByText('Hüseyin Ateş');
    expect(await axe(container)).toHaveNoViolations();
  }, 40000);
});
