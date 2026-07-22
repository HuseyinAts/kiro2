import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { describe, it, expect } from 'vitest';

import { ProgressBar } from './ProgressBar';
import { KiroThemeProvider, type KiroTheme } from './theme';

expect.extend(toHaveNoViolations);

// Ders renkleri (tokens.color.subject) — canon-guvenli hex
const MAT = '#3B82F6';
const BIY = '#1FB683';
const FIZ_DUSK = '#A77BFF';

const wrapper = (theme: KiroTheme) =>
  function Wrap({ children }: { children: React.ReactNode }) {
    return <KiroThemeProvider theme={theme}>{children}</KiroThemeProvider>;
  };

describe('ProgressBar', () => {
  it('pct degerini aria-valuenow + valuemin/valuemax olarak yansitir', () => {
    render(<ProgressBar pct={45} color={MAT} />, { wrapper: wrapper('paper') });
    const bar = screen.getByRole('progressbar');
    expect(bar).toHaveAttribute('aria-valuenow', '45');
    expect(bar).toHaveAttribute('aria-valuemin', '0');
    expect(bar).toHaveAttribute('aria-valuemax', '100');
  });

  it('pct=0 ve pct=100 sinir degerlerini aynen korur', () => {
    const { rerender } = render(<ProgressBar pct={0} color={BIY} />, { wrapper: wrapper('paper') });
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0');
    rerender(<ProgressBar pct={100} color={BIY} />);
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '100');
  });

  it('aralik disi pct 0-100 araligina kirpilir', () => {
    const { rerender } = render(<ProgressBar pct={140} color={MAT} />, { wrapper: wrapper('paper') });
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '100');
    rerender(<ProgressBar pct={-25} color={MAT} />);
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0');
  });

  it('dusk yuzeyde de progressbar rolunu render eder', () => {
    render(<ProgressBar pct={68} color={FIZ_DUSK} />, { wrapper: wrapper('dusk') });
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '68');
  });

  it('ariaLabel role=progressbar için erişilebilir ad sağlar', () => {
    render(<ProgressBar pct={45} color={MAT} ariaLabel="Matematik ilerlemesi" />, { wrapper: wrapper('paper') });
    expect(screen.getByRole('progressbar', { name: 'Matematik ilerlemesi' })).toBeInTheDocument();
  });

  it('axe: erişilebilirlik ihlali yok (ariaLabel ile, kural dışlaması YOK)', async () => {
    const { container } = render(
      <ProgressBar pct={45} color={MAT} ariaLabel="Matematik ilerlemesi" />,
      { wrapper: wrapper('paper') }
    );
    expect(await axe(container)).toHaveNoViolations();
  });
});
