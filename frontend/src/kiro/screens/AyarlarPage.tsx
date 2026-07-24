// ============================================================================
// KIRO2 — Ayarlar & Profil (SPRINT10-C · KIRO2 Ayarlar.dc.html)
// Tema = PAPER + KİLİTLİ (çalışma yüzeyi; tema-değiştirme YOK — görünüm bölümü
// yalnız bilgilendirir: "Çalışma ekranları göz konforu için hep aydınlık kalır").
// ROL: öğrenci → SEN dili.
//
// Yapı: SideNav(ogrenci, activeId=settings) + sağ tek-kolon kart yığını (max 900):
//   (1) profil-hero (getMe persona) · (2) GÖMÜLÜ DUSK abonelik-banner (#2A2433→#3A3145,
//   ikincil metin dusk.ink2) → /abonelik · (3) "Hedefin" günlük hedef stepper + ProgressBar
//   (useAyar.setDailyGoal) · (4) 5 Bildirim tercihi (Switch → useAyar.toggleBildirim) ·
//   (5) Odak & gizlilik: Sakin mod + Sıralamayı gizle · (6) Görünüm KİLİTLİ (disabled Switch) ·
//   (7) Hesap (e-posta + Çıkış yap) · (8) dipnot.
//
// SUNUCU-OTORİTE: persona getMe'den; abonelik durumu getAbonelik'ten (ikincil, tolere).
// Ayarlar client-persist (Zustand ayarStore, Faz4 server-sync). "Kaydedildi" optimistik
// flash (role=status, sonlu). KANON: paper CTA/aktif-track = coralCtaBg #C2452B; açık-zeminde
// coral METİN #C2452B (#FF6F5C YASAK olarak metin); risk=amber; bespoke SVG (emoji YOK);
// box-sizing:border-box HER container (KÖK dahil); hit-target ≥44px; sayılar tabular.
// Hareket YOK (Switch kendi RM-guard'ını taşır) → sayfa transition/animation KULLANMAZ.
// ============================================================================
import * as React from 'react';

import { getAbonelik, getMe } from '../api/api-client';
import { color, font, radius } from '../tokens';
import type { AbonelikData, Persona } from '../types';
import { useAyar } from '../lib/ayarStore';
import type { BildirimAyar } from '../lib/ayarStore';
import { KiroThemeProvider, numText } from '../ui/theme';
import { ErrorState } from '../ui/ErrorState';
import { ProgressBar } from '../ui/ProgressBar';
import { Skeleton } from '../ui/Skeleton';
import { Switch } from '../ui';
import { SideNav } from '../ui/SideNav';
import '../tokens/tokens.css';

// Görünüm ekran sabiti: çalışma yüzeyleri hep aydınlık — tema-değiştirme yok.
const themeLocked = true;
const HEDEF_MIN = 15;
const HEDEF_MAX = 180;
const HEDEF_ADIM = 15;

// --- Bespoke ikonlar (emoji/stok-ikon YOK) ----------------------------------

function CheckIcon({ stroke, size = 14 }: { stroke: string; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}
function EditIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" />
    </svg>
  );
}
function CrownIcon() {
  return (
    <svg width="21" height="21" viewBox="0 0 24 24" fill="#fff" aria-hidden>
      <path d="M5 16 3 5l5.5 4L12 4l3.5 5L21 5l-2 11H5Zm0 3h14v2H5z" />
    </svg>
  );
}
function ChevronIcon({ stroke }: { stroke: string }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }} aria-hidden>
      <polyline points="9 6 15 12 9 18" />
    </svg>
  );
}
function CalendarIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={color.dawn.coralTextOnLight} strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <rect x="3" y="4" width="18" height="17" rx="2" />
      <path d="M3 9h18M8 2v4M16 2v4" />
    </svg>
  );
}
function LockIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color.ink.muted} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <rect x="4" y="11" width="16" height="10" rx="2" />
      <path d="M8 11V7a4 4 0 0 1 8 0v4" />
    </svg>
  );
}
function LogoutIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={color.dawn.coralTextOnLight} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  );
}

