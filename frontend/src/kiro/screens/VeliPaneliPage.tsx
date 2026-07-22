// ============================================================================
// KIRO2 — Veli Paneli (SPRINT11 · KIRO2 Veli Paneli.dc.html · Grup 9/7-A)
// Tema = PAPER (rol paneli, salt-okur analitik). SideNav(veli) + topbar
// (ChildSwitcher tablist + bildirim zili) + 4 içerik bloğu + Premium ROI.
// DİL: resmi SİZ (veli/veliye) — öğrenci "sen" diline ASLA kayma.
// GÖRÜNÜRLÜK: çocuk verisi SALT-OKUR, YALNIZ çalışma metrikleri
//   (KPI/net/hâkimiyet/haftalık dk/sınav/seri). Sohbet/AI/mood İÇERİĞİ gösterilmez.
// SUNUCU-OTORİTE: KPI/net/hâkimiyet/haftalık getVeliDashboard'tan — istemci
//   net/hâkimiyet/risk/skor HESAPLAMAZ (mock'ta bile kiro-data'dan okunur).
// ============================================================================
import * as React from 'react';

import { configureKiroApi, getVeliDashboard } from '../api/api-client';
import type { MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';
import { color, font } from '../tokens';
import type { DersIlerleme, SinavOzet, VeliDashboard, VeliUyari } from '../types';
import { KiroThemeProvider, numText } from '../ui/theme';
import { Button } from '../ui/Button';
import { EmptyState } from '../ui/EmptyState';
import { ErrorState } from '../ui/ErrorState';
import { ProgressBar } from '../ui/ProgressBar';
import { Skeleton } from '../ui/Skeleton';
import { SideNav } from '../ui/SideNav';
import { WeeklyActivityBars } from '../ui/WeeklyActivityBars';
import '../tokens/tokens.css';

configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });

// Ders görünen adı → açık panel paleti (DC panelColor ile birebir).
const DERS_RENK: Record<string, string> = {
  Matematik: color.subject.light.mat,
  Fizik: color.subject.light.fiz,
  Kimya: color.subject.light.kim,
  Biyoloji: color.subject.light.biy,
  Türkçe: color.subject.light.tur,
};

const trNum = (n: number): string => new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 2 }).format(n);
const artis = (n: number): string => (n >= 0 ? '+' : '−') + trNum(Math.abs(n));
const ilk = (ad: string): string => ad.trim().split(/\s+/)[0] ?? ad;

// TYT/AYT etiketi — Sınav Sonuç standardı (port kanon düzeltmesi; DC'deki farklı renk taşınmaz).
const tagStil = (tur: string): { bg: string; fg: string } =>
  tur.toUpperCase().includes('AYT') ? { bg: '#FBF0DE', fg: '#9A5D0D' } : { bg: '#EEF3F8', fg: '#5A6B82' };

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

// ---- Bespoke SVG seti (emoji YOK) ----
const Ikon = {
  bell: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" /></svg>
  ),
  flame: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#9A5D0D" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M12 2c1.2 3 4 4.2 4 7.8A4 4 0 0 1 8 10c0-1.4.5-2.4 1-3 .2 1 .9 1.6 1.6 1.6C9.6 6.4 10.8 4.2 12 2Z" /></svg>
  ),
  check: (stroke: string) => (
    <svg style={{ flexShrink: 0, marginTop: 1 }} width="17" height="17" viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><polyline points="20 6 9 17 4 12" /></svg>
  ),
  alert: (
    <svg style={{ flexShrink: 0, marginTop: 1 }} width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#B45309" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M10.3 3.6 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.6a2 2 0 0 0-3.4 0Z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12" y2="17" /></svg>
  ),
  badge: (
    <svg style={{ flexShrink: 0, marginTop: 1 }} width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#C2452B" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M7 4h10v5a5 5 0 0 1-10 0Z" /><path d="M12 14v3M9 21h6" /></svg>
  ),
  clock: (
    <svg style={{ flexShrink: 0, marginTop: 1 }} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#9A5D0D" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M12 2v6l4 2" /><circle cx="12" cy="14" r="8" /></svg>
  ),
  crown: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="#fff" aria-hidden><path d="M5 16 3 5l5.5 4L12 4l3.5 5L21 5l-2 11H5Zm0 3h14v2H5z" /></svg>
  ),
  chevron: (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="m9 6 6 6-6 6" /></svg>
  ),
  checkSmall: (
    <svg style={{ flexShrink: 0, marginTop: 2 }} width="15" height="15" viewBox="0 0 24 24" fill="none" stroke={color.dawn.peach} strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden><polyline points="20 6 9 17 4 12" /></svg>
  ),
};

