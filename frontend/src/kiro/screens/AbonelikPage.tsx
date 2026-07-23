// ============================================================================
// KIRO2 — Abonelik (SPRINT10-B · Grup 8 billing · KIRO2 Abonelik.dc.html)
// Tema = PAPER (satın-alma yüzeyi; SideNav YOK, ortalı tek sütun max 840).
// ROL-UYARLANIR:
//   • rol='veli'  → SİZ dili; serif hero + ROI kanıt şeridi + fatura toggle
//     + 2-sütun plan ızgarası (Ücretsiz/Premium) + güven çipleri + dipnot.
//     Premium CTA → /odeme?rol=veli&fatura={donem} (zincir: Ödeme → Plan Yönetimi).
//   • rol='ogrenci' → FİYAT/PLAN GİZLİ (KVKK): paylaşılan VeliYonlendirmeKarti.
//     Başka hiçbir plan/fiyat/CTA render EDİLMEZ (childFirst=true → sunucu türetir).
//
// SUNUCU-OTORİTE: fiyat/tier/durum/fatura istemci ÜRETMEZ — getAbonelik(rol)'dan
// gelir; per-ay/per-yıl arasında istemci ARİTMETİK yapmaz (server figürü gösterir).
// KANON: paper CTA = coralCtaBg #C2452B + beyaz; açık-zeminde coral METİN #C2452B;
// indirim = yeşil success (kırmızı DEĞİL); risk-tonu amber (alarm-kırmızısı YOK);
// bespoke SVG (emoji/stok-ikon YOK); box-sizing:border-box HER container (KÖK dahil);
// hit-target ≥44px; sayı/fiyat tabular (numText). Hareket YOK → RM-guard gerekmez.
// ============================================================================
import * as React from 'react';

import { configureKiroApi, getAbonelik, getMe } from '../api/api-client';
import type { MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';
import { color, font, radius, shadow } from '../tokens';
import type { AbonelikData, AbonelikPlan, FaturaDonem, PlanTier, Persona } from '../types';
import { KiroThemeProvider, numText } from '../ui/theme';
import { SegmentedControl } from '../ui/SegmentedControl';
import { EmptyState } from '../ui/EmptyState';
import { ErrorState } from '../ui/ErrorState';
import { Skeleton } from '../ui/Skeleton';
import { VeliYonlendirmeKarti } from './billing/VeliYonlendirmeKarti';
import '../tokens/tokens.css';

configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });

// --- Bespoke ikonlar (emoji/stok-ikon YOK) ----------------------------------

function BackIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <line x1="19" y1="12" x2="5" y2="12" />
      <polyline points="12 19 5 12 12 5" />
    </svg>
  );
}
function LayersIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M12 3 3 8l9 5 9-5-9-5Z" />
      <path d="M3 16l9 5 9-5" />
      <path d="M3 12l9 5 9-5" />
    </svg>
  );
}
function CheckIcon({ stroke }: { stroke: string }) {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, marginTop: 1 }} aria-hidden>
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}
function ChevronIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="m9 6 6 6-6 6" />
    </svg>
  );
}
function BookIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color.dawn.coralTextOnLight} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z" />
    </svg>
  );
}
function EngineIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color.dawn.coralTextOnLight} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M12 3a9 9 0 1 0 9 9" />
      <path d="M12 12l5-3" />
    </svg>
  );
}
function HeartIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color.dawn.coralTextOnLight} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M12 21s-7-4.6-9.5-9C1 9 2.5 5.5 6 5.5c2 0 3.2 1.2 4 2.3.8-1.1 2-2.3 4-2.3 3.5 0 5 3.5 3.5 6.5C19 16.4 12 21 12 21Z" />
    </svg>
  );
}

// --- Yardımcılar -------------------------------------------------------------

const TIER_AD: Record<PlanTier, string> = { free: 'Ücretsiz', premium: 'Premium' };

/** Rol: prop > ?rol query > 'veli' (satın-alma varsayılanı; öğrenci fiyat görmez). */
function rolFromUrl(): 'ogrenci' | 'veli' {
  if (typeof window === 'undefined') return 'veli';
  try {
    return new URLSearchParams(window.location.search).get('rol') === 'ogrenci' ? 'ogrenci' : 'veli';
  } catch {
    return 'veli';
  }
}

