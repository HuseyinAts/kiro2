// ============================================================================
// KIRO2 — Öğrenme Yolu (SPRINT5 · KIRO2 Ogrenme Yolu.dc.html · SPRINT5_SPEC §B)
// Tema = PAPER. SideNav(active=path) + header (seri/XP pilleri, Panel'le birebir) +
// sol oyunlaştırılmış dikey patika / sağ 320px sticky ray. Rota /yol.
// Kanon: düğüm durum geçişleri SUNUCUDAN gelir — istemci "tamamlandı" işaretlemez
// (çözüm ekranı yazar, yol okur). Ders değişince curriculum+topics+atoms yeniden çekilir.
// AA düzeltmeleri (Faz2 kanonu): current düğüm + level kare + halka pilleri #C2452B
// (parlak #FF6F5C YALNIZ metinsiz dekorasyon: halka/balon kenarı, maskot gradyanı).
// Hareket (kbounce/kring/kfloat) prefers-reduced-motion'da KAPALI (useReducedMotion).
// ============================================================================
import * as React from 'react';

import { getMe, getSubjects, getCurriculum, getTopics, getTopicAtoms } from '../api/api-client';
import { color, font } from '../tokens';
import type { AtomKirilim, CurriculumDers, Persona, Subject, SubjectKey, Topic } from '../types';
import { KiroThemeProvider, numText } from '../ui/theme';
import { SideNav } from '../ui/SideNav';
import { MasteryBadge } from '../ui/MasteryBadge';
import { ProgressRing } from '../ui/ProgressRing';
import { Skeleton } from '../ui/Skeleton';
import { ErrorState } from '../ui/ErrorState';
import { useReducedMotion } from '../ui/ConfettiDawn';
import '../tokens/tokens.css';

const ACCENT = color.dawn.coralCtaBg; // #C2452B — AA-güvenli coral CTA/vurgu (beyaz metin taşır)
const ACCENT_LEDGE = '#973622'; // koyu coral 3D ledge
const trTR = (n: number) => new Intl.NumberFormat('tr-TR').format(n);

// DC "PİKSEL OTORİTESİ": ünite gradyan renkleri (spec #3B6FD4 der; DC #3B82F6 KAZANIR)
const U_COLORS = ['#3B82F6', '#0E9E9E', '#8B5CF6', '#1FB683', '#E0593F', '#D98A2B'];
const OFFSETS = [0, 40, 52, 40, 0, -40, -52, -40];

/** DC darken(): her RGB kanalı × (1-amt), yuvarla. */
function darken(hex: string, amt: number): string {
  const n = parseInt(hex.slice(1), 16);
  let r = (n >> 16) & 255;
  let g = (n >> 8) & 255;
  let b = n & 255;
  r = Math.round(r * (1 - amt));
  g = Math.round(g * (1 - amt));
  b = Math.round(b * (1 - amt));
  return '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
}

/** PanelPage.tsx'ten birebir kopya (jsdom guard'lı). */
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

