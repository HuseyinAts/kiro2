/**
 * Accessibility Utilities
 * Color contrast calculation and WCAG compliance helpers
 */

/**
 * Convert hex color to RGB values
 */
export const hexToRgb = (hex: string): { r: number; g: number; b: number } | null => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : null;
};

/**
 * Calculate relative luminance of a color
 * Formula from WCAG 2.1: https://www.w3.org/TR/WCAG21/#dfn-relative-luminance
 */
export const getLuminance = (hex: string): number => {
  const rgb = hexToRgb(hex);
  if (!rgb) {return 0;}

  const { r, g, b } = rgb;

  // Convert RGB to sRGB
  const rsRGB = r / 255;
  const gsRGB = g / 255;
  const bsRGB = b / 255;

  // Apply gamma correction
  const rLinear = rsRGB <= 0.03928 ? rsRGB / 12.92 : Math.pow((rsRGB + 0.055) / 1.055, 2.4);
  const gLinear = gsRGB <= 0.03928 ? gsRGB / 12.92 : Math.pow((gsRGB + 0.055) / 1.055, 2.4);
  const bLinear = bsRGB <= 0.03928 ? bsRGB / 12.92 : Math.pow((bsRGB + 0.055) / 1.055, 2.4);

  // Calculate luminance
  return 0.2126 * rLinear + 0.7152 * gLinear + 0.0722 * bLinear;
};

/**
 * Calculate contrast ratio between two colors
 * Formula from WCAG 2.1: https://www.w3.org/TR/WCAG21/#dfn-contrast-ratio
 * @returns Contrast ratio (1:1 to 21:1)
 */
export const getContrastRatio = (foreground: string, background: string): number => {
  const l1 = getLuminance(foreground);
  const l2 = getLuminance(background);

  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);

  return (lighter + 0.05) / (darker + 0.05);
};

/**
 * WCAG Contrast Level constants
 * Note: AAA_LARGE and AA both require 4.5:1 ratio per WCAG spec
 */
export const WCAGLevel = {
  AAA_LARGE: 4.5,  // AAA for large text (18pt+)
  AA: 4.5,         // AA standard (normal text)
  AA_LARGE: 3,     // AA for large text (18pt+ or 14pt+ bold)
  AAA: 7,          // AAA standard (normal text)
} as const;

export type WCAGLevel = (typeof WCAGLevel)[keyof typeof WCAGLevel];

/**
 * Check if color combination meets WCAG contrast requirements
 */
export const meetsContrastRequirement = (
  foreground: string,
  background: string,
  level: WCAGLevel = WCAGLevel.AA,
): boolean => {
  const ratio = getContrastRatio(foreground, background);
  return ratio >= level;
};

/**
 * Get WCAG compliance level for a color combination
 */
export const getWCAGLevel = (
  foreground: string,
  background: string,
): { level: string; ratio: number; passes: { aa: boolean; aaLarge: boolean; aaa: boolean; aaaLarge: boolean } } => {
  const ratio = getContrastRatio(foreground, background);

  return {
    level: ratio >= WCAGLevel.AAA
      ? 'AAA'
      : ratio >= WCAGLevel.AA
      ? 'AA'
      : ratio >= WCAGLevel.AA_LARGE
      ? 'AA (Large Text)'
      : 'Fail',
    ratio: Math.round(ratio * 100) / 100,
    passes: {
      aa: ratio >= WCAGLevel.AA,
      aaLarge: ratio >= WCAGLevel.AA_LARGE,
      aaa: ratio >= WCAGLevel.AAA,
      aaaLarge: ratio >= WCAGLevel.AAA_LARGE,
    },
  };
};

/**
 * Get appropriate text color (black or white) for a background color
 * Ensures WCAG AA compliance
 */
export const getContrastText = (backgroundColor: string): '#000000' | '#FFFFFF' => {
  const whiteContrast = getContrastRatio('#FFFFFF', backgroundColor);
  const blackContrast = getContrastRatio('#000000', backgroundColor);

  // Return color with better contrast
  return whiteContrast > blackContrast ? '#FFFFFF' : '#000000';
};

/**
 * Darken a hex color by a percentage
 */
export const darkenColor = (hex: string, percent: number): string => {
  const rgb = hexToRgb(hex);
  if (!rgb) {return hex;}

  const factor = 1 - percent / 100;
  const r = Math.round(rgb.r * factor);
  const g = Math.round(rgb.g * factor);
  const b = Math.round(rgb.b * factor);

  return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
};

/**
 * Lighten a hex color by a percentage
 */
export const lightenColor = (hex: string, percent: number): string => {
  const rgb = hexToRgb(hex);
  if (!rgb) {return hex;}

  const factor = percent / 100;
  const r = Math.round(rgb.r + (255 - rgb.r) * factor);
  const g = Math.round(rgb.g + (255 - rgb.g) * factor);
  const b = Math.round(rgb.b + (255 - rgb.b) * factor);

  return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
};

