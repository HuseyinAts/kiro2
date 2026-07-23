// ============================================================================
// KIRO2 — İnteraktif Çözüm (KIRO2 Interaktif Cozum.dc.html)
// Tema = PAPER. Keşif-öğrenme: öğrenci a/b/c kaydırıcılarını sürükler; parabol
// (y=ax²+bx+c) + içgörü kartları İSTEMCİDE deterministik hesaplanır/çizilir.
//
// KANON İSTİSNASI (sunucu-otorite): "istemci cevap uydurmaz" kuralı sohbet /
// çözüm-üretimi içindir. Burada tepe (-b/2a), diskriminant (b²-4ac), kökler ve
// eğri noktaları SAF MATEMATİK — cevap-uydurma DEĞİL, meşru manipülatif.
// Sohbet / ChatBubble / QuestionCard / backend / streaming YOK.
//
// A11y: her <input type=range> aria-label + native valuenow/min/max + klavye ok
// tuşları; içgörü kartları aria-live=polite; SVG role=img + güncel denklem
// aria-label; hit-target ≥44 (kaydırıcı 44px, "Kontrol et" ≥44). Rol dili: SEN.
// Hareket YOK — grafik yalnız re-render ile anlık güncellenir (reduced'da da anlık).
// ============================================================================
import * as React from 'react';

import { color, font } from '../tokens';
import { KiroThemeProvider, numText } from '../ui/theme';
import { SideNav } from '../ui/SideNav';
import { Card } from '../ui/Card';
import { Callout } from '../ui/Callout';
import { IconBadge } from '../ui/IconBadge';
import '../tokens/tokens.css';

// ── SVG viewBox + eksen aralığı (DC ile birebir) ──────────────────────────
const X0 = 10;
const X1 = 290;
const Y0 = 10;
const Y1 = 230;
const X_MIN = -5;
const X_MAX = 5;
const Y_MIN = -10;
const Y_MAX = 10;

const sx = (x: number): number => X0 + ((x - X_MIN) / (X_MAX - X_MIN)) * (X1 - X0);
const sy = (y: number): number => {
  const v = Y1 - ((y - Y_MIN) / (Y_MAX - Y_MIN)) * (Y1 - Y0);
  return Math.max(2, Math.min(238, v));
};

/** 1 ondalık; tam sayıysa kesir gösterme (−0 → "0"). */
function fmt(n: number): string {
  const r = Math.round(n * 10) / 10;
  return Number.isInteger(r) ? String(r) : r.toFixed(1);
}

// ── Katsayı meta — kaydırıcı + etiket rengi (AA-güvenli metin tonları) ─────
interface CoefMeta {
  key: 'a' | 'b' | 'c';
  ad: string;
  ariaLabel: string;
  text: string;
  min: number;
  max: number;
  step: number;
}
const COEF_A: CoefMeta = { key: 'a', ad: 'a · açılım', ariaLabel: 'a katsayısı — açılım', text: color.dawn.coralTextOnLight, min: -2, max: 2, step: 0.1 };
const COEF_B: CoefMeta = { key: 'b', ad: 'b · konum', ariaLabel: 'b katsayısı — konum', text: color.semantic.successTextOnLight, min: -6, max: 6, step: 0.5 };
const COEF_C: CoefMeta = { key: 'c', ad: 'c · yükseklik', ariaLabel: 'c katsayısı — yükseklik', text: color.semantic.riskTextOnLight, min: -6, max: 6, step: 0.5 };

export interface ParabolModel {
  a: number;
  b: number;
  c: number;
  aLabel: string;
  bSign: string;
  bAbs: string;
  cSign: string;
  cAbs: string;
  /** polyline points — eğri (x∈[-5,5], adım 0.2) */
  curve: string;
  /** SVG koordinatında tepe */
  vx: string;
  vy: string;
  hasVertex: boolean;
  /** insan-okur tepe (fmt) */
  vertexX: string;
  vertexY: string;
  /** ham tepe (görev kontrolü için) */
  tepeX: number | null;
  tepeY: number | null;
  up: boolean;
  dirText: 'yukarı' | 'aşağı';
  widthText: string;
  insight: string;
  /** b²−4ac (a≠0 iken); a=0 → null */
  diskriminant: number | null;
  /** görünür aralıktaki gerçek kökler (SVG'de çizilir) */
  kokler: number[];
  /** SVG role=img aria-label — güncel denklem + tepe + kök durumu */
  denklemLabel: string;
}

