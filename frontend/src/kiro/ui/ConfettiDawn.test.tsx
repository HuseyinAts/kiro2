import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

import { useAyar, resetAyar } from '../lib/ayarStore';
import { ConfettiDawn } from './ConfettiDawn';
import { KiroThemeProvider } from './theme';

expect.extend(toHaveNoViolations);

const paper = (ui: React.ReactNode) => render(<KiroThemeProvider theme="paper">{ui}</KiroThemeProvider>);

const originalMatchMedia = window.matchMedia;

function setReducedMotion(reduce: boolean) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: reduce && query.includes('prefers-reduced-motion'),
    media: query,
    onchange: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
}

describe('ConfettiDawn', () => {
  beforeEach(() => {
    setReducedMotion(false);
    resetAyar();
  });
  afterEach(() => {
    window.matchMedia = originalMatchMedia;
    resetAyar();
  });

  it('konfeti parçalarını count kadar render eder', () => {
    const { container } = paper(<ConfettiDawn count={5} />);
    const overlay = container.firstChild as HTMLElement;
    expect(overlay).toHaveAttribute('aria-hidden');
    expect(overlay.querySelectorAll('div')).toHaveLength(5);
  });

  it('dekoratif katman pointer-events almaz (etkileşimi engellemez)', () => {
    const { container } = paper(<ConfettiDawn count={3} />);
    const overlay = container.firstChild as HTMLElement;
    expect(overlay.style.pointerEvents).toBe('none');
  });

  it('azaltılmış hareket tercihinde konfeti render edilmez', () => {
    setReducedMotion(true);
    const { container } = paper(<ConfettiDawn count={12} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('sakin mod açıkken (calmMode) OS tercihi olmasa da konfeti render edilmez', () => {
    setReducedMotion(false);
    useAyar.getState().setCalmMode(true);
    const { container } = paper(<ConfettiDawn count={12} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = paper(<ConfettiDawn count={6} />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
