import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { describe, it, expect } from 'vitest';

import { Chip } from './Chip';
import { KiroThemeProvider, type KiroTheme } from './theme';

expect.extend(toHaveNoViolations);

const withTheme = (theme: KiroTheme, ui: React.ReactNode) =>
  render(<KiroThemeProvider theme={theme}>{ui}</KiroThemeProvider>);

const paper = (ui: React.ReactNode) => withTheme('paper', ui);

describe('Chip', () => {
  it('status kind label metnini gösterir', () => {
    paper(<Chip label="Sözcük anlamı" />);
    expect(screen.getByText('Sözcük anlamı')).toBeInTheDocument();
  });

  it('streak kind sayı label render eder (tabular numText)', () => {
    paper(<Chip kind="streak" label={7} />);
    expect(screen.getByText('7')).toBeInTheDocument();
  });

  it('tag kind TYT tonu label gösterir', () => {
    paper(<Chip kind="tag" tone="tyt" label="TYT" />);
    expect(screen.getByText('TYT')).toBeInTheDocument();
  });

  it('tag kind AYT tonu label gösterir', () => {
    paper(<Chip kind="tag" tone="ayt" label="AYT" />);
    expect(screen.getByText('AYT')).toBeInTheDocument();
  });

  it('icon prop içeriği render edilir', () => {
    paper(<Chip label="Etiketli" icon={<svg data-testid="ikon" aria-hidden width="12" height="12" />} />);
    expect(screen.getByTestId('ikon')).toBeInTheDocument();
  });

  it('axe: paper status ihlal yok', async () => {
    const { container } = paper(<Chip label="Durum" />);
    expect(await axe(container)).toHaveNoViolations();
  });

  it('axe: dusk status ihlal yok', async () => {
    const { container } = withTheme('dusk', <Chip label="Gece modu" />);
    expect(await axe(container)).toHaveNoViolations();
  });

  it('axe: streak sayı çipi ihlal yok', async () => {
    const { container } = paper(<Chip kind="streak" label={12} />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