// --- Bildirim satırları (store anahtarı ile birebir; kanon: baskı/alarm dili YOK) ---
const BILDIRIM_SATIRLARI: { key: keyof BildirimAyar; label: string; desc: string }[] = [
  { key: 'fsrs', label: 'FSRS tekrar hatırlatması', desc: 'Kartların hazır olduğunda — günde en fazla bir kez.' },
  { key: 'zayifKonu', label: 'Zayıf konu dokunuşu', desc: 'Bir konuda zorlandığında nazik bir hatırlatma.' },
  { key: 'seri', label: 'Seri hatırlatması', desc: 'Serini korumak üzereyken yumuşakça haber verir.' },
  { key: 'duello', label: 'Düello daveti', desc: 'Bir arkadaşın seni düelloya çağırdığında.' },
  { key: 'basarim', label: 'Başarım bildirimi', desc: 'Yeni bir rozet kazandığında.' },
];

// --- e-posta türetme (persona'dan; ASCII placeholder — fabrikasyon değil) ----
const TR_ASCII: Record<string, string> = {
  ç: 'c', ğ: 'g', ı: 'i', ö: 'o', ş: 's', ü: 'u', â: 'a', î: 'i', û: 'u',
  Ç: 'c', Ğ: 'g', İ: 'i', I: 'i', Ö: 'o', Ş: 's', Ü: 'u',
};
function epostaTuret(ad: string): string {
  let out = '';
  for (const ch of ad) {
    const m = TR_ASCII[ch];
    if (m) out += m;
    else if (/[A-Za-z0-9]/.test(ch)) out += ch.toLowerCase();
    else out += '.';
  }
  out = out.replace(/\.+/g, '.').replace(/^\.|\.$/g, '');
  return `${out || 'ogrenci'}@ornek.com`;
}

// --- Ayar açıklaması için deterministik id (aria-describedby hedefi) ----------
// Etiketler benzersiz → id'ler benzersiz. SR anahtarı okurken açıklamayı da seslendirir.
function ayarSlug(label: string): string {
  let out = '';
  for (const ch of label) {
    const m = TR_ASCII[ch];
    if (m) out += m;
    else if (/[A-Za-z0-9]/.test(ch)) out += ch.toLowerCase();
    else out += '-';
  }
  return 'ayar-' + (out.replace(/-+/g, '-').replace(/^-|-$/g, '') || 'satir') + '-desc';
}

const trSayi = (n: number): string => n.toLocaleString('tr-TR');

// --- Bölüm kartı (paper) -----------------------------------------------------
function Kart({ baslik, altBaslik, children }: { baslik: string; altBaslik?: string; children: React.ReactNode }) {
  return (
    <section
      style={{
        boxSizing: 'border-box',
        background: color.paper.card,
        border: `1px solid ${color.paper.border}`,
        borderRadius: 18,
        padding: 22,
      }}
    >
      <h2 style={{ margin: 0, fontFamily: font.sans, fontSize: 16, fontWeight: 800, color: color.ink.primary }}>{baslik}</h2>
      {altBaslik && <p style={{ margin: '3px 0 0', fontSize: 12.5, color: color.ink.muted, lineHeight: 1.45 }}>{altBaslik}</p>}
      {children}
    </section>
  );
}

// --- Aç/kapa satırı (bildirim + odak/gizlilik + kilitli görünüm) -------------
function AyarSatiri({
  label,
  desc,
  checked,
  onChange,
  disabled,
  ilk,
  trailing,
}: {
  label: string;
  desc: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  disabled?: boolean;
  ilk?: boolean;
  trailing?: React.ReactNode;
}) {
  const descId = ayarSlug(label);
  return (
    <div
      style={{
        boxSizing: 'border-box',
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        padding: '14px 0',
        borderTop: ilk ? undefined : `1px solid ${color.paper.borderFaint}`,
      }}
    >
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: color.ink.primary }}>{label}</div>
        <div id={descId} style={{ fontSize: 12.5, color: color.ink.muted, lineHeight: 1.4 }}>{desc}</div>
      </div>
      {trailing}
      <Switch ariaLabel={label} ariaDescribedby={descId} checked={checked} onChange={onChange} disabled={disabled} />
    </div>
  );
}

