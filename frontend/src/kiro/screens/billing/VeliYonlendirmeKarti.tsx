// ============================================================================
// KIRO2 — Veli Yönlendirme Kartı (SPRINT10-B · Grup 8 billing infra · PAYLAŞILAN)
// Abonelik + Plan Yönetimi ekranları, rol=ogrenci bağlamında fiyat/plan-grid/ödeme
// GÖSTERMEZ → bu kartı render eder (ÖĞRENCİ FİYAT GİZLİ · KVKK). Satın-alma/kart/
// iptal yalnız veli hesabından. Tek yer → iki ekran birebir tutarlı.
//
// KANON: Tema = PAPER; CTA = coralCtaBg #C2452B + beyaz; serif italik başlık;
// gövde ink.muted (AA); bespoke SVG (emoji/stok-ikon YOK); box-sizing:border-box
// (KÖK dahil); hit-target ≥44px. FİYAT/PLAN GÖSTERME. Öğrenci dili = SEN (kaygı azalt).
// Hareket YOK → reduced-motion guard'ı gerekmez (animation/transition yok).
// ============================================================================
import { color, font, radius, shadow } from '../../tokens';

export interface VeliYonlendirmeKartiProps {
  /** Hangi ekrandan çağrıldı — gövde metnini nüanslar (varsayılan 'abonelik'). */
  baglam?: 'abonelik' | 'yonetim';
}

/** Bespoke kalkan + onay ikonu (stroke; emoji/stok-ikon YOK) — güven/koruma tonu. */
function KalkanIkon() {
  return (
    <svg
      width="26"
      height="26"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
      stroke={color.dawn.coralTextOnLight}
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 3l7 3v5c0 4.4-3 7.6-7 9-4-1.4-7-4.6-7-9V6l7-3z" />
      <path d="M9.2 11.8l2 2 3.6-3.8" />
    </svg>
  );
}

export function VeliYonlendirmeKarti({ baglam = 'abonelik' }: VeliYonlendirmeKartiProps) {
  const govde =
    baglam === 'yonetim'
      ? 'Plan ve ödeme ayarların veli hesabından yönetilir — güvenli ve KVKK uyumlu. Sen çalışmaya odaklan; gerisini velin halleder.'
      : 'Ödeme ve plan işlemleri veli hesabından yapılır — güvenli ve KVKK uyumlu. Sen çalışmaya odaklan.';

  return (
    <section
      style={{
        boxSizing: 'border-box',
        maxWidth: 460,
        margin: '0 auto',
        padding: 24,
        backgroundColor: color.paper.card,
        border: `1px solid ${color.paper.border}`,
        borderRadius: radius.cardLg,
        boxShadow: shadow.cardSoft,
        fontFamily: font.sans,
        textAlign: 'center',
      }}
    >
      <div
        aria-hidden="true"
        style={{
          boxSizing: 'border-box',
          width: 52,
          height: 52,
          margin: '0 auto 14px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: radius.pill,
          backgroundColor: '#FDECE7', // coral tint (dekoratif; alarm-kırmızısı DEĞİL)
        }}
      >
        <KalkanIkon />
      </div>

      <h2
        style={{
          margin: 0,
          fontFamily: font.serif,
          fontStyle: 'italic',
          fontSize: 24,
          fontWeight: 400,
          color: color.ink.primary,
          lineHeight: 1.2,
        }}
      >
        Aboneliğini velin yönetir
      </h2>

      <p
        style={{
          boxSizing: 'border-box',
          margin: '10px auto 20px',
          maxWidth: 360,
          fontSize: 14.5,
          lineHeight: 1.6,
          color: color.ink.muted,
        }}
      >
        {govde}
      </p>

      <a
        href="/veli"
        style={{
          boxSizing: 'border-box',
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: 44,
          padding: '0 22px',
          backgroundColor: color.dawn.coralCtaBg,
          color: '#fff',
          fontFamily: font.sans,
          fontSize: 14.5,
          fontWeight: 800,
          borderRadius: radius.button,
          textDecoration: 'none',
        }}
      >
        Veli hesabına git
      </a>
    </section>
  );
}

export default VeliYonlendirmeKarti;
