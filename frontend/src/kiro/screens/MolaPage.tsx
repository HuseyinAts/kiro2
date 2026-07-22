// kanon-allow: kutlama
// ============================================================================
// KIRO2 — Mola (SPRINT6 · KIRO2 Mola.dc.html)
// Tema = DUSK (en koyu zemin #0F0B16 — gece-şafak sakinliği). Ekranın kalbi:
// 4·4·4·4 kutu nefesi orbu (16s döngü, 4 faz). Tek istek: getMe() → bugünkü
// çalışma dakikası (studyLabel). Hata kutusu ASLA gösterilmez — veri yoksa alt
// satır gizlenir (sakinlik bozulmaz). Tüm ambient hareket reduced-motion guard'lı;
// nefes yönergeleri İÇERİKTİR → reduce'ta statik liste olarak kalır (egzersiz erişilebilir).
// ============================================================================
import * as React from 'react';

import { configureKiroApi, getMe } from '../api/api-client';
import type { MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';
import type { Persona } from '../types';
import { color, font } from '../tokens';
import { KiroThemeProvider, numText, useReducedMotion, Skeleton } from '../ui';
import '../tokens/tokens.css';

configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });

/** Bugünkü çalışma süresi etiketi — DC fmtDk ile birebir. */
function fmtDk(dk: number): string {
  if (dk < 60) return `${dk} dk`;
  const s = Math.floor(dk / 60);
  const d = dk % 60;
  return d ? `${s} sa ${d} dk` : `${s} saat`;
}

function useMedia(query: string): boolean {
  const [esles, setEsles] = React.useState(false);
  React.useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return;
    const mq = window.matchMedia(query);
    const on = () => setEsles(mq.matches);
    on();
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, [query]);
  return esles;
}

// @keyframes BİREBİR (DC KIRO2 Mola.dc.html) — 16s nefes döngüsü + c1-c4 faz crossfade.
// Hareket JS'te `reduced` ile kapanır (animation: reduced ? undefined : '…').
const KEYFRAMES = `
@keyframes molaDrift { 0%,100% { opacity:0.8; } 50% { opacity:1; } }
@keyframes molaTwinkle { 0%,100% { opacity:0.2; } 50% { opacity:0.85; } }
@keyframes breatheOrb { 0% { transform:scale(0.7); } 25% { transform:scale(1.12); } 50% { transform:scale(1.12); } 75% { transform:scale(0.7); } 100% { transform:scale(0.7); } }
@keyframes breatheRing { 0% { transform:scale(0.7); opacity:0.5; } 25% { transform:scale(1.12); opacity:0.9; } 50% { transform:scale(1.12); opacity:0.9; } 75% { transform:scale(0.7); opacity:0.5; } 100% { transform:scale(0.7); opacity:0.5; } }
@keyframes c1 { 0%,22% { opacity:1; } 26%,100% { opacity:0; } }
@keyframes c2 { 0%,23% { opacity:0; } 27%,47% { opacity:1; } 51%,100% { opacity:0; } }
@keyframes c3 { 0%,48% { opacity:0; } 52%,72% { opacity:1; } 76%,100% { opacity:0; } }
@keyframes c4 { 0%,73% { opacity:0; } 77%,98% { opacity:1; } 100% { opacity:0; } }
`;

// Dekoratif gece yıldızları (aria-hidden; twinkle reduced'ta kapalı) — DC birebir konumlar.
const YILDIZLAR = [
  { top: 40, left: '18%', size: 2, bg: '#FFF', dur: 5, delay: 0 },
  { top: 70, left: '74%', size: 2.3, bg: '#FFE8C9', dur: 6.4, delay: 0.8 },
  { top: 110, left: '40%', size: 1.7, bg: '#FFF', dur: 5.6, delay: 1.4 },
  { top: 54, left: '88%', size: 1.9, bg: '#FFF', dur: 4.8, delay: 0.4 },
];

// Faz yönergeleri (16s senkron crossfade) — orb'la birlikte.
const FAZLAR = ['Nefes al', 'Tut', 'Yavaşça bırak', 'Tut'];
// reduce: egzersiz erişilebilir kalır → statik liste alt alta.
const FAZLAR_STATIK = ['4 sn nefes al', '4 sn tut', '4 sn bırak', '4 sn tut'];