/** ≤720px → plan ızgarası tek sütuna çöker (jsdom matchMedia'sız güvenli). */
function useDar(): boolean {
  const [dar, setDar] = React.useState(false);
  React.useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return;
    const mq = window.matchMedia('(max-width: 720px)');
    const on = () => setDar(mq.matches);
    on();
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, []);
  return dar;
}

const trSayi = (n: number): string => n.toLocaleString('tr-TR');

// --- ROI kanıt çipi (EKRAN-YEREL) -------------------------------------------
// kanit string'i "değer + etiket" (örn "+8,5 net"); ilk kelime vurgulu tabular.
function KanitCip({ metin, renk }: { metin: string; renk: string }) {
  const bosluk = metin.indexOf(' ');
  const deger = bosluk === -1 ? metin : metin.slice(0, bosluk);
  const etiket = bosluk === -1 ? '' : metin.slice(bosluk + 1);
  return (
    <span
      style={{
        boxSizing: 'border-box',
        display: 'inline-flex',
        alignItems: 'baseline',
        gap: 7,
        padding: '10px 15px',
        backgroundColor: color.paper.card,
        border: `1px solid ${color.paper.border}`,
        borderRadius: 12,
      }}
    >
      <span style={{ ...numText, fontSize: 17, fontWeight: 800, color: renk }}>{deger}</span>
      {etiket && <span style={{ fontSize: 12, fontWeight: 600, color: color.ink.muted }}>{etiket}</span>}
    </span>
  );
}

// --- Güven çipi (EKRAN-YEREL) -----------------------------------------------
function GuvenCip({ ikon, metin }: { ikon: React.ReactNode; metin: string }) {
  return (
    <span
      style={{
        boxSizing: 'border-box',
        display: 'inline-flex',
        alignItems: 'center',
        gap: 8,
        padding: '10px 15px',
        backgroundColor: color.paper.card,
        border: `1px solid ${color.paper.border}`,
        borderRadius: 12,
      }}
    >
      {ikon}
      <span style={{ ...numText, fontSize: 12.5, fontWeight: 700, color: color.ink.primary }}>{metin}</span>
    </span>
  );
}

