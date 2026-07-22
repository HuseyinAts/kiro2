// ============================================================================
// KIRO2 — Tasarım Token'ları (platformdan bağımsız TypeScript)
// Kaynak: KIRO2 Tasarim Sistemi.dc.html + handoff README "Design System" bölümü.
// Web (React/Next) ve React Native ikisinde de bu dosya TEK kaynaktır;
// web'de tokens.css bu değerlerin CSS-değişkeni yansımasıdır.
//
// KANON KURALLARI (koddan bağımsız, ihlal etme):
// - Ekran ruhu temayı belirler: çalışma/odak/analitik = AÇIK (paper),
//   duygusal/hub/kutlama/ritüel = KOYU (dusk). Kullanıcı toggle'ı DEĞİL.
// - Risk = amber; ASLA alarm-kırmızısı. İndigo/lacivert YASAK (mor yalnız Fizik).
// - Emoji yok; ikonlar bespoke inline SVG (stroke 1.8-2.2, round cap/join).
// - Tüm sayılar Hanken Grotesk + tabular-nums.
// ============================================================================

export const color = {
  /** AÇIK yüzeyler — çalışma/odak/analitik ekranlar */
  paper: {
    bg: '#F7F4EF',
    card: '#FFFFFF',
    subtle: '#FBF8F3',
    subtle2: '#FBF7F1',
    border: '#ECE6DD',
    borderStrong: '#E2DACE',
    borderFaint: '#F0EAE1',
  },
  /** Mürekkep — açık zeminde metin */
  ink: {
    primary: '#2A2433',
    secondary: '#4A4456',
    /** Açık zeminde KÜÇÜK ikincil metin için AA minimumu (bkz. ACCESSIBILITY.md) */
    muted: '#6B6478',
    /** Yalnız dekoratif / koyu zeminde: açıkta küçük metin için KULLANMA */
    faded: '#8A8398',
    faded2: '#B0A9B8',
    faded3: '#B5AEA2',
  },
  /** KOYU yüzeyler — duygusal/hub/kutlama/ritüel ekranlar */
  dusk: {
    bg: '#110C18',
    bg2: '#150E20',
    bg3: '#170E22',
    bgBoss: '#120A14',
    text: '#F1E9F2',
    textWarm: '#FBEFE6',
    text2: '#ECE4F0',
    textSecondary: 'rgba(241,233,242,0.6)',
    /* Koyu-zemin ikincil metin tonları (SPRINT6 §7 kanonu — dusk'ta açık-zemin grisi YASAK) */
    ink2: '#B6A6C4', // ikincil (leylak-gri)
    iconMuted: '#9B8FB5', // ikon / soluk-ikincil
    faded: '#8C8398', // soluk
    body80: 'rgba(236,228,240,0.8)', // gövde (0.8 alfa)
  },
  /** Dawn aksanı — marka ipliği (her iki yüzeyde) */
  dawn: {
    coral: '#FF6F5C',
    coral2: '#FF8A5B',
    peach: '#FFAE86',
    peach2: '#FFC59B',
    gold: '#FFD98C',
    gold2: '#FCD34D',
    /** Açık zeminde CORAL METİN için AA karşılığı (dolgu değil) */
    coralTextOnLight: '#C2452B',
    /** Beyaz metin taşıyan coral CTA/balon zemini — AA-güvenli derin coral (beyaz metin 5:1) */
    coralCtaBg: '#C2452B',
  },
  /** Semantik */
  semantic: {
    /** Risk/zayıf: dolgu-grafik amber'i */
    risk: '#C77A1E',
    /** Risk/zayıf: açık zeminde METİN amber'i (sıkı-AA) */
    riskTextOnLight: '#9A5D0D',
    riskBgSoft: '#FBF0DE',
    riskBorderSoft: '#F2D9AC',
    success: '#1FB683',
    success2: '#34D399',
    successTextOnLight: '#047857',
    successBgSoft: '#ECFDF5',
    successBorderSoft: '#BBF7D0',
  },
  /** Hâkimiyet kademeleri (masteryTier ile birebir) */
  mastery: {
    tanidik: '#9A93A5',
    yetkin: '#7FB0FF',
    usta: '#FFAE86',
    fethedildi: '#FCD34D',
  },
  /**
   * Ders renkleri — İKİ palet: koyu zeminde parlak (kiro-data `subjects[].renk`),
   * açık panellerde doygun. Zemine göre doğru paleti seç.
   */
  subject: {
    dark: { mat: '#5B8DEF', fiz: '#A77BFF', kim: '#E25A72', biy: '#2DD4A7', tur: '#FFB347' },
    light: { mat: '#3B82F6', fiz: '#8B5CF6', kim: '#E0593F', biy: '#1FB683', tur: '#F59E0B' },
    /** Alan-üstü katalog (EA/Sözel dersleri — dersKatalog ile birebir) */
    katalog: { edb: '#D97706', tar: '#B45309', cog: '#0D9488', fel: '#7C3AED', din: '#6B7280' },
  },
  /** Şafak göğü gradyanları (kanon stringleri — koyu hero zeminleri) */
  gradient: {
    dawnSkyLinear:
      'linear-gradient(176deg, #141029 0%, #241640 17%, #3E1F4E 33%, #6A2B52 51%, #A33C4E 66%, #D35F49 80%, #F2974C 92%, #FFC76F 100%)',
    dawnUnderglowRadial:
      'radial-gradient(130% 100% at 50% 118%, #FFB57E, #FF8A5B, #C24E7E, #5B2F66, #1A0F26)',
  },
} as const;

