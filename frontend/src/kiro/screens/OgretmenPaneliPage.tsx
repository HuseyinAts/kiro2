// ============================================================================
// KIRO2 — Öğretmen Paneli (SPRINT11 · KIRO2 Ogretmen Paneli.dc.html · Grup 9/A)
// Tema = PAPER (çalışma/analitik yüzeyi). SideNav(role=ogretmen) + topbar + içerik.
// SALT-OKUR: öğrenci net/hâkimiyet/risk metrikleri getOgretmenPanel'den gelir;
// ekran net/hâkimiyet/risk/skor HESAPLAMAZ (sunucu-otorite). Bu panelde veri-yazan
// etkileşim YOK — yazma (Ödev Atama / Sınıf Kurulumu) ayrı ekranlar (bu sprintte
// link/placeholder). Dil SİZ (öğretmene hitap); risk = amber (öğrenciye bayrak YOK).
//
// KOPYA: DC birebir (SIZ-dili). Sunucu yanıtında olmayan alanlar (DC'de authored:
//  KPI "Bu hafta çözülen soru", "2 gecikmiş" ayrı sayısı, öğrenci trend oku) porta
//  TAŞINMAZ — fabrikasyon yasak (sunucu-otorite). Empty/Error kopyası inferred → onay.
// ============================================================================
import * as React from 'react';

import { configureKiroApi, getOgretmenPanel } from '../api/api-client';
import type { MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';
import { color, font } from '../tokens';
import type { DikkatKarti, DersIlerleme, OgretmenOgrenci, OgretmenPanel } from '../types';
import { KiroThemeProvider, numText } from '../ui/theme';
import { ErrorState } from '../ui/ErrorState';
import { ProgressBar } from '../ui/ProgressBar';
import { Skeleton } from '../ui/Skeleton';
import { SideNav } from '../ui/SideNav';
import '../tokens/tokens.css';

configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });

// Rotalar (bu sprintte port EDİLMEYEN yazma-ekranları için placeholder link):
const ROTA = {
  yeniSinif: '/ogretmen/sinif/yeni',
  odevYeni: '/ogretmen/odev/yeni',
  ogrenciler: '/ogretmen/ogrenciler',
  ogrenci: (id: string) => '/ogretmen/ogrenci/' + id,
};

// DC fmtNet — virgüllü net (72.4 → "72,4", 94 → "94,0"). Sunucu sayısını yalnız BİÇİMLER.
function fmtNet(n: number): string {
  const r = Math.round(n * 100) / 100;
  const s = Number.isInteger(r) || Math.round(r * 10) / 10 === r ? r.toFixed(1) : r.toFixed(2);
  return s.replace('.', ',');
}
function fmtDelta(n: number): string {
  return (n >= 0 ? '+' : '−') + fmtNet(Math.abs(n));
}

// Hâkimiyet kademe renkleri — GRAFİK dolgu (metrik değil; sunucu %'sini yalnız renklendirir).
// Öğrenci satırı (DC): ≥75 yeşil · ≥55 coral · altı amber.
function ogrenciBarFill(m: number): string {
  return m >= 75 ? color.semantic.success : m >= 55 ? color.dawn.coralCtaBg : color.semantic.risk;
}
// Sınıf konu hâkimiyeti (DC): ≥75 yeşil · ≥60 amber · altı terracotta (coral).
function konuBarFill(m: number): string {
  return m >= 75 ? color.semantic.success : m >= 60 ? color.semantic.risk : color.dawn.coralCtaBg;
}
function konuPctText(m: number): string {
  return m >= 75 ? color.semantic.successTextOnLight : m >= 60 ? color.semantic.riskTextOnLight : color.dawn.coralTextOnLight;
}

// SSR-guard'lı matchMedia (jsdom'da matchMedia yok → false; breakpoint harness gezer).
function useMedia(query: string): boolean {
  const [esles, setEsles] = React.useState(false);
  React.useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
      return;
    }
    const mq = window.matchMedia(query);
    const on = () => setEsles(mq.matches);
    on();
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, [query]);
  return esles;
}

