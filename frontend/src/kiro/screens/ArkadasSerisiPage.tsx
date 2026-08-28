// ============================================================================
// KIRO2 — Arkadaş Serisi (SPRINT8 · Grup 6 · KIRO2 Arkadas Serisi.dc.html)
// Tema = PAPER (çalışma/sosyal yüzey; route-bazlı, toggle YOK). Rota /arkadas-serisi.
// Kopya DC'den BİREBİR. Sunucu-otorite: ortakSeri/görev/arkadaş seri+xp+durum
// getFriends'ten; ekran puan/seri/xp HESAPLAMAZ (sıralama = yalnız görünüm düzeni).
// Kanon: "Arkadaş ekle" CTA coralCtaBg (#C2452B, AA) — DC'deki #FF6F5C değil;
// metin-tik glyph -> bespoke SVG tik + görünmez SR metni; risk=amber; rank NUMARASI YOK.
// [ONAY BEKLER] Empty/Error kopyası inferred; "Arkadaş ekle" hedef akışı DC'de yok (flag).
// Veri: configureKiroApi mock → getMe + getFriends (kiro-data.json).
// ============================================================================
import * as React from 'react';

import { getFriends, getMe, postFriendCongrats, postFriendNudge } from '../api/api-client';
import { useAyar } from '../lib/ayarStore';
import { color, font } from '../tokens';
import type { Friend, FriendsData, Persona } from '../types';
import {
  Button, EmptyState, ErrorState, KiroThemeProvider, numText, SegmentedControl,
  SideNav, Skeleton, useReducedMotion,
} from '../ui';
import '../tokens/tokens.css';

// +1 tebrik uçuşu (paper micro-motion) — HER animasyon reduced-motion guard'lı.
const KEYFRAMES = `@keyframes kiroCongratsFloat { 0%{transform:translateY(0);opacity:0;} 20%{opacity:1;} 100%{transform:translateY(-26px);opacity:0;} }`;

const srOnly: React.CSSProperties = {
  position: 'absolute', width: 1, height: 1, padding: 0, margin: -1,
  overflow: 'hidden', clip: 'rect(0 0 0 0)', whiteSpace: 'nowrap', border: 0,
};

// ---- Bespoke ikonlar (emoji YOK; metin glyph tik -> SVG tik + SR metni) ----
function Tik({ srText, c = 'currentColor', size = 13 }: { srText: string; c?: string; size?: number }) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center' }}>
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <path d="M20 6 9 17l-5-5" />
      </svg>
      <span style={srOnly}>{srText}</span>
    </span>
  );
}
function Alev({ c, size = 15 }: { c: string; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill={c} aria-hidden style={{ flexShrink: 0 }}>
      <path d="M12 2c1.4 3.4 4.4 4.6 4.4 8.2a4.4 4.4 0 0 1-8.8.2c0-1.6.6-2.8 1.3-3.6.2 1.2 1 1.9 1.8 1.9C10.2 6.6 11 4.2 12 2Z" />
    </svg>
  );
}
function Saat() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={color.semantic.riskTextOnLight} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <circle cx="12" cy="12" r="9" /><polyline points="12 7 12 12 15 14" />
    </svg>
  );
}
function UserPlus() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M19 8v6M22 11h-6" />
    </svg>
  );
}

// Çift-avatar: ui/Avatar backgroundColor-only → gradyan gerektiği için bespoke INLINE div.
function GradientAvatar({ gradient, label, size = 56 }: { gradient: string; label: string; size?: number }) {
  return (
    <div aria-hidden style={{
      width: size, height: size, flexShrink: 0, borderRadius: Math.round(size * 0.28),
      background: gradient, display: 'flex', alignItems: 'center', justifyContent: 'center',
      color: '#fff', fontWeight: 800, fontSize: Math.round(size * 0.32),
      border: '2px solid rgba(255,255,255,0.25)', boxSizing: 'border-box',
    }}>{label}</div>
  );
}

