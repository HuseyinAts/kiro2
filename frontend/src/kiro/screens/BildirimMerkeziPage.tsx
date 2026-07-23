// ============================================================================
// KIRO2 — Bildirim Merkezi (SPRINT10-A · Grup 8 · KIRO2 Bildirim Merkezi.dc.html)
// Tema = PAPER (öğrenci → SEN; route-bazlı, toggle YOK).
// Kilit kopya (başlık/pil/boş-durum/dipnot) DC'den BİREBİR. Bildirim satır kopyası
// paylaşılan mock sözleşmesinden (BildirimYanit) gelir — DC'nin örnek metninden
// bilerek ayrışır (server-otoriter içerik). Zayıf-konu tonu AMBER (kanon>DC).
// Veri: configureKiroApi mock → getMe + getBildirimler; mutasyonlar optimistik.
// ============================================================================
import * as React from 'react';

import {
  clearBildirimler,
  configureKiroApi,
  getBildirimler,
  getMe,
  markBildirimOkundu,
  markTumBildirimOkundu,
} from '../api/api-client';
import type { MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';
import { color, font } from '../tokens';
import type { Bildirim, BildirimTon, Persona } from '../types';
import { KiroThemeProvider, numText } from '../ui/theme';
import { Button } from '../ui/Button';
import { EmptyState } from '../ui/EmptyState';
import { ErrorState } from '../ui/ErrorState';
import { Skeleton } from '../ui/Skeleton';
import { SideNav } from '../ui/SideNav';
import '../tokens/tokens.css';

configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });

// Ton → açık-zemin renk + bespoke ikon eşlemesi (risk = amber; alarm-kırmızısı YOK).
// coral = kanon coralTextOnLight (#C2452B, AA); violet = Fizik mor'u (#8B5CF6).
const TON: Record<BildirimTon, { c: string; bg: string; icon: string }> = {
  teal: {
    c: color.semantic.success, bg: color.semantic.successBgSoft,
    icon: 'M3 12a9 9 0 0 1 15-6.6L21 8M21 4v4h-4M21 12a9 9 0 0 1-15 6.6L3 16M3 20v-4h4',
  },
  amber: {
    c: color.semantic.riskTextOnLight, bg: color.semantic.riskBgSoft,
    icon: 'M12 3a9 9 0 1 0 9 9M12 7a5 5 0 1 0 5 5M12 12h9',
  },
  coral: {
    c: color.dawn.coralTextOnLight, bg: '#FFF3EE',
    icon: 'M13 2 4 14h7l-1 8 9-12h-7l1-8Z',
  },
  gold: {
    c: '#C99A2E', bg: color.paper.subtle2,
    icon: 'M12 2c1.4 3.4 4.4 4.6 4.4 8.2a4.4 4.4 0 0 1-8.8.2c0-1.6.6-2.8 1.3-3.6.2 1.2 1 1.9 1.8 1.9C10.2 6.6 11 4.2 12 2Z',
  },
  violet: {
    c: color.subject.light.fiz, bg: '#F5F3FF',
    icon: 'M12 15a6 6 0 1 0 0-12 6 6 0 0 0 0 12ZM8.2 13.5 7 22l5-3 5 3-1.2-8.5',
  },
  blue: {
    c: color.subject.light.mat, bg: '#EFF6FF',
    icon: 'M3 3v18h18M7 14l3-3 3 3 5-6',
  },
};

const srOnly: React.CSSProperties = {
  position: 'absolute', width: 1, height: 1, padding: 0, margin: -1,
  overflow: 'hidden', clip: 'rect(0 0 0 0)', whiteSpace: 'nowrap', border: 0,
};

function CheckIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}
function TrashIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
    </svg>
  );
}