// Dinlenme önerileri — tıklanmaz görsel kartlar (aksiyon yok). Bespoke SVG, %14 dolgu.
const ONERILER: { label: string; bg: string; stroke: string; path: React.ReactNode }[] = [
  {
    label: '2 dk nefes',
    bg: 'rgba(201,168,224,0.14)',
    stroke: '#C9A8E0',
    path: (
      <>
        <path d="M12 4a4 4 0 0 0-4 4c0 2 1 3 1 5M12 4a4 4 0 0 1 4 4c0 2-1 3-1 5" />
        <path d="M9 18a3 3 0 0 0 6 0" />
      </>
    ),
  },
  {
    label: 'Göz dinlendir',
    bg: 'rgba(255,181,112,0.14)',
    stroke: '#FFB570',
    path: (
      <>
        <path d="M2 12s3.5-6 10-6 10 6 10 6" />
        <path d="M2 12s3.5 6 10 6 10-6 10-6" />
      </>
    ),
  },
  {
    label: 'Su iç',
    bg: 'rgba(111,168,255,0.14)',
    stroke: '#6FA8FF',
    path: <path d="M12 3c4 5 6 7.5 6 10a6 6 0 0 1-12 0c0-2.5 2-5 6-10Z" />,
  },
  {
    label: 'Kısa yürüyüş',
    bg: 'rgba(45,212,167,0.14)',
    stroke: '#2DD4A7',
    path: (
      <>
        <circle cx="13" cy="4" r="1.4" />
        <path d="M11 8l-2 4 3 2 1 6M9 12l-3 2M14 14l3 1" />
      </>
    ),
  },
];