// ---- Bespoke SVG (emoji YOK; metin glyph yok) ----
function IkonArti({ boy = 15 }: { boy?: number }) {
  return (
    <svg width={boy} height={boy} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  );
}
function IkonChevron() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <polyline points="9 6 15 12 9 18" />
    </svg>
  );
}
// Dikkat işareti (uyarı üçgeni) — risk = amber (alarm-kırmızı DEĞİL). SR metni ayrı taşınır.
function IkonDikkat() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M10.3 3.6 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.6a2 2 0 0 0-3.4 0Z" /><path d="M12 9v4" /><path d="M12 17h.01" />
    </svg>
  );
}

const SR_ONLY: React.CSSProperties = {
  position: 'absolute', width: 1, height: 1, padding: 0, margin: -1,
  overflow: 'hidden', clip: 'rect(0 0 0 0)', whiteSpace: 'nowrap', border: 0,
};

const kartStil: React.CSSProperties = {
  boxSizing: 'border-box', background: color.paper.card,
  border: `1px solid ${color.paper.border}`, borderRadius: 18, padding: 20,
};

// ---- Yerel KPI kartı (StatBlock amber-delta desteklemiyor → yerel; risk=amber) ----
interface KpiCardProps {
  label: string;
  value: React.ReactNode;
  valueTone?: string;
  delta?: string;
  deltaTone?: 'success' | 'attention';
}
function KpiCard({ label, value, valueTone, delta, deltaTone = 'success' }: KpiCardProps) {
  return (
    <div style={{ boxSizing: 'border-box', background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 16, padding: 18, minWidth: 0 }}>
      <div style={{ fontFamily: font.sans, fontSize: 12.5, color: color.ink.muted, fontWeight: 600, marginBottom: 8 }}>{label}</div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, flexWrap: 'wrap' }}>
        <span style={{ ...numText, fontSize: 28, fontWeight: 800, lineHeight: 1, color: valueTone ?? color.ink.primary }}>{value}</span>
        {delta ? (
          deltaTone === 'attention' ? (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontFamily: font.sans, fontSize: 12, fontWeight: 700, color: color.semantic.riskTextOnLight, background: color.semantic.riskBgSoft, border: `1px solid ${color.semantic.riskBorderSoft}`, borderRadius: 999, padding: '2px 9px' }}>
              <IkonDikkat />{delta}
            </span>
          ) : (
            <span style={{ fontFamily: font.sans, fontSize: 12, fontWeight: 700, color: color.semantic.success }}>{delta}</span>
          )
        ) : null}
      </div>
    </div>
  );
}

