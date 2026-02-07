/**
 * KIRO2 Modern Theme Configuration
 * Complete design system with modern aesthetics
 */

import { createTheme, ThemeOptions } from '@mui/material/styles';

import { a11y } from './accessibility';
import modernColors from './modern-colors';
import modernTypography from './modern-typography';

/**
 * Spacing Configuration (8px base unit)
 */
const spacing = 8;

/**
 * Responsive Breakpoints
 */
const breakpoints = {
  values: {
    xs: 0,
    sm: 640,    // Tailwind-aligned
    md: 768,
    lg: 1024,
    xl: 1280,
  },
};

/**
 * Shape Configuration - Modern rounded corners
 */
const shape = {
  borderRadius: 12,  // Increased for modern look
};

/**
 * Modern Shadow System
 */
const shadows = [
  'none',
  modernColors.shadow.sm,
  modernColors.shadow.md,
  modernColors.shadow.lg,
  modernColors.shadow.xl,
  modernColors.shadow['2xl'],
  modernColors.shadow.glass,
  modernColors.shadow.modern,
  modernColors.shadow.glow,
  // MUI requires 25 shadow levels
  '0 30px 60px -15px rgba(0,0,0,0.3)',
  '0 35px 70px -20px rgba(0,0,0,0.35)',
  '0 40px 80px -25px rgba(0,0,0,0.4)',
  '0 45px 90px -30px rgba(0,0,0,0.45)',
  '0 50px 100px -35px rgba(0,0,0,0.5)',
  '0 55px 110px -40px rgba(0,0,0,0.55)',
  '0 60px 120px -45px rgba(0,0,0,0.6)',
  '0 65px 130px -50px rgba(0,0,0,0.65)',
  '0 70px 140px -55px rgba(0,0,0,0.7)',
  '0 75px 150px -60px rgba(0,0,0,0.75)',
  '0 80px 160px -65px rgba(0,0,0,0.8)',
  '0 85px 170px -70px rgba(0,0,0,0.85)',
  '0 90px 180px -75px rgba(0,0,0,0.9)',
  '0 95px 190px -80px rgba(0,0,0,0.95)',
  '0 100px 200px -85px rgba(0,0,0,1)',
  '0 105px 210px -90px rgba(0,0,0,1)',
] as const;

/**
 * Modern Light Theme Configuration
 */