export const font = {
  /** His / mantra / duygusal başlık (italik sık) */
  serif: "'Instrument Serif', Georgia, serif",
  /** İşlev + TÜM sayılar (font-variant-numeric: tabular-nums) */
  sans: "'Hanken Grotesk', -apple-system, sans-serif",
  /** Kod / API dokümanı */
  mono: "'IBM Plex Mono', ui-monospace, monospace",
} as const;

export const typeScale = {
  h1: { size: 38, weight: 800, lineHeight: 1.1 },
  h2: { size: 24, weight: 800, lineHeight: 1.15 },
  h3: { size: 17, weight: 700, lineHeight: 1.25 },
  body: { size: 14, weight: 500, lineHeight: 1.5 },
  bodyLg: { size: 15.5, weight: 500, lineHeight: 1.6 },
  small: { size: 12.5, weight: 600, lineHeight: 1.45 },
  micro: { size: 11, weight: 700, lineHeight: 1.35 },
  /** Büyük sayı hero'ları clamp(96px → 176px) aralığında */
  heroNum: { min: 96, max: 176, weight: 800, lineHeight: 0.9 },
} as const;

export const radius = {
  chip: 10,
  input: 11,
  button: 13,
  card: 16,
  cardLg: 20,
  pill: 999,
} as const;

/** 4'lük ritim — gap/padding bu ölçekten */
export const space = [0, 4, 8, 12, 16, 20, 24, 32, 44] as const;

export const shadow = {
  cardSoft: '0 1px 2px rgba(16,24,40,0.04)',
  cardFloat: '0 20px 50px -24px rgba(42,36,51,0.3)',
  screenshotFloat: '0 44px 100px -46px rgba(42,36,51,0.5)',
  coralCta: '0 10px 22px -10px rgba(255,111,92,0.7)',
  dawnGlow: '0 8px 22px -6px rgba(255,111,92,0.7)',
} as const;

export const motion = {
  /** Kaygı-duyarlı: sakin, yavaş, agresif değil. Girişler transform-only. */
  fast: 120,
  base: 150,
  page: 220,
  pageIn: 300,
  easing: 'cubic-bezier(0.33, 0, 0.2, 1)',
  /** Her animasyon prefers-reduced-motion'a saygı duymak ZORUNDA */
} as const;

export const hit = {
  /** Mobil dokunma hedefi minimumu (px) */
  minTarget: 44,
} as const;

const tokens = { color, font, typeScale, radius, space, shadow, motion, hit };
export default tokens;
