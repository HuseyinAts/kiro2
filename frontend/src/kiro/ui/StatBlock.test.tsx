import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { describe, it, expect } from 'vitest';

import { StatBlock } from './StatBlock';
import { KiroThemeProvider } from './theme';

expect.extend(toHaveNoViolations);

const paper = (ui: React.ReactNode) => render(<KiroThemeProvider theme="paper">{ui}</KiroThemeProvider>);
const dusk = (ui: React.ReactNode) => render(<KiroThemeProvider theme="dusk">{ui}</KiroThemeProvider>);

describe('StatBlock', () => {
  it('value ve label birlikte render eder', () => {
    paper(<StatBlock value={1284} label="Çözülen soru" />);
    expect(screen.getByText('1284')).toBeInTheDocument();
    expect(screen.getByText('Çözülen soru')).toBeInTheDocument();
  });

  it('delta verilince gösterilir', () => {
    paper(<StatBlock value={12} label="Seri gün" delta="+48" />);
    expect(screen.getByText('+48')).toBeInTheDocument();
  });

  it('delta yoksa delta düğümü render edilmez', () => {
    paper(<StatBlock value={12} label="Seri gün" />);
    expect(screen.queryByText('+48')).not.toBeInTheDocument();
  });

  it('axe: paper yüzey ihlal yok', async () => {
    const { container } = paper(<StatBlock value={92} label="Başarı oranı" delta="+3" />);
    expect(await axe(container)).toHaveNoViolations();
  });

  it('axe: dusk yüzey ihlal yok', async () => {
    const { container } = dusk(<StatBlock value={7} label="Seri gün" />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