// --- Hesap satırı ------------------------------------------------------------
function HesapSatiri({
  baslik,
  alt,
  trailing,
  ilk,
}: {
  baslik: string;
  alt?: string;
  trailing: React.ReactNode;
  ilk?: boolean;
}) {
  return (
    <div
      style={{
        boxSizing: 'border-box',
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        padding: '16px 0',
        minHeight: 44,
        borderTop: ilk ? undefined : `1px solid ${color.paper.borderFaint}`,
      }}
    >
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: color.ink.primary }}>{baslik}</div>
        {alt && <div style={{ ...numText, fontSize: 12.5, color: color.ink.muted }}>{alt}</div>}
      </div>
      {trailing}
    </div>
  );
}

// --- Hesap gezinme satırı (chevron'lu; Şifre değiştir · Gizlilik & veri) -----
// KVKK giriş noktası "Gizlilik & veri"; rota Faz 4 — şimdilik placeholder onClick.
function HesapNavSatiri({ baslik }: { baslik: string }) {
  return (
    <button
      type="button"
      onClick={() => undefined}
      style={{
        boxSizing: 'border-box',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 8,
        width: '100%',
        minHeight: 44,
        padding: '16px 0',
        background: 'transparent',
        border: 'none',
        borderTop: `1px solid ${color.paper.borderFaint}`,
        cursor: 'pointer',
        fontFamily: font.sans,
        fontSize: 14,
        fontWeight: 700,
        color: color.ink.primary,
        textAlign: 'left',
      }}
    >
      {baslik}
      <ChevronIcon stroke={color.ink.muted} />
    </button>
  );
}

// --- Yeşil "doğrulandı" çipi -------------------------------------------------
function DogrulandiCip() {
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 5,
        fontSize: 11.5,
        fontWeight: 700,
        color: color.semantic.successTextOnLight,
        background: color.semantic.successBgSoft,
        padding: '4px 10px',
        borderRadius: 7,
      }}
    >
      <CheckIcon stroke={color.semantic.successTextOnLight} size={12} />
      doğrulandı
    </span>
  );
}

// SideNav ≤760px'te 64px ikon rayına çöker (Ayarlar DC .rnav) — jsdom matchMedia'sız guard'lı.
function useDarEkran(): boolean {
  const [dar, setDar] = React.useState(false);
  React.useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return;
    const mq = window.matchMedia('(max-width: 760px)');
    const on = () => setDar(mq.matches);
    on();
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, []);
  return dar;
}

