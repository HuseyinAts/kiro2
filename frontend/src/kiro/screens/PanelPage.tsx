// ============================================================================
// KIRO2 — Öğrenci Paneli (SPRINT2 · KIRO2 Ogrenci Paneli.dc.html)
// Tema = PAPER (çalışma yüzeyi). SideNav(active=panel) + topbar + 7 içerik bloğu.
// Kopya SPRINT2_SPEC §D'den; sayılar data-bound (getMe/getSubjects/getLastExam) veya §D-mock.
// "Seriyi koru" (TALIMAT v2 kararı — anglicism DEĞİL): seri dili "seri/gün".
// ============================================================================
import * as React from 'react';

import { configureKiroApi, getMe, getSubjects, getLastExam } from '../api/api-client';
import type { MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';
import { color, font } from '../tokens';
import type { LastExam, Persona, Subject, SubjectKey } from '../types';
import { KiroThemeProvider, numText } from '../ui/theme';
import { Button } from '../ui/Button';
import { ErrorState } from '../ui/ErrorState';
import { MasteryBadge } from '../ui/MasteryBadge';
import { ProgressBar } from '../ui/ProgressBar';
import { ProgressRing } from '../ui/ProgressRing';
import { Skeleton } from '../ui/Skeleton';
import { StatBlock } from '../ui/StatBlock';
import { SideNav } from '../ui/SideNav';
import '../tokens/tokens.css';

configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });

const dersRenk = color.subject.light;
const trTR = (n: number) => new Intl.NumberFormat('tr-TR').format(n);
const TREND: Record<SubjectKey, 'up' | 'stable' | 'down'> = { mat: 'up', tur: 'up', biy: 'stable', fiz: 'stable', kim: 'down' };

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

const Ikon = {
  alev: (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M12 2c1.2 3 4 4.2 4 7.8A4 4 0 0 1 8 10c0-1.4.5-2.4 1-3 .2 1 .9 1.6 1.6 1.6C9.6 6.4 10.8 4.2 12 2Z" /></svg>
  ),
  ayar: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden><circle cx="12" cy="12" r="3.2" /><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M19.1 4.9 17 7M7 17l-2.1 2.1" /></svg>
  ),
  bildirim: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0" /></svg>
  ),
};

function Pil({ children, bg, fg, border }: { children: React.ReactNode; bg: string; fg: string; border?: string }) {
  return <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: bg, color: fg, border: border ? `1px solid ${border}` : 'none', borderRadius: 999, padding: '6px 11px', fontSize: 12.5, fontWeight: 700 }}>{children}</span>;
}
function IkonBtn({ label, children, nokta }: { label: string; children: React.ReactNode; nokta?: boolean }) {
  return (
    <button type="button" aria-label={label} style={{ position: 'relative', width: 44, height: 44, borderRadius: 12, border: `1px solid ${color.paper.border}`, background: color.paper.card, color: color.ink.secondary, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
      {children}
      {nokta && <span aria-hidden style={{ position: 'absolute', top: 9, right: 9, width: 7, height: 7, borderRadius: 999, background: '#E0593F' }} />}
    </button>
  );
}

function KartBaslik({ ust, alt }: { ust: string; alt?: string }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ fontSize: 15, fontWeight: 800 }}>{ust}</div>
      {alt && <div style={{ fontSize: 12, color: color.ink.muted, marginTop: 2 }}>{alt}</div>}
    </div>
  );
}
const kartStil: React.CSSProperties = { background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 18, padding: 20, boxShadow: '0 1px 2px rgba(16,24,40,0.04)' };

const KPI = [
  { value: '%72', label: 'Ortalama başarı', delta: '+4' },
  { value: '1.248', label: 'Çözülen soru', delta: '+186' },
  { value: '14', label: 'Tamamlanan sınav', delta: '+2' },
  { value: '47 sa', label: 'Çalışma süresi (bu ay)' },
];
const HAFTA = [
  { g: 'Pzt', v: 34 }, { g: 'Sal', v: 52 }, { g: 'Çar', v: 41 }, { g: 'Per', v: 63 },
  { g: 'Cum', v: 58 }, { g: 'Cmt', v: 72 }, { g: 'Paz', v: 48 },
];
const GOREVLER = [
  { ad: 'Bugünkü planı tamamla', xp: 40, ok: true },
  { ad: 'Seriyi koru', xp: 20, ok: true },
  { ad: 'Sabah tekrarını yap', xp: 30, ok: true },
  { ad: 'FSRS tekrarını bitir', xp: 50, ok: false },
  { ad: '1 deneme çöz', xp: 80, ok: false },
];

