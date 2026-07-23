// ============================================================================
// KIRO2 — Ödeme (3-fazlı composite · SPRINT10-B · KIRO2 Odeme.dc.html)
// Tema = PAPER. Merkezi kart-akışı (SideNav YOK; GirisPage/VeliBaglamaPage kabuğu
// emsal). VELİ-BAĞLAMI (ödeyen) → dil resmi SİZ. Durum makinesi: form → 3ds → tamam.
// Rota /odeme (?rol=veli&fatura={donem}); Abonelik CTA buraya, başarı → Plan Yönetimi.
//
// SAF-MOCK: gerçek PSP (iyzico/PayTR/Stripe) YOK. Kart alanları PCI: UI-only, gerçek
// backend'e GİTMEZ. 3DS = timer-sim (getOdeme3dsSonuc; sunucu-otorite). SUNUCU-OTORİTE:
// tutar/planAd/ilkOdemeTarih/3DS-sonucu SUNUCUDAN — istemci fiyat HESAPLAMAZ, 3DS
// sonucu ÜRETMEZ (getOdeme3dsSonuc döndürür). Fiyat modeli veliDashboard.premium+roi
// ile HİZALI (istemci çelişen 2. model üretmez).
//
// KANON: CTA = coralCtaBg #C2452B + beyaz (DC ham #FF6F5C AA-değil → çekildi); açık
// zeminde coral METİN #C2452B; risk/banka-red = sıcak AMBER (#9A5D0D metin, alarm-kırmızı
// YOK); indirim/başarı = yeşil success; bespoke SVG (emoji YOK); serif italik H1 +
// tabular sayı. 3DS spinner @keyframes → useReducedMotion guard ZORUNLU; süre <600ms
// (Motion Kanonu). box-sizing:border-box HER padded container (KÖK dahil); hit≥44.
// KOPYA: DC birebir; SEN→SİZ (veli) ve fiyat-rakamları (sunucu) copyDeviations'ta.
// ============================================================================
import * as React from 'react';

import {
  configureKiroApi,
  getOdemeOzeti,
  postOdemeDeneme,
  getOdeme3dsSonuc,
} from '../api/api-client';
import type { MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';
import type {
  OdemeFaz,
  OdemeOzeti,
  KartFormState,
  ThreeDSDurum,
  PlanTier,
  FaturaDonem,
} from '../types';
import { color, font, radius } from '../tokens';
import { KiroThemeProvider, numText } from '../ui/theme';
import { useReducedMotion } from '../ui/ConfettiDawn';
import { Card, Callout, IconBadge, Skeleton, ErrorState } from '../ui';
import { VeliYonlendirmeKarti } from './billing/VeliYonlendirmeKarti';
import '../tokens/tokens.css';

configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });

// --- DC-özgü sıcak tint'ler (token karşılığı yok; dekoratif ham hex istisnası) -----
const HERO_BG = `radial-gradient(1200px 500px at 50% -10%, #FFF3EE 0%, ${color.paper.bg} 60%)`;
const CARD_SHADOW = '0 1px 2px rgba(16,24,40,.04), 0 12px 34px -20px rgba(16,24,40,.16)';
const INPUT_BG = color.paper.subtle;
const SPIN_KEYFRAMES = '@keyframes kiroSpin { to { transform: rotate(360deg); } }';

// Ödeme SAF-MOCK: yalnız Premium satın alınabilir (free ücretsiz — ödeme yok).
const PURCHASABLE_TIER: PlanTier = 'premium';

// --- Client-side ön-kontrol ipuçları (DC birebir; sunucu çağrısından önce) ----------
const HINT = {
  ad: 'Kart üzerindeki ismi de alalım.',
  numara: 'Kart numarası 16 haneli olmalı — acele yok.',
  skt: 'Son kullanma AA/YY biçiminde olsun.',
  cvv: 'Güvenlik kodu kartın arkasındaki 3 hane.',
  // ONAY BEKLER (inferred) — ağ/sunucu hatası (alarm dili YOK, SİZ).
  genel: 'Bağlantı bir soluklandı — kartınız güvende, birazdan tekrar deneyin.',
  // 3DS reddedildi → forma dön (DC "bankan..." → SİZ).
  reddedildi: 'Kart bu sefer onaylanmadı — bankanız engellemiş olabilir; başka kartla deneyin ya da bize yazın.',
} as const;

