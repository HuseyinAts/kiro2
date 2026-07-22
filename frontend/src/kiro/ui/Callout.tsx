import * as React from 'react';
import { font, radius } from '../tokens';

export type CalloutTone = 'success' | 'attention' | 'dawn';

const TONES: Record<CalloutTone, { bg: string; border: string; fg: string }> = {
  success: { bg: '#ECFDF5', border: '#BBF7D0', fg: '#1E5631' },
  attention: { bg: '#FFFBEB', border: '#FDE9B8', fg: '#854D0E' }, // amber — alarm-kırmızısı YASAK
  dawn: { bg: '#FFF3EE', border: '#F6D9CB', fg: '#C2452B' },
};

export interface CalloutProps {
  tone?: CalloutTone;
  icon?: React.ReactNode;
  children: React.ReactNode;
}

export function Callout({ tone = 'dawn', icon, children }: CalloutProps) {
  const t = TONES[tone];
  return (
    <div style={{ display: 'flex', gap: 11, padding: '12px 13px',
      backgroundColor: t.bg, border: `1px solid ${t.border}`, borderRadius: radius.chip + 2 }}>
      {icon ? <span style={{ flexShrink: 0, marginTop: 1, color: t.fg }}>{icon}</span> : null}
      <span style={{ fontFamily: font.sans, fontSize: 13, color: t.fg, lineHeight: 1.5 }}>{children}</span>
    </div>
  );
}