/**
 * Parabolün TÜM türetilmiş değerlerini İSTEMCİDE deterministik hesaplar.
 * Saf fonksiyon — cevap uydurmaz, yalnız y=ax²+bx+c'yi çizer/ölçer.
 */
export function hesaplaParabol(a: number, b: number, c: number): ParabolModel {
  const pts: string[] = [];
  for (let x = X_MIN; x <= X_MAX + 0.001; x += 0.2) {
    const y = a * x * x + b * x + c;
    pts.push(`${fmt(sx(x))},${fmt(sy(y))}`);
  }
  const curve = pts.join(' ');

  let vx = '150';
  let vy = '120';
  let vertexX = '—';
  let vertexY = '—';
  let tepeX: number | null = null;
  let tepeY: number | null = null;
  let hasVertex = false;
  if (Math.abs(a) > 0.001) {
    const xv = -b / (2 * a);
    const yv = a * xv * xv + b * xv + c;
    vx = fmt(sx(xv));
    vy = fmt(sy(yv));
    vertexX = fmt(xv);
    vertexY = fmt(yv);
    tepeX = xv;
    tepeY = yv;
    hasVertex = true;
  }

  const up = a > 0;
  const absA = Math.abs(a);
  const widthText = absA < 0.001 ? 'doğru (a=0)' : absA >= 1.4 ? 'dar' : absA <= 0.6 ? 'geniş' : 'orta';

  let insight: string;
  if (absA < 0.001) insight = 'a = 0 olunca x² kaybolur ve grafik bir doğruya dönüşür — artık parabol değil!';
  else if (absA >= 1.4) insight = '|a| büyüdükçe kollar birbirine yaklaşır — parabol daralır.';
  else if (absA <= 0.6) insight = '|a| küçüldükçe kollar açılır — parabol yayvanlaşır.';
  else if (!up) insight = 'a negatif → parabol aşağı bakar, tepe noktası bir maksimumdur.';
  else insight = 'c değeri parabolü yukarı/aşağı kaydırır; b ise tepeyi yana taşır.';

  // Diskriminant + kökler (a≠0). "çizilir" için görünür aralıktaki gerçek kökler.
  let diskriminant: number | null = null;
  let kokler: number[] = [];
  if (Math.abs(a) > 0.001) {
    diskriminant = b * b - 4 * a * c;
    if (diskriminant >= 0) {
      const r = Math.sqrt(diskriminant);
      const ham = [(-b - r) / (2 * a), (-b + r) / (2 * a)];
      kokler = ham.filter(
        (k, i) => k >= X_MIN && k <= X_MAX && (i === 0 || Math.abs(k - ham[0]!) > 0.001),
      );
    }
  }

  const aLabel = fmt(a);
  const bSign = b < 0 ? '−' : '+';
  const cSign = c < 0 ? '−' : '+';
  const bAbs = fmt(Math.abs(b));
  const cAbs = fmt(Math.abs(c));
  const denklemLabel =
    `Parabol grafiği. Denklem: y = ${aLabel}x² ${bSign} ${bAbs}x ${cSign} ${cAbs}. ` +
    (hasVertex ? `Tepe noktası (${vertexX}, ${vertexY}). ` : 'a = 0 — grafik bir doğru. ') +
    (diskriminant === null
      ? ''
      : diskriminant < 0
        ? 'Gerçek kök yok — diskriminant negatif.'
        : kokler.length <= 1
          ? 'Tek (çakışık) kök.'
          : 'İki gerçek kök.');

  return {
    a,
    b,
    c,
    aLabel,
    bSign,
    bAbs,
    cSign,
    cAbs,
    curve,
    vx,
    vy,
    hasVertex,
    vertexX,
    vertexY,
    tepeX,
    tepeY,
    up,
    dirText: up ? 'yukarı' : 'aşağı',
    widthText,
    insight,
    diskriminant,
    kokler,
    denklemLabel,
  };
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

// ── Bespoke SVG ikonlar (emoji/stok-ikon YOK) ─────────────────────────────
/** Açılış yönü — U (yukarı) / ∩ (aşağı) parabol yayı */
const YonYay = ({ up }: { up: boolean }) => (
  <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden>
    {up ? <path d="M5 5 C5 20, 19 20, 19 5" /> : <path d="M5 19 C5 4, 19 4, 19 19" />}
  </svg>
);
/** Açıklık — yatay genişleme okları */
const Aciklik = () => (
  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M4 12h16" />
    <path d="M8 8 4 12l4 4" />
    <path d="M16 8l4 4-4 4" />
  </svg>
);
/** Tepe — hedef nokta */
const TepeNokta = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
    <circle cx="12" cy="12" r="6.5" />
    <circle cx="12" cy="12" r="1.6" fill="currentColor" stroke="none" />
  </svg>
);
/** Aktif öğrenme — kıvılcım/şimşek */
const Kivilcim = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M13 2 4 14h6l-1 8 9-12h-6z" />
  </svg>
);

