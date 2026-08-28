// ============================================================================
// KIRO2 — Seri & Motivasyon (SPRINT8 · Grup 6 · KIRO2 Seri Dondurma.dc.html)
// Tema = PAPER (çalışma yüzeyi; route /seri, toggle YOK).
// Sunucu-otorite: seri/rekor getMe()'den · dondurmaHak + hafta[] getStreak()'ten.
//   Dondurma OTOMATİK (buton YOK); istemci hangi gün dondu / kaç hak HESAPLAMAZ —
//   freeze günü hafta[] durumundan OKUNUR, hak sayısı sunucudan gelir. seriNext=seri+1
//   yalnız salt gösterim (BasarimlarPage rekorKala deseni).
// KOPYA: DC birebir. İKİ İSTİSNA (kullanıcı kararı):
//   1) freeze "%48 daha uzun seri" istatistik kutusu ÇIKARILDI (yazılmadı).
//   2) AGRESİF nudge (anti-örnek: toggle/kırmızı/emoji/"SERİN TEHLİKEDE") PORTLANMADI;
//      yalnız insani ton statik.
// Empty(seri=0) kopyası inferred → onay bekler.
// ============================================================================
import * as React from 'react';

import { getMe, getStreak } from '../api/api-client';
import { color, font } from '../tokens';
import type { Persona, StreakData, StreakDay } from '../types';
import {
  KiroThemeProvider,
  numText,
  useReducedMotion,
  Skeleton,
  ErrorState,
  EmptyState,
  ChatBubble,
  SideNav,
} from '../ui';
import '../tokens/tokens.css';

// Dondurma SEMANTİK rengi (buz-mavi) — indigo-yasak istisnası (SPRINT6 §7 / kanon).
const BUZ = { bg: '#DBEAFE', ink: '#2563EB', shield: '#3B82F6' } as const;

const srOnly: React.CSSProperties = {
  position: 'absolute', width: 1, height: 1, padding: 0, margin: -1,
  overflow: 'hidden', clip: 'rect(0 0 0 0)', whiteSpace: 'nowrap', border: 0,
};

// Girişte tek yumuşak beliriş (DC kv-in) — reduced-motion'da kapalı; SPRING YOK.
const KEYFRAMES = `@keyframes seriEntrance { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:none; } }`;

// SideNav ≤1023px'te 64px ikon rayına çöker; gridler ≤760px tek sütun + bağlayıcı gizle.
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

/* ---- Bespoke SVG ikonlar (DC path'leri birebir; emoji YOK) ---- */
function FlameFill({ size, fill }: { size: number; fill: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill={fill} aria-hidden>
      <path d="M12 2c1.4 3.4 4.4 4.6 4.4 8.2a4.4 4.4 0 0 1-8.8.2c0-1.6.6-2.8 1.3-3.6.2 1.2 1 1.9 1.8 1.9C10.2 6.6 11 4.2 12 2Z" />
    </svg>
  );
}
function KristalIcon({ size }: { size: number }) {
  // Buz kristali (hafta karosu) — 6-kollu.
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={BUZ.ink} strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M12 2v20M3 7l18 10M21 7 3 17" /><path d="m9 4 3 2 3-2M9 20l3-2 3 2" />
    </svg>
  );
}
function FreezeBadgeIcon() {
  // Dondurma rozeti (kart) — asteriks kristali.
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={BUZ.ink} strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M12 2v20M2 12h20M5 5l14 14M19 5 5 19" />
    </svg>
  );
}
function ShieldMini() {
  return (
    <svg width="9" height="9" viewBox="0 0 24 24" fill={BUZ.shield} aria-hidden>
      <path d="M12 2 4 6v6c0 5 8 8 8 8s8-3 8-8V6Z" />
    </svg>
  );
}
function SparkleIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M5 3v4M3 5h4M6 17v4M4 19h4M13 3l2.5 6.5L22 12l-6.5 2.5L13 21l-2.5-6.5L4 12l6.5-2.5Z" />
    </svg>
  );
}
function BoltFill({ fill }: { fill: string }) {
  return <svg width="24" height="24" viewBox="0 0 24 24" fill={fill} aria-hidden><path d="M13 2 4 14h6l-1 8 9-12h-6l1-8Z" /></svg>;
}
function MedalIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#C99A2E" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <circle cx="12" cy="14" r="6" /><path d="M9 8 7 2M15 8l2-6M10.5 14l1.5-1.5 1.5 1.5-.6 2h-1.8Z" fill="#C99A2E" />
    </svg>
  );
}
function CrownFill() {
  return <svg width="24" height="24" viewBox="0 0 24 24" fill="#C99A2E" aria-hidden><path d="M3 8l3.5 3L12 5l5.5 6L21 8l-1.5 10h-15Z" /></svg>;
}

