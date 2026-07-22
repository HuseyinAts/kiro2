// ============================================================================
// KIRO2 — Çalışma Modları (SPRINT5 · KIRO Calisma Modlari.dc.html · §D)
// Tema = PAPER. SideNav YOK — tek sütun (max 880px), 2×2 mod grid'i (≤760px 1fr).
// "Tek havuz · çok yol": aynı kart havuzu (en zayıf mat konusu = Türev) 4 farklı
// getirim biçimiyle test edilir. Motorlar sunucuda — ekran salt-okur.
// Veri: getTopics() (en zayıf mat konusu) + getReviewDue() (kart sayısı). Rota /modlar.
// ============================================================================
import * as React from 'react';

import { configureKiroApi, getTopics, getReviewDue } from '../api/api-client';
import type { MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';
import type { ReviewItem, Topic } from '../types';
import { color, font } from '../tokens';
import {
  KiroThemeProvider,
  numText,
  tierFromPct,
  Skeleton,
  EmptyState,
  ErrorState,
} from '../ui';
import '../tokens/tokens.css';

configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });

const TIER_AD: Record<ReturnType<typeof tierFromPct>, string> = {
  tanidik: 'Tanıdık',
  yetkin: 'Yetkin',
  usta: 'Usta',
  fethedildi: 'Fethedildi',
};

// Bespoke inline SVG — DC path'lerinden birebir (emoji/ikon-kütüphanesi YOK).
const chevron = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="m9 6 6 6-6 6" />
  </svg>
);
function ModIkon({ d, renk }: { d: string; renk: string }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={renk} strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d={d} />
    </svg>
  );
}

interface Mod {
  ad: string;
  renk: string;
  /** CTA metni için AA-güvenli koyu karşılık (ikon canlı renk kalır) */
  ctaRenk: string;
  bg: string;
  sayac: string;
  aciklama: string;
  cta: string;
  href: string;
  ikon: string;
}

