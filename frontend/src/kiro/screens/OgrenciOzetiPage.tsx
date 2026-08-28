// ============================================================================
// KIRO2 — Öğrenci Özeti (SPRINT11 · KIRO2 Ogretmen Ogrenci Ozet.dc.html)
// Tema = PAPER (analitik/panel yüzeyi; rol=öğretmen, TEK öğrenci SALT-OKUR).
// Rota: /ogretmen/ogrenci/:id — öğretmen yalnız kendi sınıfındaki öğrenciyi görür.
//
// SUNUCU-OTORİTE: net/hâkimiyet/genelHâkimiyet/haftalık/risk getOgrenciOzeti'nden
// gelir; ekran net/hâkimiyet/risk/skor HESAPLAMAZ, ortalamaz. DC'nin "zayıf konular",
// "atanan ödevler", "son deneme (AYT net)", "haftalık toplam dk", "trend" alanları
// OgrenciOzeti sözleşmesinde YOK → server-otorite gereği fabrike EDİLMEZ (bkz. onay/kanon).
//
// Tek yazma-eylemi: "Bu öğrenciye ödev ata" → Ödev Atama (bu sprintte YOK → link).
// KOPYA: DC birebir. Sağlıklı-durum metni + hata metni inferred → ONAY BEKLER.
// ============================================================================
import * as React from 'react';

import { getOgrenciOzeti } from '../api/api-client';
import { color, font } from '../tokens';
import type { OgrenciOzeti } from '../types';
import { KiroThemeProvider, numText } from '../ui/theme';
import { ErrorState } from '../ui/ErrorState';
import { ProgressBar } from '../ui/ProgressBar';
import { Skeleton } from '../ui/Skeleton';
import { WeeklyActivityBars } from '../ui/WeeklyActivityBars';
import { SideNav } from '../ui/SideNav';
import '../tokens/tokens.css';

// Ders adı → açık-panel ders rengi (subject.light). Görünen ad eşlemesi — türetme değil.
const DERS_RENK: Record<string, string> = {
  Matematik: color.subject.light.mat,
  Fizik: color.subject.light.fiz,
  Kimya: color.subject.light.kim,
  Biyoloji: color.subject.light.biy,
  Türkçe: color.subject.light.tur,
};
const dersRengi = (ad: string): string => DERS_RENK[ad] ?? color.ink.muted;

const fmtNet = (n: number): string => new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 2 }).format(n);
const trTR = (n: number): string => new Intl.NumberFormat('tr-TR').format(n);

// SideNav ≤1023px'te 64px ikon rayına çöker (BREAKPOINT_SPEC §3) — jsdom matchMedia'sız guard'lı.
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

const S = { fill: 'none' as const, stroke: 'currentColor', strokeWidth: 2, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };
const Ikon = {
  geri: <svg width="15" height="15" viewBox="0 0 24 24" {...S} strokeWidth={2.2} aria-hidden><polyline points="15 18 9 12 15 6" /></svg>,
  goz: <svg width="12" height="12" viewBox="0 0 24 24" {...S} aria-hidden><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" /></svg>,
  arti: <svg width="16" height="16" viewBox="0 0 24 24" {...S} aria-hidden><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>,
  uyari: <svg width="17" height="17" viewBox="0 0 24 24" {...S} style={{ flexShrink: 0, marginTop: 1 }} aria-hidden><circle cx="12" cy="12" r="9" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg>,
  onay: <svg width="17" height="17" viewBox="0 0 24 24" {...S} strokeWidth={2.2} style={{ flexShrink: 0 }} aria-hidden><polyline points="20 6 9 17 4 12" /></svg>,
  kilit: <svg width="15" height="15" viewBox="0 0 24 24" {...S} aria-hidden><rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>,
  onayKucuk: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color.semantic.success} strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, marginTop: 2 }} aria-hidden><polyline points="20 6 9 17 4 12" /></svg>,
};

const kartStil: React.CSSProperties = {
  boxSizing: 'border-box', background: color.paper.card, border: `1px solid ${color.paper.border}`,
  borderRadius: 18, padding: 22,
};
const kpiKartStil: React.CSSProperties = {
  boxSizing: 'border-box', background: color.paper.card, border: `1px solid ${color.paper.border}`,
  borderRadius: 16, padding: 18,
};