// Birlikte-görev çift-renk barı — WIDTH DEĞİL: iki katman transform:scaleX (statik).
// Konteyner role=progressbar (birleşik ilerleme). Segment renkleri dekoratif.
function CoopBar({ benPay, partnerPay, hedef, partner }: { benPay: number; partnerPay: number; hedef: number; partner: string }) {
  const h = Math.max(1, hedef);
  const benR = Math.max(0, Math.min(1, benPay / h));
  const totR = Math.max(0, Math.min(1, (benPay + partnerPay) / h));
  return (
    <div
      role="progressbar" aria-valuenow={benPay + partnerPay} aria-valuemin={0} aria-valuemax={hedef}
      aria-label={`Birlikte görev — sen ${benPay}, ${partner} ${partnerPay}, toplam ${benPay + partnerPay} / ${hedef} soru`}
      style={{ position: 'relative', height: 11, borderRadius: 999, background: color.paper.borderFaint, overflow: 'hidden', boxSizing: 'border-box' }}
    >
      {/* Partner katmanı (arkada) toplam'a kadar; Sen katmanı (önde) ben'e kadar → [ben,tot) partner rengi kalır */}
      <div aria-hidden style={{ position: 'absolute', inset: 0, background: '#EC4899', borderRadius: 999, transformOrigin: 'left', transform: `scaleX(${totR})` }} />
      <div aria-hidden style={{ position: 'absolute', inset: 0, background: color.dawn.coral, borderRadius: 999, transformOrigin: 'left', transform: `scaleX(${benR})` }} />
    </div>
  );
}

// SideNav ≤1023px'te 64px ikon rayına çöker; jsdom matchMedia'sız guard'lı.
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

interface Veri { persona: Persona; friends: FriendsData }
type SortKey = 'seri' | 'xp';

const STATUS_MAP: Record<Friend['durum'], { label: string; fg: string; bg: string; tik: boolean }> = {
  calisti: { label: 'çalıştı', fg: color.semantic.successTextOnLight, bg: color.semantic.successBgSoft, tik: true },
  henuz: { label: 'henüz değil', fg: color.semantic.riskTextOnLight, bg: color.semantic.riskBgSoft, tik: false },
};

function FriendRow({ f, gold, kompakt, sent, onCongrats, floating, reduced }: {
  f: Friend; gold: boolean; kompakt: boolean; sent: boolean;
  onCongrats: () => void; floating: boolean; reduced: boolean;
}) {
  const st = STATUS_MAP[f.durum];
  return (
    <li style={{ listStyle: 'none' }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: kompakt ? 10 : 14, padding: '13px 15px',
        borderRadius: 13, background: gold ? '#FFFBEB' : color.paper.card,
        border: `1px solid ${gold ? '#FDE68A' : color.paper.border}`, boxSizing: 'border-box',
      }}>
        <GradientAvatar gradient={f.avatarGradient} label={f.ini} size={44} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: color.ink.primary, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{f.ad}</div>
          <div style={{ fontSize: 12, color: color.ink.muted }}>{f.sinif}</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5, flexShrink: 0 }}>
          <Alev c={color.semantic.riskTextOnLight} />
          <span style={{ ...numText, fontSize: 14, fontWeight: 800, color: color.semantic.riskTextOnLight }}>{f.seri}</span>
          <span style={srOnly}>gün seri</span>
        </div>
        <div style={{ flexShrink: 0, textAlign: 'center' }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 11.5, fontWeight: 800, color: st.fg, background: st.bg, padding: '5px 11px', borderRadius: 8, boxSizing: 'border-box', whiteSpace: 'nowrap' }}>
            {st.label}{st.tik && <Tik srText="tamamlandı" c={st.fg} size={12} />}
          </span>
        </div>
        {!kompakt && (
          <div style={{ ...numText, width: 84, textAlign: 'right', fontSize: 13, fontWeight: 700, color: color.ink.secondary, flexShrink: 0 }}>
            {f.xp.toLocaleString('tr-TR')} XP
          </div>
        )}
        <button
          type="button" onClick={onCongrats} disabled={sent} aria-pressed={sent} aria-label={`${f.ad} için tebrik gönder`}
          style={{
            position: 'relative', width: 44, height: 44, flexShrink: 0, border: 'none', padding: 0,
            background: 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: sent ? 'default' : 'pointer', boxSizing: 'border-box',
          }}
        >
          <span style={{
            width: 36, height: 36, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center',
            border: `1px solid ${sent ? color.semantic.successBorderSoft : color.paper.border}`,
            background: sent ? color.semantic.successBgSoft : color.paper.card, boxSizing: 'border-box',
          }}>
            {sent ? (
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke={color.semantic.successTextOnLight} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M20 6 9 17l-5-5" /></svg>
            ) : (
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke={color.dawn.coralTextOnLight} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="m4 17 4-9 4 6 4-9 4 12" /></svg>
            )}
          </span>
          {floating && !reduced && (
            <span aria-hidden style={{ ...numText, position: 'absolute', top: -14, right: -4, fontSize: 13, fontWeight: 800, color: '#17936B', whiteSpace: 'nowrap', animation: 'kiroCongratsFloat 1s ease-out forwards' }}>+1</span>
          )}
        </button>
      </div>
    </li>
  );
}

