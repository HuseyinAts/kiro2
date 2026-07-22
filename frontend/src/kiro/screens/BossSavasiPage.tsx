// kanon-allow: boss-arena, kutlama
// ============================================================================
// KIRO2 — Boss Savaşı (SPRINT7 · KIRO2 Boss Savasi.dc.html · TEMA = DUSK)
// En koyu kırmızı arena: ejderha = kurgusal düşman kimliği (alarm-semantiği DEĞİL).
// Sunucu-otoriter: dogru + hasar/HP/kombo/can postBossAnswer'dan iner — İSTEMCİ
// HP/kombo/correct HESAPLAMAZ (postCatNext deseni). Kırmızı aile yalnız bu dosyada
// serbest (kanon-allow: boss-arena); kullanıcı-hatası TERRACOTTA #E8836B kalır.
// Zafer konfetisi ConfettiDawn (reuse) — reduced-motion'da kendi içinde kapanır.
// ============================================================================
import * as React from 'react';

import {
  configureKiroApi,
  postBossSession,
  postBossAnswer,
} from '../api/api-client';
import type { BossSession, MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';
import { color, font } from '../tokens';
import { KiroThemeProvider, numText } from '../ui/theme';
import { ConfettiDawn, useReducedMotion } from '../ui/ConfettiDawn';
import { Skeleton } from '../ui/Skeleton';
import { ErrorState } from '../ui/ErrorState';
import '../tokens/tokens.css';

configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });

// --- Kırmızı arena paleti (inline · token DEĞİL — boss-arena istisnası) ---
const KIRMIZI = {
  parlak: '#FB7185',
  koyu: '#BE123C',
  koyu2: '#991B1B',
  koyu3: '#7F1D1D',
  cekirdek: '#641225',
} as const;
const TERRACOTTA = '#E8836B'; // kullanıcı-hatası (kırmızı DEĞİL)
const YESIL = '#1FB683';
const YESIL2 = '#34D399';
const HARF = ['A', 'B', 'C', 'D', 'E'];

interface Combat {
  hp: number;
  kombo: number;
  can: number;
  qIdx: number;
  sel: number | null;
  faz: 'play' | 'reveal' | 'won' | 'lost';
  sonHasar: number;
  sonDogru: boolean;
  dogruIdx: number | null;
}

function atkGuc(kombo: number): number {
  return 280 + (kombo - 1) * 70;
}

const KEYFRAMES = `
@keyframes kfBoss { 0%,100% { transform:translateY(0) scale(1); } 50% { transform:translateY(-5px) scale(1.015); } }
@keyframes kfAura { 0%,100% { opacity:0.55; } 50% { opacity:0.95; } }
@keyframes kfHit { 0%,100% { transform:translateX(0); } 25% { transform:translateX(-8px); } 75% { transform:translateX(8px); } }
@keyframes kpop { 0% { transform:scale(0.5); opacity:0; } 60% { transform:scale(1.12); opacity:1; } 100% { transform:scale(1); opacity:1; } }
`;

const srOnly: React.CSSProperties = {
  position: 'absolute',
  width: 1,
  height: 1,
  padding: 0,
  margin: -1,
  overflow: 'hidden',
  clip: 'rect(0 0 0 0)',
  whiteSpace: 'nowrap',
  border: 0,
};

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

const trFmt = (n: number): string => n.toLocaleString('tr-TR');

// --- Bespoke SVG'ler (dekoratif olanlar aria-hidden) ---
const SimsekSvg = ({ boy = 14, renk = '#FCD34D' }: { boy?: number; renk?: string }) => (
  <svg width={boy} height={boy} viewBox="0 0 24 24" fill={renk} aria-hidden>
    <path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z" />
  </svg>
);