const kart: React.CSSProperties = {
  boxSizing: 'border-box', background: color.paper.card, border: `1px solid ${color.paper.border}`,
  borderRadius: 18, padding: 22,
};
const headStil: React.CSSProperties = { margin: 0, fontFamily: font.sans, fontSize: 16.5, fontWeight: 700 };

// ---- Uyarı kartı (ton dengesi: 1 kutlama + 1 nazik + 1 sevinç; yığılmış kırmızı YOK) ----
const UYARI_STIL: Record<VeliUyari['tip'], { bg: string; border: string; fg: string; ikon: React.ReactNode }> = {
  success: { bg: color.semantic.successBgSoft, border: color.semantic.successBorderSoft, fg: '#1E5631', ikon: Ikon.check(color.semantic.successTextOnLight) },
  risk: { bg: '#FFFBEB', border: '#FDE9B8', fg: '#854D0E', ikon: Ikon.alert },
  sevinc: { bg: '#FFF3EE', border: '#F6D9CB', fg: color.dawn.coralTextOnLight, ikon: Ikon.badge },
};
function UyariKart({ u }: { u: VeliUyari }) {
  const s = UYARI_STIL[u.tip];
  return (
    <div style={{ boxSizing: 'border-box', display: 'flex', gap: 11, padding: '12px 13px', background: s.bg, border: `1px solid ${s.border}`, borderRadius: 12 }}>
      {s.ikon}
      <span style={{ fontSize: 13, color: s.fg, lineHeight: 1.5 }}>{u.metin}</span>
    </div>
  );
}

// ---- Son sınav satırı (veli salt-okur → Sınav Sonuç) ----
function SinavSatiri({ e }: { e: SinavOzet }) {
  const t = tagStil(e.tur);
  return (
    <a
      href="/sinav-sonuc"
      aria-label={`${e.ders} — ${trNum(e.net)} net · salt-okur görünüm`}
      style={{ boxSizing: 'border-box', display: 'flex', alignItems: 'center', gap: 12, minHeight: 44, padding: '9px 6px', borderRadius: 9, textDecoration: 'none', color: color.ink.primary }}
    >
      <span aria-hidden style={{ width: 34, height: 34, flexShrink: 0, borderRadius: 9, background: t.bg, color: t.fg, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10.5, fontWeight: 800 }}>{e.tur}</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{e.ders}</div>
        <div style={{ fontSize: 11.5, color: color.ink.muted }}>{e.tarih}</div>
      </div>
      <span style={{ ...numText, fontSize: 13, fontWeight: 800, color: color.semantic.successTextOnLight, background: color.semantic.successBgSoft, padding: '4px 10px', borderRadius: 8 }}>{trNum(e.net)}</span>
    </a>
  );
}

// ---- Ders bazında ilerleme satırı (açık palet) ----
function DersSatiri({ d }: { d: DersIlerleme }) {
  const c = DERS_RENK[d.ders] ?? color.ink.muted;
  return (
    <div style={{ boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 7 }}>
        <span aria-hidden style={{ width: 9, height: 9, borderRadius: 3, background: c, flexShrink: 0 }} />
        <span style={{ fontSize: 13.5, fontWeight: 700, color: color.ink.primary }}>{d.ders}</span>
        <span style={{ ...numText, marginLeft: 'auto', fontSize: 13, fontWeight: 800 }}>%{trNum(d.hakimiyet)}</span>
      </div>
      <ProgressBar pct={d.hakimiyet} color={c} height={8} ariaLabel={`${d.ders} hâkimiyeti yüzde ${d.hakimiyet}`} />
    </div>
  );
}

// ---- KPI kartı ----
function Kpi({ ust, deger, delta, tone }: { ust: string; deger: string; delta?: string; tone?: string }) {
  return (
    <div style={{ boxSizing: 'border-box', background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 16, padding: 18 }}>
      <div style={{ fontSize: 12.5, color: color.ink.muted, fontWeight: 600, marginBottom: 8 }}>{ust}</div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <span style={{ ...numText, fontSize: 28, fontWeight: 800, color: tone ?? color.ink.primary }}>{deger}</span>
        {delta ? <span style={{ fontSize: 12, fontWeight: 700, color: color.semantic.successTextOnLight }}>{delta}</span> : null}
      </div>
    </div>
  );
}

