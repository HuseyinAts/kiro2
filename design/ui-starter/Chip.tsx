import * as React from 'react';
import { color, font, radius } from '../tokens';
import { useKiroTheme, surf, numText } from './theme';

export interface ChipProps {
  kind?: 'streak' | 'tag' | 'status';
  label: string | number;
  icon?: React.ReactNode;
  /** tag için: 'tyt' | 'ayt' */
  tone?: 'tyt' | 'ayt';
}

/** Seri çipi (alev+sayı) · TYT/AYT etiketi · durum pili */
export function Chip({ kind = 'status', label, icon, tone }: ChipProps) {
  const theme = useKiroTheme();
  const s = surf(theme);

  if (kind === 'streak') {
    return (
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7, height: 38, padding: '0 12px',
        backgroundColor: color.semantic.riskBgSoft, border: `1px solid ${color.semantic.riskBorderSoft}`, borderRadius: radius.chip }}>
        {icon}
        <span style={{ ...numText, fontWeight: 800, fontSize: 14, color: color.semantic.riskTextOnLight }}>{label}</span>
      </span>
    );
  }
  if (kind === 'tag') {
    const ayt = tone === 'ayt';
    return (
      <span style={{ display: 'inline-flex', alignItems: 'center', height: 18, padding: '0 7px', borderRadius: 6,
        backgroundColor: ayt ? color.semantic.riskBgSoft : '#EEF3F8',
        color: ayt ? color.semantic.riskTextOnLight : '#5A6B82',
        fontFamily: font.sans, fontSize: 10, fontWeight: 800, letterSpacing: '0.04em' }}>
        {label}
      </span>
    );
  }
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '5px 11px', borderRadius: radius.pill,
      backgroundColor: s.subtle, border: `1px solid ${s.borderFaint}`,
      fontFamily: font.sans, fontSize: 11.5, fontWeight: 700, color: s.muted }}>
      {icon}
      {label}
    </span>
  );
}
