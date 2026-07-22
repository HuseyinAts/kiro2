// ============================================================================
// KIRO2 — FSRS Tekrar (SPRINT3 · KIRO2 FSRS Tekrar.dc.html)
// Tema = PAPER. SideNav(active=review) + sayfa (özet) + tekrar-oturumu OVERLAY (modal).
// Kanon: FSRS zamanlama SUNUCUDA — istemci yalnız derece POST eder, aralığı YANITTAN alır.
// Overlay: focus trap + Esc + aria-modal + scroll kilidi; klavye Boşluk=göster, 1-4=derece.
// Tek hareket: ConfettiDawn (bitişte, reduced-motion'da oynatılmaz).
// ============================================================================
import * as React from 'react';

import { configureKiroApi, getMe, getReviewTopics, getReviewSession, postReviewGrade } from '../api/api-client';
import type { MockData, ReviewCard, ReviewGrade } from '../api/api-client';
import type { Persona, ReviewItem } from '../types';
import kiroData from '../api/kiro-data.json';
import { color, font } from '../tokens';
import { KiroThemeProvider, numText } from '../ui/theme';
import { SideNav } from '../ui/SideNav';
import { Button } from '../ui/Button';
import { Skeleton } from '../ui/Skeleton';
import { EmptyState } from '../ui/EmptyState';
import { ErrorState } from '../ui/ErrorState';
import { ConfettiDawn } from '../ui/ConfettiDawn';
import '../tokens/tokens.css';

configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });

const HEDEF_TUTMA = 90; // /me hedef (mock)
const HAFTA = [
  { g: 'Bugün', n: 8 }, { g: 'Yarın', n: 14 }, { g: 'Çar', n: 9 }, { g: 'Per', n: 18 },
  { g: 'Cum', n: 7 }, { g: 'Cmt', n: 11 }, { g: 'Paz', n: 5 },
]; // 7-gün yükü: API yok (açık nokta #1) → mock

