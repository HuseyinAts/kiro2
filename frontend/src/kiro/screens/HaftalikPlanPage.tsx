// ============================================================================
// KIRO2 — Haftalık Plan (SPRINT5 · KIRO2 Haftalik Plan.dc.html)
// Tema = PAPER (çalışma yüzeyi). SideNav(active=plan) + 66px header + 7-sütun hafta grid'i.
// Kopya SPRINT5_SPEC §A'dan BİREBİR. Veri: getPlanWeek + getMe (mock katmanı).
// DC otoritesi: blok kartı TAG satırında 7×7 nokta (DC'de sol 3px bar YOK).
// Coral AA: pill METNİ + BUGÜN rozeti #C2452B; bugün kart kenarı dekoratif #FF6F5C OK.
// ============================================================================
import * as React from 'react';

import { getPlanWeek, getMe } from '../api/api-client';
import { color, font } from '../tokens';
import type { PlanBlok, PlanGun, PlanWeek, Persona, SubjectKey } from '../types';
import { KiroThemeProvider, numText } from '../ui/theme';
import { Button } from '../ui/Button';
import { EmptyState } from '../ui/EmptyState';
import { ErrorState } from '../ui/ErrorState';
import { Skeleton } from '../ui/Skeleton';
import { SideNav } from '../ui/SideNav';
import '../tokens/tokens.css';

const DERS_AD: Record<SubjectKey, string> = { mat: 'Matematik', fiz: 'Fizik', kim: 'Kimya', biy: 'Biyoloji', tur: 'Türkçe' };
const GUN_TAM: Record<string, string> = { Pzt: 'Pazartesi', Sal: 'Salı', Çar: 'Çarşamba', Per: 'Perşembe', Cum: 'Cuma', Cmt: 'Cumartesi', Paz: 'Pazar' };

// SideNav ≤1023px'te 64px ikon rayına çöker; grid ≤1080px 4 sütun, ≤760px tek sütun.
// jsdom matchMedia'sız guard'lı (PanelPage.tsx local hook'u).
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

// tur → { renk, tag }. calisma'da ders rengi/adı; diğerleri sabit.
function blokStil(b: PlanBlok): { renk: string; tag: string } {
  switch (b.tur) {
    case 'calisma': {
      const d = b.ders ?? 'mat';
      return { renk: color.subject.light[d], tag: DERS_AD[d] };
    }
    case 'tekrar':
      return { renk: '#9A5D0D', tag: 'FSRS Tekrar' };
    case 'deneme':
      return { renk: color.dawn.coralTextOnLight, tag: 'Deneme' }; // coral METİN → AA
    case 'analiz':
      return { renk: color.ink.muted, tag: 'Analiz' };
    case 'mola':
      return { renk: '#1FB683', tag: 'Mola' };
    default:
      return { renk: color.ink.muted, tag: '' };
  }
}

const trOndalik = (n: number) => n.toFixed(1).replace('.', ',');

function Saat() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#6B6478" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <circle cx="12" cy="12" r="9" /><polyline points="12 7 12 12 15 14" />
    </svg>
  );
}
function Takvim() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke={color.dawn.coralTextOnLight} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <rect x="3" y="4" width="18" height="17" rx="2" /><path d="M3 9h18M8 2v4M16 2v4" />
    </svg>
  );
}

