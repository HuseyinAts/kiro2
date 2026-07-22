// ============================================================================
// KIRO2 — Ödevlerim (SPRINT1 · KIRO2 Odevlerim.dc.html)
// Tema = PAPER (çalışma yüzeyi; route-bazlı, toggle YOK).
// Kopya SPRINT1_SPEC §C'den BİREBİR — istisna: liste dipnotu absence-dili içeriyordu,
// kanon (ve spec'in kendi kuralı) gereği nötrlendi (onay bekler).
// Veri: configureKiroApi mock → getMe + getAssignments (kiro-data.json).
// ============================================================================
import * as React from 'react';

import { configureKiroApi, getAssignments, getMe } from '../api/api-client';
import type { MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';
import { color, font } from '../tokens';
import type { Odev, Persona, SubjectKey } from '../types';
import { KiroThemeProvider, numText } from '../ui/theme';
import { Button } from '../ui/Button';
import { Callout } from '../ui/Callout';
import { EmptyState } from '../ui/EmptyState';
import { ErrorState } from '../ui/ErrorState';
import { ProgressBar } from '../ui/ProgressBar';
import { Skeleton } from '../ui/Skeleton';
import { StatusChip } from '../ui/StatusChip';
import { SideNav } from '../ui/SideNav';
import '../tokens/tokens.css';

configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });

const DERS_AD: Record<SubjectKey, string> = { mat: 'Matematik', fiz: 'Fizik', kim: 'Kimya', biy: 'Biyoloji', tur: 'Türkçe' };
const dersRenk = color.subject.light;

const dk1 = (o: Odev) => Math.max(1, Math.round((o.adet - o.yapilan) * 1.6));
const yuzde = (o: Odev) => Math.round((o.yapilan / Math.max(1, o.adet)) * 100);

function Pano({ c }: { c: string }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
      <rect x="8" y="2" width="8" height="4" rx="1" /><path d="M9 12h6M9 16h4" />
    </svg>
  );
}
function Hedef() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#6B6478" strokeWidth="1.8" aria-hidden>
      <circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="4.5" /><circle cx="12" cy="12" r="0.9" fill="#6B6478" />
    </svg>
  );
}
function Saat() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" aria-hidden>
      <circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" />
    </svg>
  );
}
function Sunrise() {
  return (
    <svg width="120" height="38" viewBox="0 0 120 38" fill="none" aria-hidden>
      <line x1="4" y1="31" x2="42" y2="31" stroke="#E2DACE" strokeWidth="1.4" strokeLinecap="round" />
      <line x1="78" y1="31" x2="116" y2="31" stroke="#E2DACE" strokeWidth="1.4" strokeLinecap="round" />
      <path d="M46 31a14 14 0 0 1 28 0Z" fill="#FF8A5B" />
    </svg>
  );
}

