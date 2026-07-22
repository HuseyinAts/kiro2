// ============================================================================
// KIRO2 — Adaptif Test (SPRINT4 · KIRO2 Adaptif Test.dc.html)
// Tema = PAPER. SideNav YOK (odak modu). Header + soru sütunu + MOTOR PANELİ (380px sticky).
// KANON: θ/SE/madde-seçimi/durdurma SUNUCUDA (postCatNext) — DC IRT simülasyonu taşınmaz.
// Motor paneli sunucu değerleriyle çizilir ve KALIR (ekranın kimliği; şeffaf motor = güven).
// Doğru/yanlış geri bildirimi YOK (yerleştirme, ceza yok). Grafikler aria-hidden; bitişte tek polite duyuru.
// ============================================================================
import * as React from 'react';

import { configureKiroApi, postCatNext } from '../api/api-client';
import type { MockData, CatNextResult, CatUygulanan } from '../api/api-client';
import type { CatItem } from '../types';
import kiroData from '../api/kiro-data.json';
import { color, font } from '../tokens';
import { KiroThemeProvider, numText } from '../ui/theme';
import { Skeleton } from '../ui/Skeleton';
import { ErrorState } from '../ui/ErrorState';
import '../tokens/tokens.css';

configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });

const HARFLER = ['A', 'B', 'C', 'D', 'E'];
const MAT = color.subject.light.mat;

function trOndalik(n: number, d = 2): string {
  return new Intl.NumberFormat('tr-TR', { minimumFractionDigits: d, maximumFractionDigits: d }).format(n).replace('-', '−');
}
function useDar(): boolean {
  const [dar, setDar] = React.useState(false);
  React.useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return;
    const mq = window.matchMedia('(max-width: 900px)');
    const on = () => setDar(mq.matches);
    on(); mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, []);
  return dar;
}

const SEVIYE: Record<CatNextResult['seviye'], { ad: string; fg: string; bg: string }> = {
  zayif: { ad: 'Zayıf', fg: '#E0593F', bg: 'rgba(224,89,63,0.15)' },
  orta: { ad: 'Orta', fg: '#9A5D0D', bg: 'rgba(245,158,11,0.15)' },
  guclu: { ad: 'Güçlü', fg: '#0E9E6E', bg: 'rgba(16,185,129,0.15)' },
};
function zorluk(b: number): { ad: string; c: string; fg: string } {
  if (b <= -0.3) return { ad: 'Kolay', c: '#1FB683', fg: '#047857' };
  if (b <= 0.9) return { ad: 'Orta', c: '#F59E0B', fg: '#B45309' };
  return { ad: 'Zor', c: '#E8836B', fg: '#C2452B' };
}
const fillN = (b: number) => Math.max(1, Math.min(5, Math.round(((b + 1.5) / 3.5) * 5)));

const Kapat = () => <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M18 6 6 18M6 6l12 12" /></svg>;
const Hedef = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="4" /></svg>;
const Ok = () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M5 12h14M13 6l6 6-6 6" /></svg>;
const Tik = () => <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M20 6 9 17l-5-5" /></svg>;

const kart: React.CSSProperties = { background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 18, padding: 20 };

