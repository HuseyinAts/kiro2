import * as React from 'react';
import { font, radius } from '../tokens';
import { useKiroTheme, surf, serifText } from './theme';

/**
 * "Yönlendiren boşluk" (KIRO Durumlar §2):
 * serif tek cümle İYİ haberi verir, gövde akran sesiyle açıklar, tek CTA sıradaki adım.
 * "Henüz hiçbir şey yok" gibi eksiklik dili YASAK.
 */
export interface EmptyStateProps {
  icon?: React.ReactNode;
  serifTitle: string;
  body?: string;
  action?: React.ReactNode; // <Button variant="primary">…</Button>
}

export function EmptyState({ icon, serifTitle, body, action }: EmptyStateProps) {
  const theme = useKiroTheme();
  const s = surf(theme);
  return (
    <div style={{ border: `1px dashed ${theme === 'dusk' ? 'rgba(255,240,230,0.22)' : '#E0D8CB'}`,
      backgroundColor: s.card, borderRadius: radius.cardLg, padding: '36px 26px',
      display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: 10 }}>
      {icon}
      <div style={{ ...serifText, fontSize: 21, color: s.text, lineHeight: 1.25 }}>{serifTitle}</div>
      {body ? <p style={{ margin: 0, fontFamily: font.sans, fontSize: 13, color: s.muted, maxWidth: 360, lineHeight: 1.6 }}>{body}</p> : null}
      {action ? <div style={{ marginTop: 6 }}>{action}</div> : null}
    </div>
  );
}
