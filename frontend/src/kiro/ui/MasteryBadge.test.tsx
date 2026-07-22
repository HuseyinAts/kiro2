import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { describe, it, expect } from 'vitest';

import { MasteryBadge, tierFromPct } from './MasteryBadge';
import { KiroThemeProvider, type KiroTheme } from './theme';

expect.extend(toHaveNoViolations);

const withTheme = (theme: KiroTheme, ui: React.ReactNode) =>
  render(<KiroThemeProvider theme={theme}>{ui}</KiroThemeProvider>);

const paper = (ui: React.ReactNode) => withTheme('paper', ui);

describe('MasteryBadge', () => {
  it('kademe adını ve yüzdeyi gösterir', () => {
    paper(<MasteryBadge tier="usta" pct={72} trend="up" />);
    expect(screen.getByText('Usta')).toBeInTheDocument();
    expect(screen.getByText('%72')).toBeInTheDocument();
  });

  it('role=img erişilebilir isim hâkimiyet durumunu taşır', () => {
    paper(<MasteryBadge tier="yetkin" pct={52} trend="down" />);
    expect(screen.getByRole('img', { name: /Yetkin, yüzde 52, geriliyor/ })).toBeInTheDocument();
  });

  it('tierFromPct eşik kanonuna uyar', () => {
    expect(tierFromPct(28)).toBe('tanidik');
    expect(tierFromPct(52)).toBe('yetkin');
    expect(tierFromPct(72)).toBe('usta');
    expect(tierFromPct(92)).toBe('fethedildi');
  });

  it('tier verilmezse yüzdeden türetilir', () => {
    paper(<MasteryBadge pct={90} />);
    expect(screen.getByText('Fethedildi')).toBeInTheDocument();
  });

  it('KANON: geriye yön absence-dili değil yön dili kullanır', () => {
    paper(<MasteryBadge tier="usta" pct={78} trend="down" />);
    expect(screen.getByRole('img', { name: /geriliyor/ })).toBeInTheDocument();
    expect(screen.queryByText(/eksik/i)).not.toBeInTheDocument();
  });

  it('axe: paper ihlal yok', async () => {
    const { container } = paper(<MasteryBadge tier="usta" pct={72} trend="up" />);
    expect(await axe(container)).toHaveNoViolations();
  });

  it('axe: dusk yüzey ihlal yok', async () => {
    const { container } = withTheme('dusk', <MasteryBadge tier="fethedildi" pct={92} trend="up" />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
