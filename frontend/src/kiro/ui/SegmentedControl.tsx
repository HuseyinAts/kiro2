import * as React from 'react';
import { color, font, radius, hit } from '../tokens';

export interface SegmentedOption<T extends string> {
  key: T;
  label: string;
  badge?: React.ReactNode;
}

export interface SegmentedControlProps<T extends string> {
  options: SegmentedOption<T>[];
  value: T;
  onChange: (key: T) => void;
  /** 'pill' = Abonelik fatura toggle'ı · 'scale' = anket 1-4 ölçeği */
  variant?: 'pill' | 'scale';
  /** scale varyantında satır bağlamı — aria-label için zorunlu */
  ariaContext?: string;
}

export function SegmentedControl<T extends string>({ options, value, onChange, variant = 'pill', ariaContext }: SegmentedControlProps<T>) {
  if (variant === 'scale') {
    return (
      <div style={{ display: 'flex', gap: 6 }} role="radiogroup" aria-label={ariaContext}>
        {options.map((o) => {
          const on = o.key === value;
          return (
            <button key={o.key} type="button" role="radio" aria-checked={on}
              aria-label={ariaContext ? `${ariaContext} — ${o.label}` : o.label}
              onClick={() => onChange(o.key)}
              style={{ minHeight: hit.minTarget, padding: '0 15px', borderRadius: radius.input,
                fontFamily: font.sans, fontSize: 13, fontWeight: 700, cursor: 'pointer',
                backgroundColor: on ? color.ink.primary : '#fff',
                color: on ? '#FFF6EC' : color.ink.secondary,
                border: `1px solid ${on ? color.ink.primary : color.paper.border}` }}>
              {o.label}
            </button>
          );
        })}
      </div>
    );
  }
  return (
    <div style={{ display: 'inline-flex', padding: 4, borderRadius: 12, backgroundColor: color.paper.borderFaint, gap: 3 }} role="radiogroup" aria-label={ariaContext}>
      {options.map((o) => {
        const on = o.key === value;
        return (
          <button key={o.key} type="button" role="radio" aria-checked={on} onClick={() => onChange(o.key)}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 4, minHeight: hit.minTarget, padding: '0 16px', borderRadius: 9,
              fontFamily: font.sans, fontSize: 13, fontWeight: 700, cursor: 'pointer', border: 'none',
              backgroundColor: on ? '#fff' : 'transparent',
              color: on ? color.ink.primary : color.ink.muted,
              boxShadow: on ? '0 1px 3px rgba(0,0,0,0.08)' : undefined }}>
            {o.label}{o.badge}
          </button>
        );
      })}
    </div>
  );
}
