import { radius } from '../tokens';
import { useKiroTheme, surf } from './theme';

export interface ProgressBarProps {
  /** 0-100 */
  pct: number;
  /** ders rengi — açık panelde tokens.color.subject.light */
  color: string;
  height?: number; // 6-9
}

export function ProgressBar({ pct, color: barColor, height = 8 }: ProgressBarProps) {
  const theme = useKiroTheme();
  const s = surf(theme);
  const clamped = Math.max(0, Math.min(100, pct));
  return (
    <div style={{ height, backgroundColor: s.skeleton, borderRadius: radius.pill, overflow: 'hidden' }}
      role="progressbar" aria-valuenow={clamped} aria-valuemin={0} aria-valuemax={100}>
      <div style={{ height: '100%', width: `${clamped}%`, borderRadius: radius.pill, backgroundColor: barColor }} />
    </div>
  );
}
