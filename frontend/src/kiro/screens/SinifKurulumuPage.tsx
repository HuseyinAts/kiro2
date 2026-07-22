// ============================================================================
// KIRO2 — Sınıf Kurulumu (SPRINT11 · KIRO2 Sinif Kurulum.dc.html)
// Tema = PAPER. Rol = ÖĞRETMEN. 3 adımlı sihirbaz: Bilgi → Davet(kod) → Hazır.
// DC birebir kopya + yapı (DC>spec tiebreaker): DC'nin SEN dili ("yenileyebilirsin"/
// "dönebilirsin") + tek "yalnız size görünür" satırı KORUNDU — SİZ'e çevrilmedi.
// SUNUCU-OTORİTE: katılım kodu/link postSinif yanıtından; istemci kod ÜRETMEZ.
// Rotate → rotateKatilimKodu (mock; backend YOK). SideNav YOK — DC standalone onboarding.
// ============================================================================
import * as React from 'react';

import { configureKiroApi, postSinif, rotateKatilimKodu } from '../api/api-client';
import type { MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';
import { color, font, radius, shadow, motion } from '../tokens';
import type { KurulanSinif } from '../types';
import { KiroThemeProvider, numText } from '../ui/theme';
import { useReducedMotion } from '../ui/ConfettiDawn';
import '../tokens/tokens.css';

configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });

// DC'ye özgü sıcak tint'ler — token karşılığı yok (dekoratif; ham hex istisnası).
const PEACH_TINT = '#FFF8F2';   // seçili segment + kaygı-duyarlı panel zemini
const PEACH_BORDER = '#FFE3D8'; // kaygı-duyarlı panel kenarı
const HERO_BG = `radial-gradient(1100px 460px at 50% -8%, #FFF3EE 0%, ${color.paper.bg} 62%)`;

type Adim = 'bilgi' | 'davet' | 'hazir';
type SeviyeSeg = '11' | '12' | 'mez';
type AlanSeg = 'say' | 'ea' | 'soz';

// DC Düzey = [11 · 12 · Mezun] (spec 9/10/11/12/Mezun ile ayrışır → DC>spec).
const DUZEY: { key: SeviyeSeg; label: string }[] = [
  { key: '11', label: '11. Sınıf' },
  { key: '12', label: '12. Sınıf' },
  { key: 'mez', label: 'Mezun' },
];
const ALAN: { key: AlanSeg; label: string }[] = [
  { key: 'say', label: 'Sayısal' },
  { key: 'ea', label: 'Eşit Ağırlık' },
  { key: 'soz', label: 'Sözel' },
];
const ADIM_ETIKET: Record<Adim, string> = {
  bilgi: 'Adım 1 / 3 · Bilgi',
  davet: 'Adım 2 / 3 · Davet',
  hazir: 'Adım 3 / 3 · Hazır',
};
const ADIM_NO: Record<Adim, number> = { bilgi: 1, davet: 2, hazir: 3 };

const STEP_ANIM =
  '@keyframes kiroStepIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }';

const SR_ONLY: React.CSSProperties = {
  position: 'absolute', width: 1, height: 1, padding: 0, margin: -1,
  overflow: 'hidden', clip: 'rect(0 0 0 0)', whiteSpace: 'nowrap', border: 0,
};

// jsdom matchMedia'sız SSR-guard'lı (BREAKPOINT_SPEC §3).
function useMedia(query: string): boolean {
  const [esles, setEsles] = React.useState(false);
  React.useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
      return;
    }
    const mq = window.matchMedia(query);
    const on = () => setEsles(mq.matches);
    on();
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, [query]);
  return esles;
}

// --- Bespoke ikonlar (emoji YOK) --------------------------------------------

const CapIcon = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M12 3 3 8l9 5 9-5-9-5Z" /><path d="M3 16l9 5 9-5M3 12l9 5 9-5" />
  </svg>
);
const CopyIcon = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <rect x="9" y="9" width="13" height="13" rx="2" /><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
  </svg>
);
const ShareIcon = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M4 12v7a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-7" /><polyline points="16 6 12 2 8 6" /><line x1="12" y1="2" x2="12" y2="15" />
  </svg>
);
const RefreshIcon = (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M21 12a9 9 0 1 1-2.64-6.36" /><polyline points="21 3 21 9 15 9" />
  </svg>
);
const CheckIcon = (
  <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke={color.semantic.success} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <polyline points="20 6 9 17 4 12" />
  </svg>
);
const LockIcon = (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden style={{ flexShrink: 0 }}>
    <rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" />
  </svg>
);

