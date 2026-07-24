// kanon-allow: kutlama
// ============================================================================
// KIRO2 — Bugün / Şafak Hub (SPRINT6 · KIRO Safak.dc.html) — İLK DUSK EKRAN
// Tema = DUSK (koyu duygusal giriş kapısı). SideNav YOK — dikey akış, max 840px.
// Gökyüzü hero (gradyan + yıldız + güneş + silüet) → görev kartı (ufka oturan) →
// ders kartları → FSRS + SEN-vs-DÜN → mood → mantra. Rota /bugun.
//
// RESOLVED (DC piksel-otoritesi + anti-fabrikasyon):
// - {n} tuğla = İSTEMCİ hesabı (motor değil): toplamT=ceil(hedef/15),
//   konanT=floor(bugun/15), kalanT=toplam-konan. Hero + progress aynı birim.
// - Görev kartı = getPlanWeek() bugünkü ilk blok (mock: Türev · 12 soru · ~30 dk).
// - SEN-vs-DÜN = DC-STATİK (+15 dk + sabit çubuklar) — "dün" verisi yok, uydurma yok.
// - Mood = YEREL: localStorage gün-anahtarlı; 5 mesaj istemci sabiti (POST /me/mood açık-nokta).
// - FSRS konu = en düşük hatırlanabilirlik (getReviewDue); dk = max(5, round(kart*0.5)).
// ============================================================================
import * as React from 'react';

import { getMe, getSubjects, getReviewDue, getPlanWeek } from '../api/api-client';
import { color, font } from '../tokens';
import type { Persona, Subject, ReviewItem, PlanWeek, PlanBlok } from '../types';
import { KiroThemeProvider, numText, useReducedMotion, ErrorState, Skeleton } from '../ui';
import '../tokens/tokens.css';

// --- Ambient hareket (reduced-motion'da <style> koşullu enjekte edilir) ---
const KEYFRAMES = `
@keyframes kiroTwinkle { 0%,100% { opacity: 0.25; } 50% { opacity: 0.9; } }
@keyframes kiroSunPulse { 0%,100% { opacity: 0.85; transform: scale(1); } 50% { opacity: 1; transform: scale(1.04); } }
@keyframes kiroGlowB { 0%,100% { opacity: 0; } 50% { opacity: 1; } }
`;

const STARS = [
  { top: 34, left: '14%', s: 2, dur: 4, delay: 0, c: '#FFFFFF' },
  { top: 58, left: '28%', s: 2.5, dur: 5.5, delay: 0.6, c: '#FFFFFF' },
  { top: 30, left: '46%', s: 1.6, dur: 4.8, delay: 1.2, c: '#FFFFFF' },
  { top: 76, left: '62%', s: 2, dur: 6, delay: 0.3, c: '#FFE8C9' },
  { top: 48, left: '80%', s: 1.8, dur: 5, delay: 0.9, c: '#FFFFFF' },
  { top: 20, left: '88%', s: 2.2, dur: 4.4, delay: 1.6, c: '#FFFFFF' },
] as const;

// --- Gün-seed'li mantra rotasyonu (havuz 5, ilk = kanon) ---
export const MANTRA = [
  'Sınav bir günü ölçer. Sen çok daha fazlasısın.',
  'Küçük adım, her gün.',
  'Dünkü senden bir adım önde.',
  'Acele etme; istikrar yetenektir.',
  'Bu yol tuğla tuğla örülür.',
] as const;

export function gunlukMantra(d: Date = new Date()): string {
  const i = (d.getFullYear() * 372 + d.getMonth() * 31 + d.getDate()) % MANTRA.length;
  return MANTRA[i] ?? MANTRA[0];
}

export function selamla(d: Date = new Date()): string {
  const h = d.getHours();
  if (h >= 5 && h < 12) return 'Günaydın';
  if (h >= 12 && h < 18) return 'İyi günler';
  if (h >= 18 && h < 23) return 'İyi akşamlar';
  return 'Geç oldu';
}

function moodKey(d: Date = new Date()): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `kiro:mood:${y}-${m}-${dd}`;
}