function KpiKart({ etiket, deger, birim, tone }: { etiket: string; deger: string; birim?: string; tone?: string }) {
  return (
    <div style={kpiKartStil}>
      <div style={{ fontFamily: font.sans, fontSize: 12.5, fontWeight: 600, color: color.ink.muted, marginBottom: 8 }}>{etiket}</div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
        <span style={{ ...numText, fontSize: 28, fontWeight: 800, lineHeight: 1, color: tone ?? color.ink.primary }}>{deger}</span>
        {birim ? <span style={{ fontFamily: font.sans, fontSize: 14, fontWeight: 700, color: color.ink.muted }}>{birim}</span> : null}
      </div>
    </div>
  );
}

function DersSatiri({ ad, pct }: { ad: string; pct: number }) {
  const c = dersRengi(ad);
  return (
    <div style={{ boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 6 }}>
        <span aria-hidden style={{ width: 9, height: 9, borderRadius: 3, background: c, marginRight: 8, flexShrink: 0 }} />
        <span style={{ fontSize: 13, fontWeight: 700 }}>{ad}</span>
        <span style={{ ...numText, marginLeft: 'auto', fontSize: 12.5, fontWeight: 800, color: color.ink.secondary }}>%{pct}</span>
      </div>
      <ProgressBar pct={pct} color={c} height={7} ariaLabel={`${ad} hâkimiyeti yüzde ${pct}`} />
    </div>
  );
}

export interface OgrenciOzetiPageProps {
  /** Rota parametresi (/ogretmen/ogrenci/:id) — port için prop; router bunu geçer. */
  ogrenciId?: string;
}

