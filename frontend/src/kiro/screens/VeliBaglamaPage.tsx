// ============================================================================
// KIRO2 — Veli Bağlama / KVKK iki-taraf onam (SPRINT9-B · KIRO2 Veli Baglama.dc.html)
// Tema = PAPER. Merkezi kart-akışı (SideNav YOK; GirisPage/OnboardingPage kabuğu emsal).
// İKİ MUHATAP, İKİ DİL: VELİ tarafı resmi SİZ; ÖĞRENCİ tarafı akran SEN. Rota
// /veli-baglama (+ ?rol=ogrenci öğrenci tarafı). SR'da da doğru muhatap.
//
// SUNUCU-OTORİTE: 6-hane kodun üretimi/doğrulaması + 10dk TTL, KVKK rıza kaydı,
// bağlantı durumu SUNUCUDA. İstemci kod ÜRETMEZ/DOĞRULAMAZ — yalnız verifyLinkCode/
// giveConsent/pollLinkStatus/approveRelation yanıtını render eder. Öğrenci metriği
// (θ/net/hâkimiyet) BU ekranda YOK.
//
// KANON: CTA = coralCtaBg #C2452B + beyaz (DC ham #FF6F5C AA-değil → çekildi); coral
// link/KVKK #C2452B; ScopePanel yeşil = success (olumlu ifşa OK); indigo/mor YOK;
// bespoke SVG (emoji YOK); serif italik H1 + tabular kod. Konfeti/spring YOK (onam).
// KOPYA: DC birebir (veli SİZ / öğrenci SEN). Empty/Error/kod-dogrulanamadi → ONAY BEKLER.
// ============================================================================
import * as React from 'react';

import {
  configureKiroApi,
  verifyLinkCode,
  getKvkkNotice,
  giveConsent,
  pollLinkStatus,
  getPendingParentRequest,
  approveRelation,
} from '../api/api-client';
import type { MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';
import type { KvkkNotice, LinkCodeSonuc, PendingVeliIstek } from '../types';
import { color, font, radius } from '../tokens';
import { KiroThemeProvider, numText } from '../ui/theme';
import { useReducedMotion } from '../ui/ConfettiDawn';
import '../tokens/tokens.css';

configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });

type Taraf = 'veli' | 'ogrenci';
type VeliAdim = 'kod' | 'riza' | 'bekle' | 'tamam';

// DC-özgü sıcak tint'ler — token karşılığı yok (dekoratif; ham hex istisnası).
const HERO_BG = `radial-gradient(1100px 460px at 50% -8%, #FFF3EE 0%, ${color.paper.bg} 62%)`;
const KOD_BG = color.paper.subtle;
// DC-özgü yeşil ifşa tinti (olumlu; success ailesi — kanon: yeşil=success, kırmızı DEĞİL).
const SCOPE_GREEN = { bg: '#F0FDF4', border: '#BBF7D0', head: '#166534', text: '#1E5631', check: '#17936B' };
// Öğrenci veli-avatarı — DC coral gradyanı (coralCtaBg → coral).
const VELI_AVATAR = `linear-gradient(135deg, ${color.dawn.coralCtaBg}, ${color.dawn.coral})`;

// KVKK aydınlatma kapsam listeleri — VELİ tarafı statik ifşa kopyası (DC birebir).
// Sözleşmede veli-scope getter YOK; kiro-data.veliBaglama.scope açık edilmiyor → bu
// KVKK metni OgrenciOzeti'nin gizlilik-bülteni gibi statik kopyadır (per-user değil).
const VELI_GORUR = [
  'Haftalık çalışma süresi ve plan uyumu',
  'Deneme sonuçları ve net gelişimi',
  'Ders bazında hâkimiyet özeti',
  'Günlük seri (istikrar göstergesi)',
];
const VELI_GORMEZ = [
  'AI sohbet içerikleri',
  'Ruh hâli kayıtları',
  'Soru bazlı cevap detayları',
  'Arkadaş etkileşimleri',
];

const HINT = {
  // DC birebir — client-side uzunluk ön-kontrolü (sunucu çağrısından önce).
  uzunluk: 'Kod 6 haneli olmalı — çocuğunuzun ekranındaki kodu birlikte kontrol edin.',
  // ONAY BEKLER (inferred) — sunucu gecerli:false döndürdüğünde.
  dogrulanamadi: 'Kod doğrulanamadı — çocuğunuzun ekranındaki güncel kodu birlikte kontrol edin (10 dakikada bir yenilenir).',
  // ONAY BEKLER (inferred) — ağ/sunucu hatası (alarm dili YOK).
  genel: 'Bağlantı bir soluklandı — çalışman güvende, birazdan tekrar dene.',
} as const;