// --- Bespoke ikonlar (emoji/stok-ikon YOK) ------------------------------------------
const DiamondIcon = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M12 3 3 8l9 5 9-5-9-5Z" /><path d="M3 16l9 5 9-5M3 12l9 5 9-5" />
  </svg>
);
const InfoIcon = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color.semantic.riskTextOnLight} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }} aria-hidden>
    <circle cx="12" cy="12" r="9" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
  </svg>
);
const LockMini = (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={color.ink.muted} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" />
  </svg>
);
const CheckMini = (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <polyline points="20 6 9 17 4 12" />
  </svg>
);
const Chevron = (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke={color.ink.faded2} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <polyline points="9 18 15 12 9 6" />
  </svg>
);
const ArrowRight = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
  </svg>
);
const ShieldIcon = (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={color.dawn.coralTextOnLight} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);
const BigCheck = (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke={color.semantic.success} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

// --- Yardımcılar ---------------------------------------------------------------------

/** jsdom matchMedia'sız SSR-guard'lı responsive eşleşme. */
function useMedia(query: string): boolean {
  const [esles, setEsles] = React.useState(false);
  React.useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') { return; }
    const mq = window.matchMedia(query);
    const on = (): void => setEsles(mq.matches);
    on();
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, [query]);
  return esles;
}

function fazFromQuery(): OdemeFaz | undefined {
  if (typeof window === 'undefined') { return undefined; }
  try {
    const f = new URLSearchParams(window.location.search).get('faz');
    return f === '3ds' || f === 'tamam' || f === 'form' ? f : undefined;
  } catch {
    return undefined;
  }
}

function faturaFromQuery(): FaturaDonem | undefined {
  if (typeof window === 'undefined') { return undefined; }
  try {
    const v = new URLSearchParams(window.location.search).get('fatura');
    return v === 'aylik' || v === 'yillik' ? v : undefined;
  } catch {
    return undefined;
  }
}

/** Rol: prop > ?rol query > 'veli' (satın-alma varsayılanı; öğrenci fiyat/kart görmez — KVKK). */
function rolFromUrl(): 'ogrenci' | 'veli' {
  if (typeof window === 'undefined') { return 'veli'; }
  try {
    return new URLSearchParams(window.location.search).get('rol') === 'ogrenci' ? 'ogrenci' : 'veli';
  } catch {
    return 'veli';
  }
}

/** Tutar metni — SUNUCUDAN gelen sayı; istemci fiyat HESAPLAMAZ (tabular). */
function tutarText(o: OdemeOzeti): string {
  const suffix = o.fatura === 'yillik' ? '/yıl' : '/ay';
  return '₺' + new Intl.NumberFormat('tr-TR').format(o.tutar) + suffix;
}

const faturaLabel = (f: FaturaDonem): string => (f === 'yillik' ? 'Yıllık' : 'Aylık');

// Kart alan biçimlendiriciler (PCI: UI-only — gerçek backend'e GİTMEZ).
const formatNumara = (v: string): string => v.replace(/\D/g, '').slice(0, 16).replace(/(.{4})/g, '$1 ').trim();
const formatSkt = (v: string): string => {
  const d = v.replace(/\D/g, '').slice(0, 4);
  return d.length > 2 ? d.slice(0, 2) + ' / ' + d.slice(2) : d;
};
const formatCvv = (v: string): string => v.replace(/\D/g, '').slice(0, 3);

