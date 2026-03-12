/**
 * useReducedMotion — Framer Motion + CSS animasyonları kontrol et
 *
 * settingsStore.reduceMotion (kullanıcı tercihi) VEYA
 * OS prefers-reduced-motion (sistem tercihi) aktifse true döner.
 *
 * Side-effect: documentElement'e .reduced-motion CSS class ekler/kaldırır
 * (accessibility.css'teki kural: tüm CSS transition/animation'ları sıfırlar)
 */

import { useEffect } from 'react';
import { useSettingsStore } from '../store/settingsStore';

export function useReducedMotion(): boolean {
  const reduceMotion = useSettingsStore((s) => s.accessibility.reduceMotion);

  // Apply .reduced-motion CSS class to <html> element
  useEffect(() => {
    const root = document.documentElement;
    if (reduceMotion) {
      root.classList.add('reduced-motion');
    } else {
      root.classList.remove('reduced-motion');
    }
  }, [reduceMotion]);

  return reduceMotion;
}

/**
 * Framer Motion'da kullanım için: reduceMotion true ise animasyon yerine
 * anında geçiş yapan variant döner.
 */
export function useMotionProps(reduceMotion: boolean) {
  if (reduceMotion) {
    return {
      initial: false as const,
      animate: undefined,
      exit: undefined,
      transition: { duration: 0 },
    };
  }
  return {};
}

export default useReducedMotion;
