// kanon-allow: boss-arena, kutlama
// ============================================================================
// KIRO2 — 1v1 Düello (SPRINT8 · Grup 6 · KIRO2 Duello.dc.html · TEMA = DUSK)
// Arena-lacivert oyun-sahnesi (#0A0E1B / #16203B / #141A2C) — kurgusal 1v1 arena
// kimliği; alarm-semantiği DEĞİL. Süre halkasının renk-shift'i = TEMPO (kırmızı-
// alarm değil). Aksan CORAL #FF6F5C (teal proto DEĞİL); doğru YEŞİL, kullanıcı-hata
// ve rakip TERRACOTTA #E8836B (alarm-kırmızı #FB7185 sızmaz).
// Sunucu-otoriter: benDogru/puan/tur-sonucu/skor/maç-sonucu/elo HEP API'den —
// postDuelMatchmake → getDuelCurrentQuestion → postDuelAnswer → getDuelResult;
// rakip cevapları + bitiş duelStream(handlers) ile (EKRAN EventSource AÇMAZ, yalnız
// abone olur + cleanup'ta unsubscribe). Ekran puan/skor/kim-kazandı HESAPLAMAZ
// (proto Math.random + lock skorlaması TAŞINMADI). Zafer konfetisi ConfettiDawn.
// ============================================================================
import * as React from 'react';

import {
  configureKiroApi,
  postDuelMatchmake,
  getDuelCurrentQuestion,
  postDuelAnswer,
  getDuelResult,
  duelStream,
  getMe,
} from '../api/api-client';
import type { DuelMatch, DuelQuestion, DuelResult, DuelTurSonucu, MockData } from '../api/api-client';
import type { Persona } from '../types';
import kiroData from '../api/kiro-data.json';
import { color, font } from '../tokens';
import { KiroThemeProvider, numText } from '../ui/theme';
import { ConfettiDawn, useReducedMotion } from '../ui/ConfettiDawn';
import { Skeleton } from '../ui/Skeleton';
import { ErrorState } from '../ui/ErrorState';
import '../tokens/tokens.css';

configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });

const HARF = ['A', 'B', 'C', 'D', 'E'];

// --- Arena-lacivert paleti (inline · token DEĞİL — oyun-sahnesi istisnası) ---
const ARENA = {
  radial: 'radial-gradient(1200px 500px at 50% -5%, #16203B 0%, #0A0E1B 60%)',
  card: '#141A2C',
  border: '#252C44',
  border2: '#2A3350',
  opt: '#1B2236',
  correctBg: '#10231C',
  wrongBg: '#2A1620',
  ringTrack: '#1E2540',
  dotDim: '#1E2540',
  neutralBadge: '#2A3350',
  darkInk: '#0A0E1B', // parlak rozet üstünde koyu harf (beyaz AA'yı geçemez → koyu harf)
  meGrad: 'linear-gradient(135deg,#2A2433,#4A4456)',
  oppGrad: 'linear-gradient(135deg,#9A3520,#C2452B)',
} as const;

const CORAL = color.dawn.coral; // #FF6F5C — aksan
const TERRA = '#E8836B'; // terracotta — kullanıcı-hata / rakip (alarm-kırmızı DEĞİL)
const YESIL = color.semantic.success; // #1FB683 — doğru
const YESIL2 = color.semantic.success2; // #34D399
const NOTR = '#C4BBAE'; // berabere nötr metin (dark üstünde AA)
const MUT = color.dusk.ink2; // #B6A6C4 — dusk ikincil (AA-güvenli; dusk'ta #8A8398 YASAK)
const TXT = color.dusk.text; // #F1E9F2
const GOLD = color.dawn.gold2; // #FCD34D

const MOD_LABEL: Record<string, string> = {
  mat: 'Matematik', fiz: 'Fizik', kim: 'Kimya', biy: 'Biyoloji', tur: 'Türkçe',
};

const KEYFRAMES = `
@keyframes kfRing { 0%,100% { box-shadow:0 0 0 0 rgba(232,131,107,.55);} 50% { box-shadow:0 0 0 8px rgba(232,131,107,0);} }
@keyframes kpop { 0% { transform:scale(0.5); opacity:0; } 60% { transform:scale(1.12); opacity:1; } 100% { transform:scale(1); opacity:1; } }
`;