// --- Plan kartı (EKRAN-YEREL, iki kez kullanılır) ---------------------------
function PlanKarti({
  plan,
  fatura,
  mevcut,
  denemeGunu,
  ctaHref,
  cocukAd,
}: {
  plan: AbonelikPlan;
  fatura: FaturaDonem;
  mevcut: boolean;
  denemeGunu: number;
  ctaHref: string;
  cocukAd: string | null;
}) {
  const one = plan.oneCikan === true;
  const fiyat = fatura === 'yillik' ? plan.fiyatYil : plan.fiyatAy;
  const birim = fatura === 'yillik' ? '/yıl' : '/ay';
  const priceFull = `₺${trSayi(fiyat)}${birim}`;
  // Veli varyantı (DC:225/227): çocuk kişiselleştirmesi + "deneme kontrolü sizde" (SİZ).
  // cocukAd yoksa nötr fallback korunur.
  const ctaLabel = cocukAd
    ? `${cocukAd} için ${denemeGunu} gün ücretsiz başlat`
    : `${denemeGunu} gün ücretsiz başla`;
  const ctaNote = cocukAd
    ? `Sonra ${priceFull} · iptal ve deneme kontrolü sizde`
    : `Sonra ${priceFull} · istediğiniz zaman iptal`;
  const note = one
    ? fatura === 'yillik'
      ? `Yıllık tek ödeme · %${trSayi(plan.indirimYuzde ?? 0)} indirim`
      : 'Aylık faturalanır · esnek'
    : 'Başlamak için — temel çalışma araçları';

  return (
    <div
      style={{
        position: 'relative',
        boxSizing: 'border-box',
        background: one ? 'linear-gradient(158deg,#FFFDFB,#FFF3EE)' : color.paper.card,
        border: one ? `2px solid ${color.dawn.coral}` : `1px solid ${color.paper.border}`,
        borderRadius: radius.cardLg,
        padding: '24px 22px',
        boxShadow: one ? shadow.cardFloat : shadow.cardSoft,
      }}
    >
      {one && (
        <div
          style={{
            position: 'absolute',
            top: -12,
            left: 22,
            boxSizing: 'border-box',
            fontFamily: font.sans,
            fontSize: 11,
            fontWeight: 800,
            letterSpacing: '0.05em',
            color: '#fff',
            backgroundColor: color.dawn.coralCtaBg,
            padding: '4px 12px',
            borderRadius: radius.pill,
            textTransform: 'uppercase',
          }}
        >
          En çok seçilen
        </div>
      )}

      <div
        style={{
          fontSize: 13,
          fontWeight: 800,
          letterSpacing: '0.04em',
          textTransform: 'uppercase',
          color: one ? color.dawn.coralTextOnLight : color.ink.muted,
        }}
      >
        {plan.ad}
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: 4, margin: '12px 0 4px' }}>
        <span style={{ ...numText, fontSize: 38, fontWeight: 800, letterSpacing: '-0.02em', color: color.ink.primary }}>
          ₺{trSayi(fiyat)}
        </span>
        <span style={{ fontSize: 13, color: color.ink.muted, fontWeight: 600 }}>{birim}</span>
      </div>
      <p style={{ margin: '0 0 18px', fontSize: 12.5, color: color.ink.muted, lineHeight: 1.5 }}>{note}</p>

      <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 10 }}>
        {plan.maddeler.map((m, i) => (
          <li
            key={i}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 9,
              fontSize: 13,
              lineHeight: 1.45,
              color: one ? color.ink.primary : color.ink.secondary,
              fontWeight: one ? 600 : 500,
            }}
          >
            <CheckIcon stroke={one ? color.dawn.coralTextOnLight : color.ink.faded3} />
            <span>{m}</span>
          </li>
        ))}
      </ul>

      {mevcut ? (
        <div
          style={{
            boxSizing: 'border-box',
            marginTop: 20,
            minHeight: 46,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: radius.button,
            border: `1px solid ${color.paper.border}`,
            fontSize: 13.5,
            fontWeight: 700,
            color: color.ink.muted,
          }}
        >
          Mevcut planın
        </div>
      ) : (
        <>
          <a
            href={ctaHref}
            style={{
              boxSizing: 'border-box',
              marginTop: 20,
              minHeight: 50,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 9,
              borderRadius: radius.button,
              backgroundColor: color.dawn.coralCtaBg,
              color: '#fff',
              fontFamily: font.sans,
              fontSize: 15,
              fontWeight: 800,
              textDecoration: 'none',
              boxShadow: shadow.coralCta,
            }}
          >
            {ctaLabel}
            <ChevronIcon />
          </a>
          <div style={{ marginTop: 10, textAlign: 'center', fontSize: 11.5, color: color.ink.muted }}>
            {ctaNote}
          </div>
        </>
      )}
    </div>
  );
}

