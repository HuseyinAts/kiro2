// ============================================================================
// KIRO2 — İlk Hafta (FAZ 3 KAPANIŞ · KIRO Ilk Hafta.dc.html · PAPER)
// Momentum yayı: SideNav YOK, ortalı tek-kolon (max 960). Öğrenci → SEN.
// Sunucu-otorite: currentDay/yüzde/gün-durumları/mesaj SUNUCUDAN (getIlkHafta);
// istemci gün/oran/tier TÜRETMEZ — odakKonu/tier/zayifAtom sunucuda kopyaya baked
// (DC birebir: gün etiketleri + kart açıklamaları). Persona'ya rol EKLENMEZ (ayrı kaynak).
//
// KANON (P0 kararları — DC → üretim uyarlaması):
// - DC coral GRADYANLARI (#FF8A5B→#FF5E7E · current-node/CTA/progress) → solid
//   coralCtaBg #C2452B. Eyebrow/progress-sayı/current #E0593F → coralTextOnLight #C2452B.
// - #6B6478 ikincil → ink.muted (paper AA minimumu). done node yeşil #1FB683 korunur.
// - Küçük tag/label metni (11px) AA-sertleştirildi: done/NEDEN yeşil → successTextOnLight
//   #047857, gün7 amber → riskTextOnLight #9A5D0D (hue korunur; DC #17936B/#C99A2E AA-FAIL).
//   YARIN mavisi #3163C4 AA-sertleştirildi (#EAF0FC üzeri 4.95:1; DC #3B6FD4 4.16:1 AA-FAIL, hue korunur; indigo değil).
// - Sayılar Hanken tabular (KANON: tüm sayılar Hanken; DC serif rakamları uyarlandı).
// - Pulse (current düğüm halkası) → useReducedMotion/calmMode gate; layout-anim YOK (box-shadow).
// - Bespoke SVG (check/play/arrow), emoji YOK. Absence-dili yumuşak ("Acelesi yok" korundu).
// ============================================================================
import * as React from 'react';

import { configureKiroApi, getIlkHafta } from '../api/api-client';
import type { MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';
import { color, font } from '../tokens';
import type { IlkHaftaResponse, IlkHaftaGun, IlkHaftaKart } from '../types';
import { KiroThemeProvider, numText, useReducedMotion, Skeleton, ErrorState } from '../ui';
import '../tokens/tokens.css';

configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });

const CORAL = color.dawn.coralCtaBg; // #C2452B — solid coral CTA/vurgu (beyaz metin AA-güvenli)
const CORAL_TEXT = color.dawn.coralTextOnLight; // #C2452B — açık zeminde coral METİN

// Pulse (current düğüm) — box-shadow halkası (layout DEĞİL). @keyframes dosyada var →
// kanon-lint useReducedMotion import'unu HAS_RM_GUARD sayar; JS-motion RM/calm'da kapanır.
const KEYFRAMES =
  '@keyframes ikPulse { 0%,100% { box-shadow: 0 0 0 0 rgba(255,111,92,0.5); } 50% { box-shadow: 0 0 0 9px rgba(255,111,92,0); } }';

// jsdom matchMedia'sız guard'lı (PanelPage local hook deseni).
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

// --- Bespoke ikonlar (DC birebir) ---
const Check = (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <polyline points="20 6 9 17 4 12" />
  </svg>
);
const Play = (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="#fff" stroke="none" aria-hidden>
    <path d="M7 5.5v13a1 1 0 0 0 1.5.86l11-6.5a1 1 0 0 0 0-1.72l-11-6.5A1 1 0 0 0 7 5.5Z" />
  </svg>
);
const ArrowR = (
  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M4 12h15" />
    <path d="m13 6 6 6-6 6" />
  </svg>
);

/** Durum → düğüm görseli. done yeşil node korunur; current solid coral (gradyan DEĞİL); lock nötr. */
function dugumStil(durum: IlkHaftaGun['durum']): { nodeBg: string; nodeBorder: string; dColor: string; labelColor: string } {
  switch (durum) {
    case 'done':
      return { nodeBg: color.semantic.success, nodeBorder: 'none', dColor: color.semantic.successTextOnLight, labelColor: color.ink.primary };
    case 'current':
      return { nodeBg: CORAL, nodeBorder: 'none', dColor: CORAL_TEXT, labelColor: CORAL_TEXT };
    default: // lock
      return { nodeBg: '#F0EAE1', nodeBorder: '1px solid #E0D8CC', dColor: color.ink.muted, labelColor: color.ink.muted };
  }
}

