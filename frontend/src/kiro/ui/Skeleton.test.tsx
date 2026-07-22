import { render, screen, act } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { describe, it, expect, vi, afterEach } from 'vitest';

import { Skeleton } from './Skeleton';
import { KiroThemeProvider } from './theme';

expect.extend(toHaveNoViolations);

const paper = (ui: React.ReactNode) => render(<KiroThemeProvider theme="paper">{ui}</KiroThemeProvider>);

describe('Skeleton', () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('delayMs=0: iskelet anında görünür (layout korunur)', () => {
    const { container } = paper(<Skeleton shape="bar" delayMs={0} />);
    expect(container.querySelector('.kiro-skel')).not.toBeNull();
  });

  it('delayMs=400: ilk anda görünmez, süre dolunca görünür', () => {
    vi.useFakeTimers();
    const { container } = paper(<Skeleton shape="bar" delayMs={400} />);
    // 400ms dolmadan iskelet DOM'da yok
    expect(container.querySelector('.kiro-skel')).toBeNull();
    act(() => {
      vi.advanceTimersByTime(400);
    });
    expect(container.querySelector('.kiro-skel')).not.toBeNull();
  });

  it('shape=card slowAfterMs=50: süre dolunca güvence satırı + mantra (role="status") belirir', () => {
    vi.useFakeTimers();
    paper(<Skeleton shape="card" delayMs={0} slowAfterMs={50} />);
    // güvence satırı henüz bekliyor
    expect(screen.queryByRole('status')).toBeNull();
    act(() => {
      vi.advanceTimersByTime(50);
    });
    const status = screen.getByRole('status');
    expect(status).toBeInTheDocument();
    expect(status.textContent).toMatch(/uzun sürdü/i);
  });

  it('prefers-reduced-motion ortamında geometri yine render edilir', () => {
    vi.stubGlobal(
      'matchMedia',
      vi.fn().mockImplementation((query: string) => ({
        matches: true,
        media: query,
        onchange: null,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        addListener: vi.fn(),
        removeListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }))
    );
    const { container } = paper(<Skeleton shape="card" delayMs={0} slowAfterMs={null} />);
    expect(container.querySelector('.kiro-skel')).not.toBeNull();
  });

  it('axe: erişilebilirlik ihlali yok (card + süpürme)', async () => {
    const { container } = paper(<Skeleton shape="card" delayMs={0} slowAfterMs={null} sweep />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
