import * as React from 'react';

// Kaynak: KIRO2 Kutlama.dc.html — deterministik şafak konfetisi.
// KANON: transform-only animasyon; prefers-reduced-motion'da TAMAMEN kapalı.
// Kutlama yalnız GERÇEK kademe geçişi / gerçek başarıda — sahte tamamlanmada değil.

/** Faz 1.4'teki temel a11y aracı — başka bileşenler de kullanabilir. */
export function useReducedMotion(): boolean {
  const [reduced, setReduced] = React.useState(
    () => typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  );
  React.useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    const on = (e: MediaQueryListEvent) => setReduced(e.matches);
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, []);
  return reduced;
}

/** Şafak paleti — coral · şeftali · altın · leylak · nane */
const CC = ['#FF6F5C', '#FF9E7D', '#FFD98C', '#C9A8E0', '#2DD4A7'];

const KEYFRAMES = `@keyframes kiroCfall {
  0% { transform: translateY(-10vh) rotate(0); opacity: 0; }
  10% { opacity: 0.95; }
  100% { transform: translateY(108vh) rotate(680deg); opacity: 0.25; }
}`;

export interface ConfettiDawnProps {
  /** Parça sayısı (deterministik dağılım — her render aynı) */
  count?: number;
  zIndex?: number;
}

export function ConfettiDawn({ count = 20, zIndex = 2 }: ConfettiDawnProps) {
  const reduced = useReducedMotion();
  if (reduced) return null;

  const pieces: React.ReactNode[] = [];
  for (let i = 0; i < count; i++) {
    const left = (i * 53 + 7) % 100;
    const w = 6 + (i % 3) * 3;
    const dur = 2.6 + (i % 5) * 0.55;
    const delay = (i % 7) * 0.45;
    pieces.push(
      <div key={i} style={{ position: 'absolute', left: `${left}%`, top: '-8%',
        width: w, height: w + 2, background: CC[i % CC.length],
        borderRadius: i % 2 ? 2 : '50%', opacity: 0.9,
        animation: `kiroCfall ${dur}s linear ${delay}s infinite` }} />,
    );
  }

  return (
    <div aria-hidden style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none', zIndex }}>
      <style>{KEYFRAMES}</style>
      {pieces}
    </div>
  );
}
