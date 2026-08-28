// ============================================================================
// KIRO2 — Lig (SPRINT8 · Grup 6 · KIRO2 Lig.dc.html)
// Tema = PAPER (oyunlaştırma yüzeyi; route-bazlı, toggle YOK).
// Kaygı-duyarlı hiyerarşi: "Sen vs dün" seridi sıralamadan ÖNCE gelir (bilinçli).
// SUNUCU-OTORİTE: tier/rank/xp/standings/senVsDun/zonEsik getLeague'ten; seviye/
// kalanXp getMe+getLevel'ten. Ekran puan/sıra/seri/skor HESAPLAMAZ — yalnız gösterir.
// Not: DC "Altın Ligi" sabitini SERVER tier'i (league.tier) ile değiştirdim (otorite).
//   5-kademe TierStepper aria-hidden dekoratif ladder; aktif kademe tier-adı eşleşmesiyle.
//   DC'nin "XP kazan" düğmesi + client XP mutasyonu (gainXP) PROTOTİP → TAŞINMADI.
//   leveledUp sunucudan gelen bir sinyal değil (getLevel'de yok) → prop (varsayılan false).
// Kopya DC'den; inferred dizeler (ilk-hafta empty · zon status · seviye-atlama gövdesi)
//   ONAY BEKLER (rapor). Motion: paper — spring/konfeti YOK; stagger reduced-motion guard'lı.
// ============================================================================
import * as React from 'react';

import { getLeague, getLevel, getMe } from '../api/api-client';
import type { LeagueData, LeagueStanding } from '../api/api-client';
import { useAyar } from '../lib/ayarStore';
import { color, font } from '../tokens';
import type { Persona, SeviyeBilgi } from '../types';
import { KiroThemeProvider, numText, serifText, SideNav, ErrorState, EmptyState, Skeleton, useReducedMotion } from '../ui';
import '../tokens/tokens.css';

// --- Renk kanonu (paper) ------------------------------------------------------
const ACCENT = color.dawn.coral;               // #FF6F5C — dekoratif aksan (nokta/kenar/ikon)
const CORAL_TEXT = color.dawn.coralTextOnLight; // #C2452B — açık-zemin coral METİN + SEN/seviye rozeti zemini (beyaz metin AA)
const GREEN_TEXT = color.semantic.successTextOnLight; // #047857 — açık-zemin yeşil METİN (AA)
const AMBER_TEXT = color.semantic.riskTextOnLight;    // #9A5D0D — açık-zemin amber METİN (AA)
const DARK_CARD = '#2A2433';                    // sağ ray izole koyu kart
const DARK_SEC = '#C4BBAE';                     // koyu kart üzerinde AA-güvenli ikincil metin
const DARK_RISK = '#FFB347';                    // koyu kart üzerinde AA-güvenli amber risk metni (~8:1; semantic.risk koyu-zeminde AA-altı)

// 5-kademe ladder (dekoratif, aria-hidden). Renkler mor/indigo İÇERMEZ (kanon).
const TIER_LADDER: { ad: string; fill: string; text: string }[] = [
  { ad: 'Bronz', fill: '#C08248', text: '#8A5A2B' },
  { ad: 'Gümüş', fill: '#AEB4BD', text: '#6B6478' },
  { ad: 'Altın', fill: '#F59E0B', text: '#B45309' },
  { ad: 'Platin', fill: '#7DD3C4', text: '#0F766E' },
  { ad: 'Elmas', fill: '#56C2F0', text: '#0369A1' },
];

// Sıralama avatar paleti — mor(#8B5CF6)/indigo/lacivert YASAK (kanon: mor yalnız Fizik).
const AVA = ['#3B82F6', '#1FB683', '#EC4899', '#06B6D4', '#F59E0B', '#E0593F', '#0EA5E9', '#14B8A6', '#D97706', '#EA580C', '#0D9488'];

const trNum = (n: number): string => n.toLocaleString('tr-TR');
const normTr = (s: string): string => s.toLocaleLowerCase('tr-TR');

const srOnly: React.CSSProperties = {
  position: 'absolute', width: 1, height: 1, padding: 0, margin: -1,
  overflow: 'hidden', clip: 'rect(0 0 0 0)', whiteSpace: 'nowrap', border: 0,
};

const KEYFRAMES = '@keyframes ligIn { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:none; } }';

