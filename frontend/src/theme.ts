/**
 * KIRO2 Theme Configuration
 * WCAG AA compliant theme with accessibility features
 */

import { createTheme, ThemeOptions } from '@mui/material/styles';

import { a11y } from './theme/accessibility';
import colors from './theme/colors';

/**
 * Typography Configuration
 * WCAG requires readable text with proper contrast
 */
const typography = {
  fontFamily: [
    'Roboto',
    '-apple-system',
    'BlinkMacSystemFont',
    '"Segoe UI"',
    'Arial',
    'sans-serif',
  ].join(','),

  // Font sizes optimized for readability
  h1: {
    fontSize: '2.5rem',    // 40px
    fontWeight: 700,
    lineHeight: 1.2,
    letterSpacing: '-0.01562em',
  },
  h2: {
    fontSize: '2rem',      // 32px
    fontWeight: 700,
    lineHeight: 1.3,
    letterSpacing: '-0.00833em',
  },
  h3: {
    fontSize: '1.75rem',   // 28px
    fontWeight: 600,
    lineHeight: 1.4,
  },
  h4: {
    fontSize: '1.5rem',    // 24px
    fontWeight: 600,
    lineHeight: 1.4,
  },
  h5: {
    fontSize: '1.25rem',   // 20px
    fontWeight: 600,
    lineHeight: 1.5,
  },
  h6: {
    fontSize: '1.125rem',  // 18px
    fontWeight: 600,
    lineHeight: 1.5,
  },
  body1: {
    fontSize: '1rem',      // 16px
    lineHeight: 1.5,       // WCAG recommends 1.5 for body text
    letterSpacing: '0.00938em',
  },
  body2: {
    fontSize: '0.875rem',  // 14px
    lineHeight: 1.43,
    letterSpacing: '0.01071em',
  },
  button: {
    fontSize: '0.875rem',
    fontWeight: 600,
    textTransform: 'none' as const, // Keep original case (better UX)
    letterSpacing: '0.02857em',
  },
  caption: {
    fontSize: '0.75rem',   // 12px (minimum readable size)
    lineHeight: 1.66,
    letterSpacing: '0.03333em',
  },
};

/**
 * Spacing Configuration
 * Consistent spacing for better visual hierarchy
 */
const spacing = 8; // Base spacing unit (8px)

/**
 * Breakpoints Configuration
 * Responsive design breakpoints
 */
const breakpoints = {
  values: {
    xs: 0,
    sm: 600,
    md: 960,
    lg: 1280,
    xl: 1920,
  },
};

/**
 * Shape Configuration
 */
const shape = {
  borderRadius: 8, // Rounded corners for better aesthetics
};

/**
 * Light Theme Configuration
 */