const ADIM_ETIKET: Record<VeliAdim, string> = {
  kod: 'Adım 1 / 3',
  riza: 'Adım 2 / 3',
  bekle: 'Adım 3 / 3',
  tamam: 'Tamamlandı',
};

const STEP_ANIM =
  '@keyframes vbStepIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }';

const SR_ONLY: React.CSSProperties = {
  position: 'absolute', width: 1, height: 1, padding: 0, margin: -1,
  overflow: 'hidden', clip: 'rect(0 0 0 0)', whiteSpace: 'nowrap', border: 0,
};

// jsdom matchMedia'sız SSR-guard'lı (BREAKPOINT_SPEC §3).
function useMedia(query: string): boolean {
  const [esles, setEsles] = React.useState(false);
  React.useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {return;}
    const mq = window.matchMedia(query);
    const on = () => setEsles(mq.matches);
    on();
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, [query]);
  return esles;
}

function tarafFromUrl(): Taraf {
  if (typeof window === 'undefined') {return 'veli';}
  try {
    return new URLSearchParams(window.location.search).get('rol') === 'ogrenci' ? 'ogrenci' : 'veli';
  } catch {
    return 'veli';
  }
}

const ilkAd = (tam: string | undefined, fallback: string): string => (tam ? tam.split(' ')[0] : fallback);

// --- Bespoke ikonlar (emoji YOK) --------------------------------------------

const DiamondIcon = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M12 3 3 8l9 5 9-5-9-5Z" /><path d="M3 16l9 5 9-5M3 12l9 5 9-5" />
  </svg>
);
const PhoneIcon = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color.ink.muted} strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, marginTop: 1 }} aria-hidden>
    <rect x="7" y="2" width="10" height="20" rx="2.5" /><path d="M11 18h2" />
  </svg>
);
const InfoIcon = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color.semantic.riskTextOnLight} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }} aria-hidden>
    <circle cx="12" cy="12" r="9" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
  </svg>
);
const CheckMini = (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <polyline points="20 6 9 17 4 12" />
  </svg>
);
const LockMini = (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <rect x="5" y="11" width="14" height="10" rx="2" /><path d="M8 11V7a4 4 0 0 1 8 0v4" />
  </svg>
);
const CheckBox = (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <polyline points="20 6 9 17 4 12" />
  </svg>
);
const ClockIcon = (
  <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke={color.semantic.riskTextOnLight} strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <circle cx="12" cy="12" r="9" /><polyline points="12 7 12 12 15 14" />
  </svg>
);
const BigCheck = (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke={color.semantic.success} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <polyline points="20 6 9 17 4 12" />
  </svg>
);
const Chevron = (
  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="m9 6 6 6-6 6" />
  </svg>
);

// --- Alt bileşenler ----------------------------------------------------------

/** Paper beyaz-metin coral CTA (coralCtaBg #C2452B, AA). Tam genişlik, hit≥44.
 *  Gerçek disabled (klavye tetiklemez). */
function CtaButton({
  children, onClick, disabled,
}: { children: React.ReactNode; onClick: () => void; disabled?: boolean }) {
  return (
    <button
      type="button" onClick={onClick} disabled={disabled}
      style={{
        boxSizing: 'border-box', width: '100%', minHeight: 50, height: 50, border: 'none',
        borderRadius: radius.button,
        background: disabled ? color.paper.borderFaint : color.dawn.coralCtaBg,
        color: disabled ? color.ink.faded3 : '#fff',
        fontFamily: font.sans, fontSize: 15, fontWeight: 800,
        cursor: disabled ? 'default' : 'pointer',
        boxShadow: disabled ? 'none' : '0 10px 22px -10px rgba(194,69,43,0.55)',
      }}
    >
      {children}
    </button>
  );
}

