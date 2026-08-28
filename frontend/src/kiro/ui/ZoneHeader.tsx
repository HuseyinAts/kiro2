import * as React from 'react';
import { color, font } from '../tokens';

export type ZoneTone = 'promote' | 'safe' | 'demote';

/** sakin modda demote AMBER'dir (Lig §22g) — kırmızı kullanma */
const TONES: Record<ZoneTone, { fg: string; line: string }> = {
  promote: { fg: '#17936B', line: '#D1FAE5' },
  safe: { fg: color.ink.muted, line: color.paper.borderFaint },
  demote: { fg: color.semantic.riskTextOnLight, line: color.semantic.riskBorderSoft },
};

export interface ZoneHeaderProps {
  label: string;
  tone?: ZoneTone;
  icon?: React.ReactNode;
}

export function ZoneHeader({ label, tone = 'safe', icon }: ZoneHeaderProps) {
  const t = TONES[tone];
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      {icon ? <span style={{ color: t.fg, display: 'inline-flex' }}>{icon}</span> : null}
      <span style={{ fontFamily: font.sans, fontSize: 11.5, fontWeight: 800, color: t.fg,
        letterSpacing: '0.04em', textTransform: 'uppercase' }}>{label}</span>
      <div style={{ flex: 1, height: 1, backgroundColor: t.line }} />
    </div>
  );
}