/* ---- Hafta karosu erişilebilir etiketi (tek-string; durum→tam metin) ---- */
function karoLabel(d: StreakDay): string {
  if (d.durum === 'done') return `${d.label} günü tamamlandı`;
  if (d.durum === 'freeze') return `${d.label} günü dondurma ile korundu`;
  // today: karo label'i zaten 'Bugün' olabilir → 'Bugün · bugün' tekrarını önle.
  return d.label === 'Bugün' ? 'Bugün · henüz tamamlanmadı, sıra sende' : `${d.label} · bugün`;
}

interface Veri {
  persona: Persona;
  streak: StreakData;
}

export function SeriDondurmaPage(): React.ReactElement {
  const reduced = useReducedMotion();
  const navCollapse = useMedia('(max-width: 1023px)');
  const dar = useMedia('(max-width: 760px)');
  const [veri, setVeri] = React.useState<Veri | null>(null);
  const [hata, setHata] = React.useState(false);

  const yukle = React.useCallback(() => {
    let alive = true;
    setHata(false);
    setVeri(null);
    Promise.all([getMe(), getStreak()])
      .then(([persona, streak]) => {
        if (alive) setVeri({ persona, streak });
      })
      .catch(() => {
        if (alive) setHata(true);
      });
    return () => {
      alive = false;
    };
  }, []);

  React.useEffect(() => yukle(), [yukle]);

  return (
    <KiroThemeProvider theme="paper">
      <div
        className="k-paper"
        style={{
          minHeight: '100vh', background: color.paper.bg, display: 'flex',
          fontFamily: font.sans, color: color.ink.primary, boxSizing: 'border-box',
        }}
      >
        <SideNav
          role="ogrenci"
          activeId="seri"
          collapsed={navCollapse}
          userName={veri?.persona.ad ?? 'Öğrenci'}
          userSub={veri?.persona.sinif ?? ''}
          onAssistant={() => undefined}
        />

        <main style={{ flex: 1, minWidth: 0 }}>
          <style>{KEYFRAMES}</style>
          <header
            style={{
              position: 'sticky', top: 0, zIndex: 5, height: 64, display: 'flex',
              alignItems: 'center', padding: '0 30px', background: color.paper.card,
              borderBottom: `1px solid ${color.paper.border}`, boxSizing: 'border-box',
            }}
          >
            <div style={{ lineHeight: 1.2 }}>
              <div style={{ fontSize: 16, fontWeight: 800 }}>Seri &amp; Motivasyon</div>
              <div style={{ fontSize: 11.5, color: color.ink.muted, fontWeight: 600 }}>
                Alışkanlık koru — affedicilikle, baskıyla değil
              </div>
            </div>
          </header>

          <div
            style={{
              maxWidth: 980, margin: '0 auto',
              padding: dar ? '22px 20px 50px' : '26px 30px 50px', boxSizing: 'border-box',
            }}
          >
            {hata ? (
              <ErrorState onRetry={yukle} />
            ) : !veri ? (
              <Iskelet dar={dar} />
            ) : (
              <Icerik veri={veri} reduced={reduced} dar={dar} />
            )}
          </div>
        </main>
      </div>
    </KiroThemeProvider>
  );
}