function DersSatiri({ s, kompakt }: { s: Subject; kompakt: boolean }) {
  const c = dersRenk[s.key];
  return (
    <li style={{ listStyle: 'none', display: 'flex', alignItems: 'center', gap: kompakt ? 6 : 12, padding: '9px 0', borderTop: `1px solid ${color.paper.borderFaint}` }}>
      <span aria-hidden style={{ width: 9, height: 9, borderRadius: 999, background: c, flexShrink: 0 }} />
      <span style={{ fontSize: 13.5, fontWeight: 700, minWidth: kompakt ? 52 : 78 }}>{s.ad}</span>
      {!kompakt && <span className="k-theta" style={{ ...numText, fontSize: 11, fontWeight: 700, color: color.ink.muted }}>θ {s.theta.toFixed(1)}</span>}
      <MasteryBadge pct={s.hakimiyet} trend={TREND[s.key]} />
      <div style={{ flex: 1, minWidth: kompakt ? 24 : 60 }}>
        <ProgressBar pct={s.hakimiyet} color={c} height={7} ariaLabel={`${s.ad} hâkimiyeti yüzde ${s.hakimiyet}`} />
      </div>
      {!kompakt && <span style={{ ...numText, fontSize: 13, fontWeight: 800, minWidth: 34, textAlign: 'right' }}>%{s.hakimiyet}</span>}
    </li>
  );
}