// --- Alt bileşenler ----------------------------------------------------------

/** DC full-width segment (radio) — seçili = coral kenar + şeftali tint. hit≥44. */
function SegButton({ label, secili, onClick }: { label: string; secili: boolean; onClick: () => void }) {
  return (
    <button
      type="button" role="radio" aria-checked={secili} onClick={onClick}
      style={{
        boxSizing: 'border-box', flex: 1, minWidth: 0, minHeight: 44, height: 44,
        borderRadius: 11, border: `1.5px solid ${secili ? color.dawn.coral : color.paper.border}`,
        background: secili ? PEACH_TINT : color.paper.card,
        fontFamily: font.sans, fontSize: 13.5, fontWeight: 700, color: color.ink.primary, cursor: 'pointer',
      }}
    >
      {label}
    </button>
  );
}

/** Paper beyaz-metin coral CTA (coralCtaBg #C2452B, AA). Tam genişlik, hit≥44. */
function CtaButton({ children, onClick, disabled }: { children: React.ReactNode; onClick: () => void; disabled?: boolean }) {
  return (
    <button
      type="button" onClick={onClick} disabled={disabled}
      style={{
        boxSizing: 'border-box', width: '100%', minHeight: 50, height: 50, border: 'none',
        borderRadius: radius.button,
        background: disabled ? color.paper.borderFaint : color.dawn.coralCtaBg,
        color: disabled ? color.ink.faded3 : '#fff',
        fontFamily: font.sans, fontSize: 15, fontWeight: 800,
        cursor: disabled ? 'default' : 'pointer', boxShadow: disabled ? 'none' : shadow.coralCta,
      }}
    >
      {children}
    </button>
  );
}

/** İkonlu ikincil buton (kopyala / paylaş) — hit≥44. */
function MiniButton({ children, onClick, icon }: { children: React.ReactNode; onClick: () => void; icon: React.ReactNode }) {
  return (
    <button
      type="button" onClick={onClick}
      style={{
        boxSizing: 'border-box', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 7,
        minHeight: 44, padding: '0 15px', border: `1px solid ${color.paper.border}`, borderRadius: 11,
        background: color.paper.card, color: color.ink.secondary,
        fontFamily: font.sans, fontSize: 13, fontWeight: 700, cursor: 'pointer',
      }}
    >
      {icon}{children}
    </button>
  );
}

/** Altı çizili metin butonu (yenile / sonra paylaş) — hit≥44 (şeffaf pad). */
function TextButton({ children, onClick, icon }: { children: React.ReactNode; onClick: () => void; icon?: React.ReactNode }) {
  return (
    <button
      type="button" onClick={onClick}
      style={{
        boxSizing: 'border-box', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6,
        minHeight: 44, padding: '0 8px', background: 'transparent', border: 'none',
        fontFamily: font.sans, fontSize: 12.5, fontWeight: 700, color: color.ink.muted, cursor: 'pointer', textDecoration: 'underline',
      }}
    >
      {icon}{children}
    </button>
  );
}

const h1Serif: React.CSSProperties = {
  margin: '0 0 8px', fontFamily: font.serif, fontStyle: 'italic', fontWeight: 400,
  fontSize: 30, lineHeight: 1.12, color: color.ink.primary, outline: 'none',
};
const pAlt: React.CSSProperties = { margin: '0 0 20px', fontSize: 13.5, color: color.ink.muted, lineHeight: 1.6 };

// pano-kopya (jsdom / eski tarayıcı guard'lı)
function panoyaYaz(text: string): void {
  try {
    if (typeof navigator !== 'undefined' && navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
      void navigator.clipboard.writeText(text);
    }
  } catch {
    /* pano yok (jsdom) — sessiz geç */
  }
}

const kodGoster = (k: string): string => (k.length === 6 ? `${k.slice(0, 3)} ${k.slice(3)}` : k);

// --- Ekran -------------------------------------------------------------------

export interface SinifKurulumuPageProps {
  /** Storybook önizleme: hangi adımda başlasın (üretimde geçilmez → 'bilgi'). */
  baslangicAdim?: Adim;
}

