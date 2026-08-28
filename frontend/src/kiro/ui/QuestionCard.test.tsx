import * as React from 'react';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect, vi } from 'vitest';

import { QuestionCard } from './QuestionCard';
import { KiroThemeProvider } from './theme';
import type { AnswerResult } from '../api/api-client';

expect.extend(toHaveNoViolations);

const BASE = {
  soruNo: 1, toplam: 10, konu: 'Türev', zorlukB: 0.4,
  soru: 'f(x)=x² fonksiyonunun türevi nedir?', secenekler: ['2x', 'x', '2', 'x²'],
};

function Harness(props: Partial<React.ComponentProps<typeof QuestionCard>>) {
  const [sec, setSec] = React.useState<number | null>(null);
  return (
    <KiroThemeProvider theme="paper">
      <QuestionCard {...BASE} secilen={sec} onSelect={setSec} {...props} />
    </KiroThemeProvider>
  );
}

const DOGRU: AnswerResult = { correct: true, dogru: 0, cozum: ['Kuvvet kuralı uygula.', 'n·xⁿ⁻¹ → 2x.'], neden: 'Türev anlık değişim hızıdır.', xpKazanilan: 10 };
const YANLIS: AnswerResult = { correct: false, dogru: 0, cozum: ['Kuvvet kuralı uygula.'], neden: 'Türev anlık değişim hızıdır.', xpKazanilan: 2 };

describe('QuestionCard', () => {
  it('etkileşimli: radiogroup + şık seçimi aria-checked yansıtır', async () => {
    render(<Harness />);
    const grp = screen.getByRole('radiogroup', { name: 'Şıklar' });
    const radios = within(grp).getAllByRole('radio');
    expect(radios).toHaveLength(4);
    await userEvent.click(radios[0]!);
    expect(radios[0]!).toHaveAttribute('aria-checked', 'true');
  });

  it('klavye: rakam tuşu doğrudan şık seçer', async () => {
    render(<Harness />);
    const radios = within(screen.getByRole('radiogroup')).getAllByRole('radio');
    radios[0]!.focus();
    await userEvent.keyboard('3');
    expect(radios[2]!).toHaveAttribute('aria-checked', 'true');
  });

  it('klavye: ok tuşu odağı gezinir ama cevabı GÖNDERMEZ', async () => {
    render(<Harness />);
    const radios = within(screen.getByRole('radiogroup')).getAllByRole('radio');
    radios[0]!.focus();
    await userEvent.keyboard('{ArrowDown}');
    expect(radios[1]!).toHaveFocus();
    expect(radios[1]!).toHaveAttribute('aria-checked', 'false'); // kazara gönderim yok
  });

  it('klavye: Enter odaklı şıkkı gönderir (native onClick)', async () => {
    render(<Harness />);
    const radios = within(screen.getByRole('radiogroup')).getAllByRole('radio');
    radios[1]!.focus();
    await userEvent.keyboard('{Enter}');
    expect(radios[1]!).toHaveAttribute('aria-checked', 'true');
  });

  it('review: doğru/senin etiketleri + çözüm paneli + neden', () => {
    render(
      <KiroThemeProvider theme="paper">
        <QuestionCard {...BASE} secilen={1} sonuc={YANLIS} />
      </KiroThemeProvider>,
    );
    expect(screen.getByText('Doğru cevap')).toBeInTheDocument();
    expect(screen.getByText('Senin cevabın')).toBeInTheDocument();
    expect(screen.getByText('Çözüm · adım adım')).toBeInTheDocument();
    expect(screen.getByText(/Türev anlık değişim/)).toBeInTheDocument();
    // Kaygı-tonu: "birlikte bakalım" — alarm dili yok
    expect(screen.getByText(/hadi nedenini görelim/)).toBeInTheDocument();
    // review'da şıklar kilitli
    expect(screen.getAllByRole('radio')[0]!).toBeDisabled();
  });

  it('review doğru: ölçülü kutlama (abartısız)', () => {
    render(
      <KiroThemeProvider theme="paper">
        <QuestionCard {...BASE} secilen={0} sonuc={DOGRU} />
      </KiroThemeProvider>,
    );
    expect(screen.getByText('Doğru!')).toBeInTheDocument();
    expect(screen.getByText(/mantığı pekiştirelim/)).toBeInTheDocument();
  });

  it('işaretle toggle: aria-pressed + callback', async () => {
    const onT = vi.fn();
    render(
      <KiroThemeProvider theme="paper">
        <QuestionCard {...BASE} secilen={null} onSelect={() => {}} isaretli={false} onToggleIsaret={onT} />
      </KiroThemeProvider>,
    );
    const btn = screen.getByRole('button', { name: 'İşaretle' });
    expect(btn).toHaveAttribute('aria-pressed', 'false');
    await userEvent.click(btn);
    expect(onT).toHaveBeenCalledTimes(1);
  });

  it('axe: etkileşimli temiz', async () => {
    const { container } = render(<Harness />);
    expect(await axe(container)).toHaveNoViolations();
  }, 20000);

  it('axe: review temiz', async () => {
    const { container } = render(
      <KiroThemeProvider theme="paper">
        <QuestionCard {...BASE} secilen={1} sonuc={YANLIS} isaretli onToggleIsaret={() => {}} konuHakimiyet={58} konuTrend="down" />
      </KiroThemeProvider>,
    );
    expect(await axe(container)).toHaveNoViolations();
  }, 20000);
});
