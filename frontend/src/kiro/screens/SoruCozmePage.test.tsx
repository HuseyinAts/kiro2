import { render, screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { SoruCozmePage } from './SoruCozmePage';

expect.extend(toHaveNoViolations);

describe('SoruCozmePage', () => {
  it('header + set yüklenir, ilk soru radiogroup gelir', async () => {
    render(<SoruCozmePage />);
    expect(screen.getByText('Matematik · Günlük Set')).toBeInTheDocument();
    expect(await screen.findByRole('radiogroup', { name: 'Şıklar' })).toBeInTheDocument();
  });

  it('şık seçimi → sunucu-otoriter review (çözüm paneli açılır, şıklar kilitlenir)', async () => {
    render(<SoruCozmePage />);
    const grp = await screen.findByRole('radiogroup', { name: 'Şıklar' });
    await userEvent.click(within(grp).getAllByRole('radio')[0]!);
    expect(await screen.findByText('Çözüm · adım adım')).toBeInTheDocument();
    expect(within(screen.getByRole('radiogroup')).getAllByRole('radio')[0]!).toBeDisabled();
  });

  it('navigatör render eder', async () => {
    render(<SoruCozmePage />);
    await screen.findByRole('radiogroup', { name: 'Şıklar' });
    const nav = screen.getByRole('navigation', { name: 'Sorular' });
    expect(within(nav).getByText('Soru Navigatörü')).toBeInTheDocument();
  });

  it('"Bu soruyu atla" bir sonraki soruya ilerletir', async () => {
    render(<SoruCozmePage />);
    await screen.findByRole('radiogroup', { name: 'Şıklar' });
    expect(screen.getByRole('button', { name: 'Önceki' })).toBeDisabled();
    await userEvent.click(screen.getByRole('button', { name: 'Bu soruyu atla' }));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Önceki' })).toBeEnabled());
  });

  it('pasif sayaç MM:SS biçiminde görünür', async () => {
    render(<SoruCozmePage />);
    await screen.findByRole('radiogroup', { name: 'Şıklar' });
    expect(screen.getByText(/^\d{2}:\d{2}$/)).toBeInTheDocument();
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<SoruCozmePage />);
    await screen.findByRole('radiogroup', { name: 'Şıklar' });
    expect(await axe(container)).toHaveNoViolations();
  }, 20000);
});
