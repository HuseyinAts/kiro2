/**
 * useAccessibilityStyles — settingsStore → CSS custom properties sync
 *
 * Reads fontSize, lineHeight, highContrast from Zustand settingsStore
 * and applies them as CSS variables on <html> so the entire app reflects
 * the user's accessibility preferences.
 *
 * Call once in App.tsx or a top-level layout component.
 */

import { useEffect } from 'react';
import { useSettingsStore } from '../store/settingsStore';

export function useAccessibilityStyles(): void {
  const fontSize = useSettingsStore((s) => s.accessibility.fontSize);
  const lineHeight = useSettingsStore((s) => s.accessibility.lineHeight);
  const highContrast = useSettingsStore((s) => s.accessibility.highContrast);

  useEffect(() => {
    const root = document.documentElement;
    root.style.setProperty('--font-size-base', `${fontSize}px`);
    root.style.setProperty('--line-height', `${lineHeight}`);

    if (highContrast) {
      root.classList.add('high-contrast');
    } else {
      root.classList.remove('high-contrast');
    }
  }, [fontSize, lineHeight, highContrast]);
}

export default useAccessibilityStyles;
