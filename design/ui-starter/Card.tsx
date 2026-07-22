import * as React from 'react';
import { radius, shadow } from '../tokens';
import { useKiroTheme, surf } from './theme';

export interface CardProps {
  variant?: 'solid' | 'dashed' | 'dusk';
  padding?: number;
  radiusSize?: 'card' | 'lg';
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

export function Card({ variant = 'solid', padding = 22, radiusSize = 'card', style, children }: CardProps) {
  const theme = useKiroTheme();
  const s = surf(theme);
  const r = radiusSize === 'lg' ? radius.cardLg : radius.card;

  let look: React.CSSProperties;
  if (variant === 'dusk') {
    look = { backgroundColor: '#2A2433', color: '#fff', borderRadius: r };
  } else if (variant === 'dashed') {
    look = { backgroundColor: s.card, border: `1px dashed ${theme === 'dusk' ? 'rgba(255,240,230,0.22)' : '#E0D8CB'}`, borderRadius: r };
  } else {
    look = { backgroundColor: s.card, border: `1px solid ${s.border}`, borderRadius: r, boxShadow: theme === 'paper' ? shadow.cardSoft : undefined };
  }
  return <div style={{ padding, ...look, ...style }}>{children}</div>;
}