/**
 * Create alpha transparency for a hex color
 */
export const withAlpha = (hex: string, alpha: number): string => {
  const rgb = hexToRgb(hex);
  if (!rgb) {return hex;}

  const a = Math.round(alpha * 255);
  return `#${((1 << 24) + (rgb.r << 16) + (rgb.g << 8) + rgb.b).toString(16).slice(1)}${a.toString(16).padStart(2, '0')}`;
};

/**
 * Convert hex color to rgba() string
 */
export const hexToRgba = (hex: string, alpha: number = 1): string => {
  const rgb = hexToRgb(hex);
  if (!rgb) {return `rgba(0, 0, 0, ${alpha})`;}

  return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`;
};

/**
 * Accessibility Helper: Focus Ring
 * WCAG 2.1 requires visible focus indicators
 */
export const getFocusRing = (color: string = '#1976D2', width: string = '2px'): string => {
  return `0 0 0 ${width} ${hexToRgba(color, 0.4)}`;
};

/**
 * Accessibility Helper: Ensure minimum touch target size
 * WCAG 2.1 requires 44x44px minimum for touch targets
 */
export const ensureTouchTarget = (size: number = 44): { minWidth: string; minHeight: string } => {
  return {
    minWidth: `${size}px`,
    minHeight: `${size}px`,
  };
};

/**
 * Accessibility Helper: Skip Link Styles
 * For keyboard-only navigation
 */
export const getSkipLinkStyles = () => ({
  position: 'absolute' as const,
  left: '-9999px',
  top: 'auto',
  width: '1px',
  height: '1px',
  overflow: 'hidden',
  '&:focus': {
    position: 'static' as const,
    width: 'auto',
    height: 'auto',
    overflow: 'visible',
    padding: '8px 16px',
    backgroundColor: '#1976D2',
    color: '#FFFFFF',
    textDecoration: 'none',
    borderRadius: '4px',
    zIndex: 9999,
  },
});

/**
 * Accessibility Helper: Screen Reader Only Text
 */
export const getScreenReaderOnlyStyles = () => ({
  position: 'absolute' as const,
  left: '-10000px',
  top: 'auto',
  width: '1px',
  height: '1px',
  overflow: 'hidden',
  clip: 'rect(0, 0, 0, 0)',
  whiteSpace: 'nowrap' as const,
});

/**
 * Accessibility Helper: High Contrast Mode Detection
 */
export const isHighContrastMode = (): boolean => {
  if (typeof window === 'undefined') {return false;}

  // Check for Windows high contrast mode
  const match = window.matchMedia('(prefers-contrast: high)');
  return match.matches;
};

/**
 * Accessibility Helper: Reduced Motion Detection
 */
export const prefersReducedMotion = (): boolean => {
  if (typeof window === 'undefined') {return false;}

  const match = window.matchMedia('(prefers-reduced-motion: reduce)');
  return match.matches;
};

/**
 * Accessibility Helper: Color Scheme Preference
 */
export const getColorSchemePreference = (): 'light' | 'dark' | 'no-preference' => {
  if (typeof window === 'undefined') {return 'no-preference';}

  if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }
  if (window.matchMedia('(prefers-color-scheme: light)').matches) {
    return 'light';
  }
  return 'no-preference';
};

/**
 * Accessibility Helper: Get Safe Color Pair
 * Returns a foreground/background pair that meets WCAG AA
 */
export const getSafeColorPair = (
  foreground: string,
  background: string,
  level: WCAGLevel = WCAGLevel.AA,
): { foreground: string; background: string; meetsRequirement: boolean } => {
  const meets = meetsContrastRequirement(foreground, background, level);

  if (meets) {
    return { foreground, background, meetsRequirement: true };
  }

  // Try adjusting foreground
  let adjustedForeground = foreground;
  let attempts = 0;
  while (!meetsContrastRequirement(adjustedForeground, background, level) && attempts < 10) {
    adjustedForeground = darkenColor(adjustedForeground, 10);
    attempts++;
  }

  if (meetsContrastRequirement(adjustedForeground, background, level)) {
    return { foreground: adjustedForeground, background, meetsRequirement: true };
  }

  // Fallback to black or white
  const safeColor = getContrastText(background);
  return { foreground: safeColor, background, meetsRequirement: true };
};

/**
 * Export all accessibility utilities
 */
export const a11y = {
  hexToRgb,
  getLuminance,
  getContrastRatio,
  meetsContrastRequirement,
  getWCAGLevel,
  getContrastText,
  darkenColor,
  lightenColor,
  withAlpha,
  hexToRgba,
  getFocusRing,
  ensureTouchTarget,
  getSkipLinkStyles,
  getScreenReaderOnlyStyles,
  isHighContrastMode,
  prefersReducedMotion,
  getColorSchemePreference,
  getSafeColorPair,
};

export default a11y;