// ---------------------------------------------------------------------------
// Bespoke SVG ikonlar (emoji YOK; metin glyph YOK — hepsi inline SVG)
// ---------------------------------------------------------------------------
function ShieldGold() {
  return (
    <svg width="68" height="68" viewBox="0 0 64 64" aria-hidden>
      <defs>
        <linearGradient id="ligGold" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#FCD34D" /><stop offset="1" stopColor="#D97706" />
        </linearGradient>
      </defs>
      <path d="M32 3 56 14v19c0 15-11 24-24 28C19 57 8 48 8 33V14Z" fill="url(#ligGold)" stroke="#B45309" strokeWidth="1.5" />
      <path d="M32 17l4.2 8.6 9.5 1.4-6.9 6.7 1.6 9.4L32 39l-8 4.2 1.6-9.4-6.9-6.7 9.5-1.4Z" fill="#fff" fillOpacity="0.92" />
    </svg>
  );
}
function Clock({ c }: { c: string }) {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <circle cx="12" cy="12" r="9" /><polyline points="12 7 12 12 15 14" />
    </svg>
  );
}
function EyeIcon({ off }: { off: boolean }) {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M2 12s3.5-6.5 10-6.5S22 12 22 12s-3.5 6.5-10 6.5S2 12 2 12Z" /><circle cx="12" cy="12" r="2.6" />
      {off && <line x1="3" y1="3" x2="21" y2="21" />}
    </svg>
  );
}
function Flame({ c }: { c: string }) {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M12 2c1.2 3 4 4.2 4 7.8A4 4 0 0 1 8 10c0-1.4.5-2.4 1-3 .2 1 .9 1.6 1.6 1.6C9.6 6.4 10.8 4.2 12 2Z" />
    </svg>
  );
}
function ArrowUp({ c }: { c: string }) {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <line x1="12" y1="19" x2="12" y2="5" /><polyline points="5 12 12 5 19 12" />
    </svg>
  );
}
function ArrowDown({ c }: { c: string }) {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <line x1="12" y1="5" x2="12" y2="19" /><polyline points="5 12 12 19 19 12" />
    </svg>
  );
}
function Dash({ c }: { c: string }) {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="2.4" strokeLinecap="round" aria-hidden>
      <line x1="6" y1="12" x2="18" y2="12" />
    </svg>
  );
}
function Check({ c }: { c: string }) {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}
function Bolt({ c, fill }: { c?: string; fill?: string }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill={fill ?? 'none'} stroke={c ?? 'none'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z" />
    </svg>
  );
}
function Medal({ c }: { c: string }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <circle cx="12" cy="8" r="6" /><path d="M8.2 13.9 7 22l5-3 5 3-1.2-8.1" />
    </svg>
  );
}
function StarFill({ c }: { c: string }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill={c} aria-hidden>
      <path d="M5 16 3 5l5.5 4L12 4l3.5 5L21 5l-2 11Z" />
    </svg>
  );
}
function Sparkle() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M5 3v4M3 5h4M6 17v4M4 19h4M13 3l2.5 6.5L22 12l-6.5 2.5L13 21l-2.5-6.5L4 12l6.5-2.5Z" />
    </svg>
  );
}
function TierTrophy() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="#2A2433" aria-hidden>
      <path d="M12 2l2.9 6.26 6.9.7-5.13 4.64L18 21l-6-3.5L6 21l1.33-7.4L2.2 8.96l6.9-.7L12 2Z" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Trend işareti — bespoke SVG (aria-hidden) + görünmez SR metni
// ---------------------------------------------------------------------------
function Trend({ dir }: { dir: LeagueStanding['trend'] }) {
  const meta =
    dir === 'up' ? { c: GREEN_TEXT, sr: 'yükseldi', node: <ArrowUp c={GREEN_TEXT} /> }
      : dir === 'down' ? { c: CORAL_TEXT, sr: 'düştü', node: <ArrowDown c={CORAL_TEXT} /> }
        : { c: color.ink.muted, sr: 'sabit', node: <Dash c={color.ink.muted} /> };
  return (
    <span style={{ width: 18, display: 'inline-flex', justifyContent: 'center', flexShrink: 0 }}>
      {meta.node}
      <span style={srOnly}>{meta.sr}</span>
    </span>
  );
}

// ---------------------------------------------------------------------------
// Sunucu-verilerinden salt-render bar (scaleX; WIDTH DEĞİL — layout-anim yok)
// ---------------------------------------------------------------------------
function ScaleBar({ ratio, track, fill, height, ariaLabel }: { ratio: number; track: string; fill: string; height: number; ariaLabel: string }) {
  const r = Math.max(0, Math.min(1, ratio));
  return (
    <div role="progressbar" aria-label={ariaLabel} aria-valuenow={Math.round(r * 100)} aria-valuemin={0} aria-valuemax={100} style={{ height, borderRadius: 99, background: track, overflow: 'hidden' }}>
      <div aria-hidden style={{ width: '100%', height: '100%', borderRadius: 99, background: fill, transform: `scaleX(${r})`, transformOrigin: 'left' }} />
    </div>
  );
}

// ---------------------------------------------------------------------------
// matchMedia — SSR/jsdom guard'lı
// ---------------------------------------------------------------------------
function useMedia(query: string): boolean {
  const [esles, setEsles] = React.useState(false);
  React.useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {return;}
    const mq = window.matchMedia(query);
    const on = () => setEsles(mq.matches);
    on();
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, [query]);
  return esles;
}

interface Veri {
  league: LeagueData;
  persona: Persona;
  level: SeviyeBilgi;
}

export interface LigPageProps {
  /** Kaygı-duyarlı sakin çerçeve (varsayılan AÇIK) — kapalıyken yarışmacı dil + amber geri-sayım */
  sakinMod?: boolean;
  /**
   * Storybook/test override — verilirse store yerine bu değeri gösterir.
   * OMITTED (varsayılan) → durum useAyar.hideRanking'ten okunur (Ayarlar ile tek kaynak).
   */
  siralamaGizli?: boolean;
  /** Sunucu bu turda seviye atlattıysa (getLevel'de sinyal YOK → dışarıdan gelir; varsayılan false) */
  leveledUp?: boolean;
}