interface MoodDef { key: string; label: string; color: string; mouth: string; msg: string }
const MOODS: MoodDef[] = [
  { key: 'bitkin', label: 'bitkin', color: '#9B93C4', mouth: 'M12 25 Q18 21 24 25', msg: 'Tükendiysen bugün 10 dakika yeter — gerçekten. Dinlenmek de hazırlığın parçası.' },
  { key: 'gergin', label: 'gergin', color: '#C9A8E0', mouth: 'M12 24 Q18 22.5 24 24', msg: 'Gerginlik normal. Önce 2 nefes, sonra tek küçük adım. Birlikte.' },
  { key: 'idare', label: 'idare', color: '#BCB0C0', mouth: 'M12.5 24 L23.5 24', msg: 'İdare ediyorsan iyidir. Momentumu küçük tutalım, zorlamadan.' },
  { key: 'iyi', label: 'iyi', color: '#FFB570', mouth: 'M12 23 Q18 27.5 24 23', msg: 'Güzel — bu enerjiyi zayıf konuna harca, en çok orada kazanırsın.' },
  { key: 'harika', label: 'harika', color: '#FF9E7D', mouth: 'M11 22 Q18 30 25 22', msg: 'Harikaysan gaza basalım! Bugün biraz daha zorlu bir set deneyebilirsin.' },
];

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

// --- Bespoke SVG ikonlar (aria-hidden) ---
const IconLogo = (
  <svg width="30" height="30" viewBox="0 0 40 40" fill="none" aria-hidden>
    <line x1="5" y1="28" x2="35" y2="28" stroke="#FFE8C9" strokeWidth="2.2" strokeLinecap="round" />
    <path d="M12 28a8 8 0 0 1 16 0Z" fill="#FFD98C" />
    <path d="M20 9v3M31 13l-2 2M9 13l2 2" stroke="#FFE8C9" strokeWidth="2.2" strokeLinecap="round" />
  </svg>
);
const IconCal = (
  <svg aria-hidden width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FFD98C" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="17" rx="2" /><path d="M3 9h18M8 2v4M16 2v4" /></svg>
);
const IconStreak = (
  <svg aria-hidden width="15" height="15" viewBox="0 0 24 24" fill="none"><path d="M4 18h16" stroke="#FFD98C" strokeWidth="2" strokeLinecap="round" /><path d="M7 18a5 5 0 0 1 10 0Z" fill="#FFD98C" /></svg>
);
const IconClock = (
  <svg aria-hidden width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#9B8FB5" strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>
);
const IconPlay = (
  <svg aria-hidden width="30" height="30" viewBox="0 0 24 24" fill="currentColor"><path d="M7 5.5v13a1 1 0 0 0 1.5.86l11-6.5a1 1 0 0 0 0-1.72l-11-6.5A1 1 0 0 0 7 5.5Z" /></svg>
);
const IconArrow = (
  <svg aria-hidden width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#8C8398" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
);
const IconChevron = (
  <svg aria-hidden width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C29A88" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m9 6 6 6-6 6" /></svg>
);
const IconRefresh = (
  <svg aria-hidden width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFB570" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5" /></svg>
);

function Gokyuzu({ reduced }: { reduced: boolean }): React.ReactElement {
  // Dekoratif katman — DOM içeriğinin önünde, aria-hidden. Her durumda çizilir.
  return (
    <div aria-hidden style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
      {/* Yıldızlar */}
      {STARS.map((st, i) => (
        <div key={i} style={{ position: 'absolute', top: st.top, left: st.left, width: st.s, height: st.s, borderRadius: '50%', background: st.c, animation: reduced ? undefined : `kiroTwinkle ${st.dur}s ease-in-out ${st.delay}s infinite` }} />
      ))}
      {/* Güneş glow + çekirdek (390px'te de %67 sabit) */}
      <div style={{ position: 'absolute', left: '67%', bottom: 0, width: 0, height: 0 }}>
        <div style={{ position: 'absolute', bottom: -40, left: -260, width: 520, height: 520, borderRadius: '50%', background: 'radial-gradient(circle, rgba(255,234,180,0.55) 0%, rgba(255,180,110,0.32) 24%, rgba(240,120,90,0.14) 42%, transparent 62%)', animation: reduced ? undefined : 'kiroSunPulse 7s ease-in-out infinite' }} />
        <div style={{ position: 'absolute', bottom: 6, left: -64, width: 128, height: 128, borderRadius: '50%', background: 'radial-gradient(circle at 50% 40%, #FFF4D6 0%, #FFD98C 38%, #FFB36B 64%, rgba(255,150,90,0) 78%)', boxShadow: '0 0 80px 20px rgba(255,200,130,0.35)' }} />
      </div>
      {/* İki katman tepe silüeti */}
      <svg viewBox="0 0 1440 180" preserveAspectRatio="none" style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', height: 140, display: 'block' }}>
        <path d="M0,90 C220,40 380,70 560,84 C760,100 900,56 1120,72 C1280,84 1380,70 1440,64" fill="none" stroke="rgba(255,180,120,0.35)" strokeWidth="1.5" />
        <path d="M0,90 C220,40 380,70 560,84 C760,100 900,56 1120,72 C1280,84 1380,70 1440,64 L1440,180 L0,180 Z" fill="#1C1330" opacity="0.85" />
        <path d="M0,128 C260,96 460,118 720,120 C980,122 1180,104 1440,118" fill="none" stroke="rgba(255,150,100,0.18)" strokeWidth="1.2" />
        <path d="M0,128 C260,96 460,118 720,120 C980,122 1180,104 1440,118 L1440,180 L0,180 Z" fill="#140E22" />
      </svg>
    </div>
  );
}

