import * as React from 'react';
import { color, font, radius, shadow, hit } from '../tokens';
import { useKiroTheme, surf } from './theme';

export interface ButtonProps {
  variant?: 'primary' | 'ghost' | 'goldDark';
  size?: 'md' | 'lg';
  icon?: React.ReactNode;
  disabled?: boolean;
  onClick?: () => void;
  /** İkon-yalnız kullanımda zorunlu */
  ariaLabel?: string;
  children?: React.ReactNode;
}

export function Button({ variant = 'primary', size = 'md', icon, disabled, onClick, ariaLabel, children }: ButtonProps) {
  const theme = useKiroTheme();
  const s = surf(theme);
  const h = size === 'lg' ? 48 : 40;

  const base: React.CSSProperties = {
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 8,
    height: h, minHeight: variant === 'ghost' ? h : undefined, padding: size === 'lg' ? '0 22px' : '0 16px',
    borderRadius: size === 'lg' ? radius.button : radius.input,
    fontFamily: font.sans, fontSize: size === 'lg' ? 14.5 : 13.5, fontWeight: 800,
    border: 'none', cursor: disabled ? 'default' : 'pointer',
    minWidth: hit.minTarget,
  };

  let look: React.CSSProperties;
  if (disabled) {
    look = { backgroundColor: color.paper.borderFaint, color: color.ink.faded3 };
  } else if (variant === 'primary') {
    look = { backgroundColor: color.dawn.coralCtaBg, color: '#fff', boxShadow: shadow.coralCta };
  } else if (variant === 'goldDark') {
    // Yalnız KOYU ekranlarda kullan
    look = { background: `linear-gradient(110deg, ${color.dawn.gold2}, ${color.dawn.gold})`, color: '#2A1810' };
  } else {
    look = { backgroundColor: s.card, color: s.text2, border: `1px solid ${s.border}`, fontWeight: 700 };
  }

  return (
    <button type="button" aria-label={ariaLabel} disabled={disabled} onClick={onClick} style={{ ...base, ...look }}>
      {icon}
      {children}
    </button>
  );
}