export function AyarlarPage(): React.ReactElement {
  const dar = useDarEkran();
  const [persona, setPersona] = React.useState<Persona | null>(null);
  const [abonelik, setAbonelik] = React.useState<AbonelikData | null>(null);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);
  const [saved, setSaved] = React.useState(0);

  // Ayar store — selector'larla oku (tüm store'a abone olma).
  const dailyGoal = useAyar((s) => s.dailyGoalMinutes);
  const bildirim = useAyar((s) => s.bildirim);
  const calmMode = useAyar((s) => s.calmMode);
  const hideRanking = useAyar((s) => s.hideRanking);
  const setDailyGoal = useAyar((s) => s.setDailyGoal);
  const toggleBildirim = useAyar((s) => s.toggleBildirim);
  const setCalmMode = useAyar((s) => s.setCalmMode);
  const setHideRanking = useAyar((s) => s.setHideRanking);

  // "Kaydedildi" optimistik flash (sonlu; unmount'ta temizlenir).
  const flashTimer = React.useRef<ReturnType<typeof setTimeout> | null>(null);
  const flash = React.useCallback(() => {
    const t = Date.now();
    setSaved(t);
    if (flashTimer.current) clearTimeout(flashTimer.current);
    flashTimer.current = setTimeout(() => setSaved((cur) => (cur === t ? 0 : cur)), 1600);
  }, []);
  React.useEffect(() => () => { if (flashTimer.current) clearTimeout(flashTimer.current); }, []);

  React.useEffect(() => {
    let alive = true;
    setPersona(null);
    setHata(false);
    // getMe birincil (reddi → ErrorState). getAbonelik ikincil (durum pili; reddi tolere → null).
    Promise.all([getMe(), getAbonelik('ogrenci').catch(() => null)])
      .then(([p, a]) => {
        if (!alive) return;
        setPersona(p);
        setAbonelik(a);
      })
      .catch(() => {
        if (alive) setHata(true);
      });
    return () => {
      alive = false;
    };
  }, [yeniden]);

  const stepHedef = (yon: 1 | -1) => {
    const next = Math.max(HEDEF_MIN, Math.min(HEDEF_MAX, dailyGoal + yon * HEDEF_ADIM));
    if (next !== dailyGoal) {
      setDailyGoal(next);
      flash();
    }
  };
  const onToggleBildirim = (key: keyof BildirimAyar) => {
    toggleBildirim(key);
    flash();
  };
  const onCalmMode = (v: boolean) => {
    setCalmMode(v);
    flash();
  };
  const onHideRanking = (v: boolean) => {
    setHideRanking(v);
    flash();
  };

  const yksYil = persona ? new Date(persona.yksTarihi).getFullYear() : '';
  const yksKalan = persona ? Math.max(0, Math.round((new Date(persona.yksTarihi).getTime() - Date.now()) / 86_400_000)) : 0;
  const premium = abonelik?.mevcutTier === 'premium';

  let icerik: React.ReactNode;
  if (hata) {
    icerik = (
      <ErrorState
        serifTitle="Ayarların şu an gelmedi."
        body="Sorun sende değil — bağlantı bir soluklandı, çalışman güvende. Birazdan yeniden dene."
        onRetry={() => setYeniden((n) => n + 1)}
      />
    );
  } else if (persona === null) {
    icerik = (
      <div aria-busy="true" aria-label="Ayarlar yükleniyor" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        <div style={{ boxSizing: 'border-box', background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 20, padding: 24 }}>
          <Skeleton shape="card" delayMs={0} slowAfterMs={null} />
        </div>
        {[0, 1].map((i) => (
          <div key={i} style={{ boxSizing: 'border-box', background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 18, padding: 22 }}>
            <Skeleton shape="card" delayMs={0} slowAfterMs={null} />
          </div>
        ))}
      </div>
    );
  } else {
    const eposta = epostaTuret(persona.ad);
    icerik = (
      <>
        {/* (1) Profil-hero — coral gradyan, beyaz metin */}
        <section
          style={{
            boxSizing: 'border-box',
            display: 'flex',
            alignItems: 'center',
            gap: 18,
            background: `linear-gradient(140deg, ${color.dawn.coralCtaBg}, ${color.dawn.coral})`,
            borderRadius: 20,
            padding: 24,
            color: '#fff',
            flexWrap: 'wrap',
          }}
        >
          <div
            aria-hidden
            style={{
              boxSizing: 'border-box',
              width: 66,
              height: 66,
              flexShrink: 0,
              borderRadius: 18,
              background: 'rgba(255,255,255,0.16)',
              border: '2px solid rgba(255,255,255,0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              ...numText,
              fontSize: 24,
              fontWeight: 800,
            }}
          >
            {persona.bas}
          </div>
          <div style={{ flex: 1, minWidth: 150 }}>
            <div style={{ fontSize: 21, fontWeight: 800, letterSpacing: '-0.01em' }}>{persona.ad}</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'rgba(255,240,232,0.85)', marginTop: 2 }}>{persona.sinif}</div>
            <div style={{ display: 'flex', gap: 18, marginTop: 13, flexWrap: 'wrap' }}>
              <div>
                <span style={{ ...numText, fontSize: 17, fontWeight: 800 }}>{persona.seviye}</span>
                <span style={{ fontSize: 12, color: 'rgba(255,240,232,0.8)', marginLeft: 5 }}>seviye</span>
              </div>
              <div>
                <span style={{ ...numText, fontSize: 17, fontWeight: 800 }}>{trSayi(persona.xp)}</span>
                <span style={{ fontSize: 12, color: 'rgba(255,240,232,0.8)', marginLeft: 5 }}>XP</span>
              </div>
              <div>
                <span style={{ ...numText, fontSize: 17, fontWeight: 800 }}>{persona.seri}</span>
                <span style={{ fontSize: 12, color: 'rgba(255,240,232,0.8)', marginLeft: 5 }}>gün seri</span>
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={() => undefined}
            style={{
              boxSizing: 'border-box',
              flexShrink: 0,
              alignSelf: 'flex-start',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 7,
              minHeight: 44,
              padding: '0 16px',
              border: '1px solid rgba(255,255,255,0.35)',
              background: 'rgba(255,255,255,0.12)',
              color: '#fff',
              borderRadius: 11,
              fontFamily: font.sans,
              fontSize: 13,
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            <EditIcon />
            Düzenle
          </button>
        </section>

        {/* (2) GÖMÜLÜ DUSK abonelik-banner — /abonelik'e köprü */}
        <a
          href="/abonelik"
          aria-label={premium ? 'Aboneliğin — Premium aktif' : 'Premium\'a geç'}
          style={{
            boxSizing: 'border-box',
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            background: 'linear-gradient(120deg, #2A2433, #3A3145)',
            borderRadius: 18,
            padding: '18px 22px',
            textDecoration: 'none',
          }}
        >
          <span
            aria-hidden
            style={{
              boxSizing: 'border-box',
              width: 46,
              height: 46,
              flexShrink: 0,
              borderRadius: 13,
              background: color.dawn.coral,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <CrownIcon />
          </span>
          <span style={{ flex: 1, minWidth: 0 }}>
            <span style={{ display: 'block', fontSize: 10.5, fontWeight: 800, letterSpacing: '0.09em', color: color.dawn.peach, textTransform: 'uppercase' }}>
              Premium
            </span>
            <span style={{ display: 'block', fontSize: 15, fontWeight: 800, color: '#fff', marginTop: 2 }}>
              {premium ? 'Premium aktif' : 'Sınava kadar tam erişim'}
            </span>
            <span style={{ display: 'block', fontSize: 12.5, color: color.dusk.ink2, marginTop: 2 }}>
              {premium ? 'Tüm motorlar açık — sınava kadar yanındayız.' : '7 gün ücretsiz · CAT/IRT · FSRS · sınırsız soru'}
            </span>
          </span>
          <ChevronIcon stroke="#fff" />
        </a>

        {/* (3) Hedefin — günlük hedef stepper + ProgressBar */}
        <Kart baslik="Hedefin" altBaslik="Tüm plan bu hedefe göre uyarlanır.">
          <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', margin: '16px 0 4px' }}>
            <div style={{ boxSizing: 'border-box', flex: 1, minWidth: 150, background: color.paper.subtle2, borderRadius: 13, padding: 15 }}>
              <div style={{ fontSize: 11.5, fontWeight: 700, color: color.ink.muted, marginBottom: 6 }}>Hedef bölüm</div>
              <div style={{ fontSize: 15, fontWeight: 800, color: color.ink.primary }}>{persona.hedefBolum}</div>
              <div style={{ fontSize: 12.5, color: color.ink.muted, marginTop: 2 }}>{persona.hedefUni}</div>
            </div>
            <div style={{ boxSizing: 'border-box', flex: 1, minWidth: 150, background: color.paper.subtle2, borderRadius: 13, padding: 15 }}>
              <div style={{ fontSize: 11.5, fontWeight: 700, color: color.ink.muted, marginBottom: 6 }}>Hedef sıralama</div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                <span style={{ ...numText, fontSize: 19, fontWeight: 800, color: color.ink.primary }}>{trSayi(persona.hedefSiralama)}</span>
                <span style={{ ...numText, fontSize: 12, color: color.ink.muted }}>şu an ~{trSayi(persona.guncelSiralama)}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 10, fontSize: 12.5, color: color.ink.secondary }}>
                <CalendarIcon />
                <span style={numText}>{yksYil} YKS'ye {trSayi(yksKalan)} gün</span>
              </div>
            </div>
          </div>

          <div
            style={{
              boxSizing: 'border-box',
              marginTop: 12,
              background: color.paper.subtle2,
              borderRadius: 13,
              padding: 16,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
              <div style={{ flex: 1, minWidth: 140 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: color.ink.muted }}>Günlük hedef</div>
                <div style={{ ...numText, fontSize: 22, fontWeight: 800, color: color.ink.primary }}>{dailyGoal} dk</div>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  type="button"
                  aria-label="Günlük hedefi azalt"
                  onClick={() => stepHedef(-1)}
                  disabled={dailyGoal <= HEDEF_MIN}
                  style={hedefBtnStyle(dailyGoal <= HEDEF_MIN)}
                >
                  −
                </button>
                <button
                  type="button"
                  aria-label="Günlük hedefi artır"
                  onClick={() => stepHedef(1)}
                  disabled={dailyGoal >= HEDEF_MAX}
                  style={hedefBtnStyle(dailyGoal >= HEDEF_MAX)}
                >
                  +
                </button>
              </div>
            </div>
            <div style={{ marginTop: 12 }}>
              <ProgressBar
                pct={Math.round((dailyGoal / HEDEF_MAX) * 100)}
                color={color.dawn.coralCtaBg}
                height={7}
                ariaLabel={`Günlük hedef ${dailyGoal} dakika`}
              />
            </div>
            <p style={{ margin: '10px 0 0', fontSize: 12, color: color.ink.muted, lineHeight: 1.45 }}>
              Az ama düzenli — planın bu hedefe göre kendini ayarlar.
            </p>
          </div>
        </Kart>

        {/* (4) Bildirim tercihleri */}
        <Kart baslik="Bildirim tercihleri" altBaslik="Sakin varsayılan: az ve zamanında. Baskı yok.">
          <div style={{ marginTop: 6 }}>
            {BILDIRIM_SATIRLARI.map((r, i) => (
              <AyarSatiri
                key={r.key}
                ilk={i === 0}
                label={r.label}
                desc={r.desc}
                checked={bildirim[r.key]}
                onChange={() => onToggleBildirim(r.key)}
              />
            ))}
          </div>
        </Kart>

        {/* (5) Odak & gizlilik — Sakin mod + Sıralamayı gizle */}
        <Kart baslik="Odak & gizlilik" altBaslik="Deneyimini kendine göre yumuşat.">
          <div style={{ marginTop: 6 }}>
            <AyarSatiri
              ilk
              label="Sakin mod"
              desc="Rozet, konfeti ve kutlama efektlerini kısar — yalın bir akış."
              checked={calmMode}
              onChange={onCalmMode}
            />
            <AyarSatiri
              label="Sıralamayı gizle"
              desc="Lig ve sınıf sıralamalarını gizler; senin dünle kıyasın kalır."
              checked={hideRanking}
              onChange={onHideRanking}
            />
          </div>
        </Kart>

        {/* (6) Görünüm — KİLİTLİ (tema-değiştirme yok) */}
        <Kart baslik="Görünüm">
          <div style={{ marginTop: 6 }}>
            <AyarSatiri
              ilk
              disabled
              label="Tema"
              desc="Çalışma ekranları göz konforu için hep aydınlık kalır."
              checked={themeLocked}
              onChange={() => undefined}
              trailing={
                <span
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 6,
                    fontSize: 12,
                    fontWeight: 700,
                    color: color.ink.muted,
                    background: color.paper.borderFaint,
                    borderRadius: radius.pill,
                    padding: '6px 12px',
                  }}
                >
                  <LockIcon />
                  Otomatik — ekran türüne göre
                </span>
              }
            />
            {/* Vurgu rengi — kilitli bilgi satırı (Tema ile simetri). DC swatch #FF6F5C
                kanon-YASAK → KANON-güvenli coral #C2452B (coralCtaBg) gösterilir. */}
            <div
              style={{
                boxSizing: 'border-box',
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                padding: '14px 0',
                borderTop: `1px solid ${color.paper.borderFaint}`,
              }}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: color.ink.primary }}>Vurgu rengi</div>
                <div style={{ fontSize: 12.5, color: color.ink.muted, lineHeight: 1.4 }}>
                  Marka şafak tonu — uygulamanın kimliği.
                </div>
              </div>
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 8,
                  fontSize: 12.5,
                  fontWeight: 700,
                  color: color.ink.muted,
                  background: color.paper.borderFaint,
                  borderRadius: radius.pill,
                  padding: '7px 14px',
                }}
              >
                <span
                  aria-hidden
                  style={{
                    width: 14,
                    height: 14,
                    flexShrink: 0,
                    borderRadius: '50%',
                    background: color.dawn.coralCtaBg,
                    boxShadow: '0 0 0 2px #fff',
                  }}
                />
                Şafak mercanı
              </span>
            </div>
          </div>
        </Kart>

        {/* (7) Hesap */}
        <Kart baslik="Hesap">
          <div style={{ marginTop: 6 }}>
            <HesapSatiri ilk baslik="E-posta" alt={eposta} trailing={<DogrulandiCip />} />
            <HesapNavSatiri baslik="Şifre değiştir" />
            <HesapNavSatiri baslik="Gizlilik & veri" />
            <button
              type="button"
              onClick={() => undefined}
              style={{
                boxSizing: 'border-box',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 8,
                width: '100%',
                minHeight: 44,
                padding: '16px 0 4px',
                background: 'transparent',
                border: 'none',
                borderTop: `1px solid ${color.paper.borderFaint}`,
                cursor: 'pointer',
                fontFamily: font.sans,
                fontSize: 14,
                fontWeight: 700,
                color: color.dawn.coralTextOnLight,
                textAlign: 'left',
              }}
            >
              Çıkış yap
              <LogoutIcon />
            </button>
          </div>
        </Kart>

        {/* (8) Dipnot */}
        <p style={{ margin: '2px 2px 0', fontSize: 11.5, color: color.ink.muted, textAlign: 'center' }}>
          KIRO2 · YKS Hazırlık · sürüm 0.9 (prototip)
        </p>
      </>
    );
  }

  return (
    <KiroThemeProvider theme="paper">
      <div
        className="k-paper"
        style={{
          boxSizing: 'border-box',
          minHeight: '100vh',
          background: color.paper.bg,
          display: 'flex',
          fontFamily: font.sans,
          color: color.ink.primary,
          fontSize: 14,
          lineHeight: 1.5,
        }}
      >
        <SideNav
          role="ogrenci"
          activeId="settings"
          showSettings
          collapsed={dar}
          userName={persona?.ad ?? 'Öğrenci'}
          userSub={persona?.sinif ?? ''}
          onAssistant={() => undefined}
        />

        <main style={{ flex: 1, minWidth: 0 }}>
          <header
            style={{
              boxSizing: 'border-box',
              position: 'sticky',
              top: 0,
              zIndex: 2,
              height: 66,
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '0 30px',
              background: 'rgba(250,247,242,0.86)',
              backdropFilter: 'blur(8px)',
              borderBottom: `1px solid ${color.paper.border}`,
            }}
          >
            <div style={{ fontSize: 18, fontWeight: 800, letterSpacing: '-0.02em' }}>Ayarlar &amp; Profil</div>
            <div style={{ flex: 1 }} />
            <div role="status" aria-live="polite">
              {saved ? (
                <span
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 6,
                    fontSize: 12.5,
                    fontWeight: 700,
                    color: color.semantic.successTextOnLight,
                    background: color.semantic.successBgSoft,
                    border: `1px solid ${color.semantic.successBorderSoft}`,
                    padding: '6px 12px',
                    borderRadius: 9,
                  }}
                >
                  <CheckIcon stroke={color.semantic.successTextOnLight} />
                  Kaydedildi
                </span>
              ) : null}
            </div>
          </header>

          <div
            style={{
              boxSizing: 'border-box',
              maxWidth: 900,
              width: '100%',
              padding: '24px 30px 60px',
              display: 'flex',
              flexDirection: 'column',
              gap: 20,
            }}
          >
            {icerik}
          </div>
        </main>
      </div>
    </KiroThemeProvider>
  );
}

function hedefBtnStyle(disabled: boolean): React.CSSProperties {
  return {
    boxSizing: 'border-box',
    width: 44,
    height: 44,
    borderRadius: 11,
    border: `1px solid ${color.paper.border}`,
    background: color.paper.card,
    color: color.ink.secondary,
    fontSize: 22,
    fontWeight: 700,
    lineHeight: 1,
    cursor: disabled ? 'default' : 'pointer',
    opacity: disabled ? 0.45 : 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  };
}

export default AyarlarPage;