export function ArkadasSerisiPage(): React.ReactElement {
  const reduced = useReducedMotion();
  // Sakin mod: seri-dürtme baskısını sustur (nudge CTA gizlenir). Congrats KORUNUR.
  const calmMode = useAyar((s) => s.calmMode);
  const dar = useMedia('(max-width: 1023px)');
  const kompakt = useMedia('(max-width: 560px)');

  const [veri, setVeri] = React.useState<Veri | null>(null);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);

  const [sortBy, setSortBy] = React.useState<SortKey>('seri');
  const [nudged, setNudged] = React.useState(false);
  const [sentSet, setSentSet] = React.useState<Record<string, boolean>>({});
  const [floatSet, setFloatSet] = React.useState<Record<string, boolean>>({});
  const [announce, setAnnounce] = React.useState('');

  React.useEffect(() => {
    let alive = true;
    setVeri(null);
    setHata(false);
    Promise.all([getMe(), getFriends()])
      .then(([persona, friends]) => {
        if (!alive) return;
        setVeri({ persona, friends });
      })
      .catch(() => {
        if (alive) setHata(true);
      });
    return () => { alive = false; };
  }, [yeniden]);

  const partner = veri?.friends.ortakSeri.partner ?? '';
  // Dürtme günde-1 sunucuda enforce; ekran yalnız 'sent' durumunu yansıtır (istemci saymaz).
  const nudgedEff = nudged || veri?.friends.ortakSeri.nudgeDurum === 'sent';

  const durt = () => {
    if (!veri || nudgedEff) return;
    const pid = veri.friends.arkadaslar.find(
      (f) => f.ad.toLocaleLowerCase('tr-TR').startsWith(partner.toLocaleLowerCase('tr-TR')),
    )?.id ?? partner;
    setNudged(true);
    setAnnounce(`${partner}'e nazik bir dürtme gönderildi`);
    void postFriendNudge(pid).catch(() => undefined); // optimistik; sunucu-sim
  };

  const tebrikGonder = (f: Friend) => {
    if (f.tebrikGonderildi || sentSet[f.id]) return;
    setSentSet((s) => ({ ...s, [f.id]: true }));
    setFloatSet((s) => ({ ...s, [f.id]: true }));
    setAnnounce(`${f.ad} tebrik edildi`);
    window.setTimeout(() => setFloatSet((s) => { const n = { ...s }; delete n[f.id]; return n; }), 1000);
    void postFriendCongrats(f.id).catch(() => undefined); // +1 optimistik; sayı sunucuda
  };

  const arkadaslar = veri?.friends.arkadaslar ?? [];
  // Sıralama = yalnız GÖRÜNÜM düzeni (server-provided seri/xp üstünde); ekran skor hesaplamaz.
  const sirali = [...arkadaslar].sort((a, b) => (sortBy === 'xp' ? b.xp - a.xp : b.seri - a.seri));

  return (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={{ minHeight: '100vh', background: color.paper.bg, display: 'flex', fontFamily: font.sans, color: color.ink.primary, boxSizing: 'border-box' }}>
        <style>{KEYFRAMES}</style>
        <SideNav role="ogrenci" activeId="arkadas" collapsed={dar} userName={veri?.persona.ad ?? 'Öğrenci'} userSub={veri?.persona.sinif ?? ''} onAssistant={() => undefined} />

        <main style={{ flex: 1, minWidth: 0 }}>
          <header style={{
            position: 'sticky', top: 0, zIndex: 5, height: 64, display: 'flex', alignItems: 'center', gap: 14,
            padding: kompakt ? '0 16px' : '0 30px', background: 'rgba(255,255,255,0.9)', backdropFilter: 'blur(8px)',
            borderBottom: `1px solid ${color.paper.border}`, boxSizing: 'border-box',
          }}>
            <div style={{ lineHeight: 1.2, minWidth: 0 }}>
              <div style={{ fontWeight: 800, fontSize: 16 }}>Arkadaşlar &amp; Birlikte</div>
              <div style={{ fontSize: 11.5, color: color.ink.muted, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>Karşılıklı sorumluluk — birbirinizi bırakmayın</div>
            </div>
            <button
              type="button" onClick={() => undefined}
              style={{
                marginLeft: 'auto', flexShrink: 0, display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                border: 'none', padding: 0, background: 'transparent', fontFamily: 'inherit', cursor: 'pointer',
                minHeight: 44, boxSizing: 'border-box',
              }}
            >
              <span style={{
                display: 'flex', alignItems: 'center', gap: 7,
                background: color.dawn.coralCtaBg, color: '#fff', borderRadius: 10,
                padding: '9px 15px', fontSize: 13, fontWeight: 700, minHeight: 40, boxSizing: 'border-box',
              }}>
                <UserPlus />{!kompakt && 'Arkadaş ekle'}<span style={kompakt ? srOnly : undefined}>{kompakt ? 'Arkadaş ekle' : ''}</span>
              </span>
            </button>
          </header>

          <div style={{ maxWidth: 1000, margin: '0 auto', padding: kompakt ? '22px 16px 50px' : '26px 30px 50px', boxSizing: 'border-box' }}>
            {/* Görünmez canlı bölge — dürtme/tebrik onayları */}
            <div aria-live="polite" style={srOnly}>{announce}</div>

            {hata ? (
              // [ONAY BEKLER] Error kopyası inferred (DC'de yok)
              <ErrorState
                serifTitle="Arkadaşların şu an gelmedi."
                body="Sorun sende değil — bağlantı bir soluklandı. Serin ve çalışman güvende. Birazdan yeniden dene."
                onRetry={() => setYeniden((n) => n + 1)}
              />
            ) : veri === null ? (
              <div aria-busy="true" aria-label="Arkadaşlar yükleniyor">
                <div style={{ display: 'grid', gridTemplateColumns: kompakt ? 'minmax(0,1fr)' : 'minmax(0,1fr) minmax(0,1fr)', gap: 18, marginBottom: 18 }}>
                  {[0, 1].map((i) => (
                    <div key={i} style={{ padding: 24, background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 20, boxSizing: 'border-box' }}>
                      <Skeleton shape="card" delayMs={0} slowAfterMs={null} />
                    </div>
                  ))}
                </div>
                <div style={{ padding: 22, background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 18, boxSizing: 'border-box' }}>
                  <Skeleton shape="card" delayMs={0} slowAfterMs={null} />
                </div>
              </div>
            ) : arkadaslar.length === 0 ? (
              // [ONAY BEKLER] Empty kopyası inferred (DC'de yok)
              <EmptyState
                serifTitle="Henüz arkadaşın yok."
                body="Birlikte seri tutmak yalnız tutmaktan daha dayanıklı. Bir arkadaşını ekle — birbirinizi bırakmayın."
                action={<Button variant="primary" onClick={() => undefined}>Arkadaş ekle</Button>}
              />
            ) : (
              <>
                <div style={{ display: 'grid', gridTemplateColumns: kompakt ? 'minmax(0,1fr)' : 'minmax(0,1fr) minmax(0,1fr)', gap: 18, marginBottom: 18 }}>
                  {/* ORTAK SERİ hero */}
                  <div style={{ background: `linear-gradient(140deg, ${color.dawn.coralCtaBg}, ${color.dawn.coral})`, borderRadius: 20, padding: 24, color: '#fff', boxSizing: 'border-box' }}>
                    <div style={{ fontSize: 12.5, fontWeight: 700, color: 'rgba(255,240,232,0.9)', marginBottom: 16 }}>Ortak seri · {partner} ile</div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 14, marginBottom: 16 }}>
                      <GradientAvatar gradient="linear-gradient(135deg,#2A2433,#4A4456)" label={veri.persona.bas} size={56} />
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ display: 'flex', justifyContent: 'center' }}><Alev c="#FFE4D0" size={34} /></div>
                        <div style={{ ...numText, fontSize: 30, fontWeight: 800, lineHeight: 1 }}>{veri.friends.ortakSeri.sayi}</div>
                        <span style={srOnly}>gün ortak seri</span>
                      </div>
                      <GradientAvatar gradient="linear-gradient(135deg,#BE185D,#EC4899)" label={partner.slice(0, 2).toLocaleUpperCase('tr-TR')} size={56} />
                    </div>
                    <div style={{ background: 'rgba(255,255,255,0.12)', borderRadius: 12, padding: '12px 14px', display: 'flex', alignItems: 'center', gap: 10, boxSizing: 'border-box' }}>
                      <span style={{ fontSize: 13, color: 'rgba(255,240,232,0.92)', flex: 1, lineHeight: 1.4, minWidth: 0 }}>
                        Sen bugün <Tik srText="tamamlandı" c="#FFE4D0" size={12} /> · {nudgedEff ? `${partner}'e nazik bir dürtme gönderildi` : `${partner} henüz çalışmadı`}
                      </span>
                      {calmMode ? (
                        // Sakin mod: dürtme sustur — baskı-azaltma. CTA render edilmez, kısa açıklama kalır.
                        <span style={{
                          flexShrink: 0, maxWidth: 132, fontSize: 12, fontWeight: 700,
                          color: 'rgba(255,240,232,0.92)', lineHeight: 1.35, textAlign: 'right', boxSizing: 'border-box',
                        }}>
                          Sakin mod açık — dürtme kapalı
                        </span>
                      ) : (
                        <button
                          type="button" onClick={durt} disabled={nudgedEff} aria-pressed={!!nudgedEff}
                          aria-label={nudgedEff ? 'Dürtme gönderildi' : `${partner} arkadaşını dürt`}
                          style={{
                            flexShrink: 0, display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                            border: 'none', padding: 0, background: 'transparent', fontFamily: 'inherit',
                            cursor: nudgedEff ? 'default' : 'pointer', minHeight: 44, boxSizing: 'border-box',
                          }}
                        >
                          <span style={{
                            display: 'inline-flex', alignItems: 'center', gap: 5,
                            background: nudgedEff ? 'rgba(255,255,255,0.18)' : '#fff',
                            color: nudgedEff ? 'rgba(255,240,232,0.92)' : color.dawn.coralTextOnLight,
                            borderRadius: 9, padding: '7px 13px', fontSize: 12, fontWeight: 800,
                            whiteSpace: 'nowrap', minHeight: 34, boxSizing: 'border-box',
                          }}>
                            {nudgedEff ? <>Gönderildi <Tik srText="" c="#FFE4D0" size={12} /></> : `${partner}'i dürt`}
                          </span>
                        </button>
                      )}
                    </div>
                  </div>

                  {/* BİRLİKTE GÖREV */}
                  <div style={{ background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 20, padding: 24, boxSizing: 'border-box' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 6 }}>
                      <span style={{ fontSize: 11, fontWeight: 800, color: color.dawn.coralTextOnLight, background: '#FFF3EE', padding: '4px 10px', borderRadius: 7 }}>BİRLİKTE GÖREV</span>
                      <span style={{ marginLeft: 'auto', display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 12, fontWeight: 700, color: color.semantic.riskTextOnLight }}>
                        <Saat /><span style={numText}>{veri.friends.gorev.kalanGun}</span> gün kaldı
                      </span>
                    </div>
                    <h3 style={{ margin: '6px 0 4px', fontSize: 17, fontWeight: 800 }}>{veri.friends.gorev.baslik}</h3>
                    <p style={{ margin: '0 0 16px', fontSize: 13, color: color.ink.muted, lineHeight: 1.5 }}>Ödül: {veri.friends.gorev.odul}.</p>
                    <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 6 }}>
                      <span style={{ fontSize: 13, fontWeight: 700, color: color.ink.secondary }}>İlerleme</span>
                      <span style={{ ...numText, fontSize: 14, fontWeight: 800, color: color.dawn.coralTextOnLight }}>{veri.friends.gorev.ilerleme} / {veri.friends.gorev.hedef}</span>
                    </div>
                    <CoopBar benPay={veri.friends.gorev.benPay} partnerPay={veri.friends.gorev.partnerPay} hedef={veri.friends.gorev.hedef} partner={partner} />
                    <div style={{ display: 'flex', gap: 16, marginTop: 10, fontSize: 12, fontWeight: 700, flexWrap: 'wrap' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 6, color: color.dawn.coralTextOnLight }}>
                        <span aria-hidden style={{ width: 10, height: 10, borderRadius: 3, background: color.dawn.coral }} />Sen · <span style={numText}>{veri.friends.gorev.benPay}</span>
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#BE185D' }}>
                        <span aria-hidden style={{ width: 10, height: 10, borderRadius: 3, background: '#EC4899' }} />{partner} · <span style={numText}>{veri.friends.gorev.partnerPay}</span>
                      </span>
                    </div>
                  </div>
                </div>

                {/* ARKADAŞ LİSTESİ */}
                <div style={{ background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 18, padding: 22, boxSizing: 'border-box' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, gap: 14, flexWrap: 'wrap' }}>
                    <div style={{ fontSize: 16, fontWeight: 800 }}>Arkadaşların</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 11 }}>
                      <span style={{ fontSize: 11.5, fontWeight: 700, color: color.ink.muted }}>Sırala</span>
                      <SegmentedControl<SortKey>
                        options={[{ key: 'seri', label: 'Seri' }, { key: 'xp', label: 'XP' }]}
                        value={sortBy} onChange={setSortBy} ariaContext="Arkadaşları sırala"
                      />
                    </div>
                  </div>
                  <ul style={{ margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {sirali.map((f, i) => (
                      <FriendRow
                        key={f.id} f={f} gold={i === 0} kompakt={kompakt}
                        sent={f.tebrikGonderildi || !!sentSet[f.id]}
                        floating={!!floatSet[f.id]} reduced={reduced}
                        onCongrats={() => tebrikGonder(f)}
                      />
                    ))}
                  </ul>
                  <p style={{ margin: '14px 0 0', padding: '13px 16px', borderRadius: 11, background: '#F0FDF4', fontFamily: font.serif, fontStyle: 'italic', fontSize: 15, color: '#166534', lineHeight: 1.5 }}>
                    Ortak seriler, bireysel seriden daha dayanıklıdır: kimse arkadaşını bırakmak istemez.
                  </p>
                </div>
              </>
            )}
          </div>
        </main>
      </div>
    </KiroThemeProvider>
  );
}

export default ArkadasSerisiPage;