export function BossSavasiPage(): React.ReactElement {
  const reduced = useReducedMotion();
  const darEkran = useMedia('(max-width: 540px)');

  const [oturum, setOturum] = React.useState<BossSession | null>(null);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);
  const [combat, setCombat] = React.useState<Combat | null>(null);
  const bitisRef = React.useRef<HTMLHeadingElement>(null);

  // Oturum yükle / yeniden savaş → tam sıfırlama (state reset, postBossSession yeniden)
  React.useEffect(() => {
    let alive = true;
    setOturum(null);
    setHata(false);
    setCombat(null);
    postBossSession()
      .then((s) => {
        if (!alive) return;
        if (!s.sorular.length) {
          setHata(true);
          return;
        }
        setOturum(s);
        setCombat({
          hp: s.maxHP,
          kombo: 1,
          can: s.maxCan,
          qIdx: 0,
          sel: null,
          faz: 'play',
          sonHasar: 0,
          sonDogru: false,
          dogruIdx: null,
        });
      })
      .catch(() => {
        if (alive) setHata(true);
      });
    return () => {
      alive = false;
    };
  }, [yeniden]);

  const soru = oturum && combat ? oturum.sorular[combat.qIdx] : null;

  const secOpt = React.useCallback((i: number) => {
    setCombat((c) => (c && c.faz === 'play' ? { ...c, sel: i } : c));
  }, []);

  const saldir = React.useCallback(async () => {
    if (!oturum || !combat || combat.faz !== 'play' || combat.sel === null) return;
    const q = oturum.sorular[combat.qIdx];
    const durum = { hp: combat.hp, kombo: combat.kombo, can: combat.can };
    // İSTEMCİ correct/hasar HESAPLAMAZ — sunucudan (mock server-sim) iner.
    const res = await postBossAnswer(q.id, combat.sel, durum);
    setCombat((c) =>
      c
        ? {
            ...c,
            hp: res.hp,
            kombo: res.kombo,
            can: res.can,
            sonHasar: res.hasar,
            sonDogru: res.correct,
            dogruIdx: res.dogru,
            faz: res.sonuc === 'won' ? 'won' : res.sonuc === 'lost' ? 'lost' : 'reveal',
          }
        : c,
    );
  }, [oturum, combat]);

  const sonraki = React.useCallback(() => {
    setCombat((c) =>
      c && oturum
        ? {
            ...c,
            qIdx: (c.qIdx + 1) % oturum.sorular.length,
            sel: null,
            faz: 'play',
            sonHasar: 0,
            sonDogru: false,
            dogruIdx: null,
          }
        : c,
    );
  }, [oturum]);

  const yenidenSavas = React.useCallback(() => setYeniden((n) => n + 1), []);

  // Klavye: 1-4/A-D seçim · Enter saldır (reveal'da sonraki)
  React.useEffect(() => {
    if (!combat || !soru) return;
    const onKey = (e: KeyboardEvent) => {
      if (combat.faz === 'won' || combat.faz === 'lost') return;
      const k = e.key;
      if (k === 'Enter') {
        if (combat.faz === 'play' && combat.sel !== null) {
          e.preventDefault();
          void saldir();
        } else if (combat.faz === 'reveal') {
          e.preventDefault();
          sonraki();
        }
        return;
      }
      if (combat.faz !== 'play') return;
      let idx = -1;
      if (k >= '1' && k <= '5') idx = Number(k) - 1;
      else {
        const up = k.toUpperCase();
        const li = HARF.indexOf(up);
        if (li >= 0) idx = li;
      }
      if (idx >= 0 && idx < soru.secenekler.length) {
        e.preventDefault();
        secOpt(idx);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [combat, soru, saldir, sonraki, secOpt]);

  // Bitiş overlay'inde başlığa odak
  React.useEffect(() => {
    if (combat && (combat.faz === 'won' || combat.faz === 'lost')) {
      bitisRef.current?.focus();
    }
  }, [combat?.faz]);

  const kirmiziAnim = (name: string, spec: string): string | undefined =>
    reduced ? undefined : `${name} ${spec}`;

  return (
    <KiroThemeProvider theme="dusk">
      <div
        className="k-dusk"
        style={{
          minHeight: '100vh',
          background: 'radial-gradient(900px 460px at 50% 8%, #3A0E1E 0%, #160A18 45%, #120A14 100%)',
          color: color.dusk.text,
          fontFamily: font.sans,
          fontSize: 14,
          lineHeight: 1.5,
          position: 'relative',
          overflowX: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          boxSizing: 'border-box',
        }}
      >
        {!reduced && <style>{KEYFRAMES}</style>}

        {hata ? (
          <div style={{ padding: '48px 20px', maxWidth: 480, margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>
            <ErrorState
              serifTitle="Ejderha uyanamadı — senlik bir şey değil."
              body="Boss canlı bir oturum; bağlantı bir soluklandı. Hazır olduğunda tekrar dene — ilerlemen sunucuda güvende."
              onRetry={yenidenSavas}
              retryLabel="Yeniden dene"
            />
          </div>
        ) : !oturum || !combat || !soru ? (
          <div
            aria-busy="true"
            aria-label="Ejderha uyanıyor…"
            style={{ padding: '32px 22px', maxWidth: 760, margin: '0 auto', width: '100%', boxSizing: 'border-box' }}
          >
            <Skeleton shape="card" delayMs={0} slowAfterMs={null} />
          </div>
        ) : (
          (() => {
            const { hp, kombo, can, qIdx, sel, faz, sonHasar, sonDogru, dogruIdx } = combat;
            const playing = faz === 'play';
            const revealing = faz === 'reveal';
            const ended = faz === 'won' || faz === 'lost';
            const won = faz === 'won';
            const ratio = hp / oturum.maxHP;
            const phaseNo = ratio > 0.66 ? 1 : ratio > 0.33 ? 2 : 3;
            const guc = atkGuc(kombo);
            const accent = color.dawn.coral; // #FF6F5C

            const srOzet = revealing
              ? sonDogru
                ? `${sonHasar} hasar verdin. Can ${can}, kombo ${kombo}.`
                : `Iskaladın, 1 can kaybettin. Can ${can}, kombo ${kombo}.`
              : `Can ${can}, kombo ${kombo}.`;

            return (
              <>
                {/* Görünmez tek aria-live bölgesi (her vuruş polite) */}
                <div aria-live="polite" style={srOnly}>
                  {srOzet}
                </div>

                {/* ---- 58px bar ---- */}
                <header
                  style={{
                    height: 58,
                    flexShrink: 0,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 14,
                    padding: '0 22px',
                    boxSizing: 'border-box',
                  }}
                >
                  <a
                    href="/ogrenme-yolu"
                    aria-label="Kapat"
                    style={{
                      width: 38,
                      height: 38,
                      flexShrink: 0,
                      border: '1px solid #3A2230',
                      background: 'rgba(255,255,255,0.03)',
                      borderRadius: 10,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#C9A8B6',
                      textDecoration: 'none',
                    }}
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </a>
                  <div style={{ fontSize: 15.5, fontWeight: 800 }}>Boss Savaşı</div>
                  <span
                    style={{
                      fontSize: 11.5,
                      fontWeight: 800,
                      color: KIRMIZI.parlak,
                      background: 'rgba(244,63,94,0.12)',
                      border: '1px solid rgba(244,63,94,0.3)',
                      padding: '3px 10px',
                      borderRadius: 99,
                      letterSpacing: '0.04em',
                    }}
                  >
                    ZORLU
                  </span>
                  <div style={{ flex: 1 }} />
                  <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                    <span style={{ fontSize: 12.5, fontWeight: 700, color: '#C9A8B6' }}>Faz</span>
                    {[1, 2, 3].map((n) => {
                      const aktif = n === phaseNo;
                      const gecti = n < phaseNo;
                      return (
                        <span
                          key={n}
                          aria-hidden
                          style={{
                            width: aktif ? 11 : 9,
                            height: aktif ? 11 : 9,
                            borderRadius: 99,
                            background: aktif ? KIRMIZI.parlak : gecti ? YESIL : '#3A2230',
                            boxShadow: aktif ? `0 0 8px ${KIRMIZI.parlak}` : 'none',
                          }}
                        />
                      );
                    })}
                    <span style={{ ...numText, fontSize: 12.5, fontWeight: 800, color: color.dusk.text, marginLeft: 2 }}>
                      {phaseNo} / 3
                    </span>
                  </div>
                </header>

                {/* ---- Boss arena ---- */}
                <section style={{ padding: '6px 22px 18px', display: 'flex', flexDirection: 'column', alignItems: 'center', boxSizing: 'border-box' }}>
                  <div
                    aria-hidden
                    style={{
                      position: 'relative',
                      width: 150,
                      height: 150,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      marginBottom: 14,
                      animation: revealing && sonDogru ? kirmiziAnim('kfHit', '.35s ease') : undefined,
                    }}
                  >
                    <div
                      style={{
                        position: 'absolute',
                        inset: -18,
                        borderRadius: 99,
                        background: 'radial-gradient(circle, rgba(244,63,94,0.45) 0%, transparent 68%)',
                        animation: kirmiziAnim('kfAura', '2.4s ease-in-out infinite'),
                      }}
                    />
                    <div style={{ position: 'relative', animation: kirmiziAnim('kfBoss', '3s ease-in-out infinite') }}>
                      <svg width="142" height="142" viewBox="0 0 130 130">
                        <defs>
                          <radialGradient id="bossCore" cx="0.5" cy="0.42" r="0.65">
                            <stop offset="0" stopColor={KIRMIZI.parlak} />
                            <stop offset="0.6" stopColor={KIRMIZI.koyu} />
                            <stop offset="1" stopColor={KIRMIZI.cekirdek} />
                          </radialGradient>
                        </defs>
                        <rect x="20" y="20" width="90" height="90" rx="14" fill={KIRMIZI.koyu3} transform="rotate(0 65 65)" />
                        <rect x="20" y="20" width="90" height="90" rx="14" fill={KIRMIZI.koyu2} transform="rotate(45 65 65)" />
                        <circle cx="65" cy="65" r="44" fill="url(#bossCore)" stroke={KIRMIZI.parlak} strokeWidth="2" />
                        <path d="M44 56 L58 60 L44 66 Z" fill="#160A18" />
                        <path d="M86 56 L72 60 L86 66 Z" fill="#160A18" />
                        <path d="M50 82 L56 76 L62 82 L68 76 L74 82 L80 76" fill="none" stroke="#160A18" strokeWidth="3.4" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    </div>
                    <div
                      style={{
                        position: 'absolute',
                        top: -6,
                        right: 8,
                        width: 30,
                        height: 30,
                        borderRadius: 9,
                        background: '#2A2433',
                        border: `1.5px solid ${KIRMIZI.parlak}`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        ...numText,
                        fontWeight: 800,
                        fontSize: 13,
                        color: KIRMIZI.parlak,
                      }}
                    >
                      {oturum.bossSeviye}
                    </div>
                  </div>

                  <div style={{ fontSize: 24, fontWeight: 800, letterSpacing: '-0.01em' }}>{oturum.bossAd}</div>
                  <div style={{ fontSize: 12.5, color: '#C9A8B6', fontWeight: 600, marginBottom: 9 }}>
                    Konu Canavarı · {oturum.konu}
                  </div>
                  <div
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 7,
                      marginBottom: 16,
                      padding: '5px 12px',
                      borderRadius: 99,
                      background: 'rgba(244,63,94,0.1)',
                      border: '1px solid rgba(244,63,94,0.28)',
                    }}
                  >
                    <SimsekSvg boy={13} renk={KIRMIZI.parlak} />
                    <span style={{ fontSize: 11.5, fontWeight: 700, color: '#FBA5B4' }}>
                      Zayıf noktası: <strong style={{ color: color.dusk.text }}>{oturum.zayifAtom}</strong>
                    </span>
                  </div>

                  {/* Boss CAN barı */}
                  <div style={{ width: '100%', maxWidth: 560, boxSizing: 'border-box' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                      <span style={{ fontSize: 11.5, fontWeight: 800, color: KIRMIZI.parlak, letterSpacing: '0.05em' }}>BOSS CAN</span>
                      <span style={{ ...numText, fontSize: 14, fontWeight: 800, color: color.dusk.text }}>
                        {trFmt(hp)} <span style={{ color: '#7E5566' }}>/ {trFmt(oturum.maxHP)}</span>
                      </span>
                    </div>
                    <div
                      role="progressbar"
                      aria-label="Boss canı"
                      aria-valuenow={hp}
                      aria-valuemin={0}
                      aria-valuemax={oturum.maxHP}
                      style={{ height: 18, borderRadius: 99, background: '#2A1620', border: '1px solid #3A2230', overflow: 'hidden', position: 'relative' }}
                    >
                      <div
                        style={{
                          width: '100%',
                          height: '100%',
                          borderRadius: 99,
                          background: `linear-gradient(90deg, ${KIRMIZI.koyu}, ${KIRMIZI.parlak})`,
                          boxShadow: `0 0 16px -2px ${KIRMIZI.parlak}`,
                          transformOrigin: 'left',
                          transform: `scaleX(${ratio.toFixed(3)})`,
                          transition: reduced ? undefined : 'transform .4s cubic-bezier(.4,0,.2,1)',
                        }}
                      />
                    </div>
                  </div>
                </section>

                {/* ---- Durum şeridi ---- */}
                <section style={{ padding: '0 22px 14px', display: 'flex', justifyContent: 'center', boxSizing: 'border-box' }}>
                  <div
                    style={{
                      width: '100%',
                      maxWidth: 760,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 14,
                      flexWrap: 'wrap',
                      background: 'rgba(255,255,255,0.03)',
                      border: '1px solid #2E1B28',
                      borderRadius: 14,
                      padding: '12px 18px',
                      boxSizing: 'border-box',
                    }}
                  >
                    <span style={{ fontSize: 12, fontWeight: 800, color: '#C9A8B6', letterSpacing: '0.04em' }}>CANLARIN</span>
                    <div aria-hidden style={{ display: 'flex', gap: 5 }}>
                      {Array.from({ length: oturum.maxCan }, (_, i) => {
                        const dolu = i < can;
                        return (
                          <svg key={i} width="22" height="22" viewBox="0 0 24 24" fill={dolu ? TERRACOTTA : 'none'} stroke={dolu ? 'none' : '#5A3848'} strokeWidth="2">
                            <path d="M12 21s-7-4.6-9.5-9C1 9 2.5 5.5 6 5.5c2 0 3.2 1.2 4 2.3.8-1.1 2-2.3 4-2.3 3.5 0 5 3.5 3.5 6.5C19 16.4 12 21 12 21Z" />
                          </svg>
                        );
                      })}
                    </div>
                    <div style={{ flex: 1 }} />
                    <div
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 8,
                        padding: '6px 13px',
                        borderRadius: 99,
                        background: 'rgba(252,211,77,0.12)',
                        border: '1px solid rgba(252,211,77,0.28)',
                      }}
                    >
                      <SimsekSvg boy={16} renk={color.dawn.gold2} />
                      <span style={{ ...numText, fontSize: 15, fontWeight: 800, color: color.dawn.gold2 }}>×{kombo}</span>
                      <span style={{ fontSize: 12, fontWeight: 700, color: '#D9B477' }}>KOMBO</span>
                    </div>
                    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}>
                      <SimsekSvg boy={16} renk={accent} />
                      <span style={{ ...numText, fontSize: 13, fontWeight: 800, color: accent }}>{guc}</span>
                      <span style={{ fontSize: 12, fontWeight: 600, color: '#C9A8B6' }}>saldırı gücü</span>
                    </div>
                  </div>
                </section>

                {/* ---- Savaş kartı ---- */}
                <main style={{ flex: 1, padding: '0 22px 22px', boxSizing: 'border-box' }}>
                  <div
                    style={{
                      maxWidth: 760,
                      margin: '0 auto',
                      background: '#1B1018',
                      border: '1px solid #33202C',
                      borderRadius: 20,
                      padding: '24px 28px',
                      boxShadow: '0 20px 50px -20px rgba(0,0,0,.7)',
                      boxSizing: 'border-box',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
                      <span style={{ fontSize: 13.5, fontWeight: 800, color: '#C9A8B6' }}>SALDIRI SORUSU · {qIdx + 1}</span>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: 12, fontWeight: 700, color: KIRMIZI.parlak }}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                          <circle cx="12" cy="12" r="9" />
                          <polyline points="12 7 12 12 15 14" />
                        </svg>
                        Doğru cevap = <strong style={{ color: color.dusk.text }}>~{guc} hasar</strong>
                      </span>
                    </div>

                    <p style={{ margin: '0 0 22px', fontSize: 18, lineHeight: 1.7, fontWeight: 600 }}>{soru.soru}</p>

                    <div style={{ display: 'grid', gridTemplateColumns: darEkran ? '1fr' : '1fr 1fr', gap: 12 }}>
                      {soru.secenekler.map((metin, i) => {
                        const isSel = i === sel;
                        const isCor = dogruIdx !== null && i === dogruIdx;
                        // Varsayılan (pasif) görünüm
                        let bg = '#231521';
                        let border = '1px solid #33202C';
                        let boxShadow: string | undefined;
                        let badgeBg = '#33202C';
                        let badgeFg = '#C9A8B6';
                        let showHit = false;
                        if (playing) {
                          if (isSel) {
                            bg = '#2A1620';
                            border = `2px solid ${TERRACOTTA}`;
                            boxShadow = '0 0 0 4px rgba(244,63,94,.18)';
                            badgeBg = TERRACOTTA;
                            badgeFg = '#fff';
                          }
                        } else if (isCor) {
                          bg = '#10231C';
                          border = `2px solid ${YESIL}`;
                          badgeBg = YESIL;
                          badgeFg = '#fff';
                          if (sonDogru) showHit = true;
                        } else if (isSel) {
                          bg = '#2A1620';
                          border = `2px solid ${TERRACOTTA}`;
                          badgeBg = TERRACOTTA;
                          badgeFg = '#fff';
                        }
                        const rowStyle: React.CSSProperties = {
                          display: 'flex',
                          alignItems: 'center',
                          gap: 13,
                          padding: '15px 16px',
                          minHeight: 44,
                          borderRadius: 13,
                          textAlign: 'left',
                          fontFamily: font.sans,
                          color: color.dusk.text,
                          cursor: playing ? 'pointer' : 'default',
                          background: bg,
                          border,
                          boxShadow,
                          transition: reduced ? undefined : 'background .15s, border-color .15s',
                          boxSizing: 'border-box',
                        };
                        return (
                          <button
                            key={i}
                            type="button"
                            aria-pressed={isSel}
                            disabled={!playing}
                            onClick={() => secOpt(i)}
                            style={rowStyle}
                          >
                            <span
                              style={{
                                width: 30,
                                height: 30,
                                flexShrink: 0,
                                borderRadius: 9,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontWeight: 800,
                                fontSize: 13.5,
                                background: badgeBg,
                                color: badgeFg,
                              }}
                            >
                              {HARF[i]}
                            </span>
                            <span style={{ ...numText, flex: 1, fontSize: 16, fontWeight: 700 }}>{metin}</span>
                            {showHit && (
                              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 12, fontWeight: 800, color: KIRMIZI.parlak }}>
                                <SimsekSvg boy={13} renk={KIRMIZI.parlak} />−{sonHasar}
                              </span>
                            )}
                          </button>
                        );
                      })}
                    </div>

                    {revealing && (
                      <div
                        style={{
                          marginTop: 16,
                          display: 'flex',
                          alignItems: 'center',
                          gap: 12,
                          background: sonDogru ? 'rgba(16,185,129,0.1)' : 'rgba(244,63,94,0.1)',
                          border: `1px solid ${sonDogru ? 'rgba(16,185,129,0.3)' : 'rgba(244,63,94,0.3)'}`,
                          borderRadius: 13,
                          padding: '13px 18px',
                        }}
                      >
                        {sonDogru ? (
                          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={YESIL2} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                            <path d="M13 2 4 14h6l-1 8 8-12h-6l2-8Z" />
                          </svg>
                        ) : (
                          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={KIRMIZI.parlak} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                            <path d="M12 3 3 7v5c0 5 4 8 9 9 2-.4 3.7-1.3 5-2.6" />
                            <path d="m15 9-6 6M9 9l6 6" />
                          </svg>
                        )}
                        <div style={{ fontSize: 14, fontWeight: 800, color: sonDogru ? YESIL2 : KIRMIZI.parlak }}>
                          {sonDogru
                            ? `${sonHasar} hasar verdin! Kombo ×${kombo} — vur vur!`
                            : 'Iskaladın — 1 can kaybettin. Kombo sıfırlandı.'}
                        </div>
                      </div>
                    )}

                    <button
                      type="button"
                      onClick={revealing ? sonraki : saldir}
                      disabled={playing && sel === null}
                      style={{
                        width: '100%',
                        marginTop: revealing ? 16 : 20,
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 10,
                        height: 52,
                        border: 'none',
                        borderRadius: 14,
                        background: revealing ? accent : `linear-gradient(90deg, ${KIRMIZI.koyu}, ${TERRACOTTA})`,
                        color: '#fff',
                        fontFamily: font.sans,
                        fontSize: 15.5,
                        fontWeight: 800,
                        cursor: playing && sel === null ? 'default' : 'pointer',
                        opacity: playing && sel === null ? 0.5 : 1,
                        boxShadow: revealing ? undefined : '0 10px 26px -8px rgba(244,63,94,.6)',
                        boxSizing: 'border-box',
                      }}
                    >
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                        <path d="m14.5 3-9 9h5l-1.5 9 9-11h-5z" />
                      </svg>
                      {revealing ? 'Sonraki saldırı' : 'Saldır!'}
                    </button>
                  </div>

                  {/* Ödül şeridi */}
                  <div style={{ maxWidth: 760, margin: '14px auto 0', display: 'flex', alignItems: 'center', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: 12.5, fontWeight: 700, color: '#C9A8B6' }}>Ejderhayı yenersen:</span>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7, ...numText, fontSize: 13, fontWeight: 800, color: color.dawn.gold2, background: 'rgba(252,211,77,0.1)', border: '1px solid rgba(252,211,77,0.22)', padding: '6px 13px', borderRadius: 99 }}>
                      <SimsekSvg boy={14} renk={color.dawn.gold2} />+{oturum.odulXp} XP
                    </span>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: 13, fontWeight: 800, color: '#FFC98A', background: 'rgba(255,181,112,0.12)', border: '1px solid rgba(255,181,112,0.3)', padding: '6px 13px', borderRadius: 99 }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                        <circle cx="12" cy="8" r="6" />
                        <path d="M8.2 13.9 7 22l5-3 5 3-1.2-8.1" />
                      </svg>
                      {oturum.odulRozet}
                    </span>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: 13, fontWeight: 800, color: YESIL2, background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.28)', padding: '6px 13px', borderRadius: 99 }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      Konu fethi
                    </span>
                  </div>
                </main>

                {/* ---- Bitiş overlay'i ---- */}
                {ended && (
                  <div
                    role="dialog"
                    aria-modal="true"
                    aria-label={won ? 'Zafer' : 'Yenilgi'}
                    onKeyDown={(e) => {
                      // Odak tuzağı: Tab dialog içinde döner (aria-modal gereği; arka plan erişilmez)
                      if (e.key !== 'Tab') return;
                      const f = Array.from(e.currentTarget.querySelectorAll<HTMLElement>('a[href], button:not([disabled])'));
                      if (f.length === 0) return;
                      const first = f[0]!;
                      const last = f[f.length - 1]!;
                      const inside = f.includes(document.activeElement as HTMLElement);
                      if (e.shiftKey && (!inside || document.activeElement === first)) { e.preventDefault(); last.focus(); }
                      else if (!e.shiftKey && (!inside || document.activeElement === last)) { e.preventDefault(); first.focus(); }
                    }}
                    style={{
                      position: 'fixed',
                      inset: 0,
                      zIndex: 60,
                      background: 'rgba(10,5,12,0.82)',
                      backdropFilter: 'blur(4px)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      padding: 24,
                      boxSizing: 'border-box',
                    }}
                  >
                    {won && <ConfettiDawn count={26} zIndex={61} />}
                    <div
                      style={{
                        position: 'relative',
                        zIndex: 62,
                        width: '100%',
                        maxWidth: 440,
                        background: '#1B1018',
                        border: `1px solid ${won ? 'rgba(252,211,77,0.4)' : 'rgba(244,63,94,0.4)'}`,
                        borderRadius: 22,
                        padding: '34px 30px',
                        textAlign: 'center',
                        boxShadow: '0 30px 70px -20px rgba(0,0,0,0.8)',
                        boxSizing: 'border-box',
                      }}
                    >
                      <div
                        aria-hidden
                        style={{
                          width: 74,
                          height: 74,
                          margin: '0 auto 16px',
                          borderRadius: 22,
                          background: won ? 'linear-gradient(135deg,#CA8A04,#FCD34D)' : `linear-gradient(135deg,${KIRMIZI.koyu3},${KIRMIZI.koyu})`,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          animation: kirmiziAnim('kpop', '.55s cubic-bezier(.22,1.4,.5,1) both'),
                        }}
                      >
                        {won ? (
                          <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={1.9} strokeLinecap="round" strokeLinejoin="round">
                            <path d="M8 4h8v4a4 4 0 0 1-8 0Z" />
                            <path d="M8 5H5v1a3 3 0 0 0 3 3M16 5h3v1a3 3 0 0 1-3 3" />
                            <path d="M12 12v3" />
                            <path d="M9.5 20h5l-.7-3h-3.6Z" />
                          </svg>
                        ) : (
                          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={1.9} strokeLinecap="round" strokeLinejoin="round">
                            <path d="M12 3 5 6v5c0 4 3.2 6.8 7 8 3.8-1.2 7-4 7-8V6Z" />
                            <path d="m9 10 3 3 3-3" />
                          </svg>
                        )}
                      </div>
                      <h2 ref={bitisRef} tabIndex={-1} style={{ margin: '0 0 6px', fontSize: 26, fontWeight: 800, outline: 'none' }}>
                        {won ? 'Ejderhayı yendin!' : 'Henüz değil'}
                      </h2>
                      <p style={{ margin: '0 0 22px', fontSize: 14, color: '#C9A8B6', lineHeight: 1.55 }}>
                        {won
                          ? `${oturum.konu} konusunu fethettin — lig sıran ve XP’n yükseldi.`
                          : 'Bu tur ejderha güçlüydü — birkaç tekrar, sonra yeniden deneriz. Kaybeden yok; sadece “henüz” olan var.'}
                      </p>

                      {won && (
                        <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap', marginBottom: 22 }}>
                          <span style={{ ...numText, display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12.5, fontWeight: 800, color: color.dawn.gold2, background: 'rgba(252,211,77,0.12)', padding: '6px 12px', borderRadius: 99 }}>
                            +{oturum.odulXp} XP
                          </span>
                          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12.5, fontWeight: 800, color: '#FFC98A', background: 'rgba(255,181,112,0.14)', padding: '6px 12px', borderRadius: 99 }}>
                            {oturum.odulRozet}
                          </span>
                          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12.5, fontWeight: 800, color: YESIL2, background: 'rgba(16,185,129,0.14)', padding: '6px 12px', borderRadius: 99 }}>
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                              <polyline points="20 6 9 17 4 12" />
                            </svg>
                            Konu fethi
                          </span>
                        </div>
                      )}

                      {won && (
                        <a
                          href="/kutlama?type=boss"
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: 10,
                            width: '100%',
                            height: 52,
                            marginBottom: 11,
                            border: 'none',
                            borderRadius: 14,
                            background: 'linear-gradient(110deg,#E0A82E,#FCD34D)',
                            color: '#2A1018',
                            fontFamily: font.sans,
                            fontSize: 15,
                            fontWeight: 800,
                            textDecoration: 'none',
                            boxShadow: '0 12px 30px -10px rgba(252,211,77,0.55)',
                            boxSizing: 'border-box',
                          }}
                        >
                          <svg width="19" height="19" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
                            <path d="M12 2l2.9 6.26 6.9.7-5.13 4.64L18 21l-6-3.5L6 21l1.33-7.4L2.2 8.96l6.9-.7L12 2Z" />
                          </svg>
                          Zaferi kutla
                        </a>
                      )}

                      <div style={{ display: 'flex', gap: 11 }}>
                        <button
                          type="button"
                          onClick={yenidenSavas}
                          style={{
                            flex: 1,
                            height: 48,
                            border: won ? '1px solid #3A2230' : 'none',
                            borderRadius: 13,
                            background: won ? 'rgba(255,255,255,0.04)' : `linear-gradient(90deg,${KIRMIZI.koyu},${TERRACOTTA})`,
                            color: won ? color.dusk.text : '#fff',
                            fontFamily: font.sans,
                            fontSize: 14.5,
                            fontWeight: 800,
                            cursor: 'pointer',
                            boxSizing: 'border-box',
                          }}
                        >
                          {won ? 'Yeniden savaş' : 'Hazırlan, geri dön'}
                        </button>
                        <a
                          href="/ogrenme-yolu"
                          style={{
                            flex: 1,
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            height: 48,
                            border: '1px solid #3A2230',
                            borderRadius: 13,
                            background: 'rgba(255,255,255,0.04)',
                            color: color.dusk.text,
                            fontFamily: font.sans,
                            fontSize: 14,
                            fontWeight: 700,
                            textDecoration: 'none',
                            boxSizing: 'border-box',
                          }}
                        >
                          Öğrenme Yolu
                        </a>
                      </div>
                    </div>
                  </div>
                )}
              </>
            );
          })()
        )}
      </div>
    </KiroThemeProvider>
  );
}

export default BossSavasiPage;