export function OgrenciOzetiPage({ ogrenciId = 'o-ha' }: OgrenciOzetiPageProps = {}): React.ReactElement {
  const dar = useMedia('(max-width: 1023px)');
  const ikiSut = useMedia('(max-width: 900px)');
  const kpiIki = useMedia('(max-width: 760px)');
  const kpiBir = useMedia('(max-width: 440px)');
  const kpiCols = kpiBir ? '1fr' : kpiIki ? 'repeat(2, minmax(0,1fr))' : 'repeat(4, minmax(0,1fr))';
  const ikiSutCols = ikiSut ? '1fr' : 'minmax(0,1.7fr) minmax(0,1fr)';

  const [ozeti, setOzeti] = React.useState<OgrenciOzeti | null>(null);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);

  React.useEffect(() => {
    let alive = true;
    setOzeti(null);
    setHata(false);
    getOgrenciOzeti(ogrenciId)
      .then((o) => {
        if (alive) setOzeti(o);
      })
      .catch(() => {
        if (alive) setHata(true);
      });
    return () => {
      alive = false;
    };
  }, [ogrenciId, yeniden]);

  const dikkat = ozeti?.durum === 'dikkat';
  const avatarBg = dikkat ? color.semantic.riskTextOnLight : color.dawn.coralCtaBg;

  return (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={{ minHeight: '100vh', background: color.paper.bg, display: 'flex', fontFamily: font.sans, color: color.ink.primary }}>
        <SideNav role="ogretmen" activeId="students" collapsed={dar} userName="Öğretmen" userSub="Sınıf görünümü" showSettings />

        <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
          {/* Topbar */}
          <header
            style={{
              boxSizing: 'border-box', position: 'sticky', top: 0, zIndex: 5, minHeight: 66,
              display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 12, padding: '9px 24px',
              background: 'rgba(250,247,242,0.86)', backdropFilter: 'blur(8px)', borderBottom: `1px solid ${color.paper.border}`,
            }}
          >
            <a
              href="/ogretmen"
              aria-label="Öğretmen Paneli'ne dön"
              style={{ display: 'inline-flex', alignItems: 'center', gap: 7, minHeight: 44, padding: '0 4px', fontSize: 13, fontWeight: 700, color: color.ink.muted, textDecoration: 'none' }}
            >
              {Ikon.geri}
              Panel
            </a>
            <span aria-hidden style={{ width: 1, height: 22, background: color.paper.borderStrong }} />
            <h1 style={{ margin: 0, fontSize: 18, fontWeight: 800, letterSpacing: '-0.02em' }}>Öğrenci özeti</h1>
            {ozeti && (
              <span style={{ display: 'inline-flex', alignItems: 'center', height: 28, padding: '0 12px', borderRadius: 999, background: color.paper.card, border: `1px solid ${color.paper.border}`, color: color.ink.secondary, fontSize: 12, fontWeight: 700 }}>
                {ozeti.sinif}
              </span>
            )}
            <span style={{ flex: 1 }} />
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, height: 28, padding: '0 12px', borderRadius: 999, background: color.paper.subtle, color: color.ink.muted, fontSize: 11.5, fontWeight: 700 }}>
              {Ikon.goz}
              Salt-okur görünüm
            </span>
          </header>

          <main
            style={{
              boxSizing: 'border-box', width: '100%', maxWidth: 1220, padding: '24px 24px 46px',
              display: 'flex', flexDirection: 'column', gap: 20,
            }}
          >
            {hata ? (
              <ErrorState
                serifTitle="Öğrenci özeti şu an gelmedi."
                body="Sorun sende değil — bağlantı bir soluklandı, öğrencinin verisi güvende. Birazdan yeniden dene."
                onRetry={() => setYeniden((n) => n + 1)}
              />
            ) : ozeti === null ? (
              <div aria-busy="true" aria-label="Öğrenci özeti yükleniyor" style={{ display: 'grid', gap: 20 }}>
                <div style={kartStil}><Skeleton shape="card" delayMs={0} slowAfterMs={null} /></div>
                <div style={{ display: 'grid', gridTemplateColumns: kpiCols, gap: 16 }}>
                  {[0, 1, 2, 3].map((i) => <div key={i} style={kpiKartStil}><Skeleton shape="row" delayMs={0} /></div>)}
                </div>
              </div>
            ) : (
              <>
                {/* Kimlik bandı — avatar + ad + sınıf/son aktivite + tek yazma-eylemi CTA */}
                <section style={{ ...kartStil, padding: '20px 22px', display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
                  <div aria-hidden style={{ width: 52, height: 52, flexShrink: 0, borderRadius: 14, background: avatarBg, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 17, fontWeight: 800 }}>
                    {ozeti.ini}
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800, letterSpacing: '-0.01em' }}>{ozeti.ad}</h2>
                    <div style={{ fontSize: 12.5, fontWeight: 600, color: color.ink.muted }}>{ozeti.sinif} · Son aktivite: {ozeti.sonAktivite}</div>
                  </div>
                  <span style={{ flex: 1 }} />
                  <a
                    href={`/ogretmen/odev/yeni?ogrenci=${encodeURIComponent(ozeti.id)}`}
                    style={{ boxSizing: 'border-box', display: 'inline-flex', alignItems: 'center', gap: 8, minHeight: 44, padding: '0 16px', borderRadius: 11, background: color.dawn.coralCtaBg, color: '#fff', fontSize: 13.5, fontWeight: 700, textDecoration: 'none' }}
                  >
                    {Ikon.arti}
                    Bu öğrenciye ödev ata
                  </a>
                </section>

                {/* Durum bandı — dikkat (amber riskMetni) ya da sağlıklı ritim (yön: renk-dışı metin) */}
                {dikkat ? (
                  <section style={{ boxSizing: 'border-box', display: 'flex', alignItems: 'flex-start', gap: 12, padding: '14px 16px', background: color.semantic.riskBgSoft, border: `1px solid ${color.semantic.riskBorderSoft}`, borderRadius: 14 }}>
                    <span style={{ color: color.semantic.riskTextOnLight, display: 'inline-flex' }}>{Ikon.uyari}</span>
                    <div>
                      <div style={{ fontSize: 13.5, fontWeight: 700, color: color.semantic.riskTextOnLight }}>{ozeti.riskMetni ?? 'Dikkat gerektiren bir sinyal var.'}</div>
                      <div style={{ fontSize: 12.5, fontWeight: 600, color: color.semantic.riskTextOnLight, opacity: 0.85, marginTop: 2 }}>
                        Bu sinyal yalnız size görünür — öğrenciye bayrak gösterilmez. Nazik bir başlangıç: küçük, kişiye özel bir set atamak.
                      </div>
                    </div>
                  </section>
                ) : (
                  <section style={{ boxSizing: 'border-box', display: 'flex', alignItems: 'center', gap: 12, padding: '14px 16px', background: color.semantic.successBgSoft, border: `1px solid ${color.semantic.successBorderSoft}`, borderRadius: 14 }}>
                    <span style={{ color: color.semantic.successTextOnLight, display: 'inline-flex' }}>{Ikon.onay}</span>
                    <div style={{ fontSize: 13.5, fontWeight: 700, color: color.semantic.successTextOnLight }}>
                      Ritmi sağlıklı — <span style={numText}>{ozeti.kpi.seri}</span> günlük seri sürüyor.
                    </div>
                  </section>
                )}

                {/* KPI — net · hâkimiyet · seri · çözülen (sunucudan; ekran hesaplamaz) */}
                <section style={{ display: 'grid', gridTemplateColumns: kpiCols, gap: 16 }}>
                  <KpiKart etiket="Son deneme TYT net" deger={fmtNet(ozeti.kpi.net)} tone={color.dawn.coralTextOnLight} />
                  <KpiKart etiket="Genel hâkimiyet" deger={String(ozeti.kpi.hakimiyet)} birim="%" />
                  <KpiKart etiket="Çalışma serisi" deger={String(ozeti.kpi.seri)} birim="gün" />
                  <KpiKart etiket="Çözülen soru" deger={trTR(ozeti.kpi.cozulen)} />
                </section>

                {/* İki sütun */}
                <section style={{ display: 'grid', gridTemplateColumns: ikiSutCols, gap: 20, alignItems: 'start' }}>
                  {/* Sol — ders hâkimiyeti (konu-düzeyi; tekil cevaplar inmez) */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 }}>
                    <div style={kartStil}>
                      <h3 style={{ margin: '0 0 4px', fontSize: 16.5, fontWeight: 700 }}>Ders hâkimiyeti</h3>
                      <p style={{ margin: '0 0 16px', fontSize: 12.5, fontWeight: 600, color: color.ink.muted }}>
                        Konu-düzeyi birleşik kestirim — tekil cevaplar bu görünüme inmez.
                      </p>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 13 }}>
                        {ozeti.dersHakimiyet.map((d) => <DersSatiri key={d.ders} ad={d.ders} pct={d.hakimiyet} />)}
                      </div>
                    </div>
                  </div>

                  {/* Sağ ray — haftalık aktivite + gizlilik */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 }}>
                    <div style={{ ...kartStil, padding: 20 }}>
                      <h3 style={{ margin: '0 0 14px', fontSize: 15.5, fontWeight: 700 }}>Haftalık aktivite</h3>
                      <WeeklyActivityBars gunler={ozeti.haftalik} ariaLabel="Haftalık aktivite" height={86} />
                    </div>

                    <div style={{ boxSizing: 'border-box', background: color.paper.subtle, border: `1px solid ${color.paper.borderFaint}`, borderRadius: 18, padding: 20 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                        <span style={{ color: color.ink.muted, display: 'inline-flex' }}>{Ikon.kilit}</span>
                        <h3 style={{ margin: 0, fontSize: 14, fontWeight: 700 }}>Öğrenci gizliliği</h3>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
                        {[
                          'Sohbet içerikleri ve duygu verisi bu görünüme hiçbir zaman inmez.',
                          'Tekil cevaplar görünmez — yalnız konu-düzeyi hâkimiyet.',
                          'Risk sinyalleri yalnız yetişkine gösterilir; öğrenciye bayrak yok.',
                        ].map((t) => (
                          <div key={t} style={{ display: 'flex', gap: 9, fontSize: 12.5, fontWeight: 600, color: color.ink.secondary, lineHeight: 1.55 }}>
                            {Ikon.onayKucuk}
                            <span>{t}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </section>

                {/* Net = yalnız yön; sıralama hiçbir yüzeyde yayınlanmaz (kaygı-duyarlı kanon) */}
                <p style={{ margin: 0, fontSize: 11.5, fontWeight: 600, color: color.ink.muted }}>
                  Net, yalnız yön göstergesidir — sınıf içi sıralama hiçbir yüzeyde yayınlanmaz.
                </p>
              </>
            )}
          </main>
        </div>
      </div>
    </KiroThemeProvider>
  );
}

export default OgrenciOzetiPage;