export function PanelPage(): React.ReactElement {
  const dar = useMedia('(max-width: 1023px)');
  const darIcerik = useMedia('(max-width: 1100px)');
  const kompakt = useMedia('(max-width: 560px)');
  const kpiSut = kompakt ? '1fr' : darIcerik ? 'repeat(2, 1fr)' : 'repeat(4, 1fr)';
  const [persona, setPersona] = React.useState<Persona | null>(null);
  const [dersler, setDersler] = React.useState<Subject[] | null>(null);
  const [sinav, setSinav] = React.useState<LastExam | null>(null);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);

  React.useEffect(() => {
    let alive = true;
    setDersler(null);
    setHata(false);
    Promise.all([getMe(), getSubjects(), getLastExam()])
      .then(([p, s, e]) => {
        if (!alive) return;
        setPersona(p);
        setDersler(s);
        setSinav(e);
      })
      .catch(() => {
        if (alive) setHata(true);
      });
    return () => {
      alive = false;
    };
  }, [yeniden]);

  const hedefPct = persona ? Math.min(100, Math.round((persona.bugunCozulenDk / Math.max(1, persona.gunlukHedefDk)) * 100)) : 0;
  const gunAdi = new Intl.DateTimeFormat('tr-TR', { weekday: 'long', day: 'numeric', month: 'long' }).format(new Date());
  const gunOnce = sinav ? Math.max(0, Math.round((Date.now() - new Date(sinav.tarih).getTime()) / 86400000)) : 0;
  const tamamGorev = GOREVLER.filter((g) => g.ok).length;

  return (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={{ minHeight: '100vh', background: color.paper.bg, display: 'flex', fontFamily: font.sans, color: color.ink.primary }}>
        <SideNav role="ogrenci" activeId="panel" collapsed={dar} userName={persona?.ad ?? 'Öğrenci'} userSub={persona?.sinif ?? ''} onAssistant={() => undefined} />

        <main style={{ flex: 1, minWidth: 0 }}>
          {/* Topbar */}
          <header style={{ position: 'sticky', top: 0, zIndex: 2, minHeight: 66, height: kompakt ? 'auto' : 66, display: 'flex', alignItems: 'center', flexWrap: kompakt ? 'wrap' : 'nowrap', gap: 12, padding: kompakt ? '10px 16px' : '0 24px', background: 'rgba(250,247,242,0.86)', backdropFilter: 'blur(8px)', borderBottom: `1px solid ${color.paper.border}` }}>
            <div className="k-search" style={{ flex: 1, minWidth: 0, maxWidth: 420, display: 'flex', alignItems: 'center', gap: 8, height: 44, padding: '0 12px', borderRadius: 12, background: color.paper.card, border: `1px solid ${color.paper.border}` }}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke={color.ink.muted} strokeWidth="2" strokeLinecap="round" aria-hidden><circle cx="11" cy="11" r="7" /><path d="m21 21-3.6-3.6" /></svg>
              <input aria-label="Ara" placeholder="Konu, soru veya deneme ara…" style={{ flex: 1, minWidth: 0, alignSelf: 'stretch', border: 'none', outline: 'none', background: 'transparent', fontFamily: font.sans, fontSize: 13, color: color.ink.primary }} />
              {!kompakt && <span aria-hidden style={{ ...numText, fontSize: 10.5, fontWeight: 700, color: color.ink.muted, border: `1px solid ${color.paper.border}`, borderRadius: 6, padding: '1px 5px' }}>⌘K</span>}
            </div>
            <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 10 }}>
              <Pil bg={color.semantic.riskBgSoft} fg={color.semantic.riskTextOnLight} border={color.semantic.riskBorderSoft}>{Ikon.alev}<span style={numText}>{persona?.seri ?? 0}</span>{!kompakt && ' gün'}</Pil>
              <Pil bg={color.paper.card} fg={color.ink.secondary} border={color.paper.border}>
                <span aria-hidden style={{ ...numText, width: 20, height: 20, borderRadius: 6, background: color.dawn.coralCtaBg, color: '#fff', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 800 }}>{persona?.seviye ?? 0}</span>
                <span style={numText}>{trTR(persona?.xp ?? 0)}</span>{!kompakt && ' XP'}
              </Pil>
              <IkonBtn label="Ayarlar">{Ikon.ayar}</IkonBtn>
              <IkonBtn label="Bildirimler" nokta>{Ikon.bildirim}</IkonBtn>
            </div>
          </header>

          <div style={{ maxWidth: 1280, margin: '0 auto', padding: kompakt ? '20px 12px 40px' : '24px 24px 48px' }}>
            {hata ? (
              <ErrorState serifTitle="Panelin şu an gelmedi." body="Sorun sende değil — bağlantı bir soluklandı, çalışman güvende. Birazdan yeniden dene." onRetry={() => setYeniden((n) => n + 1)} />
            ) : dersler === null || persona === null ? (
              <div aria-busy="true" aria-label="Panel yükleniyor" style={{ display: 'grid', gap: 16 }}>
                <div style={kartStil}><Skeleton shape="card" delayMs={0} slowAfterMs={null} /></div>
                <div style={{ display: 'grid', gridTemplateColumns: kpiSut, gap: 12 }}>
                  {[0, 1, 2, 3].map((i) => <div key={i} style={kartStil}><Skeleton shape="row" delayMs={0} /></div>)}
                </div>
              </div>
            ) : (
              <>
                {/* 1 · Selamlama */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: 12, marginBottom: 20 }}>
                  <div>
                    <h1 style={{ fontSize: 29, fontWeight: 800, margin: 0 }}>Merhaba, {persona.adKisa}</h1>
                    <p style={{ marginTop: 6, fontSize: 14, color: color.ink.secondary }}>
                      Bugün <strong>2 görevin</strong> kaldı — serini <strong><span style={numText}>{persona.seri + 1}</span>. güne</strong> taşımana 1 çalışma kaldı.
                    </p>
                  </div>
                  <span style={{ fontSize: 13, color: color.ink.muted }}>{gunAdi}</span>
                </div>

                {/* 2 · Hero */}
                <div className="k-hero" style={{ display: 'grid', gridTemplateColumns: darIcerik ? '1fr' : '1fr 300px', gap: 16, marginBottom: 20 }}>
                  <div style={kartStil}>
                    <span style={{ display: 'inline-flex', fontSize: 11, fontWeight: 800, letterSpacing: '0.05em', textTransform: 'uppercase', color: '#fff', background: color.dawn.coralCtaBg, borderRadius: 999, padding: '4px 11px' }}>Bugünün planı</span>
                    <div style={{ marginTop: 12, fontSize: 18, fontWeight: 800 }}>Türev soru paketi</div>
                    <div style={{ marginTop: 4, fontSize: 13, color: color.ink.muted }}>Matematik · <span style={numText}>5</span> soru · ~<span style={numText}>10</span> dk · zayıf konun olarak işaretlendi</div>
                    <div style={{ marginTop: 14 }}><ProgressBar pct={60} color={dersRenk.mat} height={8} ariaLabel="Bugünün planı — 3/5 görev" /></div>
                    <div style={{ ...numText, marginTop: 6, fontSize: 12.5, fontWeight: 700, color: color.ink.secondary }}>3/5 görev</div>
                    <div style={{ marginTop: 16, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                      <Button variant="primary" onClick={() => undefined}>Çalışmaya devam et</Button>
                      <Button variant="ghost" onClick={() => undefined}>Deneme başlat</Button>
                    </div>
                  </div>
                  <div style={{ ...kartStil, background: color.paper.subtle, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
                    <ProgressRing pct={hedefPct} size={128} ringColor={color.dawn.coralCtaBg} sublabel="günlük hedef" />
                    <div style={{ ...numText, marginTop: 12, fontSize: 12.5, color: color.ink.muted }}>{persona.bugunCozulenDk} dk çalıştın · hedef {persona.gunlukHedefDk} dk</div>
                  </div>
                </div>

                {/* 3 · KPI */}
                <div className="k-kpi" style={{ display: 'grid', gridTemplateColumns: kpiSut, gap: 12, marginBottom: 20 }}>
                  {KPI.map((k) => (
                    <div key={k.label} style={kartStil}><StatBlock value={k.value} label={k.label} delta={k.delta} /></div>
                  ))}
                </div>

                <div className="k-twocol" style={{ display: 'grid', gridTemplateColumns: darIcerik ? '1fr' : '1fr 340px', gap: 16 }}>
                  <div style={{ display: 'grid', gap: 16 }}>
                    {/* 4 · Ders Hâkimiyeti */}
                    <div style={kartStil}>
                      <KartBaslik ust="Ders Bazında Hâkimiyet" alt="IRT yetenek (θ) tahminine göre · son 30 gün" />
                      <ul style={{ margin: 0, padding: 0 }}>{dersler.map((s) => <DersSatiri key={s.key} s={s} kompakt={kompakt} />)}</ul>
                    </div>
                    {/* 5 · Haftalık İlerleme */}
                    <div style={kartStil}>
                      <KartBaslik ust="Haftalık İlerleme" alt="net · bu hafta" />
                      <div style={{ ...numText, fontSize: 20, fontWeight: 800, color: '#17936B' }}>+8,4 net</div>
                      <div aria-hidden style={{ display: 'flex', alignItems: 'flex-end', gap: 8, height: 60, marginTop: 12 }}>
                        {HAFTA.map((d) => (
                          <div key={d.g} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                            <div style={{ width: '100%', height: `${d.v}%`, borderRadius: 5, background: `${color.dawn.coralCtaBg}22` }} />
                            <span style={{ fontSize: 10, color: color.ink.muted }}>{d.g}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'grid', gap: 16 }}>
                    {/* 6 · Günlük Görevler */}
                    <div style={kartStil}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                        <span style={{ fontSize: 15, fontWeight: 800 }}>Günlük Görevler</span>
                        <span style={{ ...numText, fontSize: 12, fontWeight: 700, color: color.ink.muted }}>{tamamGorev}/5</span>
                      </div>
                      <ul style={{ margin: 0, padding: 0, display: 'grid', gap: 8 }}>
                        {GOREVLER.map((g) => (
                          <li key={g.ad} style={{ listStyle: 'none', display: 'flex', alignItems: 'center', gap: 10, padding: '9px 11px', borderRadius: 11, background: g.ok ? color.paper.subtle2 : color.paper.card, border: g.ok ? 'none' : `1px solid ${color.paper.border}` }}>
                            <span aria-hidden style={{ width: 18, height: 18, borderRadius: 999, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: g.ok ? '#1FB683' : '#fff', border: g.ok ? 'none' : `1.5px solid ${color.paper.borderStrong}` }}>
                              {g.ok ? <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5" /></svg> : null}
                            </span>
                            <span style={{ flex: 1, fontSize: 13, fontWeight: 600, color: g.ok ? color.ink.muted : color.ink.primary, textDecoration: g.ok ? 'line-through' : 'none' }}>{g.ad}</span>
                            <span style={{ ...numText, fontSize: 12, fontWeight: 800, color: g.ok ? color.ink.faded : color.dawn.coralTextOnLight }}>+{g.xp}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    {/* 7 · Son Sınavlar */}
                    <div style={kartStil}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                        <span style={{ fontSize: 15, fontWeight: 800 }}>Son Sınavlar</span>
                        <button type="button" style={{ minHeight: 44, display: 'inline-flex', alignItems: 'center', padding: '0 4px', fontSize: 12.5, fontWeight: 700, color: color.dawn.coralTextOnLight, background: 'none', border: 'none', cursor: 'pointer', fontFamily: font.sans }}>Tümü →</button>
                      </div>
                      {sinav && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 11 }}>
                          <span aria-hidden style={{ width: 40, height: 40, flexShrink: 0, borderRadius: 11, background: 'rgba(59,130,246,0.12)', color: '#3B82F6', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 12 }}>TYT</span>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ fontSize: 13.5, fontWeight: 700 }}>{sinav.ad}</div>
                            <div style={{ ...numText, fontSize: 11.5, color: color.ink.muted }}>{gunOnce} gün önce · TYT {sinav.tytNet} · AYT {sinav.aytNet} net</div>
                          </div>
                          <span style={{ ...numText, fontSize: 12.5, fontWeight: 800, color: '#047857', background: '#ECFDF5', borderRadius: 999, padding: '4px 10px' }}>{sinav.tytNet}</span>
                        </div>
                      )}
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

export default PanelPage;