// ---- Bespoke ikonlar ----
const Alev = (
  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#9A5D0D" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M12 2c1.2 3 4 4.2 4 7.8A4 4 0 0 1 8 10c0-1.4.5-2.4 1-3 .2 1 .9 1.6 1.6 1.6C9.6 6.4 10.8 4.2 12 2Z" /></svg>
);
const Tik = <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden><polyline points="20 6 9 17 4 12" /></svg>;
const Play = <svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor" stroke="none" aria-hidden><path d="M7 5.5v13a1 1 0 0 0 1.5.86l11-6.5a1 1 0 0 0 0-1.72l-11-6.5A1 1 0 0 0 7 5.5Z" /></svg>;
const Yildiz = <svg width="30" height="30" viewBox="0 0 24 24" fill="#FF6F5C" stroke="none" aria-hidden><path d="M12 3.6l2.5 5.1 5.6.8-4.05 3.95.95 5.55L12 16.4 6.95 19l.95-5.55L3.85 9.5l5.6-.8z" /></svg>;
const Kilit = <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><rect x="5" y="11" width="14" height="9" rx="2" /><path d="M8 11V8a4 4 0 0 1 8 0v3" /></svg>;
const Kupa = <svg width="38" height="38" viewBox="0 0 24 24" fill="currentColor" stroke="none" aria-hidden><path d="M7 4h10v2h3v2a4 4 0 0 1-4 4h-.3A5 5 0 0 1 13 14.9V17h2.5a1 1 0 0 1 1 1v1H7.5v-1a1 1 0 0 1 1-1H11v-2.1A5 5 0 0 1 8.3 12H8a4 4 0 0 1-4-4V6h3V4Zm0 4H6a2 2 0 0 0 2 2V8Zm10 0v2a2 2 0 0 0 2-2h-2Z" /></svg>;
const Bayrak = <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M4 21V4M4 4h13l-2 4 2 4H4" /></svg>;
const Baykus = <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden><circle cx="8.5" cy="10" r="2.4" /><circle cx="15.5" cy="10" r="2.4" /><path d="M5 7.5a4 4 0 0 1 4-3.5h6a4 4 0 0 1 4 3.5v5.5a7 7 0 0 1-14 0Z" /><path d="M10.5 16h3" /><path d="M7 4.5 5.5 2.5M17 4.5 18.5 2.5" /></svg>;
const Simsek = <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z" /></svg>;

const STYLE_CSS = `
@keyframes ky-bounce { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-7px); } }
@keyframes ky-ring { 0% { transform: scale(1); opacity: 0.55; } 100% { transform: scale(1.6); opacity: 0; } }
@keyframes ky-float { 0%,100% { transform: translateY(0) rotate(-3deg); } 50% { transform: translateY(-5px) rotate(3deg); } }
.ky-node:active { transform: translateY(5px) !important; box-shadow: none !important; }
.ky-cp:active { transform: translateY(5px) !important; box-shadow: none !important; }
`;

interface NodeVM {
  ad: string;
  offset: number;
  isCurrentFirst: boolean; // yalnız ilk 'current' düğüm: halka + balon + maskot
  locked: boolean;
  nodeStyle: React.CSSProperties;
  labelColor: string;
  icon: React.ReactNode;
  rowPad: string;
}

