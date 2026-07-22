// kanon-allow: kutlama
// ============================================================================
// KIRO2 — Başarımlar (SPRINT7 · KIRO2 Basarimlar.dc.html)
// Tema = DUSK (mor radyal zemin). Yolun kanıtı: seviye/XP hero bandı, ders başına
// hâkimiyet halkaları (kademe rozeti), seri kilometre taşları, kademe lejantı.
// İki istek: getMe() (seviye/xp/seri/rekor) + getSubjects() (hâkimiyet). Üç durum:
// Skeleton (halka iskeleti) · ErrorState (sakin amber) · içerik. Hareket YOK —
// yalnız hero bandı girişte yumuşak belirir (DC kv-in dili), reduced-motion'da kapalı.
// ============================================================================
import * as React from 'react';

import { configureKiroApi, getMe, getSubjects } from '../api/api-client';
import type { MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';
import type { Persona, Subject } from '../types';
import { color, font } from '../tokens';
import { KiroThemeProvider, numText, useReducedMotion, Skeleton, ErrorState, tierFromPct } from '../ui';
import type { MasteryTier } from '../ui';
import '../tokens/tokens.css';

configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });

// Kademe renk + etiket (dusk) — eşikler tierFromPct ile AYNI (40/65/85). tokens.color.mastery.
const TIER_META: Record<MasteryTier, { label: string; color: string }> = {
  tanidik: { label: 'Tanıdık', color: color.mastery.tanidik },
  yetkin: { label: 'Yetkin', color: color.mastery.yetkin },
  usta: { label: 'Usta', color: color.mastery.usta },
  fethedildi: { label: 'Fethedildi', color: color.mastery.fethedildi },
};

// Kademe lejantı — 4 kademe + aralık (en-dash –).
const LEJANT: { key: MasteryTier; range: string }[] = [
  { key: 'tanidik', range: '0–40' },
  { key: 'yetkin', range: '40–65' },
  { key: 'usta', range: '65–85' },
  { key: 'fethedildi', range: '85–100' },
];

// Seri kilometre taşları — kilitliGoster üretimde SABİT true (prop yok; kilitliyi saklamak
// motivasyon hilesi olur → gösterilir).
const MILESTONES = [7, 14, 21, 30, 50, 100];

const CIRC = 2 * Math.PI * 32; // halka çevresi (r=32) — dasharray 201.06

// Girişte yumuşak beliriş (DC kv-in) — opacity+transform, reduced-motion'da kapalı.
const KEYFRAMES = `@keyframes basEntrance { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:none; } }`;

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

interface Veri {
  persona: Persona;
  subjects: Subject[];
}

export function BasarimlarPage(): React.ReactElement {
  const reduced = useReducedMotion();
  const dar = useMedia('(max-width: 560px)');
  const [veri, setVeri] = React.useState<Veri | null>(null);
  const [hata, setHata] = React.useState(false);

  const yukle = React.useCallback(() => {
    let alive = true;
    setHata(false);
    setVeri(null);
    Promise.all([getMe(), getSubjects()])
      .then(([persona, subjects]) => {
        if (alive) setVeri({ persona, subjects });
      })
      .catch(() => {
        if (alive) setHata(true);
      });
    return () => {
      alive = false;
    };
  }, []);

  React.useEffect(() => yukle(), [yukle]);

  return (
    <KiroThemeProvider theme="dusk">
      <div
        className="k-dusk"
        style={{
          minHeight: '100vh',
          background: 'radial-gradient(120% 92% at 50% -8%, #3E2554 0%, #271A3C 40%, #150E20 100%)',
          color: color.dusk.text,
          fontFamily: font.sans,
          fontSize: 14,
          lineHeight: 1.5,
          position: 'relative',
          overflowX: 'hidden',
        }}
      >
        <style>{KEYFRAMES}</style>

        <div
          style={{
            maxWidth: 900,
            width: '100%',
            margin: '0 auto',
            padding: dar ? '24px 20px 70px' : '24px 30px 70px',
            boxSizing: 'border-box',
          }}
        >
          {/* Header — geri ok + başlık */}
          <header style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 24 }}>
            <a
              href="/panel"
              aria-label="Geri"
              style={{
                width: 38,
                height: 38,
                flexShrink: 0,
                border: '1px solid #3A2A48',
                background: 'rgba(255,255,255,0.04)',
                borderRadius: 11,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#C7B8D6',
                textDecoration: 'none',
              }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                <line x1="19" y1="12" x2="5" y2="12" />
                <polyline points="12 19 5 12 12 5" />
              </svg>
            </a>
            <div>
              <h1 style={{ margin: 0, fontFamily: font.serif, fontSize: 32, lineHeight: 1, color: '#F6EFF7' }}>Başarımlar</h1>
              <div style={{ fontSize: 12.5, color: 'rgba(241,233,242,0.55)', marginTop: 3 }}>
                {veri ? `${kazanilanRozet(veri)} rozet kazanıldı · yolun kanıtı` : 'yolun kanıtı'}
              </div>
            </div>
          </header>

          {hata ? (
            <ErrorState onRetry={yukle} />
          ) : !veri ? (
            <IskeletGrid />
          ) : (
            <Icerik veri={veri} reduced={reduced} />
          )}
        </div>
      </div>
    </KiroThemeProvider>
  );
}

