// ============================================================================
// KIRO2 — Alan Kütüphanesi (SPRINT10-A · Grup 8 · KIRO2 Alan Kutuphanesi.dc.html)
// Tema = PAPER (öğrenci → SEN). SideNav YOK — geri-oku + ortalı makale (max 1080px):
//   header → 3-alan kart ızgarası (Sayısal/Eşit Ağırlık/Sözel; seninKey rozetli) →
//   "Tüm dersler" başlık → katalog: her ders TEK-AÇILIR akordeon (ünite + numaralı konu;
//   soruSayisi>0 → coral "örnek soru havuzda" şerit, =0 → şerit GİZLİ).
//
// SUNUCU-OTORİTE: seninKey + ders-başına sayaçlar (konuToplam/soruSayisi) SUNUCUDAN
// gelir (getAlanKutuphane); başlıktaki "N ders · M+ konu" bu sunucu-değerlerinin
// istemci-tarafı toplam-gösterimidir (uydurma DEĞİL — istemci durum/adet ÜRETMEZ).
// Alan/ders renkleri veride YOK; ekran ders/alan → palet eşlemesini tokens üzerinden yapar (kanon).
//
// KOPYA: header/şerit/rozet DC birebir. Alan `ozet` metni + kapanış paragrafı contract'ta
// taşınmadığı için static (DC'den; kapanış SEN diline + dev-persona adı çıkarılarak
// uyarlandı → copyDeviations). "Senin alanın" rozeti alan-renk zemin+beyaz AA riski
// taşıdığından ink-metin + alan-renk outline'a çevrildi (AA-güvenli → canonNotes).
// ============================================================================
import * as React from 'react';

import { getAlanKutuphane } from '../api/api-client';
import { color, font } from '../tokens';
import type { AlanKey, AlanKutuphaneAlan, AlanKutuphaneData, AlanKutuphaneDers } from '../types';
import { KiroThemeProvider, numText } from '../ui/theme';
import { EmptyState } from '../ui/EmptyState';
import { ErrorState } from '../ui/ErrorState';
import { Skeleton } from '../ui/Skeleton';
import '../tokens/tokens.css';

// Alan → dekoratif renk (veride YOK; tokens'tan). Kaynak alan renkleri: say=mavi, ea=yeşil, soz=amber.
const ALAN_RENK: Record<AlanKey, string> = {
  say: color.subject.light.mat, // #3B82F6
  ea: color.semantic.success, // #1FB683
  soz: color.subject.light.tur, // #F59E0B
};
// Alan özet metni — contract `alanlar` bunu taşımaz; DC-verbatim static kopya.
const ALAN_OZET: Record<AlanKey, string> = {
  say: 'Mühendislik · Tıp · Fen bilimleri',
  ea: 'Hukuk · İktisat · Psikoloji',
  soz: 'Öğretmenlik · İlahiyat · Hukuk',
};

// Ders → dekoratif renk (letter badge). Kaynak: tokens.color.subject (light + katalog).
const DERS_RENK: Record<string, string> = {
  ...color.subject.light,
  ...color.subject.katalog,
};
// Ders rengi → yumuşak tint (letter badge zemini; DC tintOf ile birebir).
const DERS_TINT: Record<string, string> = {
  '#3B82F6': '#EFF6FF', // mat
  '#8B5CF6': '#F1EBFC', // fiz
  '#E0593F': '#FCEBE6', // kim
  '#1FB683': '#E4F7F0', // biy
  '#F59E0B': '#FEF3E2', // tur
  '#D97706': '#FBF0DE', // edb
  '#B45309': '#F7ECDD', // tar
  '#0D9488': '#E2F5F2', // cog
  '#7C3AED': '#F0E9FC', // fel
  '#6B7280': '#EEF0F2', // din
};

// jsdom matchMedia'sız guard'lı responsive kanca (PanelPage deseni).
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

// ---- Bespoke inline SVG (emoji/stok-lib YOK) ----
const Geri = (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
  </svg>
);
function Chevron({ open }: { open: boolean }) {
  // Statik transform (transition YOK) — reduced-motion guard gerektirmez.
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden style={{ flexShrink: 0, transform: open ? 'rotate(180deg)' : undefined }}>
      <polyline points="6 9 12 15 18 9" />
    </svg>
  );
}
const Kitap = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color.dawn.coralTextOnLight} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden style={{ flexShrink: 0 }}>
    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z" />
  </svg>
);