export function OgrenmeYoluPage(): React.ReactElement {
  const dar = useMedia('(max-width: 1023px)');
  const tek = useMedia('(max-width: 1024px)');
  const daralt = useMedia('(max-width: 390px)');
  const reduced = useReducedMotion();

  const [persona, setPersona] = React.useState<Persona | null>(null);
  const [subjects, setSubjects] = React.useState<Subject[] | null>(null);
  const [curriculum, setCurriculum] = React.useState<CurriculumDers | null>(null);
  const [topics, setTopics] = React.useState<Topic[] | null>(null);
  const [atoms, setAtoms] = React.useState<AtomKirilim | null>(null);
  const [ders, setDers] = React.useState<SubjectKey>('mat');
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);

  React.useEffect(() => {
    let alive = true;
    setCurriculum(null);
    setTopics(null);
    setHata(false);
    (async () => {
      try {
        // getTopicAtoms(enZayifKonu) zorunlu olarak topics'e bağlı → topics'i önce çöz,
        // en zayıf konuyu hesapla, sonra atoms'u çek (Promise.all sırası mantıken korunur).
        const [p, s, cur, tps] = await Promise.all([getMe(), getSubjects(), getCurriculum(ders), getTopics(ders)]);
        if (!alive) return;
        const zayif = tps.slice().sort((a, b) => a.hakimiyet - b.hakimiyet)[0];
        const at = zayif ? await getTopicAtoms(zayif.ad) : null;
        if (!alive) return;
        setPersona(p);
        setSubjects(s);
        setCurriculum(cur);
        setTopics(tps);
        setAtoms(at);
      } catch {
        if (alive) setHata(true);
      }
    })();
    return () => {
      alive = false;
    };
  }, [ders, yeniden]);

  const yukleniyor = curriculum === null || topics === null || persona === null || subjects === null;

  // ---- Türetilenler (yalnız içerik dalında kullanılır) ----
  const dersAd = subjects?.find((s) => s.key === ders)?.ad ?? 'Ders';
  const hakimiyet = subjects?.find((s) => s.key === ders)?.hakimiyet ?? 0;
  const enZayif = topics ? topics.slice().sort((a, b) => a.hakimiyet - b.hakimiyet)[0] : undefined;
  const zayifAtom = atoms?.atomlar.find((a) => a.enZayif)?.ad ?? '';

  // Ofset daraltma (≤390px taşma testi): 0/±28px
  const daraltilmis = (off: number) => (daralt ? (off === 0 ? 0 : off > 0 ? 28 : -28) : off);

  // ---- Patika VM'i: global düğüm sayacı + ilk-current bayrağı ----
  let g = 0;
  let currentPlaced = false;
  const sections = (curriculum?.units ?? []).map((u, ui) => {
    const uColor = U_COLORS[ui % U_COLORS.length]!;
    const nodes: NodeVM[] = u.konular.map((k) => {
      const off = OFFSETS[g % OFFSETS.length]!;
      g += 1;
      const isCurrentFirst = k.durum === 'current' && !currentPlaced;
      if (isCurrentFirst) currentPlaced = true;

      let nodeStyle: React.CSSProperties;
      let labelColor: string = color.ink.muted;
      let icon: React.ReactNode;
      if (k.durum === 'done') {
        nodeStyle = { background: '#1FB683', color: '#fff', boxShadow: '0 5px 0 #17936B' };
        labelColor = color.ink.primary;
        icon = Tik;
      } else if (k.durum === 'current') {
        nodeStyle = { background: ACCENT, color: '#fff', boxShadow: `0 5px 0 ${ACCENT_LEDGE}` };
        labelColor = color.dawn.coralTextOnLight;
        icon = Play;
      } else if (k.durum === 'locked') {
        nodeStyle = { background: '#ECE6DD', color: '#B5AEA2', boxShadow: 'none' };
        labelColor = '#B5AEA2';
        icon = Kilit;
      } else {
        // open (Hazır)
        nodeStyle = { background: '#fff', color: color.dawn.coralTextOnLight, boxShadow: '0 5px 0 #E6DFD4', border: '2px solid #F0EAE1' };
        labelColor = color.ink.secondary;
        icon = Yildiz;
      }
      return {
        ad: k.ad,
        offset: daraltilmis(off),
        isCurrentFirst,
        locked: k.durum === 'locked',
        nodeStyle,
        labelColor,
        icon,
        rowPad: isCurrentFirst ? '38px 0 7px' : '7px 0',
      };
    });

    // Checkpoint
    let cpStyle: React.CSSProperties;
    let cpLabel: string;
    let cpLabelColor: string;
    let cpLocked = false;
    let cpTarget: (() => void) | undefined;
    if (u.durum === 'done') {
      cpStyle = { background: 'linear-gradient(140deg,#FBBF24,#F59E0B)', color: '#fff', boxShadow: '0 6px 0 #D97706' };
      cpLabel = 'ÜNİTE FETHEDİLDİ';
      cpLabelColor = '#9A5D0D';
      cpTarget = () => undefined; // → Ünite özeti (Sınav Sonuç portu)
    } else if (u.durum === 'current') {
      cpStyle = { background: 'linear-gradient(140deg,#FF8A6B,#E0593F)', color: '#fff', boxShadow: '0 6px 0 #B8472E' };
      cpLabel = 'ÜNİTE TESTİ · BOSS';
      cpLabelColor = color.dawn.coralTextOnLight;
      cpTarget = () => undefined; // → Boss Savaşı (S7)
    } else {
      cpStyle = { background: '#F0EAE1', color: '#C4BBAE', boxShadow: 'none' };
      cpLabel = 'KİLİTLİ';
      cpLabelColor = '#B5AEA2';
      cpLocked = true;
    }

    return { no: u.no, ad: u.ad, progress: u.progress, uColor, nodes, cpStyle, cpLabel, cpLabelColor, cpLocked, cpTarget };
  });

  const barW = (progress: string): number => {
    const [a, b] = progress.split('/').map(Number);
    return Math.round(((a ?? 0) / (b || 1)) * 100);
  };

  const railStil: React.CSSProperties = {
    background: color.paper.card,
    border: `1px solid ${color.paper.border}`,
    borderRadius: 18,
    padding: 22,
  };

  return (
    <KiroThemeProvider theme="paper">
      <style>{STYLE_CSS}</style>
      <div className="k-paper" style={{ minHeight: '100vh', background: color.paper.bg, display: 'flex', fontFamily: font.sans, color: color.ink.primary }}>
        <SideNav role="ogrenci" activeId="path" collapsed={dar} userName={persona?.ad ?? 'Öğrenci'} userSub={persona?.sinif ?? ''} onAssistant={() => undefined} />

        <main style={{ flex: 1, minWidth: 0 }}>
          {/* Header — seri + XP pilleri (Panel'le birebir) */}
          <header style={{ position: 'sticky', top: 0, zIndex: 6, minHeight: 66, display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 14, rowGap: 8, padding: '0 30px', background: 'rgba(250,247,242,0.86)', backdropFilter: 'blur(8px)', borderBottom: `1px solid ${color.paper.border}` }}>
            <h1 style={{ margin: 0, fontSize: 18, fontWeight: 800, letterSpacing: '-0.02em' }}>Öğrenme Yolu</h1>
            <div style={{ flex: 1 }} />
            <div style={{ display: 'flex', alignItems: 'center', gap: 7, height: 38, padding: '0 12px', background: color.semantic.riskBgSoft, border: `1px solid ${color.semantic.riskBorderSoft}`, borderRadius: 10 }}>
              {Alev}
              <span style={{ ...numText, fontWeight: 800, fontSize: 14, color: '#9A5D0D' }}>{persona?.seri ?? 0}</span>
              <span style={{ fontSize: 12, color: '#C99A6A', fontWeight: 600 }}>gün</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 9, height: 38, padding: '0 12px', background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 10 }}>
              <span aria-hidden style={{ width: 22, height: 22, borderRadius: 7, background: ACCENT, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 800, fontSize: 11 }}>{persona?.seviye ?? 0}</span>
              <span style={{ ...numText, fontWeight: 700, fontSize: 13, color: color.ink.primary }}>{trTR(persona?.xp ?? 0)}</span>
              <span style={{ fontSize: 11.5, color: color.ink.muted, fontWeight: 600 }}>XP</span>
            </div>
          </header>

          <div style={{ maxWidth: 1180, width: '100%', boxSizing: 'border-box', padding: daralt ? '18px 14px 60px' : '22px 30px 60px' }}>
            {hata ? (
              <ErrorState serifTitle="Öğrenme yolun şu an gelmedi." body="Sorun sende değil — bağlantı bir soluklandı, patikan güvende. Hazır olduğunda tekrar dene." onRetry={() => setYeniden((n) => n + 1)} />
            ) : yukleniyor ? (
              <div aria-busy="true" aria-label="Öğrenme yolu yükleniyor" style={{ display: 'grid', gridTemplateColumns: tek ? '1fr' : '1fr 320px', gap: 26, alignItems: 'start' }}>
                <div style={{ display: 'grid', gap: 12 }}>
                  <div style={{ ...railStil, borderRadius: 16 }}><Skeleton shape="card" delayMs={0} slowAfterMs={null} /></div>
                  <div style={{ display: 'grid', gap: 14, justifyItems: 'center', padding: '10px 0' }}>
                    {[0, 1, 2, 3].map((i) => <Skeleton key={i} shape="bar" width={72} height={72} delayMs={0} />)}
                  </div>
                </div>
                {!tek && <div style={railStil}><Skeleton shape="card" delayMs={0} slowAfterMs={null} /></div>}
              </div>
            ) : (
              <>
                {/* Ders değiştirici */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 20, flexWrap: 'wrap' }}>
                  {subjects!.map((s) => {
                    const aktif = s.key === ders;
                    return (
                      <button
                        key={s.key}
                        type="button"
                        onClick={() => setDers(s.key)}
                        aria-pressed={aktif}
                        style={{
                          display: 'inline-flex', alignItems: 'center', height: 44, padding: '0 16px', borderRadius: 999,
                          fontFamily: font.sans, fontSize: 13, cursor: 'pointer',
                          ...(aktif
                            ? { background: ACCENT, color: '#fff', fontWeight: 700, border: 'none', boxShadow: `0 3px 0 ${ACCENT_LEDGE}` }
                            : { background: '#fff', color: color.ink.secondary, fontWeight: 600, border: `1px solid ${color.paper.border}` }),
                        }}
                      >
                        {s.ad}
                      </button>
                    );
                  })}
                  {/* marginLeft:auto (spacer div DEĞİL) → flex-wrap'ta özet güvenle alt satıra sarar, taşma yok */}
                  <span style={{ marginLeft: 'auto', fontSize: 13, fontWeight: 600, color: color.ink.muted }}>
                    <strong style={{ ...numText, color: color.ink.primary, fontWeight: 800 }}>{curriculum!.done}/{curriculum!.total}</strong> konu · hâkimiyet <strong style={{ ...numText, color: color.ink.primary, fontWeight: 800 }}>%{hakimiyet}</strong>
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: tek ? '1fr' : 'minmax(0,1fr) 320px', gap: 26, alignItems: 'start' }}>
                  {/* ===== PATİKA ===== */}
                  <div style={{ minWidth: 0 }}>
                    {sections.map((sec) => (
                      <div key={sec.no}>
                        {/* Ünite bandı */}
                        <div style={{ borderRadius: 16, padding: '15px 20px', marginBottom: 6, color: '#fff', boxShadow: `0 6px 0 ${darken(sec.uColor, 0.28)}`, background: `linear-gradient(120deg, ${sec.uColor}, ${darken(sec.uColor, 0.12)})` }}>
                          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 12 }}>
                            <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: '0.09em', opacity: 0.85 }}>{sec.no}. ÜNİTE</div>
                            <span style={{ ...numText, fontSize: 12.5, fontWeight: 800, opacity: 0.95, flexShrink: 0 }}>{sec.progress}</span>
                          </div>
                          <div style={{ fontSize: 17, fontWeight: 800, letterSpacing: '-0.01em', lineHeight: 1.2, margin: '3px 0 11px' }}>{sec.ad}</div>
                          <div aria-hidden style={{ height: 8, borderRadius: 99, background: 'rgba(255,255,255,0.28)', overflow: 'hidden' }}>
                            <div style={{ height: '100%', borderRadius: 99, background: '#fff', width: `${barW(sec.progress)}%` }} />
                          </div>
                        </div>

                        {/* Düğümler */}
                        <div style={{ position: 'relative', padding: '18px 0 26px' }}>
                          <div aria-hidden style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: 4, transform: 'translateX(-2px)', background: 'repeating-linear-gradient(to bottom, #E0D8CC 0 7px, transparent 7px 15px)', zIndex: 0 }} />
                          {sec.nodes.map((n, ni) => (
                            <div key={`${sec.no}-${ni}`} style={{ position: 'relative', zIndex: 1, display: 'flex', justifyContent: 'center', padding: n.rowPad }}>
                              <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center', transform: `translateX(${n.offset}px)` }}>
                                {/* BAŞLA balonu (yalnız ilk current) */}
                                {n.isCurrentFirst && (
                                  <div aria-hidden style={{ position: 'absolute', top: -34, zIndex: 3, background: '#fff', border: '2px solid #FF6F5C', color: color.dawn.coralTextOnLight, fontWeight: 800, fontSize: 12, letterSpacing: '0.04em', padding: '5px 13px', borderRadius: 99, whiteSpace: 'nowrap', boxShadow: '0 4px 12px -4px rgba(16,24,40,.25)', animation: reduced ? undefined : 'ky-bounce 1.4s ease-in-out infinite' }}>
                                    BAŞLA
                                    <span style={{ position: 'absolute', left: '50%', bottom: -6, width: 10, height: 10, background: '#fff', borderRight: '2px solid #FF6F5C', borderBottom: '2px solid #FF6F5C', transform: 'translateX(-50%) rotate(45deg)' }} />
                                  </div>
                                )}

                                <button
                                  type="button"
                                  className="ky-node"
                                  aria-label={n.ad}
                                  {...(n.locked ? { 'aria-disabled': true } : { onClick: () => undefined /* → Soru Çözme (portlu; app-shell rota bağlar) */ })}
                                  style={{ position: 'relative', width: 72, height: 72, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 0, cursor: n.locked ? 'default' : 'pointer', transition: 'transform 0.08s ease', ...n.nodeStyle }}
                                >
                                  {n.isCurrentFirst && (
                                    <span aria-hidden style={{ position: 'absolute', inset: -5, borderRadius: '50%', border: '3px solid #FF6F5C', pointerEvents: 'none', animation: reduced ? undefined : 'ky-ring 1.7s ease-out infinite' }} />
                                  )}
                                  {n.icon}
                                </button>

                                <div style={{ marginTop: 8, maxWidth: 128, fontSize: 11.5, fontWeight: 700, color: n.labelColor, textAlign: 'center', lineHeight: 1.25 }}>{n.ad}</div>

                                {/* Maskot (yalnız ilk current) */}
                                {n.isCurrentFirst && (
                                  <div aria-hidden style={{ position: 'absolute', top: 6, ...(n.offset <= 0 ? { left: 62 } : { right: 62 }), zIndex: 2, display: 'flex', animation: reduced ? undefined : 'ky-float 3s ease-in-out infinite' }}>
                                    <div style={{ width: 46, height: 46, borderRadius: '50%', background: 'linear-gradient(140deg,#FFB570,#FF6F91)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 6px 14px -5px rgba(255,111,145,.5)' }}>
                                      {Baykus}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}

                          {/* Checkpoint (ünite testi / boss) */}
                          <div style={{ position: 'relative', zIndex: 1, display: 'flex', justifyContent: 'center', padding: '10px 0 4px' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                              <button
                                type="button"
                                className="ky-cp"
                                aria-label={`${sec.no}. ünite · ${sec.cpLabel}`}
                                {...(sec.cpLocked ? { 'aria-disabled': true } : { onClick: sec.cpTarget })}
                                style={{ width: 86, height: 86, borderRadius: 24, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 0, cursor: sec.cpLocked ? 'default' : 'pointer', border: 'none', transition: 'transform 0.08s ease', ...sec.cpStyle }}
                              >
                                {Kupa}
                              </button>
                              <div style={{ marginTop: 8, fontSize: 11.5, fontWeight: 800, color: sec.cpLabelColor, letterSpacing: '0.03em' }}>{sec.cpLabel}</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}

                    {/* Patika sonu bayrağı */}
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '6px 0 0' }}>
                      <div aria-hidden style={{ width: 56, height: 56, borderRadius: 18, background: '#F0EAE1', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#B5AEA2' }}>{Bayrak}</div>
                      <div style={{ marginTop: 8, fontSize: 12, fontWeight: 700, color: color.ink.muted }}>{dersAd} bitiş</div>
                    </div>
                  </div>

                  {/* ===== SAĞ RAY ===== */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 16, position: tek ? 'static' : 'sticky', top: 90 }}>
                    {/* (a) Sıradaki adım */}
                    <div style={{ ...railStil, boxShadow: '0 1px 2px rgba(16,24,40,.04),0 10px 28px -18px rgba(16,24,40,.18)' }}>
                      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 7, height: 26, padding: '0 11px', borderRadius: 999, background: '#FFF3EE', color: color.dawn.coralTextOnLight, fontSize: 12, fontWeight: 700, marginBottom: 13 }}>
                        {Simsek}
                        Sıradaki adım
                      </div>
                      <div style={{ marginBottom: 11 }}><MasteryBadge pct={enZayif?.hakimiyet ?? hakimiyet} trend="up" /></div>
                      <h2 style={{ margin: '0 0 6px', fontSize: 18, fontWeight: 700, letterSpacing: '-0.015em', color: color.ink.primary }}>{enZayif?.ad ?? dersAd}</h2>
                      <p style={{ margin: '0 0 16px', fontSize: 13, color: color.ink.muted, lineHeight: 1.6 }}>
                        Bu derste en düşük hâkimiyetli konun (%{enZayif?.hakimiyet ?? hakimiyet}). En çok kazanımı burada elde edersin.
                      </p>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 16, fontSize: 12.5, color: color.ink.muted, fontWeight: 600 }}>
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="m3 7 2 2 4-4" /><path d="m3 17 2 2 4-4" /><line x1="13" y1="6" x2="21" y2="6" /><line x1="13" y1="18" x2="21" y2="18" /></svg>
                          <span style={numText}>{curriculum!.next.q}</span> soru
                        </span>
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><circle cx="12" cy="12" r="9" /><polyline points="12 7 12 12 15 14" /></svg>
                          ~<span style={numText}>{curriculum!.next.min}</span> dk
                        </span>
                      </div>
                      <a href="/soru-cozme" style={{ width: '100%', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 9, height: 50, borderRadius: 14, background: ACCENT, color: '#fff', fontFamily: font.sans, fontSize: 15, fontWeight: 800, textDecoration: 'none', boxSizing: 'border-box', boxShadow: `0 5px 0 ${ACCENT_LEDGE}` }}>
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" stroke="none" aria-hidden><path d="M7 5.5v13a1 1 0 0 0 1.5.86l11-6.5a1 1 0 0 0 0-1.72l-11-6.5A1 1 0 0 0 7 5.5Z" /></svg>
                        Konuya başla
                      </a>
                      {atoms && (
                        <a href={`/atomlar?konu=${encodeURIComponent(enZayif?.ad ?? '')}`} style={{ marginTop: 10, width: '100%', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 8, minHeight: 44, padding: '9px 14px', border: `1px solid ${color.paper.border}`, borderRadius: 13, background: color.paper.subtle2, color: '#9A5D0D', fontFamily: font.sans, fontSize: 13, fontWeight: 700, textDecoration: 'none', lineHeight: 1.35, textAlign: 'center', boxSizing: 'border-box' }}>
                          <svg width="15" height="15" style={{ flexShrink: 0 }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden><circle cx="12" cy="12" r="2.2" /><ellipse cx="12" cy="12" rx="10" ry="4.4" /><ellipse cx="12" cy="12" rx="10" ry="4.4" transform="rotate(60 12 12)" /><ellipse cx="12" cy="12" rx="10" ry="4.4" transform="rotate(120 12 12)" /></svg>
                          Atomlara in · en zayıf: {zayifAtom}
                        </a>
                      )}
                    </div>

                    {/* (b) Ders hâkimiyeti halkası */}
                    <div style={{ ...railStil, display: 'flex', alignItems: 'center', gap: 18 }}>
                      <div style={{ flexShrink: 0 }}>
                        <ProgressRing pct={hakimiyet} size={100} strokeWidth={11} ringColor={ACCENT} label={`%${hakimiyet}`} ariaLabel={`${dersAd} hâkimiyeti yüzde ${hakimiyet}`} />
                      </div>
                      <div>
                        <h2 style={{ margin: '0 0 8px', fontSize: 15.5, fontWeight: 700, color: color.ink.primary }}>{dersAd} hâkimiyeti</h2>
                        <div style={{ fontSize: 13, color: color.ink.muted, lineHeight: 1.7 }}>
                          <strong style={{ ...numText, color: color.ink.primary }}>{curriculum!.done}/{curriculum!.total}</strong> konu tamam<br />
                          Tahmini bitiş: <strong style={{ color: color.ink.primary }}>{curriculum!.est}</strong>
                        </div>
                      </div>
                    </div>

                    {/* (c) Lejant kartı */}
                    <div style={{ background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 18, padding: '18px 22px' }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 11 }}>
                        {[
                          { renk: '#1FB683', ad: 'Tamam', border: undefined as string | undefined },
                          { renk: ACCENT, ad: 'Şu an', border: undefined },
                          { renk: '#fff', ad: 'Hazır', border: '2px solid #E6DFD4' },
                          { renk: '#ECE6DD', ad: 'Kilitli', border: undefined },
                        ].map((l) => (
                          <div key={l.ad} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, color: color.ink.muted, fontWeight: 600 }}>
                            <span aria-hidden style={{ width: 14, height: 14, borderRadius: '50%', background: l.renk, border: l.border }} />
                            {l.ad}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        </main>
      </div>
    </KiroThemeProvider>
  );
}

export default OgrenmeYoluPage;
