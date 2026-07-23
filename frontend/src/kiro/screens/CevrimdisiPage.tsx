// ============================================================================
// KIRO2 — Çevrimdışı / Senkron (SPRINT10-A · KIRO2 Cevrimdisi.dc.html)
// Tema = PAPER (öğrenci durum yüzeyi; rol=öğrenci → SEN dili). SideNav(solve) +
// tam-genişlik bağlantı durum bandı (ConnectivityState) + iki-sütun (1.4fr/1fr):
// sol "Cihazında hazır" paket listesi (CachedPack) · sağ "Eşitleme kuyruğu"
// (SyncQueueItem) + "Bağlantı bekliyor" (bağlantı gerektiren yüzeyler, DC statik).
//
// Bağlantı durumu ekran-YEREL: navigator.onLine + window online/offline event
// (SyncStatus alanı DEĞİL). MANUEL toggle YOK (DC'deki "Tweaks" meta-notu kopya
// değil). Veri getCevrimdisiDurum() → SyncStatus (son eşitleme + kuyruk + paketler).
//
// KOPYA: DC birebir (kaygı-duyarlı, absence-dili yok). AA override: DC #17936B
// yeşil metni açık-yeşil zeminde AA geçmez → successTextOnLight #047857.
// ============================================================================
import * as React from 'react';

import { configureKiroApi, getCevrimdisiDurum, getMe } from '../api/api-client';
import type { MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';
import { color, font } from '../tokens';
import type { CachedPack, ConnectivityState, Persona, SyncQueueItem, SyncStatus } from '../types';
import { KiroThemeProvider, numText } from '../ui/theme';
import { EmptyState } from '../ui/EmptyState';
import { ErrorState } from '../ui/ErrorState';
import { Skeleton } from '../ui/Skeleton';
import { SideNav } from '../ui/SideNav';
import '../tokens/tokens.css';

configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });

const ACCENT = color.dawn.coralCtaBg; // #C2452B — beyaz-metin coral CTA (paper AA-güvenli)
const GREEN = color.semantic.successTextOnLight; // #047857 — açık-yeşil zeminde AA metin (DC #17936B override)
const GREEN_TINT = '#E4F7F0'; // yeşil şerit zemini (paper)

// --- Bağlantı durum bandı renkleri (DC bant tablosuyla birebir; connected fg AA override) ---
const BANT: Record<ConnectivityState, { bg: string; border: string; nokta: string; fg: string; baslik: string; alt: string }> = {
  cevrimdisi: {
    bg: color.semantic.riskBgSoft, border: color.semantic.riskBorderSoft, nokta: color.semantic.risk, fg: color.semantic.riskTextOnLight,
    baslik: 'Çevrimdışısın', alt: '— sorun değil, çalışman cihazında sürüyor.',
  },
  yeniden_baglaniyor: {
    bg: '#FFF3EE', border: '#F6D9CB', nokta: color.dawn.coral2, fg: color.dawn.coralTextOnLight,
    baslik: 'Yeniden bağlanıyor…', alt: 'çalışmaya devam edebilirsin, kesinti hissetmezsin.',
  },
  baglandi: {
    bg: GREEN_TINT, border: '#BEE9D9', nokta: color.semantic.success, fg: GREEN,
    baslik: 'Bağlantı geldi', alt: '— her şey eşitlendi, kuyruk boş.',
  },
};

// --- Paket türü → paper-güvenli aksan + rota (bespoke ikon rengi) ---
const PACK_RENK: Record<string, string> = {
  plan: color.subject.light.mat, // #3B82F6 mavi
  tekrar: color.dawn.coralTextOnLight, // #C2452B coral
  soru: color.semantic.riskTextOnLight, // #9A5D0D amber
  video: color.ink.muted, // nötr (hazır değil)
};
const PACK_ROTA: Record<string, string> = { plan: '/plan', tekrar: '/tekrar', soru: '/soru-cozme', video: '' };

// --- Bağlantı bekleyen yüzeyler (DC statik; canlı sıralama/AI bağlantı ister) ---
const BEKLEYEN: { ad: string; meta: string }[] = [
  { ad: 'KIRO Koç (AI)', meta: 'canlı yanıt ister' },
  { ad: 'Lig & Düello', meta: 'canlı sıralama' },
  { ad: 'Yeni paket indirme', meta: 'bağlantı ister' },
];