// ---- Alan kartı (3 alan; seninKey rozetli) ----
function SeninRozet({ renk }: { renk: string }) {
  // AA-güvenli: ink metin + alan-renk outline (alan-renk zemin+beyaz AA riskini önler).
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', fontFamily: font.sans, fontSize: 10, fontWeight: 800, letterSpacing: '0.04em', textTransform: 'uppercase', padding: '3px 9px', borderRadius: 999, background: color.paper.subtle, color: color.ink.primary, border: `1.5px solid ${renk}` }}>
      Senin alanın
    </span>
  );
}

function AlanKart({ alan, senin }: { alan: AlanKutuphaneAlan; senin: boolean }) {
  const renk = ALAN_RENK[alan.key];
  const ozet = ALAN_OZET[alan.key];
  return (
    <div style={{ boxSizing: 'border-box', background: color.paper.card, border: senin ? `2px solid ${renk}` : `1px solid ${color.paper.border}`, borderRadius: 18, padding: 22 }}>
      <div aria-hidden style={{ height: 4, width: 44, borderRadius: 99, background: renk, marginBottom: 16 }} />
      <div style={{ display: 'flex', alignItems: 'center', gap: 9, flexWrap: 'wrap', marginBottom: 4 }}>
        <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800, letterSpacing: '-0.02em', color: color.ink.primary }}>{alan.ad}</h2>
        {senin && <SeninRozet renk={renk} />}
      </div>
      <p style={{ margin: '0 0 14px', fontSize: 12.5, color: color.ink.muted, fontWeight: 600, lineHeight: 1.5 }}>{ozet}</p>
      <div style={{ fontSize: 12.5, color: color.ink.secondary, fontWeight: 600 }}>
        <strong style={{ ...numText, fontWeight: 800, color: color.ink.primary }}>{alan.dersSayisi}</strong> AYT dersi
      </div>
      {/* DC-birebir statik dipnot (~DC:74) — her alanın üstüne TYT ortak dersler; ink.muted (AA). */}
      <div style={{ marginTop: 14, paddingTop: 12, borderTop: `1px solid ${color.paper.borderFaint}`, fontSize: 11, color: color.ink.muted, lineHeight: 1.5 }}>
        TYT ortak: Türkçe · Matematik · Fen · Sosyal
      </div>
    </div>
  );
}

// ---- Ders akordeonu (TEK-AÇILIR; ünite başlığı + numaralı konu + koşullu coral şerit) ----
function numaraliUniteler(uniteler: AlanKutuphaneDers['uniteler']): { ad: string; konular: { n: number; ad: string }[] }[] {
  let n = 0;
  return uniteler.map((u) => ({
    ad: u.ad,
    konular: u.konular.map((k) => ({ n: (n += 1), ad: k })),
  }));
}

