import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { PanelPage } from './PanelPage';

expect.extend(toHaveNoViolations);

describe('PanelPage', () => {
  it('SideNav + selamlama render eder', async () => {
    render(<PanelPage />);
    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(await screen.findByText('Merhaba, Hüseyin')).toBeInTheDocument();
  });

  it('ders hâkimiyeti + progressbar erişilebilir ad taşır', async () => {
    render(<PanelPage />);
    await screen.findByText('Merhaba, Hüseyin');
    expect(screen.getByText('Ders Bazında Hâkimiyet')).toBeInTheDocument();
    expect(screen.getByRole('progressbar', { name: /Matematik hâkimiyeti yüzde 78/ })).toBeInTheDocument();
  });

  it('KPI + günlük görevler + son sınav bloklarını gösterir', async () => {
    render(<PanelPage />);
    await screen.findByText('Merhaba, Hüseyin');
    expect(screen.getByText('Ortalama başarı')).toBeInTheDocument();
    expect(screen.getByText('Günlük Görevler')).toBeInTheDocument();
    expect(screen.getByText('FSRS tekrarını bitir')).toBeInTheDocument();
    expect(screen.getByText('KIRO Genel Deneme #7')).toBeInTheDocument();
  });

  it('topbar bildirim + ayar butonları erişilebilir', async () => {
    render(<PanelPage />);
    await screen.findByText('Merhaba, Hüseyin');
    expect(screen.getByLabelText('Bildirimler')).toBeInTheDocument();
    expect(screen.getByLabelText('Ayarlar')).toBeInTheDocument();
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<PanelPage />);
    await screen.findByText('Merhaba, Hüseyin');
    expect(await axe(container)).toHaveNoViolations();
  }, 20000);
});