const HEDEF_BG = '#FBF9F6'; // grafik alanı zemini (DC birebir)

export function InteraktifCozumPage(): React.ReactElement {
  const dar = useMedia('(max-width: 760px)');
  const tekSutun = useMedia('(max-width: 900px)');

  const [a, setA] = React.useState(1);
  const [b, setB] = React.useState(-2);
  const [c, setC] = React.useState(-1);
  const [gorevSonuc, setGorevSonuc] = React.useState<{ ok: boolean; msg: string } | null>(null);

  const m = React.useMemo(() => hesaplaParabol(a, b, c), [a, b, c]);

  const setter: Record<CoefMeta['key'], (v: number) => void> = { a: setA, b: setB, c: setC };
  const deger: Record<CoefMeta['key'], number> = { a, b, c };

  const kontrolEt = () => {
    const basarili =
      a < 0 && m.tepeX !== null && m.tepeY !== null && Math.abs(m.tepeX) < 0.3 && Math.abs(m.tepeY - 3) < 0.3;
    setGorevSonuc(
      basarili
        ? { ok: true, msg: "Tam isabet — tepe (0, 3)'e oturdu. a'yı negatif yaptın, b'yi 0'a, c'yi 3'e getirdin." }
        : { ok: false, msg: `Henüz değil — tepe şu an (${m.vertexX}, ${m.vertexY}). a negatif mi? b'yi 0'a, c'yi 3'e yaklaştır.` },
    );
  };

  const kartOrtak: React.CSSProperties = { boxSizing: 'border-box' };
  const dirColor = m.up ? color.dawn.coralTextOnLight : color.semantic.riskTextOnLight;

  const kaydirici = (meta: CoefMeta) => (
    <div style={{ boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
        <span style={{ fontSize: 13, fontWeight: 700, color: meta.text }}>{meta.ad}</span>
        <span style={{ ...numText, fontSize: 13, fontWeight: 800, color: color.ink.primary }}>{fmt(deger[meta.key])}</span>
      </div>
      <input
        type="range"
        aria-label={meta.ariaLabel}
        min={meta.min}
        max={meta.max}
        step={meta.step}
        value={deger[meta.key]}
        onChange={(e) => {
          setter[meta.key](parseFloat(e.target.value));
          setGorevSonuc(null);
        }}
        style={{ boxSizing: 'border-box', width: '100%', height: 44, accentColor: meta.text, cursor: 'pointer' }}
      />
    </div>
  );

  return (
    <KiroThemeProvider theme="paper">
      <div
        className="k-paper"
        style={{ boxSizing: 'border-box', minHeight: '100vh', display: 'flex', background: color.paper.bg, fontFamily: font.sans, color: color.ink.primary, fontSize: 14 }}
      >
        <SideNav role="ogrenci" activeId="interaktif" collapsed={dar} userName="Öğrenci" userSub="" onAssistant={() => undefined} />

        <main style={{ flex: 1, minWidth: 0, height: '100vh', overflowY: 'auto' }}>
          {/* Header */}
          <header
            style={{ boxSizing: 'border-box', position: 'sticky', top: 0, zIndex: 5, minHeight: 64, display: 'flex', alignItems: 'center', gap: 14, padding: '10px 24px', flexWrap: 'wrap', background: color.paper.card, borderBottom: `1px solid ${color.paper.border}` }}
          >
            <div style={{ minWidth: 0, flex: 1, lineHeight: 1.2 }}>
              <h1 style={{ margin: 0, fontSize: 16, fontWeight: 800 }}>İnteraktif Çözüm</h1>
              <div style={{ fontSize: 12, fontWeight: 600, color: color.ink.muted, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>Okuma değil — kaydırarak keşfet</div>
            </div>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: 11, fontWeight: 800, color: color.semantic.riskTextOnLight, background: color.semantic.riskBgSoft, padding: '6px 11px', borderRadius: 8 }}>
              <Kivilcim />
              Aktif öğrenme
            </span>
          </header>

          <div style={{ boxSizing: 'border-box', maxWidth: 1000, margin: '0 auto', padding: '26px 30px 50px' }}>
            {/* Başlık bloğu */}
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 11, fontWeight: 800, color: color.ink.muted, letterSpacing: '0.05em', marginBottom: 6 }}>AYT MATEMATİK · PARABOL</div>
              <h2 style={{ margin: '0 0 6px', fontSize: 23, fontWeight: 800, letterSpacing: '-0.02em' }}>Katsayılar parabolü nasıl değiştirir?</h2>
              <p style={{ margin: 0, fontSize: 14, color: color.ink.muted, lineHeight: 1.55, maxWidth: 620 }}>
                a, b ve c'yi kaydır; grafiğin <strong style={{ color: color.ink.secondary }}>anında</strong> nasıl tepki verdiğini gör. Formülü ezberleme — davranışını hisset.
              </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: tekSutun ? '1fr' : '1.25fr 1fr', gap: 18 }}>
              {/* GRAFİK + KAYDIRICILAR */}
              <Card padding={22} style={{ ...kartOrtak, borderRadius: 18 }}>
                {/* Denklem */}
                <div style={{ ...numText, display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'center', gap: 6, marginBottom: 14, fontSize: 20, fontWeight: 800 }}>
                  <span>y =</span>
                  <span style={{ color: COEF_A.text }}>{m.aLabel}</span>
                  <span>x² {m.bSign}</span>
                  <span style={{ color: COEF_B.text }}>{m.bAbs}</span>
                  <span>x {m.cSign}</span>
                  <span style={{ color: COEF_C.text }}>{m.cAbs}</span>
                </div>

                {/* Bespoke SVG parabol — role=img + güncel denklem */}
                <svg viewBox="0 0 300 240" role="img" aria-label={m.denklemLabel} style={{ display: 'block', width: '100%', height: 'auto', background: HEDEF_BG, borderRadius: 12 }}>
                  <line x1="10" y1="120" x2="290" y2="120" stroke="#D9D2C6" strokeWidth="1.5" />
                  <line x1="150" y1="10" x2="150" y2="230" stroke="#D9D2C6" strokeWidth="1.5" />
                  <line x1="10" y1="65" x2="290" y2="65" stroke={color.paper.border} strokeWidth="1" />
                  <line x1="10" y1="175" x2="290" y2="175" stroke={color.paper.border} strokeWidth="1" />
                  <line x1="95" y1="10" x2="95" y2="230" stroke={color.paper.border} strokeWidth="1" />
                  <line x1="205" y1="10" x2="205" y2="230" stroke={color.paper.border} strokeWidth="1" />
                  <polyline points={m.curve} fill="none" stroke="#E0593F" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
                  {/* Kökler (x-kesişimleri) — deterministik çizim */}
                  {m.kokler.map((k) => (
                    <circle key={`kok-${k.toFixed(3)}`} cx={sx(k)} cy={sy(0)} r="4" fill="#fff" stroke="#9A5D0D" strokeWidth="2.5" />
                  ))}
                  {/* Tepe noktası */}
                  {m.hasVertex && <circle cx={m.vx} cy={m.vy} r="5" fill="#fff" stroke="#E0593F" strokeWidth="3" />}
                </svg>

                {/* Kaydırıcılar */}
                <div style={{ marginTop: 18, display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {kaydirici(COEF_A)}
                  {kaydirici(COEF_B)}
                  {kaydirici(COEF_C)}
                </div>
              </Card>

              {/* CANLI İÇGÖRÜLER */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {/* Şu an + Keşfet — kaydırıcı değişince duyurulur */}
                <div aria-live="polite" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <Card padding={20} style={{ ...kartOrtak, borderRadius: 16 }}>
                    <div style={{ fontSize: 13, fontWeight: 800, color: color.ink.primary, marginBottom: 13 }}>Şu an</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 11 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 11 }}>
                        <IconBadge tone="dawn" size={34} icon={<span style={{ color: dirColor, display: 'inline-flex' }}><YonYay up={m.up} /></span>} />
                        <div style={{ fontSize: 13.5, color: color.ink.secondary }}>
                          Kollar <strong style={{ color: color.ink.primary }}>{m.dirText}</strong> açılıyor
                        </div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 11 }}>
                        <IconBadge tone="success" size={34} icon={<Aciklik />} />
                        <div style={{ fontSize: 13.5, color: color.ink.secondary }}>
                          Açıklık: <strong style={{ color: color.ink.primary }}>{m.widthText}</strong>
                        </div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 11 }}>
                        <IconBadge tone="attention" size={34} icon={<TepeNokta />} />
                        <div style={{ fontSize: 13.5, color: color.ink.secondary }}>
                          Tepe noktası: <strong style={{ ...numText, color: color.ink.primary }}>({m.vertexX}, {m.vertexY})</strong>
                        </div>
                      </div>
                    </div>
                  </Card>

                  {/* KEŞFET — dawn/amber gradyan (alarm-kırmızısı YOK) */}
                  <div style={{ boxSizing: 'border-box', background: 'linear-gradient(135deg,#FBF0DE,#FFF3EE)', border: `1px solid ${color.semantic.riskBorderSoft}`, borderRadius: 16, padding: 18 }}>
                    <div style={{ fontSize: 11, fontWeight: 800, color: color.dawn.coralTextOnLight, letterSpacing: '0.04em', marginBottom: 7 }}>KEŞFET</div>
                    <div style={{ fontSize: 13.5, color: color.ink.secondary, lineHeight: 1.6 }}>{m.insight}</div>
                  </div>
                </div>

                {/* Mini görev */}
                <Card padding={18} style={{ ...kartOrtak, borderRadius: 16 }}>
                  <div style={{ fontSize: 13, fontWeight: 800, color: color.ink.primary, marginBottom: 8 }}>Mini görev</div>
                  <div style={{ fontSize: 13, color: color.ink.secondary, lineHeight: 1.55 }}>
                    a'yı negatif yap, sonra tepe noktasını <strong style={{ ...numText, color: color.ink.primary }}>(0, 3)</strong>'e taşımayı dene. Hangi katsayıları değiştirmen gerekti?
                  </div>
                  <button
                    type="button"
                    onClick={kontrolEt}
                    style={{ boxSizing: 'border-box', marginTop: 13, width: '100%', minHeight: 44, background: color.dawn.coralCtaBg, color: '#fff', border: 'none', borderRadius: 11, padding: '11px 12px', fontFamily: font.sans, fontSize: 13.5, fontWeight: 700, cursor: 'pointer' }}
                  >
                    Kontrol et
                  </button>
                  <div role="status" aria-live="polite">
                    {gorevSonuc && (
                      <div style={{ marginTop: 12 }}>
                        <Callout tone={gorevSonuc.ok ? 'success' : 'dawn'}>{gorevSonuc.msg}</Callout>
                      </div>
                    )}
                  </div>
                </Card>
              </div>
            </div>
          </div>
        </main>
      </div>
    </KiroThemeProvider>
  );
}

export default InteraktifCozumPage;
