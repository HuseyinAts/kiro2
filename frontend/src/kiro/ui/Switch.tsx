import * as React from 'react';
import { color, font, hit, motion } from '../tokens';
import { useReducedMotion } from './ConfettiDawn';

// ============================================================================
// KIRO2 — Switch (aç/kapa) · SPRINT10-C
// Ayarlar ekranı bildirim/sakin-mod/gizle-sıralama anahtarları için.
// KANON: açık (paper) yüzey; AÇIK track = coralCtaBg #C2452B (beyaz thumb 5:1);
//   KAPALI track = nötr kâğıt grisi + görünür nötr sınır (#8F8577 beyaz kartta
//   3.63:1 → WCAG 1.4.11 ≥3:1). #FF6F5C dolgu YASAK. Hareket yalnız
//   transform + renk (layout-anim yok), prefers-reduced-motion'da kapalı.
// ============================================================================

export interface SwitchProps {
  checked: boolean;
  onChange: (v: boolean) => void;
  /** Görünür etiket — verilirse erişilebilir ad içerikten türetilir. */
  label?: string;
  /** label yoksa erişilebilir ad (ikon-yalnız/görünmez etiket) için zorunlu. */
  ariaLabel?: string;
  /** İlişkili açıklama metninin id'si — verilirse aria-describedby olarak iletilir. */
  ariaDescribedby?: string;
  disabled?: boolean;
  id?: string;
}

const TRACK_W = 46;
const TRACK_H = 28;
const THUMB = 22;
const BORDER = 1.5;
// Sınır (1.5) + iç boşluk (1.5) = 3px → thumb'ın orijinal yerleşimi korunur.
const PAD = 1.5;
const OFFSET = TRACK_W - THUMB - (PAD + BORDER) * 2; // 18px — sınır eklenince değişmez

// KAPALI track dolgusu beyaz kartta 1.44:1; WCAG 1.4.11'i (≥3:1) tek başına
// karşılamaz → görünür nötr sınır. #8F8577 beyaza karşı 3.63:1.
const TRACK_OFF_BG = '#DDD6CC';
const TRACK_OFF_BORDER = '#8F8577';
// :focus-visible odak halkası tokens.css'e taşındı (.kiro-switch:focus-visible) —
// her örnekte ayrı <style> enjekte etme (8 kopya) yerine tek CSS kuralı.

export function Switch({ checked, onChange, label, ariaLabel, ariaDescribedby, disabled, id }: SwitchProps) {
  const reduced = useReducedMotion();

  const toggle = () => {
    if (!disabled) onChange(!checked);
  };
  const onKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return;
    if (e.key === ' ' || e.key === 'Enter' || e.key === 'Spacebar') {
      e.preventDefault();
      onChange(!checked);
    }
  };

  const rootStyle: React.CSSProperties = {
    boxSizing: 'border-box',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: label ? 'flex-start' : 'center',
    gap: label ? 12 : 0,
    minHeight: hit.minTarget,
    minWidth: label ? undefined : hit.minTarget,
    cursor: disabled ? 'default' : 'pointer',
    opacity: disabled ? 0.45 : 1,
    userSelect: 'none',
  };

  const trackStyle: React.CSSProperties = {
    boxSizing: 'border-box',
    position: 'relative',
    flex: '0 0 auto',
    display: 'inline-flex',
    alignItems: 'center',
    width: TRACK_W,
    height: TRACK_H,
    padding: PAD,
    borderRadius: 999,
    backgroundColor: checked ? color.dawn.coralCtaBg : TRACK_OFF_BG,
    // AÇIK: coralCtaBg beyaza 5:1 → sınır dolguyla aynı (görünmez dikiş).
    // KAPALI: nötr sınır beyaz kartta ≥3:1 (WCAG 1.4.11). box-sizing border-box korunur.
    border: `${BORDER}px solid ${checked ? color.dawn.coralCtaBg : TRACK_OFF_BORDER}`,
    transition: reduced
      ? undefined
      : `background-color ${motion.base}ms ${motion.easing}, border-color ${motion.base}ms ${motion.easing}`,
  };

  const thumbStyle: React.CSSProperties = {
    boxSizing: 'border-box',
    width: THUMB,
    height: THUMB,
    borderRadius: 999,
    backgroundColor: '#FFFFFF',
    boxShadow: '0 1px 2px rgba(16,24,40,0.24)',
    transform: `translateX(${checked ? OFFSET : 0}px)`,
    transition: reduced ? undefined : `transform ${motion.base}ms ${motion.easing}`,
  };

  return (
    <span
      role="switch"
      aria-checked={checked}
      aria-label={label ? undefined : ariaLabel}
      aria-describedby={ariaDescribedby}
      aria-disabled={disabled || undefined}
      id={id}
      className="kiro-switch"
      tabIndex={disabled ? -1 : 0}
      onClick={toggle}
      onKeyDown={onKeyDown}
      style={rootStyle}
    >
      {label ? (
        <span
          style={{
            fontFamily: font.sans,
            fontSize: 14,
            fontWeight: 600,
            color: color.ink.secondary,
          }}
        >
          {label}
        </span>
      ) : null}
      <span aria-hidden style={trackStyle}>
        <span style={thumbStyle} />
      </span>
    </span>
  );
}