// ---- Premium ROI mini-stat ----
function RoiStat({ deger, alt, tone }: { deger: string; alt: React.ReactNode; tone: string }) {
  return (
    <div style={{ boxSizing: 'border-box', background: color.paper.card, border: '1px solid #F0E4DC', borderRadius: 14, padding: '14px 15px' }}>
      <div style={{ ...numText, fontSize: 24, fontWeight: 800, color: tone, lineHeight: 1 }}>{deger}</div>
      <div style={{ fontSize: 11.5, color: color.ink.muted, fontWeight: 600, marginTop: 6, lineHeight: 1.35 }}>{alt}</div>
    </div>
  );
}

export function VeliPaneliPage(): React.ReactElement {
  const dar = useMedia('(max-width: 1023px)');
  const kpi1 = useMedia('(max-width: 440px)');
  const kpi2 = useMedia('(max-width: 1023px)');
  const twoStack = useMedia('(max-width: 1023px)');
  const roiStack = useMedia('(max-width: 720px)');

  const [dash, setDash] = React.useState<VeliDashboard | null>(null);
  const [aktifId, setAktifId] = React.useState<string | undefined>(undefined);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);

  React.useEffect(() => {
    let alive = true;
    setHata(false);
    getVeliDashboard(aktifId)
      .then((d) => {
        if (alive) setDash(d);
      })
      .catch(() => {
        if (alive) setHata(true);
      });
    return () => {
      alive = false;
    };
  }, [aktifId, yeniden]);

  const kpiSut = kpi1 ? '1fr' : kpi2 ? 'repeat(2, minmax(0,1fr))' : 'repeat(4, minmax(0,1fr))';
  const cocuklar = dash?.cocuklar ?? [];
  const aktif = dash ? (cocuklar.find((c) => c.id === dash.aktifCocukId) ?? cocuklar[0]) : undefined;

  return (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={{ minHeight: '100vh', background: color.paper.bg, display: 'flex', fontFamily: font.sans, color: color.ink.primary }}>
        <SideNav role="veli" activeId="overview" collapsed={dar} showSettings userName={aktif ? 'Veli' : 'Veli'} userSub={aktif ? `${ilk(aktif.ad)} velisi` : ''} />

        <main style={{ flex: 1, minWidth: 0 }}>
          {/* Topbar: başlık + ChildSwitcher (tablist) + bildirim zili */}
          <header style={{ boxSizing: 'border-box', position: 'sticky', top: 0, zIndex: 5, minHeight: 66, display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 12, rowGap: 8, padding: '9px 24px', background: 'rgba(250,247,242,0.86)', backdropFilter: 'blur(8px)', borderBottom: `1px solid ${color.paper.border}` }}>
            <h1 style={{ margin: 0, fontFamily: font.sans, fontSize: 18, fontWeight: 800, letterSpacing: '-0.02em' }}>Genel Bakış</h1>
            <span aria-hidden style={{ width: 1, height: 22, background: '#E6DFD4', margin: '0 2px' }} />

            {cocuklar.length > 0 && (
              <div role="tablist" aria-label="Çocuk seçimi" style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                {cocuklar.map((c) => {
                  const secili = dash?.aktifCocukId === c.id;
                  return (
                    <button
                      key={c.id}
                      type="button"
                      role="tab"
                      aria-selected={secili}
                      onClick={() => setAktifId(c.id)}
                      style={{
                        display: 'inline-flex', alignItems: 'center', gap: 8, minHeight: 44, padding: '0 14px 0 6px',
                        borderRadius: 999, cursor: 'pointer', fontFamily: font.sans, fontSize: 13, fontWeight: secili ? 700 : 600,
                        background: secili ? color.dawn.coralCtaBg : color.paper.card,
                        color: secili ? '#fff' : color.ink.secondary,
                        border: secili ? 'none' : `1px solid ${color.paper.border}`,
                      }}
                    >
                      <span aria-hidden style={{ width: 24, height: 24, borderRadius: 999, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 800, background: secili ? 'rgba(255,255,255,0.25)' : '#F0EAE1', color: secili ? '#fff' : color.ink.muted }}>{c.ini}</span>
                      {ilk(c.ad)}
                    </button>
                  );
                })}
              </div>
            )}

            <div style={{ flex: 1 }} />
            <button type="button" aria-label="Bildirimler" style={{ position: 'relative', width: 44, height: 44, borderRadius: 10, background: color.paper.card, border: `1px solid ${color.paper.border}`, color: color.ink.muted, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {Ikon.bell}
              <span aria-hidden style={{ position: 'absolute', top: 10, right: 11, width: 7, height: 7, borderRadius: 999, background: '#E0593F', border: '1.5px solid #fff' }} />
            </button>
          </header>

          <div style={{ boxSizing: 'border-box', maxWidth: 1240, width: '100%', margin: '0 auto', padding: '24px 24px 46px' }}>
            {hata ? (
              <ErrorState
                serifTitle="Panel şu an yüklenemedi."
                body="Sorun sizde değil — bağlantı bir an duraksadı, çocuğunuzun ilerlemesi güvende. Birazdan yeniden deneyebilirsiniz."
                onRetry={() => setYeniden((n) => n + 1)}
                retryLabel="Yeniden dene"
              />
            ) : dash === null ? (
              <div aria-busy="true" aria-label="Panel yükleniyor" style={{ display: 'grid', gap: 20 }}>
                <div style={kart}><Skeleton shape="card" delayMs={0} slowAfterMs={null} /></div>
                <div style={{ display: 'grid', gridTemplateColumns: kpiSut, gap: 16 }}>
                  {[0, 1, 2, 3].map((i) => (
                    <div key={i} style={{ boxSizing: 'border-box', background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 16, padding: 18 }}><Skeleton shape="row" delayMs={0} /></div>
                  ))}
                </div>
              </div>
            ) : cocuklar.length === 0 || !aktif ? (
              <EmptyState
                serifTitle="Henüz bağlı bir çocuk hesabı yok."
                body="Çocuğunuzun hesabını bağladığınızda çalışma özetini burada takip edebilirsiniz. Bağlama, açık rıza akışıyla birkaç adımda tamamlanır."
                action={<Button variant="primary" onClick={() => undefined}>Çocuk hesabı bağla</Button>}
              />
            ) : (
              <div style={{ display: 'grid', gap: 20 }}>
                {/* 1 · Çocuk özet bandı */}
                <section style={{ boxSizing: 'border-box', background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 18, padding: '22px 24px', display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap' }}>
                  <div aria-hidden style={{ width: 60, height: 60, flexShrink: 0, borderRadius: 16, background: aktif.avatarGradient, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 22 }}>{aktif.ini}</div>
                  <div style={{ minWidth: 160 }}>
                    <div style={{ fontSize: 20, fontWeight: 800, letterSpacing: '-0.02em' }}>{aktif.ad}</div>
                    <div style={{ fontSize: 13, color: color.ink.muted, fontWeight: 500 }}>{aktif.sinif} · Hedef: {aktif.hedef}</div>
                  </div>
                  <div style={{ flex: 1 }} />
                  <div style={{ display: 'flex', gap: 26, flexWrap: 'wrap', alignItems: 'center' }}>
                    <div>
                      <div style={{ ...numText, fontSize: 22, fontWeight: 800 }}>{trNum(dash.haftaToplamSa)}<span style={{ fontSize: 14, color: color.ink.muted }}> sa</span></div>
                      <div style={{ fontSize: 12, color: color.ink.muted, fontWeight: 500 }}>Bu hafta çalışma</div>
                    </div>
                    <div>
                      <div style={{ ...numText, fontSize: 22, fontWeight: 800 }}>{dash.sonSinavlar[0] ? trNum(dash.sonSinavlar[0].net) : '—'}</div>
                      <div style={{ fontSize: 12, color: color.ink.muted, fontWeight: 500 }}>Son deneme neti</div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, minHeight: 44, padding: '0 14px', background: color.semantic.riskBgSoft, border: `1px solid ${color.semantic.riskBorderSoft}`, borderRadius: 12 }}>
                      {Ikon.flame}
                      <div>
                        <div style={{ ...numText, fontWeight: 800, fontSize: 16, color: color.semantic.riskTextOnLight, lineHeight: 1 }}>{trNum(dash.roi.seri)}</div>
                        <div style={{ fontSize: 10.5, color: color.semantic.riskTextOnLight, fontWeight: 700 }}>günlük seri</div>
                      </div>
                    </div>
                  </div>
                </section>

                {/* 2 · KPI ×4 */}
                <section style={{ display: 'grid', gridTemplateColumns: kpiSut, gap: 16 }}>
                  <Kpi ust="Çözülen soru" deger={trNum(dash.kpi.cozulenSoru)} delta={artis(dash.kpi.cozulenSoruDelta)} />
                  <Kpi ust="Çözülen deneme" deger={trNum(dash.kpi.cozulenDeneme)} delta={artis(dash.kpi.cozulenDenemeDelta)} />
                  <Kpi ust="Plan uyumu" deger={`%${trNum(dash.kpi.planUyumu)}`} tone={color.dawn.coralTextOnLight} />
                  <Kpi ust="Net değişimi" deger={artis(dash.kpi.netDegisimi)} delta="bu ay" />
                </section>

                {/* 3 · İki sütun */}
                <section style={{ display: 'grid', gridTemplateColumns: twoStack ? '1fr' : 'minmax(0,1.5fr) minmax(0,1fr)', gap: 20, alignItems: 'start' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 }}>
                    {/* Haftalık aktivite (paylaşımlı WeeklyActivityBars) */}
                    <div style={kart}>
                      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 16, gap: 12 }}>
                        <div>
                          <h2 style={headStil}>Haftalık Aktivite</h2>
                          <p style={{ margin: '4px 0 0', fontSize: 12.5, color: color.ink.muted }}>Günlük çalışma süresi (dk)</p>
                        </div>
                        <div style={{ textAlign: 'right', flexShrink: 0 }}>
                          <div style={{ ...numText, fontSize: 20, fontWeight: 800 }}>{trNum(dash.haftaToplamSa)} sa</div>
                          <div style={{ fontSize: 11.5, color: color.semantic.successTextOnLight, fontWeight: 700 }}>{dash.haftaTrend}</div>
                        </div>
                      </div>
                      <WeeklyActivityBars gunler={dash.haftalik} ariaLabel="Haftalık çalışma aktivitesi" height={96} />
                    </div>

                    {/* Ders bazında ilerleme */}
                    <div style={kart}>
                      <h2 style={{ ...headStil, marginBottom: 18 }}>Ders Bazında İlerleme</h2>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
                        {dash.dersIlerleme.map((d) => <DersSatiri key={d.ders} d={d} />)}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 }}>
                    {/* Son sınavlar (salt-okur) */}
                    <div style={kart}>
                      <h2 style={{ ...headStil, marginBottom: 14 }}>Son Sınavlar</h2>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {dash.sonSinavlar.map((e, i) => <SinavSatiri key={e.ders + '-' + i} e={e} />)}
                      </div>
                    </div>

                    {/* Uyarılar & öne çıkanlar (ton dengesi) */}
                    <div style={kart}>
                      <h2 style={{ ...headStil, marginBottom: 14 }}>Uyarılar &amp; Öne Çıkanlar</h2>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                        {dash.uyarilar.map((u, i) => <UyariKart key={u.tip + '-' + i} u={u} />)}
                      </div>
                    </div>
                  </div>
                </section>

                {/* 4 · Premium ROI / veli satın-alma yüzeyi */}
                <section style={{ boxSizing: 'border-box', background: 'linear-gradient(120deg,#FFFDFB 0%,#FFF3EE 100%)', border: '1px solid #F6D9CB', borderRadius: 20, padding: '24px 26px', display: 'grid', gridTemplateColumns: roiStack ? '1fr' : 'minmax(0,1.35fr) minmax(0,1fr)', gap: 26, alignItems: 'stretch' }}>
                  {/* Sol: kanıt bloğu */}
                  <div style={{ minWidth: 0 }}>
                    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 7, minHeight: 24, padding: '0 11px', borderRadius: 999, background: color.paper.card, border: '1px solid #F6D9CB', marginBottom: 13 }}>
                      <span aria-hidden style={{ width: 6, height: 6, borderRadius: 999, background: color.semantic.success }} />
                      <span style={{ fontSize: 11, fontWeight: 800, letterSpacing: '0.04em', color: color.semantic.successTextOnLight, textTransform: 'uppercase' }}>Yöntem işe yarıyor</span>
                    </div>
                    <h2 style={{ margin: '0 0 6px', fontFamily: font.sans, fontSize: 20, fontWeight: 800, letterSpacing: '-0.02em', lineHeight: 1.15 }}>{ilk(aktif.ad)} bu ay ölçülebilir ilerledi</h2>
                    <p style={{ margin: '0 0 18px', fontSize: 13.5, color: color.ink.muted, lineHeight: 1.55, maxWidth: 440 }}>
                      Bilim-temelli çekirdek (aralıklı tekrar + kişiye özel zorluk) ücretsiz katmanda bile sonuç veriyor. Rakamlar {`${ilk(aktif.ad)}'in`} gerçek verisinden.
                    </p>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0,1fr))', gap: 12, marginBottom: 18 }}>
                      <RoiStat deger={artis(dash.roi.netArtisi)} alt={<>net artışı<br />bu ay</>} tone={color.semantic.successTextOnLight} />
                      <RoiStat deger={`%${trNum(dash.roi.planUyum)}`} alt={<>plana<br />uyum</>} tone={color.dawn.coralTextOnLight} />
                      <RoiStat deger={trNum(dash.roi.seri)} alt={<>günlük<br />seri</>} tone={color.semantic.riskTextOnLight} />
                    </div>

                    <div style={{ display: 'flex', gap: 11, padding: '13px 15px', background: color.paper.card, border: '1px solid #F0E4DC', borderRadius: 13 }}>
                      {Ikon.clock}
                      <span style={{ fontSize: 12.5, color: color.ink.muted, lineHeight: 1.55 }}>
                        Günde ~{trNum(dash.roi.haftaOrtDk)} dk — dershaneye taşınma yükü olmadan, evde kendi hızında. <strong style={{ color: color.ink.primary }}>Tipik dershane maliyetinin çok altında.</strong>
                      </span>
                    </div>
                  </div>

                  {/* Sağ: KOYU izole promo kartı (tema DEĞİL) */}
                  <div style={{ boxSizing: 'border-box', background: 'linear-gradient(155deg,#2A2433,#3A3145)', borderRadius: 18, padding: '22px 22px 20px', display: 'flex', flexDirection: 'column', boxShadow: '0 18px 40px -22px rgba(42,36,51,0.6)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 14 }}>
                      <div aria-hidden style={{ width: 34, height: 34, flexShrink: 0, borderRadius: 10, background: color.dawn.coralCtaBg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{Ikon.crown}</div>
                      <div style={{ lineHeight: 1.1 }}>
                        <div style={{ fontSize: 10.5, fontWeight: 800, letterSpacing: '0.09em', color: color.dawn.peach, textTransform: 'uppercase' }}>Premium</div>
                        <div style={{ fontSize: 15.5, fontWeight: 800, color: '#fff' }}>Tam kapasiteyi aç</div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 9, marginBottom: 18 }}>
                      {dash.premium.maddeler.map((m) => (
                        <div key={m} style={{ display: 'flex', alignItems: 'flex-start', gap: 9, fontSize: 13, color: '#EDE7F0', fontWeight: 500 }}>
                          {Ikon.checkSmall}
                          <span>{m}</span>
                        </div>
                      ))}
                    </div>

                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 7, marginBottom: 14, flexWrap: 'wrap' }}>
                      <span style={{ ...numText, fontSize: 30, fontWeight: 800, color: '#fff', letterSpacing: '-0.02em' }}>₺{trNum(dash.premium.fiyatAy)}</span>
                      <span style={{ fontSize: 12.5, color: '#B8B0C4', fontWeight: 600 }}>/ay · yıllık</span>
                      <span style={{ ...numText, marginLeft: 'auto', fontSize: 11, fontWeight: 800, color: '#7BE0B0', background: 'rgba(123,224,176,0.14)', padding: '3px 9px', borderRadius: 999 }}>−%{trNum(dash.premium.indirimYuzde)}</span>
                    </div>

                    <a
                      href="/abonelik?rol=veli"
                      style={{ boxSizing: 'border-box', minHeight: 48, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, borderRadius: 12, background: color.dawn.coralCtaBg, color: '#fff', fontFamily: font.sans, fontSize: 14.5, fontWeight: 800, textDecoration: 'none', boxShadow: '0 10px 22px -10px rgba(194,69,43,0.7)' }}
                    >
                      7 gün ücretsiz deneyin
                      {Ikon.chevron}
                    </a>
                    <div style={{ marginTop: 10, textAlign: 'center', fontSize: 11, color: '#9990A8', lineHeight: 1.5 }}>İstediğiniz zaman iptal · deneme bitmeden hatırlatırız · sessiz ücret yok</div>
                  </div>
                </section>
              </div>
            )}
          </div>
        </main>
      </div>
    </KiroThemeProvider>
  );
}

export default VeliPaneliPage;