/** İki yönlü şeffaflık kapsamı — yeşil (görür) success, nötr (görmez). Uzun-içerik minmax(0). */
function ScopePanel({ baslik, items, tone }: { baslik: string; items: string[]; tone: 'gorur' | 'gormez' }) {
  const yesil = tone === 'gorur';
  return (
    <div
      style={{
        boxSizing: 'border-box', minWidth: 0,
        background: yesil ? SCOPE_GREEN.bg : color.paper.subtle,
        border: `1px solid ${yesil ? SCOPE_GREEN.border : color.paper.border}`,
        borderRadius: 14, padding: '15px 16px',
      }}
    >
      <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 10, color: yesil ? SCOPE_GREEN.head : color.ink.muted }}>
        {baslik}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {items.map((g) => (
          <div key={g} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', fontSize: 12.5, fontWeight: 600, lineHeight: 1.4, color: yesil ? SCOPE_GREEN.text : color.ink.muted }}>
            <span aria-hidden style={{ flexShrink: 0, marginTop: 2, display: 'inline-flex', color: yesil ? SCOPE_GREEN.check : color.ink.muted }}>
              {yesil ? CheckMini : LockMini}
            </span>
            <span>{g}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

const h1Serif: React.CSSProperties = {
  margin: '0 0 8px', fontFamily: font.serif, fontStyle: 'italic', fontWeight: 400,
  fontSize: 30, lineHeight: 1.12, color: color.ink.primary, outline: 'none',
};
const h1SerifKucuk: React.CSSProperties = { ...h1Serif, fontSize: 28, lineHeight: 1.15 };
const pAlt: React.CSSProperties = { margin: '0 0 20px', fontSize: 13.5, color: color.ink.muted, lineHeight: 1.6 };

// --- Ekran -------------------------------------------------------------------

export interface VeliBaglamaPageProps {
  /** Rota: veli tarafı (varsayılan) vs ?rol=ogrenci öğrenci tarafı. URL'den türer. */
  taraf?: Taraf;
  /** Storybook önizleme: veli akışı hangi adımda başlasın (üretimde geçilmez → 'kod'). */
  baslangicAdim?: VeliAdim;
}

export function VeliBaglamaPage({ taraf: tarafProp, baslangicAdim }: VeliBaglamaPageProps = {}): React.ReactElement {
  const taraf = tarafProp ?? tarafFromUrl();
  const isVeli = taraf === 'veli';
  const reduced = useReducedMotion();
  const dar = useMedia('(max-width: 430px)');
  const scopeCols = dar ? '1fr' : 'repeat(2, minmax(0, 1fr))';

  // --- Veli tarafı durumu ---
  const [adim, setAdim] = React.useState<VeliAdim>(baslangicAdim ?? 'kod');
  const [kod, setKod] = React.useState('');
  const [hint, setHint] = React.useState('');
  const [dogrulaniyor, setDogrulaniyor] = React.useState(false);
  const [sonuc, setSonuc] = React.useState<LinkCodeSonuc | null>(null);
  const [riza, setRiza] = React.useState(false);
  const [eposta, setEposta] = React.useState(false);
  const [basliyor, setBasliyor] = React.useState(false);
  const [notice, setNotice] = React.useState<KvkkNotice | null>(null);

  // --- Öğrenci tarafı durumu ---
  const [pending, setPending] = React.useState<PendingVeliIstek | null | undefined>(undefined);
  const [oDurum, setODurum] = React.useState<'bekliyor' | 'tamam'>('bekliyor');
  const [onaylaniyor, setOnaylaniyor] = React.useState(false);

  const baslikRef = React.useRef<HTMLHeadingElement>(null);
  const ilk = React.useRef(true);

  // KVKK aydınlatma sürümü SUNUCUDAN — rıza kaydında mühürlenir (veli tarafı).
  React.useEffect(() => {
    if (!isVeli) {return;}
    let alive = true;
    getKvkkNotice().then((n) => { if (alive) {setNotice(n);} }).catch(() => undefined);
    return () => { alive = false; };
  }, [isVeli]);

  // Öğrenci tarafı: bekleyen veli isteği (null → boş durum).
  React.useEffect(() => {
    if (isVeli) {return;}
    let alive = true;
    setPending(undefined);
    getPendingParentRequest()
      .then((p) => { if (alive) {setPending(p);} })
      .catch(() => { if (alive) {setPending(null);} });
    return () => { alive = false; };
  }, [isVeli]);

  // Storybook önizleme: veli akışı kod-sonrası adımda başlarsa çocuk kimliğini
  // SUNUCUDAN (verifyLinkCode) yükle — üretimde baslangicAdim geçilmez.
  React.useEffect(() => {
    if (isVeli && baslangicAdim && baslangicAdim !== 'kod') {
      verifyLinkCode('482913').then((r) => { if (r.gecerli) {setSonuc(r);} }).catch(() => undefined);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Adım/durum geçişinde odağı yeni başlığa taşı (odak-sırası korunur).
  React.useEffect(() => {
    if (ilk.current) { ilk.current = false; return; }
    baslikRef.current?.focus();
  }, [adim, oDurum, pending]);

  const cocukAd = ilkAd(sonuc?.cocukAd, 'çocuğunuz');

  const kodDevam = (): void => {
    if (dogrulaniyor) {return;}
    const temiz = kod.replace(/\D/g, '').slice(0, 6);
    if (temiz.length !== 6) { setHint(HINT.uzunluk); return; }
    setDogrulaniyor(true);
    setHint('');
    // SUNUCU-OTORİTE: kod doğrulama + relationId sunucuda; istemci eşitlik hesaplamaz.
    verifyLinkCode(temiz)
      .then((r) => {
        if (r.gecerli) { setSonuc(r); setAdim('riza'); }
        else {setHint(HINT.dogrulanamadi);}
      })
      .catch(() => setHint(HINT.genel))
      .finally(() => setDogrulaniyor(false));
  };

  const rizaDevam = (): void => {
    if (!riza || basliyor) {return;}
    setBasliyor(true);
    // Rıza kaydı SUNUCUDA — görülen KVKK sürümü mühürlenir (istemci rızayı hesaplamaz).
    giveConsent('veli-baglama · KVKK ' + (notice?.version ?? 'v3'))
      .then(() => setAdim('bekle'))
      .catch(() => setHint(HINT.genel))
      .finally(() => setBasliyor(false));
  };

  const simuleOnay = async (): Promise<void> => {
    if (!sonuc?.relationId) {return;}
    // Prototip: çocuğun cihazındaki onayı simüle eder — ÜRETİMDE sunucu-güdümlü
    // arka-plan yoklaması yapar. SUNUCU-OTORİTE: yalnız 'onaylandi' yanıtında ilerler;
    // mock pollLinkStatus 1. yoklamada 'bekliyor', 2.+'de 'onaylandi' döner (bounded).
    for (let i = 0; i < 3; i++) {
      const { durum } = await pollLinkStatus(sonuc.relationId);
      if (durum === 'onaylandi') { setAdim('tamam'); return; }
    }
  };

  const onayla = (): void => {
    if (!pending || onaylaniyor) {return;}
    setOnaylaniyor(true);
    // Onay/ret SUNUCUDA işlenir (approveRelation); istemci ilişki durumu hesaplamaz.
    approveRelation(pending.relationId, true)
      .then(() => setODurum('tamam'))
      .catch(() => undefined)
      .finally(() => setOnaylaniyor(false));
  };

  const cardStyle: React.CSSProperties = {
    boxSizing: 'border-box', width: '100%', maxWidth: 560, marginTop: '5vh',
    background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: radius.cardLg,
    padding: dar ? '28px 20px 26px' : '34px 34px 30px',
    boxShadow: '0 1px 2px rgba(16,24,40,.04), 0 12px 34px -20px rgba(16,24,40,.16)',
  };

  return (
    <KiroThemeProvider theme="paper">
      <div
        className="k-paper"
        style={{
          boxSizing: 'border-box', minHeight: '100vh', width: '100%', background: HERO_BG,
          fontFamily: font.sans, color: color.ink.primary, overflowX: 'hidden',
          display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '0 20px 60px',
        }}
      >
        {/* Üst bar */}
        <div style={{ boxSizing: 'border-box', width: '100%', maxWidth: 640, display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 10, rowGap: 8, padding: '22px 0 0' }}>
          <span aria-hidden style={{ width: 30, height: 30, borderRadius: 9, background: color.dawn.coralCtaBg, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{DiamondIcon}</span>
          <span style={{ fontWeight: 800, fontSize: 16 }}>KIRO<span style={{ color: color.dawn.coralTextOnLight }}>2</span></span>
          <span style={{ fontSize: 11, fontWeight: 800, letterSpacing: '0.06em', textTransform: 'uppercase', color: color.semantic.riskTextOnLight, background: color.semantic.riskBgSoft, border: `1px solid ${color.semantic.riskBorderSoft}`, borderRadius: 999, padding: '3px 10px', marginLeft: 4 }}>Veli bağlantısı</span>
          <div style={{ flex: 1, minWidth: 0 }} />
          {isVeli ? (
            <span aria-live="polite" style={{ ...numText, fontSize: 11.5, fontWeight: 800, letterSpacing: '0.08em', color: color.ink.muted, textTransform: 'uppercase' }}>
              {ADIM_ETIKET[adim]}
            </span>
          ) : null}
        </div>

        {/* Kart */}
        <div style={cardStyle}>
          {!reduced ? <style>{STEP_ANIM}</style> : null}
          <div key={isVeli ? adim : oDurum} style={{ animation: reduced ? undefined : 'vbStepIn 0.24s cubic-bezier(0.33,0,0.2,1) both' }}>

            {/* ===================== VELİ TARAFI (resmi SİZ) ===================== */}
            {isVeli && adim === 'kod' ? (
              <>
                <h1 ref={baslikRef} tabIndex={-1} style={h1Serif}>Çocuğunuzu güvenle bağlayın.</h1>
                <p style={{ ...pAlt, marginBottom: 22 }}>
                  Bağlantı çift taraflı kurulur: siz açık rıza verirsiniz, çocuğunuz bağlantıyı <strong style={{ color: color.ink.primary }}>kendi cihazında onaylar</strong>. Kimse habersiz izlenmez.
                </p>

                {/* Görsel başlık; erişilebilir ad input'un aria-label'ından (çift-etiket YOK). */}
                <div style={{ fontSize: 12.5, fontWeight: 700, color: color.ink.secondary, marginBottom: 7 }}>Bağlantı kodu</div>
                <input
                  id="vb-kod"
                  inputMode="numeric"
                  value={kod}
                  onChange={(e) => { setKod(e.target.value.replace(/\D/g, '').slice(0, 6)); setHint(''); }}
                  onKeyDown={(e) => { if (e.key === 'Enter') {kodDevam();} }}
                  placeholder="······"
                  aria-label="6 haneli bağlantı kodu"
                  aria-describedby={hint ? 'vb-hint' : undefined}
                  style={{
                    boxSizing: 'border-box', width: '100%', height: 56, padding: '0 15px',
                    border: `1px solid ${color.paper.borderStrong}`, borderRadius: 13, background: KOD_BG,
                    fontFamily: font.sans, fontSize: 24, fontWeight: 800, letterSpacing: '0.42em',
                    textAlign: 'center', color: color.ink.primary, fontVariantNumeric: 'tabular-nums', outline: 'none',
                  }}
                />

                <div style={{ boxSizing: 'border-box', marginTop: 12, display: 'flex', gap: 10, alignItems: 'flex-start', padding: '12px 14px', background: KOD_BG, border: `1px solid ${color.paper.borderFaint}`, borderRadius: 12 }}>
                  {PhoneIcon}
                  <span style={{ ...numText, fontSize: 12.5, color: color.ink.muted, lineHeight: 1.55 }}>
                    Kod, çocuğunuzun uygulamasında: <strong style={{ color: color.ink.primary }}>Ayarlar → Veli bağlantısı → Kod göster</strong>. 10 dakika geçerlidir.
                  </span>
                </div>

                {hint ? (
                  <div id="vb-hint" role="status" aria-live="polite" style={{ boxSizing: 'border-box', marginTop: 12, display: 'flex', alignItems: 'center', gap: 8, padding: '10px 13px', background: color.semantic.riskBgSoft, border: `1px solid ${color.semantic.riskBorderSoft}`, borderRadius: 11 }}>
                    {InfoIcon}
                    <span style={{ fontSize: 12.5, fontWeight: 600, color: color.semantic.riskTextOnLight }}>{hint}</span>
                  </div>
                ) : null}

                <div style={{ marginTop: 20 }}>
                  <CtaButton onClick={kodDevam} disabled={dogrulaniyor}>{dogrulaniyor ? 'Doğrulanıyor…' : 'Devam et'}</CtaButton>
                </div>
              </>
            ) : null}

            {isVeli && adim === 'riza' ? (
              <>
                <h1 ref={baslikRef} tabIndex={-1} style={h1Serif}>Neyi görürsünüz, neyi görmezsiniz?</h1>
                <p style={pAlt}>Şeffaflık iki yönlü: aynı liste {cocukAd}&apos;e de gösterilir.</p>

                <div style={{ display: 'grid', gridTemplateColumns: scopeCols, gap: 12, marginBottom: 18 }}>
                  <ScopePanel baslik="Görürsünüz" items={VELI_GORUR} tone="gorur" />
                  <ScopePanel baslik="Asla görmezsiniz" items={VELI_GORMEZ} tone="gormez" />
                </div>

                {/* KVKK açık rıza — çekbox tıklama-bölgesi AYRI, KVKK linki AYRI (iç-içe interaktif YASAK). */}
                <div style={{ boxSizing: 'border-box', display: 'flex', gap: 10, alignItems: 'flex-start', padding: '9px 12px 9px 4px', border: `1.5px solid ${riza ? color.dawn.coralCtaBg : color.paper.border}`, borderRadius: 13, background: riza ? '#FFF9F6' : color.paper.card }}>
                  <button
                    type="button" role="checkbox" aria-checked={riza} aria-labelledby="vb-riza-metin"
                    onClick={() => setRiza((v) => !v)}
                    style={{ boxSizing: 'border-box', flexShrink: 0, width: 44, height: 44, minHeight: 44, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', border: 'none', background: 'transparent', cursor: 'pointer', padding: 0 }}
                  >
                    <span aria-hidden style={{ width: 22, height: 22, borderRadius: 7, border: `2px solid ${riza ? color.dawn.coralCtaBg : '#D9D2C7'}`, background: riza ? color.dawn.coralCtaBg : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
                      {riza ? CheckBox : null}
                    </span>
                  </button>
                  <span id="vb-riza-metin" style={{ alignSelf: 'center', fontSize: 12.5, color: color.ink.primary, lineHeight: 1.55 }}>
                    <a href="/kvkk" style={{ color: color.dawn.coralTextOnLight, fontWeight: 700, textDecoration: 'none' }}>KVKK Aydınlatma Metni</a>&apos;ni okudum; {cocukAd}&apos;in yukarıda listelenen çalışma verilerinin veli hesabımda işlenmesine <strong>açık rıza</strong> veriyorum.
                  </span>
                </div>

                {/* İsteğe bağlı e-posta özeti (iç-içe link YOK → tek buton). */}
                <button
                  type="button" role="checkbox" aria-checked={eposta}
                  onClick={() => setEposta((v) => !v)}
                  style={{ boxSizing: 'border-box', display: 'flex', alignItems: 'center', gap: 10, width: '100%', minHeight: 44, marginTop: 9, padding: '9px 12px 9px 4px', border: `1px solid ${color.paper.border}`, borderRadius: 13, background: color.paper.card, fontFamily: font.sans, cursor: 'pointer', textAlign: 'left' }}
                >
                  <span aria-hidden style={{ flexShrink: 0, width: 22, height: 22, marginLeft: 8, borderRadius: 7, border: `2px solid ${eposta ? color.dawn.coralCtaBg : '#D9D2C7'}`, background: eposta ? color.dawn.coralCtaBg : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
                    {eposta ? CheckBox : null}
                  </span>
                  <span style={{ fontSize: 12.5, color: color.ink.secondary, lineHeight: 1.55 }}>
                    Pazar akşamları sakin bir haftalık özet e-postası almak istiyorum. <span style={{ color: color.ink.muted }}>(isteğe bağlı)</span>
                  </span>
                </button>

                <div style={{ marginTop: 18 }}>
                  <CtaButton onClick={rizaDevam} disabled={!riza || basliyor}>{basliyor ? 'Bağlanıyor…' : 'Rıza ver ve bağlantıyı başlat'}</CtaButton>
                </div>
                <p style={{ margin: '12px 0 0', textAlign: 'center', fontSize: 11.5, color: color.ink.muted, lineHeight: 1.5 }}>
                  Rızanızı istediğiniz an Ayarlar&apos;dan geri çekebilirsiniz — tek dokunuş, soru sorulmaz.
                </p>
              </>
            ) : null}

            {isVeli && adim === 'bekle' ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
                <div aria-hidden style={{ width: 58, height: 58, borderRadius: 18, background: color.semantic.riskBgSoft, border: `1px solid ${color.semantic.riskBorderSoft}`, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>{ClockIcon}</div>
                <h1 ref={baslikRef} tabIndex={-1} style={h1SerifKucuk}>Şimdi söz {cocukAd}&apos;te.</h1>
                <p style={{ margin: '0 0 20px', fontSize: 13.5, color: color.ink.muted, lineHeight: 1.65, maxWidth: 380 }}>
                  Bağlantı isteğiniz {cocukAd}&apos;in cihazına gitti. Kendi ekranında neyi görebileceğinizi görüp onaylayınca burası kendiliğinden güncellenir. <strong style={{ color: color.ink.primary }}>Bu bir saygı adımı — hesap onun.</strong>
                </p>
                <button
                  type="button" onClick={() => void simuleOnay()}
                  style={{ boxSizing: 'border-box', display: 'inline-flex', alignItems: 'center', gap: 7, minHeight: 44, padding: '0 20px', border: `1px solid ${color.paper.border}`, borderRadius: 12, background: color.paper.card, color: color.ink.secondary, fontFamily: font.sans, fontSize: 13, fontWeight: 700, cursor: 'pointer' }}
                >
                  Prototip: çocuk onayını simüle et
                  <span style={{ display: 'inline-flex', color: color.ink.muted }}>{Chevron}</span>
                </button>
              </div>
            ) : null}

            {isVeli && adim === 'tamam' ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
                <div aria-hidden style={{ width: 58, height: 58, borderRadius: '50%', background: color.semantic.successBgSoft, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>{BigCheck}</div>
                <h1 ref={baslikRef} tabIndex={-1} style={h1SerifKucuk}>Bağlantı kuruldu.</h1>
                <p style={{ margin: '0 0 22px', fontSize: 13.5, color: color.ink.muted, lineHeight: 1.65, maxWidth: 380 }}>
                  {cocukAd} onayladı. Panelinizde çalışma özeti görünür — sohbetleri ve ruh hâli kayıtları ise her zaman ona ait kalır.
                </p>
                <a href="/veli" style={{ boxSizing: 'border-box', display: 'inline-flex', alignItems: 'center', gap: 9, minHeight: 48, padding: '0 24px', borderRadius: radius.button, background: color.dawn.coralCtaBg, color: '#fff', fontFamily: font.sans, fontSize: 14.5, fontWeight: 800, textDecoration: 'none', boxShadow: '0 10px 22px -10px rgba(194,69,43,0.55)' }}>
                  Veli paneline git
                  {Chevron}
                </a>
              </div>
            ) : null}

            {/* ===================== ÖĞRENCİ TARAFI (akran SEN) ===================== */}
            {!isVeli && pending === undefined ? (
              <div aria-busy="true" aria-live="polite" style={{ minHeight: 120, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 600, color: color.ink.muted }}>
                Bağlantı isteği yükleniyor…
              </div>
            ) : null}

            {!isVeli && pending === null ? (
              // ONAY BEKLER (inferred) — sözleşmede öğrenci-tarafı boş durum yok.
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
                <div aria-hidden style={{ width: 58, height: 58, borderRadius: 18, background: color.paper.subtle, border: `1px solid ${color.paper.border}`, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16, color: color.ink.muted }}>{ClockIcon}</div>
                <h1 ref={baslikRef} tabIndex={-1} style={h1SerifKucuk}>Bekleyen bir bağlantı isteği yok.</h1>
                <p style={{ margin: '0 0 22px', fontSize: 13.5, color: color.ink.muted, lineHeight: 1.65, maxWidth: 380 }}>
                  Bir veli hesabını bağlamak istediğinde burası kendiliğinden dolar — acelesi yok, kontrol sende.
                </p>
                <a href="/bugun" style={{ boxSizing: 'border-box', display: 'inline-flex', alignItems: 'center', gap: 9, minHeight: 48, padding: '0 24px', borderRadius: radius.button, background: color.dawn.coralCtaBg, color: '#fff', fontFamily: font.sans, fontSize: 14.5, fontWeight: 800, textDecoration: 'none' }}>Çalışmaya dön</a>
              </div>
            ) : null}

            {!isVeli && pending && oDurum === 'bekliyor' ? (
              <>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                  <div aria-hidden style={{ width: 44, height: 44, flexShrink: 0, borderRadius: 13, background: VELI_AVATAR, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 16 }}>{pending.veliBas}</div>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 14.5, fontWeight: 800 }}>{pending.veliAd}</div>
                    <div style={{ fontSize: 12, color: color.ink.muted, fontWeight: 600 }}>hesabını bağlamak istiyor</div>
                  </div>
                </div>
                <h1 ref={baslikRef} tabIndex={-1} style={h1SerifKucuk}>Desteklemek istiyor — şartları sen de gör.</h1>
                <p style={{ margin: '0 0 18px', fontSize: 13.5, color: color.ink.muted, lineHeight: 1.6 }}>
                  Onaylarsan görebilecekleri yalnız şunlar. <strong style={{ color: color.ink.primary }}>Sohbetlerin, ruh hâlin ve cevap detayların her zaman sana ait.</strong>
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: scopeCols, gap: 12, marginBottom: 20 }}>
                  <ScopePanel baslik="Görebilir" items={pending.scope.gorur} tone="gorur" />
                  <ScopePanel baslik="Asla göremez" items={pending.scope.gormez} tone="gormez" />
                </div>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 11 }}>
                  <button
                    type="button" onClick={onayla} disabled={onaylaniyor}
                    style={{ boxSizing: 'border-box', flex: '1.4 1 180px', minHeight: 50, height: 50, border: 'none', borderRadius: 13, background: onaylaniyor ? color.paper.borderFaint : color.dawn.coralCtaBg, color: onaylaniyor ? color.ink.faded3 : '#fff', fontFamily: font.sans, fontSize: 14.5, fontWeight: 800, cursor: onaylaniyor ? 'default' : 'pointer', boxShadow: onaylaniyor ? 'none' : '0 10px 22px -10px rgba(194,69,43,0.55)' }}
                  >
                    {onaylaniyor ? 'Bağlanıyor…' : 'Bağlantıyı onayla'}
                  </button>
                  <a
                    href="/bugun"
                    style={{ boxSizing: 'border-box', flex: '1 1 130px', minHeight: 50, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', border: `1px solid ${color.paper.border}`, borderRadius: 13, background: color.paper.card, color: color.ink.secondary, fontFamily: font.sans, fontSize: 14, fontWeight: 700, textDecoration: 'none' }}
                  >
                    Şimdi değil
                  </a>
                </div>
                <p style={{ margin: '12px 0 0', textAlign: 'center', fontSize: 11.5, color: color.ink.muted, lineHeight: 1.5 }}>
                  &quot;Şimdi değil&quot; dersen kimseye bildirim gitmez. Onayı istediğin zaman Ayarlar&apos;dan kaldırabilirsin — bu senin alanın.
                </p>
                <div aria-live="polite" style={SR_ONLY}>{onaylaniyor ? 'Bağlantı onaylanıyor' : ''}</div>
              </>
            ) : null}

            {!isVeli && pending && oDurum === 'tamam' ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
                <div aria-hidden style={{ width: 58, height: 58, borderRadius: '50%', background: color.semantic.successBgSoft, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>{BigCheck}</div>
                <h1 ref={baslikRef} tabIndex={-1} style={h1SerifKucuk}>Bağlandı — sınırlar sende.</h1>
                <p style={{ margin: '0 0 22px', fontSize: 13.5, color: color.ink.muted, lineHeight: 1.65, maxWidth: 380 }}>
                  {pending.veliAd} artık çalışma özetini görebilir. Neyi görebildiğini her zaman <strong style={{ color: color.ink.primary }}>Ayarlar → Veli bağlantısı</strong>&apos;ndan kontrol edebilirsin.
                </p>
                <a href="/bugun" style={{ boxSizing: 'border-box', display: 'inline-flex', alignItems: 'center', gap: 9, minHeight: 48, padding: '0 24px', borderRadius: radius.button, background: color.dawn.coralCtaBg, color: '#fff', fontFamily: font.sans, fontSize: 14.5, fontWeight: 800, textDecoration: 'none' }}>Çalışmaya dön</a>
              </div>
            ) : null}
          </div>
        </div>

        {/* Alt destek satırı — coral link (#C2452B) */}
        <p style={{ margin: '18px 0 0', textAlign: 'center', fontSize: 12, color: color.ink.muted, lineHeight: 1.6, maxWidth: 520 }}>
          Takıldıysanız <a href="/sohbet" style={{ color: color.dawn.coralTextOnLight, fontWeight: 700, textDecoration: 'none' }}>destek ekibine yazın</a> — gerçek bir insan, okul saatlerinde ~10 dk içinde döner.
        </p>
      </div>
    </KiroThemeProvider>
  );
}

export default VeliBaglamaPage;