export function LigPage({ sakinMod = true, siralamaGizli, leveledUp = false }: LigPageProps): React.ReactElement {
  const reduced = useReducedMotion();
  const darNav = useMedia('(max-width: 1023px)');
  const darGrid = useMedia('(max-width: 760px)');
  // Sıralama-gizleme TEK KAYNAK: useAyar.hideRanking (Ayarlar "Sıralamayı gizle" ile çift-yönlü).
  // siralamaGizli prop yalnız Storybook/test override'ı — verilmezse store okunur.
  const storeHidden = useAyar((s) => s.hideRanking);
  const rankHidden = siralamaGizli ?? storeHidden;
  const [duyuru, setDuyuru] = React.useState('');
  const [veri, setVeri] = React.useState<Veri | null>(null);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);

  React.useEffect(() => {
    let alive = true;
    setVeri(null);
    setHata(false);
    Promise.all([getLeague(), getMe(), getLevel()])
      .then(([league, persona, level]) => {
        if (alive) {setVeri({ league, persona, level });}
      })
      .catch(() => {
        if (alive) {setHata(true);}
      });
    return () => {
      alive = false;
    };
  }, [yeniden]);

  const toggle = React.useCallback(() => {
    // Override modu (siralamaGizli prop verilmiş — Storybook/test): NO-OP.
    // Görünen durum prop'a kilitli; store'a yazmak görünür etki yapmaz + global store'u kirletir.
    if (siralamaGizli != null) {return;}
    const next = !useAyar.getState().hideRanking;
    useAyar.getState().setHideRanking(next);
    setDuyuru(next ? 'Sıralama gizlendi' : 'Sıralama gösteriliyor');
  }, [siralamaGizli]);

  // Süre 450ms (<600ms; paper — kanon-allow gerekmez). Stagger reduced-motion guard'lı.
  const anim = (delay: number): React.CSSProperties =>
    reduced ? {} : { animation: 'ligIn 450ms ease both', animationDelay: `${delay}ms` };

  return (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={{ minHeight: '100vh', background: color.paper.bg, display: 'flex', fontFamily: font.sans, color: color.ink.primary, fontSize: 14, lineHeight: 1.5, boxSizing: 'border-box' }}>
        <SideNav role="ogrenci" activeId="league" collapsed={darNav} userName={veri?.persona.ad ?? 'Öğrenci'} userSub={veri?.persona.sinif ?? ''} onAssistant={() => undefined} />

        <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
          <header
            style={{
              height: 66, flexShrink: 0, display: 'flex', alignItems: 'center', gap: 12, padding: '0 30px',
              background: 'rgba(250,247,242,0.86)', backdropFilter: 'blur(8px)', borderBottom: `1px solid ${color.paper.border}`,
              position: 'sticky', top: 0, zIndex: 5, boxSizing: 'border-box',
            }}
          >
            <div style={{ fontSize: 18, fontWeight: 800, letterSpacing: '-0.02em' }}>Lig</div>
            <div style={{ flex: 1 }} />
            {veri && (
              <>
                <div style={{ display: 'flex', alignItems: 'center', gap: 7, height: 38, padding: '0 12px', background: color.semantic.riskBgSoft, border: `1px solid ${color.semantic.riskBorderSoft}`, borderRadius: 10, boxSizing: 'border-box' }}>
                  <Flame c={AMBER_TEXT} />
                  <span style={{ ...numText, fontWeight: 800, fontSize: 14, color: AMBER_TEXT }}>{veri.persona.seri !== null ? trNum(veri.persona.seri) : '—'}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 9, height: 38, padding: '0 12px', background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 10, boxSizing: 'border-box' }}>
                  <span aria-hidden style={{ width: 22, height: 22, borderRadius: 7, background: CORAL_TEXT, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 800, fontSize: 11 }}>{veri.level.seviye}</span>
                  <span style={{ ...numText, fontWeight: 700, fontSize: 13 }}>{veri.persona.xp !== null ? trNum(veri.persona.xp) : '—'}</span>
                  <span style={{ fontSize: 11.5, color: color.ink.muted, fontWeight: 600 }}>XP</span>
                </div>
              </>
            )}
          </header>

          <main style={{ padding: darGrid ? '20px 16px 46px' : '24px 30px 46px', maxWidth: 1280, width: '100%', display: 'flex', flexDirection: 'column', gap: 20, boxSizing: 'border-box' }}>
            <style>{KEYFRAMES}</style>

            {hata ? (
              <ErrorState
                serifTitle="Lig şu an gelmedi."
                body="Sorun sende değil — XP'n, serin ve terfi hakkın güvende. Bağlantı bir soluklandı; birazdan yeniden dene."
                onRetry={() => setYeniden((n) => n + 1)}
              />
            ) : !veri ? (
              <div aria-busy="true" aria-label="Lig yükleniyor" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                <div style={{ padding: '20px 24px', background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 20, boxSizing: 'border-box' }}>
                  <Skeleton shape="card" delayMs={0} />
                </div>
                <div style={{ padding: '22px 26px', background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 20, boxSizing: 'border-box' }}>
                  <Skeleton shape="card" delayMs={0} />
                </div>
              </div>
            ) : (
              <Icerik
                veri={veri}
                sakinMod={sakinMod}
                rankHidden={rankHidden}
                onToggle={toggle}
                leveledUp={leveledUp}
                darGrid={darGrid}
                anim={anim}
              />
            )}
          </main>
        </div>

        {/* Tek aria-live duyuru bölgesi (toggle sonucu) */}
        <div aria-live="polite" style={srOnly}>{duyuru}</div>
      </div>
    </KiroThemeProvider>
  );
}