// --- Veli plan ızgarası (fiyat GÖRÜNÜR — yalnız veli) ------------------------
function VeliAbonelik({
  data,
  persona,
  fatura,
  onFatura,
  dar,
}: {
  data: AbonelikData;
  persona: Persona | null;
  fatura: FaturaDonem;
  onFatura: (f: FaturaDonem) => void;
  dar: boolean;
}) {
  const cocukAd = persona?.ad ? persona.ad.split(' ')[0] : null;
  const denemeGunu = data.denemeGunu ?? 7;
  const premium = data.planlar.find((p) => p.oneCikan) ?? data.planlar.find((p) => p.tier === 'premium');
  const indirim = premium?.indirimYuzde ?? 0;
  const bankSize = data.bankSize ?? 0;
  const motorlar = (data.motorlar ?? []).join(' · ');
  const ctaHref = `/odeme?rol=veli&fatura=${fatura}`;

  const faturaSecenek = [
    { key: 'aylik' as FaturaDonem, label: 'Aylık' },
    {
      key: 'yillik' as FaturaDonem,
      label: 'Yıllık',
      badge: (
        <span
          style={{
            ...numText,
            marginLeft: 5,
            fontSize: 10.5,
            fontWeight: 800,
            color: color.semantic.successTextOnLight,
            backgroundColor: color.semantic.successBgSoft,
            padding: '1px 6px',
            borderRadius: radius.pill,
          }}
        >
          {`−%${trSayi(indirim)}`}
        </span>
      ),
    },
  ];

  return (
    <>
      {/* header */}
      <header style={{ display: 'flex', alignItems: 'center', gap: 13, marginBottom: 26, boxSizing: 'border-box' }}>
        <a
          href="/veli"
          aria-label="Geri"
          style={{
            boxSizing: 'border-box',
            width: 44,
            height: 44,
            flexShrink: 0,
            border: `1px solid ${color.paper.border}`,
            backgroundColor: color.paper.card,
            borderRadius: 11,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: color.ink.muted,
            textDecoration: 'none',
          }}
        >
          <BackIcon />
        </a>
        <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
          <span
            aria-hidden
            style={{
              boxSizing: 'border-box',
              width: 30,
              height: 30,
              borderRadius: 9,
              backgroundColor: color.dawn.coralCtaBg,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <LayersIcon />
          </span>
          <span style={{ fontWeight: 800, fontSize: 16, color: color.ink.primary }}>
            KIRO<span style={{ color: color.dawn.coralTextOnLight }}>2</span> Premium
          </span>
        </div>
        <div style={{ flex: 1 }} />
        <span
          style={{
            fontSize: 11.5,
            fontWeight: 700,
            color: color.ink.muted,
            backgroundColor: color.paper.borderFaint,
            padding: '5px 11px',
            borderRadius: radius.pill,
            boxSizing: 'border-box',
          }}
        >
          {`Şu an: ${TIER_AD[data.mevcutTier]}`}
        </span>
      </header>

      {/* hero */}
      <div style={{ textAlign: 'center', marginBottom: 26 }}>
        <h1 style={{ fontFamily: font.serif, margin: '0 0 10px', fontSize: 40, lineHeight: 1.06, color: color.ink.primary }}>
          {`${cocukAd ?? 'Çocuğunuz'} için tam erişim`}
        </h1>
        <p style={{ margin: '0 auto', maxWidth: 520, fontSize: 15.5, color: color.ink.muted, lineHeight: 1.6 }}>
          Kararı rakamlarla verin — aşağıdaki ilerleme {cocukAd ? `${cocukAd}'in` : 'çocuğunuzun'} gerçek verisi. Önce{' '}
          <strong style={{ color: color.ink.primary }}>{`${denemeGunu} gün ücretsiz`}</strong>; beğenmezseniz tek dokunuşla iptal.
        </p>
      </div>

      {/* ROI kanıt şeridi */}
      {data.kanit && (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10, marginBottom: 24 }}>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', justifyContent: 'center' }}>
            <KanitCip metin={data.kanit.netArtisi} renk={color.semantic.successTextOnLight} />
            <KanitCip metin={data.kanit.planUyum} renk={color.dawn.coralTextOnLight} />
            <KanitCip metin={data.kanit.seri} renk={color.dawn.coralTextOnLight} />
          </div>
          <div style={{ fontSize: 12, color: color.ink.muted, fontWeight: 500, textAlign: 'center' }}>
            Evde, kendi hızında — tipik dershane maliyetinin çok altında.
          </div>
        </div>
      )}

      {/* fatura toggle */}
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 24 }}>
        <SegmentedControl<FaturaDonem>
          options={faturaSecenek}
          value={fatura}
          onChange={onFatura}
          variant="pill"
          ariaContext="Fatura dönemi"
        />
      </div>

      {/* plan ızgarası */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: dar ? '1fr' : '1fr 1.15fr',
          gap: 16,
          marginBottom: 30,
          alignItems: 'start',
          boxSizing: 'border-box',
        }}
      >
        {data.planlar.map((p) => (
          <PlanKarti
            key={p.tier}
            plan={p}
            fatura={fatura}
            mevcut={p.tier === data.mevcutTier}
            denemeGunu={denemeGunu}
            ctaHref={ctaHref}
            cocukAd={cocukAd}
          />
        ))}
      </div>

      {/* güven çipleri */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', justifyContent: 'center' }}>
        <GuvenCip ikon={<BookIcon />} metin={`${trSayi(bankSize)}+ soru`} />
        {motorlar && <GuvenCip ikon={<EngineIcon />} metin={motorlar} />}
        <GuvenCip ikon={<HeartIcon />} metin="Kaygı-duyarlı tasarım" />
      </div>

      {/* dipnot */}
      <p style={{ margin: '24px auto 0', textAlign: 'center', fontSize: 12, color: color.ink.muted, maxWidth: 460, lineHeight: 1.5 }}>
        Fiyat ve satın alma yalnız veli hesabında — {cocukAd ?? 'çocuğunuz'} fiyat baskısı görmez. Deneme bitmeden hatırlatırız; sessizce ücret alınmaz.
      </p>
    </>
  );
}