// θ Yakınsaması SVG — uygulananlar[].theta/se'den (istemci HESAPLAMAZ, çizer)
function Yakinsama({ ug }: { ug: CatUygulanan[] }) {
  const W = 340, H = 160;
  const cx = (i: number) => 20 + (i / 11) * 300;
  const cy = (th: number) => 80 - Math.max(-2, Math.min(2, th)) * 34;
  const cizgi = ug.map((u, i) => `${i === 0 ? 'M' : 'L'}${cx(i).toFixed(1)},${cy(u.theta).toFixed(1)}`).join(' ');
  const ust = ug.map((u, i) => `${i === 0 ? 'M' : 'L'}${cx(i).toFixed(1)},${cy(u.theta + u.se).toFixed(1)}`).join(' ');
  const alt = [...ug].reverse().map((u, i) => `L${cx(ug.length - 1 - i).toFixed(1)},${cy(u.theta - u.se).toFixed(1)}`).join(' ');
  const son = ug[ug.length - 1];
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="auto" aria-hidden style={{ display: 'block' }}>
      {[40, 80, 120].map((y) => <line key={y} x1="10" y1={y} x2="330" y2={y} stroke={color.paper.border} strokeWidth="1" />)}
      {ug.length >= 2 && <path d={`${ust} ${alt} Z`} fill={color.dawn.coral} opacity="0.12" />}
      {ug.length >= 2 && <path d={cizgi} fill="none" stroke={color.dawn.coral} strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />}
      {son && <circle cx={cx(ug.length - 1)} cy={cy(son.theta)} r="5" fill="#fff" stroke={color.dawn.coral} strokeWidth="3" />}
      <text x="20" y="152" fontSize="10.5" fontWeight="600" fill={color.ink.muted} fontFamily={font.sans}>Madde 1</text>
      <text x="165" y="152" fontSize="10.5" fontWeight="600" fill={color.ink.muted} fontFamily={font.sans}>6</text>
      <text x="315" y="152" fontSize="10.5" fontWeight="600" fill={color.ink.muted} fontFamily={font.sans}>12</text>
    </svg>
  );
}

