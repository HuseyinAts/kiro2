/**
 * Modern Theme Configuration
 * Enhanced Material-UI theme with design tokens and accessibility
 */

import { createTheme, ThemeOptions } from '@mui/material/styles'
import { alpha } from '@mui/material/styles'

// Design tokens
const designTokens = {
  colors: {
    primary: {
      50: '#eff6ff',
      100: '#dbeafe',
      200: '#bfdbfe',
      300: '#93c5fd',
      400: '#60a5fa',
      500: '#3b82f6',
      600: '#2563eb',
      700: '#1d4ed8',
      800: '#1e40af',
      900: '#1e3a8a'
    },
    secondary: {
      50: '#f0fdf4',
      100: '#dcfce7',
      200: '#bbf7d0',
      300: '#86efac',
      400: '#4ade80',
      500: '#22c55e',
      600: '#16a34a',
      700: '#15803d',
      800: '#166534',
      900: '#14532d'
    },
    neutral: {
      50: '#fafafa',
      100: '#f5f5f5',
      200: '#e5e5e5',
      300: '#d4d4d4',
      400: '#a3a3a3',
      500: '#737373',
      600: '#525252',
      700: '#404040',
      800: '#262626',
      900: '#171717'
    },
    error: {
      50: '#fef2f2',
      100: '#fee2e2',
      200: '#fecaca',
      300: '#fca5a5',
      400: '#f87171',
      500: '#ef4444',
      600: '#dc2626',
      700: '#b91c1c',
      800: '#991b1b',
      900: '#7f1d1d'
    },
    warning: {
      50: '#fffbeb',
      100: '#fef3c7',
      200: '#fde68a',
      300: '#fcd34d',
      400: '#fbbf24',
      500: '#f59e0b',
      600: '#d97706',
      700: '#b45309',
      800: '#92400e',
      900: '#78350f'
    },
    success: {
      50: '#f0fdf4',
      100: '#dcfce7',
      200: '#bbf7d0',
      300: '#86efac',
      400: '#4ade80',
      500: '#22c55e',
      600: '#16a34a',
      700: '#15803d',
      800: '#166534',
      900: '#14532d'
    }
  },
  typography: {
    fontFamily: {
      sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      mono: ['JetBrains Mono', 'Fira Code', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace']
    },
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
      '3xl': '1.875rem',
      '4xl': '2.25rem',
      '5xl': '3rem'
    },
    fontWeight: {
      thin: 100,
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
      extrabold: 800
    }
  },
  spacing: {
    px: '1px',
    0: '0rem',
    1: '0.25rem',
    2: '0.5rem',
    3: '0.75rem',
    4: '1rem',
    5: '1.25rem',
    6: '1.5rem',
    8: '2rem',
    10: '2.5rem',
    12: '3rem',
    16: '4rem',
    20: '5rem',
    24: '6rem'
  },
  borderRadius: {
    none: '0',
    sm: '0.125rem',
    md: '0.375rem',
    lg: '0.5rem',
    xl: '0.75rem',
    '2xl': '1rem',
    '3xl': '1.5rem',
    full: '9999px'
  },
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
  }
}

