import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { describe, it, expect } from 'vitest';

import { IconBadge } from './IconBadge';
import { KiroThemeProvider } from './theme';

expect.extend(toHaveNoViolations);

const paper = (ui: React.ReactNode) => render(<KiroThemeProvider theme="paper">{ui}</KiroThemeProvider>);

// Bespoke inline SVG (kanon: lucide/emoji YOK; stroke 2.1 round-cap)
const BadgeIcon = () => (
  <svg data-testid="badge-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" aria-hidden>
    <path d="M5 13l4 4L19 7" />
  </svg>
);

describe('IconBadge', () => {
  it('geçirilen bespoke ikonu render eder', () => {
    paper(<IconBadge icon={<BadgeIcon />} />);
    expect(screen.getByTestId('badge-icon')).toBeInTheDocument();
  });

  it('dekoratif kabuk aria-hidden ve verilen boyutu taşır', () => {
    const { container } = paper(<IconBadge icon={<BadgeIcon />} size={56} />);
    const shell = container.querySelector('span');
    expect(shell).toHaveAttribute('aria-hidden', 'true');
    expect(shell).toHaveStyle({ width: '56px', height: '56px' });
  });

  it('KANON: attention tonu amber taşır (alarm-kırmızısı değil)', () => {
    const { container } = paper(<IconBadge icon={<BadgeIcon />} tone="attention" />);
    const shell = container.querySelector('span');
    expect(shell).toHaveStyle({ color: '#9A5D0D' });
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = paper(<IconBadge icon={<BadgeIcon />} tone="success" />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