export function MolaPage(): React.ReactElement {
  const reduced = useReducedMotion();
  const chipWrap = useMedia('(max-width: 720px)');
  const dar = useMedia('(max-width: 480px)');
  const [persona, setPersona] = React.useState<Persona | null>(null);
  const [hata, setHata] = React.useState(false);
  const baslikRef = React.useRef<HTMLHeadingElement>(null);

  // Tek istek: getMe() → bugünCozulenDk. Hata → alt satır gizlenir (kutu YOK).
  React.useEffect(() => {
    let alive = true;
    getMe()
      .then((p) => { if (alive) setPersona(p); })
      .catch(() => { if (alive) setHata(true); });
    return () => { alive = false; };
  }, []);

  // Sayfa başlığına programatik odak (ekran okuyucu girişi).
  React.useEffect(() => {
    baslikRef.current?.focus();
  }, []);

  return (
    <KiroThemeProvider theme="dusk">
      <div
        className="k-dusk"
        style={{
          minHeight: '100vh',
          background: '#0F0B16',
          color: color.dusk.text2,
          fontFamily: font.sans,
          fontSize: 14,
          lineHeight: 1.6,
          position: 'relative',
          overflowX: 'hidden',
        }}
      >
        <style>{KEYFRAMES}</style>

        {/* Sakin gece-şafak parıltısı + yıldızlar (dekoratif) */}
        <div
          aria-hidden
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 520,
            pointerEvents: 'none',
            background:
              'radial-gradient(115% 90% at 50% -12%, rgba(201,168,224,0.20) 0%, rgba(255,158,125,0.10) 40%, rgba(255,197,111,0.03) 60%, transparent 74%)',
            animation: reduced ? undefined : 'molaDrift 11s ease-in-out infinite',
          }}
        />
        {YILDIZLAR.map((y, i) => (
          <div
            key={i}
            aria-hidden
            style={{
              position: 'absolute',
              top: y.top,
              left: y.left,
              width: y.size,
              height: y.size,
              borderRadius: '50%',
              background: y.bg,
              animation: reduced ? undefined : `molaTwinkle ${y.dur}s ease-in-out ${y.delay}s infinite`,
            }}
          />
        ))}

        <div
          style={{
            position: 'relative',
            maxWidth: 720,
            width: '100%',
            margin: '0 auto',
            padding: dar ? '20px 16px 44px' : '26px 26px 60px',
            minHeight: '100vh',
            display: 'flex',
            flexDirection: 'column',
            boxSizing: 'border-box',
          }}
        >
          {/* Üst bar */}
          <header style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <svg width="30" height="30" viewBox="0 0 40 40" fill="none" aria-hidden>
              <path d="M20 6a11 11 0 1 0 10 15A9 9 0 0 1 20 6Z" fill="#C9A8E0" />
            </svg>
            <span style={{ fontWeight: 800, fontSize: 16, letterSpacing: '-0.01em', color: '#F4ECF2' }}>Mola</span>
            <div style={{ flex: 1 }} />
            <a
              href="/bugun"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                height: 38,
                padding: '0 15px',
                borderRadius: 11,
                border: '1px solid #2E2740',
                background: 'rgba(255,255,255,0.03)',
                color: '#B6A6C4',
                fontSize: 13,
                fontWeight: 700,
                textDecoration: 'none',
              }}
            >
              Çalışmaya dön
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                <path d="m9 6 6 6-6 6" />
              </svg>
            </a>
          </header>

          {/* Selamlama */}
          <div style={{ textAlign: 'center', marginTop: 26 }}>
            <div style={{ fontSize: 13.5, fontWeight: 700, letterSpacing: '0.14em', color: '#C9A8E0' }}>NEFESLEN</div>
            <h1
              ref={baslikRef}
              tabIndex={-1}
              style={{ margin: '10px 0 0', fontFamily: font.serif, fontSize: 33, lineHeight: 1.18, color: '#F6EFE7' }}
            >
              Mola da hazırlığın<br />bir parçası.
            </h1>
          </div>

          {/* Nefes orbu — ekranın kalbi */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '26px 0', minHeight: 300 }}>
            <div style={{ position: 'relative', width: 260, height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {/* Dış halka (dekoratif) */}
              <div
                aria-hidden
                style={{
                  position: 'absolute',
                  width: 230,
                  height: 230,
                  borderRadius: '50%',
                  border: '1.5px solid rgba(201,168,224,0.35)',
                  animation: reduced ? undefined : 'breatheRing 16s ease-in-out infinite',
                }}
              />
              {/* Degrade orb (dekoratif) */}
              <div
                aria-hidden
                style={{
                  position: 'absolute',
                  width: 200,
                  height: 200,
                  borderRadius: '50%',
                  background:
                    'radial-gradient(circle at 50% 42%, rgba(255,213,140,0.6), rgba(255,158,125,0.4) 42%, rgba(201,168,224,0.22) 70%, transparent 78%)',
                  boxShadow: '0 0 70px 10px rgba(201,168,224,0.25)',
                  animation: reduced ? undefined : 'breatheOrb 16s ease-in-out infinite',
                }}
              />
              {/* Faz yönergeleri — İÇERİK (tek aria-live bölge) */}
              {reduced ? (
                <div aria-live="polite" style={{ position: 'relative', textAlign: 'center' }}>
                  {FAZLAR_STATIK.map((t, i) => (
                    <div key={i} style={{ fontSize: 16, fontWeight: 700, color: '#F6EFE7', lineHeight: 1.7 }}>{t}</div>
                  ))}
                </div>
              ) : (
                <div aria-live="polite" style={{ position: 'relative', textAlign: 'center', height: 34 }}>
                  {FAZLAR.map((t, i) => (
                    <span
                      key={i}
                      style={{
                        position: 'absolute',
                        left: '50%',
                        top: 0,
                        transform: 'translateX(-50%)',
                        whiteSpace: 'nowrap',
                        fontSize: 22,
                        fontWeight: 700,
                        color: '#F6EFE7',
                        animation: `c${i + 1} 16s linear infinite`,
                      }}
                    >
                      {t}
                    </span>
                  ))}
                </div>
              )}
            </div>
            <div style={{ marginTop: 22, fontSize: 12.5, fontWeight: 600, letterSpacing: '0.1em', color: '#8C8398' }}>
              4 · 4 · 4 · 4 KUTU NEFESİ · ORBLA BİRLİKTE
            </div>
          </div>

          {/* Dinlenme önerileri — tıklanmaz görsel kartlar */}
          <div style={{ display: 'flex', gap: 11, justifyContent: 'center', marginBottom: 26, flexWrap: chipWrap ? 'wrap' : 'nowrap' }}>
            {ONERILER.map((c) => (
              <div
                key={c.label}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 8,
                  width: 118,
                  padding: '16px 10px',
                  borderRadius: 16,
                  background: 'rgba(255,255,255,0.03)',
                  border: '1px solid #241C30',
                  boxSizing: 'border-box',
                }}
              >
                <div style={{ width: 40, height: 40, borderRadius: 12, background: c.bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={c.stroke} strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                    {c.path}
                  </svg>
                </div>
                <div style={{ fontSize: 12.5, fontWeight: 700, color: '#DCD0E4', textAlign: 'center', lineHeight: 1.3 }}>{c.label}</div>
              </div>
            ))}
          </div>

          {/* Onaylama + dönüş */}
          <div style={{ textAlign: 'center', borderTop: '1px solid #241C30', paddingTop: 24 }}>
            {persona ? (
              <p style={{ margin: '0 0 4px', fontSize: 14, color: '#C7B6D0' }}>
                Bugün <strong style={{ ...numText, color: '#F0E7D8' }}>{fmtDk(persona.bugunCozulenDk)}</strong> çalıştın — bu molayı hak ettin.
              </p>
            ) : !hata ? (
              <div aria-hidden style={{ maxWidth: 240, margin: '0 auto 6px' }}>
                <Skeleton shape="bar" width="70%" delayMs={0} />
              </div>
            ) : null}
            <p style={{ margin: '0 0 20px', fontFamily: font.serif, fontStyle: 'italic', fontSize: 18, color: '#C9A8E0' }}>
              &ldquo;Dinlenen zihin daha iyi öğrenir.&rdquo;
            </p>
            <a
              href="/bugun"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 10,
                height: 50,
                padding: '0 28px',
                border: 'none',
                borderRadius: 14,
                background: 'linear-gradient(110deg,#C9A8E0,#FF9E7D)',
                color: '#241329',
                fontFamily: font.sans,
                fontSize: 15,
                fontWeight: 800,
                textDecoration: 'none',
                boxShadow: '0 8px 26px -10px rgba(201,168,224,0.6)',
              }}
            >
              Hazır hissediyorum
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
                <path d="M7 5.5v13a1 1 0 0 0 1.5.86l11-6.5a1 1 0 0 0 0-1.72l-11-6.5A1 1 0 0 0 7 5.5Z" />
              </svg>
            </a>
          </div>
        </div>
      </div>
    </KiroThemeProvider>
  );
}

export default MolaPage;