// --- Ortak stiller -------------------------------------------------------------------
const h1Serif: React.CSSProperties = {
  margin: '0 0 8px', fontFamily: font.serif, fontStyle: 'italic', fontWeight: 400,
  fontSize: 28, lineHeight: 1.12, color: color.ink.primary, outline: 'none',
};
const pAlt: React.CSSProperties = { margin: '0 0 22px', fontSize: 13.5, color: color.ink.muted, lineHeight: 1.6 };
const fieldLabel: React.CSSProperties = { display: 'block', fontSize: 12.5, fontWeight: 700, color: color.ink.secondary, marginBottom: 7 };
const fieldInput: React.CSSProperties = {
  boxSizing: 'border-box', width: '100%', height: 46, padding: '0 15px',
  border: `1px solid ${color.paper.borderStrong}`, borderRadius: 12, background: INPUT_BG,
  fontFamily: font.sans, fontSize: 14.5, color: color.ink.primary,
  // outline KALDIRILDI — global :focus-visible coral ring (tokens.css) klavye odağında görünsün (WCAG 2.4.7).
};

// --- 3DS bespoke stepper (ProgressBar DEĞİL) -----------------------------------------
type StepDurum = 'done' | 'active' | 'pending';

/** Görsel-gizli (ekran-okuyucu) durum metni — adım durumunu sesli ilan eder. */
const srOnly: React.CSSProperties = {
  position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0 0 0 0)', whiteSpace: 'nowrap',
};

function StepEtiket({ metin, durum }: { metin: string; durum: StepDurum }): React.ReactElement {
  const govde =
    durum === 'done' ? (
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: color.semantic.successTextOnLight }}>
        <span aria-hidden style={{ display: 'inline-flex' }}>{CheckMini}</span>
        <span style={{ fontSize: 12, fontWeight: 700 }}>{metin}</span>
      </span>
    ) : durum === 'active' ? (
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
        <span aria-hidden style={{ width: 7, height: 7, borderRadius: '50%', background: color.dawn.coral, display: 'inline-block' }} />
        <span style={{ fontSize: 12, fontWeight: 800, color: color.ink.primary }}>{metin}</span>
      </span>
    ) : (
      <span style={{ fontSize: 12, fontWeight: 600, color: color.ink.muted }}>{metin}</span>
    );
  // Aktif adım aria-current="step"; done/pending görünür-gizli durum metniyle ilan edilir.
  return (
    <span role="listitem" aria-current={durum === 'active' ? 'step' : undefined} style={{ display: 'inline-flex', alignItems: 'center' }}>
      {govde}
      {durum !== 'active' ? (
        <span style={srOnly}>{durum === 'done' ? ' — tamamlandı' : ' — bekliyor'}</span>
      ) : null}
    </span>
  );
}

function Stepper(): React.ReactElement {
  return (
    <div role="list" aria-label="Ödeme doğrulama adımları" style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 18, flexWrap: 'wrap', justifyContent: 'center' }}>
      <StepEtiket metin="Kart bilgisi alındı" durum="done" />
      {Chevron}
      <StepEtiket metin="Banka onayı" durum="active" />
      {Chevron}
      <StepEtiket metin="Deneme başlar" durum="pending" />
    </div>
  );
}