function Icerik({ veri, reduced, dar }: { veri: Veri; reduced: boolean; dar: boolean }): React.ReactElement {
  const { seri, seriRekor: rekor } = veri.persona;
  const { dondurmaHak, hafta } = veri.streak;

  // 31 Tem 2026 ölçümü: seri/seriRekor 73/77 kullanıcıda null (%95). Bu ekranın
  // TAMAMI seri merdiveni üzerine kurulu — veri yokken her değeri '—' yapmak
  // merdiveni anlamsız bir iskelete çevirirdi. Onun yerine dürüst boş-durum.
  if (seri === null || rekor === null) {
    return (
      <p style={{ margin: 0, fontSize: 14, color: color.ink.muted }}>
        Seri bilgin henüz oluşmadı. Çalışmaya başladığında burada görünecek.
      </p>
    );
  }

  const seriNext = seri + 1;
  const kaldi = (t: number) => Math.max(0, t - seri);
  const donmusGun = hafta.find((d) => d.durum === 'freeze')?.label;

  // seri=0 → yönlendiren boşluk (inferred kopya, alarm dili YOK → onay bekler).
  if (seri === 0) {
    return (
      <EmptyState
        serifTitle="Serin bugün başlıyor."
        body="İlk günü koymak en zor adım — bir ders ya da birkaç soru yeter. Dondurma hakların hazır; kaçırdığın gün seni geri çekmez."
        action={<PrimaryLink href="/soru-cozme">Bugünü tamamla</PrimaryLink>}
      />
    );
  }

  const MILES: {
    d: string; label: string; bg: string; border: string; dColor: string;
    icon: React.ReactNode; conn: string | null;
  }[] = [
    { d: '7 gün', label: 'Alev', bg: '#FBF0DE', border: '2px solid #FDBA74', dColor: color.semantic.riskTextOnLight, icon: <FlameFill size={22} fill="#E0593F" />, conn: '#FDBA74' },
    { d: `${seri} gün`, label: 'Şu an', bg: '#FFF3EE', border: `2px solid ${color.dawn.coral}`, dColor: color.dawn.coralTextOnLight, icon: <BoltFill fill={color.dawn.coral} />, conn: color.paper.border },
    { d: `${rekor} gün`, label: `Rekor · ${kaldi(rekor)} gün`, bg: color.paper.subtle2, border: '2px dashed #DED6C8', dColor: color.ink.muted, icon: <MedalIcon />, conn: color.paper.border },
    { d: '30 gün', label: `${kaldi(30)} gün kaldı`, bg: color.paper.subtle2, border: '2px dashed #DED6C8', dColor: color.ink.muted, icon: <CrownFill />, conn: null },
  ];

  return (
    <div style={{ animation: reduced ? undefined : 'seriEntrance 0.5s ease both' }}>
      {/* BLOK 1 — Hero seri + Bu hafta */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: dar ? '1fr' : '300px minmax(0, 1fr)',
          gap: 18, marginBottom: 18,
        }}
      >
        {/* Amber seri hero */}
        <div
          style={{
            background: 'linear-gradient(150deg,#7C2D12 0%,#B5701A 55%,#C77A1E 100%)',
            borderRadius: 20, padding: 26, color: '#fff', textAlign: 'center', boxSizing: 'border-box',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'center', lineHeight: 1 }}>
            <FlameFill size={56} fill="#FFE4D0" />
          </div>
          <div style={{ ...numText, fontSize: 54, fontWeight: 800, lineHeight: 1.05, marginTop: 6 }}>{seri}</div>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#FFE4D0' }}>günlük seri</div>
          <div
            style={{
              marginTop: 12, display: 'inline-flex', gap: 6, alignItems: 'center',
              background: 'rgba(255,255,255,0.16)', padding: '6px 13px', borderRadius: 99,
              fontSize: 12, fontWeight: 700, boxSizing: 'border-box',
            }}
          >
            <span style={numText}>En uzun · {rekor} gün</span>
          </div>
          <PrimaryLink
            href="/kutlama?type=seri"
            variant="amberHero"
          >
            <SparkleIcon />
            Seriyi kutla
          </PrimaryLink>
        </div>

        {/* Bu hafta */}
        <div
          style={{
            background: color.paper.card, border: `1px solid ${color.paper.border}`,
            borderRadius: 20, padding: 24, boxSizing: 'border-box',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
            <div style={{ fontSize: 16, fontWeight: 800 }}>Bu hafta</div>
            {donmusGun ? (
              <div style={{ fontSize: 12, fontWeight: 700, color: color.ink.muted }}>{donmusGun} günü dondurma kurtardı</div>
            ) : null}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
            {hafta.map((d, i) => {
              const kutuBg = d.durum === 'freeze' ? BUZ.bg : d.durum === 'today' ? color.paper.card : '#FBF0DE';
              const kutuBorder = d.durum === 'today' ? `2px solid ${color.dawn.coral}` : 'none';
              const etiketRenk = d.durum === 'freeze' ? BUZ.ink : d.durum === 'today' ? color.dawn.coralTextOnLight : color.ink.muted;
              return (
                <div key={`${d.label}-${i}`} style={{ flex: 1, textAlign: 'center', minWidth: 0 }}>
                  <div
                    role="img"
                    aria-label={karoLabel(d)}
                    style={{
                      width: '100%', aspectRatio: '1', maxWidth: 50, margin: '0 auto',
                      borderRadius: 13, background: kutuBg, border: kutuBorder,
                      display: 'flex', alignItems: 'center', justifyContent: 'center', boxSizing: 'border-box',
                    }}
                  >
                    {d.durum === 'done' ? <FlameFill size={20} fill="#E0593F" /> : null}
                    {d.durum === 'freeze' ? <KristalIcon size={22} /> : null}
                  </div>
                  <div style={{ fontSize: 11, fontWeight: 700, color: etiketRenk, marginTop: 7 }}>{d.label}</div>
                </div>
              );
            })}
          </div>

          {/* Lejant */}
          <div style={{ marginTop: 16, display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: 11.5, fontWeight: 600, color: color.ink.muted }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}><FlameFill size={15} fill="#E0593F" />Tamamlandı</span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <span aria-hidden style={{ width: 13, height: 13, borderRadius: 4, background: BUZ.bg, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', boxSizing: 'border-box' }}><ShieldMini /></span>
              Dondurma
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <span aria-hidden style={{ width: 13, height: 13, borderRadius: 4, border: `2px solid ${color.dawn.coral}`, display: 'inline-block', boxSizing: 'border-box' }} />
              Bugün
            </span>
          </div>
        </div>
      </div>

      {/* BLOK 2 — Seri Dondurma + Nudge önizleme */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: dar ? '1fr' : 'minmax(0, 1fr) minmax(0, 1fr)',
          gap: 18, marginBottom: 18,
        }}
      >
        {/* Seri Dondurma kartı */}
        <div
          style={{
            background: color.paper.card, border: `1px solid ${color.paper.border}`,
            borderRadius: 18, padding: 22, boxSizing: 'border-box',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 11, marginBottom: 14 }}>
            <span
              aria-hidden
              style={{
                width: 42, height: 42, flexShrink: 0, borderRadius: 12, background: BUZ.bg,
                display: 'flex', alignItems: 'center', justifyContent: 'center', boxSizing: 'border-box',
              }}
            >
              <FreezeBadgeIcon />
            </span>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: 16, fontWeight: 800 }}>Seri Dondurma</div>
              <div style={{ fontSize: 12, color: color.ink.muted, fontWeight: 600 }}>affedicilik mekanizması</div>
            </div>
            <div style={{ marginLeft: 'auto', textAlign: 'center' }}>
              <div aria-hidden style={{ ...numText, fontSize: 24, fontWeight: 800, color: BUZ.ink, lineHeight: 1 }}>{dondurmaHak}</div>
              <div aria-hidden style={{ fontSize: 10.5, color: color.ink.muted, fontWeight: 700 }}>hakkın</div>
              <span style={srOnly}>{dondurmaHak} dondurma hakkın kaldı</span>
            </div>
          </div>
          <p style={{ margin: 0, fontSize: 13.5, color: color.ink.secondary, lineHeight: 1.6 }}>
            Bir gün kaçırırsan serin <strong>sıfırlanmaz</strong> — dondurma otomatik devreye girer.{' '}
            <span style={{ fontFamily: font.serif, fontStyle: 'italic', fontSize: 15.5, color: color.ink.primary }}>
              Kötü bir gün, ayların emeğini silmesin.
            </span>
          </p>
        </div>

        {/* Nudge önizleme (yalnız insani ton — statik) */}
        <div
          style={{
            background: color.paper.card, border: `1.5px solid ${color.paper.border}`,
            borderRadius: 18, padding: 22, boxSizing: 'border-box',
          }}
        >
          <div style={{ marginBottom: 14 }}>
            <span
              style={{
                fontSize: 11, fontWeight: 800, color: color.dawn.coralTextOnLight,
                background: '#FFF3EE', padding: '4px 10px', borderRadius: 7, boxSizing: 'border-box',
              }}
            >
              İNSANİ NUDGE
            </span>
          </div>
          <ChatBubble role="ai">
            Bugün son bir adım kaldı — serini koru. Acelesi yok, sana uygun bir saatte hallederiz.
          </ChatBubble>
          <div style={{ marginTop: 9, fontSize: 11.5, color: color.ink.muted, lineHeight: 1.5 }}>
            Günde en fazla 1 nazik hatırlatma. İstediğin an kapatabilirsin.
          </div>
        </div>
      </div>

      {/* BLOK 3 — Kilometre taşları */}
      <div
        style={{
          background: color.paper.card, border: `1px solid ${color.paper.border}`,
          borderRadius: 18, padding: 22, marginBottom: 18, boxSizing: 'border-box',
        }}
      >
        <div style={{ fontSize: 16, fontWeight: 800, marginBottom: 16 }}>Kilometre taşları</div>
        <div style={{ display: 'flex', alignItems: 'flex-start', flexWrap: 'wrap', rowGap: 16 }}>
          {MILES.map((m, i) => (
            <div key={m.label} style={{ display: 'flex', alignItems: 'center' }}>
              <div style={{ textAlign: 'center', width: 92, flexShrink: 0 }}>
                <div
                  style={{
                    width: 54, height: 54, margin: '0 auto', borderRadius: 16, background: m.bg,
                    border: m.border, display: 'flex', alignItems: 'center', justifyContent: 'center', boxSizing: 'border-box',
                  }}
                >
                  {m.icon}
                </div>
                <div style={{ ...numText, fontSize: 13, fontWeight: 800, color: m.dColor, marginTop: 8 }}>{m.d}</div>
                <div style={{ fontSize: 11, color: color.ink.muted, fontWeight: 600 }}>{m.label}</div>
              </div>
              {!dar && m.conn && i < MILES.length - 1 ? (
                <div aria-hidden style={{ width: 32, height: 3, borderRadius: 2, background: m.conn, margin: '0 6px 30px' }} />
              ) : null}
            </div>
          ))}
        </div>
      </div>

      {/* BLOK 4 — CTA bandı (beyaz-metin coral, AA) */}
      <div
        style={{
          background: color.dawn.coralCtaBg, borderRadius: 18, padding: '22px 26px',
          display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap',
          color: '#fff', boxSizing: 'border-box',
        }}
      >
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 18, fontWeight: 800 }}>
            Bugünü tamamla, seriyi <span style={numText}>{seriNext}</span>&apos;e taşı
          </div>
          <div style={{ fontSize: 13, color: 'rgba(255,240,232,0.88)', marginTop: 3 }}>
            Sadece 1 ders veya 10 soru yeterli — acelesi yok.
          </div>
        </div>
        <PrimaryLink href="/soru-cozme" variant="whiteOnCoral">Bugünü tamamla</PrimaryLink>
      </div>
    </div>
  );
}