// Light theme configuration
const lightThemeOptions: ThemeOptions = {
  palette: {
    mode: 'light',
    primary: {
      main: designTokens.colors.primary[600],
      light: designTokens.colors.primary[400],
      dark: designTokens.colors.primary[800],
      contrastText: '#ffffff'
    },
    secondary: {
      main: designTokens.colors.secondary[600],
      light: designTokens.colors.secondary[400],
      dark: designTokens.colors.secondary[800],
      contrastText: '#ffffff'
    },
    error: {
      main: designTokens.colors.error[600],
      light: designTokens.colors.error[400],
      dark: designTokens.colors.error[800]
    },
    warning: {
      main: designTokens.colors.warning[600],
      light: designTokens.colors.warning[400],
      dark: designTokens.colors.warning[800]
    },
    success: {
      main: designTokens.colors.success[600],
      light: designTokens.colors.success[400],
      dark: designTokens.colors.success[800]
    },
    background: {
      default: designTokens.colors.neutral[50],
      paper: '#ffffff'
    },
    text: {
      primary: designTokens.colors.neutral[900],
      secondary: designTokens.colors.neutral[600]
    },
    divider: designTokens.colors.neutral[200]
  },
  typography: {
    fontFamily: designTokens.typography.fontFamily.sans.join(', '),
    h1: {
      fontSize: designTokens.typography.fontSize['5xl'],
      fontWeight: designTokens.typography.fontWeight.bold,
      lineHeight: 1.2,
      letterSpacing: '-0.025em'
    },
    h2: {
      fontSize: designTokens.typography.fontSize['4xl'],
      fontWeight: designTokens.typography.fontWeight.bold,
      lineHeight: 1.3,
      letterSpacing: '-0.025em'
    },
    h3: {
      fontSize: designTokens.typography.fontSize['3xl'],
      fontWeight: designTokens.typography.fontWeight.semibold,
      lineHeight: 1.4
    },
    h4: {
      fontSize: designTokens.typography.fontSize['2xl'],
      fontWeight: designTokens.typography.fontWeight.semibold,
      lineHeight: 1.4
    },
    h5: {
      fontSize: designTokens.typography.fontSize.xl,
      fontWeight: designTokens.typography.fontWeight.semibold,
      lineHeight: 1.5
    },
    h6: {
      fontSize: designTokens.typography.fontSize.lg,
      fontWeight: designTokens.typography.fontWeight.semibold,
      lineHeight: 1.5
    },
    body1: {
      fontSize: designTokens.typography.fontSize.base,
      lineHeight: 1.6
    },
    body2: {
      fontSize: designTokens.typography.fontSize.sm,
      lineHeight: 1.5
    },
    button: {
      fontSize: designTokens.typography.fontSize.sm,
      fontWeight: designTokens.typography.fontWeight.medium,
      textTransform: 'none' as const
    }
  },
  spacing: 8,
  shape: {
    borderRadius: 8
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: designTokens.borderRadius.lg,
          fontWeight: designTokens.typography.fontWeight.medium,
          padding: '10px 20px',
          minHeight: 44, // Touch-friendly minimum
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-1px)',
            boxShadow: designTokens.shadows.md
          }
        },
        contained: {
          boxShadow: designTokens.shadows.sm,
          '&:hover': {
            boxShadow: designTokens.shadows.lg
          }
        }
      }
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: designTokens.borderRadius.xl,
          boxShadow: designTokens.shadows.sm,
          border: `1px solid ${designTokens.colors.neutral[200]}`,
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            boxShadow: designTokens.shadows.md
          }
        }
      }
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: designTokens.borderRadius.lg,
            minHeight: 44, // Touch-friendly
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: designTokens.colors.primary[400]
            }
          }
        }
      }
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: 'none',
          backdropFilter: 'blur(8px)',
          backgroundColor: alpha('#ffffff', 0.8),
          borderBottom: `1px solid ${designTokens.colors.neutral[200]}`
        }
      }
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRight: `1px solid ${designTokens.colors.neutral[200]}`,
          boxShadow: 'none'
        }
      }
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: designTokens.borderRadius.full,
          fontWeight: designTokens.typography.fontWeight.medium
        }
      }
    },
    MuiTabs: {
      styleOverrides: {
        root: {
          '& .MuiTab-root': {
            textTransform: 'none',
            fontWeight: designTokens.typography.fontWeight.medium,
            minHeight: 44
          }
        }
      }
    }
  }
}

// Dark theme configuration
const darkThemeOptions: ThemeOptions = {
  ...lightThemeOptions,
  palette: {
    mode: 'dark',
    primary: {
      main: designTokens.colors.primary[400],
      light: designTokens.colors.primary[300],
      dark: designTokens.colors.primary[600],
      contrastText: designTokens.colors.neutral[900]
    },
    secondary: {
      main: designTokens.colors.secondary[400],
      light: designTokens.colors.secondary[300],
      dark: designTokens.colors.secondary[600],
      contrastText: designTokens.colors.neutral[900]
    },
    background: {
      default: designTokens.colors.neutral[900],
      paper: designTokens.colors.neutral[800]
    },
    text: {
      primary: designTokens.colors.neutral[100],
      secondary: designTokens.colors.neutral[400]
    },
    divider: designTokens.colors.neutral[700]
  }
}

// Create themes
export const lightTheme = createTheme(lightThemeOptions)
export const darkTheme = createTheme(darkThemeOptions)

// Theme context type
export interface ThemeContextType {
  mode: 'light' | 'dark'
  toggleMode: () => void
  theme: typeof lightTheme
}

// Export design tokens for use in components
export { designTokens }

export default lightTheme