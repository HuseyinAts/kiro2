import * as React from 'react';
import { color, font } from '../tokens';
import { useAyar } from '../lib/ayarStore';

/** Tema = ekran TÜRÜ (çalışma=paper, duygusal=dusk). Kullanıcı toggle'ı DEĞİL. */
export type KiroTheme = 'paper' | 'dusk';

const ThemeCtx = React.createContext<KiroTheme>('paper');

export function KiroThemeProvider(props: { theme: KiroTheme; children: React.ReactNode }) {
  // Sakin mod GLOBAL: useReducedMotion (JS store) yalnız JS-motion'ı kısar; CSS-@media
  // ambient motion (Skeleton kiroSweep, konfeti keyframe'leri) store'u göremez. Kök
  // <html>'e .k-calm eklenince tokens.css'teki blok CSS-ambient motion'ı da etkisizler.
  // ADDITIVE: calmMode default false → sınıf yok → mevcut davranış değişmez.
  const calmMode = useAyar((s) => s.calmMode);
  const kulturelTema = useAyar((s) => s.kulturelTema);
  React.useEffect(() => {
    if (typeof document === 'undefined') return undefined;
    const root = document.documentElement;
    root.classList.toggle('k-calm', calmMode);
    
    // Temizle ve yeni temayı ekle
    const toRemove: string[] = [];
    root.classList.forEach((cls) => {
      if (cls.startsWith('k-') && cls !== 'k-calm') toRemove.push(cls);
    });
    if (toRemove.length > 0) root.classList.remove(...toRemove);
    
    root.classList.add(`k-${kulturelTema}`);

    return () => root.classList.remove('k-calm', `k-${kulturelTema}`);
  }, [calmMode, kulturelTema]);
  return React.createElement(ThemeCtx.Provider, { value: props.theme }, props.children);
}

export function useKiroTheme(): KiroTheme {
  return React.useContext(ThemeCtx);
}

/** Temaya göre yüzey token'ları — bileşenler ham hex yerine bunu okur. */
export function surf(theme: KiroTheme) {
  return theme === 'dusk'
    ? {
        bg: color.dusk.bg,
        card: color.dusk.bg2,
        subtle: 'rgba(255,255,255,0.06)',
        border: 'rgba(255,240,230,0.16)',
        borderFaint: 'rgba(255,240,230,0.1)',
        text: color.dusk.text,
        text2: color.dusk.text2,
        muted: color.dusk.textSecondary,
        skeleton: 'rgba(255,255,255,0.1)',
        skeletonSoft: 'rgba(255,255,255,0.06)',
      }
    : {
        bg: color.paper.bg,
        card: color.paper.card,
        subtle: color.paper.subtle,
        border: color.paper.border,
        borderFaint: color.paper.borderFaint,
        text: color.ink.primary,
        text2: color.ink.secondary,
        muted: color.ink.muted,
        skeleton: color.paper.border,
        skeletonSoft: color.paper.borderFaint,
      };
}

export const baseText: React.CSSProperties = { fontFamily: font.sans };
/** Sayı gösteren HER metne uygula */
export const numText: React.CSSProperties = { fontFamily: font.sans, fontVariantNumeric: 'tabular-nums' };
export const serifText: React.CSSProperties = { fontFamily: font.serif, fontStyle: 'italic' };