// ---------------------------------------------------------------------------
// Bespoke inline SVG ikonlar (emoji/stok-lib YOK)
// ---------------------------------------------------------------------------
function IndirIkon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={GREEN} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M12 3v12" /><polyline points="7 10 12 15 17 10" /><path d="M5 21h14" />
    </svg>
  );
}
function PackIkon({ tur }: { tur: string }) {
  const c = PACK_RENK[tur] ?? color.ink.muted;
  const stroke = { fill: 'none' as const, stroke: c, strokeWidth: 1.9, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };
  if (tur === 'plan') return <svg width="18" height="18" viewBox="0 0 24 24" {...stroke} aria-hidden><rect x="3" y="4" width="18" height="17" rx="2" /><path d="M3 9h18M8 2v4M16 2v4" /><path d="m8 14 2.4 2.4L15 12" /></svg>;
  if (tur === 'tekrar') return <svg width="18" height="18" viewBox="0 0 24 24" {...stroke} aria-hidden><path d="M3 12a9 9 0 0 1 15-6.6L21 8" /><path d="M21 4v4h-4" /><path d="M21 12a9 9 0 0 1-15 6.6L3 16" /><path d="M3 20v-4h4" /></svg>;
  if (tur === 'soru') return <svg width="18" height="18" viewBox="0 0 24 24" {...stroke} aria-hidden><path d="M9 11l3 3 8-8" /><path d="M20 12v6a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h9" /></svg>;
  // video (hazır değil)
  return <svg width="18" height="18" viewBox="0 0 24 24" {...stroke} aria-hidden><rect x="3" y="5" width="18" height="14" rx="2.4" /><path d="m10 9 5 3-5 3Z" /></svg>;
}
function SaatIkon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color.ink.faded2} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }} aria-hidden>
      <circle cx="12" cy="12" r="9" /><polyline points="12 7 12 12 15 14" />
    </svg>
  );
}
function BulutIkon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke={color.ink.muted} strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }} aria-hidden>
      <path d="M17.5 19a4.5 4.5 0 1 0-1.03-8.88A6 6 0 0 0 5 12.5 3.5 3.5 0 0 0 6.5 19Z" />
    </svg>
  );
}

// SideNav DC'de ≤1060px'te tamamen gizlenir (width:0) + iki-sütun tek sütun olur.
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

// ---------------------------------------------------------------------------
// Alt bileşenler
// ---------------------------------------------------------------------------
const sectionStil: React.CSSProperties = {
  boxSizing: 'border-box', minWidth: 0, background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 18,
};