export function SinifKurulumuPage({ baslangicAdim }: SinifKurulumuPageProps = {}): React.ReactElement {
  const reduced = useReducedMotion();
  const dar = useMedia('(max-width: 560px)');
  const [adim, setAdim] = React.useState<Adim>(baslangicAdim ?? 'bilgi');
  const [ad, setAd] = React.useState('');
  const [seviye, setSeviye] = React.useState<SeviyeSeg>('12');
  const [alan, setAlan] = React.useState<AlanSeg>('say');
  const [kurulan, setKurulan] = React.useState<KurulanSinif | null>(null);
  const [kopyalandi, setKopyalandi] = React.useState(false);
  const [duyuru, setDuyuru] = React.useState('');
  const [gonderiliyor, setGonderiliyor] = React.useState(false);
  const [hata, setHata] = React.useState(false);

  const baslikRef = React.useRef<HTMLHeadingElement>(null);
  const ilk = React.useRef(true);
  // Adım geçişinde odağı yeni adımın başlığına taşı (odak-sırası korunur).
  React.useEffect(() => {
    if (ilk.current) {
      ilk.current = false;
      return;
    }
    baslikRef.current?.focus();
  }, [adim]);

  // Storybook önizleme: davet/hazır adımında başlarken kodu SUNUCUDAN (postSinif) al.
  React.useEffect(() => {
    if (baslangicAdim && baslangicAdim !== 'bilgi') {
      postSinif({ ad: '12-A', seviye: '12. Sınıf', ders: 'Sayısal' })
        .then(setKurulan)
        .catch(() => undefined);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const seviyeLabel = DUZEY.find((d) => d.key === seviye)?.label ?? '12. Sınıf';
  const alanLabel = ALAN.find((a) => a.key === alan)?.label ?? 'Sayısal';
  const adGoster = kurulan?.ad || ad.trim() || '12-A';

  const olustur = (): void => {
    if (gonderiliyor) {
      return;
    }
    setGonderiliyor(true);
    setHata(false);
    // SUNUCU-OTORİTE: kod/link postSinif yanıtından — istemci üretmez.
    postSinif({ ad: ad.trim() || '12-A', seviye: seviyeLabel, ders: alanLabel })
      .then((res) => {
        setKurulan(res);
        setKopyalandi(false);
        setAdim('davet');
      })
      .catch(() => setHata(true))
      .finally(() => setGonderiliyor(false));
  };

  const kopyala = (): void => {
    panoyaYaz(kurulan?.katilimKodu ?? '');
    setKopyalandi(true);
    setDuyuru('Kod kopyalandı');
  };

  const paylas = (): void => {
    const link = kurulan?.katilimLink ?? '';
    const nav = navigator as Navigator & { share?: (d: ShareData) => Promise<void> };
    if (typeof nav.share === 'function') {
      nav.share({ title: 'KIRO2 sınıf daveti', text: `${adGoster} sınıfına katıl`, url: link }).catch(() => undefined);
      setDuyuru('Davet paylaşıldı');
    } else {
      panoyaYaz(link);
      setDuyuru('Davet linki kopyalandı');
    }
  };

  const yenile = (): void => {
    if (!kurulan) {
      return;
    }
    // Rotate MOCK (backend YOK) — yeni kod yine SUNUCUDAN (server-sim).
    rotateKatilimKodu(kurulan.id)
      .then((res) => {
        setKurulan({ ...kurulan, katilimKodu: res.katilimKodu, katilimLink: res.katilimLink });
        setKopyalandi(false);
        setDuyuru('Kod yenilendi');
      })
      .catch(() => undefined);
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
          fontFamily: font.sans, color: color.ink.primary,
          display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '0 20px 60px',
        }}
      >
        {/* Üst bar */}
        <div style={{ boxSizing: 'border-box', width: '100%', maxWidth: 640, display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 10, rowGap: 8, padding: '22px 0 0' }}>
          <span aria-hidden style={{ width: 30, height: 30, borderRadius: 9, background: color.dawn.coralCtaBg, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{CapIcon}</span>
          <span style={{ fontWeight: 800, fontSize: 16 }}>KIRO<span style={{ color: color.dawn.coralTextOnLight }}>2</span></span>
          <span style={{ fontSize: 11, fontWeight: 800, letterSpacing: '0.06em', textTransform: 'uppercase', color: color.semantic.riskTextOnLight, background: color.semantic.riskBgSoft, border: `1px solid ${color.semantic.riskBorderSoft}`, borderRadius: 999, padding: '3px 10px', marginLeft: 4 }}>Öğretmen · sınıf kurulumu</span>
          <div style={{ flex: 1, minWidth: 0 }} />
          <span aria-live="polite" style={{ ...numText, fontSize: 11.5, fontWeight: 800, letterSpacing: '0.08em', color: color.ink.muted, textTransform: 'uppercase' }}>{ADIM_ETIKET[adim]}</span>
        </div>

        {/* İlerleme (dekoratif; adım göstergesi aria-live etiket üzerinden) */}
        <div aria-hidden style={{ boxSizing: 'border-box', width: '100%', maxWidth: 560, display: 'flex', gap: 6, marginTop: 14 }}>
          {[1, 2, 3].map((n) => (
            <span key={n} style={{ flex: 1, minWidth: 0, height: 4, borderRadius: 999, background: n <= ADIM_NO[adim] ? color.dawn.coral : color.paper.border }} />
          ))}
        </div>

        {/* Kart */}
        <div style={cardStyle}>
          {!reduced ? <style>{STEP_ANIM}</style> : null}
          <div key={adim} style={{ animation: reduced ? undefined : `kiroStepIn 0.24s ${motion.easing} both` }}>

            {/* ADIM 1 · BİLGİ */}
            {adim === 'bilgi' ? (
              <>
                <h1 ref={baslikRef} tabIndex={-1} style={h1Serif}>İlk sınıfını kur.</h1>
                <p style={{ ...pAlt, marginBottom: 22 }}>İki dakika sürer. Öğrenciler kodla katılır — liste kendiliğinden dolar.</p>

                <label htmlFor="sk-ad" style={{ display: 'block', fontSize: 12.5, fontWeight: 700, color: color.ink.secondary, marginBottom: 7 }}>Sınıf adı</label>
                <input
                  id="sk-ad" value={ad} onChange={(e) => setAd(e.target.value)} placeholder="örn. 12-A"
                  style={{ boxSizing: 'border-box', width: '100%', height: 48, padding: '0 15px', border: `1px solid ${color.paper.borderStrong}`, borderRadius: 12, background: color.paper.subtle, fontFamily: font.sans, fontSize: 15, fontWeight: 700, color: color.ink.primary, outline: 'none' }}
                />

                <div style={{ marginTop: 16, fontSize: 12.5, fontWeight: 700, color: color.ink.secondary }}>Düzey</div>
                <div role="radiogroup" aria-label="Düzey" style={{ display: 'flex', gap: 8, marginTop: 7 }}>
                  {DUZEY.map((d) => <SegButton key={d.key} label={d.label} secili={seviye === d.key} onClick={() => setSeviye(d.key)} />)}
                </div>

                <div style={{ marginTop: 16, fontSize: 12.5, fontWeight: 700, color: color.ink.secondary }}>Alan</div>
                <div role="radiogroup" aria-label="Alan" style={{ display: 'flex', gap: 8, marginTop: 7 }}>
                  {ALAN.map((a) => <SegButton key={a.key} label={a.label} secili={alan === a.key} onClick={() => setAlan(a.key)} />)}
                </div>

                <div style={{ marginTop: 22 }}>
                  <CtaButton onClick={olustur} disabled={gonderiliyor}>Sınıfı oluştur</CtaButton>
                </div>
                {hata ? (
                  <div role="alert" style={{ marginTop: 12, fontSize: 12.5, lineHeight: 1.5, color: color.semantic.riskTextOnLight }}>
                    Sınıf şu an kurulamadı — sorun sende değil, bağlantı bir soluklandı. Birazdan yeniden dene.
                  </div>
                ) : null}
              </>
            ) : null}

            {/* ADIM 2 · DAVET KODU */}
            {adim === 'davet' ? (
              <>
                <h1 ref={baslikRef} tabIndex={-1} style={h1Serif}>{adGoster} hazır — şimdi öğrenciler.</h1>
                <p style={pAlt}>Bu kodu tahtaya yaz ya da sınıf grubunda paylaş. Öğrenciler <strong style={{ color: color.ink.primary }}>Ayarlar → Sınıfa katıl</strong>&apos;dan girer.</p>

                <div style={{ boxSizing: 'border-box', border: `1.5px dashed ${color.paper.borderStrong}`, borderRadius: 16, padding: 22, textAlign: 'center', background: color.paper.subtle }}>
                  <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: '0.08em', color: color.ink.muted, textTransform: 'uppercase', marginBottom: 8 }}>Sınıf katılım kodu</div>
                  <div style={{ ...numText, fontSize: 'clamp(26px, 8.5vw, 38px)', fontWeight: 800, letterSpacing: '0.18em', color: color.ink.primary, overflowWrap: 'anywhere' }}>{kodGoster(kurulan?.katilimKodu ?? '')}</div>
                  <div style={{ display: 'flex', justifyContent: 'center', flexWrap: 'wrap', gap: 9, marginTop: 14 }}>
                    <MiniButton onClick={kopyala} icon={CopyIcon}>{kopyalandi ? 'Kopyalandı' : 'Kodu kopyala'}</MiniButton>
                    <MiniButton onClick={paylas} icon={ShareIcon}>Davet linkini paylaş</MiniButton>
                  </div>
                  <div style={{ marginTop: 10, fontSize: 11.5, color: color.ink.muted }}>Kod süresiz geçerli; istediğin an yenileyebilirsin.</div>
                  <div style={{ display: 'flex', justifyContent: 'center', marginTop: 2 }}>
                    <TextButton onClick={yenile} icon={RefreshIcon}>Kodu yenile</TextButton>
                  </div>
                </div>

                <div aria-live="polite" style={SR_ONLY}>{duyuru}</div>

                <div style={{ boxSizing: 'border-box', marginTop: 16, padding: '14px 16px', background: PEACH_TINT, border: `1px solid ${PEACH_BORDER}`, borderRadius: 13 }}>
                  <div style={{ fontSize: 12, fontWeight: 800, color: color.dawn.coralTextOnLight, marginBottom: 8 }}>Kaygı-duyarlı varsayılanlar — sınıfla birlikte gelir</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 12.5, color: color.ink.secondary, lineHeight: 1.5 }}>
                    <div>· Sınıf içi sıralama öğrencilere <strong style={{ color: color.ink.primary }}>yayınlanmaz</strong> — herkes kendi &quot;sen vs dün&quot; grafiğini görür.</div>
                    <div>· Geciken ödev &quot;<strong style={{ color: color.ink.primary }}>bekliyor</strong>&quot; olarak görünür; suçlayıcı dil hiçbir yüzeyde kullanılmaz.</div>
                    <div>· Risk sinyalleri yalnız size görünür — öğrenciye bayrak <strong style={{ color: color.ink.primary }}>gösterilmez</strong>.</div>
                  </div>
                </div>

                <div style={{ marginTop: 20 }}>
                  <CtaButton onClick={() => setAdim('hazir')}>Devam et</CtaButton>
                </div>
                <div style={{ display: 'flex', justifyContent: 'center', marginTop: 10 }}>
                  <TextButton onClick={() => setAdim('hazir')}>Kodu sonra paylaşacağım</TextButton>
                </div>
              </>
            ) : null}

            {/* ADIM 3 · HAZIR */}
            {adim === 'hazir' ? (
              <>
                <div aria-hidden style={{ width: 56, height: 56, borderRadius: 17, background: color.semantic.successBgSoft, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>{CheckIcon}</div>
                <h1 ref={baslikRef} tabIndex={-1} style={h1Serif}>{adGoster} kuruldu.</h1>
                <p style={pAlt}>Öğrenciler katıldıkça panelde belirecek — boş liste bir sorun değil, başlangıçtır. İlk ödevi şimdi hazırlayabilir ya da sınıf dolunca dönebilirsin.</p>
                <a href="/ogretmen/panel" style={{ boxSizing: 'border-box', display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 50, width: '100%', textDecoration: 'none', background: color.dawn.coralCtaBg, color: '#fff', borderRadius: radius.button, padding: '15px', fontSize: 15, fontWeight: 800, boxShadow: shadow.coralCta }}>Panele git</a>
                <a href="/ogretmen/odev-atama" style={{ boxSizing: 'border-box', display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 44, width: '100%', textDecoration: 'none', background: color.paper.card, color: color.ink.secondary, border: `1px solid ${color.paper.border}`, borderRadius: radius.button, padding: '13px', fontSize: 13.5, fontWeight: 700, marginTop: 10 }}>İlk ödevi hazırla</a>
              </>
            ) : null}
          </div>
        </div>

        {/* Alt gizlilik notu */}
        <div style={{ boxSizing: 'border-box', width: '100%', maxWidth: 560, marginTop: 14, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 7, fontSize: 12, fontWeight: 600, color: color.ink.muted, textAlign: 'center' }}>
          {LockIcon}
          Öğrenci sohbetleri, ruh hâli ve tekil cevaplar öğretmene hiçbir zaman açılmaz.
        </div>
      </div>
    </KiroThemeProvider>
  );
}

export default SinifKurulumuPage;