// --- Ödeme özeti kartı (sağ ray; SUNUCUDAN — Skeleton + Error bağlı) -----------------
function OzetKarti({
  ozet, onRetry,
}: { ozet: OdemeOzeti | null | 'error'; onRetry: () => void }): React.ReactElement {
  return (
    <Card
      radiusSize="lg"
      style={{ boxSizing: 'border-box', padding: 24, boxShadow: '0 1px 2px rgba(16,24,40,.04)' }}
    >
      <div style={{ fontSize: 11.5, fontWeight: 800, letterSpacing: '0.07em', color: color.ink.muted, textTransform: 'uppercase', marginBottom: 14 }}>
        Özet
      </div>

      {ozet === null ? (
        <div aria-busy="true" aria-live="polite">
          <Skeleton shape="card" delayMs={0} />
        </div>
      ) : ozet === 'error' ? (
        <ErrorState
          serifTitle="Özet şu an yüklenemedi."
          body="Sorun sizde değil. Ödeme güvenli — bağlantınızı kontrol edip yeniden deneyebilirsiniz."
          onRetry={onRetry}
        />
      ) : (
        <>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 11 }}>
            <OzetSatir k="Plan" v={`${ozet.planAd} · ${faturaLabel(ozet.fatura)}`} />
            <OzetSatir k="Deneme" v={`${ozet.denemeGunu} gün ücretsiz`} vRenk={color.semantic.successTextOnLight} />
            <OzetSatir k="İlk ödeme" v={ozet.ilkOdemeTarih} tabular />
            <div style={{ borderTop: `1px solid ${color.paper.borderFaint}`, paddingTop: 11 }}>
              <OzetSatir k="Sonra" v={tutarText(ozet)} tabular guclu />
            </div>
          </div>

          <div style={{ boxSizing: 'border-box', marginTop: 16, padding: '12px 14px', background: INPUT_BG, border: `1px solid ${color.paper.borderFaint}`, borderRadius: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
            <GuvenceMadde>Deneme bitmeden e-postayla hatırlatırız — sessizce ücret alınmaz.</GuvenceMadde>
            <GuvenceMadde>Tek dokunuşla iptal; soru sorulmaz.</GuvenceMadde>
            <GuvenceMadde>Deneme ve iptal kontrolü sizde; öğrenci fiyat baskısı görmez.</GuvenceMadde>
          </div>

          <div style={{ marginTop: 14, display: 'flex', alignItems: 'center', gap: 7, justifyContent: 'center' }}>
            <span aria-hidden style={{ display: 'inline-flex' }}>{LockMini}</span>
            <span style={{ fontSize: 11.5, fontWeight: 600, color: color.ink.muted }}>256-bit şifreli bağlantı · kart bilgisi bizde tutulmaz</span>
          </div>
        </>
      )}
    </Card>
  );
}

function OzetSatir({ k, v, vRenk, tabular, guclu }: { k: string; v: string; vRenk?: string; tabular?: boolean; guclu?: boolean }): React.ReactElement {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
      <span style={{ fontSize: 13, color: color.ink.muted, fontWeight: 600 }}>{k}</span>
      <span style={{ ...(tabular ? numText : {}), fontSize: guclu ? 14 : 13, fontWeight: guclu ? 800 : 700, color: vRenk ?? color.ink.primary }}>{v}</span>
    </div>
  );
}

function GuvenceMadde({ children }: { children: React.ReactNode }): React.ReactElement {
  return (
    <div style={{ display: 'flex', gap: 8, fontSize: 12, color: color.ink.secondary, lineHeight: 1.5 }}>
      <span aria-hidden style={{ flexShrink: 0, marginTop: 1, color: color.semantic.success, display: 'inline-flex' }}>{CheckMini}</span>
      <span>{children}</span>
    </div>
  );
}

// --- Ekran ---------------------------------------------------------------------------

export interface OdemePageProps {
  /** Storybook/rota: başlangıç fazı (form/3ds/tamam). Üretim: 'form' (?faz ile 3ds/tamam). */
  baslangicFazi?: OdemeFaz;
  /** Satın alınan kademe — yalnız Premium (free ücretsiz, ödeme yok). */
  tier?: PlanTier;
  /** Fatura dönemi — Abonelik CTA'sından (?fatura). Varsayılan 'aylik'. */
  fatura?: FaturaDonem;
  /** Rol: satın-alma veli varsayılan; 'ogrenci' → fiyat/kart/özet GİZLİ (VeliYonlendirmeKarti). ?rol'den de türer. */
  rol?: 'ogrenci' | 'veli';
  /** TEST/PREVIEW seam: 3DS sonucu sağlayıcı — üretimde GEÇİLMEZ (varsayılan
   *  getOdeme3dsSonuc, SUNUCU-OTORİTE). İstemci sonucu ÜRETMEZ; test/preview yalnız
   *  sunucu-yanıtını enjekte eder (banka-red/onay dalını deterministik doğrulamak için). */
  resolve3ds?: (intentId: string) => Promise<ThreeDSDurum>;
}

