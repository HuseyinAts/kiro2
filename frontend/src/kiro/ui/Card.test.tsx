import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { describe, it, expect } from 'vitest';

import { Card } from './Card';
import { KiroThemeProvider, type KiroTheme } from './theme';

expect.extend(toHaveNoViolations);

const withTheme = (theme: KiroTheme, ui: React.ReactNode) =>
  render(<KiroThemeProvider theme={theme}>{ui}</KiroThemeProvider>);

describe('Card', () => {
  it('children içeriğini render eder', () => {
    withTheme('paper', <Card>
      <span>Kart içeriği</span>
    </Card>);
    expect(screen.getByText('Kart içeriği')).toBeInTheDocument();
  });

  it('axe: paper solid ihlal yok', async () => {
    const { container } = withTheme('paper', <Card>
      <p>Metin</p>
    </Card>);
    expect(await axe(container)).toHaveNoViolations();
  });

  it('axe: dusk yüzey ihlal yok', async () => {
    const { container } = withTheme('dusk', <Card variant="dusk">
      <p>Metin</p>
    </Card>);
    expect(await axe(container)).toHaveNoViolations();
  });
});