// ---------------------------------------------------------------------------
// İçerik (veri hazır)
// ---------------------------------------------------------------------------
function Icerik({
  veri, sakinMod, rankHidden, onToggle, leveledUp, darGrid, anim,
}: {
  veri: Veri;
  sakinMod: boolean;
  rankHidden: boolean;
  onToggle: () => void;
  leveledUp: boolean;
  darGrid: boolean;
  anim: (d: number) => React.CSSProperties;
}): React.ReactElement {
  const { league, level } = veri;
  const { tier, rank, haftalikXp, tierToplam, haftaBitisText, zonEsik, senVsDun, standings } = league;

  // Sen vs dün — sunucu iki sayı verir; delta/oran salt-render türetimi (skor değil).
  const buHafta = senVsDun.buHafta;
  const gecenHafta = senVsDun.gecenHafta;
  const svdDelta = Math.max(0, buHafta - gecenHafta);
  const svdPct = gecenHafta > 0 ? Math.round((svdDelta / gecenHafta) * 100) : 0;
  const svdMax = Math.max(buHafta, gecenHafta, 1);
  const hDun = Math.round((gecenHafta / svdMax) * 52) + 8;
  const hBugun = Math.round((buHafta / svdMax) * 52) + 8;

  // Zon sınıflaması — SUNUCU zonEsik (istemci eşik hesaplamaz).
  const yuk = zonEsik.yukselme;
  const dus = zonEsik.dusme;
  const zoneOf = (r: number): 'promote' | 'safe' | 'demote' => (r <= yuk ? 'promote' : r > dus ? 'demote' : 'safe');

  // TierStepper aktif kademe — server tier adı eşleşmesi (yoksa nötr; DC "Altın" sabiti değil).
  const activeTierIdx = TIER_LADDER.findIndex((t) => normTr(tier).includes(normTr(t.ad)));

  const subtitle = sakinMod
    ? `${tier} — kendi ritminde ilerle, sıralama ikincil.`
    : `${trNum(tierToplam)} kişiden #${rank} sıradasın · ilk ${yuk} üst lige yükselir.`;

  const me = standings.find((s) => s.benMi) ?? null;
  const meIdx = me ? standings.indexOf(me) : -1;
  const above = meIdx > 0 ? standings[meIdx - 1] : null;

  return (
    <>
      {/* (1) SEN vs DÜN — kişisel ilerleme (sıralamadan ÖNCE, bilinçli hiyerarşi) */}
      <section
        style={{
          background: 'linear-gradient(120deg,#FFFDFB,#FFF3EE)', border: '1px solid #F6D9CB', borderRadius: 20,
          padding: '20px 24px', display: 'flex', alignItems: 'center', gap: 26, flexWrap: 'wrap', boxSizing: 'border-box',
          ...anim(0),
        }}
      >
        <div style={{ minWidth: 220, flex: 1 }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 7, height: 22, padding: '0 10px', borderRadius: 99, background: '#fff', border: '1px solid #F6D9CB', marginBottom: 11 }}>
            <span aria-hidden style={{ width: 6, height: 6, borderRadius: 99, background: ACCENT }} />
            <span style={{ fontSize: 10.5, fontWeight: 800, letterSpacing: '0.05em', color: CORAL_TEXT, textTransform: 'uppercase' }}>Sen vs dün</span>
          </div>
          <div style={{ ...serifText, fontSize: 22, lineHeight: 1.2, color: color.ink.primary }}>Yarıştığın tek kişi dünkü sensin.</div>
          <div style={{ fontSize: 12.5, color: color.ink.muted, marginTop: 5, lineHeight: 1.5 }}>
            Sıralama bir oyun — asıl ölçü kendi ilerlemen. {svdDelta > 0 ? 'Bu hafta geçen haftayı geçtin.' : 'Kendi ritminde ilerliyorsun.'}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 20 }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ ...numText, fontSize: 30, fontWeight: 800, color: GREEN_TEXT, lineHeight: 1 }}>+{trNum(svdDelta)}</div>
            <div style={{ fontSize: 11.5, color: color.ink.muted, fontWeight: 600, marginTop: 6 }}>XP · geçen haftaya +%{trNum(svdPct)}</div>
          </div>
          <div aria-hidden style={{ display: 'flex', alignItems: 'flex-end', gap: 10, height: 64 }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
              <div style={{ width: 26, height: hDun, background: '#E7DFD3', borderRadius: '6px 6px 3px 3px' }} />
              <span style={{ fontSize: 10, color: color.ink.muted, fontWeight: 600 }}>dün</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
              <div style={{ width: 26, height: hBugun, background: ACCENT, borderRadius: '6px 6px 3px 3px' }} />
              <span style={{ fontSize: 10, color: color.ink.muted, fontWeight: 700 }}>bugün</span>
            </div>
          </div>
        </div>
      </section>

      {/* (2) Lig bandı — server tier + kalkan + gerisayım + gizle/göster toggle + ladder */}
      <section style={{ background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 20, padding: '22px 26px', boxShadow: '0 1px 2px rgba(16,24,40,.04)', boxSizing: 'border-box', ...anim(60) }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap' }}>
          <div aria-hidden style={{ width: 68, height: 68, flexShrink: 0 }}><ShieldGold /></div>
          <div style={{ minWidth: 0 }}>
            <h1 style={{ margin: 0, fontSize: 24, fontWeight: 800, letterSpacing: '-0.02em' }}>{tier}</h1>
            <div style={{ fontSize: 13, color: color.ink.muted, fontWeight: 500, marginTop: 2 }}>{subtitle}</div>
          </div>
          <div style={{ flex: 1 }} />
          {/* Gerisayım chip — sakin: nötr / yarışmacı: amber (alarm-kırmızı DEĞİL) */}
          <div
            style={{
              display: 'flex', alignItems: 'center', gap: 8, height: 40, padding: '0 16px', borderRadius: 12, boxSizing: 'border-box',
              ...(sakinMod
                ? { background: color.paper.subtle, border: `1px solid ${color.paper.border}` }
                : { background: color.semantic.riskBgSoft, border: `1px solid ${color.semantic.riskBorderSoft}` }),
            }}
          >
            <Clock c={sakinMod ? color.ink.muted : AMBER_TEXT} />
            <span style={{ fontSize: 13, fontWeight: 700, color: sakinMod ? color.ink.muted : AMBER_TEXT }}>
              {sakinMod ? 'Hafta sonu yenilenir' : `Bitişe ${haftaBitisText}`}
            </span>
          </div>
          <button
            type="button"
            onClick={onToggle}
            aria-pressed={rankHidden}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 7, minHeight: 44, padding: '0 14px', border: `1px solid ${color.paper.border}`, borderRadius: 12, background: color.paper.card, color: color.ink.secondary, fontFamily: 'inherit', fontSize: 12.5, fontWeight: 700, cursor: 'pointer', boxSizing: 'border-box' }}
          >
            <EyeIcon off={rankHidden} />
            {rankHidden ? 'Sıralamayı göster' : 'Sıralamayı gizle'}
          </button>
        </div>

        {/* Ladder — dekoratif (aria-hidden); aktif kademe server tier eşleşmesi */}
        <div aria-hidden style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 20 }}>
          {TIER_LADDER.map((t, i) => {
            const reached = activeTierIdx >= 0 && i <= activeTierIdx;
            const isActive = i === activeTierIdx;
            return (
              <React.Fragment key={t.ad}>
                <span style={{ flex: 1, height: 6, borderRadius: 99, background: reached ? t.fill : color.paper.border }} />
                <span style={{ fontSize: isActive ? 12 : 11, fontWeight: isActive ? 800 : 700, color: reached ? t.text : color.ink.faded2 }}>{t.ad}</span>
              </React.Fragment>
            );
          })}
          <span style={{ flex: 1, height: 6, borderRadius: 99, background: color.paper.border }} />
        </div>
      </section>

      {/* (3) Grid: sol sıralama · sağ ray */}
      <div style={{ display: 'grid', gridTemplateColumns: darGrid ? '1fr' : 'minmax(0,1fr) 330px', gap: 20, alignItems: 'start', ...anim(120) }}>
        {/* SOL */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 }}>
          {rankHidden ? (
            <GizliDurumKarti onToggle={onToggle} />
          ) : standings.length === 0 ? (
            <EmptyState
              serifTitle="Ligin Pazartesi başlıyor — bu hafta odak sende."
              body="Bu hafta çalışman XP'ye dönüşecek; lig başlayınca sıralaman burada belirir. Acele yok."
            />
          ) : (
            <>
              <Podyum top3={standings.slice(0, 3)} />
              <SiralamaListesi standings={standings.filter((s) => s.rank > 3)} zoneOf={zoneOf} yuk={yuk} son={Math.max(0, tierToplam - dus)} sakinMod={sakinMod} />
            </>
          )}
        </div>

        {/* SAĞ RAY */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18, position: darGrid ? 'static' : 'sticky', top: 90, minWidth: 0 }}>
          {rankHidden ? (
            <GizliEmekKarti haftalikXp={haftalikXp} svdDelta={svdDelta} />
          ) : (
            <SiranKarti rank={rank} haftalikXp={haftalikXp} yuk={yuk} me={me} above={above} sakinMod={sakinMod} />
          )}

          <TerfiOdulleri oduller={league.oduller} />

          {leveledUp ? <SeviyeAtladiKarti seviye={level.seviye} /> : <SonrakiSeviyeKarti level={level} />}
        </div>
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// SOL — gizli durum kartı
// ---------------------------------------------------------------------------
function GizliDurumKarti({ onToggle }: { onToggle: () => void }): React.ReactElement {
  return (
    <section style={{ background: color.paper.card, border: '1px dashed #E0D8CB', borderRadius: 20, padding: '46px 32px', display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: 11, boxSizing: 'border-box' }}>
      <div aria-hidden style={{ width: 52, height: 52, borderRadius: 16, background: '#FFF3EE', display: 'flex', alignItems: 'center', justifyContent: 'center', color: CORAL_TEXT }}>
        <EyeIcon off />
      </div>
      <div style={{ ...serifText, fontSize: 24, color: color.ink.primary, lineHeight: 1.25 }}>Sıralama gizli — odak sende.</div>
      <p style={{ margin: 0, maxWidth: 430, fontSize: 13.5, color: color.ink.muted, lineHeight: 1.6 }}>
        {"XP'n, serin ve terfi hakkın aynen işliyor. Kıyası istediğin an geri açarsın — bu bir ceza değil, bir tercih."}
      </p>
      <button
        type="button"
        onClick={onToggle}
        style={{ marginTop: 6, display: 'inline-flex', alignItems: 'center', gap: 8, minHeight: 44, padding: '0 18px', border: `1px solid ${color.paper.border}`, borderRadius: 12, background: color.paper.card, color: color.ink.secondary, fontFamily: 'inherit', fontSize: 13, fontWeight: 700, cursor: 'pointer', boxSizing: 'border-box' }}
      >
        Sıralamayı göster
      </button>
    </section>
  );
}

