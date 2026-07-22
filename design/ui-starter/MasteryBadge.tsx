import * as React from 'react';
import { color, font } from '../tokens';
import { useKiroTheme, numText } from './theme';

// Kaynak: KIRO Mastery Rozet.dc.html — tek model, tek rozet.
// Panel · Öğrenme Yolu · Neden Geri Bildirim · Soru Çözme'de AYNI bileşen.
// Kutlama YALNIZ gerçek kademe geçişinde tetiklenir (bu bileşen tetiklemez,
// yalnız gösterir — geçiş kararı sunucu yanıtından gelir).

export type MasteryTier = 'tanidik' | 'yetkin' | 'usta' | 'fethedildi';
export type MasteryTrend = 'up' | 'stable' | 'down';

/** Eşikler kanon: Tanıdık<40 · Yetkin<65 · Usta<85 · Fethedildi≥85 */
export function tierFromPct(pct: number): MasteryTier {
  return pct >= 85 ? 'fethedildi' : pct >= 65 ? 'usta' : pct >= 40 ? 'yetkin' : 'tanidik';
}

/** Açık (paper) yüzey paleti — piksel referansı Mastery Rozet DC'sinden birebir. */
const LIGHT: Record<MasteryTier, { name: string; color: string; bg: string; border: string; glow: string }> = {
  tanidik:    { name: 'Tanıdık',    color: '#6B6478', bg: 'rgba(154,147,165,0.14)', border: '#E0D8CC',               glow: 'rgba(154,147,165,0.5)' },
  yetkin:     { name: 'Yetkin',     color: '#3B6FD4', bg: 'rgba(59,111,212,0.12)',  border: 'rgba(59,111,212,0.32)', glow: 'rgba(59,111,212,0.55)' },
  usta:       { name: 'Usta',       color: '#E0593F', bg: 'rgba(224,89,63,0.12)',   border: 'rgba(224,89,63,0.32)',  glow: 'rgba(224,89,63,0.55)' },
  fethedildi: { name: 'Fethedildi', color: '#C99A2E', bg: 'rgba(201,154,46,0.16)',  border: 'rgba(201,154,46,0.4)',  glow: 'rgba(201,154,46,0.6)' },
};

/** Koyu (dusk) yüzeyde parlak kademe renkleri (tokens.color.mastery). */
const DARK: Record<MasteryTier, { name: string; color: string; bg: string; border: string; glow: string }> = {
  tanidik:    { name: 'Tanıdık',    color: color.mastery.tanidik,    bg: 'rgba(255,255,255,0.06)', border: 'rgba(255,240,230,0.16)', glow: 'rgba(154,147,165,0.5)' },
  yetkin:     { name: 'Yetkin',     color: color.mastery.yetkin,     bg: 'rgba(127,176,255,0.12)', border: 'rgba(127,176,255,0.3)',  glow: 'rgba(127,176,255,0.5)' },
  usta:       { name: 'Usta',       color: color.mastery.usta,       bg: 'rgba(255,174,134,0.12)', border: 'rgba(255,174,134,0.3)',  glow: 'rgba(255,174,134,0.5)' },
  fethedildi: { name: 'Fethedildi', color: color.mastery.fethedildi, bg: 'rgba(252,211,77,0.14)',  border: 'rgba(252,211,77,0.35)',  glow: 'rgba(252,211,77,0.55)' },
};

const TREND = {
  up:     { fill: '#1FB683',  rotate: undefined as string | undefined, opacity: 1 },
  down:   { fill: '#FFB570',  rotate: 'rotate(180deg)', opacity: 1 },   // sıcak amber — alarm değil
  stable: { fill: '#B5AEA2',  rotate: undefined, opacity: 0.4 },
};

export interface MasteryBadgeProps {
  /** 0-100; tier verilmezse buradan türetilir */
  pct: number;
  tier?: MasteryTier;
  /** up = başarılı getirim · down = FSRS yarı-ömrü doluyor (görünür düşüş) */
  trend?: MasteryTrend;
  /** md=30px (satır içi) · lg=34px (canlı vurgular) */
  size?: 'md' | 'lg';
  'aria-label'?: string;
}

export function MasteryBadge({ pct, tier, trend = 'stable', size = 'md', ...rest }: MasteryBadgeProps) {
  const theme = useKiroTheme();
  const t = (theme === 'dusk' ? DARK : LIGHT)[tier ?? tierFromPct(pct)];
  const tr = TREND[trend];
  const h = size === 'lg' ? 34 : 30;
  const fs = size === 'lg' ? 13 : 12.5;
  const mutedPct = theme === 'dusk' ? color.dusk.textSecondary : color.ink.muted;
  return (
    <span
      role="img"
      aria-label={rest['aria-label'] ?? `Hâkimiyet: ${t.name}, yüzde ${pct}, ${trend === 'up' ? 'yükseliyor' : trend === 'down' ? 'geriliyor' : 'sabit'}`}
      style={{ display: 'inline-flex', alignItems: 'center', gap: 8, height: h, padding: '0 12px 0 10px',
        borderRadius: 999, background: t.bg, border: `1px solid ${t.border}`, fontFamily: font.sans }}
    >
      <span aria-hidden style={{ width: 9, height: 9, borderRadius: '50%', background: t.color, boxShadow: `0 0 8px ${t.glow}` }} />
      <span style={{ fontSize: fs, fontWeight: 800, color: t.color }}>{t.name}</span>
      <span style={{ ...numText, fontSize: fs, fontWeight: 700, color: mutedPct }}>%{pct}</span>
      <svg aria-hidden width="12" height="12" viewBox="0 0 24 24" fill={tr.fill}
        style={{ transform: tr.rotate, opacity: tr.opacity, flexShrink: 0 }}>
        <path d="M12 5l7 10H5z" />
      </svg>
    </span>
  );
}
