import { color, font, radius } from '../tokens';
import { useKiroTheme, surf, serifText } from './theme';
import { Button } from './Button';

/**
 * Sakin hata (KIRO Durumlar §3) — AMBER çerçeve, kırmızı/hata kodu/jargon YASAK.
 * Kopya formülü zorunlu: ne oldu · "sorun sende değil" · "çalışman güvende" · tek kurtarma eylemi.
 */
export interface ErrorStateProps {
  serifTitle?: string;
  body?: string;
  onRetry?: () => void;
  retryLabel?: string;
}

export function ErrorState({
  serifTitle = 'Veri şu an yüklenemedi.',
  body = 'Sorun sende değil. Çalışman ve ilerlemen güvende — bağlantını kontrol edip yeniden deneyebilirsin.',
  onRetry,
  retryLabel = 'Tekrar dene',
}: ErrorStateProps) {
  const theme = useKiroTheme();
  const s = surf(theme);
  const border = theme === 'dusk' ? 'rgba(255,197,155,0.3)' : color.semantic.riskBorderSoft;
  return (
    <div style={{ border: `1px solid ${border}`, backgroundColor: s.card, borderRadius: radius.cardLg,
      padding: '36px 26px', display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: 10 }}>
      <div style={{ ...serifText, fontSize: 21, color: s.text, lineHeight: 1.25 }}>{serifTitle}</div>
      <p style={{ margin: 0, fontFamily: font.sans, fontSize: 13, color: s.muted, maxWidth: 360, lineHeight: 1.6 }}>{body}</p>
      {onRetry ? (
        <div style={{ marginTop: 6 }}>
          <Button variant="ghost" onClick={onRetry}>{retryLabel}</Button>
        </div>
      ) : null}
    </div>
  );
}
