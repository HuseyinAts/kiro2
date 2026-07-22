import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { describe, it, expect } from 'vitest';

import { StatusChip } from './StatusChip';
import { KiroThemeProvider } from './theme';

expect.extend(toHaveNoViolations);

const paper = (ui: React.ReactNode) => render(<KiroThemeProvider theme="paper">{ui}</KiroThemeProvider>);

describe('StatusChip', () => {
  it('acik durumu "Açık" gösterir', () => {
    paper(<StatusChip durum="acik" />);
    expect(screen.getByText('Açık')).toBeInTheDocument();
  });

  it('tamam durumu "Tamam" gösterir', () => {
    paper(<StatusChip durum="tamam" />);
    expect(screen.getByText('Tamam')).toBeInTheDocument();
  });

  it('acik + kalan → "Açık · 2 gün"', () => {
    paper(<StatusChip durum="acik" kalan="2 gün" />);
    expect(screen.getByText('Açık · 2 gün')).toBeInTheDocument();
  });

  it('KANON: geciken durum Bekliyor gösterir, absence-dili yok', () => {
    paper(<StatusChip durum="bekliyor" />);
    expect(screen.getByText('Bekliyor')).toBeInTheDocument();
    expect(screen.queryByText(/eksik/i)).not.toBeInTheDocument();
  });

  it('axe: ihlal yok', async () => {
    const { container } = paper(<StatusChip durum="bekliyor" />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
