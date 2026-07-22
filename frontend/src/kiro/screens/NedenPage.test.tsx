import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { NedenPage } from './NedenPage';

expect.extend(toHaveNoViolations);

describe('NedenPage', () => {
  it('yanlış senaryo: sonuç bandı + soru özeti + NEDEN YANLIŞ + çözüm + sağ ray', async () => {
    render(<NedenPage />);
    expect(await screen.findByText('Yanlış — hadi nedenini görelim')).toBeInTheDocument();
    expect(screen.getByText('Çözüm & Açıklama')).toBeInTheDocument();
    expect(screen.getByText('Senin cevabın')).toBeInTheDocument();
    expect(screen.getByText(/NEDEN .* YANLIŞ/)).toBeInTheDocument();
    expect(screen.getByText('ÇÖZÜM · adım adım')).toBeInTheDocument();
    // sağ ray (jsdom matchMedia false → görünür)
    expect(screen.getByText('Hafıza motoru (FSRS)')).toBeInTheDocument();
    expect(screen.getByText('Kavram hâkimiyeti etkisi')).toBeInTheDocument();
    expect(screen.getByText('İlgili kavramlar')).toBeInTheDocument();
  });

  it('doğru senaryo: ölçülü kutlama, NEDEN YANLIŞ kutusu render edilmez', async () => {
    render(<NedenPage senaryo="dogru" />);
    expect(await screen.findByText('Doğru!')).toBeInTheDocument();
    expect(screen.getByText(/Güzel iş\. Yine de/)).toBeInTheDocument();
    expect(screen.queryByText(/YANLIŞ/)).not.toBeInTheDocument();
  });

  it('SideNav (practice aktif) render eder', async () => {
    render(<NedenPage />);
    await screen.findByText('Yanlış — hadi nedenini görelim');
    expect(screen.getByRole('navigation')).toBeInTheDocument();
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<NedenPage />);
    await screen.findByText('Yanlış — hadi nedenini görelim');
    expect(await axe(container)).toHaveNoViolations();
  }, 20000);
});