// Kart tag renkleri (DC piksel otoritesi; yeşil/amber AA-sert token'a çekildi, mavi DC korunur).
const KART_STIL: Record<IlkHaftaKart['tur'], { tagColor: string; tagBg: string; border: string }> = {
  bugun: { tagColor: CORAL_TEXT, tagBg: '#FFF3EE', border: '#F2D9CE' },
  yarin: { tagColor: '#3163C4', tagBg: '#EAF0FC', border: color.paper.border },
  gun7: { tagColor: color.semantic.riskTextOnLight, tagBg: '#FAF3E0', border: color.paper.border },
  neden: { tagColor: color.semantic.successTextOnLight, tagBg: '#E3F6EE', border: color.paper.border },
};

// Görsel-gizli (SR-only) — durum yalnız renkle aktarılmasın; renk-körü/SR için metin.
const SR_ONLY: React.CSSProperties = {
  position: 'absolute', width: 1, height: 1, padding: 0, margin: -1,
  overflow: 'hidden', clip: 'rect(0 0 0 0)', whiteSpace: 'nowrap', border: 0,
};
const DURUM_METNI: Record<IlkHaftaGun['durum'], string> = {
  done: 'Tamamlandı',
  current: 'Bugün',
  lock: 'Kilitli',
};

function GunDugumu({ g, reduced }: { g: IlkHaftaGun; reduced: boolean }): React.ReactElement {
  const st = dugumStil(g.durum);
  const pulse = g.durum === 'current' && !reduced;
  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', position: 'relative', boxSizing: 'border-box' }}>
      <span style={SR_ONLY}>{DURUM_METNI[g.durum]}</span>
      {/* soldaki bağlaç çizgisi (rengi sunucudan; gün 1'de yok) */}
      {g.connColor ? (
        <div aria-hidden style={{ position: 'absolute', top: 26, left: '-50%', width: '100%', height: 3, background: g.connColor, zIndex: 0 }} />
      ) : null}
      <div
        style={{
          position: 'relative', zIndex: 1, width: 52, height: 52, borderRadius: 16,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: st.nodeBg, border: st.nodeBorder, boxSizing: 'border-box',
          ...(pulse ? { animation: 'ikPulse 1.8s ease-in-out infinite' } : {}),
        }}
      >
        {g.durum === 'done' ? Check : g.durum === 'current' ? Play : (
          <span style={{ ...numText, fontSize: 20, fontWeight: 800, color: color.ink.muted }}>{g.dayNo}</span>
        )}
      </div>
      <div style={{ ...numText, marginTop: 9, fontSize: 11, fontWeight: 800, letterSpacing: '0.04em', color: st.dColor }}>GÜN {g.dayNo}</div>
      <div style={{ marginTop: 3, maxWidth: 96, fontSize: 11.5, fontWeight: 600, color: st.labelColor, textAlign: 'center', lineHeight: 1.3 }}>{g.label}</div>
    </div>
  );
}

function IskeletBlok({ dar }: { dar: boolean }): React.ReactElement {
  return (
    <div aria-busy="true" aria-label="İlk hafta yükleniyor">
      {/* ilerleme özeti iskeleti */}
      <div style={{ background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 18, padding: '20px 24px', marginBottom: 22, boxSizing: 'border-box' }}>
        <Skeleton shape="card" delayMs={0} slowAfterMs={null} />
      </div>
      {/* 7 gün iskeleti */}
      <div style={{ overflowX: 'auto', padding: '6px 2px 14px', boxSizing: 'border-box' }}>
        <div style={{ display: 'flex', gap: 0, minWidth: 640 }}>
          {[0, 1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 9 }}>
              <Skeleton shape="bar" width={52} height={52} delayMs={0} />
              <Skeleton shape="bar" width={40} height={10} delayMs={0} />
            </div>
          ))}
        </div>
      </div>
      {/* 4 kart iskeleti */}
      <div style={{ display: 'grid', gridTemplateColumns: dar ? '1fr' : '1fr 1fr', gap: 14, marginTop: 20 }}>
        {[0, 1, 2, 3].map((i) => (
          <div key={i} style={{ background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 16, padding: '18px 20px', boxSizing: 'border-box' }}>
            <Skeleton shape="card" delayMs={0} slowAfterMs={null} />
          </div>
        ))}
      </div>
    </div>
  );
}