export function CalismaModlariPage(): React.ReactElement {
  const [topics, setTopics] = React.useState<Topic[] | null>(null);
  const [due, setDue] = React.useState<ReviewItem[] | null>(null);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);

  React.useEffect(() => {
    let alive = true;
    setTopics(null);
    setDue(null);
    setHata(false);
    Promise.all([getTopics(), getReviewDue()])
      .then(([t, r]) => {
        if (!alive) return;
        setTopics(t);
        setDue(r);
      })
      .catch(() => {
        if (alive) setHata(true);
      });
    return () => {
      alive = false;
    };
  }, [yeniden]);

  // En zayıf matematik konusu (min hâkimiyet → Türev 48). İstemci yalnız gösterir.
  const matTopics = (topics ?? []).filter((t) => t.ders === 'mat');
  const w = matTopics.length
    ? matTopics.reduce((a, b) => (b.hakimiyet < a.hakimiyet ? b : a))
    : undefined;
  const poolPct = w ? w.hakimiyet : 0;
  const poolTier = TIER_AD[tierFromPct(poolPct)];
  const poolCards = (due ?? []).find((r) => r.konu === w?.ad)?.kart ?? 6;
  const ciftler = Math.round(poolCards / 2);

  const modlar: Mod[] = [
    {
      ad: 'Kart', renk: '#E0593F', ctaRenk: '#C2452B', bg: 'rgba(224,89,63,0.12)', sayac: `${poolCards} kart`,
      aciklama: 'Klasik çevir-göster: soruyu gör, cevabı hatırla, kendini derecelendir (FSRS).',
      cta: 'Karta başla', href: '/tekrar', ikon: 'M4 6h16v12H4zM4 10h16',
    },
    {
      ad: 'Test', renk: '#3B82F6', ctaRenk: '#1D4ED8', bg: 'rgba(59,130,246,0.12)', sayac: `${poolCards} soru`,
      aciklama: 'Çoktan seçmeli sınav biçimi — gerçek getirim, en güçlü pekiştirme.',
      cta: 'Teste başla', href: '/soru-cozme', ikon: 'M9 11l3 3 8-8M20 12v6a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h9',
    },
    {
      ad: 'Eşleştirme', renk: '#1FB683', ctaRenk: '#047857', bg: 'rgba(31,182,131,0.12)', sayac: `${ciftler} çift`,
      aciklama: 'Kavram ↔ tanım eşle — hızlı, oyunsu, tanıma hafızasını tazeler.',
      cta: 'Eşleştir', href: '/tekrar', ikon: 'M4 7h6v6H4zM14 11h6v6h-6zM10 10l4 2', // en yakın deneyim → FSRS Tekrar (ayrı mod ekranı yok)
    },
    {
      ad: 'Hız', renk: '#9A5D0D', ctaRenk: '#9A5D0D', bg: 'rgba(199,122,30,0.14)', sayac: '60 sn',
      aciklama: 'Zaman baskısı altında geri getirme — sınav refleksini keskinleştirir.',
      cta: 'Hıza başla', href: '/duello', ikon: 'M13 2 4 14h7l-1 8 9-12h-7l1-8Z', // ileri-referans → Düello (Sprint 8)
    },
  ];

  const dar = useMedia('(max-width: 760px)');

  return (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={{ minHeight: '100vh', background: color.paper.bg, fontFamily: font.sans, color: color.ink.primary, fontSize: 14, lineHeight: 1.6 }}>
        <div style={{ maxWidth: 880, margin: '0 auto', padding: dar ? '28px 18px 60px' : '34px 30px 70px', boxSizing: 'border-box' }}>

          {/* Başlık */}
          <header style={{ marginBottom: 8 }}>
            <span style={{ display: 'inline-block', fontSize: 11, fontWeight: 800, letterSpacing: '0.14em', color: '#E0593F', textTransform: 'uppercase' }}>Tek Havuz · Çok Yol</span>
            <h1 style={{ fontFamily: font.serif, margin: '11px 0 6px', fontSize: 38, lineHeight: 1.06, color: color.ink.primary }}>Çalışma Modları</h1>
            <p style={{ margin: 0, fontSize: 15, color: color.ink.muted, maxWidth: 600 }}>Aynı kart havuzundan farklı getirim biçimleri — motor senin verinden üretir, ekstra içerik yok. Çeşitlilik hafızayı güçlendirir.</p>
          </header>

          {hata ? (
            <div style={{ marginTop: 20 }}>
              <ErrorState serifTitle="Modlar şu an gelmedi." body="Sorun sende değil — bağlantı bir soluklandı, çalışman güvende. Hazır olduğunda tekrar dene." onRetry={() => setYeniden((n) => n + 1)} />
            </div>
          ) : topics === null ? (
            <div aria-busy="true" aria-label="Modlar yükleniyor" style={{ marginTop: 20, display: 'grid', gap: 14 }}>
              <div style={{ background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 16, padding: 18 }}>
                <Skeleton shape="row" delayMs={0} />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: dar ? '1fr' : '1fr 1fr', gap: 14 }}>
                {[0, 1, 2, 3].map((i) => (
                  <div key={i} style={{ background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 16, padding: 20 }}>
                    <Skeleton shape="card" delayMs={0} />
                  </div>
                ))}
              </div>
            </div>
          ) : !w ? (
            <div style={{ marginTop: 20 }}>
              <EmptyState serifTitle="Bugün tekrar havuzun boş — eğrin sağlıklı." body="Yeni bir kart havuzu belirdiğinde modlar burada seni bekliyor olacak. Şimdilik panelden bir sonraki adımını seçebilirsin." />
            </div>
          ) : (
            <>
              {/* Havuz kartı */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 14, background: 'linear-gradient(150deg,#FFF3EE,#FFFFFF)', border: '1px solid #F2D9CE', borderRadius: 16, padding: '16px 20px', margin: '20px 0 16px' }}>
                <div aria-hidden style={{ width: 42, height: 42, flexShrink: 0, borderRadius: 12, background: 'rgba(255,111,92,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#E0593F" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                    <rect x="3" y="5" width="18" height="14" rx="2" />
                    <path d="M3 10h18" />
                  </svg>
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 15, fontWeight: 800 }}>Türev · zincir kuralı havuzu</div>
                  <div style={{ fontSize: 12.5, color: color.ink.muted }}><span style={numText}>{poolCards}</span> kart · zayıf atomundan otomatik derlendi</div>
                </div>
                <span style={{ fontSize: 12.5, fontWeight: 700, color: '#E0593F', flexShrink: 0, whiteSpace: 'nowrap' }}>{poolTier} %<span style={numText}>{poolPct}</span></span>
              </div>

              {/* Mod grid'i */}
              <div style={{ display: 'grid', gridTemplateColumns: dar ? '1fr' : '1fr 1fr', gap: 14 }}>
                {modlar.map((m) => (
                  <a
                    key={m.ad}
                    href={m.href}
                    style={{ display: 'block', background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 16, padding: 20, textDecoration: 'none', color: color.ink.primary }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 11 }}>
                      <div aria-hidden style={{ width: 40, height: 40, flexShrink: 0, borderRadius: 12, background: m.bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <ModIkon d={m.ikon} renk={m.renk} />
                      </div>
                      <div style={{ fontSize: 16, fontWeight: 800, color: color.ink.primary }}>{m.ad}</div>
                      <span style={{ ...numText, marginLeft: 'auto', fontSize: 12, fontWeight: 700, color: color.ink.muted, whiteSpace: 'nowrap' }}>{m.sayac}</span>
                    </div>
                    <p style={{ margin: '0 0 12px', fontSize: 13, color: color.ink.muted, lineHeight: 1.5 }}>{m.aciklama}</p>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 800, color: m.ctaRenk }}>
                      {m.cta}
                      {chevron}
                    </span>
                  </a>
                ))}
              </div>

              {/* Alt not */}
              <p style={{ margin: '18px 2px 0', fontSize: 12.5, color: color.ink.muted, lineHeight: 1.55 }}>Not: Dört mod da aynı <span style={numText}>{poolCards}</span> kartı farklı getirim yüküyle test eder — tanıma (kart), hatırlama (test), eşleme (eşleştirme), hız altında geri getirme (hız). Motor hangi modun hangi kartta en çok işe yaradığını öğrenir.</p>
            </>
          )}
        </div>
      </div>
    </KiroThemeProvider>
  );
}

// PanelPage.tsx'teki local hook'un birebir kopyası (jsdom guard'lı).
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

export default CalismaModlariPage;
