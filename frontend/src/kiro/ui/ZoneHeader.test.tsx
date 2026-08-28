import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { describe, it, expect } from 'vitest';

import { ZoneHeader } from './ZoneHeader';
import { KiroThemeProvider, type KiroTheme } from './theme';

expect.extend(toHaveNoViolations);

const withTheme = (theme: KiroTheme, ui: React.ReactNode) =>
  render(<KiroThemeProvider theme={theme}>{ui}</KiroThemeProvider>);

describe('ZoneHeader', () => {
  it('label metnini gösterir', () => {
    withTheme('paper', <ZoneHeader label="Yükselen konular" />);
    expect(screen.getByText('Yükselen konular')).toBeInTheDocument();
  });

  it('demote tonu amber renk uygular (alarm-kırmızısı değil)', () => {
    withTheme('paper', <ZoneHeader label="Tekrar bekleyen" tone="demote" />);
    expect(screen.getByText('Tekrar bekleyen')).toHaveStyle({ color: '#9A5D0D' });
  });

  it('icon verildiğinde render eder', () => {
    withTheme(
      'paper',
      <ZoneHeader
        label="Yükselen konular"
        tone="promote"
        icon={<svg data-testid="zone-ikon" aria-hidden width="14" height="14" />}
      />
    );
    expect(screen.getByTestId('zone-ikon')).toBeInTheDocument();
  });

  it('KANON: demote tonu absence-dili taşımaz, bekleme dili kullanır', () => {
    withTheme('paper', <ZoneHeader label="Tekrar bekleyen" tone="demote" />);
    expect(screen.getByText('Tekrar bekleyen')).toBeInTheDocument();
    expect(screen.queryByText(/eksik/i)).not.toBeInTheDocument();
  });

  it('axe: paper ihlal yok', async () => {
    const { container } = withTheme('paper', <ZoneHeader label="Bugünkü akış" />);
    expect(await axe(container)).toHaveNoViolations();
  });

  it('axe: dusk yüzey ihlal yok', async () => {
    const { container } = withTheme('dusk', <ZoneHeader label="Bu haftaki ritüel" tone="promote" />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
