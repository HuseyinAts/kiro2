import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { OnboardingPage } from './OnboardingPage';

expect.extend(toHaveNoViolations);

describe('OnboardingPage', () => {
  it('ton adımı: radiogroup + 3 seçenek + başlık', () => {
    render(<OnboardingPage />);
    expect(screen.getByText('Hoş geldin. Önce sen, sonra sorular.')).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'Kaygı ağır basıyor' })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'Değişken — güne göre' })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'Genelde sakinim' })).toBeInTheDocument();
  });

  it('ton seçince yanıt görünür + Devam etkinleşir', async () => {
    render(<OnboardingPage />);
    expect(screen.getByRole('button', { name: 'Devam et' })).toBeDisabled();
    await userEvent.click(screen.getByRole('radio', { name: 'Kaygı ağır basıyor' }));
    expect(screen.getByText(/Acele etmiyoruz/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Devam et' })).toBeEnabled();
  });

  it('tam akış: ton → 6 soru yerleştirme → Planın hazır', async () => {
    render(<OnboardingPage />);
    await userEvent.click(screen.getByRole('radio', { name: 'Genelde sakinim' }));
    await userEvent.click(screen.getByRole('button', { name: 'Devam et' }));
    expect(await screen.findByText('Seviyeni öğreniyoruz')).toBeInTheDocument();
    expect(screen.getByText('Soru 1 / 6')).toBeInTheDocument();
    for (let i = 0; i < 6; i++) {
      // calib'de yalnız 4 şık butonu var (üst öğeler <a>); ilkine tıkla
      await userEvent.click(screen.getAllByRole('button')[0]);
    }
    expect(await screen.findByText('Planın hazır!')).toBeInTheDocument();
  });

  it('"Bu soruyu geç" doğrudan ölçüme geçer', async () => {
    render(<OnboardingPage />);
    await userEvent.click(screen.getByRole('button', { name: 'Bu soruyu geç' }));
    expect(await screen.findByText('Soru 1 / 6')).toBeInTheDocument();
  });

  it('axe: erişilebilirlik ihlali yok (ton adımı)', async () => {
    const { container } = render(<OnboardingPage />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