// ---------------------------------------------------------------------------
// SOL — podyum (ilk 3, server standings)
// ---------------------------------------------------------------------------
function Podyum({ top3 }: { top3: LeagueStanding[] }): React.ReactElement {
  const first = top3[0];
  const second = top3[1];
  const third = top3[2];
  const cell = (s: LeagueStanding | undefined, spec: { max: number; av: number; avBg: string; avBorder: string; badgeBg: string; xpCol: string; kaide: string; kaideH: number; big?: boolean }) => {
    if (!s) {return <div style={{ flex: 1, maxWidth: spec.max }} />;}
    return (
      <div style={{ flex: 1, maxWidth: spec.max, textAlign: 'center', minWidth: 0 }}>
        {/* DOM sırası 2-1-3; rozet aria-hidden → ekran okuyucu için görünmez sıra metni */}
        <span style={srOnly}>{s.rank}. sıra</span>
        {spec.big && <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 2 }}><StarFill c="#F59E0B" /></div>}
        <div style={{ position: 'relative', width: spec.av, height: spec.av, margin: '0 auto 9px' }}>
          <div style={{ width: spec.av, height: spec.av, borderRadius: spec.big ? 18 : 16, background: spec.avBg, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: spec.big ? 24 : 20, border: `3px solid ${spec.avBorder}`, boxSizing: 'border-box' }}>{s.ini}</div>
          <div aria-hidden style={{ position: 'absolute', bottom: -8, left: '50%', transform: 'translateX(-50%)', width: spec.big ? 24 : 22, height: spec.big ? 24 : 22, borderRadius: 99, background: spec.badgeBg, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: spec.big ? 12 : 11, border: '2px solid #fff' }}>{s.rank}</div>
        </div>
        <div style={{ fontSize: spec.big ? 14 : 13, fontWeight: spec.big ? 800 : 700, marginTop: 6, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.ad}</div>
        <div style={{ ...numText, fontSize: spec.big ? 12.5 : 12, fontWeight: 800, color: spec.xpCol }}>{trNum(s.xp)} XP</div>
        <div aria-hidden style={{ height: spec.kaideH, marginTop: 10, borderRadius: '12px 12px 0 0', background: spec.kaide }} />
      </div>
    );
  };
  return (
    <section aria-label="İlk üç" style={{ background: 'linear-gradient(180deg,#FFFCF5 0%,#fff 60%)', border: '1px solid #F3E6C8', borderRadius: 20, padding: '24px 20px 22px', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'center', gap: 14 }}>
        {cell(second, { max: 150, av: 58, avBg: '#6B6478', avBorder: '#C4BBAE', badgeBg: '#C4BBAE', xpCol: color.ink.muted, kaide: 'linear-gradient(180deg,#EAE3D9,#C4BBAE)', kaideH: 54 })}
        {cell(first, { max: 160, av: 70, avBg: '#2A2433', avBorder: '#F59E0B', badgeBg: '#F59E0B', xpCol: '#B45309', kaide: 'linear-gradient(180deg,#FCD34D,#F59E0B)', kaideH: 78, big: true })}
        {cell(third, { max: 150, av: 58, avBg: '#92400E', avBorder: '#D97706', badgeBg: '#D97706', xpCol: '#92400E', kaide: 'linear-gradient(180deg,#FBD9A8,#D97706)', kaideH: 40 })}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// SOL — sıralama listesi (3 zon; <ol>/<li>; SEN aria-current)
// ---------------------------------------------------------------------------
function SiralamaSatiri({ s }: { s: LeagueStanding }): React.ReactElement {
  const benMi = s.benMi;
  return (
    <li
      aria-current={benMi ? 'true' : undefined}
      style={{
        listStyle: 'none', display: 'flex', alignItems: 'center', gap: 13, padding: '11px 10px', borderRadius: 12, boxSizing: 'border-box', minWidth: 0,
        background: benMi ? '#FFF3EE' : color.paper.card,
        border: benMi ? `1.5px solid ${ACCENT}` : '1.5px solid transparent',
      }}
    >
      <span style={{ ...numText, width: 24, textAlign: 'center', fontSize: 15, fontWeight: 800, color: color.ink.muted, flexShrink: 0 }}>{s.rank}</span>
      <div aria-hidden style={{ width: 38, height: 38, flexShrink: 0, borderRadius: 11, background: AVA[s.rank % AVA.length], color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 800 }}>{s.ini}</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 14, fontWeight: 700, color: color.ink.primary, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.ad}</span>
          {benMi && <span style={{ fontSize: 10, fontWeight: 800, color: '#fff', background: CORAL_TEXT, padding: '1px 7px', borderRadius: 99, flexShrink: 0 }}>SEN</span>}
        </div>
        <div style={{ fontSize: 11.5, color: color.ink.muted, fontWeight: 600 }}>Seviye {s.seviye}</div>
      </div>
      <Trend dir={s.trend} />
      <span style={{ ...numText, fontSize: 14, fontWeight: 800, color: color.ink.primary, width: 66, textAlign: 'right', flexShrink: 0 }}>{trNum(s.xp)}</span>
    </li>
  );
}