// ---- Öğrenci satırı (gerçek <tr>; satır linkinin erişilebilir adı = öğrenci adı) ----
function OgrenciSatir({ o, sonAktifGizli }: { o: OgretmenOgrenci; sonAktifGizli: boolean }) {
  const risk = o.risk === 'dikkat';
  const hucreStil: React.CSSProperties = { boxSizing: 'border-box', padding: '12px 8px', borderBottom: `1px solid ${color.paper.borderFaint}`, verticalAlign: 'middle' };
  return (
    <tr>
      <td style={{ ...hucreStil, minWidth: 0 }}>
        <a
          href={ROTA.ogrenci(o.id)}
          aria-label={o.ad}
          style={{ display: 'flex', alignItems: 'center', gap: 11, minHeight: 44, minWidth: 0, textDecoration: 'none', color: 'inherit', borderRadius: 10 }}
        >
          <span aria-hidden style={{ width: 34, height: 34, flexShrink: 0, borderRadius: 10, background: 'linear-gradient(135deg,#2A2433,#4A4456)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 800 }}>{o.ini}</span>
          <span style={{ minWidth: 0 }}>
            <span style={{ display: 'block', fontFamily: font.sans, fontSize: 13.5, fontWeight: 700, color: color.ink.primary, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{o.ad}</span>
            {risk ? (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontFamily: font.sans, fontSize: 11, fontWeight: 700, color: color.semantic.riskTextOnLight, marginTop: 1 }}>
                <IkonDikkat />{o.odevDurum}
              </span>
            ) : (
              <span style={{ display: 'block', fontFamily: font.sans, fontSize: 11, fontWeight: 600, color: color.ink.muted, marginTop: 1 }}>{o.odevDurum}</span>
            )}
          </span>
        </a>
      </td>
      <td style={{ ...hucreStil }}>
        <span style={{ ...numText, fontSize: 15, fontWeight: 800, color: color.ink.primary }}>{fmtNet(o.ortNet)}</span>
      </td>
      <td style={{ ...hucreStil }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 9, minWidth: 0 }}>
          <div style={{ flex: 1, minWidth: 24 }}>
            <ProgressBar pct={o.hakimiyet} color={ogrenciBarFill(o.hakimiyet)} height={7} ariaLabel={`${o.ad} hâkimiyeti yüzde ${o.hakimiyet}`} />
          </div>
          <span style={{ ...numText, fontSize: 11.5, fontWeight: 700, color: color.ink.muted, width: 32, textAlign: 'right', flexShrink: 0 }}>%{o.hakimiyet}</span>
        </div>
      </td>
      {!sonAktifGizli ? (
        <td style={{ ...hucreStil }}>
          <span style={{ fontFamily: font.sans, fontSize: 12.5, fontWeight: 500, color: color.ink.muted, whiteSpace: 'nowrap' }}>{o.sonAktif}</span>
        </td>
      ) : null}
    </tr>
  );
}

// ---- Dikkat kartı (yalnız yetişkine görünür; amber — en yüksek öncelik koyu amber) ----
function DikkatKart({ k, koyu }: { k: DikkatKarti; koyu: boolean }) {
  const bg = koyu ? color.semantic.riskBgSoft : '#FFFBEB';
  const kenar = koyu ? color.semantic.riskBorderSoft : '#FDE9B8';
  return (
    <a
      href={ROTA.ogrenciler}
      aria-label={`${k.ad}: ${k.metin}`}
      style={{ boxSizing: 'border-box', display: 'flex', alignItems: 'center', gap: 11, minHeight: 44, padding: '11px 12px', background: bg, border: `1px solid ${kenar}`, borderRadius: 12, textDecoration: 'none', color: 'inherit' }}
    >
      <span aria-hidden style={{ width: 32, height: 32, flexShrink: 0, borderRadius: 9, background: color.semantic.riskTextOnLight, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 800 }}>
        {k.ad.split(' ').map((p) => p[0]).join('').slice(0, 2)}
      </span>
      <span style={{ flex: 1, minWidth: 0 }}>
        <span style={{ display: 'block', fontFamily: font.sans, fontSize: 13, fontWeight: 700, color: color.ink.primary }}>{k.ad}</span>
        <span style={{ display: 'block', fontFamily: font.sans, fontSize: 11.5, fontWeight: 600, color: color.semantic.riskTextOnLight }}>{k.metin}</span>
      </span>
    </a>
  );
}

// Topbar sınıf seçici — gerçek <button> + aria-pressed (DC span→button kanon düzeltmesi).
function SinifChip({ ad, ders, aktif, onSec }: { ad: string; ders: string; aktif: boolean; onSec: () => void }) {
  return (
    <button
      type="button"
      aria-pressed={aktif}
      onClick={onSec}
      style={{
        boxSizing: 'border-box', display: 'inline-flex', alignItems: 'center', minHeight: 44, padding: '0 14px',
        borderRadius: 999, cursor: 'pointer', fontFamily: font.sans, fontSize: 13, fontWeight: aktif ? 700 : 600,
        background: aktif ? color.dawn.coralCtaBg : color.paper.card, color: aktif ? '#fff' : color.ink.secondary,
        border: aktif ? '1px solid transparent' : `1px solid ${color.paper.border}`, whiteSpace: 'nowrap',
      }}
    >
      {ad} · {ders}
    </button>
  );
}

export function OgretmenPaneliPage(): React.ReactElement {
  const dar = useMedia('(max-width: 1023px)');
  const tekSutun = useMedia('(max-width: 760px)');
  const kpiKompakt = useMedia('(max-width: 760px)');
  const kpiTek = useMedia('(max-width: 440px)');
  const tabloDar = useMedia('(max-width: 520px)');
  const baslikSar = useMedia('(max-width: 520px)');

  const [panel, setPanel] = React.useState<OgretmenPanel | null>(null);
  const [aktifSinif, setAktifSinif] = React.useState<string | undefined>(undefined);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);

  React.useEffect(() => {
    let alive = true;
    setPanel(null);
    setHata(false);
    getOgretmenPanel(aktifSinif)
      .then((p) => {
        if (!alive) {
          return;
        }
        setPanel(p);
      })
      .catch(() => {
        if (alive) {
          setHata(true);
        }
      });
    return () => {
      alive = false;
    };
  }, [aktifSinif, yeniden]);

  const kpiSut = kpiTek ? '1fr' : kpiKompakt ? 'repeat(2, 1fr)' : 'repeat(3, minmax(0, 1fr))';
  const seciliSinifId = panel?.aktifSinifId ?? aktifSinif;

  return (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={{ minHeight: '100vh', background: color.paper.bg, display: 'flex', fontFamily: font.sans, color: color.ink.primary }}>
        <SideNav role="ogretmen" activeId="panel" collapsed={dar} userName="Öğretmen" userSub={panel ? panel.siniflar.map((s) => s.ad).join(' · ') : 'Panel'} />

        <main style={{ flex: 1, minWidth: 0 }}>
          {/* Topbar */}
          <header
            style={{
              boxSizing: 'border-box', position: 'sticky', top: 0, zIndex: 5, minHeight: 66,
              height: baslikSar ? 'auto' : 66, display: 'flex', alignItems: 'center',
              flexWrap: baslikSar ? 'wrap' : 'nowrap', gap: 10, padding: baslikSar ? '10px 16px' : '0 30px',
              rowGap: 8, background: 'rgba(250,247,242,0.86)', backdropFilter: 'blur(8px)',
              borderBottom: `1px solid ${color.paper.border}`,
            }}
          >
            <h1 style={{ margin: 0, fontFamily: font.sans, fontSize: 18, fontWeight: 800, letterSpacing: '-0.02em' }}>Panel</h1>
            {!baslikSar ? <span aria-hidden style={{ width: 1, height: 22, background: color.paper.borderStrong, margin: '0 6px' }} /> : null}

            {panel ? panel.siniflar.map((s) => (
              <SinifChip key={s.id} ad={s.ad} ders={s.ders} aktif={s.id === seciliSinifId} onSec={() => setAktifSinif(s.id)} />
            )) : null}

            <a
              href={ROTA.yeniSinif}
              aria-label="Yeni sınıf kur"
              style={{ boxSizing: 'border-box', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 44, height: 44, borderRadius: 999, background: color.paper.card, border: `1px dashed ${color.paper.borderStrong}`, color: color.ink.muted, textDecoration: 'none', flexShrink: 0 }}
            >
              <IkonArti />
            </a>

            <div style={{ flex: 1 }} />

            <a
              href={ROTA.odevYeni}
              style={{ boxSizing: 'border-box', display: 'inline-flex', alignItems: 'center', gap: 8, minHeight: 44, padding: '0 16px', borderRadius: 11, background: color.dawn.coralCtaBg, color: '#fff', fontFamily: font.sans, fontSize: 13.5, fontWeight: 700, textDecoration: 'none', flexShrink: 0 }}
            >
              <IkonArti boy={16} />Ödev oluştur
            </a>
          </header>

          <div style={{ boxSizing: 'border-box', maxWidth: 1280, margin: '0 auto', padding: baslikSar ? '20px 16px 40px' : '24px 30px 46px', display: 'flex', flexDirection: 'column', gap: 20 }}>
            {hata ? (
              <ErrorState
                serifTitle="Panelin şu an gelmedi."
                body="Sorun sizde değil — bağlantı bir soluklandı, sınıfınızın verisi güvende. Birazdan yeniden deneyin."
                onRetry={() => setYeniden((n) => n + 1)}
              />
            ) : panel === null ? (
              <div aria-busy="true" aria-label="Panel yükleniyor" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                <div style={{ display: 'grid', gridTemplateColumns: kpiSut, gap: 16 }}>
                  {[0, 1, 2].map((i) => <div key={i} style={{ ...kartStil, borderRadius: 16, padding: 18 }}><Skeleton shape="row" delayMs={0} slowAfterMs={null} /></div>)}
                </div>
                <div style={kartStil}><Skeleton shape="card" delayMs={0} /></div>
              </div>
            ) : panel.siniflar.length === 0 ? (
              // Boş durum — henüz sınıf yok. Kopya inferred → onay bekler.
              <div style={{ ...kartStil, padding: 40, display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: 14 }}>
                <div style={{ fontFamily: font.serif, fontStyle: 'italic', fontSize: 21, color: color.ink.primary, lineHeight: 1.25 }}>Henüz bir sınıfınız yok.</div>
                <p style={{ margin: 0, fontFamily: font.sans, fontSize: 13, color: color.ink.muted, maxWidth: 360, lineHeight: 1.6 }}>
                  İlk sınıfınızı kurun — öğrencileriniz bir katılım koduyla katılsın, gerisini panel toplasın.
                </p>
                <a
                  href={ROTA.yeniSinif}
                  style={{ boxSizing: 'border-box', display: 'inline-flex', alignItems: 'center', gap: 8, minHeight: 44, padding: '0 18px', borderRadius: 11, background: color.dawn.coralCtaBg, color: '#fff', fontFamily: font.sans, fontSize: 14, fontWeight: 700, textDecoration: 'none' }}
                >
                  İlk sınıfını kur
                </a>
              </div>
            ) : (
              <>
                {/* KPI — sunucu-otorite (kpi.*); DC "çözülen soru"/"2 gecikmiş" veri YOK → taşınmadı */}
                <section style={{ display: 'grid', gridTemplateColumns: kpiSut, gap: 16 }}>
                  <KpiCard
                    label="Sınıf ortalama net"
                    value={fmtNet(panel.kpi.ortNet)}
                    valueTone={color.dawn.coralTextOnLight}
                    delta={fmtDelta(panel.kpi.ortNetDelta)}
                    deltaTone={panel.kpi.ortNetDelta < 0 ? 'attention' : 'success'}
                  />
                  <KpiCard
                    label="Aktif öğrenci (7g)"
                    value={<><span>{panel.kpi.ogrenciDelta}</span><span style={{ fontSize: 17, color: color.ink.muted }}>/{panel.kpi.ogrenci}</span></>}
                  />
                  <KpiCard
                    label="Teslim bekleyen ödev"
                    value={panel.kpi.gecikmisOdev}
                    delta="bekliyor"
                    deltaTone="attention"
                  />
                </section>

                {/* İki sütun: öğrenci performansı + sağ ray */}
                <section style={{ display: 'grid', gridTemplateColumns: tekSutun ? '1fr' : 'minmax(0, 1.7fr) minmax(0, 1fr)', gap: 20, alignItems: 'start' }}>
                  {/* Öğrenci performansı tablosu */}
                  <div style={{ ...kartStil, padding: 22, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginBottom: 8 }}>
                      <h2 style={{ margin: 0, fontFamily: font.sans, fontSize: 16.5, fontWeight: 700 }}>Öğrenci Performansı</h2>
                      <a href={ROTA.ogrenciler} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, minHeight: 44, padding: '0 4px', fontFamily: font.sans, fontSize: 12.5, fontWeight: 700, color: color.dawn.coralTextOnLight, textDecoration: 'none' }}>
                        Tümü<IkonChevron />
                      </a>
                    </div>

                    <table style={{ width: '100%', borderCollapse: 'collapse', tableLayout: 'fixed' }}>
                      <caption style={SR_ONLY}>Sınıf öğrenci performansı — ortalama net, hâkimiyet ve son aktivite</caption>
                      <thead>
                        <tr>
                          <th scope="col" style={{ boxSizing: 'border-box', textAlign: 'left', padding: '0 8px 10px', borderBottom: `1px solid ${color.paper.border}`, fontFamily: font.sans, fontSize: 11, fontWeight: 700, color: color.ink.muted, textTransform: 'uppercase', letterSpacing: '0.05em', width: tabloDar ? '46%' : '38%' }}>Öğrenci</th>
                          <th scope="col" style={{ boxSizing: 'border-box', textAlign: 'left', padding: '0 8px 10px', borderBottom: `1px solid ${color.paper.border}`, fontFamily: font.sans, fontSize: 11, fontWeight: 700, color: color.ink.muted, textTransform: 'uppercase', letterSpacing: '0.05em', width: tabloDar ? '20%' : '16%' }}>Ort. net</th>
                          <th scope="col" style={{ boxSizing: 'border-box', textAlign: 'left', padding: '0 8px 10px', borderBottom: `1px solid ${color.paper.border}`, fontFamily: font.sans, fontSize: 11, fontWeight: 700, color: color.ink.muted, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Hâkimiyet</th>
                          {!tabloDar ? (
                            <th scope="col" style={{ boxSizing: 'border-box', textAlign: 'left', padding: '0 8px 10px', borderBottom: `1px solid ${color.paper.border}`, fontFamily: font.sans, fontSize: 11, fontWeight: 700, color: color.ink.muted, textTransform: 'uppercase', letterSpacing: '0.05em', width: '22%' }}>Son aktivite</th>
                          ) : null}
                        </tr>
                      </thead>
                      <tbody>
                        {panel.ogrenciler.map((o) => (
                          <OgrenciSatir key={o.id} o={o} sonAktifGizli={tabloDar} />
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Sağ ray: dikkat + sınıf hâkimiyeti */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 }}>
                    <div style={kartStil}>
                      <h2 style={{ margin: '0 0 14px', fontFamily: font.sans, fontSize: 15.5, fontWeight: 700 }}>Dikkat gerektiren öğrenciler</h2>
                      {panel.dikkat.length === 0 ? (
                        <p style={{ margin: 0, fontFamily: font.sans, fontSize: 13, color: color.ink.muted, lineHeight: 1.6 }}>
                          Şu an dikkat isteyen bir öğrenci yok — sınıf sakin.
                        </p>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                          {panel.dikkat.map((k, i) => <DikkatKart key={k.ad + i} k={k} koyu={i === 0} />)}
                        </div>
                      )}
                    </div>

                    <div style={kartStil}>
                      <h2 style={{ margin: '0 0 16px', fontFamily: font.sans, fontSize: 15.5, fontWeight: 700 }}>Sınıf konu hâkimiyeti</h2>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 13 }}>
                        {panel.sinifHakimiyet.map((t: DersIlerleme) => (
                          <div key={t.ders} style={{ minWidth: 0 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                              <span style={{ fontFamily: font.sans, fontSize: 13, fontWeight: 700, color: color.ink.primary, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.ders}</span>
                              <span style={{ ...numText, marginLeft: 'auto', fontSize: 12.5, fontWeight: 800, color: konuPctText(t.hakimiyet), flexShrink: 0 }}>%{t.hakimiyet}</span>
                            </div>
                            <ProgressBar pct={t.hakimiyet} color={konuBarFill(t.hakimiyet)} height={7} ariaLabel={`${t.ders} sınıf hâkimiyeti yüzde ${t.hakimiyet}`} />
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </section>
              </>
            )}
          </div>
        </main>
      </div>
    </KiroThemeProvider>
  );
}

export default OgretmenPaneliPage;
