/**
 * KIRO2 Modern Typography System
 * Professional font stack with hierarchy and readability
 */

import { TypographyOptions } from '@mui/material/styles/createTypography';

/**
 * Font Stack
 * - Inter: Primary font for UI elements (modern, clean, highly readable)
 * - Poppins: Display font for headings (friendly, approachable)
 * - Roboto: Fallback for compatibility
 */
export const fontFamilies = {
  primary: [
    'Inter',
    '-apple-system',
    'BlinkMacSystemFont',
    '"Segoe UI"',
    'Roboto',
    'sans-serif',
  ].join(','),

  display: [
    'Poppins',
    'Inter',
    '-apple-system',
    'BlinkMacSystemFont',
    '"Segoe UI"',
    'sans-serif',
  ].join(','),

  mono: [
    '"Fira Code"',
    '"Courier New"',
    'Courier',
    'monospace',
  ].join(','),
};

/**
 * Modern Typography Configuration
 * WCAG AA compliant with enhanced visual hierarchy
 */
export const modernTypography: TypographyOptions = {
  fontFamily: fontFamilies.primary,

  // ============================================
  // DISPLAY HEADINGS - Hero sections, landing pages
  // ============================================
  h1: {
    fontFamily: fontFamilies.display,
    fontSize: '3.5rem',      // 56px
    fontWeight: 800,
    lineHeight: 1.15,
    letterSpacing: '-0.02em',
    '@media (max-width:600px)': {
      fontSize: '2.5rem',    // 40px on mobile
    },
  },

  h2: {
    fontFamily: fontFamilies.display,
    fontSize: '2.75rem',     // 44px
    fontWeight: 700,
    lineHeight: 1.2,
    letterSpacing: '-0.015em',
    '@media (max-width:600px)': {
      fontSize: '2rem',      // 32px on mobile
    },
  },

  h3: {
    fontFamily: fontFamilies.display,
    fontSize: '2.25rem',     // 36px
    fontWeight: 700,
    lineHeight: 1.25,
    letterSpacing: '-0.01em',
    '@media (max-width:600px)': {
      fontSize: '1.75rem',   // 28px on mobile
    },
  },

  // ============================================
  // SECTION HEADINGS - Page sections, cards
  // ============================================
  h4: {
    fontFamily: fontFamilies.display,
    fontSize: '1.875rem',    // 30px
    fontWeight: 600,
    lineHeight: 1.3,
    letterSpacing: '-0.005em',
    '@media (max-width:600px)': {
      fontSize: '1.5rem',    // 24px on mobile
    },
  },

  h5: {
    fontFamily: fontFamilies.display,
    fontSize: '1.5rem',      // 24px
    fontWeight: 600,
    lineHeight: 1.35,
    letterSpacing: '0em',
    '@media (max-width:600px)': {
      fontSize: '1.25rem',   // 20px on mobile
    },
  },

  h6: {
    fontFamily: fontFamilies.display,
    fontSize: '1.25rem',     // 20px
    fontWeight: 600,
    lineHeight: 1.4,
    letterSpacing: '0.0025em',
    '@media (max-width:600px)': {
      fontSize: '1.125rem',  // 18px on mobile
    },
  },

  // ============================================
  // BODY TEXT - Main content
  // ============================================
  body1: {
    fontFamily: fontFamilies.primary,
    fontSize: '1rem',        // 16px (base size)
    fontWeight: 400,
    lineHeight: 1.6,         // Improved readability
    letterSpacing: '0.00938em',
  },

  body2: {
    fontFamily: fontFamilies.primary,
    fontSize: '0.875rem',    // 14px
    fontWeight: 400,
    lineHeight: 1.57,
    letterSpacing: '0.01071em',
  },

  // ============================================
  // BUTTON TEXT
  // ============================================
  button: {
    fontFamily: fontFamilies.primary,
    fontSize: '0.9375rem',   // 15px
    fontWeight: 600,
    lineHeight: 1.6,
    letterSpacing: '0.02em',
    textTransform: 'none' as const,  // Keep original case
  },

  // ============================================
  // CAPTIONS & OVERLINES
  // ============================================
  caption: {
    fontFamily: fontFamilies.primary,
    fontSize: '0.75rem',     // 12px
    fontWeight: 400,
    lineHeight: 1.66,
    letterSpacing: '0.03333em',
  },

  overline: {
    fontFamily: fontFamilies.primary,
    fontSize: '0.75rem',     // 12px
    fontWeight: 700,
    lineHeight: 2.66,
    letterSpacing: '0.08333em',
    textTransform: 'uppercase' as const,
  },

  // ============================================
  // SUBTITLE
  // ============================================
  subtitle1: {
    fontFamily: fontFamilies.primary,
    fontSize: '1rem',        // 16px
    fontWeight: 500,
    lineHeight: 1.75,
    letterSpacing: '0.00938em',
  },

  subtitle2: {
    fontFamily: fontFamilies.primary,
    fontSize: '0.875rem',    // 14px
    fontWeight: 600,
    lineHeight: 1.57,
    letterSpacing: '0.00714em',
  },
};

/**
 * Font Weight Tokens
 */
export const fontWeights = {
  light: 300,
  regular: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
  extrabold: 800,
  black: 900,
};

/**
 * Line Height Tokens
 */
export const lineHeights = {
  none: 1,
  tight: 1.25,
  snug: 1.375,
  normal: 1.5,
  relaxed: 1.6,
  loose: 2,
};

/**
 * Letter Spacing Tokens
 */
export const letterSpacings = {
  tighter: '-0.05em',
  tight: '-0.025em',
  normal: '0em',
  wide: '0.025em',
  wider: '0.05em',
  widest: '0.1em',
};

/**
 * Font Size Scale (in rem)
 */
export const fontSizes = {
  xs: '0.75rem',      // 12px
  sm: '0.875rem',     // 14px
  base: '1rem',       // 16px
  lg: '1.125rem',     // 18px
  xl: '1.25rem',      // 20px
  '2xl': '1.5rem',    // 24px
  '3xl': '1.875rem',  // 30px
  '4xl': '2.25rem',   // 36px
  '5xl': '3rem',      // 48px
  '6xl': '3.75rem',   // 60px
  '7xl': '4.5rem',    // 72px
  '8xl': '6rem',      // 96px
  '9xl': '8rem',      // 128px
};

/**
 * Responsive Font Sizes Helper
 */
export const responsiveFontSizes = {
  display: {
    mobile: '2.5rem',   // 40px
    tablet: '3rem',     // 48px
    desktop: '3.5rem',  // 56px
  },
  heading: {
    mobile: '1.75rem',  // 28px
    tablet: '2rem',     // 32px
    desktop: '2.25rem', // 36px
  },
  subheading: {
    mobile: '1.25rem',  // 20px
    tablet: '1.375rem', // 22px
    desktop: '1.5rem',  // 24px
  },
  body: {
    mobile: '0.875rem', // 14px
    tablet: '1rem',     // 16px
    desktop: '1rem',    // 16px
  },
};

/**
 * Typography Utility Classes
 */
export const typographyClasses = {
  gradient: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
  },
  truncate: {
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap' as const,
  },
  lineClamp: (lines: number) => ({
    display: '-webkit-box',
    WebkitLineClamp: lines,
    WebkitBoxOrient: 'vertical' as const,
    overflow: 'hidden',
  }),
  balance: {
    textWrap: 'balance' as const,
  },
  pretty: {
    textWrap: 'pretty' as const,
  },
};

export default modernTypography;