function DersKart({ ders, open, onToggle }: { ders: AlanKutuphaneDers; open: boolean; onToggle: () => void }) {
  const renk = DERS_RENK[ders.ders] ?? color.ink.muted;
  const tint = DERS_TINT[renk] ?? color.paper.subtle;
  const harf = (ders.ad || '?').charAt(0);
  const panelId = `alan-kat-${ders.ders}`;
  const gruplar = numaraliUniteler(ders.uniteler);

  return (
    <div style={{ boxSizing: 'border-box', background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 14, padding: '16px 18px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
        <span aria-hidden style={{ width: 32, height: 32, flexShrink: 0, borderRadius: 9, background: tint, color: renk, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 13 }}>{harf}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: color.ink.primary, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{ders.ad}</div>
          <div style={{ ...numText, fontSize: 11, color: color.ink.muted, fontWeight: 600 }}>{ders.konuToplam} konu</div>
        </div>
      </div>

      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        aria-label={`${ders.ad}: ${open ? 'Konuları gizle' : `${ders.konuToplam} konunun tamamını gör`}`}
        {...(open ? { 'aria-controls': panelId } : {})}
        style={{ boxSizing: 'border-box', width: '100%', minHeight: 44, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 7, padding: '10px 12px', border: `1px solid ${color.paper.border}`, borderRadius: 10, background: color.paper.subtle, color: color.ink.secondary, fontFamily: font.sans, fontSize: 12, fontWeight: 700, cursor: 'pointer' }}
      >
        {open ? 'Konuları gizle' : `${ders.konuToplam} konunun tamamını gör`}
        <Chevron open={open} />
      </button>

      {open && (
        <div id={panelId} style={{ boxSizing: 'border-box', marginTop: 12, paddingTop: 12, borderTop: `1px solid ${color.paper.borderFaint}`, display: 'flex', flexDirection: 'column', gap: 5 }}>
          {gruplar.map((gr) => (
            <div key={gr.ad} style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
              <div style={{ margin: '8px 0 2px', paddingLeft: 32, fontSize: 10.5, fontWeight: 800, letterSpacing: '0.06em', color: color.semantic.riskTextOnLight, textTransform: 'uppercase' }}>{gr.ad}</div>
              {gr.konular.map((kn) => (
                <div key={kn.ad} style={{ display: 'flex', alignItems: 'baseline', gap: 10, padding: '5px 4px' }}>
                  <span style={{ ...numText, width: 22, flexShrink: 0, textAlign: 'right', fontSize: 11, fontWeight: 800, color: color.ink.muted }}>{kn.n}</span>
                  <span style={{ fontSize: 12.5, fontWeight: 600, color: color.ink.primary }}>{kn.ad}</span>
                </div>
              ))}
            </div>
          ))}
          {ders.soruSayisi > 0 && (
            <div style={{ boxSizing: 'border-box', marginTop: 8, display: 'flex', alignItems: 'center', gap: 8, padding: '9px 12px', background: '#FFF3EE', border: '1px solid #F6D9CB', borderRadius: 10 }}>
              {Kitap}
              <span style={{ ...numText, fontSize: 11.5, fontWeight: 700, color: color.dawn.coralTextOnLight }}>{ders.soruSayisi} örnek soru çözümüyle havuzda</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function AlanKutuphanePage(): React.ReactElement {
  const dar900 = useMedia('(max-width: 900px)');
  const dar680 = useMedia('(max-width: 680px)');

  const [data, setData] = React.useState<AlanKutuphaneData | null>(null);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);
  const [acik, setAcik] = React.useState<string | null>(null);

  React.useEffect(() => {
    let alive = true;
    setData(null);
    setHata(false);
    getAlanKutuphane()
      .then((d) => { if (alive) setData(d); })
      .catch(() => { if (alive) setHata(true); });
    return () => { alive = false; };
  }, [yeniden]);

  // TEK-AÇILIR: aynı ders açıksa kapat, değilse yalnız onu aç.
  const toggle = (ders: string) => setAcik((prev) => (prev === ders ? null : ders));

  const alanGrid: React.CSSProperties = {
    display: 'grid', gridTemplateColumns: dar900 ? '1fr' : 'repeat(3, minmax(0,1fr))', gap: 16, marginBottom: 38, alignItems: 'start',
  };
  const katalogGrid: React.CSSProperties = {
    display: 'grid', gridTemplateColumns: dar680 ? '1fr' : 'repeat(2, minmax(0,1fr))', gap: 14, alignItems: 'start',
  };

  const dersSayisi = data?.dersler.length ?? 0;
  const konuToplam = (data?.dersler ?? []).reduce((acc, d) => acc + d.konuToplam, 0);
  // Katalog dolu (savunma amaçlı empty; normal akışta gösterilmez — katalog daima dolu).
  const bosMu = data != null && data.dersler.length === 0 && data.alanlar.length === 0;

  return (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={{ boxSizing: 'border-box', minHeight: '100vh', width: '100%', overflowX: 'hidden', background: color.paper.bg, fontFamily: font.sans, color: color.ink.primary }}>
        <main style={{ boxSizing: 'border-box', maxWidth: 1080, width: '100%', margin: '0 auto', padding: dar680 ? '28px 20px 70px' : '34px 40px 80px' }}>

          {/* Header — geri-oku + başlık (statik anlatı) */}
          <header style={{ boxSizing: 'border-box', display: 'flex', alignItems: 'flex-start', gap: 14, marginBottom: 30 }}>
            <a
              href="/panel"
              aria-label="Panele dön"
              style={{ boxSizing: 'border-box', width: 38, height: 38, flexShrink: 0, marginTop: 4, border: `1px solid ${color.paper.border}`, background: color.paper.card, borderRadius: 11, display: 'flex', alignItems: 'center', justifyContent: 'center', color: color.ink.muted, textDecoration: 'none' }}
            >
              {Geri}
            </a>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 11.5, fontWeight: 800, letterSpacing: '0.09em', color: color.dawn.coralTextOnLight, textTransform: 'uppercase', marginBottom: 8 }}>Kapsam · Üç YKS Alanı</div>
              <h1 style={{ margin: 0, fontFamily: font.serif, fontWeight: 400, fontSize: 40, lineHeight: 1.04, color: color.ink.primary }}>Alan Kütüphanesi</h1>
              <p style={{ margin: '11px 0 0', fontSize: 15, color: color.ink.muted, maxWidth: 600, lineHeight: 1.6 }}>
                KIRO2 yalnız Sayısal değil — <strong style={{ color: color.ink.primary }}>Sayısal, Eşit Ağırlık ve Sözel</strong> alanlarının tamamını, her ders ünite düzeyinde içerikle kapsar.
              </p>
            </div>
          </header>

          {/* 3-durum merdiveni: error → loading → (empty savunma) → içerik */}
          {hata ? (
            <ErrorState
              serifTitle="Alan kütüphanesi şu an gelmedi."
              body="Sorun sende değil — bağlantı bir soluklandı, içerik güvende. Hazır olduğunda yeniden dene."
              onRetry={() => setYeniden((n) => n + 1)}
            />
          ) : data === null ? (
            <div aria-busy="true" aria-label="Alan kütüphanesi yükleniyor">
              <div style={{ ...alanGrid }}>
                {[0, 1, 2].map((i) => (
                  <div key={i} style={{ boxSizing: 'border-box', background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 18, padding: 22 }}>
                    <Skeleton shape="card" delayMs={0} slowAfterMs={null} />
                  </div>
                ))}
              </div>
              <div style={{ ...katalogGrid }}>
                {[0, 1, 2, 3].map((i) => (
                  <div key={i} style={{ boxSizing: 'border-box', background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 14, padding: '16px 18px' }}>
                    <Skeleton shape="row" delayMs={0} />
                  </div>
                ))}
              </div>
            </div>
          ) : bosMu ? (
            <EmptyState
              serifTitle="Alan içeriği hazırlanıyor."
              body="Ders envanteri birazdan burada olacak. Şimdilik bugünkü planına dönebilirsin."
            />
          ) : (
            <>
              {/* 3-alan kart ızgarası */}
              <div style={alanGrid}>
                {data.alanlar.map((a) => (
                  <AlanKart key={a.key} alan={a} senin={a.key === data.seninKey} />
                ))}
              </div>

              {/* Katalog başlığı */}
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap', marginBottom: 16 }}>
                <h2 style={{ margin: 0, fontSize: 19, fontWeight: 800, letterSpacing: '-0.02em', color: color.ink.primary }}>Tüm dersler · içerik derinliği</h2>
                <span style={{ ...numText, fontSize: 12.5, color: color.ink.muted }}>{dersSayisi} ders · {konuToplam}+ konu</span>
              </div>

              {/* Katalog ızgarası — TEK-AÇILIR akordeonlar */}
              <div style={katalogGrid}>
                {data.dersler.map((d) => (
                  <DersKart key={d.ders} ders={d} open={acik === d.ders} onToggle={() => toggle(d.ders)} />
                ))}
              </div>

              <p style={{ margin: '26px 0 0', fontSize: 12, color: color.ink.muted, lineHeight: 1.6, maxWidth: 640 }}>
                Senin alanının verisi konu-altı atom düzeyine kadar derindir; Eşit Ağırlık ve Sözel dersleri de tam konu envanteri ve çözümlü örnek soru çekirdeği taşır. Her ders aynı motorla işler — adaptif zorluk ve aralıklı tekrar.
              </p>
            </>
          )}
        </main>
      </div>
    </KiroThemeProvider>
  );
}

export default AlanKutuphanePage;
