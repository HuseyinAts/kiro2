/**
 * KIRO2 Modern Color System
 * Professional, vibrant, and WCAG AA compliant
 * Inspired by modern educational platforms
 */

export const modernColors = {
  // ============================================
  // PRIMARY BRAND COLORS - Vibrant Blue/Purple
  // ============================================
  primary: {
    50: '#F0F4FF',
    100: '#E0EAFF',
    200: '#C7D7FE',
    300: '#A5BBFC',
    400: '#8B9FF9',
    500: '#667EEA',  // Main - Modern vibrant blue
    600: '#5568D3',
    700: '#4453B8',
    800: '#3A4199',
    900: '#2D3282',
  },

  // ============================================
  // SECONDARY COLORS - Purple/Magenta
  // ============================================
  secondary: {
    50: '#FAF5FF',
    100: '#F3E8FF',
    200: '#E9D5FF',
    300: '#D8B4FE',
    400: '#C084FC',
    500: '#A855F7',  // Main - Vibrant purple
    600: '#9333EA',
    700: '#7E22CE',
    800: '#6B21A8',
    900: '#581C87',
  },

  // ============================================
  // ACCENT COLORS - Modern palette
  // ============================================
  accent: {
    cyan: {
      main: '#06B6D4',
      light: '#22D3EE',
      dark: '#0891B2',
    },
    teal: {
      main: '#14B8A6',
      light: '#2DD4BF',
      dark: '#0D9488',
    },
    pink: {
      main: '#EC4899',
      light: '#F472B6',
      dark: '#DB2777',
    },
    orange: {
      main: '#F97316',
      light: '#FB923C',
      dark: '#EA580C',
    },
    emerald: {
      main: '#10B981',
      light: '#34D399',
      dark: '#059669',
    },
  },

  // ============================================
  // SEMANTIC COLORS - Success, Error, Warning, Info
  // ============================================
  success: {
    50: '#ECFDF5',
    100: '#D1FAE5',
    400: '#34D399',
    500: '#10B981',
    700: '#047857',
    900: '#064E3B',
    background: '#ECFDF5',
    contrastText: '#FFFFFF',
  },

  error: {
    50: '#FEF2F2',
    100: '#FEE2E2',
    400: '#F87171',
    500: '#EF4444',
    700: '#B91C1C',
    900: '#7F1D1D',
    background: '#FEF2F2',
    contrastText: '#FFFFFF',
  },

  warning: {
    50: '#FFFBEB',
    100: '#FEF3C7',
    400: '#FBBF24',
    500: '#F59E0B',
    700: '#B45309',
    900: '#78350F',
    background: '#FFFBEB',
    contrastText: '#000000',
  },

  info: {
    50: '#EFF6FF',
    100: '#DBEAFE',
    400: '#60A5FA',
    500: '#3B82F6',
    700: '#1D4ED8',
    900: '#1E3A8A',
    background: '#EFF6FF',
    contrastText: '#FFFFFF',
  },

  // ============================================
  // GRADIENT LIBRARY - Modern and vibrant
  // ============================================
  gradients: {
    // Primary gradients
    primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    primaryHover: 'linear-gradient(135deg, #5568d3 0%, #6b21a8 100%)',

    // Accent gradients
    sunset: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    ocean: 'linear-gradient(135deg, #2193b0 0%, #6dd5ed 100%)',
    forest: 'linear-gradient(135deg, #134e5e 0%, #71b280 100%)',
    fire: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    aurora: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',

    // Success/Error gradients
    success: 'linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)',
    error: 'linear-gradient(135deg, #fa709a 0%, #ff6b6b 100%)',
    warning: 'linear-gradient(135deg, #ffd89b 0%, #19547b 100%)',

    // Educational theme gradients
    learning: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    exam: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    achievement: 'linear-gradient(135deg, #ffd89b 0%, #f97316 100%)',

    // Subtle backgrounds
    lightBlue: 'linear-gradient(135deg, #e0eaff 0%, #f0f4ff 100%)',
    lightPurple: 'linear-gradient(135deg, #f3e8ff 0%, #faf5ff 100%)',
    lightGreen: 'linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%)',

    // Additional gradients for components
    mesh: 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)',
    purple: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    violet: 'linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)',
    indigo: 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)',
  },

  // ============================================
  // GLASSMORPHISM - Modern frosted glass effect
  // ============================================
  glass: {
    white: {
      light: 'rgba(255, 255, 255, 0.9)',
      medium: 'rgba(255, 255, 255, 0.7)',
      dark: 'rgba(255, 255, 255, 0.5)',
      subtle: 'rgba(255, 255, 255, 0.3)',
    },
    black: {
      light: 'rgba(0, 0, 0, 0.1)',
      medium: 'rgba(0, 0, 0, 0.2)',
      dark: 'rgba(0, 0, 0, 0.3)',
      subtle: 'rgba(0, 0, 0, 0.05)',
    },
    primary: {
      light: 'rgba(102, 126, 234, 0.1)',
      medium: 'rgba(102, 126, 234, 0.2)',
      dark: 'rgba(102, 126, 234, 0.3)',
    },
    border: 'rgba(255, 255, 255, 0.2)',
  },

  // ============================================
  // TEXT COLORS - WCAG AA compliant
  // ============================================
  text: {
    primary: '#1F2937',      // Gray 800
    secondary: '#6B7280',    // Gray 500
    disabled: '#9CA3AF',     // Gray 400
    hint: '#D1D5DB',         // Gray 300
    white: '#FFFFFF',
    dark: '#111827',         // Gray 900
  },

  // ============================================
  // BACKGROUND COLORS
  // ============================================
  background: {
    default: '#F9FAFB',      // Gray 50
    paper: '#FFFFFF',
    elevated: '#FFFFFF',
    dark: '#111827',         // Gray 900
    darkPaper: '#1F2937',    // Gray 800
    gradient: 'linear-gradient(180deg, #F9FAFB 0%, #F3F4F6 100%)',
  },

  // ============================================
  // BORDER & DIVIDER
  // ============================================
  border: {
    light: '#E5E7EB',        // Gray 200
    main: '#D1D5DB',         // Gray 300
    dark: '#9CA3AF',         // Gray 400
  },

  divider: {
    main: 'rgba(0, 0, 0, 0.12)',
    light: 'rgba(0, 0, 0, 0.06)',
    dark: 'rgba(255, 255, 255, 0.12)',
  },

  // ============================================
  // EXAM TYPE COLORS - Turkish Education System
  // ============================================
  exam: {
    tyt: {
      main: '#3B82F6',       // Blue
      light: '#DBEAFE',
      gradient: 'linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%)',
    },
    ayt: {
      main: '#10B981',       // Green
      light: '#D1FAE5',
      gradient: 'linear-gradient(135deg, #10B981 0%, #047857 100%)',
    },
    ydt: {
      main: '#EF4444',       // Red
      light: '#FEE2E2',
      gradient: 'linear-gradient(135deg, #EF4444 0%, #B91C1C 100%)',
    },
    lgs: {
      main: '#F59E0B',       // Orange
      light: '#FEF3C7',
      gradient: 'linear-gradient(135deg, #F59E0B 0%, #B45309 100%)',
    },
  },

  // ============================================
  // SUBJECT COLORS - Color-coded learning
  // ============================================
  subject: {
    matematik: {
      main: '#3B82F6',
      light: '#DBEAFE',
      gradient: 'linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%)',
    },
    fizik: {
      main: '#8B5CF6',
      light: '#EDE9FE',
      gradient: 'linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)',
    },
    kimya: {
      main: '#EF4444',
      light: '#FEE2E2',
      gradient: 'linear-gradient(135deg, #EF4444 0%, #B91C1C 100%)',
    },
    biyoloji: {
      main: '#10B981',
      light: '#D1FAE5',
      gradient: 'linear-gradient(135deg, #10B981 0%, #047857 100%)',
    },
    turkce: {
      main: '#F59E0B',
      light: '#FEF3C7',
      gradient: 'linear-gradient(135deg, #F59E0B 0%, #B45309 100%)',
    },
    tarih: {
      main: '#92400E',
      light: '#FEF3C7',
      gradient: 'linear-gradient(135deg, #92400E 0%, #78350F 100%)',
    },
    cografya: {
      main: '#06B6D4',
      light: '#CFFAFE',
      gradient: 'linear-gradient(135deg, #06B6D4 0%, #0891B2 100%)',
    },
    ingilizce: {
      main: '#EC4899',
      light: '#FCE7F3',
      gradient: 'linear-gradient(135deg, #EC4899 0%, #DB2777 100%)',
    },
  },

  // ============================================
  // CHART COLORS - Data visualization
  // ============================================
  chart: {
    series: [
      '#667EEA', // Primary
      '#10B981', // Success
      '#F59E0B', // Warning
      '#EF4444', // Error
      '#A855F7', // Purple
      '#06B6D4', // Cyan
      '#EC4899', // Pink
      '#F97316', // Orange
      '#14B8A6', // Teal
      '#8B5CF6', // Violet
    ],
  },

  // ============================================
  // SHADOW COLORS
  // ============================================
  shadow: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
    '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    glass: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
    modern: '0 10px 40px -10px rgba(0,0,0,0.2)',
    glow: '0 0 20px rgba(102, 126, 234, 0.4)',
    'glow-lg': '0 0 30px rgba(102, 126, 234, 0.6)',
  },
};

export type ModernColorPalette = typeof modernColors
export default modernColors;