export function OdemePage({
  baslangicFazi,
  tier = PURCHASABLE_TIER,
  fatura: faturaProp,
  rol: rolProp,
  resolve3ds = getOdeme3dsSonuc,
}: OdemePageProps = {}): React.ReactElement {
  const reduced = useReducedMotion();
  const dar = useMedia('(max-width: 760px)');
  const rol = rolProp ?? rolFromUrl();
  const fatura = faturaProp ?? faturaFromQuery() ?? 'aylik';

  const [faz, setFaz] = React.useState<OdemeFaz>(() => baslangicFazi ?? fazFromQuery() ?? 'form');
  const [kart, setKart] = React.useState<KartFormState>({ ad: '', numara: '', sonKullanma: '', cvv: '' });
  const [hint, setHint] = React.useState('');
  const [decline, setDecline] = React.useState(false);
  // Doğrulama başarısız olan kart alanı — aria-invalid + aria-describedby hedefi (setField ile temizlenir).
  const [hataAlan, setHataAlan] = React.useState<keyof KartFormState | null>(null);
  const [gonderiliyor, setGonderiliyor] = React.useState(false);
  const [ozet, setOzet] = React.useState<OdemeOzeti | null | 'error'>(null);
  const [ozetNonce, setOzetNonce] = React.useState(0);

  const baslikRef = React.useRef<HTMLHeadingElement>(null);
  const ilk = React.useRef(true);

  // Ödeme özeti SUNUCUDAN (tutar/ilkÖdemeTarih; istemci fiyat hesaplamaz).
  // ÖĞRENCİ: fiyat GİZLİ (KVKK) → özet çekme; VeliYonlendirmeKarti render edilir.
  React.useEffect(() => {
    if (rol === 'ogrenci') { return; }
    let alive = true;
    setOzet(null);
    getOdemeOzeti(tier, fatura)
      .then((o) => { if (alive) { setOzet(o); } })
      .catch(() => { if (alive) { setOzet('error'); } });
    return () => { alive = false; };
  }, [tier, fatura, ozetNonce, rol]);

  // 3DS akışı: postOdemeDeneme → intentId → resolve3ds (SUNUCU-OTORİTE). İstemci
  // sonucu ÜRETMEZ; yalnız 'onaylandi'→tamam / 'reddedildi'→forma-dön (amber).
  const enter3ds = React.useCallback((): void => {
    setFaz('3ds');
    setDecline(false);
    setHint('');
    setHataAlan(null);
    setGonderiliyor(false);
    postOdemeDeneme()
      .then(({ intentId }) => resolve3ds(intentId))
      .then((durum) => {
        if (durum === 'onaylandi') { setFaz('tamam'); }
        else if (durum === 'reddedildi') { setFaz('form'); setDecline(true); }
        // 'bekliyor' → 3ds ekranında kal (sunucu yeniden yoklar; live-only)
      })
      .catch(() => { setFaz('form'); setHint(HINT.genel); });
  }, [resolve3ds]);

  // ?faz=3ds ile açılırsa akışı başlat (üretim/rota). Storybook '3ds' önizlemesi
  // resolve3ds'i çözülmeyen Promise geçerek statik spinner'da tutar.
  const ilkFaz = React.useRef(faz);
  React.useEffect(() => {
    if (rol !== 'ogrenci' && ilkFaz.current === '3ds') { enter3ds(); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Faz değişiminde odağı yeni başlığa taşı (odak-sırası korunur).
  React.useEffect(() => {
    if (ilk.current) { ilk.current = false; return; }
    baslikRef.current?.focus();
  }, [faz]);

  const setField = (k: keyof KartFormState, format?: (v: string) => string) => (e: React.ChangeEvent<HTMLInputElement>): void => {
    const v = format ? format(e.target.value) : e.target.value;
    setKart((s) => ({ ...s, [k]: v }));
    setHint('');
    setDecline(false);
    setHataAlan(null);
  };

  const denemeBaslat = (): void => {
    if (gonderiliyor) { return; }
    if (kart.ad.trim().length < 2) { setHint(HINT.ad); setHataAlan('ad'); return; }
    if (kart.numara.replace(/\s/g, '').length !== 16) { setHint(HINT.numara); setHataAlan('numara'); return; }
    if (kart.sonKullanma.replace(/\D/g, '').length !== 4) { setHint(HINT.skt); setHataAlan('sonKullanma'); return; }
    if (kart.cvv.length !== 3) { setHint(HINT.cvv); setHataAlan('cvv'); return; }
    setGonderiliyor(true);
    enter3ds();
  };

  const rootStyle: React.CSSProperties = {
    boxSizing: 'border-box', minHeight: '100vh', width: '100%', background: HERO_BG,
    fontFamily: font.sans, color: color.ink.primary, fontSize: 14, overflowX: 'hidden',
    display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '0 24px 40px',
  };

  return (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={rootStyle}>
        {/* Üst bar */}
        <div style={{ boxSizing: 'border-box', width: '100%', maxWidth: 880, display: 'flex', alignItems: 'center', gap: 9, padding: '22px 0 0' }}>
          <span aria-hidden style={{ width: 30, height: 30, borderRadius: 9, background: color.dawn.coralCtaBg, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{DiamondIcon}</span>
          <span style={{ fontWeight: 800, fontSize: 16 }}>KIRO<span style={{ color: color.dawn.coralTextOnLight }}>2</span></span>
          <div style={{ flex: 1, minWidth: 0 }} />
          <a href="/abonelik" style={{ boxSizing: 'border-box', display: 'inline-flex', alignItems: 'center', minHeight: 44, padding: '0 10px', fontSize: 12.5, fontWeight: 700, color: color.ink.muted, textDecoration: 'none' }}>Planlara dön</a>
        </div>

        <div style={{ boxSizing: 'border-box', width: '100%', maxWidth: 880, marginTop: '6vh' }}>

          {/* ÖĞRENCİ FİYAT GİZLİ (KVKK): rol=ogrenci → fiyat/kart/özet YOK → paylaşılan
              yönlendirme kartı (Abonelik/Plan simetrisi; satın-alma yalnız veli hesabından). */}
          {rol === 'ogrenci' ? (
            <div style={{ boxSizing: 'border-box', paddingTop: 8 }}>
              <VeliYonlendirmeKarti baglam="yonetim" />
            </div>
          ) : (
            <>

          {/* ===================== FORM ===================== */}
          {faz === 'form' ? (
            <div style={{ display: 'grid', gridTemplateColumns: dar ? '1fr' : '1fr 320px', gap: 18, alignItems: 'start' }}>

              {/* Kart formu (PCI: UI-only) */}
              <Card radiusSize="lg" style={{ boxSizing: 'border-box', padding: dar ? '26px 22px' : '30px 32px', boxShadow: CARD_SHADOW }}>
                <h1 ref={baslikRef} tabIndex={-1} style={h1Serif}>Denemeyi birlikte başlatalım.</h1>
                <p style={pAlt}>Kart bilgisi yalnız veli hesabınızda tutulur; öğrenciniz fiyat ya da ödeme ekranı görmez.</p>

                <label htmlFor="od-ad" style={fieldLabel}>Kart üzerindeki isim</label>
                <input id="od-ad" type="text" value={kart.ad} onChange={setField('ad')} placeholder="Ad Soyad" autoComplete="cc-name" aria-invalid={hataAlan === 'ad' ? true : undefined} aria-describedby={hataAlan === 'ad' ? 'od-hint' : undefined} style={fieldInput} />

                <label htmlFor="od-numara" style={{ ...fieldLabel, marginTop: 16 }}>Kart numarası</label>
                <input id="od-numara" type="text" inputMode="numeric" autoComplete="cc-number" value={kart.numara} onChange={setField('numara', formatNumara)} placeholder="0000 0000 0000 0000" aria-invalid={decline || hataAlan === 'numara' ? true : undefined} aria-describedby={decline ? 'od-decline' : hataAlan === 'numara' ? 'od-hint' : undefined} style={{ ...fieldInput, ...numText }} />

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginTop: 16 }}>
                  <div>
                    <label htmlFor="od-skt" style={fieldLabel}>Son kullanma</label>
                    <input id="od-skt" type="text" inputMode="numeric" autoComplete="cc-exp" value={kart.sonKullanma} onChange={setField('sonKullanma', formatSkt)} placeholder="AA / YY" aria-invalid={hataAlan === 'sonKullanma' ? true : undefined} aria-describedby={hataAlan === 'sonKullanma' ? 'od-hint' : undefined} style={{ ...fieldInput, ...numText }} />
                  </div>
                  <div>
                    <label htmlFor="od-cvv" style={fieldLabel}>Güvenlik kodu</label>
                    <input id="od-cvv" type="text" inputMode="numeric" autoComplete="cc-csc" value={kart.cvv} onChange={setField('cvv', formatCvv)} placeholder="CVC" aria-invalid={hataAlan === 'cvv' ? true : undefined} aria-describedby={hataAlan === 'cvv' ? 'od-hint' : undefined} style={{ ...fieldInput, ...numText }} />
                  </div>
                </div>

                {/* Banka-red (3DS decline) — canlı bölge role="alert" ile anında ilan (WCAG 4.1.3). */}
                {decline ? (
                  <div id="od-decline" role="alert" style={{ marginTop: 14 }}>
                    <Callout tone="attention" icon={InfoIcon}>{HINT.reddedildi}</Callout>
                  </div>
                ) : null}
                {/* Doğrulama ipucu bölgesi HER ZAMAN DOM'da (aria-live) — yalnız içerik değişir; boşken sessiz. */}
                <div id="od-hint" role="status" aria-live="polite" style={hint ? { marginTop: 12 } : undefined}>
                  {hint ? (
                    <Callout tone="attention" icon={InfoIcon}>{hint}</Callout>
                  ) : null}
                </div>

                <button
                  type="button"
                  onClick={denemeBaslat}
                  disabled={gonderiliyor}
                  aria-describedby={hint ? 'od-hint' : undefined}
                  style={{
                    boxSizing: 'border-box', marginTop: 20, width: '100%', height: 49, border: 'none', borderRadius: radius.button,
                    background: gonderiliyor ? color.paper.borderFaint : color.dawn.coralCtaBg,
                    color: gonderiliyor ? color.ink.faded3 : '#fff',
                    fontFamily: font.sans, fontSize: 14.5, fontWeight: 800, cursor: gonderiliyor ? 'default' : 'pointer',
                    boxShadow: gonderiliyor ? 'none' : '0 10px 22px -10px rgba(194,69,43,0.55)',
                  }}
                >
                  {gonderiliyor ? 'Bağlanıyor…' : '7 gün ücretsiz denemeyi başlat'}
                </button>
                <p style={{ margin: '14px 0 0', fontSize: 12, color: color.ink.muted, lineHeight: 1.6, textAlign: 'center' }}>
                  <strong style={{ color: color.ink.primary }}>Bugün ödeme alınmaz.</strong> Deneme bitmeden hatırlatırız; istediğiniz an tek dokunuşla iptal.
                </p>
              </Card>

              {/* Özet (SUNUCUDAN — Skeleton + Error) */}
              <OzetKarti ozet={ozet} onRetry={() => setOzetNonce((n) => n + 1)} />
            </div>
          ) : null}

          {/* ===================== 3D SECURE ===================== */}
          {faz === '3ds' ? (
            <Card radiusSize="lg" style={{ boxSizing: 'border-box', maxWidth: 460, margin: '0 auto', padding: '38px 34px', boxShadow: CARD_SHADOW, display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
              {!reduced ? <style>{SPIN_KEYFRAMES}</style> : null}
              <div aria-hidden style={{ position: 'relative', width: 68, height: 68, marginBottom: 18, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg width="68" height="68" viewBox="0 0 68 68" style={{ position: 'absolute', inset: 0, animation: reduced ? undefined : 'kiroSpin 550ms linear infinite' }}>
                  <circle cx="34" cy="34" r="31" fill="none" stroke={color.paper.borderFaint} strokeWidth="3.5" />
                  <circle cx="34" cy="34" r="31" fill="none" stroke={color.dawn.coral} strokeWidth="3.5" strokeLinecap="round" strokeDasharray="49 146" />
                </svg>
                <div style={{ width: 50, height: 50, borderRadius: '50%', background: '#FFF3EE', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{ShieldIcon}</div>
              </div>
              <h1 ref={baslikRef} tabIndex={-1} style={h1Serif}>Bankanız doğrulama istiyor.</h1>
              <p style={{ margin: '0 0 20px', fontSize: 13.5, color: color.ink.muted, lineHeight: 1.6, maxWidth: 330 }}>
                Kartınızı korumak için olağan bir güvenlik adımı. Banka uygulamanıza gelen bildirimi ya da SMS kodunu onaylamanız yeterli — onay gelince burası kendiliğinden ilerler.
              </p>
              <Stepper />
              <div style={{ boxSizing: 'border-box', padding: '9px 14px', background: INPUT_BG, border: `1px solid ${color.paper.borderFaint}`, borderRadius: 10, fontSize: 12, fontWeight: 600, color: color.ink.muted, lineHeight: 1.5 }}>
                Genelde bir dakikadan kısa sürer — bu sayfa açık kalsın.
              </div>
              <div style={{ marginTop: 22, display: 'flex', alignItems: 'center', gap: 7 }}>
                <span aria-hidden style={{ display: 'inline-flex' }}>{LockMini}</span>
                <span style={{ fontSize: 11.5, fontWeight: 600, color: color.ink.muted }}>Doğrulama bankanın kendi güvenli sayfasında (3-D Secure) yapılır; şifreniz bize ulaşmaz.</span>
              </div>
              <div role="status" aria-live="polite" style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0 0 0 0)', whiteSpace: 'nowrap' }}>Banka onayı bekleniyor</div>
            </Card>
          ) : null}

          {/* ===================== TAMAM ===================== */}
          {faz === 'tamam' ? (
            <Card radiusSize="lg" style={{ boxSizing: 'border-box', maxWidth: 460, margin: '0 auto', padding: '38px 34px', boxShadow: CARD_SHADOW, display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
              <div style={{ marginBottom: 18 }}>
                <IconBadge icon={BigCheck} tone="success" size={58} radiusPx={29} />
              </div>
              <h1 ref={baslikRef} tabIndex={-1} style={{ ...h1Serif, fontSize: 30 }}>Deneme başladı.</h1>
              <p style={{ margin: '0 0 24px', fontSize: 13.5, color: color.ink.muted, lineHeight: 1.6, maxWidth: 320 }}>
                7 gün boyunca her şey açık — FSRS sınırsız, AI koç sınırsız. Bitmeden hatırlatırız.
              </p>
              <a
                href="/abonelik/yonetim"
                style={{
                  boxSizing: 'border-box', display: 'inline-flex', alignItems: 'center', gap: 9, minHeight: 47, padding: '0 26px',
                  borderRadius: radius.button, background: color.dawn.coralCtaBg, color: '#fff',
                  fontFamily: font.sans, fontSize: 14.5, fontWeight: 800, textDecoration: 'none',
                  boxShadow: '0 10px 22px -10px rgba(194,69,43,0.55)',
                }}
              >
                Aboneliği yönet
                {ArrowRight}
              </a>
              <a href="/veli" style={{ marginTop: 14, minHeight: 44, display: 'inline-flex', alignItems: 'center', fontSize: 13, fontWeight: 700, color: color.ink.muted, textDecoration: 'none' }}>Veli paneline dön</a>
            </Card>
          ) : null}

          {/* Alt destek satırı — coral link (#C2452B) */}
          <p style={{ margin: '18px 0 0', textAlign: 'center', fontSize: 12, color: color.ink.muted, lineHeight: 1.6 }}>
            Takıldıysanız <a href="/sohbet" style={{ color: color.dawn.coralTextOnLight, fontWeight: 700, textDecoration: 'none' }}>destek ekibine yazın</a> — gerçek bir insan, okul saatlerinde ~10 dk içinde döner.
          </p>
            </>
          )}
        </div>
      </div>
    </KiroThemeProvider>
  );
}

export default OdemePage;
