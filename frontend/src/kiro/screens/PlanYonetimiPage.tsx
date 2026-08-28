// ============================================================================
// KIRO2 — Plan Yönetimi (SPRINT10-B · Grup 8 billing · KIRO2 Plan Yonetimi.dc.html)
// Tema = PAPER (iş/yönetim yüzeyi, DC-kanıtlı). SideNav YOK — ortalı (max 680):
// geri + marka + durum pili · serif hero · koşullu iptal-bandı · plan kartı ·
// fatura geçmişi VEYA soft-empty · koşullu iptal kartı · dipnot.
//
// ROL DİLİ: veli = SİZ (resmi). ÖĞRENCİ FİYAT GİZLİ (KVKK): rol=ogrenci →
//   fiyat/plan/iptal GÖSTERMEZ → paylaşılan VeliYonlendirmeKarti (baglam='yonetim').
// SUNUCU-OTORİTE: durum/plan/fiyat/yenileme-tarih/ödemeYöntem(son4)/faturalar +
//   iptal/geri-aç sonucu getAbonelikYonetim/post*'tan — istemci fiyat/tarih ÜRETMEZ.
// İSİM: bu "Plan" = ABONELİK planı (AbonelikYonetim); çalışma planı (Plan*/PlanWeek)
//   BAMBAŞKA — dokunulmadı.
//
// KANON: iptal düğmesi destructive-RED DEĞİL → coral METİN #C2452B; risk/uyarı =
//   sıcak AMBER (alarm-kırmızısı YOK); success-yeşil "Ödendi" meşru; indirim = yeşil.
//   Hareket YOK (animation/transition yok) → reduced-motion guard'ı gerekmez.
//   box-sizing:border-box HER padded container (kök dahil); hit-target ≥44 (≤1199).
// ============================================================================
import * as React from 'react';

import {
  getAbonelikYonetim,
  postAbonelikIptal,
  postAbonelikGeriAc,
  getFaturaMakbuz,
} from '../api/api-client';
import { color, font } from '../tokens';
import type { AbonelikYonetim } from '../types';
import { KiroThemeProvider, numText } from '../ui/theme';
import { Button } from '../ui/Button';
import { ErrorState } from '../ui/ErrorState';
import { Skeleton } from '../ui/Skeleton';
import { VeliYonlendirmeKarti } from './billing/VeliYonlendirmeKarti';
import '../tokens/tokens.css';

type Rol = 'veli' | 'ogrenci';
type Durum = 'aktif' | 'deneme' | 'iptal';

const CORAL = color.dawn.coralTextOnLight; // #C2452B — açık-zeminde coral METİN (AA)
const CORAL_BG = color.dawn.coralCtaBg; // #C2452B — beyaz-metin coral CTA zemini
const AMBER_TXT = color.semantic.riskTextOnLight; // #9A5D0D — açık-zeminde amber METİN (AA)
const AMBER_BG = color.semantic.riskBgSoft; // #FBF0DE
const AMBER_BORDER = color.semantic.riskBorderSoft; // #F2D9AC
const GREEN_TXT = color.semantic.successTextOnLight; // #047857 — success METİN (AA)
const GREEN_BG = '#E4F7F0'; // yeşil pil zemini (paper)

const trNum = (n: number): string => new Intl.NumberFormat('tr-TR').format(n);
const fmtTL = (n: number): string => '₺' + trNum(n);

/** Rol çözümü: ?rol query önceliklidir (DC ile birebir), yoksa prop. */
function rolCoz(propRol: Rol): Rol {
  if (typeof window === 'undefined') return propRol;
  try {
    const q = new URLSearchParams(window.location.search).get('rol');
    return q === 'ogrenci' ? 'ogrenci' : q === 'veli' ? 'veli' : propRol;
  } catch {
    return propRol;
  }
}

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

// ---- Bespoke SVG seti (emoji / stok-ikon YOK) ----
const BackIkon = (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
  </svg>
);
const LogoIkon = (
  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M12 3 3 8l9 5 9-5-9-5Z" /><path d="M3 16l9 5 9-5" /><path d="M3 12l9 5 9-5" />
  </svg>
);
const InfoIkon = (
  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke={AMBER_TXT} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, marginTop: 1 }} aria-hidden>
    <circle cx="12" cy="12" r="9" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
  </svg>
);
const CalendarIkon = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color.ink.muted} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, marginTop: 2 }} aria-hidden>
    <rect x="3" y="4" width="18" height="18" rx="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" />
  </svg>
);
const CardIkon = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color.ink.muted} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }} aria-hidden>
    <rect x="2" y="5" width="20" height="14" rx="2" /><line x1="2" y1="10" x2="22" y2="10" />
  </svg>
);

