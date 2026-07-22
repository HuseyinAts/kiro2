import * as React from 'react';
import { color, font } from '../tokens';
import { useKiroTheme, surf, numText } from './theme';

export interface StatBlockProps {
  value: string | number;
  label: string;
  /** ör. '+48' — yeşil gösterilir */
  delta?: string;
  /** değerin rengi (tokens'tan) */
  tone?: string;
}

/** Büyük tabular sayı + alt etiket (KPI / hero stat) */
export function StatBlock({ value, label, delta, tone }: StatBlockProps) {
  const theme = useKiroTheme();
  const s = surf(theme);
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <span style={{ ...numText, fontSize: 28, fontWeight: 800, lineHeight: 1, color: tone ?? s.text }}>{value}</span>
        {delta ? <span style={{ fontFamily: font.sans, fontSize: 12, fontWeight: 700, color: color.semantic.success }}>{delta}</span> : null}
      </div>
      <div style={{ fontFamily: font.sans, fontSize: 12.5, fontWeight: 600, color: s.muted, marginTop: 6 }}>{label}</div>
    </div>
  );
}
