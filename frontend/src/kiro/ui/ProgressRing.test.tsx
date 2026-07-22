import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { describe, it, expect } from 'vitest';

import { ProgressRing } from './ProgressRing';
import { KiroThemeProvider, type KiroTheme } from './theme';

expect.extend(toHaveNoViolations);

const withTheme = (theme: KiroTheme, ui: React.ReactNode) =>
  render(<KiroThemeProvider theme={theme}>{ui}</KiroThemeProvider>);

describe('ProgressRing', () => {
  it('varsayılan etiket olarak yüzdeyi gösterir', () => {
    withTheme('paper', <ProgressRing pct={72} />);
    expect(screen.getByText('%72')).toBeInTheDocument();
    expect(screen.getByRole('img', { name: '%72' })).toBeInTheDocument();
  });

  it('label + sublabel tek erişilebilir isme birleşir', () => {
    withTheme('paper', <ProgressRing pct={64} label="Orta" sublabel="Matematik" />);
    expect(screen.getByText('Orta')).toBeInTheDocument();
    expect(screen.getByText('Matematik')).toBeInTheDocument();
    expect(screen.getByRole('img', { name: /Orta.+Matematik/ })).toBeInTheDocument();
  });

  it('100 üstü pct üst sınıra kısılır', () => {
    withTheme('paper', <ProgressRing pct={150} />);
    expect(screen.getByRole('img', { name: '%100' })).toBeInTheDocument();
  });

  it('negatif pct alt sınıra kısılır', () => {
    withTheme('paper', <ProgressRing pct={-10} />);
    expect(screen.getByRole('img', { name: '%0' })).toBeInTheDocument();
  });

  it('axe: paper yüzey ihlal yok', async () => {
    const { container } = withTheme('paper', <ProgressRing pct={72} sublabel="Bu hafta" />);
    expect(await axe(container)).toHaveNoViolations();
  });

  it('axe: dusk yüzey ihlal yok', async () => {
    const { container } = withTheme('dusk', <ProgressRing pct={82} sublabel="Bu hafta" />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