/** İç link — hit ≥44; üç varyant: sayfa (paper coral), amberHero (hero içi), whiteOnCoral (CTA bandı). */
function PrimaryLink({
  href, children, variant = 'paper',
}: {
  href: string;
  children: React.ReactNode;
  variant?: 'paper' | 'amberHero' | 'whiteOnCoral';
}): React.ReactElement {
  const base: React.CSSProperties = {
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 8,
    minHeight: 44, borderRadius: 12, fontFamily: font.sans, fontSize: 13.5, fontWeight: 800,
    textDecoration: 'none', boxSizing: 'border-box', whiteSpace: 'nowrap',
  };
  const skin: React.CSSProperties =
    variant === 'amberHero'
      ? { marginTop: 16, width: '100%', padding: '0 16px', background: 'rgba(255,255,255,0.95)', color: color.semantic.riskTextOnLight }
      : variant === 'whiteOnCoral'
        ? { padding: '0 22px', fontSize: 14, background: color.paper.card, color: color.dawn.coralTextOnLight }
        : { padding: '0 20px', fontSize: 14, background: color.dawn.coralCtaBg, color: '#fff' };
  return (
    <a href={href} style={{ ...base, ...skin }}>
      {children}
    </a>
  );
}

/** Yükleme iskeleti — hero + bu hafta + kartlar. */
function Iskelet({ dar }: { dar: boolean }): React.ReactElement {
  return (
    <div aria-busy="true" aria-label="Seri bilgisi yükleniyor">
      <div style={{ display: 'grid', gridTemplateColumns: dar ? '1fr' : '300px minmax(0, 1fr)', gap: 18, marginBottom: 18 }}>
        <div style={{ padding: 22, background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 20, boxSizing: 'border-box' }}>
          <Skeleton shape="card" delayMs={0} slowAfterMs={null} />
        </div>
        <div style={{ padding: 22, background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 20, boxSizing: 'border-box' }}>
          <Skeleton shape="card" delayMs={0} slowAfterMs={null} />
        </div>
      </div>
      <div style={{ padding: 22, background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 18, boxSizing: 'border-box' }}>
        <Skeleton shape="card" delayMs={0} slowAfterMs={null} />
      </div>
    </div>
  );
}

export default SeriDondurmaPage;