function OdevKart({ o }: { o: Odev }) {
  const c = dersRenk[o.ders];
  const kenar = o.durum === 'bekliyor' ? '#F2D9AC' : color.paper.border;
  const barColor = o.durum === 'tamam' ? '#1FB683' : c;
  const cta =
    o.durum === 'tamam'
      ? { label: 'Çözümlere bak', variant: 'ghost' as const }
      : o.yapilan > 0
        ? { label: 'Devam et', variant: 'primary' as const }
        : { label: 'Başlayalım', variant: 'primary' as const };

  return (
    <li style={{ listStyle: 'none' }}>
      <div style={{ background: color.paper.card, border: `1px solid ${kenar}`, borderRadius: 18, padding: '20px 22px', marginBottom: 14 }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
          <div aria-hidden style={{ width: 40, height: 40, flexShrink: 0, borderRadius: 11, background: c + '1A', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Pano c={c} />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
              <span style={{ fontSize: 15, fontWeight: 800 }}>{o.baslik}</span>
              <StatusChip durum={o.durum} kalan={o.kalan ?? undefined} />
            </div>
            <div style={{ marginTop: 3, fontSize: 12.5, color: color.ink.muted }}>
              {DERS_AD[o.ders]} · {o.konu} · {o.atayan}
            </div>
          </div>
          <div style={{ textAlign: 'right', flexShrink: 0 }}>
            <div style={{ ...numText, fontSize: 13.5, fontWeight: 800 }}>{o.yapilan} / {o.adet} soru</div>
            <div style={{ ...numText, fontSize: 12, color: color.ink.muted, marginTop: 2 }}>{o.durum === 'tamam' ? 'bitti' : `~${dk1(o)} dk`}</div>
          </div>
        </div>

        <div style={{ marginTop: 12 }}>
          <ProgressBar pct={yuzde(o)} color={barColor} height={7} ariaLabel={`${o.baslik} — ilerleme yüzde ${yuzde(o)}`} />
        </div>

        {o.durum === 'bekliyor' && (
          <div style={{ marginTop: 12 }}>
            <Callout tone="attention" icon={<Saat />}>Teslim geçti ama kapanmadı — çözdüğün her soru hâlâ sayılır.</Callout>
          </div>
        )}

        <div style={{ marginTop: 14, display: 'flex', flexWrap: 'wrap', gap: 10, alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center', fontSize: 12.5, color: color.ink.muted }}>
            {o.kisisel && (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}><Hedef /> Sorular seviyene göre seçildi</span>
            )}
            <span>Teslim: {o.teslim}</span>
          </div>
          <Button variant={cta.variant} onClick={() => undefined}>{cta.label}</Button>
        </div>
      </div>
    </li>
  );
}

// SideNav ≤1023px'te 64px ikon rayına çöker (BREAKPOINT_SPEC §3) — jsdom matchMedia'sız guard'lı.
function useDarEkran(): boolean {
  const [dar, setDar] = React.useState(false);
  React.useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return;
    const mq = window.matchMedia('(max-width: 1023px)');
    const on = () => setDar(mq.matches);
    on();
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, []);
  return dar;
}

export function OdevlerimPage(): React.ReactElement {
  const dar = useDarEkran();
  const [persona, setPersona] = React.useState<Persona | null>(null);
  const [odevler, setOdevler] = React.useState<Odev[] | null>(null);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);

  React.useEffect(() => {
    let alive = true;
    setOdevler(null);
    setHata(false);
    Promise.all([getMe(), getAssignments()])
      .then(([p, o]) => {
        if (!alive) return;
        setPersona(p);
        setOdevler(o);
      })
      .catch(() => {
        if (alive) setHata(true);
      });
    return () => {
      alive = false;
    };
  }, [yeniden]);

  const acik = (odevler ?? []).filter((o) => o.durum !== 'tamam');
  const kalanDk = Math.round(acik.reduce((t, o) => t + (o.adet - o.yapilan) * 1.6, 0));
  const ogretmen = (odevler ?? [])[0]?.atayan ?? '';

  return (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={{ minHeight: '100vh', background: color.paper.bg, display: 'flex', fontFamily: font.sans, color: color.ink.primary }}>
        <SideNav role="ogrenci" activeId="odev" collapsed={dar} userName={persona?.ad ?? 'Öğrenci'} userSub={persona?.sinif ?? ''} onAssistant={() => undefined} />

        <main style={{ flex: 1, minWidth: 0 }}>
          <header
            style={{
              position: 'sticky', top: 0, zIndex: 2, height: 66, display: 'flex', alignItems: 'center',
              padding: '0 30px', background: 'rgba(250,247,242,0.86)', backdropFilter: 'blur(8px)',
              borderBottom: `1px solid ${color.paper.border}`,
            }}
          >
            <div>
              <div style={{ fontSize: 16, fontWeight: 800 }}>Ödevlerim</div>
              <div style={{ fontSize: 12, color: color.ink.muted }}>12-A{ogretmen ? ` · ${ogretmen}` : ''}</div>
            </div>
          </header>

          <div style={{ maxWidth: 820, margin: '0 auto', padding: '24px 30px 48px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 20, gap: 16, flexWrap: 'wrap' }}>
              <div>
                <div style={{ ...numText, fontSize: 44, fontWeight: 800, lineHeight: 1 }}>~{kalanDk} dk</div>
                <div style={{ marginTop: 6, fontSize: 13.5, color: color.ink.secondary }}>
                  bugün kalan · <span style={numText}>{acik.length}</span> açık ödev
                </div>
              </div>
              <Sunrise />
            </div>

            {hata ? (
              <ErrorState
                serifTitle="Ödevlerin şu an gelmedi."
                body="Sorun sende değil — bağlantı bir soluklandı, çalışman güvende. Birazdan yeniden dene."
                onRetry={() => setYeniden((n) => n + 1)}
              />
            ) : odevler === null ? (
              <div aria-busy="true" aria-label="Ödevler yükleniyor">
                {[0, 1, 2].map((i) => (
                  <div key={i} style={{ marginBottom: 14, padding: '20px 22px', background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 18 }}>
                    <Skeleton shape="card" delayMs={0} slowAfterMs={null} />
                  </div>
                ))}
              </div>
            ) : odevler.length === 0 ? (
              <EmptyState
                serifTitle="Şu an ödevin yok."
                body="Plan sende — istersen bugünkü tekrar kartlarına bak ya da zayıf konunda birkaç soru çöz."
                action={<Button variant="primary" onClick={() => undefined}>Haftalık plana git</Button>}
              />
            ) : (
              <>
                <ul style={{ margin: 0, padding: 0 }}>
                  {odevler.map((o) => (
                    <OdevKart key={o.id} o={o} />
                  ))}
                </ul>
                <p style={{ marginTop: 8, fontSize: 12.5, lineHeight: 1.5, color: color.ink.muted }}>
                  Geciken ödev kapanmaz — “bekliyor”dur; kaldığın yerden devam etmen yeter. Sınıf sıralaması yayınlanmaz.
                </p>
              </>
            )}
          </div>
        </main>
      </div>
    </KiroThemeProvider>
  );
}

export default OdevlerimPage;