function PaketSatiri({ p }: { p: CachedPack }) {
  const c = PACK_RENK[p.tur] ?? color.ink.muted;
  const govde = (
    <>
      <span aria-hidden style={{ width: 38, height: 38, flexShrink: 0, borderRadius: 11, background: c + '1A', color: c, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <PackIkon tur={p.tur} />
      </span>
      <span style={{ flex: 1, minWidth: 0 }}>
        <span style={{ display: 'block', fontSize: 13.5, fontWeight: 700, color: color.ink.primary }}>{p.baslik}</span>
        <span style={{ display: 'block', fontSize: 12, color: color.ink.muted, marginTop: 1 }}>{p.aciklama}</span>
      </span>
    </>
  );

  if (p.hazir) {
    return (
      <a
        href={PACK_ROTA[p.tur] || '#'}
        aria-label={`${p.baslik} — başla`}
        style={{ boxSizing: 'border-box', display: 'flex', alignItems: 'center', gap: 13, padding: '13px 14px', border: `1px solid ${color.paper.border}`, borderRadius: 13, textDecoration: 'none', color: color.ink.primary }}
      >
        {govde}
        <span aria-hidden style={{ flexShrink: 0, display: 'inline-flex', alignItems: 'center', height: 34, padding: '0 15px', borderRadius: 10, background: ACCENT, color: '#fff', fontSize: 12.5, fontWeight: 700 }}>Başla</span>
      </a>
    );
  }
  // Hazır değil (konu videoları) — bağlantı bekler; "Başla" yok, nötr durum çipi.
  return (
    <div style={{ boxSizing: 'border-box', display: 'flex', alignItems: 'center', gap: 13, padding: '13px 14px', border: `1px solid ${color.paper.borderFaint}`, borderRadius: 13, background: color.paper.subtle }}>
      {govde}
      <span style={{ flexShrink: 0, display: 'inline-flex', alignItems: 'center', gap: 6, height: 34, padding: '0 12px', borderRadius: 10, background: color.paper.card, border: `1px solid ${color.paper.border}`, color: color.ink.muted, fontSize: 12, fontWeight: 700 }}>
        <BulutIkon /> Sırada
      </span>
    </div>
  );
}

function KuyrukSatiri({ q }: { q: SyncQueueItem }) {
  const durumLabel = q.durum === 'esitleniyor' ? 'eşitleniyor…' : 'bekliyor';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
      <SaatIkon />
      <span style={{ ...numText, flex: 1, minWidth: 0, fontSize: 12.5, fontWeight: 600, color: color.ink.secondary }}>{q.baslik}</span>
      <span style={{ flexShrink: 0, fontSize: 11.5, fontWeight: 700, color: color.ink.muted }}>{durumLabel}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
export interface CevrimdisiPageProps {
  /** Storybook/test için bağlantı durumunu sabitler; canlıda navigator.onLine + event belirler. */
  durumBaslangic?: ConnectivityState;
}

export function CevrimdisiPage({ durumBaslangic }: CevrimdisiPageProps = {}): React.ReactElement {
  const gizli = useMedia('(max-width: 1060px)'); // SideNav gizli + tek sütun

  // --- Bağlantı durumu: ekran-yerel (navigator.onLine + online/offline event) ---
  const [durum, setDurum] = React.useState<ConnectivityState>(() => {
    if (durumBaslangic) return durumBaslangic;
    if (typeof navigator !== 'undefined' && 'onLine' in navigator) return navigator.onLine ? 'baglandi' : 'cevrimdisi';
    return 'cevrimdisi';
  });
  const reconnectTimer = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  React.useEffect(() => {
    if (durumBaslangic) return; // sabitlenmiş (story/test) — canlı event dinlemez
    const gitti = () => setDurum('cevrimdisi');
    const geldi = () => {
      setDurum('yeniden_baglaniyor'); // kısa eşitleme fazı, sonra bağlandı
      reconnectTimer.current = setTimeout(() => setDurum('baglandi'), 1600);
    };
    window.addEventListener('offline', gitti);
    window.addEventListener('online', geldi);
    return () => {
      window.removeEventListener('offline', gitti);
      window.removeEventListener('online', geldi);
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
    };
  }, [durumBaslangic]);

  // --- Veri: senkron durumu + persona (nav) ---
  const [persona, setPersona] = React.useState<Persona | null>(null);
  const [veri, setVeri] = React.useState<SyncStatus | null>(null);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);

  React.useEffect(() => {
    let alive = true;
    setVeri(null);
    setHata(false);
    // Persona (nav) İKİNCİL: hatası ekranı düşürmez → SideNav fallback "Öğrenci".
    getMe()
      .catch(() => null)
      .then((p) => {
        if (alive) setPersona(p);
      });
    // Çevrimdışı durumu BİRİNCİL: hatası ErrorState'i tetikler.
    getCevrimdisiDurum()
      .then((s) => {
        if (alive) setVeri(s);
      })
      .catch(() => {
        if (alive) setHata(true);
      });
    return () => {
      alive = false;
    };
  }, [yeniden]);

  const b = BANT[durum];
  const heroBaslik = durum === 'baglandi' ? 'Hoş geldin — kaldığın yerdeyiz.' : 'İnternet gitti. Çalışman gitmedi.';
  const paketler = veri?.paketler ?? [];
  const kuyruk = veri?.kuyruk ?? [];

  return (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={{ boxSizing: 'border-box', minHeight: '100vh', width: '100%', overflowX: 'hidden', display: 'flex', background: color.paper.bg, fontFamily: font.sans, color: color.ink.primary }}>
        {!gizli && (
          <SideNav role="ogrenci" activeId="solve" userName={persona?.ad ?? 'Öğrenci'} userSub={persona?.sinif ?? ''} onAssistant={() => undefined} />
        )}

        <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
          {/* Bağlantı durum bandı — tam genişlik (risk=amber / reconnect=dawn / bağlandı=success; kırmızı YOK) */}
          <div
            role="status"
            style={{ boxSizing: 'border-box', display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', padding: '11px 30px', background: b.bg, borderBottom: `1px solid ${b.border}` }}
          >
            <span aria-hidden style={{ width: 9, height: 9, flexShrink: 0, borderRadius: 99, background: b.nokta }} />
            <span style={{ fontSize: 13, fontWeight: 700, color: b.fg }}>{b.baslik}</span>
            <span style={{ fontSize: 12.5, fontWeight: 500, color: b.fg }}>{b.alt}</span>
            <span style={{ flex: 1 }} />
            {veri && (
              <span style={{ ...numText, fontSize: 12, fontWeight: 600, color: b.fg }}>Son eşitleme: {veri.sonEsitleme}</span>
            )}
          </div>

          <main style={{ boxSizing: 'border-box', width: '100%', maxWidth: 1060, padding: '30px 30px 60px', display: 'flex', flexDirection: 'column', gap: 22 }}>
            <header>
              <h1 style={{ margin: '0 0 6px', fontFamily: font.serif, fontStyle: 'italic', fontWeight: 400, fontSize: 32, lineHeight: 1.1 }}>{heroBaslik}</h1>
              <p style={{ margin: 0, fontSize: 14, color: color.ink.muted, maxWidth: 560, lineHeight: 1.5 }}>
                Çalışman cihazında güvende — çözdüğün her soru kaydedilir, bağlantı gelince kendiliğinden eşitlenir. Hiçbir şey kaybolmaz.
              </p>
            </header>

            {hata ? (
              <ErrorState
                serifTitle="Çevrimdışı durumu şu an gelmedi."
                body="Sorun sende değil — çalışman ve eşitleme kuyruğun güvende. Birazdan yeniden dene."
                onRetry={() => setYeniden((n) => n + 1)}
              />
            ) : veri === null ? (
              <div aria-busy="true" aria-label="Çevrimdışı durumu yükleniyor" style={{ ...sectionStil, padding: 22, display: 'flex', flexDirection: 'column', gap: 12 }}>
                {[0, 1, 2].map((i) => (
                  <Skeleton key={i} shape="row" delayMs={0} slowAfterMs={null} />
                ))}
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: gizli ? '1fr' : '1.4fr 1fr', gap: 18, alignItems: 'start' }}>
                {/* SOL — Cihazında hazır */}
                <section style={{ ...sectionStil, padding: 22 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 9, flexWrap: 'wrap', marginBottom: 16 }}>
                    <span aria-hidden style={{ width: 30, height: 30, flexShrink: 0, borderRadius: 9, background: GREEN_TINT, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <IndirIkon />
                    </span>
                    <h2 style={{ margin: 0, fontSize: 16, fontWeight: 800 }}>Cihazında hazır</h2>
                    <span style={{ fontSize: 11, fontWeight: 800, letterSpacing: '0.05em', color: GREEN, background: GREEN_TINT, borderRadius: 99, padding: '3px 9px', textTransform: 'uppercase' }}>Çevrimdışı çalışır</span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {paketler.map((p) => (
                      <PaketSatiri key={p.id} p={p} />
                    ))}
                  </div>
                  <p style={{ margin: '14px 0 0', fontSize: 12, color: color.ink.muted, lineHeight: 1.55 }}>
                    Paketler sen çevrimiçiyken kendiliğinden indirilir: sıradaki plan görevin + bugünkü tekrar kartların her zaman hazır tutulur.
                  </p>
                </section>

                {/* SAĞ — Eşitleme kuyruğu + Bağlantı bekliyor */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 18, minWidth: 0 }}>
                  <section style={{ ...sectionStil, padding: 20 }}>
                    <h2 style={{ margin: '0 0 12px', fontSize: 14, fontWeight: 800 }}>Eşitleme kuyruğu</h2>
                    {kuyruk.length === 0 ? (
                      <EmptyState serifTitle="Bağlantı bekleyen bir şey yok" body="Her şey eşitlendi — kuyruğun tertemiz." />
                    ) : (
                      <>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                          {kuyruk.map((q) => (
                            <KuyrukSatiri key={q.id} q={q} />
                          ))}
                        </div>
                        <div style={{ boxSizing: 'border-box', marginTop: 13, padding: '10px 12px', background: color.paper.subtle, border: `1px dashed ${color.paper.borderStrong}`, borderRadius: 10, fontSize: 12, color: color.ink.muted, lineHeight: 1.55 }}>
                          Bağlantı gelince bu liste kendiliğinden boşalır — senin bir şey yapman gerekmez.
                        </div>
                      </>
                    )}
                  </section>

                  <section style={{ ...sectionStil, padding: 20 }}>
                    <h2 style={{ margin: '0 0 4px', fontSize: 14, fontWeight: 800, color: color.ink.muted }}>Bağlantı bekliyor</h2>
                    <p style={{ margin: '0 0 12px', fontSize: 12, color: color.ink.muted }}>Geri gelince burada olacaklar.</p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
                      {BEKLEYEN.map((x) => (
                        <div key={x.ad} style={{ boxSizing: 'border-box', display: 'flex', alignItems: 'center', gap: 10, padding: '9px 11px', border: `1px solid ${color.paper.borderFaint}`, borderRadius: 11, background: color.paper.subtle }}>
                          <BulutIkon />
                          <span style={{ flex: 1, minWidth: 0, fontSize: 12.5, fontWeight: 700, color: color.ink.muted }}>{x.ad}</span>
                          <span style={{ flexShrink: 0, fontSize: 11, fontWeight: 600, color: color.ink.muted }}>{x.meta}</span>
                        </div>
                      ))}
                    </div>
                  </section>
                </div>
              </div>
            )}
          </main>
        </div>
      </div>
    </KiroThemeProvider>
  );
}

export default CevrimdisiPage;
