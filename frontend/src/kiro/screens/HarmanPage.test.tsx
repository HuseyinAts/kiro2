import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { HarmanPage } from './HarmanPage';

expect.extend(toHaveNoViolations);

describe('HarmanPage', () => {
  it('lobi: rationale + oturum kartı + karşılaştırma + bileşim', async () => {
    render(<HarmanPage />);
    expect(await screen.findByText('Konuları karıştır, daha iyi öğren')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1, name: 'Harmanlanmış Deneme' })).toBeInTheDocument();
    expect(screen.getByText('Bu oturum')).toBeInTheDocument();
    expect(screen.getByText('Denemeyi başlat →')).toBeInTheDocument();
    expect(screen.getByText('BLOKLU')).toBeInTheDocument();
    expect(screen.getByText('HARMANLANMIŞ')).toBeInTheDocument();
    expect(screen.getByText('Oturum bileşimi')).toBeInTheDocument();
  });

  it('harman/bloklu toggle sırayı değiştirir (üretimde kalır)', async () => {
    render(<HarmanPage />);
    await screen.findByText('Konuları karıştır, daha iyi öğren');
    expect(screen.getByText('Soru sırası · Harmanlanmış')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Bloklu görünüm' }));
    expect(screen.getByText('Soru sırası · Bloklu (karşılaştırma)')).toBeInTheDocument();
  });

  it('SideNav (deneme aktif) render eder', async () => {
    render(<HarmanPage />);
    await screen.findByText('Konuları karıştır, daha iyi öğren');
    expect(screen.getByRole('navigation')).toBeInTheDocument();
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<HarmanPage />);
    await screen.findByText('Konuları karıştır, daha iyi öğren');
    expect(await axe(container)).toHaveNoViolations();
  }, 20000);
});