const lightThemeOptions: ThemeOptions = {
  palette: {
    mode: 'light',

    // Primary colors
    primary: {
      main: modernColors.primary[500],
      light: modernColors.primary[400],
      dark: modernColors.primary[700],
      contrastText: '#FFFFFF',
    },

    // Secondary colors
    secondary: {
      main: modernColors.secondary[500],
      light: modernColors.secondary[400],
      dark: modernColors.secondary[700],
      contrastText: '#FFFFFF',
    },

    // Semantic colors
    success: {
      main: modernColors.success[500],
      light: modernColors.success[100],
      dark: modernColors.success[700],
      contrastText: modernColors.success.contrastText,
    },

    error: {
      main: modernColors.error[500],
      light: modernColors.error[100],
      dark: modernColors.error[700],
      contrastText: modernColors.error.contrastText,
    },

    warning: {
      main: modernColors.warning[500],
      light: modernColors.warning[100],
      dark: modernColors.warning[700],
      contrastText: modernColors.warning.contrastText,
    },

    info: {
      main: modernColors.info[500],
      light: modernColors.info[100],
      dark: modernColors.info[700],
      contrastText: modernColors.info.contrastText,
    },

    // Text colors
    text: {
      primary: modernColors.text.primary,
      secondary: modernColors.text.secondary,
      disabled: modernColors.text.disabled,
    },

    // Background colors
    background: {
      default: modernColors.background.default,
      paper: modernColors.background.paper,
    },

    // Divider
    divider: modernColors.divider.main,
  },

  typography: modernTypography,
  spacing,
  breakpoints,
  shape,
  shadows: shadows as any,

  // ============================================
  // COMPONENT OVERRIDES - Modern styling
  // ============================================
  components: {
    // ==== MuiButton ====
    MuiButton: {
      styleOverrides: {
        root: {
          minHeight: 44,
          minWidth: 64,
          padding: '10px 20px',
          borderRadius: 12,
          fontWeight: 600,
          fontSize: '0.9375rem',
          textTransform: 'none',
          boxShadow: 'none',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: modernColors.shadow.md,
          },
          '&:active': {
            transform: 'translateY(0)',
          },
          '&:focus-visible': {
            outline: 'none',
            boxShadow: a11y.getFocusRing(modernColors.primary[500]),
          },
        },
        sizeLarge: {
          minHeight: 48,
          padding: '12px 28px',
          fontSize: '1rem',
        },
        sizeSmall: {
          minHeight: 36,
          padding: '6px 16px',
          fontSize: '0.875rem',
        },
        contained: {
          boxShadow: modernColors.shadow.sm,
          '&:hover': {
            boxShadow: modernColors.shadow.lg,
          },
        },
        outlined: {
          borderWidth: '2px',
          '&:hover': {
            borderWidth: '2px',
          },
        },
      },
      defaultProps: {
        disableElevation: false,
        disableRipple: a11y.prefersReducedMotion(),
      },
    },

    // ==== MuiCard ====
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: modernColors.shadow.sm,
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            boxShadow: modernColors.shadow.md,
          },
        },
      },
    },

    // ==== MuiPaper ====
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
        elevation1: {
          boxShadow: modernColors.shadow.sm,
        },
        elevation2: {
          boxShadow: modernColors.shadow.md,
        },
        elevation3: {
          boxShadow: modernColors.shadow.lg,
        },
      },
    },

    // ==== MuiTextField ====
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 12,
            transition: 'all 0.2s ease',
            '&:hover': {
              '& .MuiOutlinedInput-notchedOutline': {
                borderColor: modernColors.primary[300],
              },
            },
            '&.Mui-focused': {
              '& .MuiOutlinedInput-notchedOutline': {
                borderWidth: '2px',
                borderColor: modernColors.primary[500],
              },
            },
          },
          '& .MuiInputLabel-root.Mui-focused': {
            color: modernColors.primary[500],
          },
        },
      },
    },

    // ==== MuiChip ====
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          fontWeight: 500,
          transition: 'all 0.2s ease',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: modernColors.shadow.sm,
          },
        },
        filled: {
          backgroundColor: modernColors.primary[100],
          color: modernColors.primary[700],
          '&:hover': {
            backgroundColor: modernColors.primary[200],
          },
        },
      },
    },

    // ==== MuiIconButton ====
    MuiIconButton: {
      styleOverrides: {
        root: {
          minWidth: 44,
          minHeight: 44,
          borderRadius: 12,
          transition: 'all 0.2s ease',
          '&:hover': {
            backgroundColor: modernColors.glass.black.light,
            transform: 'scale(1.05)',
          },
          '&:focus-visible': {
            outline: 'none',
            boxShadow: a11y.getFocusRing(modernColors.primary[500]),
          },
        },
      },
    },

    // ==== MuiAppBar ====
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: modernColors.shadow.sm,
          backdropFilter: 'blur(10px)',
          backgroundColor: modernColors.glass.white.light,
          color: modernColors.text.primary,
        },
      },
    },

    // ==== MuiDrawer ====
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRadius: '0 16px 16px 0',
          borderRight: 'none',
          boxShadow: modernColors.shadow.xl,
        },
      },
    },

    // ==== MuiDialog ====
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 20,
          boxShadow: modernColors.shadow['2xl'],
        },
      },
    },

    // ==== MuiTooltip ====
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: 'rgba(55, 65, 81, 0.95)',
          backdropFilter: 'blur(8px)',
          borderRadius: 8,
          padding: '8px 12px',
          fontSize: '0.875rem',
          fontWeight: 500,
        },
        arrow: {
          color: 'rgba(55, 65, 81, 0.95)',
        },
      },
    },

    // ==== MuiAlert ====
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          padding: '12px 16px',
          fontWeight: 500,
        },
        standardSuccess: {
          backgroundColor: modernColors.success.background,
          color: modernColors.success[700],
        },
        standardError: {
          backgroundColor: modernColors.error.background,
          color: modernColors.error[700],
        },
        standardWarning: {
          backgroundColor: modernColors.warning.background,
          color: modernColors.warning[700],
        },
        standardInfo: {
          backgroundColor: modernColors.info.background,
          color: modernColors.info[700],
        },
      },
    },

    // ==== MuiLinearProgress ====
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          height: 8,
        },
        bar: {
          borderRadius: 8,
        },
      },
    },

    // ==== MuiTab ====
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          fontSize: '0.9375rem',
          minHeight: 48,
          transition: 'all 0.2s ease',
          '&:hover': {
            color: modernColors.primary[600],
          },
          '&.Mui-selected': {
            color: modernColors.primary[600],
          },
        },
      },
    },

    // ==== MuiTabs ====
    MuiTabs: {
      styleOverrides: {
        indicator: {
          height: 3,
          borderRadius: '3px 3px 0 0',
          background: modernColors.gradients.primary,
        },
      },
    },
  },
};

/**
 * Modern Dark Theme Configuration
 */
const darkThemeOptions: ThemeOptions = {
  ...lightThemeOptions,
  palette: {
    mode: 'dark',

    primary: {
      main: modernColors.primary[400],
      light: modernColors.primary[300],
      dark: modernColors.primary[600],
      contrastText: '#FFFFFF',
    },

    secondary: {
      main: modernColors.secondary[400],
      light: modernColors.secondary[300],
      dark: modernColors.secondary[600],
      contrastText: '#FFFFFF',
    },

    success: {
      main: modernColors.success[500],
      light: modernColors.success[400],
      dark: modernColors.success[700],
      contrastText: '#FFFFFF',
    },

    error: {
      main: modernColors.error[500],
      light: modernColors.error[400],
      dark: modernColors.error[700],
      contrastText: '#FFFFFF',
    },

    warning: {
      main: modernColors.warning[500],
      light: modernColors.warning[400],
      dark: modernColors.warning[700],
      contrastText: '#000000',
    },

    info: {
      main: modernColors.info[500],
      light: modernColors.info[400],
      dark: modernColors.info[700],
      contrastText: '#FFFFFF',
    },

    text: {
      primary: '#F9FAFB',
      secondary: '#D1D5DB',
      disabled: '#9CA3AF',
    },

    background: {
      default: modernColors.background.dark,
      paper: modernColors.background.darkPaper,
    },

    divider: modernColors.divider.dark,
  },
};

/**
 * Create theme instances
 */
export const modernLightTheme = createTheme(lightThemeOptions);
export const modernDarkTheme = createTheme(darkThemeOptions);

/**
 * Get theme based on mode
 */
export const getModernTheme = (mode: 'light' | 'dark' = 'light') => {
  return mode === 'dark' ? modernDarkTheme : modernLightTheme;
};

/**
 * Export default theme (light)
 */
export default modernLightTheme;