function GunSutunu({ g }: { g: PlanGun }) {
  const toplam = g.bloklar.reduce((a, b) => a + b.dk, 0);
  const bos = g.bloklar.length === 0;
  const gunTam = GUN_TAM[g.gun] ?? g.gun;
  const ariaLabel = `${gunTam} · ${g.bloklar.length} blok · ${toplam} dk`;

  return (
    <section
      aria-label={ariaLabel}
      style={{
        display: 'flex', flexDirection: 'column', gap: 9, borderRadius: 16, padding: '12px 11px',
        background: g.bugun ? '#FFF3EE' : color.paper.subtle,
        border: g.bugun ? '1px solid #FF6F5C' : `1px solid ${color.paper.border}`,
      }}
    >
      {/* Gün başlığı */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 7, padding: '0 2px 4px' }}>
        <h2 style={{ margin: 0, fontSize: 14, fontWeight: 800, color: g.bugun ? color.dawn.coralTextOnLight : color.ink.primary }}>{g.gun}</h2>
        <span style={{ fontSize: 11.5, color: color.ink.muted, fontWeight: 600 }}>{g.tarih}</span>
        {g.bugun && (
          <span style={{ marginLeft: 'auto', fontSize: 9.5, fontWeight: 800, letterSpacing: '0.05em', textTransform: 'uppercase', color: '#fff', background: color.dawn.coralCtaBg, padding: '2px 7px', borderRadius: 999 }}>BUGÜN</span>
        )}
      </div>

      {/* Blok kartları */}
      {bos ? (
        <div style={{ padding: '14px 10px', borderRadius: 12, border: '1px dashed #E0D8CC', textAlign: 'center', fontSize: 11.5, color: color.ink.muted }}>Serbest</div>
      ) : (
        <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 9 }}>
          {g.bloklar.map((b, i) => {
            const { renk, tag } = blokStil(b);
            return (
              <li key={`${b.tur}-${i}`} style={{ listStyle: 'none' }}>
                <a href={b.hedefRota} style={{ display: 'block', textDecoration: 'none', borderRadius: 12, border: `1px solid ${color.paper.border}`, background: color.paper.card, padding: '10px 12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 9.5, fontWeight: 800, letterSpacing: '0.06em', color: renk, textTransform: 'uppercase' }}>
                    <span aria-hidden style={{ width: 7, height: 7, borderRadius: 2.5, background: renk, flexShrink: 0 }} />
                    {tag}
                  </div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: color.ink.primary, marginTop: 3, lineHeight: 1.3 }}>{b.baslik}</div>
                  <div style={{ fontSize: 11, color: color.ink.muted, marginTop: 4 }}>{b.meta}</div>
                </a>
              </li>
            );
          })}
        </ul>
      )}

      {/* Sütun altı toplam */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '4px 3px 0', borderTop: '1px solid rgba(0,0,0,0.05)', marginTop: 2 }}>
        <span style={{ fontSize: 10.5, fontWeight: 700, color: color.ink.muted, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Toplam</span>
        <span style={{ ...numText, fontSize: 12.5, fontWeight: 800, color: color.ink.primary }}>{toplam} dk</span>
      </div>
    </section>
  );
}

