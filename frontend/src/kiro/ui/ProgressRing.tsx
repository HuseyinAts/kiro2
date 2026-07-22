import { color } from '../tokens';
import { useKiroTheme, surf, numText } from './theme';

export interface ProgressRingProps {
  /** 0-100 */
  pct: number;
  size?: number;      // px, ör. 72 / 148
  strokeWidth?: number;
  ringColor?: string; // varsayılan dawn coral
  label?: string;     // ortadaki büyük metin (varsayılan %pct)
  sublabel?: string;
}

export function ProgressRing({ pct, size = 72, strokeWidth = 8, ringColor = color.dawn.coral, label, sublabel }: ProgressRingProps) {
  const theme = useKiroTheme();
  const s = surf(theme);
  const clamped = Math.max(0, Math.min(100, pct));
  const r = (size - strokeWidth * 2) / 2;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - clamped / 100);
  const cx = size / 2;
  return (
    <div style={{ position: 'relative', width: size, height: size }} role="img" aria-label={`${label ?? `%${clamped}`}${sublabel ? ` — ${sublabel}` : ''}`}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={cx} cy={cx} r={r} fill="none" stroke={s.skeleton} strokeWidth={strokeWidth} />
        <circle cx={cx} cy={cx} r={r} fill="none" stroke={ringColor} strokeWidth={strokeWidth}
          strokeLinecap="round" strokeDasharray={c} strokeDashoffset={offset} transform={`rotate(-90 ${cx} ${cx})`} />
      </svg>
      <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ ...numText, fontSize: size / 4.5, fontWeight: 800, color: s.text, lineHeight: 1 }}>{label ?? `%${clamped}`}</span>
        {sublabel ? <span style={{ fontSize: 11, fontWeight: 600, color: s.muted, marginTop: 3 }}>{sublabel}</span> : null}
      </div>
    </div>
  );
}
