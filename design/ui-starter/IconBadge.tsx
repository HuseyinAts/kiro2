import * as React from 'react';
import { color } from '../tokens';

export type IconBadgeTone = 'dawn' | 'success' | 'attention' | 'neutral';

const TONES: Record<IconBadgeTone, { bg: string; fg: string }> = {
  dawn: { bg: '#FFF3EE', fg: color.dawn.coral },
  success: { bg: color.semantic.successBgSoft, fg: color.semantic.success },
  attention: { bg: color.semantic.riskBgSoft, fg: color.semantic.riskTextOnLight },
  neutral: { bg: color.paper.subtle, fg: color.ink.muted },
};

export interface IconBadgeProps {
  /** bespoke inline SVG (stroke 1.8-2.2, round cap/join) — ikon kütüphanesi YOK */
  icon: React.ReactNode;
  tone?: IconBadgeTone;
  size?: number; // 32-56
  radiusPx?: number;
}

export function IconBadge({ icon, tone = 'dawn', size = 40, radiusPx }: IconBadgeProps) {
  const t = TONES[tone];
  return (
    <span aria-hidden="true" style={{ width: size, height: size, flexShrink: 0,
      borderRadius: radiusPx ?? Math.round(size * 0.28),
      backgroundColor: t.bg, color: t.fg,
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
      {icon}
    </span>
  );
}
