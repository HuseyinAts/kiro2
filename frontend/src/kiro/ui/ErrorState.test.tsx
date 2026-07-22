import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { describe, it, expect, vi } from 'vitest';

import { ErrorState } from './ErrorState';
import { KiroThemeProvider, type KiroTheme } from './theme';

expect.extend(toHaveNoViolations);

const withTheme = (theme: KiroTheme, ui: React.ReactNode) =>
  render(<KiroThemeProvider theme={theme}>{ui}</KiroThemeProvider>);

describe('ErrorState', () => {
  it('varsayılan başlık ve güvence metnini gösterir', () => {
    withTheme('paper', <ErrorState />);
    expect(screen.getByText('Veri şu an yüklenemedi.')).toBeInTheDocument();
    expect(screen.getByText(/sorun sende değil/i)).toBeInTheDocument();
  });

  it('onRetry verilince kurtarma butonuna tıklanınca çağrılır', async () => {
    const onRetry = vi.fn();
    withTheme('paper', <ErrorState onRetry={onRetry} />);
    await userEvent.click(screen.getByRole('button', { name: 'Tekrar dene' }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('onRetry yokken kurtarma butonu render edilmez', () => {
    withTheme('paper', <ErrorState />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('özel başlık ve retryLabel gösterilir', () => {
    const onRetry = vi.fn();
    withTheme(
      'paper',
      <ErrorState serifTitle="Bağlantı koptu." retryLabel="Yeniden bağlan" onRetry={onRetry} />
    );
    expect(screen.getByText('Bağlantı koptu.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Yeniden bağlan' })).toBeInTheDocument();
  });

  it('axe: paper ihlal yok', async () => {
    const { container } = withTheme('paper', <ErrorState onRetry={() => {}} />);
    expect(await axe(container)).toHaveNoViolations();
  });

  it('axe: dusk yüzey ihlal yok', async () => {
    const { container } = withTheme('dusk', <ErrorState onRetry={() => {}} />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