export function HaftalikPlanPage(): React.ReactElement {
  const dar = useMedia('(max-width: 1023px)');
  const orta = useMedia('(max-width: 1080px)');
  const kompakt = useMedia('(max-width: 760px)');
  const gridSut = kompakt ? 'minmax(0, 1fr)' : orta ? 'repeat(4, minmax(0, 1fr))' : 'repeat(7, minmax(0, 1fr))';

  const [persona, setPersona] = React.useState<Persona | null>(null);
  const [week, setWeek] = React.useState<PlanWeek | null>(null);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);

  React.useEffect(() => {
    let alive = true;
    setWeek(null);
    setHata(false);
    Promise.all([getPlanWeek(), getMe()])
      .then(([w, p]) => {
        if (!alive) return;
        setWeek(w);
        setPersona(p);
      })
      .catch(() => {
        if (alive) setHata(true);
      });
    return () => {
      alive = false;
    };
  }, [yeniden]);

  const haftaSaat = week ? trOndalik(week.gunler.reduce((a, g) => a + g.bloklar.reduce((s, b) => s + b.dk, 0), 0) / 60) : '0';
  const hepsiBos = week ? week.gunler.every((g) => g.bloklar.length === 0) : false;

  return (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={{ minHeight: '100vh', background: color.paper.bg, display: 'flex', fontFamily: font.sans, color: color.ink.primary }}>
        <SideNav role="ogrenci" activeId="plan" collapsed={dar} userName={persona?.ad ?? 'Öğrenci'} userSub={persona?.sinif ?? ''} onAssistant={() => undefined} />

        <main style={{ flex: 1, minWidth: 0 }}>
          {/* Header */}
          <header style={{ position: 'sticky', top: 0, zIndex: 6, minHeight: 66, height: kompakt ? 'auto' : 66, display: 'flex', alignItems: 'center', flexWrap: kompakt ? 'wrap' : 'nowrap', gap: 14, rowGap: 8, padding: kompakt ? '12px 16px' : '0 30px', background: 'rgba(250,247,242,0.86)', backdropFilter: 'blur(8px)', borderBottom: `1px solid ${color.paper.border}` }}>
            <h1 style={{ margin: 0, fontSize: 18, fontWeight: 800, letterSpacing: '-0.02em' }}>Haftalık Plan</h1>
            <span style={{ fontSize: 13, color: color.ink.muted, fontWeight: 600 }}>{week?.aralik ?? ''}</span>
            <div style={{ flex: 1 }} />
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 7, height: 36, padding: '0 13px', borderRadius: 10, background: color.paper.card, border: `1px solid ${color.paper.border}` }}>
              <Saat />
              <span style={{ fontSize: 13, fontWeight: 700, color: color.ink.primary }}>Günlük hedef <span style={numText}>{week?.gunlukHedefDk ?? 0}</span> dk</span>
            </div>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 7, height: 36, padding: '0 13px', borderRadius: 10, background: '#FFF3EE', border: '1px solid #FBD9C9' }}>
              <Takvim />
              <span style={{ fontSize: 13, fontWeight: 800, color: color.dawn.coralTextOnLight }}>Bu hafta ~<span style={numText}>{haftaSaat}</span> sa</span>
            </div>
          </header>

          <div style={{ padding: kompakt ? '20px 16px 48px' : '24px 30px 60px' }}>
            <p style={{ margin: '0 0 20px', fontSize: 14, color: color.ink.muted, maxWidth: 680, lineHeight: 1.6 }}>
              Motor bu haftayı senin için kurdu: bugün <strong style={{ color: color.ink.primary }}>zamanı gelen tekrarlar</strong>, en zayıf konuların ve hafta sonu bir deneme. Her bloğa dokunup başla.
            </p>

            {hata ? (
              <ErrorState
                serifTitle="Haftalık planın şu an gelmedi."
                onRetry={() => setYeniden((n) => n + 1)}
              />
            ) : week === null ? (
              <div aria-busy="true" aria-label="Haftalık plan yükleniyor" style={{ display: 'grid', gridTemplateColumns: gridSut, gap: 12, alignItems: 'start' }}>
                {[0, 1, 2, 3, 4, 5, 6].map((i) => (
                  <div key={i} style={{ borderRadius: 16, padding: '12px 11px', background: color.paper.subtle, border: `1px solid ${color.paper.border}` }}>
                    <Skeleton shape="card" delayMs={0} slowAfterMs={null} />
                  </div>
                ))}
              </div>
            ) : hepsiBos ? (
              <EmptyState
                serifTitle="Planın seni bekliyor."
                body="Motor seni birkaç soruyla tanıyınca haftanı senin için kuruyor — kuruluma göz atalım, sonrası bize kalsın."
                action={<Button variant="primary" onClick={() => undefined}>Kuruluma git</Button>}
              />
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: gridSut, gap: 12, alignItems: 'start' }}>
                {week.gunler.map((g) => (
                  <GunSutunu key={g.gun} g={g} />
                ))}
              </div>
            )}
          </div>
        </main>
      </div>
    </KiroThemeProvider>
  );
}

export default HaftalikPlanPage;