/** kazanilan = hâkimiyet rozeti (her ders bir kademede) + açılan seri-taşı — DC birebir
 *  (renderVals: tierBadges.length + earned). İstemci türetim; açık-nokta 4 → üretimde /achievements özeti. */
function kazanilanRozet(v: Veri): number {
  const rozetler = v.subjects.length; // her dersin bir hâkimiyet kademesi rozeti var
  const acilanTas = MILESTONES.filter((m) => v.persona.seriRekor >= m).length;
  return rozetler + acilanTas;
}

function Icerik({ veri, reduced }: { veri: Veri; reduced: boolean }): React.ReactElement {
  const { persona, subjects } = veri;
  const { seviye, xp, seri, seriRekor } = persona;

  // DC varsayılan sıralaması: hâkimiyet azalan.
  const sirali = [...subjects].sort((a, b) => b.hakimiyet - a.hakimiyet);

  const rekorKala = Math.max(0, seriRekor - seri);
  const progressPct = Math.min(100, Math.round((seri / Math.max(1, seriRekor)) * 100));

  return (
    <>
      {/* Hero bandı (amber cam) */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 18,
          flexWrap: 'wrap',
          padding: '20px 22px',
          borderRadius: 20,
          background: 'linear-gradient(120deg, rgba(255,181,112,0.14), rgba(255,255,255,0.03))',
          border: '1px solid rgba(255,181,112,0.22)',
          marginBottom: 30,
          boxSizing: 'border-box',
          animation: reduced ? undefined : 'basEntrance 0.5s ease both',
        }}
      >
        <div
          style={{
            position: 'relative',
            width: 66,
            height: 66,
            flexShrink: 0,
            borderRadius: 18,
            background: 'linear-gradient(140deg,#FFB570,#FF6F91)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 10px 26px -8px rgba(255,111,145,0.55)',
          }}
        >
          <span style={{ ...numText, fontWeight: 800, fontSize: 26, color: '#2A1018' }}>{seviye}</span>
          <span
            aria-hidden
            style={{
              position: 'absolute',
              top: -6,
              right: -6,
              width: 24,
              height: 24,
              borderRadius: 8,
              background: '#150E20',
              border: '1.5px solid #FFC98A',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="#FFC98A">
              <path d="M5 16 3 5l5.5 4L12 4l3.5 5L21 5l-2 11H5Zm0 3h14v2H5z" />
            </svg>
          </span>
        </div>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: '0.1em', color: '#FFC98A', textTransform: 'uppercase' }}>
            Seviye {seviye}
          </div>
          <div style={{ fontSize: 20, fontWeight: 800, color: '#F6EFF7', marginTop: 2 }}>
            <span style={numText}>{xp.toLocaleString('tr-TR')}</span> XP toplandı
          </div>
        </div>
        <div style={{ flex: 1 }} />
        <div style={{ display: 'flex', gap: 22 }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ ...numText, fontSize: 24, fontWeight: 800, color: '#FFB570', lineHeight: 1 }}>{seri}</div>
            <div style={{ fontSize: 11, color: 'rgba(241,233,242,0.55)', marginTop: 4 }}>gün seri</div>
          </div>
          <div style={{ width: 1, background: 'rgba(255,255,255,0.1)' }} />
          <div style={{ textAlign: 'center' }}>
            <div style={{ ...numText, fontSize: 24, fontWeight: 800, color: '#F6EFF7', lineHeight: 1 }}>{seriRekor}</div>
            <div style={{ fontSize: 11, color: 'rgba(241,233,242,0.55)', marginTop: 4 }}>rekor</div>
          </div>
        </div>
      </div>

      {/* Hâkimiyet Rozetleri */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 16 }}>
        <h2 style={{ margin: 0, fontSize: 16, fontWeight: 800, color: '#F6EFF7', letterSpacing: '-0.01em' }}>Hâkimiyet Rozetleri</h2>
        <span style={{ fontSize: 12, color: 'rgba(241,233,242,0.5)' }}>her ders bir kademede</span>
      </div>
      <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap', marginBottom: 34 }}>
        {sirali.map((s) => {
          const tier = tierFromPct(s.hakimiyet);
          const meta = TIER_META[tier];
          const offset = (CIRC * (1 - s.hakimiyet / 100)).toFixed(1);
          return (
            <div key={s.key} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 126 }}>
              <div style={{ position: 'relative', width: 96, height: 96, marginBottom: 11 }}>
                <svg width="96" height="96" viewBox="0 0 80 80" role="img" aria-label={`${s.ad} yüzde ${s.hakimiyet}, ${meta.label}`}>
                  <circle cx="40" cy="40" r="32" fill="none" stroke="rgba(255,255,255,0.09)" strokeWidth="7" />
                  <circle
                    cx="40"
                    cy="40"
                    r="32"
                    fill="none"
                    stroke={s.renk}
                    strokeWidth="7"
                    strokeLinecap="round"
                    strokeDasharray="201.06"
                    strokeDashoffset={offset}
                    transform="rotate(-90 40 40)"
                    style={{ filter: `drop-shadow(0 0 6px ${s.glow})` }}
                  />
                </svg>
                <div aria-hidden style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <span style={{ ...numText, fontSize: 23, fontWeight: 800, color: '#F6EFF7', lineHeight: 1 }}>{s.hakimiyet}</span>
                  <span style={{ fontSize: 9, color: 'rgba(241,233,242,0.5)', fontWeight: 700 }}>%</span>
                </div>
              </div>
              <div style={{ fontSize: 13.5, fontWeight: 700, color: color.dusk.text }}>{s.ad}</div>
              <div
                style={{
                  marginTop: 6,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 5,
                  height: 22,
                  padding: '0 10px',
                  borderRadius: 99,
                  background: 'rgba(255,255,255,0.06)',
                  border: `1px solid ${meta.color}55`,
                }}
              >
                <span aria-hidden style={{ width: 6, height: 6, borderRadius: '50%', background: meta.color }} />
                <span style={{ fontSize: 11, fontWeight: 800, color: meta.color }}>{meta.label}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Seri Kilometre Taşları */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 6 }}>
        <h2 style={{ margin: 0, fontSize: 16, fontWeight: 800, color: '#F6EFF7', letterSpacing: '-0.01em' }}>Seri Kilometre Taşları</h2>
        <span style={{ fontSize: 12, color: 'rgba(241,233,242,0.5)' }}>
          aktif {seri} · rekor {seriRekor}
        </span>
      </div>

      {/* Aktif seri barı */}
      <div style={{ margin: '12px 0 20px', padding: '14px 18px', borderRadius: 16, background: 'rgba(255,255,255,0.04)', border: '1px solid #33263F' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 9, fontSize: 12.5 }}>
          <span style={{ color: 'rgba(241,233,242,0.72)', fontWeight: 600 }}>
            Aktif seri <strong style={{ color: '#FFB570' }}>{seri} gün</strong>
          </span>
          <span style={{ color: 'rgba(241,233,242,0.55)' }}>
            rekora <strong style={{ color: '#F6EFF7' }}>{rekorKala} gün</strong>
          </span>
        </div>
        <div style={{ height: 9, borderRadius: 99, background: 'rgba(255,255,255,0.08)', overflow: 'hidden' }}>
          <div style={{ width: `${progressPct}%`, height: '100%', borderRadius: 99, background: 'linear-gradient(90deg,#FF8A5B,#FFB570)' }} />
        </div>
      </div>

      {/* Kilometre taşı karoları */}
      <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
        {MILESTONES.map((m) => {
          const earned = seriRekor >= m;
          return (
            <div
              key={m}
              aria-disabled={earned ? undefined : true}
              style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 96 }}
            >
              <div
                style={{
                  position: 'relative',
                  width: 72,
                  height: 72,
                  borderRadius: 20,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: 9,
                  ...(earned
                    ? {
                        background: 'linear-gradient(140deg,#FF8A5B,#C24E7E)',
                        border: '1px solid rgba(255,181,112,0.5)',
                        boxShadow: '0 8px 22px -8px rgba(255,138,91,0.5)',
                      }
                    : {
                        background: 'rgba(255,255,255,0.04)',
                        border: '1px dashed #3A2A48',
                      }),
                }}
              >
                {earned ? (
                  <svg width="30" height="30" viewBox="0 0 24 24" fill="#fff" aria-hidden style={{ filter: 'drop-shadow(0 2px 6px rgba(255,138,91,0.6))' }}>
                    <path d="M12 2c1.4 3.4 4.5 4.8 4.5 8.6A4.5 4.5 0 0 1 7.5 11c0-1.6.6-2.7 1.2-3.4.2 1.1 1 1.8 1.8 1.8C10.8 7.2 11 4.6 12 2Z" />
                  </svg>
                ) : (
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#6B5A78" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                    <rect x="5" y="11" width="14" height="9" rx="2" />
                    <path d="M8 11V8a4 4 0 0 1 8 0v3" />
                  </svg>
                )}
              </div>
              <div style={{ ...numText, fontSize: 14, fontWeight: 800, color: earned ? '#F6EFF7' : 'rgba(241,233,242,0.4)' }}>{m}</div>
              <div style={{ fontSize: 10.5, color: 'rgba(241,233,242,0.5)', fontWeight: 600 }}>{earned ? 'açıldı' : 'kilitli'}</div>
            </div>
          );
        })}
      </div>

      {/* Kademe lejantı */}
      <div style={{ marginTop: 36, display: 'flex', gap: 10, flexWrap: 'wrap', paddingTop: 20, borderTop: '1px solid #2A2038' }}>
        {LEJANT.map((l) => {
          const meta = TIER_META[l.key];
          return (
            <div key={l.key} style={{ display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: 11.5, color: 'rgba(241,233,242,0.6)' }}>
              <span aria-hidden style={{ width: 9, height: 9, borderRadius: '50%', background: meta.color }} />
              <strong style={{ color: meta.color, fontWeight: 700 }}>{meta.label}</strong>
              <span>{l.range}</span>
            </div>
          );
        })}
      </div>
    </>
  );
}

/** Yükleme iskeleti — hâkimiyet halka ızgarası (5 iskelet). */
function IskeletGrid(): React.ReactElement {
  return (
    <>
      <div aria-hidden style={{ marginBottom: 30 }}>
        <Skeleton shape="card" delayMs={0} />
      </div>
      <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap' }} aria-hidden>
        {[0, 1, 2, 3, 4].map((i) => (
          <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 126 }}>
            <div style={{ width: 96, height: 96, borderRadius: '50%', border: '7px solid rgba(255,255,255,0.06)', boxSizing: 'border-box', marginBottom: 11 }} />
            <Skeleton shape="bar" width={70} delayMs={0} />
          </div>
        ))}
      </div>
    </>
  );
}

export default BasarimlarPage;