// ---- Ortak yüzey stilleri ----
const kartStil: React.CSSProperties = {
  boxSizing: 'border-box',
  background: color.paper.card,
  border: `1px solid ${color.paper.border}`,
  borderRadius: 20,
  padding: 24,
  marginBottom: 18,
};
const h2Stil: React.CSSProperties = { margin: 0, fontFamily: font.sans, fontSize: 15.5, fontWeight: 700, color: color.ink.primary };

// ---- Durum pili (kanon renk: aktif=success yeşil · deneme/iptal=amber; DC copy birebir) ----
function DurumPili({ durum }: { durum: Durum }) {
  const yesil = durum === 'aktif';
  const label = durum === 'iptal' ? 'Premium · İptal edildi' : durum === 'deneme' ? 'Premium · Deneme' : 'Premium · Aktif';
  return (
    <span
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 6, fontFamily: font.sans,
        fontSize: 11.5, fontWeight: 800, padding: '5px 11px', borderRadius: 999,
        background: yesil ? GREEN_BG : AMBER_BG, color: yesil ? GREEN_TXT : AMBER_TXT,
      }}
    >
      {label}
    </span>
  );
}

// ---- Marka barı (geri + logo + KIRO2 Premium + koşullu durum pili) ----
function MarkaBar({ backHref, durum }: { backHref: string; durum?: Durum }) {
  return (
    <header style={{ boxSizing: 'border-box', display: 'flex', alignItems: 'center', gap: 13, marginBottom: 26 }}>
      <a
        href={backHref}
        aria-label="Geri"
        style={{
          boxSizing: 'border-box', width: 44, height: 44, flexShrink: 0, border: `1px solid ${color.paper.border}`,
          background: color.paper.card, borderRadius: 11, display: 'inline-flex', alignItems: 'center',
          justifyContent: 'center', color: color.ink.muted, textDecoration: 'none',
        }}
      >
        {BackIkon}
      </a>
      <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
        <span aria-hidden style={{ width: 30, height: 30, borderRadius: 9, background: CORAL_BG, display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
          {LogoIkon}
        </span>
        <span style={{ fontWeight: 800, fontSize: 16 }}>KIRO<span style={{ color: CORAL }}>2</span> Premium</span>
      </div>
      <div style={{ flex: 1 }} />
      {durum ? <DurumPili durum={durum} /> : null}
    </header>
  );
}

const PAGE_ROOT: React.CSSProperties = {
  boxSizing: 'border-box', minHeight: '100vh', width: '100%', background: color.paper.bg,
  fontFamily: font.sans, color: color.ink.primary, fontSize: 14, lineHeight: 1.55,
};

export interface PlanYonetimiPageProps {
  /** Varsayılan 'veli'; ?rol query'si override eder (DC ile birebir). */
  rol?: Rol;
}

export function PlanYonetimiPage({ rol: rolProp = 'veli' }: PlanYonetimiPageProps): React.ReactElement {
  const rol = React.useMemo(() => rolCoz(rolProp), [rolProp]);
  const cocukBaglam = rol === 'ogrenci';
  const dar560 = useMedia('(max-width: 560px)');

  const [data, setData] = React.useState<AbonelikYonetim | null>(null);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);
  const [durumOverride, setDurumOverride] = React.useState<Durum | null>(null);
  const [iptalTarihOverride, setIptalTarihOverride] = React.useState<string | null>(null);
  const [isliyor, setIsliyor] = React.useState(false);

  React.useEffect(() => {
    if (cocukBaglam) return; // ÖĞRENCİ FİYAT GİZLİ → veri çekilmez (yönlendirme kartı)
    let alive = true;
    setHata(false);
    getAbonelikYonetim(rol)
      .then((d) => {
        if (!alive) return;
        setData(d);
        setDurumOverride(null);
        setIptalTarihOverride(null);
      })
      .catch(() => {
        if (alive) setHata(true);
      });
    return () => {
      alive = false;
    };
  }, [rol, yeniden, cocukBaglam]);

  const container = (children: React.ReactNode) => (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={PAGE_ROOT}>
        <div style={{ boxSizing: 'border-box', maxWidth: 680, margin: '0 auto', padding: dar560 ? '24px 20px 80px' : '24px 30px 80px' }}>
          {children}
        </div>
      </div>
    </KiroThemeProvider>
  );

  // ÖĞRENCİ: fiyat/plan/iptal GÖSTERİLMEZ → paylaşılan yönlendirme kartı (KVKK).
  // MarkaBar YOK (Abonelik öğrenci dalıyla birebir salt-kart düzeni): "KIRO2 Premium"
  // tier adı öğrenciye sızmaz — plan adı gösterilmez. Tek eylem kartın içindeki
  // "Veli hesabına git" CTA'sıdır.
  if (cocukBaglam) {
    return container(
      <div style={{ paddingTop: 32, boxSizing: 'border-box' }}>
        <VeliYonlendirmeKarti baglam="yonetim" />
      </div>,
    );
  }

  // --- Türetilenler (sunucu verisinden; istemci fiyat/tarih ÜRETMEZ) ---
  const bazDurum: Durum = data?.durum ?? 'aktif';
  const durum: Durum = durumOverride ?? bazDurum;
  const iptal = durum === 'iptal';
  const deneme = durum === 'deneme';
  const denemeKokenli = bazDurum === 'deneme';
  const aylik = data?.fatura === 'aylik';
  const plan = data?.plan;

  const yenilemeTarih = data?.yenilemeTarih ?? '';
  const denemeBitis = data?.denemeBitis ?? yenilemeTarih;
  const donemSonu = denemeKokenli ? denemeBitis : yenilemeTarih;
  const iptalBitis = iptalTarihOverride ?? donemSonu;

  const fiyat = plan ? fmtTL(aylik ? plan.fiyatAy : plan.fiyatYil) : '';
  const fiyatBirim = aylik ? '/ay' : '/yıl';
  const faturaLabel = aylik ? 'Aylık' : 'Yıllık';

  const yenilemeSatiri = iptal
    ? `Yenileme yok — erişim ${iptalBitis} gününe kadar açık kalır.`
    : deneme
      ? `İlk ödeme ${denemeBitis} · ${fiyat}${fiyatBirim} — deneme bitmeden e-postayla hatırlatırız; sessizce ücret alınmaz.`
      : `Sonraki yenileme ${yenilemeTarih} · ${fiyat}${fiyatBirim} — yenilemeden önce e-postayla hatırlatırız.`;

  const planChip = iptal ? 'Dönem sonuna dek açık' : deneme ? 'Deneme sürüyor' : 'Aktif';
  const planChipYesil = !iptal && !deneme;

  const iptalBaslik = denemeKokenli
    ? 'Deneme iptal edildi — ücret alınmadı.'
    : `İptal edildi — ${iptalBitis} gününe kadar her şey açık.`;

  const iptalAciklama = deneme
    ? 'Tek dokunuş — soru sorulmaz. Deneme sırasında iptal ederseniz hiç ücret alınmaz.'
    : `Tek dokunuş — soru sorulmaz. ${donemSonu} gününe kadar her şey açık kalır.`;

  const faturaBosMetni = iptal
    ? 'Fatura yok — deneme sırasında iptal edildi, hiç ücret alınmadı.'
    : 'Henüz fatura yok — deneme sürüyor, bugün ödeme alınmadı. İlk faturadan önce e-postayla hatırlatırız.';

  const faturalar = data?.faturalar ?? [];
  const oy = data?.odemeYontem;

  // --- Sunucu-otoriter aksiyonlar (istemci sonuç ÜRETMEZ) ---
  const iptalEt = () => {
    setIsliyor(true);
    postAbonelikIptal()
      .then((r) => {
        setIptalTarihOverride(r.iptalTarih);
        setDurumOverride('iptal');
      })
      .catch(() => undefined)
      .finally(() => setIsliyor(false));
  };
  // Geri aç → SUNUCU-OTORİTE: post sonrası getAbonelikYonetim(rol) yeniden çek;
  // durum/iptal-tarih sunucu yanıtından türer (istemci 'deneme'/'aktif' TÜRETMEZ).
  const geriAc = () => {
    setIsliyor(true);
    postAbonelikGeriAc()
      .then(() => getAbonelikYonetim(rol))
      .then((d) => {
        setData(d);
        setDurumOverride(null);
        setIptalTarihOverride(null);
      })
      .catch(() => undefined)
      .finally(() => setIsliyor(false));
  };
  const acMakbuz = (id: string) => {
    getFaturaMakbuz(id)
      .then(({ href }) => {
        if (typeof document === 'undefined') return;
        // Sunucu-otoriter href yeni sekmede açılır (jsdom-güvenli: programatik anchor).
        const a = document.createElement('a');
        a.href = href;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        a.click();
      })
      .catch(() => undefined);
  };

  const heroAlt = 'Değişiklikler anında uygulanır; öğrenci fiyat ya da fatura ekranı görmez.';
  const dipnot = 'Fiyat ve fatura yalnız veli hesabında görünür. Takıldığınız yerde destek ekibi okul saatlerinde ~10 dk içinde döner.';

  return container(
    <>
      <MarkaBar backHref="/veli" durum={hata || data === null ? undefined : durum} />

      {/* hero — serif (his) */}
      <div style={{ marginBottom: 22 }}>
        <h1 style={{ margin: '0 0 8px', fontFamily: font.serif, fontWeight: 400, fontStyle: 'italic', fontSize: 34, lineHeight: 1.08, color: color.ink.primary }}>
          Planını yönet.
        </h1>
        <p style={{ margin: 0, fontSize: 14, color: color.ink.muted, lineHeight: 1.6 }}>{heroAlt}</p>
      </div>

      {hata ? (
        <ErrorState
          serifTitle="Plan bilgisi şu an gelmedi."
          body="Sorun sizde değil — bağlantı bir an duraksadı, aboneliğiniz güvende. Birazdan yeniden deneyebilirsiniz."
          onRetry={() => setYeniden((n) => n + 1)}
          retryLabel="Yeniden dene"
        />
      ) : data === null ? (
        <div aria-busy="true" aria-label="Plan yükleniyor" style={{ display: 'grid', gap: 18 }}>
          <div style={{ ...kartStil, marginBottom: 0 }}><Skeleton shape="card" delayMs={0} slowAfterMs={null} /></div>
          <div style={{ ...kartStil, marginBottom: 0 }}><Skeleton shape="row" delayMs={0} /></div>
        </div>
      ) : (
        <>
          {/* iptal bilgi bandı (durum=iptal) */}
          {iptal ? (
            <div role="status" style={{ boxSizing: 'border-box', display: 'flex', alignItems: 'flex-start', gap: 12, padding: '14px 16px', background: AMBER_BG, border: `1px solid ${AMBER_BORDER}`, borderRadius: 14, marginBottom: 18 }}>
              {InfoIkon}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 13.5, fontWeight: 700, color: AMBER_TXT }}>{iptalBaslik}</div>
                <div style={{ fontSize: 12.5, fontWeight: 600, color: AMBER_TXT, marginTop: 2 }}>
                  Fikriniz değişirse tek dokunuşla geri açılır; yeniden kart bilgisi gerekmez.
                </div>
              </div>
              <div style={{ flexShrink: 0 }}>
                <Button variant="primary" onClick={geriAc} disabled={isliyor}>Geri aç</Button>
              </div>
            </div>
          ) : null}

          {/* plan kartı */}
          <section style={kartStil}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: CORAL, letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                  {plan?.ad ?? 'Premium'} · {faturaLabel}
                </div>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 5, marginTop: 6 }}>
                  <span style={{ ...numText, fontSize: 30, fontWeight: 800, letterSpacing: '-0.02em' }}>{fiyat}</span>
                  <span style={{ fontSize: 13, color: color.ink.muted, fontWeight: 600 }}>{fiyatBirim}</span>
                </div>
                <div style={{ fontSize: 12.5, color: color.ink.muted, fontWeight: 600, marginTop: 2 }}>
                  {aylik
                    ? 'Aylık faturalanır · esnek.'
                    : `Tek ödeme — yıllıkta %${trNum(plan?.indirimYuzde ?? 0)} avantaj.`}
                </div>
              </div>
              <div style={{ flex: 1 }} />
              <span
                style={{
                  display: 'inline-flex', alignItems: 'center', height: 26, padding: '0 11px', borderRadius: 999,
                  fontSize: 11.5, fontWeight: 800,
                  background: planChipYesil ? GREEN_BG : AMBER_BG, color: planChipYesil ? GREEN_TXT : AMBER_TXT,
                }}
              >
                {planChip}
              </span>
            </div>

            <div style={{ borderTop: `1px solid ${color.paper.borderFaint}`, marginTop: 18, paddingTop: 16, display: 'flex', flexDirection: 'column', gap: 13 }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 11 }}>
                {CalendarIkon}
                <div style={{ fontSize: 13, color: color.ink.secondary, fontWeight: 600, lineHeight: 1.55 }}>{yenilemeSatiri}</div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 11, flexWrap: 'wrap' }}>
                {CardIkon}
                <span style={{ fontSize: 13, color: color.ink.secondary, fontWeight: 600 }}>
                  {oy ? oy.tur : 'Kayıtlı kart'} <span style={{ ...numText, letterSpacing: '0.06em' }}>•••• {oy?.son4 ?? '••••'}</span>
                  {oy?.sonKullanma ? ` · ${oy.sonKullanma}` : ''}
                </span>
                <a
                  href="/odeme?rol=veli"
                  style={{ boxSizing: 'border-box', marginLeft: 'auto', display: 'inline-flex', alignItems: 'center', minHeight: 44, fontSize: 12.5, fontWeight: 700, color: CORAL, textDecoration: 'none' }}
                >
                  Kartı değiştir
                </a>
              </div>
            </div>
          </section>

          {/* fatura geçmişi */}
          <section style={kartStil}>
            <h2 style={{ ...h2Stil, marginBottom: 14 }}>Fatura geçmişi</h2>
            {faturalar.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                {faturalar.map((f) => (
                  <div
                    key={f.id}
                    style={{
                      boxSizing: 'border-box', display: 'grid',
                      gridTemplateColumns: dar560 ? '1fr auto' : '1.2fr 1fr auto auto',
                      gap: 12, alignItems: 'center', padding: '11px 2px', borderBottom: `1px solid ${color.paper.borderFaint}`,
                    }}
                  >
                    <span style={{ ...numText, fontSize: 13, fontWeight: 700 }}>{f.tarih}</span>
                    {!dar560 ? (
                      <span style={{ fontSize: 12.5, fontWeight: 600, color: color.ink.muted }}>{plan?.ad ?? 'Premium'} · {faturaLabel}</span>
                    ) : null}
                    <span style={{ ...numText, fontSize: 13, fontWeight: 800, textAlign: 'right' }}>{fmtTL(f.tutar)}</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, justifyContent: 'flex-end' }}>
                      <span
                        style={{
                          display: 'inline-flex', alignItems: 'center', height: 23, padding: '0 9px', borderRadius: 999,
                          background: f.durum === 'odendi' ? GREEN_BG : AMBER_BG, color: f.durum === 'odendi' ? GREEN_TXT : AMBER_TXT,
                          fontSize: 10.5, fontWeight: 800,
                        }}
                      >
                        {f.durum === 'odendi' ? 'Ödendi' : 'Bekliyor'}
                      </span>
                      <button
                        type="button"
                        onClick={() => acMakbuz(f.id)}
                        style={{ boxSizing: 'border-box', display: 'inline-flex', alignItems: 'center', minHeight: 44, padding: '0 4px', border: 'none', background: 'none', fontFamily: font.sans, fontSize: 12, fontWeight: 700, color: color.ink.muted, cursor: 'pointer' }}
                      >
                        Makbuz
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ margin: 0, fontSize: 13, color: color.ink.muted, fontWeight: 600, lineHeight: 1.6 }}>{faturaBosMetni}</p>
            )}
          </section>

          {/* iptal kartı (durum aktif/deneme ise) */}
          {!iptal ? (
            <section style={kartStil}>
              <h2 style={{ ...h2Stil, marginBottom: 6 }}>İptal</h2>
              <p style={{ margin: '0 0 16px', fontSize: 13, color: color.ink.muted, fontWeight: 600, lineHeight: 1.6 }}>{iptalAciklama}</p>
              {/* Kanon: iptal düğmesi destructive-RED DEĞİL → coral METİN #C2452B, beyaz zemin, kenarlık. */}
              <button
                type="button"
                onClick={iptalEt}
                disabled={isliyor}
                style={{
                  boxSizing: 'border-box', minHeight: 44, padding: '0 18px', border: `1px solid ${color.paper.border}`,
                  borderRadius: 11, background: color.paper.card, color: CORAL, fontFamily: font.sans,
                  fontSize: 13.5, fontWeight: 700, cursor: isliyor ? 'default' : 'pointer',
                }}
              >
                Aboneliği iptal et
              </button>
            </section>
          ) : null}

          <p style={{ boxSizing: 'border-box', margin: '6px auto 0', textAlign: 'center', fontSize: 12, color: color.ink.muted, maxWidth: 440, lineHeight: 1.6 }}>{dipnot}</p>
        </>
      )}
    </>,
  );
}

export default PlanYonetimiPage;
