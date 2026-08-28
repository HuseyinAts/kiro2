import * as React from 'react';
import { radius } from '../tokens';
import { useKiroTheme, surf } from './theme';

/**
 * Zıplamayan iskelet (KIRO Durumlar §1 — şafak kişiliği):
 * - gerçek düzenin geometrisini koru (layout shift yok)
 * - 1,6s sakin nabız + kart yüzeyinde 2,6s'de bir geçen "şafak süpürmesi" (tek ışık, soldan doğar)
 * - prefers-reduced-motion'da nabız da süpürme de statik
 * - 400ms'ten kısa yüklemede HİÇ gösterme (delayMs)
 * - 3sn'yi aşan yüklemede güvence satırı + gün-seed'li ONAYLI mantra (telaş değil, marka nefesi)
 */

/** Onaylı havuz — KIRO Safak.dc.html ile birebir (KARARLAR 2026-07-21). Değişiklik = kullanıcı onayı. */
const MANTRA = [
  'Sınav bir günü ölçer. Sen çok daha fazlasısın.',
  'Küçük adım, her gün.',
  'Dünkü senden bir adım önde.',
  'Acele etme; istikrar yetenektir.',
  'Bu yol tuğla tuğla örülür.',
];
function gunMantrasi(): string {
  const g = new Date();
  return MANTRA[(g.getFullYear() * 372 + g.getMonth() * 31 + g.getDate()) % MANTRA.length];
}

let injected = false;
function injectKeyframes() {
  if (injected || typeof document === 'undefined') return;
  const st = document.createElement('style');
  st.textContent =
    '@keyframes kiroSkel{0%,100%{opacity:1}50%{opacity:.55}}' +
    '@keyframes kiroSweep{from{background-position:130% 0}to{background-position:-130% 0}}' +
    '@media (prefers-reduced-motion: reduce){.kiro-skel,.kiro-sweep{animation:none!important}}';
  document.head.appendChild(st);
  injected = true;
}

export interface SkeletonProps {
  shape?: 'bar' | 'row' | 'card';
  width?: number | string;
  height?: number;
  /** iskeletin görünmeden önce bekleyeceği süre (ms) */
  delayMs?: number;
  /** şafak süpürmesi (yalnız shape="card"; dekoratif — RM'de durur) */
  sweep?: boolean;
  /** bu süreyi aşan yüklemede "Biraz uzun sürdü…" + gün mantrası (yalnız shape="card"); null = kapalı */
  slowAfterMs?: number | null;
}

export function Skeleton({ shape = 'bar', width = '100%', height, delayMs = 400, sweep = true, slowAfterMs = 3000 }: SkeletonProps) {
  const theme = useKiroTheme();
  const s = surf(theme);
  const dusk = theme === 'dusk';
  const [show, setShow] = React.useState(delayMs === 0);
  const [slow, setSlow] = React.useState(false);
  React.useEffect(() => {
    injectKeyframes();
    const ts: ReturnType<typeof setTimeout>[] = [];
    if (delayMs > 0) ts.push(setTimeout(() => setShow(true), delayMs));
    if (slowAfterMs != null && shape === 'card') ts.push(setTimeout(() => setSlow(true), slowAfterMs));
    return () => ts.forEach(clearTimeout);
  }, [delayMs, slowAfterMs, shape]);
  if (!show) return null;

  const anim: React.CSSProperties = { animation: 'kiroSkel 1.6s ease-in-out infinite' };
  if (shape === 'row') {
    return (
      <div className="kiro-skel" style={{ display: 'flex', alignItems: 'center', gap: 10, ...anim }}>
        <div style={{ width: 32, height: 32, borderRadius: 9, backgroundColor: s.skeleton }} />
        <div style={{ flex: 1, height: 11, borderRadius: 6, backgroundColor: s.skeleton }} />
      </div>
    );
  }
  if (shape === 'card') {
    return (
      <div style={{ position: 'relative', overflow: 'hidden' }}>
        {sweep && (
          <div
            className="kiro-sweep"
            aria-hidden
            style={{
              position: 'absolute',
              inset: 0,
              pointerEvents: 'none',
              background: `linear-gradient(100deg, transparent 38%, ${dusk ? 'rgba(255,180,140,0.10)' : 'rgba(224,137,90,0.09)'} 50%, transparent 62%)`,
              backgroundSize: '230% 100%',
              animation: 'kiroSweep 2.6s linear infinite',
            }}
          />
        )}
        <div className="kiro-skel" style={{ display: 'flex', flexDirection: 'column', gap: 10, ...anim }}>
          <Skeleton shape="row" delayMs={0} slowAfterMs={null} />
          <div style={{ width: '100%', height: 8, borderRadius: radius.pill, backgroundColor: s.skeletonSoft }} />
          <div style={{ width: '78%', height: 8, borderRadius: radius.pill, backgroundColor: s.skeletonSoft }} />
        </div>
        {slow && (
          <div role="status" style={{ marginTop: 14, paddingTop: 11, borderTop: `1px dashed ${s.borderFaint}`, textAlign: 'center' }}>
            <div style={{ fontSize: 12, color: s.muted }}>Biraz uzun sürdü, getiriyoruz…</div>
            <div style={{ marginTop: 3, fontFamily: "'Instrument Serif',Georgia,serif", fontStyle: 'italic', fontSize: 14.5, color: dusk ? '#FFC59B' : '#9A5D0D' }}>
              “{gunMantrasi()}”
            </div>
          </div>
        )}
      </div>
    );
  }
  return <div className="kiro-skel" style={{ width, height: height ?? 8, borderRadius: radius.pill, backgroundColor: s.skeleton, ...anim }} />;
}