const DERECE: { key: ReviewGrade; ad: string; bd: string; bg: string; fg: string; afg: string }[] = [
  { key: 'tekrar', ad: 'Tekrar', bd: '#F0B3A5', bg: '#FCEDE8', fg: '#C2452B', afg: '#C2452B' },
  { key: 'zor', ad: 'Zor', bd: '#FDE68A', bg: '#FFFBEB', fg: '#B45309', afg: '#D97706' },
  { key: 'iyi', ad: 'İyi', bd: '#86EFAC', bg: '#F0FDF4', fg: '#15803D', afg: '#16A34A' },
  { key: 'kolay', ad: 'Kolay', bd: '#93C5FD', bg: '#EFF6FF', fg: '#1D4ED8', afg: '#2563EB' },
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

const kart: React.CSSProperties = { background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 15, padding: 18 };

function barBg(r: number): string {
  if (r < 84) return 'linear-gradient(90deg,#F5B84E,#E0593F)';
  if (r < 92) return 'linear-gradient(90deg,#FCD34D,#1FB683)';
  return '#1FB683';
}
function vade(dueIn: number): { t: string; fg: string; bg: string } {
  if (dueIn <= 0) return { t: 'Bugün', fg: '#C2452B', bg: '#FBE8E2' };
  if (dueIn === 1) return { t: 'Yarın', fg: '#9A5D0D', bg: '#FFEDD5' };
  return { t: `${dueIn} gün`, fg: '#15803D', bg: '#DCFCE7' };
}

const Nokta = ({ renk = '#FF6F5C', size = 7 }: { renk?: string; size?: number }) => <svg width={size} height={size} viewBox="0 0 10 10" aria-hidden style={{ verticalAlign: 'middle' }}><circle cx="5" cy="5" r="5" fill={renk} /></svg>;
const Goz = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" /><circle cx="12" cy="12" r="3" /></svg>;
const Kapat = () => <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M18 6 6 18M6 6l12 12" /></svg>;
const Tik = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M20 6 9 17l-5-5" /></svg>;

function Egri() {
  return (
    <svg viewBox="0 0 320 138" width="100%" height="auto" aria-hidden style={{ display: 'block' }}>
      <line x1="8" y1="58" x2="312" y2="58" stroke="#C4BBAE" strokeWidth="1" strokeDasharray="4 4" />
      <text x="10" y="52" fontSize="8.5" fontWeight="700" fill="#6B6478" fontFamily={font.sans}>%85 hatırlama eşiği</text>
      <path d="M8,22 Q80,74 160,99 T312,120" fill="none" stroke="#E8A05B" strokeWidth="2.4" strokeLinecap="round" opacity="0.7" />
      <path d="M8,22 Q40,42 70,46 L70,18 Q112,38 150,44 L150,15 Q205,34 250,42 L250,13 Q286,24 312,30" fill="none" stroke="#FF6F5C" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="70" cy="18" r="3.6" fill="#FF6F5C" /><circle cx="150" cy="15" r="3.6" fill="#FF6F5C" /><circle cx="250" cy="13" r="3.6" fill="#FF6F5C" />
      <text x="8" y="134" fontSize="8.5" fontWeight="700" fill="#6B6478" fontFamily={font.sans}>Bugün</text>
      <text x="280" y="134" fontSize="8.5" fontWeight="700" fill="#6B6478" fontFamily={font.sans}>+30 gün</text>
    </svg>
  );
}

export interface FSRSPageProps {
  /** Story/demo: overlay'i açık başlat (breakpoint + görsel kapsama için). */
  demoOverlay?: boolean;
}

export function FSRSPage({ demoOverlay = false }: FSRSPageProps): React.ReactElement {
  const dar = useMedia('(max-width: 1023px)');
  const heroStack = useMedia('(max-width: 720px)');
  const [topics, setTopics] = React.useState<ReviewItem[] | null>(null);
  const [cards, setCards] = React.useState<ReviewCard[]>([]);
  const [persona, setPersona] = React.useState<Persona | null>(null);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);

  const [aktif, setAktif] = React.useState(demoOverlay);
  const [kartIdx, setKartIdx] = React.useState(0);
  const [acik, setAcik] = React.useState(false);
  const [bitti, setBitti] = React.useState(false);
  const overlayRef = React.useRef<HTMLDivElement>(null);
  const tetikleyici = React.useRef<HTMLElement | null>(null);

  React.useEffect(() => {
    let alive = true;
    setTopics(null);
    setHata(false);
    Promise.all([getReviewTopics(), getReviewSession(), getMe()])
      .then(([t, c, p]) => { if (!alive) return; setTopics(t); setCards(c); setPersona(p); })
      .catch(() => { if (alive) setHata(true); });
    return () => { alive = false; };
  }, [yeniden]);

  // Overlay: scroll kilidi + odak yönetimi (aç → ilk odak; kapat → tetikleyiciye iade)
  React.useEffect(() => {
    if (!aktif || typeof document === 'undefined') return;
    const onceki = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const t = window.setTimeout(() => {
      overlayRef.current?.querySelector<HTMLElement>('button:not([disabled])')?.focus();
    }, 0);
    return () => { document.body.style.overflow = onceki; window.clearTimeout(t); tetikleyici.current?.focus(); };
  }, [aktif]);

  const dueCount = cards.length;
  const estMin = Math.max(1, Math.round(cards.length * 0.75));
  const riskCount = (topics ?? []).filter((t) => t.dueIn <= 0).length;
  const kart0 = cards[kartIdx];

  const basla = (e: React.MouseEvent) => {
    tetikleyici.current = e.currentTarget as HTMLElement;
    setKartIdx(0); setAcik(false); setBitti(false); setAktif(true);
  };
  const kapat = () => setAktif(false);
  const goster = () => setAcik(true);
  const derecele = async (grade: ReviewGrade) => {
    if (!kart0) return;
    try { await postReviewGrade(kart0.konu, grade); } catch { /* çevrimdışı: /sync/events kuyruğa (ERTELENDİ) */ }
    if (kartIdx + 1 >= cards.length) setBitti(true);
    else { setKartIdx((n) => n + 1); setAcik(false); }
  };

  const overlayTus = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') { e.preventDefault(); kapat(); return; }
    if (e.key === 'Tab') {
      const fs = overlayRef.current?.querySelectorAll<HTMLElement>('button:not([disabled])');
      if (!fs || fs.length === 0) return;
      const ilk = fs[0]!;
      const son = fs[fs.length - 1]!;
      if (e.shiftKey && document.activeElement === ilk) { e.preventDefault(); son.focus(); }
      else if (!e.shiftKey && document.activeElement === son) { e.preventDefault(); ilk.focus(); }
      return;
    }
    if (acik && !bitti) {
      const d = Number(e.key);
      if (d >= 1 && d <= 4) { e.preventDefault(); void derecele(DERECE[d - 1]!.key); }
    }
  };

  return (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={{ minHeight: '100vh', background: color.paper.bg, display: 'flex', fontFamily: font.sans, color: color.ink.primary }}>
        <SideNav role="ogrenci" activeId="review" collapsed={dar} userName={persona?.ad ?? 'Öğrenci'} userSub={persona?.sinif ?? ''} onAssistant={() => undefined} />

        <main style={{ flex: 1, minWidth: 0, height: '100vh', overflowY: 'auto' }}>
          {/* Header */}
          <header style={{ position: 'sticky', top: 0, zIndex: 5, minHeight: 64, display: 'flex', alignItems: 'center', gap: 12, padding: '10px 24px', flexWrap: 'wrap', background: color.paper.card, borderBottom: `1px solid ${color.paper.border}` }}>
            <div style={{ minWidth: 0, flex: 1 }}>
              <div style={{ fontSize: 16, fontWeight: 800 }}>Tekrar · Hafıza Motoru</div>
              <div style={{ fontSize: 12, color: color.ink.muted, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>FSRS · ne zaman unutacağını tahmin eder, tam zamanında getirir</div>
            </div>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: color.paper.subtle, borderRadius: 999, padding: '6px 12px', fontSize: 12, fontWeight: 700, color: color.ink.secondary }}>Hedef tutma <span style={numText}>{HEDEF_TUTMA}%</span></span>
          </header>

          <div style={{ maxWidth: 1000, margin: '0 auto', padding: '26px 30px 50px' }}>
            {hata ? (
              <ErrorState serifTitle="Tekrar şu an gelmedi — senlik bir şey değil." body="Bağlantı bir soluklandı, çalışman güvende. Hazır olduğunda tekrar dene." onRetry={() => setYeniden((n) => n + 1)} retryLabel="Yeniden dene" />
            ) : topics === null ? (
              <div aria-busy="true" aria-label="Tekrar hazırlanıyor" style={{ display: 'grid', gap: 16 }}>
                <div style={{ ...kart, borderRadius: 20 }}><Skeleton shape="card" delayMs={0} slowAfterMs={null} /></div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14 }}>{[0, 1, 2].map((i) => <div key={i} style={kart}><Skeleton shape="row" delayMs={0} /></div>)}</div>
              </div>
            ) : dueCount === 0 ? (
              <EmptyState serifTitle="Bugün tekrar yok — eğrin sağlıklı." body="Hafıza eğrin şu an güçlü; yarın yeni kartlar burada olacak." action={<Button variant="primary" onClick={() => undefined}>Panele dön</Button>} />
            ) : (
              <div style={{ display: 'grid', gap: 18 }}>
                {/* Hero */}
                <div className="k-hero" style={{ display: 'grid', gridTemplateColumns: heroStack ? '1fr' : '1fr 1.15fr', gap: 18 }}>
                  <div style={{ borderRadius: 20, padding: 22, background: `linear-gradient(135deg, ${color.dawn.coralCtaBg}, ${color.dawn.coral})`, color: '#fff' }}>
                    <div style={{ fontSize: 12.5, fontWeight: 700, opacity: 0.92 }}>Bugün tekrar edilecek</div>
                    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, marginTop: 4 }}>
                      <span style={{ ...numText, fontSize: 60, fontWeight: 800, lineHeight: 1 }}>{dueCount}</span>
                      <span style={{ fontSize: 16, fontWeight: 700, marginBottom: 8 }}>kart</span>
                    </div>
                    <div style={{ fontSize: 13, marginTop: 6, opacity: 0.95 }}>Tahmini süre ~<span style={numText}>{estMin}</span> dk · tam zamanında, fazlası değil</div>
                    <div style={{ marginTop: 16 }}>
                      <button type="button" onClick={basla} style={{ minHeight: 44, padding: '0 18px', borderRadius: 12, border: 'none', background: '#fff', color: color.dawn.coralCtaBg, fontFamily: font.sans, fontSize: 14.5, fontWeight: 800, cursor: 'pointer' }}>Tekrara başla</button>
                    </div>
                  </div>
                  <div style={{ ...kart, borderRadius: 20 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginBottom: 8, flexWrap: 'wrap' }}>
                      <span style={{ fontSize: 14, fontWeight: 800 }}>Unutma eğrisi</span>
                      <span style={{ display: 'inline-flex', gap: 12, fontSize: 11, fontWeight: 700 }}>
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, color: color.dawn.coralTextOnLight }}><span aria-hidden style={{ width: 14, height: 3, borderRadius: 2, background: '#FF6F5C' }} />Tekrarla</span>
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, color: '#9A5D0D' }}><span aria-hidden style={{ width: 14, height: 3, borderRadius: 2, background: '#E8A05B' }} />Tekrarsız</span>
                      </span>
                    </div>
                    <Egri />
                    <p style={{ margin: '8px 0 0', fontSize: 12, color: color.ink.muted, lineHeight: 1.5 }}>Her tekrar (<Nokta size={6} />) hatırlamayı tazeler ve aralığı uzatır — tekrarsız bilgi hızla unutulur.</p>
                  </div>
                </div>

                {/* Stats */}
                <div className="k-stats" style={{ display: 'grid', gridTemplateColumns: heroStack ? '1fr' : 'repeat(3, 1fr)', gap: 14 }}>
                  {[
                    { et: 'Tutma oranı', v: '91%', vc: '#1FB683', alt: 'son 30 gün · hedefin üstünde' },
                    { et: 'Bu hafta tekrar', v: '142', vc: color.ink.primary, alt: 'kart · 6 gün üst üste' },
                    { et: 'Risk altında', v: String(riskCount), vc: '#E0593F', alt: 'konu · eşiğe yaklaşıyor' },
                  ].map((s) => (
                    <div key={s.et} style={kart}>
                      <div style={{ fontSize: 12, color: color.ink.muted, fontWeight: 700 }}>{s.et}</div>
                      <div style={{ ...numText, fontSize: 26, fontWeight: 800, color: s.vc, marginTop: 4 }}>{s.v}</div>
                      <div style={{ fontSize: 11.5, color: color.ink.muted, marginTop: 2 }}>{s.alt}</div>
                    </div>
                  ))}
                </div>

                {/* Konuya göre hafıza gücü */}
                <div style={{ ...kart, borderRadius: 18, padding: 20 }}>
                  <div style={{ fontSize: 15.5, fontWeight: 800 }}>Konuya göre hafıza gücü</div>
                  <div style={{ fontSize: 12, color: color.ink.muted, margin: '2px 0 14px' }}>Her konu için “unutmana kalan süre” — “Bugün” etiketliler tekrar istiyor.</div>
                  <ul style={{ margin: 0, padding: 0, display: 'grid', gap: 12, listStyle: 'none' }}>
                    {topics.map((t) => {
                      const v = vade(t.dueIn);
                      return (
                        <li key={t.konu} style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                          <span style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 150, flex: 1 }}>
                            <Nokta renk={color.subject.light[t.ders] ?? '#8C8598'} size={9} />
                            <span style={{ minWidth: 0 }}>
                              <span style={{ display: 'block', fontSize: 13.5, fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{t.konu}</span>
                              <span style={{ fontSize: 11, color: color.ink.muted, textTransform: 'uppercase' }}>{t.ders}</span>
                            </span>
                          </span>
                          <span aria-hidden style={{ flex: 1, minWidth: 90, height: 9, borderRadius: 999, background: '#F0EAE1', overflow: 'hidden' }}>
                            <span style={{ display: 'block', height: '100%', width: `${t.hatirlanabilirlik}%`, background: barBg(t.hatirlanabilirlik) }} />
                          </span>
                          <span style={{ fontSize: 11.5, fontWeight: 800, color: v.fg, background: v.bg, borderRadius: 8, padding: '5px 10px' }}>{v.t}</span>
                          <span style={{ ...numText, fontSize: 13, fontWeight: 700, minWidth: 40, textAlign: 'right' }}>%{t.hatirlanabilirlik}</span>
                        </li>
                      );
                    })}
                  </ul>
                </div>

                {/* Önümüzdeki 7 gün · tekrar yükü */}
                <div style={{ ...kart, borderRadius: 18, padding: 20 }}>
                  <div style={{ fontSize: 15.5, fontWeight: 800 }}>Önümüzdeki 7 gün · tekrar yükü</div>
                  <div style={{ fontSize: 12, color: color.ink.muted, margin: '2px 0 14px' }}>FSRS yükü dengeler — hiçbir gün seni ezmez.</div>
                  <div aria-hidden style={{ display: 'flex', alignItems: 'flex-end', gap: 14, height: 130 }}>
                    {HAFTA.map((d, i) => (
                      <div key={d.g} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
                        <div style={{ width: '100%', maxWidth: 46, height: `${(d.n / 20) * 100}%`, borderRadius: '9px 9px 4px 4px', background: i === 0 ? '#FF6F5C' : '#FFD3C4' }} />
                        <span style={{ fontSize: 10.5, fontWeight: 700, color: i === 0 ? color.dawn.coralTextOnLight : color.ink.muted }}>{d.g}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </main>

        {/* Tekrar oturumu overlay */}
        {aktif && (
          <div
            style={{ position: 'fixed', inset: 0, zIndex: 60, background: 'rgba(15,23,42,0.55)', backdropFilter: 'blur(3px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}
            onKeyDown={overlayTus}
          >
            <div ref={overlayRef} role="dialog" aria-modal="true" aria-label="Tekrar oturumu" style={{ width: 'min(580px, 100%)', maxHeight: '90vh', overflowY: 'auto', background: '#fff', borderRadius: 22, boxShadow: '0 30px 70px -20px rgba(0,0,0,0.5)', padding: 22 }}>
              {!bitti && kart0 ? (
                <>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 15, fontWeight: 800 }}>Tekrar oturumu</div>
                      <div style={{ ...numText, fontSize: 12, color: color.ink.muted }}>Kart {kartIdx + 1} / {cards.length}</div>
                    </div>
                    <button type="button" onClick={kapat} aria-label="Kapat" style={{ width: 44, height: 44, borderRadius: 12, border: `1px solid ${color.paper.border}`, background: color.paper.card, color: color.ink.secondary, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}><Kapat /></button>
                  </div>
                  <div aria-hidden style={{ height: 6, borderRadius: 999, background: color.paper.border, marginBottom: 18 }}>
                    <div style={{ height: '100%', borderRadius: 999, width: `${((kartIdx + (acik ? 1 : 0)) / cards.length) * 100}%`, background: color.dawn.coralCtaBg }} />
                  </div>

                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 700, color: color.subject.light[kart0.ders] ?? color.ink.secondary, background: color.paper.subtle, borderRadius: 999, padding: '4px 11px' }}><Nokta renk={color.subject.light[kart0.ders] ?? '#8C8598'} />{kart0.konu}</span>
                  <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: '0.04em', color: color.ink.muted, margin: '16px 0 8px' }}>SORU</div>
                  <p style={{ margin: 0, fontSize: 20, fontWeight: 700, lineHeight: 1.5, minHeight: 60 }}>{kart0.front}</p>

                  {!acik ? (
                    <div style={{ marginTop: 20 }}>
                      <Button variant="primary" size="lg" icon={<Goz />} onClick={goster}>Cevabı göster</Button>
                    </div>
                  ) : (
                    <div style={{ marginTop: 18 }}>
                      <div style={{ padding: '14px 16px', borderRadius: 14, background: '#F0FDF4', border: '1px solid #BBF7D0' }}>
                        <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: '0.04em', color: '#16A34A', marginBottom: 6 }}>CEVAP</div>
                        <p style={{ margin: 0, fontSize: 15, lineHeight: 1.6, color: '#166534' }}>{kart0.back}</p>
                      </div>
                      <p style={{ margin: '16px 0 10px', fontSize: 13, color: color.ink.secondary, textAlign: 'center' }}>Ne kadar kolay hatırladın? — aralığı FSRS belirler</p>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 9 }}>
                        {DERECE.map((d, i) => (
                          <button
                            key={d.key} type="button" onClick={() => void derecele(d.key)}
                            aria-keyshortcuts={String(i + 1)}
                            style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3, minHeight: 56, padding: '10px 6px', borderRadius: 12, cursor: 'pointer', fontFamily: font.sans,
                              border: `1.5px solid ${d.bd}`, background: d.bg, color: d.fg }}
                          >
                            <span style={{ fontSize: 13.5, fontWeight: 800 }}>{d.ad}</span>
                            <span style={{ ...numText, fontSize: 11, fontWeight: 700, color: d.afg }}>{kart0.previews[d.key]}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div style={{ textAlign: 'center', position: 'relative' }}>
                  <ConfettiDawn count={26} />
                  <div aria-hidden style={{ width: 56, height: 56, margin: '4px auto 14px', borderRadius: 999, background: '#1FB683', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Tik /></div>
                  <h2 style={{ margin: 0, fontSize: 24, fontWeight: 800 }}>Bugünün tekrarı tamam</h2>
                  <p style={{ margin: '10px 0 0', fontSize: 14.5, lineHeight: 1.6, color: color.ink.secondary }}>
                    <strong style={{ color: color.ink.primary }}><span style={numText}>{cards.length}</span> kart</strong> tam zamanında tekrarlandı — hafıza eğrin tazelendi. Serin <strong style={{ color: color.ink.primary }}><span style={numText}>{(persona?.seri ?? 0) + 1}</span>. güne</strong> uzadı.
                  </p>
                  <div style={{ marginTop: 20, display: 'grid', gap: 10 }}>
                    <Button variant="primary" onClick={() => undefined}>Günü kutla</Button>
                    <Button variant="ghost" onClick={kapat}>Panele dön</Button>
                    <Button variant="ghost" onClick={() => undefined}>Soru çözmeye geç</Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </KiroThemeProvider>
  );
}

export default FSRSPage;