export function AdaptifTestPage(): React.ReactElement {
  const dar = useDar();
  const [madde, setMadde] = React.useState(0);
  const [item, setItem] = React.useState<CatItem | null>(null);
  const [motor, setMotor] = React.useState<CatNextResult | null>(null);
  const [secilen, setSecilen] = React.useState<number | null>(null);
  const [odak, setOdak] = React.useState(0);
  const [gonderiliyor, setGonderiliyor] = React.useState(false);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);
  const grpRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    let alive = true;
    setMotor(null); setItem(null); setHata(false); setMadde(0); setSecilen(null); setOdak(0);
    postCatNext({ madde: 0 })
      .then((r) => { if (!alive) return; setMotor(r); setItem(r.item as CatItem); })
      .catch(() => { if (alive) setHata(true); });
    return () => { alive = false; };
  }, [yeniden]);

  const bitti = !!motor?.done;

  const gonder = async (secim: number | null) => {
    if (!item || gonderiliyor || bitti) return;
    setGonderiliyor(true);
    try {
      const r = await postCatNext({ madde: madde + 1, secim, maddeId: item.id });
      setMotor(r); setMadde(r.madde); setSecilen(null); setOdak(0);
      if (!r.done) setItem(r.item as CatItem);
    } catch { setHata(true); }
    finally { setGonderiliyor(false); }
  };

  const grupTus = (e: React.KeyboardEvent) => {
    if (!item || bitti) return;
    const n = item.secenekler.length;
    const radios = grpRef.current?.querySelectorAll<HTMLButtonElement>('[role="radio"]');
    const tasi = (to: number) => { e.preventDefault(); setOdak(to); radios?.[to]?.focus(); };
    if (e.key === 'ArrowDown' || e.key === 'ArrowRight') return tasi((odak + 1) % n);
    if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') return tasi((odak - 1 + n) % n);
    const d = Number(e.key);
    if (Number.isInteger(d) && d >= 1 && d <= n) { e.preventDefault(); setOdak(d - 1); setSecilen(d - 1); return; }
    const h = HARFLER.indexOf(e.key.toUpperCase());
    if (h >= 0 && h < n) { e.preventDefault(); setOdak(h); setSecilen(h); }
  };

  const ug = motor?.uygulananlar ?? [];
  const dogruSay = ug.filter((u) => u.ok).length;
  const yanlisSay = ug.length - dogruSay;
  const seProgress = motor ? Math.max(0, Math.min(100, ((0.72 - motor.se) / (0.72 - 0.28)) * 100)) : 0;
  const markLeft = motor ? Math.max(0, Math.min(100, ((motor.theta + 3) / 6) * 100)) : 50;
  const bandLeft = motor ? Math.max(0, ((motor.theta - motor.se + 3) / 6) * 100) : 0;
  const bandW = motor ? ((2 * motor.se) / 6) * 100 : 0;
  const kalan = motor ? Math.max(0, Math.ceil((motor.se - 0.28) / 0.04)) : 0;

  return (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={{ minHeight: '100vh', background: color.paper.bg, display: 'flex', flexDirection: 'column', fontFamily: font.sans, color: color.ink.primary }}>
        {/* Header */}
        <header style={{ position: 'sticky', top: 0, zIndex: 5, minHeight: 62, display: 'flex', alignItems: 'center', gap: 14, padding: '9px 22px', flexWrap: 'wrap', background: color.paper.card, borderBottom: `1px solid ${color.paper.border}` }}>
          <button type="button" onClick={() => undefined} aria-label="Kapat" style={{ flexShrink: 0, width: 44, height: 44, borderRadius: 12, border: `1px solid ${color.paper.border}`, background: color.paper.card, color: color.ink.muted, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}><Kapat /></button>
          <div style={{ minWidth: 0, flex: 1 }}>
            <h1 style={{ margin: 0, fontSize: 15.5, fontWeight: 700 }}>Adaptif Yerleştirme Testi</h1>
            <div style={{ fontSize: 12, color: color.ink.muted, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>TYT Matematik · seviyene göre uyarlanıyor</div>
          </div>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, height: 28, padding: '0 11px', borderRadius: 999, background: '#FFF3EE', color: color.dawn.coralTextOnLight, fontSize: 13, fontWeight: 700 }}><Hedef />CAT · IRT</span>
          <span style={{ fontSize: 12, color: color.ink.muted }}>Uygulanan madde <span style={{ ...numText, fontSize: 16, fontWeight: 800, color: color.ink.primary }}>{ug.length}</span></span>
        </header>

        <div style={{ flex: 1, width: '100%', maxWidth: 1280, margin: '0 auto', boxSizing: 'border-box', padding: dar ? 18 : 24, display: 'grid', gridTemplateColumns: dar ? '1fr' : '1fr 380px', gap: dar ? 16 : 20, alignItems: 'start' }}>
          {hata ? (
            <div style={{ gridColumn: '1 / -1' }}>
              <ErrorState onRetry={() => setYeniden((n) => n + 1)} />
            </div>
          ) : motor === null || item === null ? (
            <div aria-busy="true" aria-label="Test hazırlanıyor" style={{ gridColumn: '1 / -1' }}>
              <div style={{ ...kart, padding: 26 }}><Skeleton shape="card" delayMs={0} slowAfterMs={null} /><p style={{ marginTop: 12, fontSize: 12.5, color: color.ink.muted }}>Test hazırlanıyor…</p></div>
            </div>
          ) : (
            <>
              {/* Soru sütunu */}
              <div style={{ display: 'grid', gap: 16, minWidth: 0 }}>
                {!bitti ? (
                  <div style={{ ...kart, padding: '26px 28px' }}>
                    {/* Meta */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 20, flexWrap: 'wrap' }}>
                      <span style={{ fontSize: 15, fontWeight: 800 }}>Madde <span style={numText}>{ug.length + 1}</span></span>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, height: 26, padding: '0 11px', borderRadius: 999, background: '#EFF6FF', color: MAT, fontSize: 12, fontWeight: 700 }}><span aria-hidden style={{ width: 7, height: 7, borderRadius: 999, background: MAT }} />Matematik</span>
                      <span style={{ flex: 1 }} />
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: 12, fontWeight: 700, color: color.ink.muted }}>Zorluk: <strong style={{ color: zorluk(item.b).fg }}>{zorluk(item.b).ad}</strong></span>
                        <span aria-hidden style={{ display: 'inline-flex', alignItems: 'flex-end', gap: 2 }}>
                          {[0, 1, 2, 3, 4].map((i) => <span key={i} style={{ width: 7, height: 16, borderRadius: 3, background: i < fillN(item.b) ? zorluk(item.b).c : color.paper.border }} />)}
                        </span>
                      </span>
                    </div>
                    {/* Stem */}
                    <p style={{ margin: '0 0 24px', fontSize: 17, lineHeight: 1.75 }}>{item.soru}</p>
                    {/* Seçenekler (geri bildirim YOK) */}
                    <div ref={grpRef} role="radiogroup" aria-label="Şıklar" onKeyDown={grupTus} style={{ display: 'grid', gap: 11 }}>
                      {item.secenekler.map((sec, i) => {
                        const sc = i === secilen;
                        return (
                          <button key={i} type="button" role="radio" aria-checked={sc} tabIndex={i === odak ? 0 : -1}
                            onClick={() => { setOdak(i); setSecilen(i); }}
                            style={{ display: 'flex', alignItems: 'center', gap: 14, minHeight: 44, padding: '13px 16px', textAlign: 'left', width: '100%', borderRadius: 13, cursor: 'pointer', fontFamily: font.sans, background: sc ? '#FFF3EE' : color.paper.card, border: `1.5px solid ${sc ? color.dawn.coral : color.paper.border}` }}>
                            <span aria-hidden style={{ flexShrink: 0, width: 30, height: 30, borderRadius: 9, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13.5, fontWeight: 800, background: sc ? color.dawn.coralCtaBg : '#ECE6DD', color: sc ? '#fff' : '#4A4456' }}>{HARFLER[i]}</span>
                            <span style={{ ...numText, flex: 1, fontSize: 15, fontWeight: 600 }}>{sec}</span>
                          </button>
                        );
                      })}
                    </div>
                    {/* Aksiyon */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 22, flexWrap: 'wrap' }}>
                      <button type="button" onClick={() => void gonder(null)} disabled={gonderiliyor} style={{ minHeight: 46, padding: '0 16px', borderRadius: 12, border: `1px solid #E6DFD4`, background: color.paper.card, color: color.ink.muted, cursor: 'pointer', fontFamily: font.sans, fontSize: 13.5, fontWeight: 700 }}>Emin değilim</button>
                      <span style={{ flex: 1 }} />
                      <button type="button" onClick={() => void gonder(secilen)} disabled={secilen === null || gonderiliyor}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: 8, minHeight: 46, padding: '0 26px', borderRadius: 12, border: 'none', background: color.dawn.coralCtaBg, color: '#fff', cursor: secilen === null ? 'default' : 'pointer', fontFamily: font.sans, fontSize: 14.5, fontWeight: 700, opacity: secilen === null ? 0.45 : 1, pointerEvents: secilen === null ? 'none' : 'auto' }}>Cevapla<Ok /></button>
                    </div>
                  </div>
                ) : (
                  /* Bitiş kartı */
                  <div style={{ ...kart, padding: '28px 30px', textAlign: 'center' }} aria-live="polite">
                    <div aria-hidden style={{ width: 60, height: 60, margin: '0 auto 16px', borderRadius: 18, background: 'linear-gradient(135deg,#1FB683,#34D399)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 10px 24px -8px rgba(16,185,129,0.5)' }}><Tik /></div>
                    <h2 style={{ margin: 0, fontSize: 23, fontWeight: 800 }}>Yerleştirme tamamlandı</h2>
                    <p style={{ margin: '10px 0 0', fontSize: 14.5, color: color.ink.muted }}><span style={numText}>{ug.length}</span> maddede seviyeni ölçtük — tahmin yeterince kararlı (SE {trOndalik(motor.se)}).</p>
                    <div style={{ marginTop: 18, display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
                      {[
                        { et: 'Yetenek (θ)', v: trOndalik(motor.theta), c: color.dawn.coralTextOnLight },
                        { et: 'Seviye', v: SEVIYE[motor.seviye].ad, c: color.ink.primary },
                        { et: 'Net potansiyeli', v: '~' + motor.netTahmini, c: '#1FB683' },
                      ].map((s) => (
                        <div key={s.et} style={{ background: color.paper.subtle2, borderRadius: 14, padding: 16 }}>
                          <div style={{ fontSize: 11, fontWeight: 700, color: color.ink.muted }}>{s.et}</div>
                          <div style={{ ...numText, fontSize: 22, fontWeight: 800, color: s.c, marginTop: 4 }}>{s.v}</div>
                        </div>
                      ))}
                    </div>
                    <div style={{ marginTop: 18, display: 'flex', gap: 11, justifyContent: 'center', flexWrap: 'wrap' }}>
                      <button type="button" onClick={() => undefined} style={{ minHeight: 48, padding: '0 24px', borderRadius: 13, border: 'none', background: color.dawn.coralCtaBg, color: '#fff', cursor: 'pointer', fontFamily: font.sans, fontSize: 14.5, fontWeight: 700 }}>Panele git →</button>
                      <button type="button" onClick={() => undefined} style={{ minHeight: 48, padding: '0 22px', borderRadius: 13, border: '1px solid #E6DFD4', background: color.paper.card, color: color.ink.secondary, cursor: 'pointer', fontFamily: font.sans, fontSize: 14, fontWeight: 700 }}>Öğrenme yolunu aç</button>
                    </div>
                  </div>
                )}

                {/* Uygulanan maddeler şeridi */}
                <div style={{ ...kart, borderRadius: 16, padding: '16px 18px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginBottom: 10 }}>
                    <span style={{ fontSize: 12.5, fontWeight: 700, color: color.ink.secondary }}>Uygulanan maddeler — zorluk adaptasyonu</span>
                    <span style={{ ...numText, fontSize: 12, fontWeight: 700 }}><span style={{ color: '#047857' }}>{dogruSay} doğru</span> · <span style={{ color: color.dawn.coralTextOnLight }}>{yanlisSay} yanlış</span></span>
                  </div>
                  {ug.length === 0 ? (
                    <p style={{ margin: 0, fontSize: 11.5, color: '#B5AEA2' }}>İlk cevabınla dolmaya başlar…</p>
                  ) : (
                    <div aria-hidden style={{ display: 'flex', alignItems: 'flex-end', gap: 6, height: 46 }}>
                      {ug.map((u, i) => <div key={i} style={{ flex: 1, borderRadius: 4, background: u.ok ? '#1FB683' : '#E8836B', height: `${28 + ((u.b + 1.5) / 3.5) * 60}%` }} />)}
                    </div>
                  )}
                  <div style={{ display: 'flex', gap: 16, marginTop: 10, fontSize: 11.5, fontWeight: 600, color: color.ink.muted }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}><span aria-hidden style={{ width: 10, height: 10, borderRadius: 3, background: '#1FB683' }} />Doğru → zorluk arttı</span>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}><span aria-hidden style={{ width: 10, height: 10, borderRadius: 3, background: '#E8836B' }} />Yanlış → zorluk azaldı</span>
                  </div>
                </div>
              </div>

              {/* Motor paneli */}
              <aside aria-label="Motor paneli" style={{ position: dar ? 'static' : 'sticky', top: 86, display: 'grid', gap: 16 }}>
                {/* Blok 1 — θ */}
                <div style={kart}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginBottom: 8 }}>
                    <span style={{ fontSize: 12.5, fontWeight: 700, color: color.ink.muted }}>Yetenek tahmini (θ)</span>
                    <span style={{ fontSize: 11.5, fontWeight: 700, padding: '3px 9px', borderRadius: 999, color: SEVIYE[motor.seviye].fg, background: SEVIYE[motor.seviye].bg }}>{SEVIYE[motor.seviye].ad}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                    <span style={{ ...numText, fontSize: 42, fontWeight: 800, color: color.dawn.coralTextOnLight }}>{trOndalik(motor.theta)}</span>
                    <span style={{ ...numText, fontSize: 14, fontWeight: 600, color: color.ink.muted }}>± {trOndalik(motor.se)}</span>
                  </div>
                  <div style={{ ...numText, fontSize: 12.5, color: color.ink.muted, marginTop: 2 }}>≈ üst %{motor.topPct} · tahmini {motor.netTahmini} net (TYT Mat)</div>
                  <div aria-hidden style={{ position: 'relative', height: 10, borderRadius: 999, background: color.paper.border, marginTop: 14 }}>
                    <div style={{ position: 'absolute', top: 0, bottom: 0, left: `${bandLeft}%`, width: `${bandW}%`, background: 'rgba(255,111,92,0.2)', borderRadius: 4 }} />
                    <div style={{ position: 'absolute', top: -3, left: `calc(${markLeft}% - 8px)`, width: 16, height: 16, borderRadius: 999, background: color.dawn.coral, border: '3px solid #fff', boxShadow: `0 0 0 1px ${color.dawn.coral}` }} />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6, fontSize: 10.5, fontWeight: 600, color: color.ink.muted }}><span>{'−'}3</span><span>Zayıf</span><span>Orta</span><span>Güçlü</span><span>+3</span></div>
                </div>
                {/* Blok 2 — Yakınsama */}
                <div style={kart}>
                  <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 4 }}>θ Yakınsaması</div>
                  <p style={{ margin: '0 0 8px', fontSize: 12, color: color.ink.muted, lineHeight: 1.5 }}>Tahmin her maddeyle kararlı hâle geliyor; güven aralığı daralıyor.</p>
                  <Yakinsama ug={ug} />
                </div>
                {/* Blok 3 — SE */}
                <div style={kart}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                    <span style={{ fontSize: 13, fontWeight: 700 }}>Standart hata (SE)</span>
                    <span style={{ ...numText, fontSize: 15, fontWeight: 800, color: color.dawn.coralTextOnLight }}>{trOndalik(motor.se)}</span>
                  </div>
                  <div aria-hidden style={{ position: 'relative', height: 8, borderRadius: 999, background: color.paper.border, marginTop: 10 }}>
                    <div style={{ height: '100%', borderRadius: 999, width: `${seProgress}%`, background: `linear-gradient(90deg,${color.dawn.coral},#FF9E7D)` }} />
                    <div style={{ position: 'absolute', top: -1, left: '97%', width: 2, height: 10, background: '#1FB683' }} />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, marginTop: 8, fontSize: 11.5 }}>
                    <span style={{ color: color.ink.muted }}>Hedef: SE &lt; 0,30 (yeşil çizgi)</span>
                    <span style={{ ...numText, fontWeight: 800, color: '#047857' }}>{bitti ? 'tamamlandı' : `~${kalan} soru kaldı`}</span>
                  </div>
                  <div style={{ height: 1, background: color.paper.border, margin: '15px 0' }} />
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, textAlign: 'center' }}>
                    {[
                      { v: `%${Math.round((1 - motor.se * motor.se) * 100)}`, e: 'Güvenilirlik' },
                      { v: String(ug.length), e: 'Madde' },
                      { v: `%${ug.length ? Math.round((dogruSay / ug.length) * 100) : 0}`, e: 'Doğruluk' },
                    ].map((t) => (
                      <div key={t.e}><div style={{ ...numText, fontSize: 18, fontWeight: 800 }}>{t.v}</div><div style={{ fontSize: 11.5, fontWeight: 600, color: color.ink.muted }}>{t.e}</div></div>
                    ))}
                  </div>
                </div>
              </aside>
            </>
          )}
        </div>
      </div>
    </KiroThemeProvider>
  );
}

export default AdaptifTestPage;
