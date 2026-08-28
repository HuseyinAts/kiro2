import { render, act } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';

import { KiroThemeProvider } from './theme';
import { useAyar, resetAyar } from '../lib/ayarStore';

// KiroThemeProvider artık calmMode'u GLOBAL bağlar: kök <html>'e .k-calm ekler
// (tokens.css bloğu CSS-@media ambient motion'ı da kısar). Test izolasyonu zorunlu.
beforeEach(() => resetAyar());
afterEach(() => resetAyar());

describe('KiroThemeProvider — sakin mod (calmMode) global CSS wiring', () => {
  it('calmMode false iken kök <html> .k-calm taşımaz (mevcut davranış değişmez)', () => {
    render(
      <KiroThemeProvider theme="paper">
        <span>x</span>
      </KiroThemeProvider>
    );
    expect(document.documentElement.classList.contains('k-calm')).toBe(false);
  });

  it('calmMode true iken kök <html> .k-calm sınıfı kazanır (CSS-ambient motion kısılır)', () => {
    render(
      <KiroThemeProvider theme="paper">
        <span>x</span>
      </KiroThemeProvider>
    );
    act(() => useAyar.getState().setCalmMode(true));
    expect(document.documentElement.classList.contains('k-calm')).toBe(true);
  });

  it('calmMode kapatılınca .k-calm kaldırılır', () => {
    render(
      <KiroThemeProvider theme="paper">
        <span>x</span>
      </KiroThemeProvider>
    );
    act(() => useAyar.getState().setCalmMode(true));
    expect(document.documentElement.classList.contains('k-calm')).toBe(true);
    act(() => useAyar.getState().setCalmMode(false));
    expect(document.documentElement.classList.contains('k-calm')).toBe(false);
  });
});