const srOnly: React.CSSProperties = {
  position: 'absolute', width: 1, height: 1, padding: 0, margin: -1,
  overflow: 'hidden', clip: 'rect(0 0 0 0)', whiteSpace: 'nowrap', border: 0,
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

const sn = (ms: number): number => Math.max(0, Math.round(ms / 1000));

// --- Bespoke SVG'ler (emoji/metin-glyph YOK; dekoratif olanlar aria-hidden) ---
const IcSpark = ({ boy = 15, renk = GOLD }: { boy?: number; renk?: string }) => (
  <svg width={boy} height={boy} viewBox="0 0 24 24" fill={renk} aria-hidden>
    <path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z" />
  </svg>
);
const IcCheck = ({ boy = 15, renk = 'currentColor' }: { boy?: number; renk?: string }) => (
  <svg width={boy} height={boy} viewBox="0 0 24 24" fill="none" stroke={renk} strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

type Faz = 'play' | 'reveal' | 'done';
// Stream onAnswer YALNIZ rakip durum-pili besler; tur kazananı (turSonucu) postDuelAnswer'da.
interface RakipTur { rakipDogru: boolean; rakipSure: number }

export function DuelloPage(): React.ReactElement {
  const reduced = useReducedMotion();
  const dar = useMedia('(max-width: 560px)');

  const [match, setMatch] = React.useState<DuelMatch | null>(null);
  const [persona, setPersona] = React.useState<Persona | null>(null);
  const [soru, setSoru] = React.useState<DuelQuestion | null>(null);
  const [faz, setFaz] = React.useState<Faz>('play');
  const [sel, setSel] = React.useState<string | null>(null); // kilitlenen harf (reveal vurgusu)
  const [benSureMs, setBenSureMs] = React.useState(0);
  const [benDogru, setBenDogru] = React.useState(false);
  const [skor, setSkor] = React.useState<{ ben: number; rakip: number }>({ ben: 0, rakip: 0 });
  const [timeLeft, setTimeLeft] = React.useState(0);
  const [sonuc, setSonuc] = React.useState<DuelResult | null>(null);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);
  const [, setRevealBump] = React.useState(0); // reveal'de geç gelen rakip olayı için re-render

  const fazRef = React.useRef<Faz>('play');
  const rakipRef = React.useRef<RakipTur[]>([]); // duelStream onAnswer birikimi (order sıralı)
  const turSonucRef = React.useRef<(DuelTurSonucu | undefined)[]>([]); // tur kazananı postDuelAnswer'dan (SUNUCUDAN)
  const finalRef = React.useRef<DuelResult | null>(null); // onFinished yedeği (getDuelResult başarısızsa fallback)
  const roundStartRef = React.useRef<number>(0);
  const unsubRef = React.useRef<(() => void) | null>(null);
  const bitisRef = React.useRef<HTMLHeadingElement>(null);

  const setFazBoth = React.useCallback((f: Faz) => {
    fazRef.current = f;
    setFaz(f);
  }, []);

  // --- Oturum yükle / rematch → tam sıfırlama (matchmake + me + ilk soru + stream) ---
  React.useEffect(() => {
    let alive = true;
    setHata(false);
    setMatch(null);
    setSoru(null);
    setSonuc(null);
    setSel(null);
    setBenDogru(false);
    setSkor({ ben: 0, rakip: 0 });
    fazRef.current = 'play';
    setFaz('play');
    rakipRef.current = [];
    turSonucRef.current = [];
    finalRef.current = null;

    (async () => {
      try {
        const [m, me] = await Promise.all([postDuelMatchmake('mat'), getMe()]);
        if (!alive) return;
        const q = await getDuelCurrentQuestion(m.sessionId);
        if (!alive) return;
        if (!q) {
          setHata(true);
          return;
        }
        setMatch(m);
        setPersona(me);
        setSoru(q);
        setTimeLeft(q.sure);
        roundStartRef.current = Date.now();
        // Ekran EventSource açmaz — yalnız duelStream(handlers); cleanup unsubscribe.
        unsubRef.current = duelStream(m.sessionId, {
          onAnswer: (d) => {
            rakipRef.current.push(d);
            if (fazRef.current === 'reveal') setRevealBump((n) => n + 1);
          },
          onFinished: (r) => {
            finalRef.current = r;
          },
          onError: () => {
            if (alive) setHata(true);
          },
        });
      } catch {
        if (alive) setHata(true);
      }
    })();

    return () => {
      alive = false;
      if (unsubRef.current) {
        unsubRef.current();
        unsubRef.current = null;
      }
    };
  }, [yeniden]);

  // --- Cevabı kilitle (tıklama = commit; süre bitince harf=null) ---
  const kilitle = React.useCallback(
    async (harf: string | null) => {
      if (!match || !soru || fazRef.current !== 'play') return;
      fazRef.current = 'reveal'; // çift-kilit koruması (state async)
      const timeMs = Math.max(0, Date.now() - roundStartRef.current);
      setSel(harf);
      setBenSureMs(timeMs);
      try {
        // İSTEMCİ doğruluk/puan/tur-sonucu HESAPLAMAZ — sunucudan (mock server-sim) iner.
        const res = await postDuelAnswer(match.sessionId, soru.order, harf ?? '', timeMs);
        setBenDogru(res.benDogru);
        setSkor({ ben: res.benPuan, rakip: res.rakipPuan });
        turSonucRef.current[soru.order] = res.turSonucu; // tur kazananı SUNUCUDAN (band + noktalar)
        setFaz('reveal');
      } catch {
        setHata(true);
      }
    },
    [match, soru],
  );

  // --- Sonraki tur / sonuç ---
  const sonucuGor = React.useCallback(async () => {
    if (!match) return;
    try {
      const r = await getDuelResult(match.sessionId); // maç-sonucu/skor/elo SUNUCUDAN
      setSonuc(r);
      setFazBoth('done');
    } catch {
      // getDuelResult başarısız — SSE onFinished sonucu geldiyse onu yedek olarak göster.
      if (finalRef.current) {
        setSonuc(finalRef.current);
        setFazBoth('done');
      } else {
        setHata(true);
      }
    }
  }, [match, setFazBoth]);

  const sonraki = React.useCallback(async () => {
    if (!match) return;
    try {
      const q = await getDuelCurrentQuestion(match.sessionId);
      if (!q) {
        await sonucuGor();
        return;
      }
      setSoru(q);
      setSel(null);
      setBenDogru(false);
      setTimeLeft(q.sure);
      roundStartRef.current = Date.now();
      setFazBoth('play');
    } catch {
      setHata(true);
    }
  }, [match, sonucuGor, setFazBoth]);

  const yenidenOyna = React.useCallback(() => setYeniden((n) => n + 1), []);

  const sonTur = !!match && !!soru && soru.order >= match.toplamTur - 1;
  const ilerle = React.useCallback(() => {
    if (sonTur) void sonucuGor();
    else void sonraki();
  }, [sonTur, sonucuGor, sonraki]);

  // --- Süre halkası: saniyede bir azalır; 0'da otomatik kilitlenir (play) ---
  React.useEffect(() => {
    if (faz !== 'play' || !soru) return undefined;
    const id = window.setTimeout(() => setTimeLeft((t) => (t > 0 ? t - 1 : 0)), 1000);
    return () => window.clearTimeout(id);
  }, [faz, soru, timeLeft]);

  React.useEffect(() => {
    if (faz === 'play' && soru && timeLeft === 0) void kilitle(null);
  }, [faz, soru, timeLeft, kilitle]);

  // --- Klavye: play → 1-5/A-E kilitle · reveal → Enter ilerle (done overlay kendi tuzağı) ---
  React.useEffect(() => {
    if (!soru || faz === 'done') return undefined;
    const onKey = (e: KeyboardEvent) => {
      if (fazRef.current === 'play') {
        let idx = -1;
        if (e.key >= '1' && e.key <= '5') idx = Number(e.key) - 1;
        else {
          const li = HARF.indexOf(e.key.toUpperCase());
          if (li >= 0) idx = li;
        }
        if (idx >= 0 && idx < soru.secenekler.length) {
          e.preventDefault();
          void kilitle(HARF[idx]);
        }
      } else if (fazRef.current === 'reveal' && e.key === 'Enter') {
        e.preventDefault();
        ilerle();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [soru, faz, kilitle, ilerle]);

  // --- Bitiş overlay'inde başlığa programatik odak ---
  React.useEffect(() => {
    if (faz === 'done') bitisRef.current?.focus();
  }, [faz]);

  const anim = (spec: string): string | undefined => (reduced ? undefined : spec);

  return (
    <KiroThemeProvider theme="dusk">
      <div
        className="k-dusk"
        style={{
          minHeight: '100vh',
          width: '100%',
          background: ARENA.radial,
          color: TXT,
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
              serifTitle="Rakip şu an bulunamadı — senlik bir şey değil."
              body="Düello canlı bir eşleşme; bağlantı bir soluklandı. Hazır olduğunda tekrar dene — puanların ve serin güvende."
              onRetry={yenidenOyna}
              retryLabel="Yeniden eşleş"
            />
          </div>
        ) : !match || !soru || !persona ? (
          <div
            aria-busy="true"
            aria-label="Rakip eşleştiriliyor…"
            style={{ padding: '32px 22px', maxWidth: 760, margin: '0 auto', width: '100%', boxSizing: 'border-box' }}
          >
            <Skeleton shape="card" delayMs={0} slowAfterMs={null} />
          </div>
        ) : (
          (() => {
            const playing = faz === 'play';
            const revealing = faz === 'reveal';
            const bitti = faz === 'done';
            const accent = CORAL;
            const av = dar ? 48 : 66;
            const avFont = dar ? 18 : 23;

            const meIni = persona.bas;
            const meName = persona.adKisa;
            const meLvl = persona.seviye;
            const oppLvl = persona.seviye; // adil 1v1: rakip senin seviyende
            const oppFirst = match.rakip.ad.split(' ')[0] || match.rakip.ad;

            const selIndex = sel !== null ? HARF.indexOf(sel) : -1;
            const ev = !playing ? rakipRef.current[soru.order] : undefined; // YALNIZ rakip durum-pili
            const turSonuc = !playing ? turSonucRef.current[soru.order] : undefined; // tur kazananı SUNUCUDAN
            const bekliyor = revealing && !ev;

            // Süre halkası (transform/anim değil — SVG dashoffset; renk-shift TEMPO)
            const azKaldi = playing && timeLeft <= Math.max(3, Math.round(soru.sure * 0.12));
            const ringColor = playing ? (azKaldi ? TERRA : accent) : ARENA.border2;
            const oran = soru.sure > 0 ? timeLeft / soru.sure : 0;
            const ringOffset = (263.9 * (1 - oran)).toFixed(1);

            // Tur noktaları — geçmiş turlar turSonucRef'ten (postDuelAnswer → SUNUCUDAN); ekran tally etmez
            const noktaRenk = (i: number): string => {
              const ts = turSonucRef.current[i];
              const revealed = i < soru.order || (i === soru.order && !playing);
              if (revealed && ts) {
                return ts === 'me' ? YESIL : ts === 'opp' ? TERRA : '#4A4456';
              }
              if (i === soru.order && playing) return accent;
              return ARENA.dotDim;
            };

            // Rakip durum pili
            const oppStatus = playing || bekliyor
              ? { text: 'Rakip cevaplıyor…', fg: MUT, bg: 'rgba(255,255,255,0.05)', bd: ARENA.border, ic: null as React.ReactNode }
              : {
                  text: `${oppFirst} ${ev!.rakipDogru ? 'doğru' : 'yanlış'} · ${sn(ev!.rakipSure)} sn`,
                  fg: ev!.rakipDogru ? YESIL2 : TERRA,
                  bg: ev!.rakipDogru ? 'rgba(16,185,129,0.12)' : 'rgba(232,131,107,0.14)',
                  bd: ev!.rakipDogru ? 'rgba(16,185,129,0.25)' : 'rgba(232,131,107,0.3)',
                  ic: ev!.rakipDogru
                    ? <IcCheck boy={12} renk={YESIL2} />
                    : (
                      <svg width={12} height={12} viewBox="0 0 24 24" fill="none" stroke={TERRA} strokeWidth={2.4} strokeLinecap="round" aria-hidden>
                        <path d="M6 6 18 18M18 6 6 18" />
                      </svg>
                    ),
                };

            // Tur-sonuç bandı içeriği (turSonucu SUNUCUDAN)
            const resMap = {
              me: { fg: YESIL2, bg: 'rgba(16,185,129,0.1)', bd: 'rgba(16,185,129,0.3)', title: 'Turu kazandın!', sub: benDogru ? 'Doğru ve hızlıydın — puanlar senin.' : `${oppFirst} de bilemedi.` },
              opp: { fg: TERRA, bg: 'rgba(232,131,107,0.12)', bd: 'rgba(232,131,107,0.32)', title: `${oppFirst} turu aldı`, sub: benDogru ? `Doğruydun ama ${oppFirst} daha hızlıydı.` : 'Bu turda doğru cevabı kaçırdın.' },
              draw: { fg: NOTR, bg: 'rgba(255,255,255,0.06)', bd: 'rgba(255,255,255,0.16)', title: 'Berabere', sub: 'İkiniz de bu turda puan alamadınız.' },
            } as const;
            const res = turSonuc ? resMap[turSonuc] : null;

            const won = !!sonuc && sonuc.kazandin;
            const tie = !!sonuc && sonuc.berabere;

            return (
              <>
                {/* Görünmez tek aria-live bölgesi (skor polite) */}
                <div aria-live="polite" style={srOnly}>
                  {`Skor: sen ${skor.ben}, ${oppFirst} ${skor.rakip}.`}
                </div>

                {/* ---- Slim bar ---- */}
                <header
                  style={{
                    minHeight: 58,
                    flexShrink: 0,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 14,
                    flexWrap: 'wrap',
                    rowGap: 6,
                    padding: '0 22px',
                    boxSizing: 'border-box',
                  }}
                >
                  <a
                    href="/lig"
                    aria-label="Kapat"
                    style={{
                      width: 38, height: 38, flexShrink: 0, border: `1px solid ${ARENA.border}`,
                      background: 'rgba(255,255,255,0.03)', borderRadius: 10, display: 'flex',
                      alignItems: 'center', justifyContent: 'center', color: color.dusk.iconMuted,
                      textDecoration: 'none', boxSizing: 'border-box',
                    }}
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </a>
                  <div style={{ fontSize: 15.5, fontWeight: 800, letterSpacing: '0.01em' }}>1v1 Düello</div>
                  <span style={{ fontSize: 12, fontWeight: 700, color: MUT, background: 'rgba(255,255,255,0.05)', border: `1px solid ${ARENA.border}`, padding: '3px 10px', borderRadius: 99, boxSizing: 'border-box' }}>
                    {(MOD_LABEL[match.mod] ?? 'Matematik')} · Hızlı
                  </span>
                  <div style={{ flex: 1 }} />
                  <span style={{ ...numText, fontSize: 12.5, fontWeight: 700, color: MUT }}>
                    En iyi {match.toplamTur} · şu an <strong style={{ color: TXT }}>Tur {Math.min(soru.order + 1, match.toplamTur)}</strong>
                  </span>
                </header>

                {/* ---- VS bandı ---- */}
                <section style={{ padding: '8px 22px 22px', boxSizing: 'border-box' }}>
                  <div
                    style={{
                      maxWidth: 1000, margin: '0 auto', display: 'grid',
                      gridTemplateColumns: 'minmax(0,1fr) auto minmax(0,1fr)',
                      alignItems: 'center', gap: dar ? 10 : 20,
                    }}
                  >
                    {/* SEN */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 16, minWidth: 0 }}>
                      <div
                        style={{
                          width: av, height: av, flexShrink: 0, borderRadius: 18, background: ARENA.meGrad,
                          display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800,
                          fontSize: avFont, color: '#fff', border: `3px solid ${accent}`,
                          boxShadow: `0 0 22px -4px ${accent}aa`, boxSizing: 'border-box',
                        }}
                      >
                        {meIni}
                      </div>
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontSize: 16, fontWeight: 800, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{meName}</div>
                        <div style={{ ...numText, fontSize: 12, color: MUT, fontWeight: 600 }}>Seviye {meLvl} · Sen</div>
                        <div style={{ ...numText, fontSize: 30, fontWeight: 800, color: accent, lineHeight: 1.1 }}>{skor.ben}</div>
                      </div>
                    </div>

                    {/* ORTA — skor + süre halkası + tur noktaları */}
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                        <span style={{ ...numText, fontSize: 30, fontWeight: 800, color: accent }}>{skor.ben}</span>
                        <span style={{ fontSize: 16, fontWeight: 800, color: '#4A4456' }} aria-hidden>—</span>
                        <span style={{ ...numText, fontSize: 30, fontWeight: 800, color: TERRA }}>{skor.rakip}</span>
                      </div>
                      <div
                        role="timer"
                        aria-label={playing ? `kalan ${timeLeft} saniye` : 'tur tamamlandı'}
                        style={{ position: 'relative', width: 96, height: 96 }}
                      >
                        <svg width="96" height="96" viewBox="0 0 96 96" aria-hidden>
                          <circle cx="48" cy="48" r="42" fill="none" stroke={ARENA.ringTrack} strokeWidth="8" />
                          <circle
                            cx="48" cy="48" r="42" fill="none" stroke={ringColor} strokeWidth="8"
                            strokeLinecap="round" strokeDasharray="263.9" strokeDashoffset={ringOffset}
                            transform="rotate(-90 48 48)"
                            style={{ transition: reduced ? undefined : 'stroke-dashoffset 1s linear, stroke .2s' }}
                          />
                        </svg>
                        <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                          {playing ? (
                            <>
                              <span style={{ ...numText, fontSize: 30, fontWeight: 800, lineHeight: 1 }}>{timeLeft}</span>
                              <span style={{ fontSize: 10, fontWeight: 700, color: MUT }}>saniye</span>
                            </>
                          ) : (
                            <>
                              <IcCheck boy={26} renk={YESIL2} />
                              <span style={{ ...numText, fontSize: 10, fontWeight: 700, color: MUT }}>tur {Math.min(soru.order + 1, match.toplamTur)}</span>
                            </>
                          )}
                        </div>
                      </div>
                      {!dar && (
                        <div style={{ display: 'flex', gap: 6 }} aria-hidden>
                          {Array.from({ length: match.toplamTur }, (_, i) => (
                            <span key={i} style={{ width: 18, height: 6, borderRadius: 99, background: noktaRenk(i) }} />
                          ))}
                        </div>
                      )}
                    </div>

                    {/* RAKİP */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexDirection: 'row-reverse', textAlign: 'right', minWidth: 0 }}>
                      <div
                        style={{
                          width: av, height: av, flexShrink: 0, borderRadius: 18, background: ARENA.oppGrad,
                          display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800,
                          fontSize: avFont, color: '#fff', border: `3px solid ${TERRA}`, boxSizing: 'border-box',
                          animation: playing ? anim('kfRing 1.6s ease-in-out infinite') : undefined,
                        }}
                      >
                        {match.rakip.ini}
                      </div>
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontSize: 16, fontWeight: 800, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{match.rakip.ad}</div>
                        <div style={{ ...numText, fontSize: 12, color: MUT, fontWeight: 600 }}>Seviye {oppLvl} · Rakip</div>
                        <div style={{ ...numText, fontSize: 30, fontWeight: 800, color: TERRA, lineHeight: 1.1 }}>{skor.rakip}</div>
                      </div>
                    </div>
                  </div>
                </section>

                {/* ---- Soru kartı ---- */}
                <main style={{ flex: 1, padding: '0 22px 26px', boxSizing: 'border-box' }}>
                  <div
                    style={{
                      maxWidth: 760, margin: '0 auto', background: ARENA.card, border: `1px solid ${ARENA.border}`,
                      borderRadius: 20, padding: '26px 28px', boxShadow: '0 20px 50px -20px rgba(0,0,0,.6)', boxSizing: 'border-box',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', marginBottom: 18 }}>
                      <span style={{ ...numText, fontSize: 14, fontWeight: 800, color: MUT }}>SORU {Math.min(soru.order + 1, match.toplamTur)}</span>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: 12.5, fontWeight: 700, color: oppStatus.fg, background: oppStatus.bg, border: `1px solid ${oppStatus.bd}`, padding: '4px 11px', borderRadius: 99, boxSizing: 'border-box' }}>
                        {oppStatus.ic ?? <span aria-hidden style={{ width: 7, height: 7, borderRadius: 99, background: oppStatus.fg }} />}
                        {oppStatus.text}
                      </span>
                    </div>

                    <p style={{ margin: '0 0 24px', fontSize: 20, lineHeight: 1.6, fontWeight: 600, color: TXT }}>{soru.soru}</p>

                    <div style={{ display: 'grid', gridTemplateColumns: dar ? 'minmax(0,1fr)' : 'minmax(0,1fr) minmax(0,1fr)', gap: 12 }}>
                      {soru.secenekler.map((metin, i) => {
                        const isSel = i === selIndex && !playing;
                        let bg: string = ARENA.opt;
                        let border = `1px solid ${ARENA.border2}`;
                        const boxShadow: string | undefined = undefined;
                        let badgeBg: string = ARENA.neutralBadge;
                        let badgeFg: string = MUT;
                        if (isSel) {
                          if (benDogru) { bg = ARENA.correctBg; border = `2px solid ${YESIL}`; badgeBg = YESIL; badgeFg = ARENA.darkInk; }
                          else { bg = ARENA.wrongBg; border = `2px solid ${TERRA}`; badgeBg = TERRA; badgeFg = ARENA.darkInk; }
                        }
                        return (
                          <button
                            key={i}
                            type="button"
                            disabled={!playing}
                            onClick={() => void kilitle(HARF[i])}
                            style={{
                              display: 'flex', alignItems: 'center', gap: 13, padding: '15px 16px', minHeight: 44,
                              borderRadius: 13, textAlign: 'left', fontFamily: font.sans, color: TXT,
                              cursor: playing ? 'pointer' : 'default', background: bg, border, boxShadow,
                              transition: reduced ? undefined : 'background .15s, border-color .15s', boxSizing: 'border-box',
                            }}
                          >
                            <span style={{ width: 30, height: 30, flexShrink: 0, borderRadius: 9, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 13.5, background: badgeBg, color: badgeFg }}>
                              {HARF[i]}
                            </span>
                            <span style={{ ...numText, flex: 1, fontSize: 17, fontWeight: 700 }}>{metin}</span>
                            {isSel && (
                              <span style={{ ...numText, fontSize: 11, fontWeight: 800, color: benDogru ? YESIL2 : TERRA }}>{sn(benSureMs)} sn</span>
                            )}
                          </button>
                        );
                      })}
                    </div>

                    {/* Senkron kopya + kilit satırı */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', rowGap: 8, marginTop: 22, paddingTop: 18, borderTop: `1px solid ${ARENA.border}` }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: 12, fontWeight: 600, color: MUT }}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={MUT} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                          <circle cx="12" cy="12" r="9" />
                          <polyline points="12 7 12 12 15 14" />
                        </svg>
                        {oppFirst} kendi hızında çözer — puanlar tur sonunda karşılaştırılır.
                      </span>
                      <div style={{ flex: 1 }} />
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: 13, fontWeight: 800, color: playing ? MUT : YESIL }}>
                        {!playing && <IcCheck boy={15} renk={YESIL} />}
                        {playing ? `${timeLeft} sn · cevabını seç` : 'Cevabın kilitlendi'}
                      </span>
                    </div>
                  </div>

                  {/* Reveal tur-sonuç bandı — rakip açıldıktan sonra (ev), sonuç SUNUCUDAN (turSonuc) */}
                  {revealing && ev && res && (
                    <div style={{ maxWidth: 760, margin: '14px auto 0', display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap', background: res.bg, border: `1px solid ${res.bd}`, borderRadius: 14, padding: '14px 20px', boxSizing: 'border-box' }}>
                      <span aria-hidden style={{ display: 'inline-flex' }}>
                        {turSonuc === 'me' ? (
                          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={YESIL2} strokeWidth={2} aria-hidden><circle cx="12" cy="12" r="8" /><circle cx="12" cy="12" r="3.5" /></svg>
                        ) : turSonuc === 'opp' ? (
                          <svg width="22" height="22" viewBox="0 0 24 24" fill={TERRA} aria-hidden><path d="M13 2 4 14h6l-1 8 9-12h-6l1-8Z" /></svg>
                        ) : (
                          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={NOTR} strokeWidth={2} strokeLinecap="round" aria-hidden><path d="M6 10h12M6 14h12" /></svg>
                        )}
                      </span>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: 14, fontWeight: 800, color: res.fg }}>{res.title}</div>
                        <div style={{ fontSize: 12, color: MUT, fontWeight: 600 }}>{res.sub}</div>
                      </div>
                      <button
                        type="button"
                        onClick={ilerle}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: 8, minHeight: 44, padding: '0 22px', border: 'none', borderRadius: 12, background: accent, color: ARENA.darkInk, fontFamily: font.sans, fontSize: 14, fontWeight: 800, cursor: 'pointer', boxSizing: 'border-box' }}
                      >
                        {sonTur ? 'Sonucu gör' : 'Sonraki tur'}
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                          <polyline points="9 18 15 12 9 6" />
                        </svg>
                      </button>
                    </div>
                  )}

                  {bekliyor && (
                    <div style={{ maxWidth: 760, margin: '14px auto 0', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: 13, fontWeight: 700, color: MUT, background: 'rgba(255,255,255,0.05)', border: `1px solid ${ARENA.border}`, padding: '7px 14px', borderRadius: 99, boxSizing: 'border-box' }}>
                        {oppFirst} cevaplıyor…
                      </span>
                    </div>
                  )}

                  {playing && (
                    <div style={{ maxWidth: 760, margin: '14px auto 0', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: 13, fontWeight: 700, color: GOLD, background: 'rgba(252,211,77,0.1)', border: '1px solid rgba(252,211,77,0.22)', padding: '7px 14px', borderRadius: 99, boxSizing: 'border-box' }}>
                        <IcSpark boy={15} renk={GOLD} />
                        Hızlı + doğru cevap = daha çok puan
                      </span>
                    </div>
                  )}
                </main>

                {/* ---- Bitiş overlay'i ---- */}
                {bitti && sonuc && (
                  <div
                    role="dialog"
                    aria-modal="true"
                    aria-label={won ? 'Zafer' : tie ? 'Berabere' : 'Maç bitti'}
                    onKeyDown={(e) => {
                      if (e.key === 'Escape') {
                        e.preventDefault();
                        window.location.href = '/lig';
                        return;
                      }
                      if (e.key !== 'Tab') return;
                      const f = Array.from(e.currentTarget.querySelectorAll<HTMLElement>('a[href], button:not([disabled])'));
                      if (f.length === 0) return;
                      const first = f[0]!;
                      const last = f[f.length - 1]!;
                      const inside = f.includes(document.activeElement as HTMLElement);
                      if (e.shiftKey && (!inside || document.activeElement === first)) { e.preventDefault(); last.focus(); }
                      else if (!e.shiftKey && (!inside || document.activeElement === last)) { e.preventDefault(); first.focus(); }
                    }}
                    style={{ position: 'fixed', inset: 0, zIndex: 60, background: 'rgba(5,8,17,0.78)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24, boxSizing: 'border-box' }}
                  >
                    {won && <ConfettiDawn count={26} zIndex={61} />}
                    <div
                      style={{
                        position: 'relative', zIndex: 62, width: '100%', maxWidth: 440, background: ARENA.card,
                        border: `1px solid ${won ? 'rgba(252,211,77,0.4)' : tie ? ARENA.border2 : 'rgba(232,131,107,0.4)'}`,
                        borderRadius: 22, padding: '34px 30px', textAlign: 'center', boxShadow: '0 30px 70px -20px rgba(0,0,0,0.7)',
                        boxSizing: 'border-box', margin: 'env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left)',
                      }}
                    >
                      <div
                        aria-hidden
                        style={{
                          width: 72, height: 72, margin: '0 auto 16px', borderRadius: 22,
                          background: won ? 'linear-gradient(135deg,#CA8A04,#FCD34D)' : tie ? 'linear-gradient(135deg,#4A4456,#4A4456)' : 'linear-gradient(135deg,#9A3520,#C2452B)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          animation: anim('kpop .55s cubic-bezier(.22,1.4,.5,1) both'),
                        }}
                      >
                        {won ? (
                          <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={1.9} strokeLinecap="round" strokeLinejoin="round">
                            <path d="M8 4h8v4a4 4 0 0 1-8 0Z" />
                            <path d="M8 5H5v1a3 3 0 0 0 3 3M16 5h3v1a3 3 0 0 1-3 3" />
                            <path d="M12 12v3" />
                            <path d="M9.5 20h5l-.7-3h-3.6Z" />
                          </svg>
                        ) : tie ? (
                          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={2} strokeLinecap="round"><path d="M6 9h12M6 14h12" /></svg>
                        ) : (
                          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={1.9} strokeLinecap="round" strokeLinejoin="round"><path d="M4 12a8 8 0 1 0 2.3-5.6" /><path d="M4 4v4h4" /></svg>
                        )}
                      </div>
                      <h2 ref={bitisRef} tabIndex={-1} style={{ margin: '0 0 6px', fontSize: 26, fontWeight: 800, outline: 'none' }}>
                        {won ? 'Kazandın!' : tie ? 'Berabere!' : 'Bu sefer olmadı'}
                      </h2>
                      <p style={{ margin: '0 0 20px', fontSize: 14, color: MUT, lineHeight: 1.55 }}>
                        {won ? `${oppFirst}’i devirdin — lig sıran yükseldi.` : tie ? 'Çok yakındı — rövanş?' : `${oppFirst} bu turu aldı. Rövanşta sen kazanırsın.`}
                      </p>

                      <div style={{ display: 'flex', justifyContent: 'center', gap: 26, marginBottom: 22 }}>
                        <div>
                          <div style={{ ...numText, fontSize: 30, fontWeight: 800, color: accent }}>{sonuc.benSkor}</div>
                          <div style={{ fontSize: 11.5, color: MUT, fontWeight: 700 }}>Sen</div>
                        </div>
                        <div style={{ alignSelf: 'center', fontSize: 18, color: '#4A4456' }} aria-hidden>—</div>
                        <div>
                          <div style={{ ...numText, fontSize: 30, fontWeight: 800, color: TERRA }}>{sonuc.rakipSkor}</div>
                          <div style={{ fontSize: 11.5, color: MUT, fontWeight: 700 }}>{oppFirst}</div>
                        </div>
                      </div>

                      {(won || tie) && (
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 7, padding: '8px 14px', borderRadius: 99, background: 'rgba(252,211,77,0.12)', border: '1px solid rgba(252,211,77,0.28)', marginBottom: 22, boxSizing: 'border-box' }}>
                          <IcSpark boy={15} renk={GOLD} />
                          <span style={{ ...numText, fontSize: 13, fontWeight: 800, color: GOLD }}>
                            {won ? `+${sonuc.eloDelta} lig puanı` : 'Lig puanın korundu'}
                          </span>
                        </div>
                      )}

                      <div style={{ display: 'flex', gap: 11 }}>
                        <button
                          type="button"
                          onClick={yenidenOyna}
                          style={{ flex: 1, minHeight: 48, border: 'none', borderRadius: 13, background: accent, color: ARENA.darkInk, fontFamily: font.sans, fontSize: 14.5, fontWeight: 800, cursor: 'pointer', boxSizing: 'border-box' }}
                        >
                          Tekrar oyna
                        </button>
                        <a
                          href="/lig"
                          style={{ flex: 1, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', minHeight: 48, border: `1px solid ${ARENA.border2}`, borderRadius: 13, background: 'rgba(255,255,255,0.04)', color: TXT, fontFamily: font.sans, fontSize: 14, fontWeight: 700, textDecoration: 'none', boxSizing: 'border-box' }}
                        >
                          Lige dön
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

export default DuelloPage;
