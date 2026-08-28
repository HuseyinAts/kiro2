import * as React from 'react';
import { font } from '../tokens';

// Kaynak: KIRO2 Odevlerim.dc.html — ödev durumu pili.
// KANON: geciken ödev "eksik" DEĞİL, "bekliyor"dur (amber, alarm-kırmızısı asla).
// "eksik" kelimesi hiçbir katmanda yok — kopyada da, kodda da.

export type OdevDurum = 'acik' | 'bekliyor' | 'tamam';

const CHIP: Record<OdevDurum, { bg: string; fg: string; label: string }> = {
  acik:     { bg: '#FFF3EE', fg: '#C2452B', label: 'Açık' },     // coral METİN (sıkı-AA açık zeminde)
  bekliyor: { bg: '#FBF0DE', fg: '#9A5D0D', label: 'Bekliyor' }, // amber METİN (sıkı-AA)
  tamam:    { bg: '#E4F7F0', fg: '#17936B', label: 'Tamam' },
};

export interface StatusChipProps {
  durum: OdevDurum;
  /** Örn. "2 gün" → "Açık · 2 gün" (yalnız acik durumunda gösterilir) */
  kalan?: string;
}

export function StatusChip({ durum, kalan }: StatusChipProps) {
  const c = CHIP[durum];
  const label = durum === 'acik' && kalan ? `${c.label} · ${kalan}` : c.label;
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', fontFamily: font.sans,
      fontSize: 11, fontWeight: 800, letterSpacing: '0.04em', textTransform: 'uppercase',
      padding: '3px 9px', borderRadius: 999, background: c.bg, color: c.fg }}>
      {label}
    </span>
  );
}