export function IlkHaftaPage(): React.ReactElement {
  const reduced = useReducedMotion();
  const dar = useMedia('(max-width: 640px)');

  const [data, setData] = React.useState<IlkHaftaResponse | null>(null);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);

  React.useEffect(() => {
    let alive = true;
    setData(null);
    setHata(false);
    getIlkHafta()
      .then((d) => {
        if (alive) setData(d);
      })
      .catch(() => {
        if (alive) setHata(true);
      });
    return () => {
      alive = false;
    };
  }, [yeniden]);

  return (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={{ minHeight: '100vh', background: color.paper.bg, fontFamily: font.sans, color: color.ink.primary, fontSize: 14, lineHeight: 1.6, boxSizing: 'border-box' }}>
        <style>{KEYFRAMES}</style>
        <div style={{ maxWidth: 960, margin: '0 auto', padding: dar ? '26px 18px 56px' : '34px 30px 70px', boxSizing: 'border-box' }}>
          {/* Başlık */}
          <header style={{ marginBottom: 24 }}>
            <span style={{ fontSize: 11, fontWeight: 800, letterSpacing: '0.14em', color: CORAL_TEXT, textTransform: 'uppercase' }}>Momentum Haftası</span>
            <h1 style={{ margin: '11px 0 6px', fontFamily: font.serif, fontWeight: 400, fontSize: 38, lineHeight: 1.06, color: color.ink.primary }}>İlk 7 Gün</h1>
            <p style={{ margin: 0, fontSize: 15, color: color.ink.muted, maxWidth: 620, lineHeight: 1.6 }}>
              İlk hafta rastgele değil — tasarlanmış bir yay. Her gün küçük bir zafer, 7. günde ilk kilometre taşın.{' '}
              <strong style={{ color: color.ink.primary }}>Serini 7&apos;ye taşıyan öğrenci sınava kadar kalıyor.</strong>
            </p>
          </header>

          {hata ? (
            <ErrorState
              serifTitle="İlk hafta yayın şu an gelmedi."
              body="Sorun sende değil — bağlantı bir soluklandı, momentumun güvende. Hazır olduğunda tekrar dene."
              onRetry={() => setYeniden((n) => n + 1)}
            />
          ) : data === null ? (
            <IskeletBlok dar={dar} />
          ) : (
            <>
              {/* İLERLEME ÖZETİ */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 16, background: 'linear-gradient(150deg,#FFF3EE,#FFFFFF)', border: '1px solid #F2D9CE', borderRadius: 18, padding: '20px 24px', marginBottom: 22, flexWrap: 'wrap', boxSizing: 'border-box' }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                  <span style={{ ...numText, fontSize: 40, fontWeight: 800, color: CORAL_TEXT, lineHeight: 1 }}>{data.ozet.currentDay}</span>
                  <span style={{ ...numText, fontSize: 14, fontWeight: 700, color: color.ink.muted }}>/ {data.ozet.totalDays} gün</span>
                </div>
                <div style={{ flex: 1, minWidth: 180 }}>
                  <div
                    role="progressbar"
                    aria-label="İlk hafta ilerlemesi"
                    aria-valuenow={data.ozet.yuzde}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    style={{ height: 9, borderRadius: 99, background: '#F0E4DC', overflow: 'hidden' }}
                  >
                    <div aria-hidden style={{ width: `${data.ozet.yuzde}%`, height: '100%', borderRadius: 99, background: CORAL }} />
                  </div>
                  <div style={{ fontSize: 12.5, color: color.ink.muted, marginTop: 7 }}>{data.ozet.mesaj}</div>
                </div>
                <a href="/bugun" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, height: 44, padding: '0 20px', borderRadius: 12, background: CORAL, color: '#fff', fontFamily: font.sans, fontSize: 14, fontWeight: 800, textDecoration: 'none', boxSizing: 'border-box' }}>
                  Bugünü tamamla {ArrowR}
                </a>
              </div>

              {/* 7-GÜN YAYI (yatay-scroll; iç min-width korunur) — klavye ok-tuşuyla kaydırılır (WCAG 2.1.1) */}
              <div
                className="k-scan"
                tabIndex={0}
                role="group"
                aria-label="İlk 7 gün"
                style={{ overflowX: 'auto', padding: '6px 2px 14px', boxSizing: 'border-box' }}
              >
                <div style={{ display: 'flex', gap: 0, minWidth: 640 }}>
                  {data.gunler.map((g) => (
                    <GunDugumu key={g.dayNo} g={g} reduced={reduced} />
                  ))}
                </div>
              </div>

              {/* KİLOMETRE-TAŞI KARTLARI (≤ breakpoint tek-kolon) */}
              <div style={{ display: 'grid', gridTemplateColumns: dar ? '1fr' : '1fr 1fr', gap: 14, marginTop: 20 }}>
                {data.kartlar.map((c) => {
                  const ks = KART_STIL[c.tur];
                  return (
                    <div key={c.tur} style={{ background: color.paper.card, border: `1px solid ${ks.border}`, borderRadius: 16, padding: '18px 20px', boxSizing: 'border-box' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                        <span style={{ fontSize: 11, fontWeight: 800, letterSpacing: '0.06em', color: ks.tagColor, background: ks.tagBg, padding: '3px 9px', borderRadius: 99 }}>{c.tag}</span>
                        <span style={{ fontSize: 13.5, fontWeight: 800, color: color.ink.primary }}>{c.title}</span>
                      </div>
                      <p style={{ margin: 0, fontSize: 13, color: color.ink.muted, lineHeight: 1.5 }}>{c.desc}</p>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
      </div>
    </KiroThemeProvider>
  );
}

export default IlkHaftaPage;