const orta: React.CSSProperties = { position: 'relative', maxWidth: 840, width: '100%', margin: '0 auto', boxSizing: 'border-box' };

export function BugunPage(): React.ReactElement {
  const reduced = useReducedMotion();
  const dar800 = useMedia('(max-width: 800px)');
  const dar480 = useMedia('(max-width: 480px)');

  const [persona, setPersona] = React.useState<Persona | null>(null);
  const [dersler, setDersler] = React.useState<Subject[] | null>(null);
  const [review, setReview] = React.useState<ReviewItem[]>([]);
  const [plan, setPlan] = React.useState<PlanWeek | null>(null);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);
  const [mood, setMood] = React.useState<number | null>(null);

  React.useEffect(() => {
    let alive = true;
    setPersona(null);
    setDersler(null);
    setHata(false);
    Promise.all([getMe(), getSubjects(), getReviewDue(), getPlanWeek()])
      .then(([p, s, r, pw]) => {
        if (!alive) return;
        setPersona(p);
        setDersler(s);
        setReview(r);
        setPlan(pw);
      })
      .catch(() => { if (alive) setHata(true); });
    return () => { alive = false; };
  }, [yeniden]);

  // Mood — yerel, gün-anahtarlı (private-mode try/catch)
  React.useEffect(() => {
    try {
      const v = window.localStorage.getItem(moodKey());
      if (v != null) {
        const i = MOODS.findIndex((m) => m.key === v);
        if (i >= 0) setMood(i);
      }
    } catch { /* private mode */ }
  }, []);
  const pickMood = React.useCallback((i: number) => {
    setMood(i);
    try { window.localStorage.setItem(moodKey(), MOODS[i]!.key); } catch { /* private mode */ }
  }, []);

  const greeting = selamla();
  const mantra = gunlukMantra();

  // Tuğla — İSTEMCİ deterministik hesabı (motor değil)
  const hedefDk = persona?.gunlukHedefDk ?? 0;
  const bugunDk = persona?.bugunCozulenDk ?? 0;
  const toplamT = Math.max(1, Math.ceil(hedefDk / 15));
  const konanT = Math.min(toplamT, Math.floor(bugunDk / 15));
  const kalanT = toplamT - konanT;
  const gunPct = Math.min(100, Math.round((bugunDk / Math.max(1, hedefDk)) * 100));

  // Görev kartı = bugünkü ilk plan bloğu
  const bugunGun = plan?.gunler.find((g) => g.bugun);
  const blok: PlanBlok | undefined = bugunGun?.bloklar[0];
  const blokDers = blok && blok.ders ? dersler?.find((s) => s.key === blok.ders) : undefined;

  // FSRS — en düşük hatırlanabilirlik + tahmini dakika
  const reviewCount = review.length;
  const enZayifReview = reviewCount > 0
    ? review.reduce((a, b) => (b.hatirlanabilirlik < a.hatirlanabilirlik ? b : a), review[0]!)
    : null;
  const toplamKart = review.reduce((a, r) => a + (r.kart || 0), 0);
  const reviewDk = Math.max(5, Math.round(toplamKart * 0.5));

  const heroHazir = persona !== null;
  const gorevYok = heroHazir && !blok;

  const h1Size = dar480 ? 30 : 38;
  const yatayPad = dar480 ? 18 : 28;

  return (
    <KiroThemeProvider theme="dusk">
      <div className="k-dusk" style={{ minHeight: '100vh', background: color.dusk.bg, color: color.dusk.text, fontFamily: font.sans, position: 'relative', overflowX: 'hidden' }}>
        <style>{KEYFRAMES}</style>

        {/* ===== GÖKYÜZÜ HERO ===== */}
        <div style={{ position: 'relative', height: 430, overflow: 'hidden', background: color.gradient.dawnSkyLinear }}>
          <Gokyuzu reduced={reduced} />

          {/* Üst bar */}
          <div style={{ ...orta, display: 'flex', alignItems: 'center', gap: 12, padding: `24px ${yatayPad}px`, flexWrap: 'wrap' }}>
            {IconLogo}
            <span style={{ fontWeight: 800, fontSize: 17, color: '#FCEFE0', letterSpacing: '-0.01em' }}>KIRO</span>
            <div style={{ flex: 1 }} />
            <a href="/geri-sayim" style={{ display: 'inline-flex', alignItems: 'center', gap: 7, minHeight: 44, padding: '8px 13px', borderRadius: 999, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.14)', backdropFilter: 'blur(6px)', textDecoration: 'none', boxSizing: 'border-box' }}>
              {IconCal}
              <span style={{ fontWeight: 700, fontSize: 12.5, color: '#FFF1DC' }}>Sınava sayım</span>
            </a>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, minHeight: 44, padding: '8px 14px', borderRadius: 999, background: 'rgba(255,217,140,0.14)', border: '1px solid rgba(255,217,140,0.28)', backdropFilter: 'blur(6px)', boxSizing: 'border-box' }}>
              {IconStreak}
              <span style={{ ...numText, fontWeight: 800, fontSize: 13.5, color: '#FFF1DC' }}>{persona?.seri ?? '…'}</span>
              <span style={{ fontSize: 11.5, color: 'rgba(255,241,220,0.7)' }}>gün seri</span>
            </div>
          </div>

          {/* Hero kopya */}
          <div style={{ ...orta, padding: `14px ${yatayPad}px 0` }}>
            <div style={{ fontSize: 14.5, fontWeight: 600, color: 'rgba(255,238,222,0.82)', marginBottom: 10 }}>
              {greeting}{heroHazir ? `, ${persona.adKisa}` : ''}
            </div>
            {heroHazir ? (
              <>
                <h1 style={{ margin: 0, fontSize: h1Size, fontWeight: 800, letterSpacing: '-0.025em', lineHeight: 1.08, color: '#FFF6EC', textShadow: '0 2px 30px rgba(20,8,30,0.4)', maxWidth: 480 }}>
                  {kalanT > 0 && !gorevYok ? (
                    <>Şafağa <span style={{ ...numText, color: '#FFD98C' }}>{kalanT} tuğla</span> kaldı.</>
                  ) : (
                    'Bugünün tuğlaları yerinde.'
                  )}
                </h1>
                <p style={{ margin: '8px 0 0', fontSize: 15, color: 'rgba(255,235,220,0.8)', maxWidth: 420 }}>
                  Bugünkü tuğlanı koyalım — acelesi yok, sakin adım adım.
                </p>
              </>
            ) : (
              <div aria-hidden style={{ display: 'grid', gap: 10, maxWidth: 360 }}>
                <div style={{ height: h1Size, width: '80%', borderRadius: 10, background: 'rgba(255,255,255,0.12)' }} />
                <div style={{ height: 15, width: '60%', borderRadius: 8, background: 'rgba(255,255,255,0.08)' }} />
              </div>
            )}
          </div>
        </div>

        {/* ===== İÇERİK ===== */}
        <div style={{ ...orta, padding: `0 ${yatayPad}px 70px` }}>
          {hata ? (
            <div style={{ position: 'relative', zIndex: 3, marginTop: -62 }}>
              <div style={{ borderRadius: 22, padding: 24, background: 'linear-gradient(150deg, rgba(255,150,90,0.12), #19131F)', border: '1px solid rgba(255,170,110,0.28)' }}>
                <ErrorState
                  serifTitle="Bugünün özeti şu an gelmedi — senlik bir şey değil."
                  body="Bağlantı bir soluklandı, çalışman güvende. Hazır olduğunda tekrar dene."
                  onRetry={() => setYeniden((n) => n + 1)}
                  retryLabel="Yeniden dene"
                />
              </div>
            </div>
          ) : !heroHazir ? (
            <div aria-busy="true" aria-label="Bugün yükleniyor" style={{ position: 'relative', zIndex: 3, marginTop: -62 }}>
              <div style={{ borderRadius: 22, padding: 24, background: 'linear-gradient(158deg, rgba(46,32,60,0.92), rgba(24,16,34,0.95))', border: '1px solid rgba(255,180,140,0.2)' }}>
                <Skeleton shape="card" delayMs={0} slowAfterMs={null} />
              </div>
            </div>
          ) : (
            <>
              {/* Görev kartı — ufka oturan */}
              <div style={{ position: 'relative', marginTop: -62, zIndex: 3, borderRadius: 22, padding: 24, background: 'linear-gradient(158deg, rgba(46,32,60,0.92), rgba(24,16,34,0.95))', border: '1px solid rgba(255,180,140,0.2)', boxShadow: '0 24px 60px -22px rgba(0,0,0,0.75), 0 1px 0 rgba(255,255,255,0.06) inset', backdropFilter: 'blur(14px)' }}>
                <div aria-hidden style={{ position: 'absolute', inset: -1, borderRadius: 22, border: '1px solid rgba(255,180,140,0.34)', opacity: 0, animation: reduced ? undefined : 'kiroGlowB 6s ease-in-out infinite', pointerEvents: 'none' }} />
                {gorevYok ? (
                  <div style={{ position: 'relative' }}>
                    <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: '0.12em', color: '#FFAE86', marginBottom: 9 }}>BUGÜNKİ İLK TUĞLA</div>
                    <h2 style={{ margin: '0 0 6px', fontSize: 23, fontWeight: 800, color: '#FCEFE6' }}>Bugün planlı blok yok</h2>
                    <p style={{ margin: 0, fontSize: 13, color: color.dusk.ink2 }}>Dilersen bir konuya başla — küçük bir tuğla da tuğladır.</p>
                  </div>
                ) : (
                  <div style={{ position: 'relative', display: 'grid', gridTemplateColumns: dar800 ? '1fr' : '1fr auto', gap: 20, alignItems: 'center' }}>
                    <div>
                      <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: '0.12em', color: '#FFAE86', marginBottom: 9 }}>BUGÜNKİ İLK TUĞLA</div>
                      <h2 style={{ margin: '0 0 6px', fontSize: 23, fontWeight: 800, color: '#FCEFE6', letterSpacing: '-0.01em' }}>{blok!.baslik}</h2>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 14, fontSize: 13, color: color.dusk.ink2, marginBottom: 16, flexWrap: 'wrap' }}>
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>{IconClock}<span style={numText}>~{blok!.dk} dk</span></span>
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: '#FFB570' }}><span aria-hidden style={{ width: 7, height: 7, borderRadius: '50%', background: '#FFB570' }} />zayıf konun</span>
                        {blokDers && <span style={{ color: '#9B8FB5' }}>{blokDers.ad}</span>}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{ flex: 1, maxWidth: 200, height: 8, borderRadius: 999, background: 'rgba(255,255,255,0.1)', overflow: 'hidden' }}>
                          <div style={{ width: `${gunPct}%`, height: '100%', borderRadius: 999, background: 'linear-gradient(90deg,#FF9E7D,#FF6F91)' }} />
                        </div>
                        <span style={{ ...numText, fontSize: 12, color: '#9B8FB5', fontWeight: 600 }}>bugün {konanT}/{toplamT} tuğla</span>
                      </div>
                    </div>
                    <a href="/soru-cozme" style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 3, width: 104, height: 104, borderRadius: 18, background: 'linear-gradient(135deg,#FF8A5B,#FF5E7E)', color: '#2A1018', textDecoration: 'none', boxShadow: '0 12px 34px -10px rgba(255,94,126,0.65), 0 1px 0 rgba(255,255,255,0.25) inset', justifySelf: dar800 ? 'start' : 'auto' }}>
                      {IconPlay}
                      <span style={{ fontSize: 14, fontWeight: 800 }}>Başla</span>
                    </a>
                  </div>
                )}
              </div>

              {/* Ders kartları */}
              <div style={{ margin: '32px 0 12px', display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
                <h3 style={{ margin: 0, fontSize: 17, fontWeight: 800, color: color.dusk.text, letterSpacing: '-0.01em' }}>Derslerin</h3>
                <span style={{ fontSize: 12.5, color: '#8C8398' }}>hâkimiyet · son 30 gün</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: dar800 ? 'repeat(2,1fr)' : 'repeat(3,1fr)', gap: 12 }}>
                {(dersler ?? []).map((s) => {
                  const renk = color.subject.dark[s.key];
                  return (
                    <a key={s.key} href="/ogrenme-yolu" style={{ position: 'relative', overflow: 'hidden', borderRadius: 14, padding: 16, background: '#19131F', border: '1px solid #2A2236', textDecoration: 'none', display: 'block', boxSizing: 'border-box' }}>
                      <div aria-hidden style={{ position: 'absolute', top: -30, right: -30, width: 90, height: 90, borderRadius: '50%', background: `radial-gradient(circle, ${s.glow}, transparent 70%)` }} />
                      <div style={{ position: 'relative' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 13 }}>
                          <span aria-hidden style={{ width: 10, height: 10, borderRadius: '50%', background: renk, boxShadow: `0 0 10px ${s.glow}`, flexShrink: 0 }} />
                          <span style={{ flex: 1, minWidth: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontSize: 13.5, fontWeight: 700, color: '#E7DEEC' }}>{s.ad}</span>
                          <span style={{ ...numText, marginLeft: 'auto', fontSize: 14, fontWeight: 800, color: renk }}>%{s.hakimiyet}</span>
                        </div>
                        <div style={{ height: 7, borderRadius: 999, background: '#241C30', overflow: 'hidden' }}>
                          <div style={{ width: `${s.hakimiyet}%`, height: '100%', borderRadius: 999, background: renk }} />
                        </div>
                      </div>
                    </a>
                  );
                })}
                <a href="/ogrenme-yolu" style={{ borderRadius: 14, border: '1.5px dashed #2E2740', background: 'transparent', textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 7, minHeight: 92, padding: 16, boxSizing: 'border-box' }}>
                  <span style={{ fontSize: 13, fontWeight: 700, color: '#8C8398' }}>Yolu gör</span>
                  {IconArrow}
                </a>
              </div>

              {/* Sosyal sinyal — baskısız */}
              <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 8, padding: '0 2px' }}>
                <span aria-hidden style={{ width: 20, height: 20, borderRadius: 7, background: 'linear-gradient(135deg,#BE185D,#EC4899)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 9, fontWeight: 800, color: '#fff' }}>EK</span>
                <span style={{ fontSize: 12, fontWeight: 600, color: '#8C8398' }}>Elif de bugün çalıştı</span>
              </div>

              {/* Alt kartlar: FSRS + SEN vs DÜN */}
              <div style={{ display: 'grid', gridTemplateColumns: dar800 ? '1fr' : '1fr 1fr', gap: 12, marginTop: 12 }}>
                <a href="/tekrar" style={{ position: 'relative', overflow: 'hidden', borderRadius: 18, padding: 20, background: 'linear-gradient(150deg, rgba(255,150,90,0.12), #19131F)', border: '1px solid rgba(255,170,110,0.22)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 15, boxSizing: 'border-box' }}>
                  <div style={{ width: 46, height: 46, flexShrink: 0, borderRadius: 14, background: 'rgba(255,170,110,0.16)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{IconRefresh}</div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 15, fontWeight: 800, color: '#F4E6DC' }}>
                      {reviewCount > 0 ? <><span style={numText}>{reviewCount}</span> konu tekrar bekliyor</> : 'Bugün tekrar yok'}
                    </div>
                    <div style={{ fontSize: 12.5, color: '#C29A88', lineHeight: 1.4 }}>
                      {reviewCount > 0 && enZayifReview ? <>{enZayifReview.konu} sevgi istiyor — ~<span style={numText}>{reviewDk}</span> dk yeter.</> : 'Eğrin sağlıklı.'}
                    </div>
                  </div>
                  {IconChevron}
                </a>

                <div style={{ borderRadius: 18, padding: 20, background: 'linear-gradient(150deg, rgba(77,191,160,0.09), #14181A)', border: '1px solid rgba(77,191,160,0.18)', boxSizing: 'border-box' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 11 }}>
                    <span style={{ fontSize: 11.5, fontWeight: 800, letterSpacing: '0.06em', color: '#4FBFA0' }}>SEN vs DÜN</span>
                    <span style={{ ...numText, fontSize: 12, fontWeight: 700, color: '#8FCDB9' }}>+15 dk</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-end', gap: 10, height: 46 }}>
                    <div style={{ flex: 1 }}><div aria-hidden style={{ height: 26, borderRadius: 6, background: '#2A3A36' }} /></div>
                    <div style={{ flex: 1 }}><div aria-hidden style={{ height: 42, borderRadius: 6, background: 'linear-gradient(180deg,#57C9A6,#3AA383)' }} /></div>
                    <div style={{ flex: 2, fontSize: 11.5, color: '#9FC4B6', lineHeight: 1.4, alignSelf: 'center' }}>Sadece dünkü seninle yarışıyorsun.</div>
                  </div>
                </div>
              </div>

              {/* Mood + Mantra */}
              <div style={{ display: 'grid', gridTemplateColumns: dar800 ? '1fr' : '1.5fr 1fr', gap: 12, marginTop: 28 }}>
                <div style={{ borderRadius: 18, padding: 20, background: '#19131F', border: '1px solid #2A2236', boxSizing: 'border-box' }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
                    <span id="mood-baslik" style={{ fontSize: 14, fontWeight: 800, color: color.dusk.text }}>Bugün nasılsın?</span>
                    <span style={{ fontSize: 12, color: '#8C8398' }}>KIRO tonunu ayarlar</span>
                  </div>
                  <div role="radiogroup" aria-labelledby="mood-baslik" style={{ display: 'flex', gap: 8 }}>
                    {MOODS.map((m, i) => {
                      const on = mood === i;
                      return (
                        <button
                          key={m.key}
                          type="button"
                          role="radio"
                          aria-checked={on}
                          onClick={() => pickMood(i)}
                          style={{ flex: '1 1 0', aspectRatio: '1', minWidth: 44, minHeight: 44, borderRadius: 14, border: `1.5px solid ${on ? m.color : '#2E2839'}`, background: on ? 'rgba(255,255,255,0.05)' : '#221B2C', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 4, cursor: 'pointer', boxSizing: 'border-box' }}
                        >
                          <svg aria-hidden width="26" height="26" viewBox="0 0 36 36" fill="none" stroke={on ? m.color : m.color + '8C'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <circle cx="18" cy="18" r="13.5" strokeOpacity="0.4" />
                            <circle cx="13" cy="15.5" r="1.4" fill={on ? m.color : m.color + '8C'} stroke="none" />
                            <circle cx="23" cy="15.5" r="1.4" fill={on ? m.color : m.color + '8C'} stroke="none" />
                            <path d={m.mouth} />
                          </svg>
                          <span style={{ fontSize: 11, fontWeight: 700, color: on ? m.color : m.color + 'C9' }}>{m.label}</span>
                        </button>
                      );
                    })}
                  </div>
                  <div aria-live="polite">
                    {mood != null && (
                      <div style={{ marginTop: 12, padding: 12, borderRadius: 10, background: 'rgba(255,158,125,0.09)', border: '1px solid rgba(255,158,125,0.18)', fontSize: 12.5, color: '#F0CDB8', lineHeight: 1.5 }}>
                        {MOODS[mood]!.msg}
                      </div>
                    )}
                  </div>
                </div>

                <div style={{ borderRadius: 18, padding: 20, background: 'linear-gradient(160deg,#1E1730,#17111F)', border: '1px solid rgba(255,217,140,0.22)', display: 'flex', alignItems: 'center', textAlign: 'center', boxSizing: 'border-box' }}>
                  <p style={{ margin: 0, fontFamily: font.serif, fontStyle: 'italic', fontSize: 17, lineHeight: 1.45, color: '#C4BAD0' }}>“{mantra}”</p>
                </div>
              </div>

              {/* Footer ufuk çizgisi */}
              <div aria-hidden style={{ marginTop: 34, height: 2, borderRadius: 999, background: 'linear-gradient(90deg, transparent, rgba(255,163,92,0.5), transparent)' }} />
            </>
          )}
        </div>
      </div>
    </KiroThemeProvider>
  );
}

export default BugunPage;