function TonBadge({ ton }: { ton: BildirimTon }) {
  const t = TON[ton] ?? TON.teal;
  return (
    <span aria-hidden style={{ width: 40, height: 40, flexShrink: 0, borderRadius: 12, background: t.bg, boxSizing: 'border-box', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={t.c} strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
        <path d={t.icon} />
      </svg>
    </span>
  );
}

function NotifRow({ b, ilk, onRead }: { b: Bildirim; ilk: boolean; onRead: (id: string) => void }) {
  const [hover, setHover] = React.useState(false);
  const okunmadi = !b.okundu;
  const bg = hover ? color.paper.subtle : okunmadi ? '#FFFBF9' : color.paper.card;
  return (
    <li style={{ listStyle: 'none' }}>
      <button
        type="button"
        onClick={() => onRead(b.id)}
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
        style={{
          width: '100%', boxSizing: 'border-box', textAlign: 'left', cursor: 'pointer',
          display: 'flex', alignItems: 'flex-start', gap: 14, padding: '16px 18px',
          background: bg, border: 'none', borderTop: ilk ? 'none' : `1px solid ${color.paper.borderFaint}`,
          font: 'inherit', color: 'inherit',
        }}
      >
        <TonBadge ton={b.ton} />
        <span style={{ flex: 1, minWidth: 0, display: 'block' }}>
          <span style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{ ...numText, flex: '1 1 auto', minWidth: 0, fontSize: 14, fontWeight: okunmadi ? 800 : 600, color: color.ink.primary }}>{b.baslik}</span>
            {okunmadi && <span aria-hidden style={{ flexShrink: 0, alignSelf: 'center', width: 8, height: 8, borderRadius: '50%', background: color.dawn.coralCtaBg }} />}
            <span style={{ ...numText, flexShrink: 0, fontSize: 11.5, fontWeight: 600, color: color.ink.muted, whiteSpace: 'nowrap' }}>{b.zaman}</span>
          </span>
          <span style={{ ...numText, display: 'block', marginTop: 3, fontSize: 12.5, lineHeight: 1.5, color: color.ink.muted }}>{b.aciklama}</span>
        </span>
        {okunmadi && <span style={srOnly}>okunmadı</span>}
      </button>
    </li>
  );
}

// SideNav ≤1023px'te 64px ikon rayına çöker — jsdom matchMedia'sız guard'lı.
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

export function BildirimMerkeziPage(): React.ReactElement {
  const dar = useDarEkran();
  const [persona, setPersona] = React.useState<Persona | null>(null);
  const [gruplar, setGruplar] = React.useState<{ baslik: string; items: Bildirim[] }[] | null>(null);
  const [okunmamis, setOkunmamis] = React.useState(0);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);

  React.useEffect(() => {
    let alive = true;
    setGruplar(null);
    setHata(false);
    // Persona ikincil: getMe hatası TÜM ekranı düşürmesin (nav "Öğrenci"e düşer).
    // getBildirimler birincil veri — reddi ErrorState'i tetikler.
    Promise.all([getMe().catch(() => null), getBildirimler()])
      .then(([p, b]) => {
        if (!alive) return;
        setPersona(p);
        setGruplar(b.gruplar);
        setOkunmamis(b.okunmamis);
      })
      .catch(() => {
        if (alive) setHata(true);
      });
    return () => {
      alive = false;
    };
  }, [yeniden]);

  // Optimistik: tek bildirimi okundu işaretle + sayacı bilinen delta ile düşür.
  const markRead = React.useCallback((id: string) => {
    setGruplar((prev) => {
      if (!prev) return prev;
      return prev.map((g) => ({ ...g, items: g.items.map((it) => (it.id === id ? { ...it, okundu: true } : it)) }));
    });
    setOkunmamis((n) => {
      const wasUnread = (gruplar ?? []).some((g) => g.items.some((it) => it.id === id && !it.okundu));
      return wasUnread ? Math.max(0, n - 1) : n;
    });
    void markBildirimOkundu(id);
  }, [gruplar]);

  const markAll = React.useCallback(() => {
    setGruplar((prev) => (prev ? prev.map((g) => ({ ...g, items: g.items.map((it) => ({ ...it, okundu: true })) })) : prev));
    setOkunmamis(0);
    void markTumBildirimOkundu().then((r) => setOkunmamis(r.okunmamis));
  }, []);

  const clear = React.useCallback(() => {
    setGruplar([]);
    setOkunmamis(0);
    void clearBildirimler();
  }, []);

  const hasGroups = gruplar !== null && gruplar.length > 0;

  return (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={{ minHeight: '100vh', boxSizing: 'border-box', background: color.paper.bg, display: 'flex', fontFamily: font.sans, color: color.ink.primary }}>
        <SideNav role="ogrenci" activeId="panel" collapsed={dar} userName={persona?.ad ?? 'Öğrenci'} userSub={persona?.sinif ?? ''} onAssistant={() => undefined} />

        <main style={{ flex: 1, minWidth: 0, boxSizing: 'border-box' }}>
          <header
            style={{
              position: 'sticky', top: 0, zIndex: 6, minHeight: 66, boxSizing: 'border-box',
              display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', rowGap: 8,
              padding: '10px 30px', background: 'rgba(250,247,242,0.86)', backdropFilter: 'blur(8px)',
              borderBottom: `1px solid ${color.paper.border}`,
            }}
          >
            <h1 style={{ margin: 0, fontSize: 18, fontWeight: 800, letterSpacing: '-0.02em' }}>Bildirimler</h1>
            {okunmamis > 0 && (
              <span style={{ ...numText, fontSize: 12, fontWeight: 800, color: '#fff', background: color.dawn.coralCtaBg, padding: '2px 9px', borderRadius: 999, boxSizing: 'border-box' }}>
                {`${okunmamis} yeni`}
              </span>
            )}
            <div style={{ flex: 1 }} />
            {hasGroups && !hata && (
              <>
                <Button variant="ghost" icon={<CheckIcon />} onClick={markAll} disabled={okunmamis === 0}>Tümünü okundu işaretle</Button>
                <Button variant="ghost" icon={<TrashIcon />} ariaLabel="Bildirimleri temizle" onClick={clear} />
              </>
            )}
          </header>

          <div style={{ maxWidth: 760, width: '100%', boxSizing: 'border-box', padding: '22px 30px 60px' }}>
            {hata ? (
              <ErrorState
                serifTitle="Bildirimlerin şu an gelmedi."
                body="Sorun sende değil — bağlantı bir soluklandı, çalışman ve ilerlemen güvende. Birazdan yeniden dene."
                onRetry={() => setYeniden((n) => n + 1)}
              />
            ) : gruplar === null ? (
              <div aria-busy="true" aria-label="Bildirimler yükleniyor" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                {[0, 1].map((gi) => (
                  <div key={gi} style={{ display: 'flex', flexDirection: 'column', gap: 10, boxSizing: 'border-box' }}>
                    <Skeleton width={90} height={11} />
                    <div style={{ background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 16, padding: '16px 18px', boxSizing: 'border-box' }}>
                      <Skeleton shape="card" delayMs={0} slowAfterMs={null} />
                    </div>
                  </div>
                ))}
              </div>
            ) : gruplar.length === 0 ? (
              <EmptyState
                icon={
                  <span aria-hidden style={{ width: 72, height: 72, borderRadius: 22, boxSizing: 'border-box', background: `linear-gradient(150deg, ${color.semantic.successBgSoft}, ${color.paper.bg})`, border: `1px solid ${color.semantic.successBorderSoft}`, display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
                    <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke={color.semantic.success} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
                      <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
                      <path d="m8 11 2.5 2.5L16 8" />
                    </svg>
                  </span>
                }
                serifTitle="Her şey sakin."
                body="Sıfır bildirim. Dikkatin dağılmadan, sakin kafayla çalışmaya dönebilirsin."
                action={<Button variant="primary" onClick={() => undefined}>Panele dön</Button>}
              />
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                {gruplar.map((g, gi) => {
                  const labelId = `bild-grup-${gi}`;
                  return (
                    <section key={g.baslik} aria-labelledby={labelId} style={{ boxSizing: 'border-box' }}>
                      <div id={labelId} style={{ fontSize: 11.5, fontWeight: 800, letterSpacing: '0.08em', color: color.ink.muted, textTransform: 'uppercase', margin: '0 4px 10px' }}>{g.baslik}</div>
                      <ul style={{ margin: 0, padding: 0, listStyle: 'none', background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 16, overflow: 'hidden', boxSizing: 'border-box' }}>
                        {g.items.map((b, i) => (
                          <NotifRow key={b.id} b={b} ilk={i === 0} onRead={markRead} />
                        ))}
                      </ul>
                    </section>
                  );
                })}
                <p style={{ margin: '4px 2px 0', fontSize: 12, color: color.ink.muted, textAlign: 'center', lineHeight: 1.5 }}>
                  Bildirimleri Ayarlar'dan kısabilirsin — sakin varsayılan, baskı yok.
                </p>
              </div>
            )}
          </div>
        </main>
      </div>
    </KiroThemeProvider>
  );
}

export default BildirimMerkeziPage;