// --- Yükleme iskeleti --------------------------------------------------------
function AbonelikSkeleton({ dar }: { dar: boolean }) {
  return (
    <div
      aria-busy="true"
      aria-label="Abonelik seçenekleri yükleniyor"
      style={{ display: 'flex', flexDirection: 'column', gap: 24, boxSizing: 'border-box' }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
        <Skeleton width={240} height={30} />
        <Skeleton width={320} height={12} />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: dar ? '1fr' : '1fr 1.15fr', gap: 16, boxSizing: 'border-box' }}>
        {[0, 1].map((i) => (
          <div
            key={i}
            style={{
              boxSizing: 'border-box',
              background: color.paper.card,
              border: `1px solid ${color.paper.border}`,
              borderRadius: radius.cardLg,
              padding: '24px 22px',
            }}
          >
            <Skeleton shape="card" delayMs={0} slowAfterMs={null} />
          </div>
        ))}
      </div>
    </div>
  );
}

// --- Ekran -------------------------------------------------------------------

export interface AbonelikPageProps {
  /** Rol: satın-alma veli varsayılan; 'ogrenci' → fiyat GİZLİ (VeliYonlendirmeKarti). URL'den de türer. */
  rol?: 'ogrenci' | 'veli';
  /** Varsayılan fatura dönemi (DC varsayılanı yıllık = indirimli). */
  varsayilanFatura?: FaturaDonem;
}

export function AbonelikPage({ rol: rolProp, varsayilanFatura }: AbonelikPageProps = {}): React.ReactElement {
  const rol = rolProp ?? rolFromUrl();
  const dar = useDar();
  const [data, setData] = React.useState<AbonelikData | null>(null);
  const [persona, setPersona] = React.useState<Persona | null>(null);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);
  const [fatura, setFatura] = React.useState<FaturaDonem>(varsayilanFatura ?? 'yillik');

  React.useEffect(() => {
    let alive = true;
    setData(null);
    setHata(false);
    // getAbonelik birincil (reddi → ErrorState). getMe ikincil (isim; reddi ekranı düşürmez).
    Promise.all([getMe().catch(() => null), getAbonelik(rol)])
      .then(([p, d]) => {
        if (!alive) return;
        setPersona(p);
        setData(d);
      })
      .catch(() => {
        if (alive) setHata(true);
      });
    return () => {
      alive = false;
    };
  }, [rol, yeniden]);

  let icerik: React.ReactNode;
  if (hata) {
    icerik = (
      <ErrorState
        serifTitle="Abonelik seçenekleri şu an gelmedi."
        body="Sorun sizde değil — bağlantı bir soluklandı, hiçbir ücret alınmadı. Birazdan yeniden deneyebilirsiniz."
        onRetry={() => setYeniden((n) => n + 1)}
      />
    );
  } else if (data === null) {
    icerik = <AbonelikSkeleton dar={dar} />;
  } else if (data.childFirst) {
    // ÖĞRENCİ: fiyat/plan/ödeme GİZLİ (KVKK) → paylaşılan yönlendirme kartı.
    icerik = (
      <div style={{ paddingTop: 32, boxSizing: 'border-box' }}>
        <VeliYonlendirmeKarti baglam="abonelik" />
      </div>
    );
  } else if (data.planlar.length === 0) {
    icerik = (
      <EmptyState
        serifTitle="Planlar birazdan burada."
        body="Abonelik seçenekleri şu an hazırlanıyor. Çalışman kesintisiz sürüyor — birazdan tekrar bakabilirsiniz."
      />
    );
  } else {
    icerik = <VeliAbonelik data={data} persona={persona} fatura={fatura} onFatura={setFatura} dar={dar} />;
  }

  return (
    <KiroThemeProvider theme="paper">
      <div
        className="k-paper"
        style={{
          boxSizing: 'border-box',
          minHeight: '100vh',
          background: color.paper.bg,
          fontFamily: font.sans,
          color: color.ink.primary,
          fontSize: 14,
          lineHeight: 1.55,
        }}
      >
        <div style={{ boxSizing: 'border-box', maxWidth: 840, margin: '0 auto', padding: '24px 30px 80px' }}>
          {icerik}
        </div>
      </div>
    </KiroThemeProvider>
  );
}

export default AbonelikPage;