const lightThemeOptions: ThemeOptions = {
  palette: {
    mode: 'light',
    primary: {
      main: colors.primary.main,
      light: colors.primary.light,
      dark: colors.primary.dark,
      contrastText: colors.primary.contrastText,
    },
    secondary: {
      main: colors.secondary.main,
      light: colors.secondary.light,
      dark: colors.secondary.dark,
      contrastText: colors.secondary.contrastText,
    },
    success: {
      main: colors.success.main,
      light: colors.success.light,
      dark: colors.success.dark,
      contrastText: colors.success.contrastText,
    },
    error: {
      main: colors.error.main,
      light: colors.error.light,
      dark: colors.error.dark,
      contrastText: colors.error.contrastText,
    },
    warning: {
      main: colors.warning.main,
      light: colors.warning.light,
      dark: colors.warning.dark,
      contrastText: colors.warning.contrastText,
    },
    info: {
      main: colors.info.main,
      light: colors.info.light,
      dark: colors.info.dark,
      contrastText: colors.info.contrastText,
    },
    text: {
      primary: colors.text.primary,
      secondary: colors.text.secondary,
      disabled: colors.text.disabled,
    },
    background: {
      default: colors.background.default,
      paper: colors.background.paper,
    },
    action: {
      active: colors.action.active,
      hover: colors.action.hover,
      selected: colors.action.selected,
      disabled: colors.action.disabled,
      disabledBackground: colors.action.disabledBackground,
      focus: colors.action.focus,
    },
    divider: colors.divider.main,
  },
  typography,
  spacing,
  breakpoints,
  shape,
  components: {
    // Button component customization
    MuiButton: {
      styleOverrides: {
        root: {
          minHeight: 44, // WCAG touch target size
          minWidth: 64,
          padding: '8px 16px',
          // Focus ring for accessibility
          '&:focus-visible': {
            outline: 'none',
            boxShadow: a11y.getFocusRing(colors.primary.main),
          },
        },
        sizeLarge: {
          minHeight: 48,
          padding: '12px 24px',
        },
        sizeSmall: {
          minHeight: 36,
          padding: '6px 12px',
        },
      },
      defaultProps: {
        disableElevation: false, // Keep elevation for depth
        disableRipple: a11y.prefersReducedMotion(), // Disable ripple if user prefers reduced motion
      },
    },

    // TextField component customization
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiInputBase-root': {
            minHeight: 44, // WCAG touch target size
          },
          // Focus ring
          '& .MuiOutlinedInput-root.Mui-focused .MuiOutlinedInput-notchedOutline': {
            borderColor: colors.primary.main,
            borderWidth: '2px',
          },
        },
      },
    },

    // IconButton component customization
    MuiIconButton: {
      styleOverrides: {
        root: {
          minWidth: 44, // WCAG touch target size
          minHeight: 44,
          // Focus ring
          '&:focus-visible': {
            outline: 'none',
            boxShadow: a11y.getFocusRing(colors.primary.main),
          },
        },
      },
    },

    // Link component customization
    MuiLink: {
      styleOverrides: {
        root: {
          color: colors.semantic.link,
          textDecorationColor: colors.semantic.link,
          '&:hover': {
            color: colors.semantic.linkHover,
          },
          '&:visited': {
            color: colors.semantic.linkVisited,
          },
          // Focus ring
          '&:focus-visible': {
            outline: 'none',
            boxShadow: a11y.getFocusRing(colors.primary.main),
            borderRadius: '2px',
          },
        },
      },
    },

    // Alert component customization
    MuiAlert: {
      styleOverrides: {
        standardSuccess: {
          backgroundColor: colors.success.background,
          color: colors.text.primary,
        },
        standardError: {
          backgroundColor: colors.error.background,
          color: colors.text.primary,
        },
        standardWarning: {
          backgroundColor: colors.warning.background,
          color: colors.text.primary,
        },
        standardInfo: {
          backgroundColor: colors.info.background,
          color: colors.text.primary,
        },
      },
    },

    // Chip component customization
    MuiChip: {
      styleOverrides: {
        root: {
          minHeight: 32,
          // Focus ring
          '&:focus-visible': {
            outline: 'none',
            boxShadow: a11y.getFocusRing(colors.primary.main),
          },
        },
      },
    },

    // Dialog component customization
    MuiDialog: {
      styleOverrides: {
        paper: {
          boxShadow: '0px 11px 15px -7px rgba(0,0,0,0.2), 0px 24px 38px 3px rgba(0,0,0,0.14)',
        },
      },
    },

    // Tooltip component customization
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          fontSize: '0.875rem', // Readable size
          backgroundColor: 'rgba(97, 97, 97, 0.95)', // High contrast
          padding: '8px 12px',
        },
      },
    },

    // Tab component customization
    MuiTab: {
      styleOverrides: {
        root: {
          minHeight: 48,
          padding: '12px 16px',
          // Focus ring
          '&:focus-visible': {
            outline: 'none',
            boxShadow: a11y.getFocusRing(colors.primary.main),
          },
        },
      },
    },
  },
};

/**
 * Dark Theme Configuration
 */
const darkThemeOptions: ThemeOptions = {
  ...lightThemeOptions,
  palette: {
    mode: 'dark',
    primary: {
      main: colors.primary.light, // Lighter shade for dark mode
      light: colors.primary.main,
      dark: colors.primary.dark,
      contrastText: colors.text.primary,
    },
    secondary: {
      main: colors.secondary.light,
      light: colors.secondary.main,
      dark: colors.secondary.dark,
      contrastText: colors.text.primary,
    },
    success: {
      main: colors.success.light,
      light: colors.success.main,
      dark: colors.success.dark,
      contrastText: colors.text.primary,
    },
    error: {
      main: colors.error.light,
      light: colors.error.main,
      dark: colors.error.dark,
      contrastText: colors.text.primary,
    },
    warning: {
      main: colors.warning.light,
      light: colors.warning.main,
      dark: colors.warning.dark,
      contrastText: colors.text.primary,
    },
    info: {
      main: colors.info.light,
      light: colors.info.main,
      dark: colors.info.dark,
      contrastText: colors.text.primary,
    },
    text: {
      primary: colors.text.white,
      secondary: 'rgba(255, 255, 255, 0.7)',
      disabled: 'rgba(255, 255, 255, 0.5)',
    },
    background: {
      default: colors.background.dark,
      paper: colors.background.elevation1,
    },
    action: {
      active: colors.primary.light,
      hover: colors.action.hoverDark,
      selected: a11y.hexToRgba(colors.primary.light, 0.16),
      disabled: 'rgba(255, 255, 255, 0.3)',
      disabledBackground: 'rgba(255, 255, 255, 0.12)',
      focus: a11y.hexToRgba(colors.primary.light, 0.24),
    },
    divider: colors.divider.dark,
  },
};

/**
 * Create theme instances
 */
export const lightTheme = createTheme(lightThemeOptions);
export const darkTheme = createTheme(darkThemeOptions);

/**
 * Get theme based on mode
 */
export const getTheme = (mode: 'light' | 'dark' = 'light') => {
  return mode === 'dark' ? darkTheme : lightTheme;
};

/**
 * Export default theme (light)
 */
export default lightTheme;

/**
 * Export colors for direct access
 */
export { colors };

/**
 * Export accessibility utilities
 */
export { a11y };
