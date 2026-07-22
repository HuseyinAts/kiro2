import { font, radius, hit } from '../tokens';
import { useKiroTheme, surf } from './theme';

export interface InputProps {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  /** Görünür etiketi olmayan her alanda ZORUNLU (a11y §22c) */
  ariaLabel: string;
  width?: number | string;
  type?: string;
}

export function Input({ value, onChange, placeholder, ariaLabel, width = 160, type = 'text' }: InputProps) {
  const theme = useKiroTheme();
  const s = surf(theme);
  return (
    <input
      type={type}
      value={value}
      placeholder={placeholder}
      aria-label={ariaLabel}
      onChange={(e) => onChange(e.target.value)}
      style={{ width, height: hit.minTarget, padding: '0 13px',
        border: `1px solid ${s.border}`, borderRadius: radius.input, backgroundColor: s.card,
        fontFamily: font.sans, fontSize: 13, fontWeight: 600, color: s.text }}
    />
  );
}