function ZonBaslik({ icon, text, color: c, lineColor }: { icon?: React.ReactNode; text: string; color: string; lineColor: string }): React.ReactElement {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 6px 10px' }}>
      {icon}
      <span style={{ fontSize: 11.5, fontWeight: 800, color: c, letterSpacing: '0.04em', textTransform: 'uppercase' }}>{text}</span>
      <div aria-hidden style={{ flex: 1, height: 1, background: lineColor }} />
    </div>
  );
}

function SiralamaListesi({
  standings, zoneOf, yuk, son, sakinMod,
}: {
  standings: LeagueStanding[];
  zoneOf: (r: number) => 'promote' | 'safe' | 'demote';
  yuk: number;
  son: number;
  sakinMod: boolean;
}): React.ReactElement {
  const promote = standings.filter((s) => zoneOf(s.rank) === 'promote');
  const safe = standings.filter((s) => zoneOf(s.rank) === 'safe');
  const demote = standings.filter((s) => zoneOf(s.rank) === 'demote');
  const demoteFg = sakinMod ? AMBER_TEXT : CORAL_TEXT;
  const demoteLine = sakinMod ? color.semantic.riskBorderSoft : '#F0A593';
  const demoteLabel = sakinMod ? `Alt bölge · son ${trNum(son)}` : `Düşme bölgesi · son ${trNum(son)}`;

  return (
    <section style={{ background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 18, padding: '18px 18px 8px', boxSizing: 'border-box' }}>
      {promote.length > 0 && (
        <>
          <ZonBaslik icon={<ArrowUp c={GREEN_TEXT} />} text={`Yükselme bölgesi · ilk ${trNum(yuk)}`} color={GREEN_TEXT} lineColor="#D1FAE5" />
          <ol style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 2 }}>
            {promote.map((s) => <SiralamaSatiri key={s.studentId} s={s} />)}
          </ol>
        </>
      )}
      {safe.length > 0 && (
        <>
          <ZonBaslik text="Güvenli bölge" color={color.ink.muted} lineColor={color.paper.borderFaint} />
          <ol style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 2 }}>
            {safe.map((s) => <SiralamaSatiri key={s.studentId} s={s} />)}
          </ol>
        </>
      )}
      {demote.length > 0 && (
        <>
          <ZonBaslik icon={<ArrowDown c={demoteFg} />} text={demoteLabel} color={demoteFg} lineColor={demoteLine} />
          <ol style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 2 }}>
            {demote.map((s) => <SiralamaSatiri key={s.studentId} s={s} />)}
          </ol>
        </>
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------
// SAĞ RAY — koyu izole kart (#2A2433)
// ---------------------------------------------------------------------------
function SiranKarti({
  rank, haftalikXp, yuk, me, above, sakinMod,
}: {
  rank: number;
  haftalikXp: number;
  yuk: number;
  me: LeagueStanding | null;
  above: LeagueStanding | null;
  sakinMod: boolean;
}): React.ReactElement {
  const guvende = me ? me.rank <= yuk : false;
  const zoneRatio = me && above && above.xp > 0 ? me.xp / above.xp : 1;
  const toNext = above && me
    ? (sakinMod ? `Bir üst sıra ${trNum(above.xp - me.xp + 1)} XP uzakta — acele yok.` : `${trNum(above.xp - me.xp + 1)} XP ile ${trNum(me.rank - 1)}. sıraya yüksel.`)
    : 'Zirvedesin!';

  return (
    <div style={{ background: DARK_CARD, borderRadius: 18, padding: 22, color: '#fff', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <div aria-hidden style={{ width: 44, height: 44, borderRadius: 12, background: 'linear-gradient(135deg,#FCD34D,#D97706)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 800, fontSize: 17, boxShadow: '0 6px 16px -6px rgba(245,158,11,.7)' }}>
          <span style={numText}>#{rank}</span>
        </div>
        <div>
          <div style={{ fontSize: 15, fontWeight: 800 }}>Bu haftaki sıran</div>
          <div style={{ fontSize: 12.5, color: DARK_SEC }}><span style={numText}>{trNum(haftalikXp)}</span> XP kazandın</div>
        </div>
      </div>
      <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: 12, padding: '13px 15px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, gap: 8 }}>
          <span style={{ fontSize: 12.5, color: DARK_SEC, fontWeight: 600 }}>İlk {trNum(yuk)}{"'desin — üst lige doğru"}</span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 12, fontWeight: 800, color: guvende ? color.semantic.success : DARK_RISK }}>
            {guvende && <Check c={color.semantic.success} />}
            {guvende ? 'Güvende' : (sakinMod ? 'Kendi hızında' : 'Risk altında')}
            <span style={srOnly}>{guvende ? '' : 'dikkat'}</span>
          </span>
        </div>
        <ScaleBar ratio={zoneRatio} track="rgba(255,255,255,0.12)" fill="linear-gradient(90deg,#1FB683,#34D399)" height={7} ariaLabel="Bir üst sıraya ilerleme" />
        <div style={{ fontSize: 11.5, color: DARK_SEC, marginTop: 8 }}>{toNext}</div>
      </div>
    </div>
  );
}

function GizliEmekKarti({ haftalikXp, svdDelta }: { haftalikXp: number; svdDelta: number }): React.ReactElement {
  return (
    <div style={{ background: DARK_CARD, borderRadius: 18, padding: 22, color: '#fff', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
        <div aria-hidden style={{ width: 44, height: 44, borderRadius: 12, background: 'linear-gradient(135deg,#FF8A5B,#FF6F5C)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Bolt fill="#fff" />
        </div>
        <div>
          <div style={{ fontSize: 15, fontWeight: 800 }}>Bu haftaki emeğin</div>
          <div style={{ fontSize: 12.5, color: DARK_SEC }}><span style={numText}>{trNum(haftalikXp)}</span> XP topladın</div>
        </div>
      </div>
      <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: 12, padding: '13px 15px', fontSize: 12.5, color: DARK_SEC, lineHeight: 1.55 }}>
        Sıralama gizli — yarıştığın tek kişi dünkü sen. Bu hafta geçen haftadan <strong style={{ color: '#fff' }}>+{trNum(svdDelta)} XP</strong> öndesin.
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// SAĞ RAY — terfi ödülleri (server oduller)
// ---------------------------------------------------------------------------
function TerfiOdulleri({ oduller }: { oduller: string[] }): React.ReactElement {
  const ikon = (i: number) => (i === 0 ? <StarFill c={CORAL_TEXT} /> : i === 1 ? <Bolt c={CORAL_TEXT} /> : <Medal c="#D97706" />);
  const bg = (i: number) => (i === 2 ? color.semantic.riskBgSoft : '#FFF3EE');
  if (oduller.length === 0) {return <></>;}
  return (
    <div style={{ background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 18, padding: 20, boxSizing: 'border-box' }}>
      <h2 style={{ margin: '0 0 14px', fontSize: 15, fontWeight: 700 }}>Terfi ödülleri</h2>
      <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 11 }}>
        {oduller.map((o, i) => (
          <li key={o} style={{ display: 'flex', alignItems: 'center', gap: 11 }}>
            <span aria-hidden style={{ width: 34, height: 34, borderRadius: 10, background: bg(i), display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{ikon(i)}</span>
            <span style={{ fontSize: 13, fontWeight: 600, color: color.ink.primary }}>{o}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ---------------------------------------------------------------------------
// SAĞ RAY — seviye atladı (Kutlama CTA) / sonraki seviye ilerlemesi
// ---------------------------------------------------------------------------
function SeviyeAtladiKarti({ seviye }: { seviye: number }): React.ReactElement {
  return (
    <div style={{ background: 'linear-gradient(150deg,#3A2E12,#5A4416)', border: '1px solid #C99A2E', borderRadius: 18, padding: 20, color: '#fff', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 11, marginBottom: 12 }}>
        <div aria-hidden style={{ width: 44, height: 44, flexShrink: 0, borderRadius: 12, background: 'linear-gradient(135deg,#FCD34D,#D97706)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 6px 16px -6px rgba(245,158,11,.7)' }}>
          <TierTrophy />
        </div>
        <div>
          <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: '0.08em', color: '#FCD34D' }}>SEVİYE {trNum(seviye)}</div>
          <div style={{ fontSize: 17, fontWeight: 800 }}>Seviye atladın!</div>
        </div>
      </div>
      <p style={{ margin: '0 0 14px', fontSize: 12.5, color: '#F3E6C8', lineHeight: 1.55 }}>
        Seviye {trNum(seviye)} açıldı — dünkü senden bir adım ileridesin.
      </p>
      <a
        href="/kutlama?type=seviye"
        style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 9, width: '100%', height: 46, borderRadius: 12, background: 'linear-gradient(110deg,#E0A82E,#FCD34D)', color: '#2A1810', fontFamily: 'inherit', fontSize: 14, fontWeight: 800, textDecoration: 'none', boxSizing: 'border-box' }}
      >
        <Sparkle />
        Seviyeyi kutla
      </a>
    </div>
  );
}

function SonrakiSeviyeKarti({ level }: { level: SeviyeBilgi }): React.ReactElement {
  return (
    <div style={{ background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 16, padding: '16px 18px', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 9, gap: 8 }}>
        <span style={{ fontSize: 12, fontWeight: 700, color: color.ink.muted }}>Sonraki seviye</span>
        <span style={{ fontSize: 12.5, fontWeight: 800, color: color.ink.primary }}>Seviye {trNum(level.seviye + 1)}</span>
      </div>
      <ScaleBar ratio={level.ilerleme} track={color.semantic.riskBorderSoft} fill="linear-gradient(90deg,#F59E0B,#FCD34D)" height={8} ariaLabel={`Seviye ${trNum(level.seviye + 1)} ilerlemesi`} />
      <div style={{ fontSize: 11.5, color: color.ink.muted, fontWeight: 600, marginTop: 8 }}>
        <span style={numText}>{trNum(level.kalanXp)}</span> XP kaldı — birkaç oturum daha.
      </div>
    </div>
  );
}

export default LigPage;
